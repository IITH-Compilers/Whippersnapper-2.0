import os
from subprocess import call
from pkg_resources import resource_filename
from p4gen.genpcap import get_parser_header_pcap, get_parser_field_pcap
from p4gen.p4template import *
from p4gen import copy_scripts

def generate_pisces_command(out_dir, nb_headers, nb_fields, checksum=False):
    rules = add_pisces_forwarding_rule()
    matches = 'ethernet_dstAddr=0x0708090A0B0C'
    for i in range(nb_headers-1):
        matches += ',header_{0}_field_0=1'.format(i)
    actions = 'set_field:2->reg0,resubmit(,1)'
    rules += add_openflow_rule(0, 32768, matches, actions)

    actions = ''
    if checksum:
        ip_checksum = 'calc_fields_update(ipv4_hdrChecksum,csum16,fields:ipv4_version_ihl,ipv4_diffserv,ipv4_totalLen,ipv4_identification,ipv4_flags_fragOffset,ipv4_ttl,ipv4_protocol,ipv4_srcAddr,ipv4_dstAddr),'
        actions += ip_checksum
    actions += 'deparse,output:NXM_NX_REG0[]'
    rules += add_openflow_rule(1, 32768, '', actions)

    with open ('%s/pisces_rules.txt' % out_dir, 'w') as out:
        out.write(rules)

class ParseNode():
    def __init__(self, parent=None, node_name='', code=''):
        self.parent = parent
        self.node_name = node_name
        self.code = code
        self.children = []

    def set_parent(self, parent):
        self.parent = parent

    def add_children(self, child):
        self.children.append(child)

    def get_node_name(self):
        return self.node_name

    def get_children(self):
        return self.children

    def get_code(self):
        return self.code

def preorder(node):
    program = ''
    if node:
        program += node.get_code()
        for n in node.get_children():
            program += preorder(n)
    return program

def loop_rec(root, depth, fanout):
    for i in range(fanout):
        node_name = root.get_node_name() + '_%d' % i
        header_type_name = 'header{0}_t'.format(node_name)
        header_name = 'header{0}'.format(node_name)
        parser_state_name = 'parse_header{0}'.format(node_name)
        select_field = 'field_0'
        next_states = ''
        if depth == 0:
            next_states = select_case('default', 'ingress')
        else:
            for j in range(fanout):
                next_states += select_case(j+1, '{0}_{1}'.format(parser_state_name, j))
            next_states += select_case('default', 'ingress')

        field_dec = add_header_field('field_0', 16)
        code = add_header(header_type_name, field_dec)
        code += add_parser(header_type_name, header_name, parser_state_name,
            select_field, next_states)

        n = ParseNode(root, node_name, code)

        root.add_children(n)
        if depth > 0:
            loop_rec(n, depth-1, fanout)


def add_forwarding_table(output_dir, program):
    fwd_tbl = 'forward_table'
    program += forward_table()
    program += control(fwd_tbl, '')
    commands = cli_commands(fwd_tbl)
    with open ('%s/commands.txt' % output_dir, 'w') as out:
        out.write(commands)
    return program

def write_output(output_dir, program):
    with open ('%s/main.p4' % output_dir, 'w') as out:
        out.write(program)
    copy_scripts(output_dir)

