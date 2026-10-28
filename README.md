# ERPNext Demo — Duylet/du-an11

Dự án demo ERPNext chạy bằng Docker Compose, phù hợp để thử nghiệm và học các chức năng ERP cơ bản ngay trên máy tính Windows + VS Code.

## ERPNext là gì?

ERPNext là phần mềm ERP mã nguồn mở xây dựng trên Frappe Framework. Demo này dùng bản triển khai Docker chính thức để bạn có thể thử các phân hệ như bán hàng, mua hàng, kho, kế toán và nhân sự.

## Yêu cầu

- Windows 10/11 với WSL 2 được bật
- Docker Desktop đang chạy và dùng Linux containers
- Git
- VS Code (không bắt buộc nhưng khuyến nghị)
- RAM và dung lượng đĩa trống đủ để chạy nhiều container; lần đầu sẽ tải các image khá lớn

## Chạy demo trên Windows

Mở PowerShell tại thư mục muốn lưu dự án:

```powershell
git clone https://github.com/Duylet/du-an11.git
cd du-an11
docker compose up -d
```

Theo dõi quá trình khởi tạo site:

```powershell
docker compose logs -f create-site
```

Khi container tạo site hoàn tất, mở **http://localhost:8080**.

- Tài khoản: `Administrator`
- Mật khẩu demo: `admin`

Đây là thông tin đăng nhập mặc định cho môi trường demo cục bộ. Không dùng cấu hình này cho máy chủ công khai hoặc dữ liệu thật. Đổi mật khẩu ngay nếu tiếp tục sử dụng lâu dài.

## Các lệnh thường dùng

```powershell
# Xem trạng thái các container
docker compose ps

# Xem log tất cả dịch vụ
docker compose logs -f

# Dừng demo nhưng giữ dữ liệu
docker compose down

# Khởi động lại
docker compose up -d

# Xóa demo và dữ liệu database (KHÔNG THỂ HOÀN TÁC)
docker compose down -v
```

## Gợi ý nội dung trình diễn

1. Đăng nhập và xem trang Workspace.
2. Tạo Company và kiểm tra thông tin cơ bản.
3. Tạo Customer và Item mẫu.
4. Tạo Sales Order và xem quy trình bán hàng.
5. Mở Stock để xem quản lý kho (cần cấu hình kho và mặt hàng).
6. Thử các phân hệ khác bằng dữ liệu giả lập.

Tên menu và các bước cấu hình có thể khác tùy phiên bản và thiết lập ban đầu.

## Lưu ý

- Đây là môi trường **demo dùng một lần**, không dành cho production.
- Không nhập thông tin cá nhân, dữ liệu khách hàng thật hoặc thông tin tài chính thật.
- Dữ liệu được lưu trong Docker volumes. Lệnh `docker compose down -v` xóa volumes và dữ liệu.
- Nếu cổng 8080 đã được sử dụng, chỉnh ánh xạ cổng trong `compose.yaml` rồi chạy lại.
- Nếu site chưa sẵn sàng, xem log `create-site` và đợi các dịch vụ database/Redis khởi động.

## Nguồn chính thức

- ERPNext: https://github.com/frappe/erpnext
- Frappe Docker: https://github.com/frappe/frappe_docker
- Tài liệu ERPNext: https://docs.frappe.io/erpnext
