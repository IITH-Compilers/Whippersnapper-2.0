#!/usr/bin/env python

import argparse

from parsing.bm_parser import benchmark_parser_header
from parsing.bm_parser import benchmark_parser_with_header_field
from parsing.bm_parser import parser_complexity
from processing.bm_pipeline import benchmark_pipeline
from state_access.bm_memory import benchmark_memory
from packet_modification.bm_modification import benchmark_modification
from action_complexity.bm_mod_field import benchmark_field_write
from parsing.bm_parser import benchmark_parser_header_16
from parsing.bm_parser import benchmark_parser_with_header_field_16
from parsing.bm_parser import parser_complexity_16
from processing.bm_pipeline import benchmark_pipeline_16
from state_access.bm_memory import benchmark_memory_16
from packet_modification.bm_modification import benchmark_modification_16
from action_complexity.bm_mod_field import benchmark_field_write_16



features = ['parse-header', 'parse-field', 'parse-complex', # Parsing
            'set-field',                                    # Action complexity
            'add-header', 'rm-header',                      # Packet Modification
            'pipeline',                                     # Processing Pipeline
            'read-state', 'write-state'                     # State Access
            ]

versions = [ '14','16' ]

def main():
    parser = argparse.ArgumentParser(description='A programs that generate a'
                            ' P4 program for benchmarking a particular feature')
    parser.add_argument('--feature', choices=features,
                help='select a feature for benchmarking')
    parser.add_argument('--checksum', default=False, action='store_true',
                            help='perform update checksum')
    #Version
    parser.add_argument('--version', choices=versions,
                 help= 'select the version for testing')
    # Processing options
    parser.add_argument('--tables', default=1, type=int, help='number of tables')
    parser.add_argument('--table-size', default=1, type=int,
                            help='number of rules in the table')
    # Parser (Field|Header) and Packet Modification options
    parser.add_argument('--headers', default=1, type=int, help='number of headers')
    parser.add_argument('--fields', default=1, type=int, help='number of fields')
    # Parser Complexity
    parser.add_argument('--depth', default=1, type=int,
                            help='the depth of the parse graph')
    parser.add_argument('--fanout', default=2, type=int,
                            help='the number of branch of a node in the parse graph')
    # State Access option
    parser.add_argument('--registers', default=1, type=int, help='number of registers')
    parser.add_argument('--nb-element', default=1024, type=int,
                            help='number of element in a register')
    parser.add_argument('--element-width', default=32, type=int,
                            help='the bit width of a register element')
    # Parser Action complexity
    parser.add_argument('--operations', default=1, type=int,
                            help='the number of set-field/read/write operations')

    args = parser.parse_args()

    if args.feature == 'parse-header' and args.version == '14':
        benchmark_parser_header(args.headers, args.fields, do_checksum=args.checksum, )
    elif args.feature == 'parse-field' and args.version == '14':
        benchmark_parser_with_header_field(args.fields, do_checksum=args.checksum)
    elif args.feature == 'parse-complex' and args.version == '14':
        parser_complexity(args.depth, args.fanout)
    elif args.feature == 'set-field' and args.version == '14':
        benchmark_field_write(args.operations, do_checksum=args.checksum)
    elif args.feature == 'add-header' and args.version == '14':
        benchmark_modification(args.headers, args.fields, 'add')
    elif args.feature == 'rm-header' and args.version == '14':
        benchmark_modification(args.headers, args.fields, 'rm')
    elif args.feature == 'pipeline' and args.version == '14':
        benchmark_pipeline(args.tables, args.table_size)
    elif args.feature == 'read-state' and args.version == '14':
        benchmark_memory(args.registers, args.element_width, args.nb_element,
                            args.operations, False)
    elif args.feature == 'write-state' and args.version == '14':
        benchmark_memory(args.registers, args.element_width, args.nb_element,
                            args.operations, True)

    elif args.feature == 'parse-header' and args.version == '16':
        benchmark_parser_header_16(args.headers, args.fields, do_checksum=args.checksum, )
    elif args.feature == 'parse-field' and args.version == '16':
        benchmark_parser_with_header_field_16(args.fields, do_checksum=args.checksum)
    elif args.feature == 'parse-complex' and args.version == '16':
        parser_complexity_16(args.depth, args.fanout)
    elif args.feature == 'set-field' and args.version == '16':
        benchmark_field_write_16(args.operations, do_checksum=args.checksum)
    elif args.feature == 'add-header' and args.version == '16':
        benchmark_modification_16(args.headers, args.fields, 'add')
    elif args.feature == 'rm-header' and args.version == '16':
        benchmark_modification_16(args.headers, args.fields, 'rm')
    elif args.feature == 'pipeline' and args.version == '16':
        benchmark_pipeline_16(args.tables, args.table_size)
    elif args.feature == 'read-state' and args.version == '16':
        benchmark_memory_16(args.registers, args.element_width, args.nb_element,
                            args.operations, False)
    elif args.feature == 'write-state' and args.version == '16':
        benchmark_memory_16(args.registers, args.element_width, args.nb_element,
                            args.operations, True)

if __name__=='__main__':
    main()
