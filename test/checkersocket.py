import struct
import socket
import logging
import select
import os

SpiffyHeaderLen = struct.calcsize("I4s4sHH")
StdHeaderLen = struct.calcsize("HBBHHII")
_MAXBUFSIZE = 1500

class StdPkt:
    def __init__(self, magic, team, pkt_type, header_len, pkt_len, seq, ack, pkt_btyes, from_addr, to_addr) -> None:
        self.magic = magic
        self.team = team
        self.pkt_type = pkt_type
        self.header_len = header_len
        self.pkt_len = pkt_len
        self.seq = seq
        self.ack = ack
        self.from_addr = from_addr
        self.to_addr = to_addr
        self.pkt_bytes = pkt_btyes

class CheckerSocket:
    def __init__(self, addr) -> None:
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__sock.bind(addr)

        self.__logger = logging.getLogger("Checker-LOGGER")
        self.__logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter(fmt="%(relativeCreated)d - %(name)s - %(levelname)s - %(message)s")

        # check log dir
        log_dir = "log"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        fh = logging.FileHandler(filename=os.path.join(log_dir, "Checker.log"), mode="w")
        fh.setLevel(level=logging.DEBUG)
        fh.setFormatter(formatter)
        self.__logger.addHandler(fh)
        self.__logger.info("Start logging")
        
    def recv_pkt_from(self):
        read_pkt_byte, from_addr = self.__sock.recvfrom(_MAXBUFSIZE)
        mixedheaders = read_pkt_byte[:SpiffyHeaderLen+StdHeaderLen]
        s_head_ID, s_head_lSrcAddr, s_head_lDestAddr, s_head_lSrcPort, s_head_lDestPort = struct.unpack("I4s4sHH", mixedheaders[:SpiffyHeaderLen])
        s_head_lSrcAddr = socket.inet_ntoa(s_head_lSrcAddr)
        s_head_lDestAddr = socket.inet_ntoa(s_head_lDestAddr)
        s_head_lSrcPort = socket.ntohs(s_head_lSrcPort)
        s_head_lDestPort = socket.ntohs(s_head_lDestPort)

        magic, team, pkt_type, header_len, pkt_len, seq, ack = struct.unpack("HBBHHII", mixedheaders[SpiffyHeaderLen:])
        magic = socket.ntohs(magic)
        header_len = socket.ntohs(header_len)
        pkt_len = socket.ntohs(pkt_len)
        seq = socket.ntohl(seq)
        ack = socket.ntohl(ack)

        # can_read, _, _ = select.select([self.__sock], [], [], 1)
        # if len(can_read) > 0:
        #     remainder_data, _ = self.__sock.recvfrom(pkt_len+SpiffyHeaderLen)

        # if len(can_read)==0 or len(remainder_data) != pkt_len+SpiffyHeaderLen:
        #     self.__logger.error(f"Pkt len in header is not correctly set or pkt corrupted {pkt_len}, {header_len}")
        #     raise Exception("Bad pkt len in header")

        to_addr = (s_head_lDestAddr, s_head_lDestPort)
        pkt = StdPkt(magic, team, pkt_type, header_len, pkt_len, seq, ack, read_pkt_byte, from_addr, to_addr)

        self.__logger.debug(f"{from_addr} sends a type{pkt_type} pkt to {to_addr}, seq{seq}, ack{ack}")

        return pkt

    def sendto(self, data, addr):
        self.__sock.sendto(data, addr)
    
    def fileno(self):
        return self.__sock.fileno()

    def add_log(self, msg):
        self.__logger.debug(msg)
