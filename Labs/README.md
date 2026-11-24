# Hướng dẫn Triển khai Thực tế các Bài Lab VPN (Môn NT140 - An Toàn Mạng)

Thư mục này chứa toàn bộ mã nguồn, file cấu hình và kịch bản thực hành phục vụ **Chương 3** của báo cáo đồ án *"Nghiên cứu, so sánh các loại VPN và xây dựng môi trường triển khai thực tế"*.

## Yêu cầu môi trường
- **Docker Desktop** (Windows 10/11 với WSL2 hoặc Ubuntu 22.04/24.04) cho Lab 01, 02, 03.
- **Máy ảo Ubuntu 22.04/24.04** (VMware/VirtualBox) + **Windows 10/11** cho Lab 04 (PPTP cần kernel hỗ trợ GRE/PPP đầy đủ) và kiểm thử Windows OpenVPN Client.
- Công cụ bắt gói tin & đo đạc: **Wireshark**, `tcpdump`, `ping`, `iperf3`.

---

## Lab 01: Đường hầm VPN cơ bản với TUN/TAP và TLS (SEED Labs)
Thư mục: `01-seed-tun-tls-vpn/`

### Kiến trúc IP
- Mạng công cộng (`net-public` - `10.9.0.0/24`): `vpn-client` (`10.9.0.5`), `vpn-server` (`10.9.0.11`)
- Mạng nội bộ (`net-private` - `192.168.60.0/24`): `vpn-server` (`192.168.60.11`), `host-internal` (`192.168.60.5`)
- Đường hầm ảo (`tun0` - `192.168.53.0/24`): `vpn-client` (`192.168.53.5`), `vpn-server` (`192.168.53.1`)

### Các bước chạy
```bash
cd 01-seed-tun-tls-vpn
docker compose up -d --build
```
1. **Kiểm chứng trước khi bật VPN:** Từ `vpn-client` không thể ping `192.168.60.5`:
   ```bash
   docker exec seed-vpn-client ping -c 3 192.168.60.5
   ```
2. **Phần A — Đường hầm UDP/TUN không mã hóa (SEED VPN_Tunnel):**
   - Terminal 1 (Server): `docker exec -it seed-vpn-server python3 tun_server.py`
   - Terminal 2 (Client): `docker exec -it seed-vpn-client python3 tun_client.py`
   - Terminal 3 (Kiểm thử & bắt gói tin):
     ```bash
     docker exec seed-vpn-client ping -c 4 192.168.60.5
     docker exec seed-vpn-server tcpdump -i eth0 udp port 9090 -X -c 4
     ```
   - *Quan sát:* Payload ICMP bên trong UDP lộ rõ dạng bản rõ (plaintext) → chứng minh Tunneling đơn thuần chưa có bảo mật.
3. **Phần B — Đường hầm TLS Mini-VPN có mã hóa & xác thực mTLS (SEED VPN):**
   - Dừng `tun_server.py` và `tun_client.py`, sau đó tạo chứng chỉ X.509:
     ```bash
     docker exec seed-vpn-server bash gen_certs.sh
     ```
   - Chép thư mục `certs/` sang `vpn-client` (hoặc mount chung) rồi chạy:
     - Terminal 1: `docker exec -it seed-vpn-server python3 tls_vpn_server.py`
     - Terminal 2: `docker exec -it seed-vpn-client python3 tls_vpn_client.py`
     - Terminal 3: `docker exec seed-vpn-client ping -c 4 192.168.60.5` và `tcpdump -i eth0 tcp port 4433 -X -c 4`.
   - *Quan sát:* Toàn bộ dữ liệu được mã hóa TLS (`Application Data`), đồng thời xác thực 2 chiều bằng chứng chỉ X.509.

---

## Lab 02: Triển khai OpenVPN (SSL/TLS VPN)
Thư mục: `02-openvpn/`

### Các bước chạy (Remote-Access: Linux Server ↔ Windows/Linux Client)
```bash
cd 02-openvpn
docker compose up -d
# Khởi tạo PKI (CA, Server Cert, Client Cert, DH, TLS-Auth key)
docker exec -it ovpn-server bash /etc/openvpn/lab/init_pki.sh
# Chạy OpenVPN Server
docker exec -it ovpn-server openvpn --config /etc/openvpn/lab/server.conf
```
- **Kết nối từ Windows 10/11:** Cài đặt **OpenVPN GUI**, import file `client.ovpn` (đảm bảo thư mục `keys/` nằm cùng cấp với `client.ovpn`) và bấm **Connect**.
- **Kiểm chứng:**
  - Kiểm tra IP ảo cấp phát trong dải `10.8.0.0/24` (`ipconfig` trên Windows hoặc `ip a` trên Linux).
  - Truy cập máy chủ web nội bộ `http://192.168.70.20` (chỉ truy cập được khi đã bật OpenVPN).
