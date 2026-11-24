FROM ubuntu:22.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    strongswan-swanctl \
    charon-systemd \
    strongswan-pki \
    iproute2 \
    iputils-ping \
    iptables \
    tcpdump \
    iperf3 \
    && rm -rf /var/lib/apt/lists/*
