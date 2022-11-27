import grader
import time
import pytest

@pytest.fixture(scope='module')
def normal_session():
    blocking_time = 10
    handshaking_session = grader.GradingSession(grader.normal_handler)
    handshaking_session.add_peer(1, "src/peer.py", "test/tmp1/nodes1.map", "test/tmp1/data1.fragment", 1, ("127.0.0.1", 48001))
    handshaking_session.add_peer(2, "src/peer.py", "test/tmp1/nodes1.map", "test/tmp1/data1.fragment", 1, ("127.0.0.1", 48002))
    handshaking_session.add_peer(3, "src/peer.py", "test/tmp1/nodes1.map", "test/tmp1/data1.fragment", 1, ("127.0.0.1", 48003))
    handshaking_session.add_peer(4, "src/peer.py", "test/tmp1/nodes1.map", "test/tmp1/data1.fragment", 1, ("127.0.0.1", 48004))
    handshaking_session.add_peer(5, "src/peer.py", "test/tmp1/nodes1.map", "test/tmp1/data1.fragment", 1, ("127.0.0.1", 48005))
    handshaking_session.add_peer(6, "src/peer.py", "test/tmp1/nodes1.map", "test/tmp1/data1.fragment", 1, ("127.0.0.1", 48006))
    handshaking_session.add_peer(7, "src/peer.py", "test/tmp1/nodes1.map", "test/tmp1/data1.fragment", 1, ("127.0.0.1", 48007))
    handshaking_session.run_grader()

    handshaking_session.peer_list[("127.0.0.1", 48001)].send_cmd('''DOWNLOAD test/tmp1/download_target.chunkhash test/tmp1/download_result.fragment\n''')
    time.sleep(blocking_time)
    
    for p in handshaking_session.peer_list.values():
        p.terminate_peer()
    
    return handshaking_session

def test_flooding_whohas(normal_session):
    handshaking_session = normal_session
    for i in range(48002, 48008):
        assert handshaking_session.peer_list[("127.0.0.1", 48001)].send_record[("127.0.0.1", i)][0] == 1, f"Fail to send WHOHAS to {i}"

def test_send_ihave(normal_session):
    handshaking_session = normal_session
    assert handshaking_session.peer_list[("127.0.0.1", 48002)].send_record[("127.0.0.1", 48001)][1] > 0, "Fail to send IHAVE"

def test_send_download(normal_session):
    handshaking_session = normal_session
    assert handshaking_session.peer_list[("127.0.0.1", 48001)].send_record[("127.0.0.1", 48002)][2] > 0, "Fail to send DOWLOAD"

def test_handshaking(normal_session):
    handshaking_session = normal_session
    assert handshaking_session.peer_list[("127.0.0.1", 48002)].recv_record[("127.0.0.1", 48001)][0] > 0, "Fail to receive any WHOHAS"
    assert handshaking_session.peer_list[("127.0.0.1", 48001)].recv_record[("127.0.0.1", 48002)][1] > 0, "Fail to receive any IHAVE"
    assert handshaking_session.peer_list[("127.0.0.1", 48002)].recv_record[("127.0.0.1", 48001)][2] > 0, "Fail to receive any DOWNLOAD"
    assert handshaking_session.peer_list[("127.0.0.1", 48001)].recv_record[("127.0.0.1", 48002)][3] > 0, "Fail to receive any DATA"
    assert handshaking_session.peer_list[("127.0.0.1", 48002)].recv_record[("127.0.0.1", 48001)][4] > 0, "Fail to receive any ACK"