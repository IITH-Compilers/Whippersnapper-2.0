import os
from subprocess import call
from pkg_resources import resource_filename

from p4gen.genpcap import get_write_state_pcap, get_read_state_pcap
from p4gen.p4template import *
from p4gen import copy_scripts

def add_registers(nb_registers, element_width, nb_elements, nb_operations,
        field, index):
    """
    This method generate the P4 code of register declaration and register actions

    :param nb_registers: the number of registers included in the program
    :type nb_registers: int
    :param element_width: the size of each register element
    :type element_width: int
    :param nb_elements: the number of elements in each register
    :type nb_elements: int
    :param nb_operations: the number of operations to the registers
    :type nb_operations: int
    :param field: the reference field for register read or write
    :type field: str
    :param index: the index of register element involving in the operation
    :type index: int
    :returns: bool -- True if there is no error

    """
    code_block = ''
    read_set = ''
    write_set = ''
    for i in range(nb_registers):
        register_name = 'register_%d' % i
        code_block += add_register(register_name, element_width, nb_elements, 14)
        for j in range(nb_operations):
            read_set  += register_read(register_name, field, index, element_width, 14)
            write_set += register_write(register_name, field, index, element_width, 14)

    code_block += register_actions(read_set, write_set, 14)
    return code_block

def add_registers_16(nb_registers, element_width, nb_elements, nb_operations,
        field, index):
    """
    This method generate the P4 code of register declaration and register actions

    :param nb_registers: the number of registers included in the program
    :type nb_registers: int
    :param element_width: the size of each register element
    :type element_width: int
    :param nb_elements: the number of elements in each register
    :type nb_elements: int
    :param nb_operations: the number of operations to the registers
    :type nb_operations: int
    :param field: the reference field for register read or write
    :type field: str
    :param index: the index of register element involving in the operation
    :type index: int
    :returns: bool -- True if there is no error

    """
    program = ''
    actions = ''
    read_set = ''
    write_set = ''
    for i in range(nb_registers):
        register_name = 'register_%d' % i
        program += add_register(register_name, element_width, nb_elements, 16)
        for j in range(nb_operations):
            read_set  += register_read(register_name, field, index, element_width, 16)
            write_set += register_write(register_name, field, index, element_width, 16)

    actions += register_actions(read_set, write_set, 16)
    return program, actions

def benchmark_memory(nb_registers, element_width, nb_elements, nb_operations, write_op=False):
    """
    This method generate the P4 program to benchmark memory consumption

    :param nb_registers: the number of registers included in the program
    :type nb_registers: int
    :param element_width: the size of each register element
    :type element_width: int
    :param nb_elements: the number of elements in each register
    :type nb_elements: int
    :param nb_elements: the number of operations to the registers
    :type nb_elements: int
    :returns: bool -- True if there is no error

    """
    udp_dport = 0x9091
    out_dir = 'output'
    if not os.path.exists(out_dir):
       os.makedirs(out_dir)

    fwd_tbl = 'forward_table'

    program = p4_define(14) + ethernet() + ipv4() + tcp()
    header_type_name = 'memtest_t'
    header_name = 'memtest'
    parser_state_name = 'parse_memtest'
    field_dec  = add_header_field('register_op', 4, 14)
    field_dec += add_header_field('index', 12, 14)
    field_dec += add_header_field('data', element_width, 14)

    program += udp(select_case(udp_dport, parser_state_name))
    program += add_header(header_type_name, field_dec, 14)
    program += add_parser_without_select(header_type_name, header_name,
                    parser_state_name, 'ingress')

    # metadata = 'mem_metadata'
    # program += add_metadata_instance(header_type_name, metadata)
    field = '%s.data' % header_name
    index = '%s.index' % header_name

    program += nop_action()

    program += add_registers(nb_registers, element_width, nb_elements, nb_operations,
                    field, index)

    match_field = '%s.register_op' % header_name
    matches = '%s : exact;' % match_field
    actions = 'get_value; put_value; _nop;'
    table_name = 'register_table'
    program += add_table(table_name, matches, actions, 3, 14)
    applies = apply_table(table_name)

    program += forward_table()
    program += control(fwd_tbl, applies)

    with open ('%s/main.p4' % out_dir, 'w') as out:
        out.write(program)

    commands = ''
    commands += cli_commands(fwd_tbl)
    commands += add_rule(table_name, '_nop', 0)
    commands += add_rule(table_name, 'get_value', 1)
    commands += add_rule(table_name, 'put_value', 2)
    with open ('%s/commands.txt' % out_dir, 'w') as out:
        out.write(commands)
    copy_scripts(out_dir)
    
    if write_op:
        get_write_state_pcap(udp_dport, out_dir)
    else:
        get_read_state_pcap(udp_dport, out_dir)

    return True

