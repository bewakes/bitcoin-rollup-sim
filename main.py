import time
import random
from multiprocessing import Process, Manager

from bitcoin_rollup_sim.node import WalletNode, MinerNode, Node


def main():
    node_types = [
        Node,
        WalletNode,
        MinerNode,
        # For now last node should be miner as it will have all others as peers
        # and send info to others after mining a block
    ]
    with Manager() as manager:
        peers = manager.dict()

        processes = []
        for nodecls in node_types:
            node = nodecls(peers=peers)
            peers[node.nid] = node.port
            p = Process(target=node.run)
            processes.append(p)
            time.sleep(random.randrange(1, 5))

        for p in processes:
            p.start()

        for p in processes:
            p.join()


if __name__ == "__main__":
    main()
