import sqlite3
import os
import string
from datetime import datetime

BUYER_DB = os.path.join(os.path.dirname(__file__), "apex_buyer.db")


def get_buyer_db():
    conn = sqlite3.connect(BUYER_DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_buyer_db() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS buybacks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                token TEXT NOT NULL,
                seller_user_id INTEGER,
                buyer_user_id INTEGER,
                product_id TEXT,
                product_name TEXT,
                buyback_price INTEGER,
                status TEXT DEFAULT 'completed',
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS buyer_balances (
                user_id INTEGER PRIMARY KEY,
                balance INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS damaged_tokens (
                token TEXT PRIMARY KEY,
                damage_type TEXT,
                proxy_type TEXT,
                cert_type TEXT,
                price INTEGER
            );
        """)
    try:
        with get_buyer_db() as db:
            db.execute("ALTER TABLE damaged_tokens ADD COLUMN price INTEGER")
    except:
        pass
    try:
        with get_buyer_db() as db:
            db.execute("ALTER TABLE buyer_balances ADD COLUMN min_withdrawal INTEGER DEFAULT 40000")
    except:
        pass
    try:
        with get_buyer_db() as db:
            db.execute("UPDATE buyer_balances SET min_withdrawal = 40000 WHERE min_withdrawal IS NULL")
    except:
        pass


def is_valid_token_format(token: str) -> bool:
    return (
        isinstance(token, str)
        and len(token) == 28
        and all(c in string.ascii_lowercase + string.digits for c in token)
    )


def lookup_token(token: str) -> dict | None:
    if not is_valid_token_format(token):
        return None
    return {
        "id": 0,
        "token": token,
        "product_id": "dns_eco",
        "product_name": "ZEN-токен",
        "status": "confirmed",
    }


def get_token_meta(token: str) -> dict | None:
    return None


def is_token_bought(token: str) -> bool:
    with get_buyer_db() as db:
        row = db.execute(
            "SELECT id FROM buybacks WHERE token = ?", (token,)
        ).fetchone()
        return row is not None


def create_buyback(order_id: int, token: str, seller_user_id: int, buyer_user_id: int, product_id: str, product_name: str, buyback_price: int) -> int:
    with get_buyer_db() as db:
        cur = db.execute(
            "INSERT INTO buybacks (order_id, token, seller_user_id, buyer_user_id, product_id, product_name, buyback_price) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (order_id, token, seller_user_id, buyer_user_id, product_id, product_name, buyback_price),
        )
        return cur.lastrowid


def get_token_damage(token: str) -> dict | None:
    with get_buyer_db() as db:
        row = db.execute(
            "SELECT * FROM damaged_tokens WHERE token = ?", (token,)
        ).fetchone()
        return dict(row) if row else None


def save_token_damage(token: str, damage_type: str, proxy_type: str | None = None, cert_type: str | None = None):
    with get_buyer_db() as db:
        db.execute(
            "INSERT INTO damaged_tokens (token, damage_type, proxy_type, cert_type) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(token) DO UPDATE SET damage_type=excluded.damage_type, proxy_type=excluded.proxy_type, cert_type=excluded.cert_type",
            (token, damage_type, proxy_type, cert_type),
        )


def get_token_price(token: str) -> int | None:
    with get_buyer_db() as db:
        row = db.execute(
            "SELECT price FROM damaged_tokens WHERE token = ? AND price IS NOT NULL", (token,)
        ).fetchone()
        return row["price"] if row else None


def save_token_price(token: str, price: int):
    with get_buyer_db() as db:
        db.execute(
            "INSERT INTO damaged_tokens (token, damage_type, price) VALUES (?, '', ?) ON CONFLICT(token) DO UPDATE SET price = ?",
            (token, price, price),
        )


def add_buyer_balance(user_id: int, amount: int):
    with get_buyer_db() as db:
        cur = db.execute(
            "INSERT INTO buyer_balances (user_id, balance, min_withdrawal) VALUES (?, ?, 40000) ON CONFLICT(user_id) DO UPDATE SET balance = balance + ?",
            (user_id, amount, amount),
        )


def get_buyer_user(user_id: int) -> dict | None:
    with get_buyer_db() as db:
        row = db.execute(
            "SELECT * FROM buyer_balances WHERE user_id = ?", (user_id,)
        ).fetchone()
        return dict(row) if row else None


def update_min_withdrawal(user_id: int, new_min: int):
    with get_buyer_db() as db:
        db.execute(
            "UPDATE buyer_balances SET min_withdrawal = ? WHERE user_id = ?",
            (new_min, user_id),
        )


def get_buyback_stats(user_id: int) -> tuple[int, int]:
    with get_buyer_db() as db:
        row = db.execute(
            "SELECT COUNT(*) as cnt, COALESCE(SUM(buyback_price), 0) as total FROM buybacks WHERE seller_user_id = ?",
            (user_id,),
        ).fetchone()
        return (row["cnt"], row["total"])
