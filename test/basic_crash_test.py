import grader
import time
import pickle
import hashlib
import pytest
import os

'''
This test examines the basic function of your robustness.
Peer1 will be downloading chunk2 from Peer2, then peer2 will crash in the dowloading process. Peer1 should be able to download from peer3.

This test will be running with network simulator, with topology test/tmp4/topo4.map. 

.fragment files:
data4-1.fragment: chunk1
data4-2.fragment: chunk2

This testing script is equivalent to run the following commands in different shells (remember to export SIMULATOR in each shell):

perl util/hupsim.pl -m test/tmp4/topo3.map -n test/tmp4/nodes4.map -p {port_number} -v 3


python3 src/peer.py -p test/tmp4/nodes4.map -c test/tmp4/data4-1.fragment -m 100 -i 1
DOWNLOAD test/tmp4/download_target4.chunkhash test/tmp4/download_result.fragment


python3 src/peer.py -p test/tmp4/nodes4.map -c test/tmp4/data4-2.fragment -m 100 -i 2
(CTRL+C to terminate peer2 after 1 seconds)


python3 src/peer.py -p test/tmp4/nodes4.map -c test/tmp4/data4-2.fragment -m 100 -i 3
'''

@pytest.fixture(scope='module')
def crash_session():
    success = False
    time_max = 80
    if os.path.exists("test/tmp4/download_result.fragment"):
        os.remove("test/tmp4/download_result.fragment")

    stime = time.time()
    crash_session = grader.GradingSession(grader.normal_handler, latency=0.01, spiffy=True, topo_map="test/tmp4/topo4.map", nodes_map="test/tmp4/nodes4.map")
    crash_session.add_peer(1, "src/peer.py", "test/tmp4/nodes4.map", "test/tmp4/data4-1.fragment", 100, ("127.0.0.1", 48001), timeout=None)
    crash_session.add_peer(2, "src/peer.py", "test/tmp4/nodes4.map", "test/tmp4/data4-2.fragment", 100, ("127.0.0.1", 48002), timeout=None)
    crash_session.add_peer(3, "src/peer.py", "test/tmp4/nodes4.map", "test/tmp4/data4-2.fragment", 100, ("127.0.0.1", 48003), timeout=None)
    crash_session.run_grader()

    crash_session.peer_list[("127.0.0.1", 48001)].send_cmd('''DOWNLOAD test/tmp4/download_target4.chunkhash test/tmp4/download_result.fragment\n''')

    time.sleep(1)
    # crash peer2
    crash_session.peer_list[("127.0.0.1", 48002)].terminate_peer()

    while True:
        if os.path.exists("test/tmp4/download_result.fragment"):
            success = True
            break
        elif time.time()-stime>time_max:
            # Reached max transmission time, abort
            success = False
            break 

        time.sleep(0.5)
        
    for p in crash_session.peer_list.values():
        if p.process != None:
            p.terminate_peer()
    
    return crash_session, success

def test_finish(crash_session):
    session, success = crash_session
    assert success == True, "Fail to complete transfer or timeout"

def test_content():
    with open("test/tmp4/download_result.fragment", "rb") as download_file:
        download_fragment = pickle.load(download_file)

    target_hash = ["45acace8e984465459c893197e593c36daf653db"]

    for th in target_hash:
        assert th in download_fragment, f"download hash mismatch, target: {th}, has: {download_fragment.keys()}"

        sha1 = hashlib.sha1()
        sha1.update(download_fragment[th])
        received_hash_str = sha1.hexdigest()
        assert th.strip() == received_hash_str.strip(), f"received data mismatch, expect hash: {target_hash}, actual: {received_hash_str}"

