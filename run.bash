#!/bin/bash

# Start the first node on port 5000
gnome-terminal -- bash -c "python3 src/main.py 127.0.0.1:5000; exec bash"

# Start the second node on port 5001
gnome-terminal -- bash -c "python3 src/main.py 127.0.0.1:5001; exec bash"

# Start the third node on port 5002
gnome-terminal -- bash -c "python3 src/main.py 127.0.0.1:5002; exec bash"

# Start the fourth node on port 5003
gnome-terminal -- bash -c "python3 src/main.py 127.0.0.1:5003; exec bash"

# Start the fifth node on port 5004 with the neighbors file
