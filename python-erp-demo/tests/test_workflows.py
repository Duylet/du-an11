import sqlite3

import pytest
from werkzeug.security import generate_password_hash

from app import app, init_db


@pytest.fixture()
def client(tmp_path):
    database = tmp_path / "test_erp.db"
    app.config.update(TESTING=True, DATABASE=str(database), WTF_CSRF_ENABLED=False, SECRET_KEY="test-secret")
    init_db()
    connection = sqlite3.connect(database)
    connection.execute(
        "INSERT INTO users(username,password_hash,role,created_at) VALUES(?,?,?,?)",
        ("tester", generate_password_hash("test-password"), "admin", "2026-01-01 00:00:00"),
    )
    connection.execute(
        "INSERT INTO products(sku,name,price,stock,created_at) VALUES(?,?,?,?,?)",
        ("SKU-1", "Keyboard", 100000, 5, "2026-01-01 00:00:00"),
    )
    connection.execute(
        "INSERT INTO customers(name,email,phone,created_at) VALUES(?,?,?,?)",
        ("Test Customer", "", "", "2026-01-01 00:00:00"),
    )
    connection.commit()
    connection.close()
    with app.test_client() as test_client:
        yield test_client


def login(client):
    return client.post(
        "/login",
        data={"username": "tester", "password": "test-password"},
        follow_redirects=True,
    )


def stock():
    connection = sqlite3.connect(app.config["DATABASE"])
    value = connection.execute("SELECT stock FROM products WHERE sku='SKU-1'").fetchone()[0]
    connection.close()
    return value


def test_private_pages_require_login(client):
    response = client.get("/products")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_order_deducts_stock_and_cancel_restores_once(client):
    login(client)
    response = client.post("/orders", data={"customer_id": 1, "product_id": 1, "quantity": 3})
    assert response.status_code == 302
    assert stock() == 2

    connection = sqlite3.connect(app.config["DATABASE"])
    order_id = connection.execute("SELECT id FROM orders").fetchone()[0]
    connection.close()

    client.post(f"/orders/{order_id}/status", data={"status": "Đã hủy"})
    assert stock() == 5
    client.post(f"/orders/{order_id}/status", data={"status": "Đã hủy"})
    assert stock() == 5
    client.post(f"/orders/{order_id}/status", data={"status": "Mới"})
    assert stock() == 5


def test_order_cannot_oversell(client):
    login(client)
    client.post("/orders", data={"customer_id": 1, "product_id": 1, "quantity": 99})
    assert stock() == 5
    connection = sqlite3.connect(app.config["DATABASE"])
    count = connection.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    connection.close()
    assert count == 0


def test_stock_adjustment_cannot_go_negative(client):
    login(client)
    client.post("/products/1/stock", data={"change": -9, "reason": "test"})
    assert stock() == 5


def test_completed_revenue_excludes_cancelled_orders(client):
    login(client)
    client.post("/orders", data={"customer_id": 1, "product_id": 1, "quantity": 1})
    connection = sqlite3.connect(app.config["DATABASE"])
    order_id = connection.execute("SELECT id FROM orders").fetchone()[0]
    connection.close()
    client.post(f"/orders/{order_id}/status", data={"status": "Đã hủy"})
    response = client.get("/")
    assert response.status_code == 200
    assert b"DOANH THU HOÀN THÀNH" in response.data


def test_csrf_rejects_post_without_token(client):
    app.config["WTF_CSRF_ENABLED"] = True
    response = client.post("/login", data={"username": "tester", "password": "test-password"})
    assert response.status_code == 400
    app.config["WTF_CSRF_ENABLED"] = False
