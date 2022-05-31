#!/usr/bin/with-contenv bash

apk add --update --no-cache python3 py-pip gcc musl-dev python3-dev libffi-dev openssl-dev cargo make
pip install --no-cache-dir requests requests[security] cryptography loguru
apk del \
        libressl-dev \
        musl-dev \
        libffi-dev \
        gcc \
        cargo \
        python3-dev \
        make
