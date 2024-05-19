#!/bin/bash

#dá pra usar o comando nohup para rodar o programa em background...
# Start the first node on port 5000
gnome-terminal -- bash -c "python3 src/main.py 127.0.0.1:5000 src/inputs_teste/vizinhos/1/1_vizinhos.txt src/inputs_teste/vizinhos/1/1_chave_valor.txt; exec bash"

# Start the second node on port 5001
gnome-terminal -- bash -c "python3 src/main.py 127.0.0.1:5001 src/inputs_teste/vizinhos/2/2_vizinhos.txt src/inputs_teste/vizinhos/2/2_chave_valor.txt; exec bash"

# Start the third node on port 5002
gnome-terminal -- bash -c "python3 src/main.py 127.0.0.1:5002 src/inputs_teste/vizinhos/3/3_vizinhos.txt src/inputs_teste/vizinhos/3/3_chave_valor.txt; exec bash"

# Start the fourth node on port 5003
gnome-terminal -- bash -c "python3 src/main.py 127.0.0.1:5003 src/inputs_teste/vizinhos/4/4_vizinhos.txt src/inputs_teste/vizinhos/4/4_chave_valor.txt; exec bash"

