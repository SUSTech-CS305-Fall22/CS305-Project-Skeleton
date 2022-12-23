import grader
import time
import pickle
import hashlib
import pytest
import os
import concurrency_visualizer

'''
This test examines the basic function of your concurrency.
Peer1 will be downloading chunk2,3 from Peer2, 3 concurrently.

This test will be running with network simulator, with topology test/tmp3/topo3.map. You can assume there will not be
packet loss in this test. The script will check if you can correctly download all chunks, and it will generate a concurrency_analysis plot
which will be checked on presentation.

.fragment files:
data3-1.fragment: chunk1
data3-2.fragment: chunk2
data3-3.fragment: chunk3

This testing script is equivalent to run the following commands in different shells (remember to export SIMULATOR):

perl util/hupsim.pl -m test/tmp3/topo3.map -n test/tmp3/nodes3.map -p {port_number} -v 3


python3 src/peer.py -p test/tmp3/nodes3.map -c test/tmp3/data3-1.fragment -m 100 -i 1 -t 60
DOWNLOAD test/tmp3/download_target3.chunkhash test/tmp3/download_result.fragment


python3 src/peer.py -p test/tmp3/nodes3.map -c test/tmp3/data3-2.fragment -m 100 -i 2 -t 60


python3 src/peer.py -p test/tmp3/nodes3.map -c test/tmp3/data3-3.fragment -m 100 -i 3 -t 60
'''

@pytest.fixture(scope='module')
def concurrent_session():
    success = False
    time_max = 80
    if os.path.exists("test/tmp3/download_result.fragment"):
        os.remove("test/tmp3/download_result.fragment")

    stime = time.time()
    concurrent_session = grader.GradingSession(grader.normal_handler, latency=0.01, spiffy=True)
    concurrent_session.add_peer(1, "src/peer.py", "test/tmp3/nodes3.map", "test/tmp3/data3-1.fragment", 100, ("127.0.0.1", 48001))
    concurrent_session.add_peer(2, "src/peer.py", "test/tmp3/nodes3.map", "test/tmp3/data3-2.fragment", 100, ("127.0.0.1", 48002))
    concurrent_session.add_peer(3, "src/peer.py", "test/tmp3/nodes3.map", "test/tmp3/data3-3.fragment", 100, ("127.0.0.1", 48003))
    concurrent_session.run_grader()

    concurrent_session.peer_list[("127.0.0.1", 48001)].send_cmd('''DOWNLOAD test/tmp3/download_target3.chunkhash test/tmp3/download_result.fragment\n''')

    while True:
        if os.path.exists("test/tmp3/download_result.fragment"):
            success = True
            break
        elif time.time()-stime>time_max:
            # Reached max transmission time, abort
            success = False
            break 

        time.sleep(0.5)
        
    for p in concurrent_session.peer_list.values():
        p.terminate_peer()
    
    return concurrent_session, success

def test_finish(concurrent_session):
    session, success = concurrent_session
    assert success == True, "Fail to complete transfer or timeout"

def test_content():
    with open("test/tmp3/download_result.fragment", "rb") as download_file:
        download_fragment = pickle.load(download_file)

    target_hash = ["45acace8e984465459c893197e593c36daf653db", "3b68110847941b84e8d05417a5b2609122a56314"]

    for th in target_hash:
        assert th in download_fragment, f"download hash mismatch, target: {th}, has: {download_fragment.keys()}"

        sha1 = hashlib.sha1()
        sha1.update(download_fragment[th])
        received_hash_str = sha1.hexdigest()
        assert th.strip() == received_hash_str.strip(), f"received data mismatch, expect hash: {target_hash}, actual: {received_hash_str}"

def test_concurrency_vis():
    concurrency_visualizer.analyze("log/peer1.log")
    assert "This will be checked on your presentation" == "This will be checked on your presentation"

