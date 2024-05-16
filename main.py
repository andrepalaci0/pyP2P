

import sys
import client
import server

import socket
import threading

#127.0.0.0 a 127.255.255.255

#localhost da minha maquina:
#127.0.1.1
#172.115.5.198 

class Peer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.neighbors = []

    def connect(self, peer_host, peer_port):
        conn = socket.create_connection((peer_host, peer_port))
        self.neighbors.append(conn)
        print(f"Connected to {peer_host}:{peer_port}")

    def listen(self):
        self.socket.bind((self.host, self.port))
        self.socket.listen(10)
        print(f"Listening for connections on {self.host}:{self.port}")

        while True:
            conn, address = self.socket.accept()
            self.neighbors.append(conn)
            print(f"Accepted connection from {address}")
            threading.Thread(target=self.handle_client, args=(conn, address)).start()

    def send_data(self, data):
        for conn in self.neighbors:
            try:
                conn.sendall(data.encode())
            except socket.error as e:
                print(f"Failed to send data. Error: {e}")
                self.neighbors.remove(conn)

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
        self.neighbors.remove(conn)
        conn.close()

    def start(self):
        listen_thread = threading.Thread(target=self.listen)
        listen_thread.start()

  
    

if __name__ == "__main__":

    
    if len(sys.argv) < 3:
        print("USO: python3 main.py  <addr:port> <file.txt>")
        sys.exit(1)
    
    
    
    fulladdr = sys.argv[1] 
    fulladdr.split(":")
    addr = fulladdr[0]
    port = fulladdr[1]
    print("addr: ", addr)
    print("port: ", port)
    neighbors_path = sys.argv[2]
    
    
    data = {}
    try:
        with open(neighbors_path, 'r') as file:
            for line in file:
                name, value = line.strip().split()
                data[name] = int(value)
    except FileNotFoundError:
        print("Arquivo não encontrado:", neighbors_path, "confira se o path está certa certo")
        
    neighbors = data
    print(neighbors)
        

    
    
   
    