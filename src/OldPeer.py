import select
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor


class OldPeer:
    def __init__(self, host, port, neighbors=None, key_values=None):
        self.host = host
        self.port = int(port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tobe_neighbors = neighbors if neighbors else []
        self.neighbors = []
        self.connections = []
        self.lock = threading.Lock()
        self._stop_event = threading.Event()
        self.key_values = key_values if key_values else {}
        self.ttl = 100
        self.seqno = 0
        self.waiting_results = {}
        self.search_hops = {}
        self.seen_messages = set()
        self.executor = ThreadPoolExecutor(max_workers=10)
        self._executor_shutdown = threading.Event()  # Event to signal executor shutdown
        self.BUFFER_SIZE = 1024

    def connect(self, peer_host, peer_port):
        time.sleep(0.5)
        conn = socket.create_connection((peer_host, peer_port))
        with self.lock:
            self.connections.append((peer_host, peer_port, conn))
        print(f"Connected to {peer_host}:{peer_port}")

    def listen(self):
        self.socket.bind((self.host, self.port))
        self.socket.listen(10)
        print(f"Listening for connections on {self.host}:{self.port}")
        for neighbor in self.tobe_neighbors:
            self.server_hello(neighbor)
        while not self._stop_event.is_set():
            try:
                self.socket.settimeout(
                    1.0
                )  # Set a timeout to check the stop event periodically
                conn, address = self.socket.accept()
                with self.lock:
                    self.connections.append((address[0], address[1], conn))
                print(f"Accepted connection from {address}")
                if not self._executor_shutdown.is_set():
                    self.executor.submit(self.handle_client, conn, address)
            except socket.timeout:
                continue
                
    def send_data(self, data, neighbor, timeout=5.0):
        try:
            n_addr, n_port = neighbor.split(":")
            with socket.create_connection((n_addr, int(n_port))) as conn:
                conn.sendall(data.encode())
                print(f"Sent message: {data}")
        except socket.error as e:
            print(f"Failed to send data. Error: {e}")
            with self.lock:
                for peer_host, peer_port, c in self.connections:
                    if c == conn:
                        self.connections.remove((peer_host, peer_port, conn))
                        self.neighbors = [neighbor for neighbor in self.neighbors if neighbor!= f"{peer_host}:{peer_port}"]
            return False
        # Wait for OK response without blocking
        if "_OK" in data:
            return True
        readable, _, _ = select.select([conn], [], [], timeout)
        if readable:
            ok_buffer = bytearray(self.BUFFER_SIZE)
            conn.recv_into(ok_buffer, self.BUFFER_SIZE)
            ok_message = ok_buffer.decode().strip()
            
            parts = ok_message.split(' ', 3)
            if len(parts) < 4:
                print("Invalid OK message format")
                return False
            
            origin, seqno, ttl, opname_ok = parts
            if "_OK" in opname_ok:
                print(f"OK recebido: {ok_message}")
                return True
            else:
                print(f"Invalid OK response: {ok_message}")
                return False
        else:
            print(f"OK não recebido")
            return False
    
    def handle_client(self, conn, address):
        try:
            while not self._stop_event.is_set():
                try:
                    data = conn.recv(1024)
                    if not data:
                        break
                    message = data.decode()
                    if message:
                        self.handle_message(message, conn)
                except socket.error as e:
                    print(f"Socket error: {e}")
                    break
        except Exception as e:
            print(f"Error handling client: {e}")
        
    def handle_message(self, message, conn):
        parts = message.strip().split(" ", 3)  
        if len(parts) < 4:
            print("Invalid message format")
            return
        origin, seqno, ttl, operation_and_args = parts
        operation_parts = operation_and_args.split(" ", 1)
        operation = operation_parts[0]
        args = operation_parts[1] if len(operation_parts) > 1 else ""
        print(
            f"Received message from {origin}: SeqNo: {seqno}, TTL: {ttl}, Operation: {operation}, Args: {args}"
        )
        # Check if the message has already been seen
        if (origin, seqno) in self.seen_messages and not operation.endswith("_OK") and operation!= "HELLO":
            print(f"Message from {origin} with seqno {seqno} has already been seen. Ignoring.")
            return
        # Add the message to seen messages if it is not a response or HELLO
        if not operation.endswith("_OK") and operation!= "HELLO":
            self.seen_messages.add((origin, seqno))
        # Check TTL
        ttl = int(ttl)
        if ttl == 0:
            print("TTL reached 0. Dropping message.")
            return
        # Handle the operatio
        if operation == "HELLO":
            self.handle_hello(origin, conn)
        elif operation == "SEARCH":
            self.handle_search_message(origin, seqno, ttl, args, conn)
        elif operation == "VAL":
            args_parts = args.split(" ")
            if len(args_parts) < 4:
                print("Invalid VAL message format")
                return
            key, value, mode, hop_count = args_parts
            self.handle_found_key(origin, seqno, ttl, key, value, mode, hop_count)
        else:
            print(f"Unknown operation: {operation}")

    def handle_search_message(self, origin, seqno, ttl, args, conn):
        message = f"{self.host}:{self.port} {self.seqno} 1 SEARCH_OK"
        self.seqno+=1
        self.send_data(message, conn)
        
        parts = args.split(" ")
        if len(parts) != 4:
            print("Invalid SEARCH message format")
            return

        mode, last_hop_port, key, hop_count = parts
        self.search_hops[key] = last_hop_port
        print(f"Handling SEARCH message: Mode: {mode}, Last Hop Port: {last_hop_port}, Key: {key}, Hop Count: {hop_count}")
    
        # Based on mode, select the appropriate search method
        if mode == "FL":
            self.handle_search_flooding(origin, seqno, ttl, key, hop_count, last_hop_port, conn)
        elif mode == "RW":
            #self.search_random_walk(origin, seqno, ttl, key, hop_count, conn)
            pass
        elif mode == "DS":
            #self.search_depth(origin, seqno, ttl, key, hop_count, conn)
            pass
        else:
            print(f"Unknown SEARCH mode: {mode}")

    
    def handle_hello(self, origin, conn):
        message = f"{self.host}:{self.port} {self.seqno} 1 HELLO_OK"
        if self.send_data(message, conn):
            with self.lock:
                if origin not in self.neighbors:
                    self.neighbors.append(origin)
                    print(f"Adicionando vizinho na tabela: {origin}")
                else:
                    print(f"Vizinho ja esta na tabela: {origin}")
            print(f"Enviando mensagem de resposta para {origin}")
            
    def create_search_message(self, mode, search_key):
        self.seqno+=1
        return f"{self.host}:{self.port} {self.seqno} {self.ttl} SEARCH {mode} {self.port} {search_key} {1}"
    
    def update_search_message(self, message, hop_count):
        parts = message.split(" ")
        parts[2] = str(int(parts[2])-1)
        parts[7] = str(int(hop_count) + 1)
        return f"{parts[0]} {parts[1]} {parts[2]} {parts[3]} {parts[4]} {self.port} {parts[6]} {parts[7]}"

    def handle_command(self):
        while not self._stop_event.is_set():
            command = input(
                "Escolha o comando\n[0] Listar vizinhos\n[1] HELLO\n[2] SEARCH (flooding)\n[3] SEARCH (random walk)\n[4] SEARCH (busca em profundidade)\n[5] Estatisticas\n[6] Alterar valor padrao de TTL\n[9] Sair: "
            )
            if command == "9":
                self.leaves_network()
                break
            self.call_command(command)

    def stop(self):
        self._stop_event.set()  # Signal the listening thread to stop accepting new connections
        with self.lock:
            for _, _, conn in self.connections:
                try:
                    conn.shutdown(
                        socket.SHUT_RDWR
                    )  # Disable further send and receive operations
                    conn.close()
                except socket.error as e:
                    print(f"Error closing connection: {e}")
        self._executor_shutdown.set()  # Signal the executor to stop accepting new tasks
        self.executor.shutdown(wait=True)  # Wait for all tasks to complete
        self.socket.close()  # Close the listening socket

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
        self.seqno+=1
        with self.lock:
            for conn_host, conn_port, conn in self.connections:
                if conn_host == peer_host and conn_port == peer_port:
                    print(
                        f'Encaminhando mensagem "{message}" para {peer_host}:{peer_port}'
                    )
                    self.send_data(message, conn)
                    return
        print(f"Connection to {peer_host}:{peer_port} not found.")

    def server_hello(self, neighbor):
        peer_host, peer_port = neighbor.split(":")
        peer_port = int(peer_port)

        try:
            time.sleep(0.5)
            conn = socket.create_connection((peer_host, peer_port))
            print(f"Connected to {peer_host}:{peer_port}")


            message = f"{self.host}:{self.port} {self.seqno} 1 HELLO"
            self.seqno+=1
            self.send_data(message, neighbor)
            if (peer_host, peer_port, conn) not in self.connections:
                self.connections.append((peer_host, peer_port, conn))
            if neighbor not in self.neighbors:
                self.neighbors.append(neighbor)

            print(f"HELLO message sent to {peer_host}:{peer_port}")
            return True

        except Exception as e:
            print(f"Failed to connect to neighbor {peer_host}:{peer_port}: {e}")
            return False

    def search_flooding(self):
        key = input("Digite a chave a ser buscada: ")
        for k, value in self.key_values.items():
            if k == key:
                print(f"Valor na tabela local!\nchave: {k} valor: {value}")
                return
        message = self.create_search_message("FL", key)
        origin = f"{self.host}:{self.port}"
        self.seen_messages.add((origin, self.seqno))
        
        for neighbor in self.neighbors:
            peer_host, peer_port = neighbor.split(":")
            peer_port = int(peer_port)
            for conn_host, conn_port, conn in self.connections:
                if conn_host == peer_host and conn_port == peer_port:
                    print(f"Encaminhando mensagem \"{message}\" para {peer_host}:{peer_port}")
                    self.send_data(message, neighbor)
                    break
            else:
                print(f"Connection to {peer_host}:{peer_port} not found.")
                
    def handle_search_flooding(self, origin, seqno, ttl, key, hop_count, last_hop_port, conn):
        print(f"Handling SEARCH flooding: Origin: {origin}, SeqNo: {seqno}, TTL: {ttl}, Key: {key}, Hop Count: {hop_count}")
        if key in self.key_values:
            print(f"Key {key} found in local table")
            self.found_key(key, self.key_values[key], "FL", conn, last_hop_port)
            return
        
        old_message = f"{origin} {seqno} {ttl} SEARCH FL {last_hop_port} {key} {hop_count}"
        message = self.update_search_message(old_message, hop_count)
        for neighbor in self.neighbors:
            peer_host, peer_port = neighbor.split(":")
            peer_port = int(peer_port)
            for conn_host, conn_port, conn in self.connections:
                if conn_host == peer_host and conn_port == peer_port:
                    print(f"Encaminhando mensagem \"{message}\" para {peer_host}:{peer_port}")
                    self.send_data(message, conn)
                    break
            else:
                print(f"Connection to {peer_host}:{peer_port} not found.")
        
    def found_key(self, key, value, mode, hop_count, last_hop_port):
        message = f"{self.host}:{self.port} {self.seqno} {self.ttl} VAL {mode} {key} {value} {hop_count}"
        self.seqno += 1  # Increment sequence number for each new message
        print("found key blablabla AQUI")
        # Find the connection corresponding to the last hop port
        for conn_host, conn_port, conn in self.connections:
            if conn_port == last_hop_port:
                print(f"Sending found key message \"{message}\" back to {conn_host}:{conn_port}")
                self.send_data(message, conn)
                break
        else:
            print(f"Connection to last hop port {last_hop_port} not found.")
            
    def handle_found_key(self, origin, seqno, ttl, key, value, mode, hop_count):
        if self.waiting_results.get(key):
            print(f"Valor encontrado!  Chave {key}:  Valor: {value}")
            return
        
        message = f"{self.host}:{self.port} {self.seqno} {self.ttl-1} VAL {mode} {key} {value} {hop_count}"
        for conn_host, conn_port, conn in self.connections:
            if conn_port == self.search_hops[key]:
                self.send_data(message, conn)
                self.search_hops.pop(key)
                
        print("encontrou porra nenhum,a fodeu")
        
            

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
            "0": self.list_neighbors,
            "1": self.hello,
            "2": self.search_flooding,
            "3": self.search_walk,
            "4": self.search_depth,
            "5": self.stats,
            "6": self.change_ttl
        }
        default = lambda: print("\nOPCAO INVALIDA")
        commands.get(input, default)()

    def start(self):
        listen_thread = threading.Thread(target=self.listen)
        listen_thread.start()
        # self.connect_to_neighbors()

        command_thread = threading.Thread(target=self.handle_command)
        command_thread.start()
        command_thread.join()
        listen_thread.join()
