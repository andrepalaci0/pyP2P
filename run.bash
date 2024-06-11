#!/bin/bash

# Start the first node on port 5000
gnome-terminal -- bash -c "python3 src/main.py 127.0.0.1:5000 src/inputs_teste/vizinhos/1/1_vizinhos.txt src/inputs_teste/vizinhos/1/1_chave_valor.txt; exec bash"

# Start the second node on port 5001
gnome-terminal -- bash -c "python3 src/main.py 127.0.0.1:5001 src/inputs_teste/vizinhos/2/2_vizinhos.txt src/inputs_teste/vizinhos/2/2_chave_valor.txt; exec bash"

# Start the third node on port 5002
gnome-terminal -- bash -c "python3 src/main.py 127.0.0.1:5002 src/inputs_teste/vizinhos/3/3_vizinhos.txt src/inputs_teste/vizinhos/3/3_chave_valor.txt; exec bash"

# Start the fourth node on port 5003
gnome-terminal -- bash -c "python3 src/main.py 127.0.0.1:5003 src/inputs_teste/vizinhos/4/4_vizinhos.txt src/inputs_teste/vizinhos/4/4_chave_valor.txt; exec bash"

# Start the fifth node on port 5004
gnome-terminal -- bash -c "python3 src/main.py 127.0.0.1:5004 src/inputs_teste/vizinhos/5/5_vizinhos.txt src/inputs_teste/vizinhos/5/5_chave_valor.txt; exec bash"

# Start the sixth node on port 5005
gnome-terminal -- bash -c "python3 src/main.py 127.0.0.1:5005 src/inputs_teste/vizinhos/6/6_vizinhos.txt src/inputs_teste/vizinhos/6/6_chave_valor.txt; exec bash"

# Start the seventh node on port 5006
gnome-terminal -- bash -c "python3 src/main.py 127.0.0.1:5006 src/inputs_teste/vizinhos/7/7_vizinhos.txt src/inputs_teste/vizinhos/7/7_chave_valor.txt; exec bash"

# Start the eighth node on port 5007
gnome-terminal -- bash -c "python3 src/main.py 127.0.0.1:5007 src/inputs_teste/vizinhos/8/8_vizinhos.txt src/inputs_teste/vizinhos/8/8_chave_valor.txt; exec bash"

# Start the ninth node on port 5008
gnome-terminal -- bash -c "python3 src/main.py 127.0.0.1:5008 src/inputs_teste/vizinhos/9/9_vizinhos.txt src/inputs_teste/vizinhos/9/9_chave_valor.txt; exec bash"

# Start the tenth node on port 5009
gnome-terminal -- bash -c "python3 src/main.py 127.0.0.1:5009 src/inputs_teste/vizinhos/10/10_vizinhos.txt src/inputs_teste/vizinhos/10/10_chave_valor.txt; exec bash"