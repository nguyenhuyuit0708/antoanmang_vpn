FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    iproute2 \
    iputils-ping \
    iptables \
    tcpdump \
    openssl \
    net-tools \
    iperf3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app
