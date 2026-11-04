# Duylet ERP — Mini ERP 2.0

Mini ERP phục vụ học tập, xây dựng bằng **Python Flask + SQLite** với giao diện responsive, đăng nhập quản trị và lịch sử biến động kho.

## Tính năng
- Đăng nhập quản trị; mật khẩu được băm bằng Werkzeug.
- Dashboard: KPI, doanh thu từ đơn hoàn thành, giá trị đơn đang xử lý và cảnh báo tồn kho.
- Sản phẩm: thêm, sửa tên/giá, tìm kiếm, điều chỉnh tồn kho.
- Khách hàng: thêm, sửa, tìm kiếm và xóa nếu chưa có đơn hàng.
- Đơn hàng: kiểm tra tồn kho trong giao dịch SQLite, theo dõi trạng thái, hoàn kho đúng một lần khi hủy.
- Lịch sử nhập/xuất/điều chỉnh kho.
- CSRF protection cho các thao tác POST.

> Đây là dự án học tập/local. Chưa phải ERP production, chưa có phân quyền chi tiết, nhiều dòng sản phẩm trong một đơn, hóa đơn điện tử hoặc kế toán.

## Yêu cầu
- Windows 10/11, Python 3.11+, Git, VS Code và extension Python.

## Cài đặt và chạy trên Windows + VS Code

Mở PowerShell:

~~~powershell
git clone https://github.com/Duylet/du-an11.git
cd du-an11\python-erp-demo

py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

python -m flask --app app init-db
python -m flask --app app create-admin --username admin
python app.py
~~~

Lệnh tạo admin sẽ yêu cầu nhập mật khẩu. Mở http://127.0.0.1:5000 và đăng nhập bằng tài khoản vừa tạo.

### Nếu PowerShell chặn Activate.ps1

~~~powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m flask --app app init-db
.\.venv\Scripts\python.exe -m flask --app app create-admin --username admin
.\.venv\Scripts\python.exe app.py
~~~

### Trong VS Code
1. File → Open Folder..., mở thư mục python-erp-demo.
2. Ctrl+Shift+P → Python: Select Interpreter → chọn .venv.
3. Terminal → New Terminal.
4. Chạy các lệnh cài đặt, init-db, create-admin ở trên.
5. Chạy python app.py; mở URL localhost trong trình duyệt.
6. Dừng máy chủ bằng Ctrl+C.

### Khóa bí mật

~~~powershell
$env:SECRET_KEY = (python -c "import secrets; print(secrets.token_hex(32))")
~~~

Đặt biến trước khi chạy ứng dụng trong cùng terminal. Không commit khóa bí mật hoặc tệp .env. Debug mặc định tắt; chỉ bật local khi cần bằng $env:FLASK_DEBUG="1".

## Kiểm thử

~~~powershell
pip install pytest
pytest
~~~

## Cấu trúc

~~~text
python-erp-demo/
├── app.py
├── requirements.txt
├── erp_demo.db
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   └── module.html
├── static/style.css
└── tests/test_workflows.py
~~~

Database nằm tại erp_demo.db. Bản nâng cấp bổ sung bảng users, stock_movements và cột updated_at; hãy sao lưu database cũ trước khi nâng cấp nếu dữ liệu quan trọng.

## Ghi chú bảo mật
- Đặt SECRET_KEY riêng trước khi triển khai.
- Không bật Flask debug server khi triển khai ra Internet.
- Tạo tài khoản bằng lệnh CLI; mật khẩu được lưu dạng hash.
- CSRF bảo vệ các thao tác thay đổi dữ liệu.
- SQLite phù hợp demo/local và quy mô nhỏ; workload ghi đồng thời lớn cần database phù hợp hơn.

## Tài liệu
- [Flask configuration](https://flask.palletsprojects.com/en/stable/config/)
- [Flask-WTF CSRF](https://flask-wtf.readthedocs.io/en/latest/csrf/)
- [Flask-Login](https://flask-login.readthedocs.io/)
