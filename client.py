import threading
import time


class Client(threading.Thread):
    
    def __init__(self):
        super().__init__()
        self._stop_event = threading.Event()  # Evento para sinalizar que a thread deve parar

    def run(self):
        print("\nThread iniciada.")
        while True:
            if(self._stop_event.is_set()):
                break
            command = input("Escolha o comando\n[0] Listar vizinhos\n[1] HELLO\n[2] SEARCH (flooding)\n[3] SEARCH (random walk)\n[4] SEARCH (busca em profundidade)\n[5] Estatisticas\n[6] Alterar valor padrao de TTL\n[9] Sair: ")  
            self.call_command(command)
            time.sleep(0.5)
                                   
        print("\nThread encerrada.")

    def stop(self):
        self._stop_event.set()  # Sinaliza para a thread que ela deve parar
   
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

    def leaves(self):
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

