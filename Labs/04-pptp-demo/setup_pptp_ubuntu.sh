#!/usr/bin/env bash
set -euo pipefail

# Script cai dat nhanh PPTP VPN Server tren Ubuntu 22.04/24.04 (CHI DUNG CHO LAB PHAN TICH LO HONG)
if [ "$EUID" -ne 0 ]; then
  echo "Vui long chay voi quyen root: sudo bash setup_pptp_ubuntu.sh"
  exit 1
fi

apt-get update
apt-get install -y pptpd iptables tcpdump

cp pptpd.conf /etc/pptpd.conf
cp pptpd-options /etc/ppp/pptpd-options
cp chap-secrets /etc/ppp/chap-secrets
chmod 600 /etc/ppp/chap-secrets

# Bat IP Forwarding
sysctl -w net.ipv4.ip_forward=1

# Bat NAT cho subnet PPTP (thay eth0 bang card mang thuc te neu khac)
DEFAULT_IF=$(ip route | awk '/default/ {print $5; exit}')
iptables -t nat -A POSTROUTING -s 10.20.0.0/24 -o "$DEFAULT_IF" -j MASQUERADE
iptables -A FORWARD -p tcp --syn -s 10.20.0.0/24 -j TCPMSS --set-mss 1356

systemctl enable pptpd
systemctl restart pptpd
systemctl status pptpd --no-pager

echo "[OK] PPTP Server dang chay tren TCP 1723 + GRE (Protocol 47)."
echo "Tai khoan demo: uit_student / DemoPass123!"
