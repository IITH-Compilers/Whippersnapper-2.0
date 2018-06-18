import os
from subprocess import call
from pkg_resources import resource_filename
from p4gen.genpcap import get_pipeline_pcap
from p4gen import copy_scripts
from p4gen.p4template import *

def generate_pisces_command(nb_tables, table_size, out_dir):
    rules = add_pisces_forwarding_rule()
    match = 'ethernet_dstAddr=0x0708090A0B0C'
    action = 'set_field:2->reg0,resubmit(,1)'
    rules += add_openflow_rule(0, 32768, match, action)

    actions = ''
    for i in range(nb_tables-1):
        match = 'ethernet_dstAddr=0x0CC47AA32535'
        actions = 'set_field:2->reg0,resubmit(,{0})'.format(i+2)
        rules += add_openflow_rule(i+1, 32768, match, actions)
        match = 'ethernet_dstAddr=0x0708090A0B0C'
        actions = 'set_field:2->reg0,resubmit(,{0})'.format(i+2)
        rules += add_openflow_rule(i+1, 32768, match, actions)
        for j in range(table_size-2):
            mac_addr = "0x0{0}C47{1}A353{2}".format(j%10, j%7, j%5)
            match = 'ethernet_dstAddr=%s' % mac_addr
            actions = 'set_field:2->reg0,resubmit(,{0})'.format(i+2)
            rules += add_openflow_rule(i+1, 32768, match, actions)

    actions = 'deparse,output:NXM_NX_REG0[]'
    rules += add_openflow_rule(nb_tables, 32768, '', actions)

    with open ('%s/pisces_rules.txt' % out_dir, 'w') as out:
        out.write(rules)


def benchmark_pipeline(nb_tables, table_size):
    """
    This method generate the P4 program to benchmark the processing pipeline

    :param nb_tables: the number of tables in the pipeline
    :type nb_tables: str //bug
    :param table_size: the size of each table
    :type table_size: int
    :returns: bool -- True if there is no error

    """

    out_dir = 'output'
    if not os.path.exists(out_dir):
       os.makedirs(out_dir)

    fwd_tbl = 'forward_table'

    program = p4_define(14) + ethernet() + ipv4() + tcp() + udp() + \
            forward_table() + nop_action_14()

    # set Minimum table size
    if table_size < 16:
        table_size = 16

    applies = ''
    commands = ''
    match = 'ethernet.dstAddr : exact;'
    params = {1 : ("0C:C4:7A:A3:25:34", 1), 2: ("0C:C4:7A:A3:25:35", 2)}
    action_name = 'forward'
    for i in range(1, nb_tables):
        comp_action = '%s%d' % (action_name, i)
        action_param = '_port'
        instruction = '\tmodify_field(standard_metadata.egress_spec, %s);' % action_param
        program += add_compound_action_14(comp_action, action_param, instruction)
        tbl_name = 'table_%d' % i
        program += add_table(tbl_name, match, '%s;' % comp_action, table_size, 14)
        applies += apply_table(tbl_name) + '\t'
        commands += add_rule(tbl_name, comp_action, params[1][0], params[1][1])
        commands += add_rule(tbl_name, comp_action, params[2][0], params[2][1])


    program += control(fwd_tbl, applies)

    with open ('%s/main.p4' % out_dir, 'w') as out:
        out.write(program)

    commands += cli_commands(fwd_tbl)
    with open ('%s/commands.txt' % out_dir, 'w') as out:
        out.write(commands)
    copy_scripts(out_dir)

    get_pipeline_pcap(out_dir)
    generate_pisces_command(nb_tables, table_size, out_dir)
    return True


