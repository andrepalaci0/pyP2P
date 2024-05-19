#!/bin/bash

# Find all Python processes
processes=$(ps aux | grep '[p]ython')

if [ -z "$processes" ]; then
    echo "No Python processes found."
    exit 0
fi

# Kill each Python process that is running
while read -r process; do
    # Extract the PID (second column of ps output)
    pid=$(echo $process | awk '{print $2}')
    
    # Kill the process
    echo "Killing process with PID: $pid"
    kill -9 $pid
done <<< "$processes"

echo "All Python processes killed."
