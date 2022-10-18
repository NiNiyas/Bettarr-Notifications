#!/bin/bash

echo "**** installing python3 and pip ****"
apt update
apt install -y python3-pip python3

echo "**** installing requirements ****"
python3 -m pip install --upgrade pip
pip3 install setuptools-rust
pip3 install --no-cache-dir --upgrade requests requests[security] cryptography loguru
