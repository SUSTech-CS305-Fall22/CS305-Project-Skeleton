import struct
import socket
import logging
import os
import sys

class SimSocket():
    __glSrcAddr = 0
    __gsSrcPort = 0
    __giSpiffyEnabled = False
    __glNodeID = 0
    __gsSpiffyAddr = 0
    __spiffyHeaderLen = struct.calcsize("I4s4sHH")
    __stdHeaderLen = struct.calcsize("HBBHHII")
    
    def __init__(self, id, address, verbose = 2) -> None:
        self.__address = address
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__sock.bind(address)
        self.__logger = logging.getLogger(f"PEER{id}_LOGGER")
        self.__logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter(fmt="%(asctime)s -+- %(name)s -+- %(levelname)s -+- %(message)s")
        if verbose > 0:
            if verbose == 1:
                sh_level = logging.WARNING
            elif verbose == 2:
                sh_level = logging.INFO
            elif verbose == 3:
                sh_level = logging.DEBUG
            else: 
                sh_level = logging.INFO
            sh = logging.StreamHandler(stream=sys.stdout)
            sh.setLevel(level = sh_level)
            sh.setFormatter(formatter)
            self.__logger.addHandler(sh)

        # check log dir
        log_dir = "log"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        fh = logging.FileHandler(filename=os.path.join(log_dir, f"peer{id}.log"), mode="w")

        fh.setLevel(level=logging.DEBUG)
        fh.setFormatter(formatter)
        self.__logger.addHandler(fh)
        self.__logger.info("Start logging")
        self.__simulator_init(id)

    def fileno(self):
        return self.__sock.fileno()
    
    def sendto(self, data_bytes, address, flags = 0) -> int:
        ip, port = address
        magic, team, pkt_type, header_len, pkt_len, seq, ack = struct.unpack("!HBBHHII", data_bytes[:self.__stdHeaderLen])
        if not self.__giSpiffyEnabled:
            self.__logger.debug(f"sending a type{pkt_type} pkt to {address} via normal socket, seq{seq}, ack{ack}, pkt_len{pkt_len}")
            return self.__sock.sendto(data_bytes, flags, address)
        
        s_head_lDestAddr = socket.inet_aton(ip)
        s_head_lDestPort = socket.htons(port)
        s_head_ID = socket.htonl(self.__glNodeID)
        s_head_lSrcAddr = socket.inet_aton(self.__glSrcAddr)
        s_head_lSrcPort = socket.htons(self.__gsSrcPort)

        s_head = struct.pack("I4s4sHH", s_head_ID, s_head_lSrcAddr, s_head_lDestAddr, s_head_lSrcPort, s_head_lDestPort)

        s_bytes= s_head + data_bytes

        self.__logger.debug(f"sending a type{pkt_type} pkt to {address} via spiffy, seq{seq}, ack{ack}, pkt_len{pkt_len}")
        ret = self.__sock.sendto(s_bytes, flags, self.__gsSpiffyAddr)
        return ret - len(s_head)

    def recvfrom(self, bufsize, flags=0):
        if not self.__giSpiffyEnabled:
            ret = self.__sock.recvfrom(bufsize, flags)
            magic, team, pkt_type, header_len, pkt_len, seq, ack = struct.unpack("!HBBHHII", ret[0][:self.__stdHeaderLen])
            self.__logger.debug(f"Receiving a type{pkt_type} pkt from {ret[1]} via normal socket, seq{seq}, ack{ack}, pkt_len{pkt_len}")
            return ret

        ret = self.__sock.recvfrom(bufsize+self.__spiffyHeaderLen, flags)

        if ret is not None:
            simu_bytes, addr = ret
            _, s_head_lSrcAddr, s_head_lDestAddr, s_head_lSrcPort, s_head_lDestPort = struct.unpack("I4s4sHH", simu_bytes[:self.__spiffyHeaderLen])
            from_addr = (socket.inet_ntoa(s_head_lSrcAddr), socket.ntohs(s_head_lSrcPort))
            to_addr = (socket.inet_ntoa(s_head_lDestAddr), socket.ntohs(s_head_lDestPort))
            data_bytes = simu_bytes[self.__spiffyHeaderLen:]

            magic, team, pkt_type, header_len, pkt_len, seq, ack = struct.unpack("!HBBHHII", data_bytes[:self.__stdHeaderLen])
            self.__logger.debug(f"Receiving a type{pkt_type} pkt from {from_addr} via spiffy, seq{seq}, ack{ack}, pkt_len{pkt_len}")
            # check if spiffy header intact
            if not to_addr == self.__address:
                self.__logger.error("Packet header corrupted, please check bytes read.")
                raise Exception("Packet header corrupted!")

        else:
            self.__logger.error("Error on simulator recvfrom")
        
        return (data_bytes, from_addr)

    def __simulator_init(self, nodeid):
        simulator_env = os.getenv("SIMULATOR")
        if simulator_env is None:
            self.__logger.warn("Simulator not set, using normal socket.")
            return False
        
        addr = simulator_env.split(":")
        if len(addr) != 2:
            self.__logger.warn(f"Badly formatted addr: {simulator_env}")
            return False

        self.__gsSpiffyAddr = (addr[0], int(addr[1]))   


        self.__glNodeID = nodeid
        self.__giSpiffyEnabled = True

        self.__glSrcAddr = self.__address[0]
        self.__gsSrcPort = self.__address[1]

        self.__logger.info(f"Network simulator activated, running at {self.__gsSpiffyAddr}.")
        return True

    def add_log(self, msg):
        self.__logger.info(msg)

    def close(self):
        self.__logger.info("socket closed")
        self.__sock.close()