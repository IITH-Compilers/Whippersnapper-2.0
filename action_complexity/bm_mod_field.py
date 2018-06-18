import os
from subprocess import call
from pkg_resources import resource_filename
from p4gen.genpcap import get_set_field_pcap
from p4gen.genpcap import set_custom_field_pcap
from p4gen import copy_scripts
from parsing.bm_parser import add_headers_and_parsers
from parsing.bm_parser import add_headers_and_parsers_16
from p4gen.p4template import *
from array import *

modifications = {
    0 : 'ipv4.diffserv',
    1 : 'ipv4.identification',
    2 : 'ipv4.ttl',
    3 : 'ipv4.hdrChecksum',
    4 : 'udp.srcPort',
    5 : 'udp.checksum',
}

modifications_pisces = {
    0 : 'ipv4_diffserv',
    1 : 'ipv4_identification',
    2 : 'ipv4_ttl',
    3 : 'ipv4_hdrChecksum',
    4 : 'udp_srcPort',
    5 : 'udp_checksum',
}

def write_to_ip_and_udp(action_name, nb_operation):
    instruction_set =''
    for i in range(nb_operation):
        instruction_set += '\tmodify_field({0}, {1});\n'.format( modifications[i%len(modifications)], i)
    return add_compound_action(action_name, '', instruction_set)

def write_to_custom_header(action_name, nb_operation):
    instruction_set ='\tmodify_field(header_0.field_0, 1);\n'
    for i in range(1, nb_operation):
        instruction_set += '\tmodify_field(header_0.field_{0}, header_0.field_{1});\n'.format(i, i-1)
    return add_compound_action_14(action_name, '', instruction_set)

def write_to_custom_header_16(action_name, nb_operation):
    nb_operation = nb_operation - 1
    instruction_set ='\t\thdr.header_0.field_0 = 16w1;\n'
    op = array('c', ['+','-','*','/'])
    num = array('c', ['0','1','2','3','4','5','6','7','8','9'])
    i = 0
    for i in range(1, nb_operation/3+1):
        instruction_set += '\t\thdr.header_0.field_{0} = hdr.header_0.field_{1};\n'.format(i, i-1)
        instruction_set += ('\t\thdr.header_0.field_{0} = hdr.header_0.field_{0} '+ op[i%4] + ' 16w' + num[i%10] + ';\n').format(i)
        instruction_set += ('\t\thdr.header_0.field_{0} = ' + num[i%10] + op[i%3] + '(standard_metadata.egress_rid '+ op[i%3] + ' 16w' + num[i%10] + ');\n').format(i)        
    for j in range((nb_operation/3)*3, nb_operation):
        i = i+1
        instruction_set += ('\t\thdr.header_0.field_{0} = hdr.header_0.field_{0} '+ op[i%4] + ' 16w' + num[i%10] + ';\n').format(i)        

    return add_compound_action(action_name, '', instruction_set)


def generate_pisces_command_mod_ip_udp(nb_operation, out_dir, checksum=False):
    rules = add_pisces_forwarding_rule()
    actions = ''
    for i in range(nb_operation):
        # match = 'udp_dstPort=0x9091'
        match = ''
        actions += 'set_field:{0}->{1},'.format(i, modifications_pisces[i%len(modifications_pisces)])
    if checksum:
        ip_checksum = 'calc_fields_update(ipv4_hdrChecksum,csum16,fields:ipv4_version_ihl,ipv4_diffserv,ipv4_totalLen,ipv4_identification,ipv4_flags_fragOffset,ipv4_ttl,ipv4_protocol,ipv4_srcAddr,ipv4_dstAddr),'
        actions += ip_checksum
        udp_checksum = "calc_fields_update(udp_checksum,csum16,fields:ipv4_srcAddr,ipv4_dstAddr,0x8'0,ipv4_protocol,udp_length_,udp_srcPort,udp_dstPort,udp_length_,payload),"
        actions += udp_checksum
    actions += 'deparse,output:NXM_NX_REG0[]'
    rules += add_openflow_rule(1, 32768, match, actions)
    with open ('%s/pisces_rules.txt' % out_dir, 'w') as out:
        out.write(rules)

def generate_pisces_command(nb_operation, out_dir, checksum=False):
    rules = add_pisces_forwarding_rule()
    match = 'ethernet_dstAddr=0x0708090A0B0C'
    action = 'set_field:2->reg0,resubmit(,1)'
    rules += add_openflow_rule(0, 32768, match, action)

    actions = ''
    match = 'ptp_reserved2=0x1'
    for i in range(nb_operation):
        actions += 'set_field:{0}->header_0_field_{1},'.format(i+1, i)
    actions += 'deparse,output:NXM_NX_REG0[]'
    rules += add_openflow_rule(1, 32768, match, actions)
    with open ('%s/pisces_rules.txt' % out_dir, 'w') as out:
        out.write(rules)

def add_ingress_block_16(nb_operations):
    
    actions = nop_action()
    action_name = 'mod_headers'
    actions += write_to_custom_header_16(action_name, nb_operations)
    tables = forward_table_16()
    table_name = 'test_tbl'
    match = '\t\t\thdr.ptp.reserved2 : exact;'
    action = '\t\t\t_nop;\n\t\t\t{0};'.format(action_name)
    tables += add_table(table_name, match, action, 4, 16)
    applies = '\t\tforward_table.apply();\n\t\t%s.apply();' % table_name
    arguments = 'inout headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata'

    return add_control_block_16('ingress', actions, tables, applies, arguments)

