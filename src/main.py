import sys
import socket
import threading

from Peer import Peer



if __name__ == "__main__":
    neighbors = None
    key_value_pairs = {}

    if len(sys.argv) < 2:
        print("USO: python3 src/main.py <addr:port> [<neighbors.txt> [<lista_chave_valor.txt>]]")
        sys.exit(1)

    if len(sys.argv) >= 3:
        neighbors_path = sys.argv[2]
        try:
            with open(neighbors_path, 'r') as file:
                neighbors = [line.strip() for line in file]
        except FileNotFoundError:
            print(f"Arquivo de vizinhos não encontrado: {neighbors_path}")
            sys.exit(1)

    if len(sys.argv) == 4:
        key_value_path = sys.argv[3]
        try:
            with open(key_value_path, 'r') as file:
                for line in file:
                    key, value = line.strip().split()
                    key_value_pairs[key] = value
        except FileNotFoundError:
            print(f"Arquivo de chave-valor não encontrado: {key_value_path}")
            sys.exit(1)
        except ValueError:
            print(f"Formato inválido no arquivo de chave-valor: {key_value_path}")
            sys.exit(1)


    fulladdr = sys.argv[1]
    addr, port = fulladdr.split(":")
    port = int(port)

    node = Peer(addr, port, neighbors)
    node.start()
 