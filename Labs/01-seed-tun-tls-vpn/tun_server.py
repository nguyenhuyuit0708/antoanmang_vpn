#!/usr/bin/env python3
"""
SEED Labs - VPN Tunneling Server (UDP/TUN - khong ma hoa)
Mo phong co che dong goi IP-in-UDP qua giao dien ao TUN (Layer 3).
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

SERVER_BIND_IP = "0.0.0.0"
SERVER_PORT = 9090
TUN_IP = "192.168.53.1/24"


def create_tun(dev_name: str = "tun0") -> tuple[int, str]:
    tun = os.open("/dev/net/tun", os.O_RDWR)
    ifr = struct.pack("16sH", dev_name.encode(), IFF_TUN | IFF_NO_PI)
    ifname_bytes = fcntl.ioctl(tun, TUNSETIFF, ifr)
    ifname = ifname_bytes[:16].decode().strip("\x00")
    subprocess.run(["ip", "addr", "add", TUN_IP, "dev", ifname], check=True)
    subprocess.run(["ip", "link", "set", "dev", ifname, "up"], check=True)
    return tun, ifname


def main() -> None:
    tun, ifname = create_tun("tun0")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((SERVER_BIND_IP, SERVER_PORT))

    print(f"[Server] Giao dien {ifname} ({TUN_IP}) da san sang.")
    print(f"[Server] Dang lang nghe UDP tren {SERVER_BIND_IP}:{SERVER_PORT} ...")

    client_addr = None

    while True:
        ready, _, _ = select.select([sock, tun], [], [])
        for fd in ready:
            if fd is sock:
                data, addr = sock.recvfrom(4096)
                client_addr = addr
                os.write(tun, data)
            elif fd == tun:
                packet = os.read(tun, 4096)
                if client_addr:
                    sock.sendto(packet, client_addr)


if __name__ == "__main__":
    main()
