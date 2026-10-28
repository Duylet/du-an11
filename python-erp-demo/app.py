import os
import sqlite3
from datetime import datetime
from flask import Flask, abort, flash, g, redirect, render_template, request, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-this")
DATABASE = os.path.join(os.path.dirname(__file__), "erp_demo.db")


def db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_error=None):
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def init_db():
    connection = sqlite3.connect(DATABASE)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            price REAL NOT NULL DEFAULT 0 CHECK(price >= 0),
            stock INTEGER NOT NULL DEFAULT 0 CHECK(stock >= 0),
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL DEFAULT '',
            phone TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL REFERENCES customers(id),
            product_id INTEGER NOT NULL REFERENCES products(id),
            quantity INTEGER NOT NULL CHECK(quantity > 0),
            unit_price REAL NOT NULL,
            total REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Mới',
            created_at TEXT NOT NULL
        );
    """)
    connection.commit()
    connection.close()


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def money(value):
    return f"{value:,.0f} ₫"


@app.template_filter("money")
def money_filter(value):
    return money(value or 0)


@app.route("/")
def dashboard():
    connection = db()
    stats = {
        "products": connection.execute("SELECT COUNT(*) FROM products").fetchone()[0],
        "customers": connection.execute("SELECT COUNT(*) FROM customers").fetchone()[0],
        "orders": connection.execute("SELECT COUNT(*) FROM orders").fetchone()[0],
        "revenue": connection.execute("SELECT COALESCE(SUM(total), 0) FROM orders").fetchone()[0],
        "low_stock": connection.execute("SELECT COUNT(*) FROM products WHERE stock <= 5").fetchone()[0],
    }
    recent_orders = connection.execute("""
        SELECT o.*, c.name AS customer_name, p.name AS product_name
        FROM orders o JOIN customers c ON c.id=o.customer_id
        JOIN products p ON p.id=o.product_id
        ORDER BY o.id DESC LIMIT 5
    """).fetchall()
    return render_template("dashboard.html", stats=stats, recent_orders=recent_orders)


@app.route("/products", methods=["GET", "POST"])
def products():
    connection = db()
    if request.method == "POST":
        sku = request.form.get("sku", "").strip()
        name = request.form.get("name", "").strip()
        try:
            price = float(request.form.get("price", "0"))
            stock = int(request.form.get("stock", "0"))
            if not sku or not name or price < 0 or stock < 0:
                raise ValueError
            connection.execute(
                "INSERT INTO products(sku,name,price,stock,created_at) VALUES(?,?,?,?,?)",
                (sku, name, price, stock, now()),
            )
            connection.commit()
            flash("Đã thêm sản phẩm.", "success")
        except sqlite3.IntegrityError:
            flash("Mã SKU đã tồn tại. Hãy chọn mã khác.", "error")
        except ValueError:
            flash("Vui lòng nhập dữ liệu hợp lệ; giá và tồn kho không được âm.", "error")
        return redirect(url_for("products"))
    rows = connection.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    return render_template("module.html", module="products", title="Sản phẩm", rows=rows)


@app.route("/products/<int:product_id>/stock", methods=["POST"])
def update_stock(product_id):
    try:
        change = int(request.form.get("change", "0"))
    except ValueError:
        flash("Số lượng không hợp lệ.", "error")
        return redirect(url_for("products"))
    connection = db()
    product = connection.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
    if product is None:
        abort(404)
    new_stock = product["stock"] + change
    if new_stock < 0:
        flash("Không thể giảm tồn kho xuống dưới 0.", "error")
    else:
        connection.execute("UPDATE products SET stock=? WHERE id=?", (new_stock, product_id))
        connection.commit()
        flash("Đã cập nhật tồn kho.", "success")
    return redirect(url_for("products"))


@app.route("/products/<int:product_id>/delete", methods=["POST"])
def delete_product(product_id):
    connection = db()
    try:
        connection.execute("DELETE FROM products WHERE id=?", (product_id,))
        connection.commit()
        flash("Đã xóa sản phẩm.", "success")
    except sqlite3.IntegrityError:
        flash("Không thể xóa sản phẩm đã xuất hiện trong đơn hàng.", "error")
    return redirect(url_for("products"))


@app.route("/customers", methods=["GET", "POST"])
def customers():
    connection = db()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        if not name:
            flash("Tên khách hàng là bắt buộc.", "error")
        else:
            connection.execute(
                "INSERT INTO customers(name,email,phone,created_at) VALUES(?,?,?,?)",
                (name, email, phone, now()),
            )
            connection.commit()
            flash("Đã thêm khách hàng.", "success")
        return redirect(url_for("customers"))
    rows = connection.execute("SELECT * FROM customers ORDER BY id DESC").fetchall()
    return render_template("module.html", module="customers", title="Khách hàng", rows=rows)


@app.route("/customers/<int:customer_id>/delete", methods=["POST"])
def delete_customer(customer_id):
    connection = db()
    try:
        connection.execute("DELETE FROM customers WHERE id=?", (customer_id,))
        connection.commit()
        flash("Đã xóa khách hàng.", "success")
    except sqlite3.IntegrityError:
        flash("Không thể xóa khách hàng đã có đơn hàng.", "error")
    return redirect(url_for("customers"))


@app.route("/orders", methods=["GET", "POST"])
def orders():
    connection = db()
    if request.method == "POST":
        try:
            customer_id = int(request.form.get("customer_id", "0"))
            product_id = int(request.form.get("product_id", "0"))
            quantity = int(request.form.get("quantity", "0"))
            customer = connection.execute("SELECT id FROM customers WHERE id=?", (customer_id,)).fetchone()
            product = connection.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
            if customer is None or product is None or quantity <= 0:
                raise ValueError
            if product["stock"] < quantity:
                flash(f"Tồn kho chỉ còn {product['stock']}, không đủ số lượng đặt.", "error")
                return redirect(url_for("orders"))
            total = product["price"] * quantity
            connection.execute(
                "INSERT INTO orders(customer_id,product_id,quantity,unit_price,total,status,created_at) VALUES(?,?,?,?,?,'Mới',?)",
                (customer_id, product_id, quantity, product["price"], total, now()),
            )
            connection.execute("UPDATE products SET stock=stock-? WHERE id=?", (quantity, product_id))
            connection.commit()
            flash("Đã tạo đơn hàng và trừ tồn kho.", "success")
        except ValueError:
            flash("Hãy chọn khách hàng, sản phẩm và số lượng hợp lệ.", "error")
        return redirect(url_for("orders"))
    rows = connection.execute("""
        SELECT o.*, c.name AS customer_name, p.name AS product_name
        FROM orders o JOIN customers c ON c.id=o.customer_id
        JOIN products p ON p.id=o.product_id ORDER BY o.id DESC
    """).fetchall()
    customer_rows = connection.execute("SELECT id,name FROM customers ORDER BY name").fetchall()
    product_rows = connection.execute("SELECT id,name,sku,price,stock FROM products WHERE stock > 0 ORDER BY name").fetchall()
    return render_template("module.html", module="orders", title="Đơn hàng", rows=rows,
                           customer_rows=customer_rows, product_rows=product_rows)


@app.route("/orders/<int:order_id>/status", methods=["POST"])
def order_status(order_id):
    status = request.form.get("status", "")
    if status not in {"Mới", "Đang xử lý", "Hoàn thành", "Đã hủy"}:
        abort(400)
    connection = db()
    order = connection.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    if order is None:
        abort(404)
    # Cancelling restores stock once; reopening a cancelled order reserves it again.
    if status != order["status"] and status == "Đã hủy":
        connection.execute("UPDATE products SET stock=stock+? WHERE id=?", (order["quantity"], order["product_id"]))
    elif status != order["status"] and order["status"] == "Đã hủy":
        product = connection.execute("SELECT stock FROM products WHERE id=?", (order["product_id"],)).fetchone()
        if product["stock"] < order["quantity"]:
            flash("Không đủ tồn kho để mở lại đơn hàng đã hủy.", "error")
            return redirect(url_for("orders"))
        connection.execute("UPDATE products SET stock=stock-? WHERE id=?", (order["quantity"], order["product_id"]))
    connection.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
    connection.commit()
    flash("Đã cập nhật trạng thái đơn hàng.", "success")
    return redirect(url_for("orders"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
