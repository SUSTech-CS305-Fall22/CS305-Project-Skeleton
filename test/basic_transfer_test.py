import grader
import time
import pytest
import pickle
import hashlib
import os

'''
This test examines the basic function of your RDT and congestion control.
There will be a packet loss around #150
Your peer should retransmit and receive the entire data correctly and dump them to serialized dict.
To show your congestion control implementation, you need to plot your sending window size change in a plot similar to the one in
the document.
If you can pass RDT test, you will gain 10 points.
Congestion control will be inspected by humans on your presentation day. If you show the correct implementation of congestion control,
You will get 12 points. 22 in total.
However, note that this is just a sanity test. Passing this test does *NOT* guarantee your correctness in comprehensive tests.

.fragment file:
data1.fragment: chunk 1,2
data2.fragment: chunk 3,4

This test is equivalent to run (except for packet loss):
In shell1:
python3 src/peer.py -p test/tmp2/nodes2.map -c test/tmp2/data1.fragment -m 1 -i 1 -t 60

In shell2:
python3 src/peer.py -p test/tmp2/nodes2.map -c test/tmp2/data2.fragment -m 1 -i 2 -t 60

In shell1:
DOWNLOAD test/tmp2/download_target.chunkhash test/tmp2/download_result.fragment
'''

@pytest.fixture(scope='module')
def drop_session():
    success = False
    time_max = 80

    if os.path.exists("test/tmp2/download_result.fragment"):
        os.remove("test/tmp2/download_result.fragment")

    stime = time.time()
    drop_session = grader.GradingSession(grader.drop_handler, latency=0.01)
    drop_session.add_peer(1, "src/peer.py", "test/tmp2/nodes2.map", "test/tmp2/data1.fragment", 1, ("127.0.0.1", 48001))
    drop_session.add_peer(2, "src/peer.py", "test/tmp2/nodes2.map", "test/tmp2/data2.fragment", 1, ("127.0.0.1", 48002))
    drop_session.run_grader()

    drop_session.peer_list[("127.0.0.1", 48001)].send_cmd('''DOWNLOAD test/tmp2/download_target.chunkhash test/tmp2/download_result.fragment\n''')


    while True:
        if os.path.exists("test/tmp2/download_result.fragment"):
            success = True
            break
        elif time.time()-stime>time_max:
            # Reached max transmission time, abort
            success = False
            break 

        time.sleep(0.1)
        
    
    for p in drop_session.peer_list.values():
        p.terminate_peer()
    
    return drop_session, success

def test_finish(drop_session):
    session, success = drop_session
    assert success == True, "Fail to complete transfer or timeout"

def test_rdt(drop_session):
    assert os.path.exists("test/tmp2/download_result.fragment"), "no downloaded file"

    with open("test/tmp2/download_result.fragment", "rb") as download_file:
        download_fragment = pickle.load(download_file)
    target_hash = "3b68110847941b84e8d05417a5b2609122a56314"

    assert target_hash in download_fragment, f"download hash mismatch, target: {target_hash}, has: {download_fragment.keys()}"

    sha1 = hashlib.sha1()
    sha1.update(download_fragment[target_hash])
    received_hash_str = sha1.hexdigest()

    assert target_hash.strip() == received_hash_str.strip(), f"received data mismatch, expect hash: {target_hash}, actual: {received_hash_str}" 