#!/bin/bash

echo "**** installing python3 and pip ****"
apk add --update --no-cache python3 py-pip gcc musl-dev python3-dev libffi-dev openssl-dev cargo make

echo "**** installing requests module ****"
pip install --no-cache-dir --upgrade requests requests[security] cryptography loguru
apk del \
        libressl-dev \
        musl-dev \
        libffi-dev \
        gcc \
        cargo \
        python3-dev \
        make
