#!/bin/bash

rm Output/run_summary0.txt

./run_General0.sh

if [ $? -ne 0 ]; then
    echo "Error: The sub-script run_General0.sh failed. Exiting main script." >&2
    exit 1
fi

./run_Pluribus0.sh

if [ $? -ne 0 ]; then
    echo "Error: The sub-script run_Pluribus0.sh failed. Exiting main script." >&2
    exit 1
fi

./run_Simulacra0.sh

if [ $? -ne 0 ]; then
    echo "Error: The sub-script run_Simualcra0.sh failed. Exiting main script." >&2
    exit 1
fi

./run_World_Hate0.sh

if [ $? -ne 0 ]; then
    echo "Error: The sub-script run_Trump0.sh failed. Exiting main script." >&2
    exit 1
fi

./run_Trump0.sh

cat Output/run_summary0.txt
