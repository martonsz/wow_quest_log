#!/bin/bash
set -e

mkdir app
cd app

git clone --depth 1 https://github.com/martonsz/wow_quest_log.git wow_quest_log
cd wow_quest_log

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python main.py