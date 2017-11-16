"""
Clone server Model One

"""

import random
import time

import zmq

from kvsimple import KVMsg, dump_all

def main():
    # Prepare our context and publisher socket
    ctx = zmq.Context()
    publisher = ctx.socket(zmq.PUB)

    publisher.bind("tcp://*:5556")
    time.sleep(0.2)

    sequence = 0
    random.seed(time.time())
    kvmap = {}

    try:
        while True:
            # Distribute as key-value message
            sequence += 1
            kvmsg = KVMsg(sequence)
            kvmsg.key = ("%4d" % random.randint(0,9999)).encode()
            kvmsg.body = ("%6d" % random.randint(0,999999)).encode()
            kvmsg.send(publisher)
            kvmsg.store(kvmap)
            time.sleep(0.1)
    except KeyboardInterrupt:
        print (" Interrupted\n%d messages out" % sequence)
        dump_all(kvmap, 'pub.txt')


if __name__ == '__main__':
    main()
