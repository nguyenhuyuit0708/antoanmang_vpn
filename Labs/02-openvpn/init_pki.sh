#!/usr/bin/env bash
set -euo pipefail

# Khoi tao PKI bang Easy-RSA cho OpenVPN Server & Client
WORK_DIR="/etc/openvpn/lab/pki-work"
rm -rf "$WORK_DIR"
make-cadir "$WORK_DIR"
cd "$WORK_DIR"

export EASYRSA_BATCH=1
./easyrsa init-pki
./easyrsa build-ca nopass
./easyrsa gen-req server nopass
./easyrsa sign-req server server
./easyrsa gen-req client1 nopass
./easyrsa sign-req client client1
./easyrsa gen-dh
openvpn --genkey secret ta.key

mkdir -p /etc/openvpn/lab/keys
cp pki/ca.crt pki/dh.pem ta.key /etc/openvpn/lab/keys/
cp pki/issued/server.crt pki/private/server.key /etc/openvpn/lab/keys/
cp pki/issued/client1.crt pki/private/client1.key /etc/openvpn/lab/keys/

echo "[OK] Da khoi tao xong PKI tai /etc/openvpn/lab/keys/"
