import sys
import socket
import threading

from Peer import Peer



if __name__ == "__main__":
    neighbors = None

    if len(sys.argv) < 2:
        print("USO: python3 src/main.py <addr:port> [<neighbors.txt>]")
        sys.exit(1)
    if len(sys.argv) == 3:
        neighbors_path = sys.argv[2]
        try:
            with open(neighbors_path, 'r') as file:
                neighbors = [line.strip() for line in file]
        except FileNotFoundError:
            print(f"Arquivo de vizinhos não encontrado: {neighbors_path}")
            sys.exit(1)

    fulladdr = sys.argv[1]
    addr, port = fulladdr.split(":")
    port = int(port)

    node = Peer(addr, port, neighbors)
    node.start()
 