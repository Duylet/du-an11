import os
import sqlite3
from datetime import datetime

import click
from flask import Flask, abort, flash, g, redirect, render_template, request, url_for
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.environ.get("ERP_DATABASE", os.path.join(BASE_DIR, "erp_demo.db"))
STATUSES = ("Mới", "Đang xử lý", "Hoàn thành", "Đã hủy")
TRANSITIONS = {
    "Mới": {"Đang xử lý", "Đã hủy"},
    "Đang xử lý": {"Hoàn thành", "Đã hủy"},
    "Hoàn thành": set(),
    "Đã hủy": set(),
}

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY") or "local-demo-key-change-before-deploy",
    DATABASE=DATABASE,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    REMEMBER_COOKIE_HTTPONLY=True,
)
csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Vui lòng đăng nhập để tiếp tục."
login_manager.login_message_category = "warning"


class User(UserMixin):
    def __init__(self, row):
        self.id = str(row["id"])
        self.username = row["username"]
        self.role = row["role"]


@login_manager.user_loader
def load_user(user_id):
    row = get_db().execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    return User(row) if row else None


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"], timeout=10)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
        g.db.execute("PRAGMA busy_timeout = 10000")
    return g.db


@app.teardown_appcontext
def close_db(_error=None):
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def init_db():
    os.makedirs(os.path.dirname(app.config["DATABASE"]) or ".", exist_ok=True)
    connection = sqlite3.connect(app.config["DATABASE"])
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'admin',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            price INTEGER NOT NULL DEFAULT 0 CHECK(price >= 0),
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
            unit_price INTEGER NOT NULL CHECK(unit_price >= 0),
            total INTEGER NOT NULL CHECK(total >= 0),
            status TEXT NOT NULL DEFAULT 'Mới',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS stock_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL REFERENCES products(id),
            change_qty INTEGER NOT NULL CHECK(change_qty != 0),
            reason TEXT NOT NULL,
            reference TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_orders_created ON orders(created_at);
        CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
        CREATE INDEX IF NOT EXISTS idx_movements_product ON stock_movements(product_id, id DESC);
    """)
    # Safe additive migration for databases created by the earlier demo.
    columns = {row[1] for row in connection.execute("PRAGMA table_info(products)")}
    if "updated_at" not in columns:
        connection.execute("ALTER TABLE products ADD COLUMN updated_at TEXT")
    connection.commit()
    connection.close()


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def money(value):
    return f"{int(value or 0):,} ₫"


@app.template_filter("money")
def money_filter(value):
    return money(value)


@app.context_processor
def inject_globals():
    return {"current_year": datetime.now().year}


@app.cli.command("init-db")
def init_db_command():
    init_db()
    click.echo("SQLite database initialized.")


@app.cli.command("create-admin")
@click.option("--username", prompt=True)
@click.password_option()
def create_admin_command(username, password):
    init_db()
    connection = sqlite3.connect(app.config["DATABASE"])
    try:
        connection.execute(
            "INSERT INTO users(username,password_hash,role,created_at) VALUES(?,?,?,?)",
            (username.strip(), generate_password_hash(password), "admin", now()),
        )
        connection.commit()
        click.echo(f"Admin account '{username}' created.")
    except sqlite3.IntegrityError:
        raise click.ClickException("Username already exists.")
    finally:
        connection.close()


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        row = get_db().execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if row and check_password_hash(row["password_hash"], password):
            login_user(User(row), remember=bool(request.form.get("remember")))
            flash("Đăng nhập thành công.", "success")
            next_url = request.args.get("next", "")
            if next_url.startswith("/") and not next_url.startswith("//"):
                return redirect(next_url)
            return redirect(url_for("dashboard"))
        flash("Tên đăng nhập hoặc mật khẩu không đúng.", "error")
    return render_template("login.html")


@app.post("/logout")
@login_required
def logout():
    logout_user()
    flash("Bạn đã đăng xuất.", "success")
    return redirect(url_for("login"))


@app.route("/")
@login_required
def dashboard():
    connection = get_db()
    stats = {
        "products": connection.execute("SELECT COUNT(*) FROM products").fetchone()[0],
        "customers": connection.execute("SELECT COUNT(*) FROM customers").fetchone()[0],
        "orders": connection.execute("SELECT COUNT(*) FROM orders").fetchone()[0],
        "revenue": connection.execute("SELECT COALESCE(SUM(total),0) FROM orders WHERE status='Hoàn thành'").fetchone()[0],
        "pipeline": connection.execute("SELECT COALESCE(SUM(total),0) FROM orders WHERE status IN ('Mới','Đang xử lý')").fetchone()[0],
        "low_stock": connection.execute("SELECT COUNT(*) FROM products WHERE stock <= 5").fetchone()[0],
    }
    recent_orders = connection.execute("""
        SELECT o.*, c.name AS customer_name, p.name AS product_name
        FROM orders o JOIN customers c ON c.id=o.customer_id
        JOIN products p ON p.id=o.product_id ORDER BY o.id DESC LIMIT 6
    """).fetchall()
    return render_template("dashboard.html", stats=stats, recent_orders=recent_orders)


@app.route("/products", methods=["GET", "POST"])
@login_required
def products():
    connection = get_db()
    if request.method == "POST":
        sku, name = request.form.get("sku", "").strip(), request.form.get("name", "").strip()
        try:
            price, stock = int(request.form.get("price", "0")), int(request.form.get("stock", "0"))
            if not sku or not name or price < 0 or stock < 0:
                raise ValueError
            connection.execute(
                "INSERT INTO products(sku,name,price,stock,created_at) VALUES(?,?,?,?,?)",
                (sku, name, price, stock, now()),
            )
            product_id = connection.execute("SELECT last_insert_rowid()").fetchone()[0]
            if stock:
                connection.execute(
                    "INSERT INTO stock_movements(product_id,change_qty,reason,created_at) VALUES(?,?,?,?)",
                    (product_id, stock, "Tồn kho ban đầu", now()),
                )
            connection.commit()
            flash("Đã thêm sản phẩm.", "success")
        except sqlite3.IntegrityError:
            connection.rollback()
            flash("Mã SKU đã tồn tại.", "error")
        except (ValueError, TypeError):
            connection.rollback()
            flash("Giá và tồn kho phải là số nguyên không âm; SKU và tên không được trống.", "error")
        return redirect(url_for("products"))
    q = request.args.get("q", "").strip()
    rows = connection.execute(
        "SELECT * FROM products WHERE sku LIKE ? OR name LIKE ? ORDER BY id DESC",
        (f"%{q}%", f"%{q}%"),
    ).fetchall()
    return render_template("module.html", module="products", title="Sản phẩm & kho", rows=rows, q=q)


@app.post("/products/<int:product_id>/edit")
@login_required
def edit_product(product_id):
    connection = get_db()
    name = request.form.get("name", "").strip()
    try:
        price = int(request.form.get("price", ""))
        if not name or price < 0:
            raise ValueError
        cursor = connection.execute("UPDATE products SET name=?,price=?,updated_at=? WHERE id=?",
                                    (name, price, now(), product_id))
        if cursor.rowcount == 0:
            abort(404)
        connection.commit()
        flash("Đã cập nhật sản phẩm.", "success")
    except ValueError:
        flash("Tên và giá sản phẩm không hợp lệ.", "error")
    return redirect(url_for("products"))


@app.post("/products/<int:product_id>/stock")
@login_required
def update_stock(product_id):
    try:
        change = int(request.form.get("change", "0"))
        if change == 0:
            raise ValueError
    except ValueError:
        flash("Số lượng điều chỉnh phải là số nguyên khác 0.", "error")
        return redirect(url_for("products"))
    connection = get_db()
    try:
        connection.execute("BEGIN IMMEDIATE")
        cursor = connection.execute(
            "UPDATE products SET stock=stock+?,updated_at=? WHERE id=? AND stock+? >= 0",
            (change, now(), product_id, change),
        )
        if cursor.rowcount != 1:
            exists = connection.execute("SELECT id FROM products WHERE id=?", (product_id,)).fetchone()
            connection.rollback()
            if not exists:
                abort(404)
            flash("Không thể giảm tồn kho xuống dưới 0.", "error")
            return redirect(url_for("products"))
        connection.execute(
            "INSERT INTO stock_movements(product_id,change_qty,reason,created_at) VALUES(?,?,?,?)",
            (product_id, change, request.form.get("reason", "Điều chỉnh thủ công").strip()[:120] or "Điều chỉnh thủ công", now()),
        )
        connection.commit()
        flash("Đã cập nhật tồn kho và ghi lịch sử.", "success")
    except Exception:
        connection.rollback()
        raise
    return redirect(url_for("products"))


@app.post("/products/<int:product_id>/delete")
@login_required
def delete_product(product_id):
    connection = get_db()
    try:
        connection.execute("DELETE FROM products WHERE id=?", (product_id,))
        connection.commit()
        flash("Đã xóa sản phẩm.", "success")
    except sqlite3.IntegrityError:
        connection.rollback()
        flash("Không thể xóa sản phẩm đã có đơn hàng hoặc lịch sử kho.", "error")
    return redirect(url_for("products"))


@app.route("/customers", methods=["GET", "POST"])
@login_required
def customers():
    connection = get_db()
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
    q = request.args.get("q", "").strip()
    rows = connection.execute(
        "SELECT * FROM customers WHERE name LIKE ? OR email LIKE ? OR phone LIKE ? ORDER BY id DESC",
        (f"%{q}%", f"%{q}%", f"%{q}%"),
    ).fetchall()
    return render_template("module.html", module="customers", title="Khách hàng", rows=rows, q=q)


@app.post("/customers/<int:customer_id>/edit")
@login_required
def edit_customer(customer_id):
    connection = get_db()
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    if not name:
        flash("Tên khách hàng không được để trống.", "error")
    else:
        cursor = connection.execute("UPDATE customers SET name=?,email=?,phone=? WHERE id=?",
                                    (name, email, phone, customer_id))
        if cursor.rowcount == 0:
            abort(404)
        connection.commit()
        flash("Đã cập nhật khách hàng.", "success")
    return redirect(url_for("customers"))


@app.post("/customers/<int:customer_id>/delete")
@login_required
def delete_customer(customer_id):
    connection = get_db()
    try:
        connection.execute("DELETE FROM customers WHERE id=?", (customer_id,))
        connection.commit()
        flash("Đã xóa khách hàng.", "success")
    except sqlite3.IntegrityError:
        connection.rollback()
        flash("Không thể xóa khách hàng đã có đơn hàng.", "error")
    return redirect(url_for("customers"))


@app.route("/orders", methods=["GET", "POST"])
@login_required
def orders():
    connection = get_db()
    if request.method == "POST":
        try:
            customer_id = int(request.form.get("customer_id", "0"))
            product_id = int(request.form.get("product_id", "0"))
            quantity = int(request.form.get("quantity", "0"))
            if quantity <= 0:
                raise ValueError
        except ValueError:
            flash("Hãy chọn khách hàng, sản phẩm và số lượng hợp lệ.", "error")
            return redirect(url_for("orders"))
        try:
            connection.execute("BEGIN IMMEDIATE")
            customer = connection.execute("SELECT id FROM customers WHERE id=?", (customer_id,)).fetchone()
            product = connection.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
            if not customer or not product:
                raise ValueError("Không tìm thấy khách hàng hoặc sản phẩm.")
            cursor = connection.execute(
                "UPDATE products SET stock=stock-?,updated_at=? WHERE id=? AND stock>=?",
                (quantity, now(), product_id, quantity),
            )
            if cursor.rowcount != 1:
                connection.rollback()
                flash("Tồn kho không đủ cho số lượng yêu cầu.", "error")
                return redirect(url_for("orders"))
            total = int(product["price"]) * quantity
            connection.execute(
                "INSERT INTO orders(customer_id,product_id,quantity,unit_price,total,status,created_at) VALUES(?,?,?,?,?,'Mới',?)",
                (customer_id, product_id, quantity, int(product["price"]), total, now()),
            )
            connection.execute(
                "INSERT INTO stock_movements(product_id,change_qty,reason,reference,created_at) VALUES(?,?,?,?,?)",
                (product_id, -quantity, "Xuất kho tạo đơn", f"Đơn #{connection.execute('SELECT last_insert_rowid()').fetchone()[0]}", now()),
            )
            connection.commit()
            flash("Đã tạo đơn hàng và trừ kho.", "success")
        except ValueError as error:
            connection.rollback()
            flash(str(error), "error")
        except Exception:
            connection.rollback()
            raise
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


@app.post("/orders/<int:order_id>/status")
@login_required
def order_status(order_id):
    status = request.form.get("status", "")
    if status not in STATUSES:
        abort(400)
    connection = get_db()
    try:
        connection.execute("BEGIN IMMEDIATE")
        order = connection.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
        if order is None:
            abort(404)
        if status == order["status"]:
            connection.rollback()
            flash("Đơn hàng đang ở trạng thái này.", "info")
            return redirect(url_for("orders"))
        if status not in TRANSITIONS[order["status"]]:
            connection.rollback()
            flash("Không thể chuyển đơn hàng từ trạng thái hiện tại sang trạng thái đã chọn.", "error")
            return redirect(url_for("orders"))
        if status == "Đã hủy":
            connection.execute("UPDATE products SET stock=stock+?,updated_at=? WHERE id=?",
                               (order["quantity"], now(), order["product_id"]))
            connection.execute(
                "INSERT INTO stock_movements(product_id,change_qty,reason,reference,created_at) VALUES(?,?,?,?,?)",
                (order["product_id"], order["quantity"], "Hoàn kho do hủy đơn", f"Đơn #{order_id}", now()),
            )
        connection.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
        connection.commit()
        flash("Đã cập nhật trạng thái đơn hàng.", "success")
    except Exception:
        connection.rollback()
        raise
    return redirect(url_for("orders"))


@app.route("/inventory")
@login_required
def inventory():
    rows = get_db().execute("""
        SELECT m.*, p.sku, p.name AS product_name
        FROM stock_movements m JOIN products p ON p.id=m.product_id
        ORDER BY m.id DESC LIMIT 200
    """).fetchall()
    return render_template("module.html", module="inventory", title="Lịch sử kho", rows=rows)


if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=os.environ.get("FLASK_DEBUG") == "1")
