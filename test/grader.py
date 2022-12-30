import os
import random
import atexit
import select
from signal import signal
import sys
import checkersocket
from threading import Thread
import subprocess
import time
import signal
import queue
from concurrent.futures import ThreadPoolExecutor
import logging
os.chdir(os.path.join(os.path.dirname(__file__), ".."))

class PeerProc:
    def __init__(self, identity, peer_file_loc, node_map_loc, haschunk_loc, max_transmit = 1, timeout = 60):
        self.id = identity
        self.peer_file_loc = peer_file_loc
        self.node_map_loc = node_map_loc
        self.haschunk_loc = haschunk_loc
        self.max_transmit = max_transmit
        self.process = None
        self.send_record = dict() #{to_id:{type:cnt}}
        self.recv_record = dict() #{from_id:{type:cnt}}
        self.timeout = timeout

    def start_peer(self):
        if self.timeout:
            cmd = f"python3 -u {self.peer_file_loc} -p {self.node_map_loc} -c {self.haschunk_loc} -m {self.max_transmit} -i {self.id} -t {self.timeout}"
        else:
            cmd = f"python3 -u {self.peer_file_loc} -p {self.node_map_loc} -c {self.haschunk_loc} -m {self.max_transmit} -i {self.id}"

        self.process = subprocess.Popen(cmd.split(" "), stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,text=True, bufsize=1, universal_newlines=True)
        # ensure peer is running
        time.sleep(1) 

    def send_cmd(self, cmd):
        self.process.stdin.write(cmd)
        self.process.stdin.flush()

    def record_send_pkt(self, pkt_type, to_addr):
        if to_addr not in self.send_record:
            self.send_record[to_addr] = dict()
            for i in range(6):
                self.send_record[to_addr][i] = 0

        self.send_record[to_addr][pkt_type] += 1

    def record_recv_pkt(self, pkt_type, from_addr):
        if from_addr not in self.recv_record:
            self.recv_record[from_addr] = dict()
            for i in range(6):
                self.recv_record[from_addr][i] = 0

        self.recv_record[from_addr][pkt_type] += 1

    def terminate_peer(self):
        self.process.send_signal(signal.SIGINT)
        # self.process.terminate()
        self.process = None


class GradingSession:
    def __init__(self, grading_handler, latency = 0.05, spiffy=False, topo_map = "test/tmp3/topo3.map", nodes_map = "test/tmp3/nodes3.map"):
        self.peer_list = dict()
        self.checkerIP = "127.0.0.1"
        self.checkerPort = random.randint(30525, 52305)
        self.checker_sock = None
        self.checker_recv_queue = queue.Queue()
        self.checker_send_queue = queue.Queue()
        self._FINISH = False
        self.latency = latency
        self.grading_handler = grading_handler
        self.sending_window = dict()
        self.spiffy = spiffy

        self.topo = topo_map
        self.nodes = nodes_map

    def recv_pkt(self):
        while not self._FINISH:
            ready = select.select([self.checker_sock],[],[],0.1)
            read_ready = ready[0]
            if len(read_ready) > 0:
                pkt = self.checker_sock.recv_pkt_from()
                self.peer_list[pkt.from_addr].record_send_pkt(pkt.pkt_type, pkt.to_addr)
                self.checker_recv_queue.put(pkt)
    
    def send_pkt(self):
        while not self._FINISH:
            try:
                pkt = self.checker_send_queue.get(timeout = 0.1)
            except:
                continue
            
            if pkt.to_addr in self.peer_list:
                self.peer_list[pkt.to_addr].record_recv_pkt(pkt.pkt_type, pkt.from_addr)

            # time.sleep(self.latency)
            self.checker_sock.sendto(pkt.pkt_bytes, pkt.to_addr)
            # self.delay_pool.submit(lambda arg: GradingSession.delay_send(*arg), [self, pkt])

    def delay_send(self, pkt):
        time.sleep(self.latency)
        self.checker_sock.sendto(pkt.pkt_bytes, pkt.to_addr)

    def stop_grader(self):
        self._FINISH = True

    def add_peer(self, identity, peer_file_loc, node_map_loc, haschunk_loc, max_transmit, peer_addr, timeout = 60):
        peer = PeerProc(identity, peer_file_loc, node_map_loc, haschunk_loc, max_transmit, timeout=timeout)
        self.peer_list[peer_addr] = peer

    def run_grader(self):
        # set env
        os.environ["SIMULATOR"] = f"{self.checkerIP}:{self.checkerPort}"
        test_env = os.getenv("SIMULATOR")
        if test_env is None:
            raise Exception("Void env!")
        
        # run workers
        if not self.spiffy:
            self.start_time = time.time()
            self.checker_sock = checkersocket.CheckerSocket((self.checkerIP, self.checkerPort))
            recv_worker = Thread(target=GradingSession.recv_pkt,args=[self,] ,daemon = True)
            recv_worker.start()
            send_worker = Thread(target=GradingSession.send_pkt,args=[self,] ,daemon = True)
            send_worker.start()
            grading_worker = Thread(target=self.grading_handler, args=[self.checker_recv_queue, self.checker_send_queue,], daemon=True)
            grading_worker.start()
        else:
            self.start_time = time.time()
            # start simulator
            cmd = f"perl util/hupsim.pl -m {self.topo} -n {self.nodes} -p {self.checkerPort} -v 3"
            outfile = open("log/Checker.log", "w")
            simulator_process = subprocess.Popen(cmd.split(" "), stdin=subprocess.PIPE,stdout=outfile,stderr=outfile ,text=True, bufsize=1, universal_newlines=True)
            # ensure simulator starts
            time.sleep(5)

        #run peers
        for p in self.peer_list.values():
            p.start_peer()

        # wait for grading worker
        # grading_worker.join()
        # time.sleep(15)
        # grading_worker.join()
        # self._FINISH = True

def drop_handler(recv_queue, send_queue):
    dropped = False
    last_pkt = 3
    sending_window = []
    winsize_logger = logging.getLogger("WinSize-LOGGER")
    winsize_logger.setLevel(logging.INFO)
    formatter = logging.Formatter(fmt="%(relativeCreated)d - %(message)s")
    start_time = time.time()
    # check log dir
    log_dir = "log"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    fh = logging.FileHandler(filename=os.path.join(log_dir, "winsize.log"), mode="w")
    fh.setLevel(level=logging.INFO)
    fh.setFormatter(formatter)
    winsize_logger.addHandler(fh)
    winsize_logger.info("Winsize")

    cnt = 0

    while True:
        try:
            pkt = recv_queue.get(timeout=0.01)
        except:
            continue

        if pkt.pkt_type == 3:
            if pkt.seq not in sending_window:
                sending_window.append(pkt.seq)
            last_pkt = 3
            cnt+=1
        elif pkt.pkt_type == 4:
            if pkt.ack in sending_window:
                sending_window.remove(pkt.ack)
            elif len(sending_window)>0 and pkt.ack < min(sending_window):
                sending_window.clear()
            if last_pkt == 3:
                winsize_logger.info(f"{len(sending_window)}")
                last_pkt = 4
        else:
            sending_window.clear()

        if pkt.pkt_type==3 and cnt==150 and not dropped:
            winsize_logger.info("Packet Dropped!")
            dropped = True
            continue

        send_queue.put(pkt)

def normal_handler(recv_queue, send_queue):
    start_time = time.time()
    while True:
        try:
            pkt = recv_queue.get(timeout=0.01)
        except:
            continue
        send_queue.put(pkt)