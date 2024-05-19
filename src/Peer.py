import socket
import threading
import time

class Peer:
    def __init__(self, host, port, neighbors=None, key_values=None):
        self.host = host
        self.port = int(port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.neighbors = neighbors if neighbors else []
        self.connections = []
        self._stop_event = threading.Event()
        self.key_values = key_values if key_values else {}
        self.ttl = 100 
        self.seqno = 0


    def connect_to_neighbors(self):
        for neighbor in self.neighbors[:]:
            peer_host, peer_port = neighbor.split(":")
            peer_port = int(peer_port)
            try:
                self.connect(peer_host, peer_port)
            except Exception as e:
                print(f"Failed to connect to neighbor {peer_host}:{peer_port}: {e}")
                self.neighbors.remove(neighbor)

    def connect(self, peer_host, peer_port):
        time.sleep(0.5)
        conn = socket.create_connection((peer_host, peer_port))
        self.connections.append((peer_host, peer_port, conn))
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
                    self.connections.append((address[0], address[1], conn))
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

    def send_data(self, data, conn):
        try:
            conn.sendall(data.encode())
        except socket.error as e:
            print(f"Failed to send data. Error: {e}")
            for peer_host, peer_port, c in self.connections:
                if c == conn:
                    self.connections.remove((peer_host, peer_port, conn))
                    self.neighbors = [neighbor for neighbor in self.neighbors if neighbor != f"{peer_host}:{peer_port}"]

    def handle_client(self, conn, address):
        try:
            while not self._stop_event.is_set():
                try:
                    data = conn.recv(1024)
                    if not data:
                        break
                    message = data.decode()
                    self.handle_message(message, conn)
                except socket.error:
                    break
        finally:
            print(f"Connection from {address} closed.")
            self.connections.remove((address[0], address[1], conn))
            self.neighbors = [neighbor for neighbor in self.neighbors if neighbor != f"{address[0]}:{address[1]}"]
            conn.close()

    def handle_message(self, message, conn):
        parts = message.strip().split(' ', 3)  # Split the message into up to 4 parts
        if len(parts) < 4:
            print("Invalid message format")
            return

        origin, seqno, ttl, operation_and_args = parts
        operation_parts = operation_and_args.split(' ', 1)
        operation = operation_parts[0]
        args = operation_parts[1] if len(operation_parts) > 1 else ""

        print(f"Received message from {origin}: SeqNo: {seqno}, TTL: {ttl}, Operation: {operation}, Args: {args}")

        if operation == "HELLO":
            self.handle_hello(origin)

    def handle_hello(self, origin):
        if origin not in self.neighbors:
            self.neighbors.append(origin)
            print(f"Adicionando vizinho na tabela: {origin}")
        else:
            print(f"Vizinho ja esta na tabela: {origin}")

    def handle_command(self):
        while True:
            command = input("Escolha o comando\n[0] Listar vizinhos\n[1] HELLO\n[2] SEARCH (flooding)\n[3] SEARCH (random walk)\n[4] SEARCH (busca em profundidade)\n[5] Estatisticas\n[6] Alterar valor padrao de TTL\n[9] Sair: ")
            if command == '9':
                self.leaves_network()
                break
            self.call_command(command)

    def stop(self):
        self._stop_event.set()  # Signal the thread to stop
        for _, _, conn in self.connections:
            try:
                conn.shutdown(socket.SHUT_RDWR)  # Disable further send and receive operations
                conn.close()
            except socket.error as e:
                print(f"Error closing connection: {e}")
        self.socket.close()


    def hello(self):
        self.list_neighbors()
        if not self.neighbors:
            print("No neighbors to send HELLO to.")
            return

        neighbor_index = int(input("Escolha o vizinho: "))
        if neighbor_index < 0 or neighbor_index >= len(self.neighbors):
            print("Invalid neighbor index.")
            return

        neighbor = self.neighbors[neighbor_index]
        peer_host, peer_port = neighbor.split(":")
        peer_port = int(peer_port)

        message = f"{self.host}:{self.port} {self.seqno} 1 HELLO"
        self.seqno += 1

        for conn_host, conn_port, conn in self.connections:
            if conn_host == peer_host and conn_port == peer_port:
                print(f"Encaminhando mensagem \"{message}\" para {peer_host}:{peer_port}")
                self.send_data(message, conn)
                print(f"Envio feito com sucesso: \"{message}\"")
                return

        print(f"Connection to {peer_host}:{peer_port} not found.")

    def search_flooding(self):
        pass

    def search_walk(self):
        pass

    def search_depth(self):
        pass

    def stats(self):
        pass

    def change_ttl(self):
        aux = int(input("Digite o novo valor de TTL: "))
        if aux < 1:
            print("Valor de TTL invalido")
            return
        self.ttl = aux
        print(f"Novo valor de TTL: {self.ttl}")
        

    def list_neighbors(self):
        print(f"Ha {len(self.neighbors)} vizinhos na tabela:")
        for index, neighbor in enumerate(self.neighbors):
            peer_host, peer_port = neighbor.split(":")
            print(f"[{index}] {peer_host} {peer_port}")

    def leaves_network(self):
        self.stop()


    def call_command(self, input):
        commands = {
            '0': self.list_neighbors,
            '1': self.hello,
            '2': self.search_flooding,
            '3': self.search_walk,
            '4': self.search_depth,
            '5': self.stats,
            '6': self.change_ttl,
            '9': self.leaves_network
        }
        default = lambda: print("\nOPCAO INVALIDA")
        commands.get(input, default)()

    def start(self):
        listen_thread = threading.Thread(target=self.listen)
        listen_thread.start()
        self.connect_to_neighbors()

        command_thread = threading.Thread(target=self.handle_command)
        command_thread.start()
