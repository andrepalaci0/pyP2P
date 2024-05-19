import socket
import threading
import time

class Peer:
    def __init__(self, host, port, neighbors=None):
        self.host = host
        self.port = int(port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.neighbors = neighbors if neighbors else []
        self.connections = []
        self._stop_event = threading.Event()

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
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(10)
            print(f"Listening for connections on {self.host}:{self.port}")

            while not self._stop_event.is_set():
                try:
                    self.socket.settimeout(1.0)  # Set a timeout to check the stop event periodically
                    conn, address = self.socket.accept()
                    self.connections.append(conn)
                    print(f"Accepted connection from {address}")
                    threading.Thread(target=self.handle_client, args=(conn, address)).start()
                except socket.timeout:
                    continue
                except OSError as e:
                    if not self._stop_event.is_set():
                        print(f"Error accepting connections: {e}")
                    break
        finally:
            self.socket.close()
            
            
    def send_data(self, data):
        for conn in self.connections:
            try:
                conn.sendall(data.encode())
            except socket.error as e:
                print(f"Failed to send data. Error: {e}")
                self.connections.remove(conn)

    def handle_client(self, conn, address):
        try:
            while not self._stop_event.is_set():
                try:
                    data = conn.recv(1024)
                    if not data:
                        break
                    print(f"Received data from {address}: {data.decode()}")
                except socket.error:
                    break
        finally:
            print(f"Connection from {address} closed.")
            self.connections.remove(conn)
            conn.close()


    def handle_command(self):
        while True:
            command = input("Escolha o comando\n[0] Listar vizinhos\n[1] HELLO\n[2] SEARCH (flooding)\n[3] SEARCH (random walk)\n[4] SEARCH (busca em profundidade)\n[5] Estatisticas\n[6] Alterar valor padrao de TTL\n[9] Sair: ")  
            if command == '9':
                self.leaves_network()
                break
            self.call_command(command)
        
    def stop(self):
        self._stop_event.set()  # Sinaliza para a thread que ela deve parar
        for conn in self.connections:
            conn.close()
        self.socket.close()
   
    def hello(self):
        print("\nHELLO")

    def search_flooding(self):
        pass

    def search_walk(self):
        pass

    def search_depth(self):
        pass

    def stats(self):
        pass

    def change_ttl(self):
        pass
    
    def list_neighbors(self):
        pass

    def leaves_network(self):
        self.stop()
        return True
        
        
    #dicionario que define as funções a serem chamadas de acordo com a opção escolhida
    def call_command(self, input):
        commands = {
            '0': self.list_neighbors,
            '1': self.hello,
            '2': self.search_flooding,
            '3': self.search_walk,
            '4': self.search_depth,
            '5': self.stats,
            '6': self.change_ttl,
            '9': self.leaves
        }
        default = lambda: print("\nOPCAO INVALIDA")
        commands.get(input, default)()

    def start(self):
        listen_thread = threading.Thread(target=self.listen)
        listen_thread.start()
        
        command_thread = threading.Thread(target=self.handle_command)
        command_thread.start()