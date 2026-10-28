# Mini ERP Demo — Python Flask + SQLite

Ứng dụng quản lý doanh nghiệp đơn giản viết bằng **Python Flask** và **SQLite**, chạy trực tiếp trên Windows trong VS Code. Đây là dự án học tập độc lập, không cần Docker, MariaDB hay Redis.

## Chức năng

- **Bảng điều khiển:** tổng số sản phẩm, khách hàng, đơn hàng, tổng giá trị đơn và cảnh báo tồn kho thấp.
- **Sản phẩm & kho:** thêm sản phẩm, SKU duy nhất, giá bán, tồn kho; tăng/giảm tồn kho; không cho tồn kho âm.
- **Khách hàng:** thêm và xem tên, email, số điện thoại.
- **Đơn hàng:** tạo đơn cho khách hàng và sản phẩm; tự kiểm tra tồn kho, tính tổng tiền và trừ kho khi đặt hàng; đổi trạng thái đơn. Hủy đơn sẽ hoàn kho.
- **SQLite:** tự tạo cơ sở dữ liệu `erp_demo.db` ở lần chạy đầu tiên.

## Yêu cầu

- Windows 10/11
- Python 3.11 trở lên (khuyến nghị)
- Git và VS Code
- VS Code extension **Python** (Microsoft)

## Chạy trên Windows + VS Code

Mở PowerShell ở thư mục bạn muốn lưu dự án:

```powershell
git clone https://github.com/Duylet/du-an11.git
cd du-an11
cd python-erp-demo
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

Nếu PowerShell chặn kích hoạt môi trường ảo, bạn có thể bỏ qua bước Activate và gọi Python trong môi trường ảo trực tiếp:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Mở trình duyệt tại **http://127.0.0.1:5000**. Giữ cửa sổ terminal đang chạy ứng dụng. Nhấn **Ctrl+C** trong terminal để dừng.

### Mở bằng VS Code

1. Chọn **File → Open Folder...** và mở thư mục `python-erp-demo`.
2. Mở Terminal → New Terminal.
3. Chạy các lệnh tạo môi trường và cài thư viện ở trên.
4. Chạy `python app.py`, rồi mở địa chỉ localhost trong trình duyệt.

## Dùng thử

1. Vào **Sản phẩm & kho**, thêm sản phẩm ví dụ: SKU `SP-001`, tên `Bàn phím`, giá `250000`, tồn kho `20`.
2. Vào **Khách hàng**, thêm một khách hàng thử nghiệm.
3. Vào **Đơn hàng**, chọn khách hàng và sản phẩm, nhập số lượng rồi tạo đơn.
4. Quay lại **Sản phẩm & kho** để thấy tồn kho giảm.
5. Thử đổi trạng thái đơn sang **Đã hủy**; số lượng hàng sẽ được hoàn lại kho.

## Cấu trúc

```text
python-erp-demo/
├── app.py
├── requirements.txt
├── .gitignore
├── README.md
├── erp_demo.db          # tự sinh khi chạy, không commit lên Git
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   └── module.html
└── static/
    └── style.css
```

## Lưu ý

- Đây là demo chạy local, chưa có đăng nhập/phân quyền, hóa đơn thuế, kế toán kép hay bảo mật dành cho triển khai thực tế.
- Dữ liệu được lưu trong `erp_demo.db`. Sao lưu tệp này nếu cần giữ dữ liệu; xóa nó sẽ xóa dữ liệu demo.
- Flask debug server chỉ dùng để phát triển trên máy cá nhân, không dùng làm máy chủ production.
- SQLite được tích hợp trong Python nên không cần cài riêng database server.

## Tài liệu tham khảo

- [Flask Quickstart](https://flask.palletsprojects.com/en/stable/quickstart/)
- [Flask: Define and Access the Database](https://flask.palletsprojects.com/en/stable/tutorial/database/)
- [Flask trong VS Code](https://code.visualstudio.com/docs/python/tutorial-flask)
