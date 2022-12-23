from datetime import datetime
import matplotlib.pyplot as plt
import re
import argparse

fmt = "%Y-%m-%d %H:%M:%S,%f"
pattern = r".*\('127.0.0.1', (\d*)\).*"

def str2time(tstr: str) -> float:
    return datetime.strptime(tstr, fmt).timestamp()

def log2port(logstr: str) -> int:
    match = re.match(pattern, logstr)
    return int(match.group(1))

def analyze(file):
    sessions = dict()
    start_time = 0

    with open(file, "r") as f:
        first_line = f.readline()
        start_info = first_line.split("-+-")
        start_time = str2time(start_info[0].strip())*1000

        while True:
            line = f.readline()
            if not line:
                break
            info = line.split("-+-")
            if info[2].strip() != "DEBUG" or "sending" in line:
                continue
            
            # print(info)
            session_port = log2port(info[3].strip())
            pkt_time = str2time(info[0].strip())*1000 - start_time
            if session_port not in sessions:
                sessions[session_port] = []
                pkt_cnt = [0]
                time_cnt = [pkt_time]
                sessions[session_port].append(time_cnt)
                sessions[session_port].append(pkt_cnt)
            else:
                sessions[session_port][0].append(pkt_time)
                sessions[session_port][1].append(sessions[session_port][1][-1]+1)

    # print(sessions)
    plt.figure()
    for port, record in sessions.items():
        plt.plot(record[0], record[1], ",", markersize=0.1)


    plt.legend(list(sessions.keys()))
    plt.xlabel("Time Since Start (ms)")
    plt.ylabel("Stream")
    plt.savefig("concurrency_analysis.png")

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('file', type=str, help='log file to visualize')
    args = parser.parse_args()
    file = args.file
    analyze(file)