def benchmark_field_write(nb_operations, do_checksum=False):
    """
    This method generate the P4 program to benchmark packet modification

    :param nb_operations: the number of Set-Field actions
    :type nb_operations: int
    :returns: bool -- True if there is no error

    """
    out_dir = 'output'
    if not os.path.exists(out_dir):
       os.makedirs(out_dir)

    fwd_tbl = 'forward_table'
    nb_headers = 1
    program  = add_headers_and_parsers(nb_headers, nb_operations)
    program += nop_action_14()
    program += forward_table()

    action_name = 'mod_headers'
    program += write_to_custom_header(action_name, nb_operations)

    table_name = 'test_tbl'
    match = 'ptp.reserved2 : exact;'
    actions = '\t\t_nop;\n\t\t{0};'.format(action_name)
    program += add_table(table_name, match, actions, 4, 14)


    program += control(fwd_tbl, apply_table(table_name))

    with open ('%s/main.p4' % out_dir, 'w') as out:
        out.write(program)

    commands = add_default_rule(table_name, '_nop')
    # commands += add_rule(table_name, action_name, 319)
    commands += add_default_rule(table_name, action_name)
    commands += cli_commands(fwd_tbl)
    with open ('%s/commands.txt' % out_dir, 'w') as out:
        out.write(commands)
    copy_scripts(out_dir)
    set_custom_field_pcap(nb_operations, out_dir, packet_size=256)
    generate_pisces_command(nb_operations, out_dir, do_checksum)
    return True

def benchmark_field_write_16(nb_operations, do_checksum=False):
    """
    This method generate the P4 program to benchmark packet modification

    :param nb_operations: the number of Set-Field actions
    :type nb_operations: int
    :returns: bool -- True if there is no error

    """
    out_dir = 'output'
    if not os.path.exists(out_dir):
       os.makedirs(out_dir)

    fwd_tbl = 'forward_table'
    nb_headers = 1
    program  = add_headers_and_parsers_16(nb_headers, nb_operations)

    program += add_ingress_block_16(nb_operations)

    arguments = 'inout headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata'
    program += add_control_block_16('egress', '', '', '', arguments)

    applies = '\t\tpacket.emit(hdr.ethernet);\n'
    applies += '\t\tpacket.emit(hdr.ptp);\n'

    for i in range(nb_headers):
        applies += '\t\tpacket.emit(hdr.header_%d);\n' % i

    program += add_control_block_16('DeparserImpl', '', '', applies, 'packet_out packet, in headers hdr')

    program += add_control_block_16('verifyChecksum', '', '', '', 'inout headers hdr, inout metadata meta')
    program += add_control_block_16('computeChecksum', '', '', '', 'inout headers hdr, inout metadata meta')

    program += add_main_module()

    with open ('%s/main.p4' % out_dir, 'w') as out:
        out.write(program)

    action_name = 'mod_headers'
    table_name = 'test_tbl'

    commands = add_default_rule(table_name, '_nop')
    # commands += add_rule(table_name, action_name, 319)
    commands += add_default_rule(table_name, action_name)
    commands += cli_commands(fwd_tbl)
    with open ('%s/commands.txt' % out_dir, 'w') as out:
        out.write(commands)
    copy_scripts(out_dir)
    set_custom_field_pcap(nb_operations, out_dir, packet_size=256)
    generate_pisces_command(nb_operations, out_dir, do_checksum)

    return True


def benchmark_field_write_to_ip_udp(nb_operations, do_checksum=False):
    """
    This method generate the P4 program to benchmark packet modification

    :param nb_operations: the number of Set-Field actions
    :type nb_operations: int
    :returns: bool -- True if there is no error

    """
    out_dir = 'output'
    if not os.path.exists(out_dir):
       os.makedirs(out_dir)

    program = p4_define() + ethernet() + ipv4(checksum=do_checksum) + tcp() + \
            add_udp_header() + add_udp_parser(checksum=do_checksum) + \
            forward_table() + nop_action()

    fwd_tbl = 'forward_table'

    action_name = 'mod_headers'
    program += write_to_ip_and_udp(action_name, nb_operations)

    table_name = 'test_tbl'
    match = 'udp.dstPort : exact;'
    actions = '\t\t_nop;\n\t\t{0};'.format(action_name)
    program += add_table(table_name, match, actions, 4, 14)

    program += control(fwd_tbl, apply_table(table_name))

    with open ('%s/main.p4' % out_dir, 'w') as out:
        out.write(program)

    commands = add_default_rule(table_name, '_nop')
    # commands += add_rule(table_name, action_name, 319)
    commands += add_default_rule(table_name, action_name)
    commands += cli_commands(fwd_tbl)
    with open ('%s/commands.txt' % out_dir, 'w') as out:
        out.write(commands)
    copy_scripts(out_dir)
    get_set_field_pcap(out_dir, packet_size=256)
    generate_pisces_command_mod_ip_udp(nb_operations, out_dir, do_checksum)

    return True
