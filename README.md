# Duylet/du-an11 — Mini ERP 2.0

Ứng dụng quản lý doanh nghiệp phục vụ học tập, xây dựng bằng **Python Flask + SQLite**.

## Chức năng
- Đăng nhập quản trị và CSRF protection.
- Dashboard: KPI, doanh thu đơn hoàn thành, đơn đang xử lý, cảnh báo tồn kho.
- Quản lý sản phẩm: thêm/sửa/tìm kiếm, điều chỉnh tồn kho.
- Quản lý khách hàng: thêm/sửa/tìm kiếm/xóa.
- Quản lý đơn hàng: tạo đơn, kiểm tra kho an toàn, quy trình trạng thái, hoàn kho khi hủy.
- Lịch sử biến động kho.
- Giao diện responsive cho desktop và điện thoại.

## Chạy nhanh trên Windows

~~~powershell
git clone https://github.com/Duylet/du-an11.git
cd du-an11\python-erp-demo
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m flask --app app init-db
python -m flask --app app create-admin --username admin
python app.py
~~~

Mở http://127.0.0.1:5000. Hướng dẫn chi tiết và cách chạy test nằm trong [python-erp-demo/README.md](python-erp-demo/README.md).

## Cấu trúc
- python-erp-demo/: ứng dụng Flask + SQLite.
- compose.yaml: cấu hình tùy chọn cho ERPNext upstream.

Đây là dự án học tập/local, chưa phải hệ thống ERP production.