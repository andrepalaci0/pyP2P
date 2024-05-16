
import socket


class Server:
    def __init__(self, address, port):
        self.address = address
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.address, self.port))
        self.server_socket.listen(5)  # Listen for incoming connections, with a backlog of 5
    
    def handle_client(self, client_socket, client_address):
        print(f"Accepted connection from {client_address}")
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            print(f"Received data: {data.decode()}")
        print(f"Connection from {client_address} closed.")
        client_socket.close()
    
    def listen(self):
        print(f"Server listening on {self.address}:{self.port}")
        while True:
            client_socket, client_address = self.server_socket.accept()
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket, client_address))
            client_thread.start()
    