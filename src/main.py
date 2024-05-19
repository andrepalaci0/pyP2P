import sys
import socket
import threading

class Peer:
    def __init__(self, host, port, neighbors=None):
        self.host = host
        self.port = int(port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.neighbors = neighbors if neighbors else []
        self.connections = []

        if self.neighbors:
            self.connect_to_neighbors()

    def connect_to_neighbors(self):
        for neighbor in self.neighbors:
            peer_host, peer_port = neighbor.split(":")
            peer_port = int(peer_port)
            try:
                self.connect(peer_host, peer_port)
            except Exception as e:
                print(f"Failed to connect to neighbor {peer_host}:{peer_port}: {e}")

    def connect(self, peer_host, peer_port):
        conn = socket.create_connection((peer_host, peer_port))
        self.connections.append(conn)
        print(f"Connected to {peer_host}:{peer_port}")

    def listen(self):
        self.socket.bind((self.host, self.port))
        self.socket.listen(10)
        print(f"Listening for connections on {self.host}:{self.port}")

        while True:
            conn, address = self.socket.accept()
            self.connections.append(conn)
            print(f"Accepted connection from {address}")
            threading.Thread(target=self.handle_client, args=(conn, address)).start()

    def send_data(self, data):
        for conn in self.connections:
            try:
                conn.sendall(data.encode())
            except socket.error as e:
                print(f"Failed to send data. Error: {e}")
                self.connections.remove(conn)

    def handle_client(self, conn, address):
        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    break
                print(f"Received data from {address}: {data.decode()}")
            except socket.error:
                break

        print(f"Connection from {address} closed.")
        self.connections.remove(conn)
        conn.close()

    def start(self):
        listen_thread = threading.Thread(target=self.listen)
        listen_thread.start()

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
 