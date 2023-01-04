import grader
import time
import pickle
import hashlib
import pytest
import os
import shutil
"""
Initial fragments:

data5-1: chunk 1,2
data5-2: chunk 3,4
data5-3: chunk 5,6
data5-4: chunk 7,8
data5-5: chunk 9,10
data5-6: chunk 11,13,15
data5-7: chunk 12,14,16
data5-8: chunk 17,18,19,20

-----------------------------
Targets:
# target#: chunks

target1: 4

target2: 7,12

target3: 11

target4: 8,16

-----------------------------
This testing script is equivalent to run the following commands in different shells (remember to export SIMULATOR in each shell):
Enter DOWNLOAD command after all peers run

perl util/hupsim.pl -m test/tmp5/topo5.map -n test/tmp5/nodes5.map -p {port_number} -v 3

python3 src/peer.py -p test/tmp5/nodes5.map -c test/tmp5/fragments/data5-1.fragment -m 100 -i 1
DOWNLOAD test/tmp5/targets/target1.chunkhash test/tmp5/results/result1.fragment

python3 src/peer.py -p test/tmp5/nodes5.map -c test/tmp5/fragments/data5-2.fragment -m 100 -i 2

python3 src/peer.py -p test/tmp5/nodes5.map -c test/tmp5/fragments/data5-3.fragment -m 100 -i 7
DOWNLOAD test/tmp5/targets/target2.chunkhash test/tmp5/results/result2.fragment

python3 src/peer.py -p test/tmp5/nodes5.map -c test/tmp5/fragments/data5-4.fragment -m 100 -i 14

python3 src/peer.py -p test/tmp5/nodes5.map -c test/tmp5/fragments/data5-5.fragment -m 100 -i 10
DOWNLOAD test/tmp5/targets/target3.chunkhash test/tmp5/results/result3.fragment

python3 src/peer.py -p test/tmp5/nodes5.map -c test/tmp5/fragments/data5-6.fragment -m 100 -i 15

python3 src/peer.py -p test/tmp5/nodes5.map -c test/tmp5/fragments/data5-7.fragment -m 100 -i 12

python3 src/peer.py -p test/tmp5/nodes5.map -c test/tmp5/fragments/data5-8.fragment -m 100 -i 13
DOWNLOAD test/tmp5/targets/target4.chunkhash test/tmp5/results/result4.fragment


The default tasks in this file may run around 100s. Note that there will be packet loss in the simulator.
-----------------------------
You can design your own networks and tasks using this scripts!
And you can visualize your network using net-visual.py

"""

@pytest.fixture(scope='module')
def advance_session():
    success = False
    time_max = 640
    if os.path.exists("test/tmp5/results"):
        shutil.rmtree("test/tmp5/results", ignore_errors=True)
        os.mkdir("test/tmp5/results")

    stime = time.time()
    advance_session = grader.GradingSession(grader.normal_handler, latency=0.01, spiffy=True, topo_map="test/tmp5/topo5.map", nodes_map="test/tmp5/nodes5.map")
    advance_session.add_peer(1, "src/peer.py", "test/tmp5/nodes5.map", "test/tmp5/fragments/data5-1.fragment", 100, ("127.0.0.1", 48001))
    advance_session.add_peer(2, "src/peer.py", "test/tmp5/nodes5.map", "test/tmp5/fragments/data5-2.fragment", 100, ("127.0.0.1", 48002))
    advance_session.add_peer(7, "src/peer.py", "test/tmp5/nodes5.map", "test/tmp5/fragments/data5-3.fragment", 100, ("127.0.0.1", 48003))
    advance_session.add_peer(14, "src/peer.py", "test/tmp5/nodes5.map", "test/tmp5/fragments/data5-4.fragment", 100, ("127.0.0.1", 48004))
    advance_session.add_peer(10, "src/peer.py", "test/tmp5/nodes5.map", "test/tmp5/fragments/data5-5.fragment", 100, ("127.0.0.1", 48005))
    advance_session.add_peer(15, "src/peer.py", "test/tmp5/nodes5.map", "test/tmp5/fragments/data5-6.fragment", 100, ("127.0.0.1", 48006))
    advance_session.add_peer(12, "src/peer.py", "test/tmp5/nodes5.map", "test/tmp5/fragments/data5-7.fragment", 100, ("127.0.0.1", 48007))
    advance_session.add_peer(13, "src/peer.py", "test/tmp5/nodes5.map", "test/tmp5/fragments/data5-8.fragment", 100, ("127.0.0.1", 48008))
    advance_session.run_grader()

    advance_session.peer_list[("127.0.0.1", 48001)].send_cmd('''DOWNLOAD test/tmp5/targets/target1.chunkhash test/tmp5/results/result1.fragment\n''')
    advance_session.peer_list[("127.0.0.1", 48003)].send_cmd('''DOWNLOAD test/tmp5/targets/target2.chunkhash test/tmp5/results/result2.fragment\n''')
    advance_session.peer_list[("127.0.0.1", 48005)].send_cmd('''DOWNLOAD test/tmp5/targets/target3.chunkhash test/tmp5/results/result3.fragment\n''')
    advance_session.peer_list[("127.0.0.1", 48008)].send_cmd('''DOWNLOAD test/tmp5/targets/target4.chunkhash test/tmp5/results/result4.fragment\n''')


    while True:
        if os.path.exists("test/tmp5/results/result1.fragment") and os.path.exists("test/tmp5/results/result2.fragment")\
             and os.path.exists("test/tmp5/results/result3.fragment") and os.path.exists("test/tmp5/results/result4.fragment"):
            success = True
            break
        elif time.time()-stime>time_max:
            # Reached max transmission time, abort
            success = False
            break 

        time.sleep(1)
        
    for p in advance_session.peer_list.values():
        p.terminate_peer()
    
    return advance_session, success

def test_finish(advance_session):
    session, success = advance_session
    assert success == True, "Fail to complete transfer or timeout"

def test_content():
    check_target_result("test/tmp5/targets/target1.chunkhash", "test/tmp5/results/result1.fragment")
    check_target_result("test/tmp5/targets/target2.chunkhash", "test/tmp5/results/result2.fragment")
    check_target_result("test/tmp5/targets/target3.chunkhash", "test/tmp5/results/result3.fragment")
    check_target_result("test/tmp5/targets/target4.chunkhash", "test/tmp5/results/result4.fragment")

def check_target_result(target_file, result_file):
    target_hash = []
    with open(target_file, "r") as tf:
        while True:
            line = tf.readline()
            if not line:
                break
            index, hash_str = line.split(" ")
            hash_str = hash_str.strip()
            target_hash.append(hash_str)

    with open(result_file, "rb") as rf:
        result_fragments = pickle.load(rf)

    for th in target_hash:
        assert th in result_fragments, f"download hash mismatch for target {target_file}, target: {th}, has: {result_fragments.keys()}"

        sha1 = hashlib.sha1()
        sha1.update(result_fragments[th])
        received_hash_str = sha1.hexdigest()
        assert th.strip() == received_hash_str.strip(), f"received data mismatch for target {target_file}, expect hash: {target_hash}, actual: {received_hash_str}"