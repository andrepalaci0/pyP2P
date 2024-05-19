#!/bin/bash

# Start the first node on port 5000
python3 src/main.py 127.0.0.1:5000 &

# Start the second node on port 5001
python3 src/main.py 127.0.0.1:5001 &

# Start the third node on port 5002
python3 src/main.py 127.0.0.1:5002 &

# Start the fourth node on port 5003
python3 src/main.py 127.0.0.1:5003 &

# Start the fifth node on port 5004 with the neighbors file
python3 src/main.py 127.0.0.1:5004 src/inputs/vizinhos.txt &
