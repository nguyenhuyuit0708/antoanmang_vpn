#!/usr/bin/env python3
"""
SEED Labs - VPN Tunneling Client (UDP/TUN - khong ma hoa)
Tao giao dien ao tun0, dinh tuyen mang noi bo 192.168.60.0/24 qua duong ham UDP.
Tham khao: Wenliang Du, SEED Labs 20.04 - VPN Tunneling Lab.
"""

import fcntl
import os
import select
import socket
import struct
import subprocess

TUNSETIFF = 0x400454CA
IFF_TUN = 0x0001
IFF_NO_PI = 0x1000

SERVER_IP = "10.9.0.11"
SERVER_PORT = 9090
TUN_IP = "192.168.53.5/24"
PRIVATE_SUBNET = "192.168.60.0/24"


def create_tun(dev_name: str = "tun0") -> tuple[int, str]:
    tun = os.open("/dev/net/tun", os.O_RDWR)
    ifr = struct.pack("16sH", dev_name.encode(), IFF_TUN | IFF_NO_PI)
    ifname_bytes = fcntl.ioctl(tun, TUNSETIFF, ifr)
    ifname = ifname_bytes[:16].decode().strip("\x00")
    subprocess.run(["ip", "addr", "add", TUN_IP, "dev", ifname], check=True)
    subprocess.run(["ip", "link", "set", "dev", ifname, "up"], check=True)
    subprocess.run(["ip", "route", "replace", PRIVATE_SUBNET, "dev", ifname], check=True)
    return tun, ifname


def main() -> None:
    tun, ifname = create_tun("tun0")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    print(f"[Client] Giao dien {ifname} ({TUN_IP}) da san sang.")
    print(f"[Client] Dinh tuyen {PRIVATE_SUBNET} -> {ifname} -> {SERVER_IP}:{SERVER_PORT}")

    while True:
        ready, _, _ = select.select([sock, tun], [], [])
        for fd in ready:
            if fd == tun:
                packet = os.read(tun, 4096)
                sock.sendto(packet, (SERVER_IP, SERVER_PORT))
            elif fd is sock:
                data, _ = sock.recvfrom(4096)
                os.write(tun, data)


if __name__ == "__main__":
    main()
