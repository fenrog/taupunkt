#!/usr/bin/env bash
cd /home/taupunkt/taupunkt
source venv-taupunkt/bin/activate

python taupunkt.py > /dev/null 2>&1 &
#python taupunkt.py > /home/taupunkt/taupunkt.log 2>&1 &

