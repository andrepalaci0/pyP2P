import random
import socket
import threading
import time
import os
from concurrent.futures import ThreadPoolExecutor

class Peer:
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
        self.walk_start = {}
        self.mother_node = None
        self.active_neighbor = None
        self.neighbors_candidates = []
        
        self.statistic = {
            'fl': {'searchs': 0, 'hops': 0},
            'rw': {'searchs': 0, 'hops': 0},
            'bp': {'searchs': 0, 'hops': 0}
        }
        

    
    def connect(self, peer_host, peer_port):
        time.sleep(0.5)
        conn = socket.create_connection((peer_host, peer_port))
        with self.lock:
            self.connections.append((peer_host, peer_port, conn))
        print(f"Connected to {peer_host}:{peer_port}")
        
    def listen(self):
        self.socket.bind((self.host, self.port))
        self.socket.listen(10)
        for neighbor in self.tobe_neighbors:
            self.server_hello(neighbor)
            
        threading.Thread(target=self.handle_connections).start()   
        
    def handle_connections(self):
        while not self._stop_event.is_set():
            socket, addr = self.socket.accept()
            threading.Thread(target=self.handle_client, args=(socket, addr)).start()

    def handle_client(self, conn, address):
        try:
            while not self._stop_event.is_set():
                try:
                    data = conn.recv(2048)
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
        
        # Check if the message has already been seen


        args_parts = args.split(" ")
        aux_mode = args_parts[0]
        if ((origin, seqno)) in self.seen_messages and not operation.endswith("_OK") and operation!= "HELLO" and ((origin, seqno)) not in self.walk_start:
            print(f"Message from {origin} with seqno {seqno} has already been seen. Ignoring.")
            return
        # Add the message to seen messages if it is not a response or HELLO
        if not operation.endswith("_OK") and operation!= "HELLO" and operation != "BYE":
            self.seen_messages.add((origin, seqno))

        if not operation.endswith("_OK"):
            with socket.create_connection((origin.split(":"))) as conn:
                conn.sendall(f"{self.host}:{self.port} {self.seqno} 1 {operation}_OK".encode())    
        
        ttl = int(ttl)-1
        if ttl == 0 and operation != "BYE" and operation != "HELLO" and not operation.endswith("_OK"):
            print("TTL reached 0. Dropping message.")
            return
        
        if aux_mode == 'FL':
            self.statistic['fl']['searchs'] += 1
        elif aux_mode == 'RW':
            self.statistic['rw']['searchs'] += 1
        elif aux_mode == 'BP':
            self.statistic['bp']['searchs'] += 1
            
        
        print(
            f"Received message  {message}"
        )
        # Handle the operatio
        if operation == "BYE":
            self.handle_bye(origin)
            return
        if operation == "HELLO":
            self.handle_hello(origin, conn)
            return
        elif operation == "SEARCH":
            self.handle_search_message(origin, seqno, ttl, args, conn)
            return
        elif operation == "VAL":
            print(f"DEBUG {args}")
            args_parts = args.split(" ")
            if len(args_parts) < 4:
                print("Invalid VAL message format")
                return
            mode = args_parts[0]
            key = args_parts[1]
            value = args_parts[2]
            hop_count = args_parts[3]
            self.handle_found_key(origin, seqno, ttl, key, value, mode, hop_count)
            return

            
    def handle_found_key(self, origin, seqno, ttl, key, value, mode, hop_count):
        if self.waiting_results.get(key):
            print(f"Valor encontrado!  Chave: {key}  Valor: {value}")
            if mode == "FL":
                self.statistic['fl']['hops'] += int(hop_count)
            elif mode == "RW":
                self.statistic['rw']['hops'] += int(hop_count)
            elif mode == "BP":
                self.statistic['bp']['hops'] += int(hop_count)
                
            self.waiting_results[key] = False
            return
        
        print(f"DEBUG: {hop_count} {self.search_hops.get(key)}")
        message = f"{origin} {seqno} {self.ttl-1} VAL {mode} {key} {value} {hop_count}"
        for neighbor in self.neighbors:
            peer_host, peer_port = neighbor.split(":")
            if(peer_port == self.search_hops[key]):
                with socket.create_connection((peer_host, peer_port)) as conn:
                    print(f"Enviando mensagem de valor encontrado para {peer_host}:{peer_port}")
                    conn.sendall(message.encode())
                    return
                
            
    def handle_search_message(self, origin, seqno, ttl, args, conn):
       #message = f"{self.host}:{self.port} {self.seqno} 1 SEARCH_OK"
       #self.seqno+=1
       #conn.sendall(message.encode())
       
       parts = args.split(" ")
       if len(parts) < 4:
           print("Invalid SEARCH message format")
           return
       mode, last_hop_port, key, hop_count = parts
       self.search_hops[key] = last_hop_port
       print(f"Handling SEARCH message: Mode: {mode}, Last Hop Port: {last_hop_port}, Key: {key}, Hop Count: {hop_count}")

       # Based on mode, select the appropriate search method
       if mode == "FL":
           self.handle_search_flooding(origin, seqno, ttl, key, hop_count, last_hop_port, conn)
       elif mode == "RW":
           self.handle_search_random_walk(origin, seqno, ttl, key, hop_count, last_hop_port, conn)
           pass
       elif mode == "BP":
           self.handle_search_depth(origin, seqno, ttl, key, hop_count, last_hop_port, conn)
           pass
       else:
           print(f"Unknown SEARCH mode: {mode}")            
           
    def handle_search_flooding(self, origin, seqno, ttl, key, hop_count, last_hop_port, conn):
        print(f"Handling SEARCH flooding: Origin: {origin}, SeqNo: {seqno}, TTL: {ttl}, Key: {key}, Hop Count: {hop_count}, Last Hop Port: {last_hop_port}")
        if key in self.key_values:
            print(f"Key {key} found in local table")
            value = self.key_values[key]
            self.found_key(key, self.key_values[key], "FL", value , last_hop_port)
            return
        
        old_message = f"{origin} {seqno} {ttl} SEARCH FL {last_hop_port} {key} {hop_count}"
        message = self.update_search_message(old_message, hop_count)
        for neighbor in self.neighbors:
            peer_host, peer_port = neighbor.split(":")
            peer_port = int(peer_port)
            if peer_port == last_hop_port:
                continue
            with socket.create_connection((peer_host, peer_port)) as conn:
                conn.sendall(message.encode())
                print(f"Enviando mensagem de busca para {peer_host}:{peer_port}")
                
    def handle_search_random_walk(self, origin, seqno, ttl, key, hop_count, last_hop_port, conn):
        print(f"Handling SEARCH random walk: Origin: {origin}, SeqNo: {seqno}, TTL: {ttl}, Key: {key}, Hop Count: {hop_count}")
        if key in self.key_values:
            print(f"Key {key} found in local table")
            value = self.key_values[key]
            self.found_key(key, self.key_values[key], "RW", value, last_hop_port)
        
        old_message = f"{origin} {seqno} {ttl} SEARCH RW {last_hop_port} {key} {hop_count}"
        message = self.update_search_message(old_message, hop_count)
        random_index = random.randint(0, len(self.neighbors) - 1)
        random_neighbor = self.neighbors[random_index]
        peer_host, peer_port = random_neighbor.split(":")
        peer_port = int(peer_port)
        with socket.create_connection((peer_host, peer_port)) as conn:
            conn.sendall(message.encode())
            print(f"Enviando mensagem de busca para {peer_host}:{peer_port}")

    def found_key(self, key, value, mode, hop_count, last_hop_port):
        message = f"{self.host}:{self.port} {self.seqno} {self.ttl} VAL {mode} {key} {value} {hop_count}"
        self.seqno += 1  # Increment sequence number for each new message

        # Find the connection corresponding to the last hop port
        for neighbor in self.neighbors:
            peer_host, peer_port = neighbor.split(":")
            peer_port = int(peer_port)
            if(peer_port == int(last_hop_port)):
                with socket.create_connection((peer_host, peer_port)) as conn:
                    conn.sendall(message.encode())
                    print(f"Enviando mensagem de chave encontrada para {peer_host}:{peer_port}")
                    return
            
           
    def handle_bye(self, origin):
        with self.lock:
            for index, neighbor in enumerate(self.neighbors):
                if neighbor == origin:
                    print(f"Removing neighbor {origin}")
                    self.neighbors.pop(index)
                    break
        print(f"Neighbor {origin} disconnected")

    def handle_hello(self, origin, conn):
        #message = f"{self.host}:{self.port} {self.seqno} 1 HELLO_OK"
        #conn.sendall(message.encode())
        with self.lock:
            if origin not in self.neighbors:
                self.neighbors.append(origin)
                print(f"Adicionando vizinho na tabela: {origin}")
            else:
                print(f"Vizinho ja esta na tabela: {origin}")
        print(f"Enviando mensagem de resposta para {origin}")

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
        
        with socket.create_connection((peer_host, peer_port)) as conn:
            conn.sendall(message.encode())
            print(f"HELLO message sent to {peer_host}:{peer_port}")
        
        
    def server_hello(self, neighbor):
        peer_host, peer_port = neighbor.split(":")
        peer_port = int(peer_port)

        try:
            time.sleep(0.5)
            conn = socket.create_connection((peer_host, peer_port))
            print(f"Connected to {peer_host}:{peer_port}")


            message = f"{self.host}:{self.port} {self.seqno} 1 HELLO"
            self.seqno+=1
            with socket.create_connection(neighbor.split(":")) as conn:
                conn.sendall(message.encode())
                
            if neighbor not in self.neighbors:
                self.neighbors.append(neighbor)

            print(f"HELLO message sent to {peer_host}:{peer_port}")
            return True

        except Exception as e:
            print(f"Failed to connect to neighbor {peer_host}:{peer_port}: {e}")
            return False        
        
    def list_neighbors(self):
        print(f"Ha {len(self.neighbors)} vizinhos na tabela:")
        for index, neighbor in enumerate(self.neighbors):
            peer_host, peer_port = neighbor.split(":")
            print(f"[{index}] {peer_host} {peer_port}")
            
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


    def search_flooding(self):
        key = input("Digite a chave a ser buscada: ")
        for k, value in self.key_values.items():
            if k == key:
                print(f"Valor na tabela local!\nchave: {k} valor: {value}")
                return
        origin = f"{self.host}:{self.port}"
        self.seen_messages.add((origin, self.seqno))
        message = self.create_search_message("FL", key)
        
        self.waiting_results[key] = True
        for neighbor in self.neighbors:
            peer_host, peer_port = neighbor.split(":")
            peer_port = int(peer_port)
            with socket.create_connection((peer_host, peer_port)) as conn:
                conn.sendall(message.encode())
                print(f"Enviando mensagem de busca para {peer_host}:{peer_port}")
        
    def create_search_message(self, mode, search_key):
        self.seqno+=1
        return f"{self.host}:{self.port} {self.seqno} {self.ttl} SEARCH {mode} {self.port} {search_key} {1}"
    
    def update_search_message(self, message, hop_count):
        parts = message.split(" ")
        parts[7] = str(int(hop_count) + 1)
        return f"{parts[0]} {parts[1]} {parts[2]} {parts[3]} {parts[4]} {self.port} {parts[6]} {parts[7]}"

    
    def search_walk(self):
        key = input("Digite a chave a ser buscada: ")
        for k, value in self.key_values.items():
            if k == key:
                print(f"Valor na tabela local!\nchave: {k} valor: {value}")
                return
            
        self.waiting_results[key] = True
        self.walk_start = (self.host, self.port) 
        message = self.create_search_message("RW", key)
        
        random_index = random.randint(0, len(self.neighbors) - 1)
        random_neighbor = self.neighbors[random_index]
        
        with socket.create_connection((random_neighbor.split(":"))) as conn:
            conn.sendall(message.encode())
            print(f"Enviando mensagem de busca para {random_neighbor}")
        pass
    
    
    
    def search_depth(self):
        key = input("Digite a chave a ser buscada: ")
        if key in self.key_values:
            print(f"Chave encontrada! Valor: {self.key_values[key]}")
            return

        origin = f"{self.host}:{self.port}"
        seqno = self.seqno
        self.seqno += 1
        ttl = self.ttl
        mode = "BP"
        last_hop_port = self.port
        hop_count = 1
        message = f"{origin} {seqno} {ttl} SEARCH {mode} {last_hop_port} {key} {hop_count}"
        self.neighbors_candidates = self.neighbors.copy()
        self.active_neighbor = random.choice(self.neighbors_candidates)
        self.neighbors_candidates.remove(self.active_neighbor)

        with socket.create_connection(self.active_neighbor.split(":")) as conn:
            conn.sendall(message.encode())
            print(f"Enviando mensagem de busca para {self.active_neighbor}")

    def handle_search_depth(self, origin, seqno, ttl, key, hop_count, last_hop_port, conn):
        hop_count = int(hop_count)
        mode = "BP"

        if key in self.key_values:
            print(f"Key found! Value: {self.key_values[key]}")
            self.found_key(key, self.key_values[key], mode, hop_count, last_hop_port)
            return

        if ttl == 0:
            print("TTL reached zero, discarding message")
            return

        # Initialize mother_node, active_neighbor, and neighbors_candidates if not set
        if not hasattr(self, "mother_node") or self.mother_node is None:
            self.mother_node = origin
            self.neighbors_candidates = self.neighbors.copy()
            self.active_neighbor = last_hop_port

        if last_hop_port in self.neighbors_candidates:
            self.neighbors_candidates.remove(last_hop_port)

        if self.mother_node == origin and self.active_neighbor == last_hop_port and not self.neighbors_candidates:
            print(f"BP: Unable to locate key {key}")
            return

        # Determine the next hop
        if hasattr(self, "active_neighbor") and self.active_neighbor != last_hop_port:
            print("BP: cycle detected, returning the message...")
            next_hop = last_hop_port
        elif not self.neighbors_candidates:
            print("BP: no neighbors found the key, backtracking...")
            next_hop = self.mother_node
        else:
            next_hop = random.choice(self.neighbors_candidates)
            self.active_neighbor = next_hop
            self.neighbors_candidates.remove(next_hop)

        # Ensure next_hop is not None
        if next_hop is None:
            print("Error: next_hop is None. This should not happen.")
            return

        hop_count += 1
        message = f"{origin} {seqno} {ttl-1} SEARCH {mode} {self.port} {key} {hop_count}"
        
        try:
            for neighbor in self.neighbors:
                peer_host, peer_port = neighbor.split(":")
                if neighbor == next_hop:
                    with socket.create_connection((peer_host, int(peer_port))) as new_conn:
                        new_conn.sendall(message.encode())
                        print(f"Sending search message to {next_hop}")
        except Exception as e:
            print(f"Error sending message to {next_hop}: {e}")

    
    
    def stats(self):
        stats = self.statistic

        def calculate_average_hops(searches, hops):
            if searches == 0:
                return 0
            return hops / searches

        # Total messages seen
        total_flooding_messages = stats['fl']['searchs']
        total_random_walk_messages = stats['rw']['searchs']
        total_depth_search_messages = stats['bp']['searchs']

        # Average hops to find destination
        avg_hops_flooding = calculate_average_hops(stats['fl']['searchs'], stats['fl']['hops'])
        avg_hops_random_walk = calculate_average_hops(stats['rw']['searchs'], stats['rw']['hops'])
        avg_hops_depth_search = calculate_average_hops(stats['bp']['searchs'], stats['bp']['hops'])

        # Display statistics
        print("Estatisticas")
        print(f"Total de mensagens de flooding vistas: {total_flooding_messages}")
        print(f"Total de mensagens de random walk vistas: {total_random_walk_messages}")
        print(f"Total de mensagens de busca em profundidade vistas: {total_depth_search_messages}")
        print(f"Media de saltos ate encontrar destino por flooding: {avg_hops_flooding:.2f}")
        print(f"Media de saltos ate encontrar destino por random walk: {avg_hops_random_walk:.2f}")
        print(f"Media de saltos ate encontrar destino por busca em profundidade: {avg_hops_depth_search:.2f}")

        pass
    
    def change_ttl(self):
        aux = int(input("Digite o novo valor de TTL: "))
        if aux < 1:
            print("Valor de TTL invalido")
            return
        self.ttl = aux
        print(f"Novo valor de TTL: {self.ttl}")


    def handle_command(self):
        while not self._stop_event.is_set():
            command = input(
                "Escolha o comando\n[0] Listar vizinhos\n[1] HELLO\n[2] SEARCH (flooding)\n[3] SEARCH (random walk)\n[4] SEARCH (busca em profundidade)\n[5] Estatisticas\n[6] Alterar valor padrao de TTL\n[9] Sair: "
            )
            if command == "9":
                self.leaves_network()
                break
            self.call_command(command)
            
    def leaves_network(self):
        self.stop()
            
    def stop(self):
        self._stop_event.set()  # Signal the listening thread to stop accepting new connections
        for neighbor in self.neighbors:
            peer_host, peer_port = neighbor.split(":")
            peer_port = int(peer_port)
            with socket.create_connection((peer_host, peer_port)) as conn:
                message = f"{self.host}:{self.port} {self.seqno} 1 BYE"
                conn.sendall(message.encode())
                
        with self.lock:
            for _, _, conn in self.connections:
                try:
                    conn.shutdown(socket.SHUT_RDWR)  # Disable further send and receive operations
                    conn.close()
                except socket.error as e:
                    print(f"Error closing connection: {e}")
        self._executor_shutdown.set()  # Signal the executor to stop accepting new tasks
        self.executor.shutdown(wait=False)  # Wait for all tasks to complete
        self.socket.close()  # Close the listening socket
        os._exit(0)
    
    def start(self):
        listen_thread = threading.Thread(target=self.listen)
        listen_thread.start()
        # self.connect_to_neighbors()

        command_thread = threading.Thread(target=self.handle_command)
        command_thread.start()
        command_thread.join()
        listen_thread.join()
