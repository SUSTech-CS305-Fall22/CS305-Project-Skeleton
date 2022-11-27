import sys
import os
import pickle

class BtConfig:
    def __init__(self, args):
        self.output_file = 'output.dat'
        self.peer_list_file = args.p
        self.has_chunk_file = args.c
        self.max_conn = args.m
        self.identity = args.i
        self.peers = []
        self.haschunks = dict()
        self.verbose = args.v
        self.timeout = args.t

        self.bt_parse_peer_list()
        self.bt_parse_haschunk_list()

        if self.identity == 0:
            print('bt_parse error:  Node identity must not be zero!')
            sys.exit(1)

        p = self.bt_peer_info(self.identity)
        if p is None:
            print('bt_parse error:  No peer information for myself (id ', self.identity, ')!')
            sys.exit(1)

        self.ip= p[1]
        self.port = int(p[2])

    def bt_parse_peer_list(self):
        with open(self.peer_list_file, 'r') as file:
            for line in file:
                if line[0] == '#': 
                    continue
                line = line.strip(os.linesep)
                self.peers.append(line.split(' ')) # nodeid, hostname, port


    def bt_parse_haschunk_list(self):
        with open(self.has_chunk_file, 'rb') as file:
            self.haschunks = pickle.load(file)

    def bt_peer_info(self, identity):
        for item in self.peers:
            if int(item[0]) == identity:
                return item
        return None

    def bt_dump_config(self, config):
        print('CS305 PROJECT PEER')
        print('chunk-file:     ', config.chunk_file)
        print('has-chunk-file: ', config.has_chunk_file)
        print('max-conn:       ', config.max_conn)
        print('peer-identity:  ', config.identity)
        print('peer-list-file: ', config.peer_list_file)

        for p in config.peers:
            print('  peer ', p[0], ': ', p[1], ':', p[2])
    