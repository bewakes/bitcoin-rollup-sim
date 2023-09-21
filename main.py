from multiprocessing import Process, Manager

from bitcoin_rollup_sim.node import WalletNode, MinerNode, Node


def main():
    node_types = [Node, MinerNode, WalletNode, Node, WalletNode]
    with Manager() as manager:
        peers = manager.dict()

        processes = []
        for nodecls in node_types:
            node = nodecls()
            peers[node.nid] = node.port
            p = Process(target=node.run, args=(peers,))
            processes.append(p)

        for p in processes:
            p.start()

        for p in processes:
            p.join()


if __name__ == "__main__":
    main()
