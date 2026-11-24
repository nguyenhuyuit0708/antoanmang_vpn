#!/usr/bin/env python3
"""
SEED Labs - TLS Mini-VPN Client (Ma hoa TLS 1.2/1.3 + xac thuc mTLS)
Ket noi den TLS VPN Server, xac thuc chung chi X.509 va dinh tuyen 192.168.60.0/24 qua tun0.
Tham khao: Wenliang Du, SEED Labs 20.04 - Virtual Private Network (VPN) Lab.
"""

import fcntl
import os
import select
import socket
import ssl
import struct
import subprocess

TUNSETIFF = 0x400454CA
IFF_TUN = 0x0001
IFF_NO_PI = 0x1000

SERVER_IP = "10.9.0.11"
SERVER_PORT = 4433
TUN_IP = "192.168.53.5/24"
PRIVATE_SUBNET = "192.168.60.0/24"


def create_tun(dev_name: str = "tun0") -> tuple[int, str]:
    tun = os.open("/dev/net/tun", os.O_RDWR)
    ifr = struct.pack("16sH", dev_name.encode(), IFF_TUN | IFF_NO_PI)
    ifname_bytes = fcntl.ioctl(tun, TUNSETIFF, ifr)
    ifname = ifname_bytes[:16].decode().strip("\x00")
    subprocess.run(["ip", "addr", "replace", TUN_IP, "dev", ifname], check=True)
    subprocess.run(["ip", "link", "set", "dev", ifname, "up"], check=True)
    subprocess.run(["ip", "route", "replace", PRIVATE_SUBNET, "dev", ifname], check=True)
    return tun, ifname


def recv_exact(conn: ssl.SSLSocket, n: int) -> bytes:
    buf = bytearray()
    while len(buf) < n:
        chunk = conn.recv(n - len(buf))
        if not chunk:
            return b""
        buf.extend(chunk)
    return bytes(buf)


def main() -> None:
    tun, ifname = create_tun("tun0")

    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.load_verify_locations(cafile="certs/ca.crt")
    ctx.load_cert_chain(certfile="certs/client.crt", keyfile="certs/client.key")
    ctx.check_hostname = True

    raw_sock = socket.create_connection((SERVER_IP, SERVER_PORT))
    tls_conn = ctx.wrap_socket(raw_sock, server_hostname=SERVER_IP)
    print(f"[TLS-Client] Da ket noi toi {SERVER_IP}:{SERVER_PORT} | Cipher: {tls_conn.cipher()}")
    print(f"[TLS-Client] Dinh tuyen {PRIVATE_SUBNET} -> {ifname} ({TUN_IP})")

    while True:
        ready, _, _ = select.select([tls_conn, tun], [], [])
        for fd in ready:
            if fd == tun:
                pkt = os.read(tun, 4096)
                tls_conn.sendall(struct.pack("!H", len(pkt)) + pkt)
            elif fd is tls_conn:
                hdr = recv_exact(tls_conn, 2)
                if not hdr:
                    print("[TLS-Client] Server da dong ket noi.")
                    return
                (pkt_len,) = struct.unpack("!H", hdr)
                pkt = recv_exact(tls_conn, pkt_len)
                if not pkt:
                    return
                os.write(tun, pkt)


if __name__ == "__main__":
    main()
