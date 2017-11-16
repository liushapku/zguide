"""
Clone client Model Two

Author: Min RK <benjaminrk@gmail.com>

"""

import time

import zmq

from kvsimple import KVMsg, dump_all

def main():

    # Prepare our context and subscriber
    ctx = zmq.Context()
    snapshot = ctx.socket(zmq.DEALER)
    snapshot.linger = 0
    snapshot.connect("tcp://localhost:5556")
    subscriber = ctx.socket(zmq.SUB)
    subscriber.linger = 0
    subscriber.setsockopt(zmq.SUBSCRIBE, b'')
    subscriber.connect("tcp://localhost:5557")

    kvmap = {}

    # Get state snapshot
    sequence = 0
    snapshot.send(b"ICANHAZ?")
    while True:
        try:
            kvmsg = KVMsg.recv(snapshot)
        except:
            break;          # Interrupted

        if kvmsg.key == b"KTHXBAI":
            sequence = kvmsg.sequence
            print("Received snapshot=%d" % sequence)
            break          # Done
        kvmsg.store(kvmap)

    # Now apply pending updates, discard out-of-sequence messages
    while True:
        try:
            kvmsg = KVMsg.recv(subscriber)
        except:
            break          # Interrupted
        if kvmsg.sequence > sequence:
            sequence = kvmsg.sequence
            kvmsg.store(kvmap)
        else:
            print('dropped duplicates', kvmsg.sequence)
    print('quiting')
    dump_all(kvmap, 'sub.txt')

if __name__ == '__main__':
    main()
