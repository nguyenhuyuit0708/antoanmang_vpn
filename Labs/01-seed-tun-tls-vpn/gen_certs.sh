#!/usr/bin/env bash
set -euo pipefail

mkdir -p certs
cd certs

# 1. Tao Root CA
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout ca.key -out ca.crt -days 365 \
  -subj "/C=VN/ST=HCM/L=ThuDuc/O=UIT-NT140/CN=VPN-Lab-CA"

# 2. Tao Server Key & CSR voi SAN = IP:10.9.0.11, DNS:vpn-server
cat > server_ext.cnf << 'EOF'
subjectAltName = IP:10.9.0.11,DNS:vpn-server
extendedKeyUsage = serverAuth
EOF

openssl req -newkey rsa:2048 -nodes \
  -keyout server.key -out server.csr \
  -subj "/C=VN/ST=HCM/L=ThuDuc/O=UIT-NT140/CN=vpn-server"

openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
  -out server.crt -days 365 -extfile server_ext.cnf

# 3. Tao Client Key & Cert (ho tro xac thuc 2 chieu mTLS)
cat > client_ext.cnf << 'EOF'
extendedKeyUsage = clientAuth
EOF

openssl req -newkey rsa:2048 -nodes \
  -keyout client.key -out client.csr \
  -subj "/C=VN/ST=HCM/L=ThuDuc/O=UIT-NT140/CN=vpn-client"

openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
  -out client.crt -days 365 -extfile client_ext.cnf

echo "[OK] Da tao xong chung chi CA, Server va Client trong thu muc ./certs"