- **Mô hình Site-to-Site:** Dùng `site-a.conf` và `site-b.conf` trên 2 máy ảo Ubuntu để kết nối 2 LAN `192.168.10.0/24` ↔ `192.168.20.0/24`.

---

## Lab 03: Triển khai IPsec Site-to-Site với strongSwan (IKEv2/IPsec)
Thư mục: `03-ipsec-strongswan/`

### Kiến trúc IP
- WAN (`172.16.0.0/24`): `gateway-a` (`172.16.0.10`), `gateway-b` (`172.16.0.20`)
- LAN A (`10.1.0.0/24`): `gateway-a` (`10.1.0.2`), `host-a` (`10.1.0.10`)
- LAN B (`10.2.0.0/24`): `gateway-b` (`10.2.0.2`), `host-b` (`10.2.0.10`)

### Các bước chạy & kiểm chứng
```bash
cd 03-ipsec-strongswan
docker compose up -d --build
# Kiểm tra trạng thái IKE_SA và CHILD_SA (ESP Tunnel)
docker exec ipsec-gateway-a swanctl --list-sas
# Kiểm tra kết nối giữa 2 máy đầu cuối thuộc 2 LAN khác nhau
docker exec ipsec-host-a ping -c 4 10.2.0.10
# Bắt gói tin ESP mã hóa trên giao diện WAN
docker exec ipsec-gateway-a tcpdump -i eth0 esp -c 6
```

---

## Lab 04: Triển khai PPTP VPN & Phân tích lỗ hổng bảo mật
Thư mục: `04-pptp-demo/`

> **Lưu ý an toàn:** Chỉ triển khai trong mạng LAN/máy ảo cô lập để phục vụ nghiên cứu học thuật, tuyệt đối không đưa PPTP lên môi trường sản xuất.

### Các bước chạy
1. Trên máy ảo **Ubuntu 22.04/24.04**, copy thư mục `04-pptp-demo/` vào máy ảo và chạy:
   ```bash
   cd 04-pptp-demo
   sudo bash setup_pptp_ubuntu.sh
   ```
2. Trên **Windows 10/11**: Mở *Settings → Network & internet → VPN → Add VPN*:
   - VPN provider: `Windows (built-in)`
   - VPN type: `Point to Point Tunneling Protocol (PPTP)`
   - Server address: `<IP máy ảo Ubuntu>`
   - Username / Password: `uit_student` / `DemoPass123!`
3. **Bắt gói tin & phân tích trên Wireshark:**
   - Lọc: `tcp.port == 1723 || gre || chap`
   - Ghi nhận: Toàn bộ quá trình điều khiển trên TCP 1723 truyền ở dạng bản rõ; gói tin xác thực MS-CHAPv2 (Challenge/Response) có thể bị bắt lại để tấn công vét cạn ngoại tuyến (offline brute-force).

---

## Kịch bản đo đạc hiệu năng (cho Mục 3.6 của Báo cáo)
Sử dụng `iperf3` và `ping` để lấy số liệu so sánh trực tiếp giữa Baseline (không VPN), OpenVPN, IPsec (strongSwan) và PPTP:
```bash
# Phía Server / Host đích
iperf3 -s

# Phía Client / Host nguồn (đo TCP throughput trong 15 giây)
iperf3 -c <IP_DICH> -t 15

# Đo độ trễ trung bình (RTT)
ping -c 20 <IP_DICH>
```

## Checklist ảnh chụp màn hình cần bổ sung vào Chương 3
1. **Hình 3.3:** Kết quả `ping 192.168.60.5` thành công qua `tun0` và `tcpdump` chứng minh TLS mã hóa (Lab 01).
2. **Hình 3.4:** Kết quả kết nối OpenVPN GUI trên Windows + truy cập thành công `http://192.168.70.20` (Lab 02).
3. **Hình 3.5:** Kết quả `swanctl --list-sas` hiển thị `ESTABLISHED` (AES-256-GCM) và `tcpdump` bắt gói tin ESP giữa 2 Gateway (Lab 03).
4. **Hình 3.6:** Kết quả bắt gói tin PPTP/GRE/MS-CHAPv2 trên Wireshark minh họa điểm yếu kênh điều khiển không mã hóa (Lab 04).
5. **Hình 3.7:** Kết quả đo thông lượng `iperf3` và độ trễ `ping` giữa các giao thức.
