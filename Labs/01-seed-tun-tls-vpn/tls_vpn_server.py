#!/usr/bin/env python3
"""
SEED Labs - TLS Mini-VPN Server (Ma hoa TLS 1.2/1.3 + xac thuc mTLS)
Dong goi goi tin IP tu giao dien ao tun0 vao kenh ma hoa TLS (co length-prefix 2 byte).
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

SERVER_BIND_IP = "0.0.0.0"
SERVER_PORT = 4433
TUN_IP = "192.168.53.1/24"


def create_tun(dev_name: str = "tun0") -> tuple[int, str]:
    tun = os.open("/dev/net/tun", os.O_RDWR)
    ifr = struct.pack("16sH", dev_name.encode(), IFF_TUN | IFF_NO_PI)
    ifname_bytes = fcntl.ioctl(tun, TUNSETIFF, ifr)
    ifname = ifname_bytes[:16].decode().strip("\x00")
    subprocess.run(["ip", "addr", "replace", TUN_IP, "dev", ifname], check=True)
    subprocess.run(["ip", "link", "set", "dev", ifname, "up"], check=True)
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

    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.load_cert_chain(certfile="certs/server.crt", keyfile="certs/server.key")
    ctx.load_verify_locations(cafile="certs/ca.crt")
    ctx.verify_mode = ssl.CERT_REQUIRED  # Bat buoc xac thuc chung chi Client (mTLS)

    raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    raw_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    raw_sock.bind((SERVER_BIND_IP, SERVER_PORT))
    raw_sock.listen(5)

    print(f"[TLS-Server] Giao dien {ifname} ({TUN_IP}) san sang. Lang nghe TLS :{SERVER_PORT}...")

    while True:
        client_raw, addr = raw_sock.accept()
        try:
            tls_conn = ctx.wrap_socket(client_raw, server_side=True)
            print(f"[TLS-Server] Ket noi TLS thanh cong tu {addr} | Cipher: {tls_conn.cipher()}")
            while True:
                ready, _, _ = select.select([tls_conn, tun], [], [])
                for fd in ready:
                    if fd is tls_conn:
                        hdr = recv_exact(tls_conn, 2)
                        if not hdr:
                            raise ConnectionError("Client da ngat ket noi")
                        (pkt_len,) = struct.unpack("!H", hdr)
                        pkt = recv_exact(tls_conn, pkt_len)
                        if not pkt:
                            raise ConnectionError("Mat du lieu goi tin")
                        os.write(tun, pkt)
                    elif fd == tun:
                        pkt = os.read(tun, 4096)
                        tls_conn.sendall(struct.pack("!H", len(pkt)) + pkt)
        except Exception as exc:
            print(f"[TLS-Server] Phien ket thuc: {exc}")
        finally:
            try:
                client_raw.close()
            except OSError:
                pass


if __name__ == "__main__":
    main()
