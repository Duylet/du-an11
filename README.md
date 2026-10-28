# Duylet/du-an11 — Demo quản lý ERP bằng Python

Repository này có một ứng dụng **Mini ERP** phục vụ học tập, xây dựng bằng Python Flask và SQLite.

## Bắt đầu nhanh trên Windows + VS Code

```powershell
git clone https://github.com/Duylet/du-an11.git
cd du-an11\python-erp-demo
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Mở **http://127.0.0.1:5000** trong trình duyệt. Hướng dẫn đầy đủ nằm trong [python-erp-demo/README.md](python-erp-demo/README.md).

## Các chức năng

- Bảng điều khiển tổng quan.
- Quản lý sản phẩm, giá bán và tồn kho.
- Quản lý khách hàng.
- Tạo đơn hàng, tự động trừ kho và hoàn kho khi hủy đơn.
- Lưu dữ liệu cục bộ bằng SQLite.

## Cấu trúc dự án

- `python-erp-demo/`: demo Python Flask + SQLite, không cần Docker.
- `compose.yaml`: cấu hình Docker Compose cho bản ERPNext chính thức đã được chuẩn bị trước đó (tùy chọn).

Đây là dự án demo local để học tập, chưa phù hợp để triển khai production.