def benchmark_pipeline_16(nb_tables, table_size):
    """
    This method generate the P4 program to benchmark the processing pipeline

    :param nb_tables: the number of tables in the pipeline
    :type nb_tables: str //bug
    :param table_size: the size of each table
    :type table_size: int
    :returns: bool -- True if there is no error

    """

    out_dir = 'output'
    if not os.path.exists(out_dir):
       os.makedirs(out_dir)

    fwd_tbl = 'forward_table'

    program = p4_define(16) + ethernet_header(16) + ipv4_header(16) + tcp_header(16)+ add_udp_header(16)

    program += add_metadata()

    header_dec = ''
    header_dec += add_struct_item('ethernet_t', 'ethernet')
    header_dec += add_struct_item('tcp_t', 'tcp')
    header_dec += add_struct_item('udp_t', 'udp')
    header_dec += add_struct_item('ipv4_t', 'ipv4')

    program += add_headers(header_dec)


    states_dec = ''
    states_dec += add_state_without_select('start','parse_ethernet')

    next_states = select_case('16w0x800', 'parse_ipv4')
    next_states += select_case('default', 'accept')
    states_dec += add_state('parse_ethernet', 'ethernet', 'etherType', next_states)

    next_states = select_case('8w0x6', 'parse_tcp')
    next_states = select_case('8w0x11', 'parse_udp')
    next_states += select_case('default', 'accept')
    states_dec += add_state('parse_ipv4', 'ipv4', 'protocol', next_states)

    states_dec += add_state_type_3('parse_tcp','accept', 'tcp')

    next_states = select_case('default', 'accept')
    states_dec += add_state('parse_udp', 'udp', 'dstPort', next_states)

    program += parser_16(states_dec, 'ParserImpl')


    tables = forward_table_16()
    actions = nop_action()

    # set Minimum table size
    if table_size < 16:
        table_size = 16

    applies = '\t\tbit<16> tmp = hdr.tcp.window;\n'

    commands = ''
    match = '\t\thdr.ethernet.dstAddr : exact;'
    params = {1 : ("0C:C4:7A:A3:25:34", 1), 2: ("0C:C4:7A:A3:25:35", 2)}
    action_name = 'forward'
    for i in range(1, nb_tables/2+1):
        comp_action = '%s%d' % (action_name, i)
        action_param = '_port'
        instruction = '\t\tstandard_metadata.egress_spec = %s;' % action_param
        actions += add_compound_action(comp_action, 'bit<9> ' + action_param, instruction)
        tbl_name = 'table_%d' % i
        tables += add_table(tbl_name, match, '\t%s;' % comp_action, table_size, 16)
        applies += '\t\tif(tmp != hdr.tcp.window) {\
                    \n\t\t\t %s.apply();\n\t\t}\n' % tbl_name
        table_name = 'table_%d' % (i+nb_tables/2)
        tables += test_table_16(table_name)
        applies += '\t\t else \n\t\t\t%s.apply();\n ' % table_name
        commands += add_rule(tbl_name, comp_action, params[1][0], params[1][1])
        commands += add_rule(tbl_name, comp_action, params[2][0], params[2][1])
    
    for i in range((nb_tables/2)*2+1, nb_tables+1):
        comp_action = '%s%d' % (action_name, i)
        action_param = '_port'
        instruction = '\t\tstandard_metadata.egress_spec = %s;' % action_param
        actions += add_compound_action(comp_action, 'bit<9> ' + action_param, instruction)
        tbl_name = 'table_%d' % i
        tables += add_table(tbl_name, match, '\t%s;' % comp_action, table_size, 16)
        applies += '\t\t%s.apply();\n\t\t}\n' % tbl_name
        commands += add_rule(tbl_name, comp_action, params[1][0], params[1][1])
        commands += add_rule(tbl_name, comp_action, params[2][0], params[2][1])

    arguments = 'inout headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata'
    program += add_control_block_16('ingress', actions, tables, applies, arguments)
    program += add_control_block_16('egress', '', '', '', arguments)

    applies = '\t\tpacket.emit(hdr.ethernet);\n'
    applies += '\t\tpacket.emit(hdr.tcp);\n'
    applies += '\t\tpacket.emit(hdr.udp);\n'
    applies += '\t\tpacket.emit(hdr.ipv4);\n'

    program += add_control_block_16('DeparserImpl', '', '', applies, 'packet_out packet, in headers hdr')

    program += add_control_block_16('verifyChecksum', '', '', '', 'inout headers hdr, inout metadata meta')
    program += add_control_block_16('computeChecksum', '', '', '', 'inout headers hdr, inout metadata meta')

    program += add_main_module()

    with open ('%s/main.p4' % out_dir, 'w') as out:
        out.write(program)

    commands += cli_commands(fwd_tbl)
    with open ('%s/commands.txt' % out_dir, 'w') as out:
        out.write(commands)
    copy_scripts(out_dir)

    get_pipeline_pcap(out_dir)
    generate_pisces_command(nb_tables, table_size, out_dir)
    return True