def parser_complexity(depth, fanout):
    """
    This method adds Ethernet, IPv4, TCP, UDP, and a number of generic headers
    which follow the UDP header. The UDP destination port 0x9091 is used to
    identify the generic header

    :param depth: the depth of the parsing graph
    :type depth: int
    :param fanout: the number branches for each node
    :type fanout: int
    :returns: str -- the header and parser definition

    """
    program = p4_define() + ethernet_header() + ptp_header() + parser_start()

    next_headers = select_case('ETHERTYPE_PTP', 'parse_ptp')
    next_headers += select_case('default', 'ingress')
    program += add_parser('ethernet_t', 'ethernet', 'parse_ethernet',
                            'etherType', next_headers)

    ptp_next_states = ''
    for i in range(fanout):
        ptp_next_states += select_case(i+1, 'parse_header_%d' % i)
    ptp_next_states += select_case('default', 'ingress')
    program += add_parser('ptp_t', 'ptp', 'parse_ptp',
                            'reserved2', ptp_next_states)

    root = ParseNode()
    loop_rec(root, depth, fanout)
    program += preorder(root)

    output_dir = 'output'
    if not os.path.exists(output_dir):
       os.makedirs(output_dir)
    program = add_forwarding_table(output_dir, program)
    write_output(output_dir, program)
    get_parser_header_pcap(depth+1, 1, output_dir)

    return True

def add_headers_and_parsers(nb_headers, nb_fields, do_checksum=False):
    """
    This method adds Ethernet, IPv4, TCP, UDP, and a number of generic headers
    which follow the UDP header. The UDP destination port 0x9091 is used to
    identify the generic header

    :param nb_headers: the number of generic headers included in the program
    :type nb_headers: int
    :param nb_fields: the number of fields (16 bits) in each header
    :type nb_fields: int
    :returns: str -- the header and parser definition

    """
    program = p4_define() + ethernet_header() + ptp_header() + parser_start()

    next_headers = select_case('ETHERTYPE_PTP', 'parse_ptp')
    next_headers += select_case('default', 'ingress')
    program += add_parser('ethernet_t', 'ethernet', 'parse_ethernet',
                            'etherType', next_headers)

    ptp_next_states = ''
    if (nb_headers > 0):
        ptp_next_states += select_case(0x1, 'parse_header_0')
    ptp_next_states += select_case('default', 'ingress')
    program += add_parser('ptp_t', 'ptp', 'parse_ptp',
                            'reserved2', ptp_next_states)

    field_dec = ''
    for i in range(nb_fields):
        field_dec += add_header_field('field_%d' % i, 16)

    for i in range(nb_headers):
        header_type_name = 'header_%d_t' % i
        header_name = 'header_%d' % i
        parser_state_name = 'parse_header_%d' % i
        if (i < (nb_headers - 1)):
            next_state  = select_case(0, 'ingress')
            next_state += select_case('default', 'parse_header_%d' % (i + 1))
        else:
            next_state = select_case('default', 'ingress')
        program += add_header(header_type_name, field_dec)
        program += add_parser(header_type_name, header_name, parser_state_name,
                                'field_0', next_state)
    return program


def benchmark_parser_header(nb_headers, nb_fields, do_checksum=False):
    """
    This method generate the P4 program to benchmark the P4 parser

    :param nb_headers: the number of generic headers included in the program
    :type nb_headers: int
    :param nb_fields: the number of fields (16 bits) in each header
    :type tbl_size: int
    :returns: bool -- True if there is no error

    """
    output_dir = 'output'
    if not os.path.exists(output_dir):
       os.makedirs(output_dir)
    program  = add_headers_and_parsers(nb_headers, nb_fields, do_checksum)
    program = add_forwarding_table(output_dir, program)
    write_output(output_dir, program)
    get_parser_header_pcap(nb_fields, nb_headers, output_dir)
    generate_pisces_command(output_dir, nb_headers, nb_fields, do_checksum)

    return True

def benchmark_parser_with_header_field(nb_fields, do_checksum=False):
    """
    This method generate the P4 program to benchmark the P4 parser

    :param nb_fields: the number of fields (16 bits) in each header
    :type tbl_size: int
    :returns: bool -- True if there is no error

    """
    output_dir = 'output'
    if not os.path.exists(output_dir):
       os.makedirs(output_dir)
    program  = add_headers_and_parsers(1, nb_fields, do_checksum)
    program = add_forwarding_table(output_dir, program)
    write_output(output_dir, program)
    get_parser_field_pcap(nb_fields, output_dir)
    generate_pisces_command(output_dir, 1, nb_fields)

    return True