def benchmark_memory_16(nb_registers, element_width, nb_elements, nb_operations, write_op=False):
    """
    This method generate the P4 program to benchmark memory consumption

    :param nb_registers: the number of registers included in the program
    :type nb_registers: int
    :param element_width: the size of each register element
    :type element_width: int
    :param nb_elements: the number of elements in each register
    :type nb_elements: int
    :param nb_elements: the number of operations to the registers
    :type nb_elements: int
    :returns: bool -- True if there is no error

    """
    udp_dport = 0x9091
    out_dir = 'output'
    if not os.path.exists(out_dir):
       os.makedirs(out_dir)

    fwd_tbl = 'forward_table'

    program = p4_define(16) + ethernet_header(16) + ipv4_header(16) + tcp_header(16)+ add_udp_header(16)
    header_type_name = 'memtest_t'
    header_name = 'memtest'
    parser_state_name = 'parse_memtest'
    field_dec  = add_header_field('register_op', 4, 16)
    field_dec += add_header_field('index', 12, 16)
    field_dec += add_header_field('data', element_width, 16)

    program += add_header(header_type_name, field_dec, 16)

    program += add_metadata()

    header_dec = ''
    header_dec += add_struct_item('ethernet_t', 'ethernet')
    header_dec += add_struct_item('tcp_t', 'tcp')
    header_dec += add_struct_item('udp_t', 'udp')
    header_dec += add_struct_item('ipv4_t', 'ipv4')
    header_dec += add_struct_item('memtest_t', 'memtest')

    program += add_headers(header_dec)

    states_dec = ''
    states_dec += add_state_without_select('start','parse_ethernet')

    next_states = select_case('16w0x800', 'parse_ipv4')
    next_states += select_case('default', 'accept')
    states_dec += add_state('parse_ethernet', 'ethernet', 'etherType', next_states)

    next_states = select_case('8w0x6', 'parse_tcp')
    next_states += select_case('8w0x11', 'parse_udp')
    next_states += select_case('default', 'accept')
    states_dec += add_state('parse_ipv4', 'ipv4', 'protocol', next_states)

    states_dec += add_state_type_3('parse_tcp','accept', 'tcp')

    next_states = select_case('16w37009', 'parse_memtest')
    next_states += select_case('default', 'accept')
    states_dec += add_state('parse_udp', 'udp', 'dstPort', next_states)

    states_dec += add_state_type_3('parse_memtest', 'accept', 'memtest')

    program += parser_16(states_dec, 'ParserImpl')

    # metadata = 'mem_metadata'
    # program += add_metadata_instance(header_type_name, metadata)
    field = '%s.data' % header_name
    index = '%s.index' % header_name


    code_block, actions = add_registers_16(nb_registers, element_width, nb_elements, nb_operations,
                    field, index)

    program += code_block
    actions += nop_action()
    tables = forward_table_16()

    match_field = '\t\thdr.%s.register_op' % header_name
    matches = '%s : exact;\n' % match_field
    action = '\t\tget_value;\n\t\tput_value;\n\t\t_nop;\n'
    table_name = 'register_table'
    tables += add_table(table_name, matches, action, 3, 16)
    applies = '\t\t%s.apply();\n' % fwd_tbl
    applies += '\t\t%s.apply();\n' % table_name

    arguments = 'inout headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata'
    program += add_control_block_16('ingress', actions, tables, applies, arguments)
    program += add_control_block_16('egress', '', '', '', arguments)

    applies = '\t\tpacket.emit(hdr.ethernet);\n'
    applies += '\t\tpacket.emit(hdr.tcp);\n'
    applies += '\t\tpacket.emit(hdr.udp);\n'
    applies += '\t\tpacket.emit(hdr.ipv4);\n'
    applies += '\t\tpacket.emit(hdr.memtest);\n'

    program += add_control_block_16('DeparserImpl', '', '', applies, 'packet_out packet, in headers hdr')

    program += add_control_block_16('verifyChecksum', '', '', '', 'inout headers hdr, inout metadata meta')
    program += add_control_block_16('computeChecksum', '', '', '', 'inout headers hdr, inout metadata meta')

    program += add_main_module()

    with open ('%s/main.p4' % out_dir, 'w') as out:
        out.write(program)

    commands = ''
    commands += cli_commands(fwd_tbl)
    commands += add_rule(table_name, '_nop', 0)
    commands += add_rule(table_name, 'get_value', 1)
    commands += add_rule(table_name, 'put_value', 2)
    with open ('%s/commands.txt' % out_dir, 'w') as out:
        out.write(commands)
    copy_scripts(out_dir)
    
    if write_op:
        get_write_state_pcap(udp_dport, out_dir)
    else:
        get_read_state_pcap(udp_dport, out_dir)

    return program
