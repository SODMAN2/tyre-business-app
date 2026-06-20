import os
import re
import sqlite3
from datetime import date, datetime

import pandas as pd
import streamlit as st


DB_NAME = "tyre_business.db"
LOW_STOCK_LIMIT = 5
WALK_IN_CUSTOMER = "Walk-in Customer"
REGULAR_CUSTOMER = "Regular Customer"
PAYMENT_METHODS = ["Cash", "POS", "Bank Transfer", "Credit", "Other"]


def get_database_url():
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    try:
        database_url = st.secrets.get("DATABASE_URL")
        if database_url:
            return database_url

        database_secrets = st.secrets.get("database", {})
        if hasattr(database_secrets, "get"):
            return database_secrets.get("url")
    except Exception:
        return None

    return None


def get_app_password():
    try:
        return st.secrets.get("APP_PASSWORD")
    except Exception:
        return None


def require_login():
    app_password = get_app_password()

    if not app_password:
        st.warning("APP_PASSWORD is missing. The app is not password protected during local development.")
        return True

    if st.session_state.get("logged_in"):
        return True

    st.title("Tyre Business App")
    st.subheader("Password Required")

    with st.form("login_form"):
        entered_password = st.text_input("Password", type="password")
        login_clicked = st.form_submit_button("Login")

    if login_clicked:
        if entered_password == app_password:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Incorrect password. Please try again.")

    return False


def using_postgres():
    return bool(get_database_url())


class PostgresCursor:
    def __init__(self, cursor):
        self.cursor = cursor
        self.lastrowid = None

    def execute(self, query, params=None):
        query = prepare_postgres_query(query)
        query = add_postgres_returning_id(query)
        params = tuple(params or ())
        self.cursor.execute(query, params)

        if query.rstrip().upper().endswith("RETURNING ID"):
            row = self.cursor.fetchone()
            self.lastrowid = row[0] if row else None
        else:
            self.lastrowid = None

        return self

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()

    @property
    def description(self):
        return self.cursor.description


class PostgresConnection:
    def __init__(self, connection):
        self.connection = connection

    def cursor(self):
        return PostgresCursor(self.connection.cursor())

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()

    def close(self):
        self.connection.close()


def prepare_postgres_query(query):
    query = query.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
    query = query.replace("?", "%s")
    return query


def add_postgres_returning_id(query):
    clean_query = query.strip()
    if re.match(r"INSERT\s+INTO\s+(stock|customers|sales|sale_items|payments)\b", clean_query, re.IGNORECASE):
        if "RETURNING" not in clean_query.upper():
            return f"{query.rstrip()} RETURNING id"
    return query


def get_connection():
    database_url = get_database_url()
    if database_url:
        import psycopg2

        return PostgresConnection(psycopg2.connect(database_url))

    return sqlite3.connect(DB_NAME)


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            size TEXT NOT NULL,
            brand TEXT NOT NULL,
            pattern_model TEXT,
            condition TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            buying_price REAL NOT NULL,
            selling_price REAL NOT NULL,
            supplier TEXT,
            date_added TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_type TEXT NOT NULL,
            name TEXT NOT NULL,
            phone TEXT,
            address TEXT,
            vehicle_type TEXT,
            notes TEXT,
            created_at TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT,
            customer_id INTEGER,
            customer_type TEXT,
            customer_name TEXT,
            phone TEXT,
            total_quantity INTEGER,
            total_amount REAL,
            total_cost REAL,
            total_profit REAL,
            payment_method TEXT,
            amount_paid REAL,
            balance REAL,
            payment_status TEXT,
            sale_date TEXT NOT NULL,
            created_at TEXT,
            stock_id INTEGER,
            size TEXT,
            brand TEXT,
            pattern_model TEXT,
            condition TEXT,
            quantity_sold INTEGER,
            selling_price REAL,
            buying_price REAL,
            profit REAL,
            FOREIGN KEY (customer_id) REFERENCES customers (id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sale_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER NOT NULL,
            stock_id INTEGER NOT NULL,
            size TEXT NOT NULL,
            brand TEXT NOT NULL,
            pattern_model TEXT,
            condition TEXT NOT NULL,
            quantity_sold INTEGER NOT NULL,
            selling_price REAL NOT NULL,
            buying_price REAL NOT NULL,
            line_total REAL NOT NULL,
            line_cost REAL NOT NULL,
            line_profit REAL NOT NULL,
            FOREIGN KEY (sale_id) REFERENCES sales (id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER NOT NULL,
            payment_date TEXT NOT NULL,
            payment_method TEXT NOT NULL,
            amount_paid REAL NOT NULL,
            payment_note TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (sale_id) REFERENCES sales (id)
        )
        """
    )

    migrate_database(cursor)

    conn.commit()
    conn.close()


def migrate_database(cursor):
    add_column_if_missing(cursor, "stock", "pattern_model", "TEXT")

    sales_columns = {
        "invoice_number": "TEXT",
        "customer_id": "INTEGER",
        "customer_type": "TEXT",
        "customer_name": "TEXT",
        "phone": "TEXT",
        "address": "TEXT",
        "vehicle_type": "TEXT",
        "customer_notes": "TEXT",
        "total_quantity": "INTEGER",
        "total_amount": "REAL",
        "total_cost": "REAL",
        "total_profit": "REAL",
        "payment_method": "TEXT",
        "amount_paid": "REAL",
        "balance": "REAL",
        "payment_status": "TEXT",
        "promised_payment_date": "TEXT",
        "follow_up_note": "TEXT",
        "created_at": "TEXT",
        "stock_id": "INTEGER",
        "size": "TEXT",
        "brand": "TEXT",
        "pattern_model": "TEXT",
        "condition": "TEXT",
        "quantity_sold": "INTEGER",
        "selling_price": "REAL",
        "buying_price": "REAL",
        "profit": "REAL",
        "sale_status": "TEXT DEFAULT 'Active'",
        "cancellation_reason": "TEXT",
        "cancelled_at": "TEXT",
    }

    for column_name, column_type in sales_columns.items():
        add_column_if_missing(cursor, "sales", column_name, column_type)

    add_column_if_missing(cursor, "sale_items", "item_status", "TEXT DEFAULT 'Active'")
    add_column_if_missing(cursor, "payments", "payment_status", "TEXT DEFAULT 'Active'")
    add_column_if_missing(cursor, "payments", "cancelled_at", "TEXT")

    cursor.execute("UPDATE sales SET sale_status = 'Active' WHERE sale_status IS NULL OR sale_status = ''")
    cursor.execute("UPDATE sale_items SET item_status = 'Active' WHERE item_status IS NULL OR item_status = ''")
    cursor.execute("UPDATE payments SET payment_status = 'Active' WHERE payment_status IS NULL OR payment_status = ''")

    migrate_legacy_sales(cursor)
    migrate_legacy_payments(cursor)


def add_column_if_missing(cursor, table_name, column_name, column_type):
    if using_postgres():
        cursor.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
                AND table_name = ?
            """,
            (table_name,),
        )
        existing_columns = [row[0] for row in cursor.fetchall()]
    else:
        cursor.execute(f"PRAGMA table_info({table_name})")
        existing_columns = [row[1] for row in cursor.fetchall()]

    if column_name not in existing_columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")


def migrate_legacy_sales(cursor):
    cursor.execute(
        """
        SELECT
            s.id,
            s.stock_id,
            s.size,
            s.brand,
            COALESCE(s.pattern_model, ''),
            s.condition,
            s.quantity_sold,
            s.selling_price,
            s.buying_price,
            s.profit,
            s.sale_date
        FROM sales s
        LEFT JOIN sale_items si ON si.sale_id = s.id
        WHERE si.id IS NULL
            AND s.stock_id IS NOT NULL
            AND s.quantity_sold IS NOT NULL
        """
    )
    legacy_sales = cursor.fetchall()

    for sale in legacy_sales:
        (
            sale_id,
            stock_id,
            size,
            brand,
            pattern_model,
            condition,
            quantity_sold,
            selling_price,
            buying_price,
            profit,
            sale_date,
        ) = sale
        line_total = float(selling_price or 0) * int(quantity_sold or 0)
        line_cost = float(buying_price or 0) * int(quantity_sold or 0)
        line_profit = float(profit or (line_total - line_cost))

        cursor.execute(
            """
            INSERT INTO sale_items
            (
                sale_id,
                stock_id,
                size,
                brand,
                pattern_model,
                condition,
                quantity_sold,
                selling_price,
                buying_price,
                line_total,
                line_cost,
                line_profit
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                sale_id,
                stock_id,
                size,
                brand,
                pattern_model,
                condition,
                int(quantity_sold or 0),
                float(selling_price or 0),
                float(buying_price or 0),
                line_total,
                line_cost,
                line_profit,
            ),
        )

        cursor.execute(
            """
            UPDATE sales
            SET
                invoice_number = COALESCE(invoice_number, ?),
                customer_type = COALESCE(customer_type, ?),
                customer_name = COALESCE(customer_name, ?),
                total_quantity = COALESCE(total_quantity, ?),
                total_amount = COALESCE(total_amount, ?),
                total_cost = COALESCE(total_cost, ?),
                total_profit = COALESCE(total_profit, ?),
                payment_method = COALESCE(payment_method, ?),
                amount_paid = COALESCE(amount_paid, ?),
                balance = COALESCE(balance, ?),
                payment_status = COALESCE(payment_status, ?),
                created_at = COALESCE(created_at, ?)
            WHERE id = ?
            """,
            (
                make_invoice_number(sale_id),
                WALK_IN_CUSTOMER,
                WALK_IN_CUSTOMER,
                int(quantity_sold or 0),
                line_total,
                line_cost,
                line_profit,
                "Cash",
                line_total,
                0.0,
                "Paid",
                str(sale_date or date.today()),
                sale_id,
            ),
        )


def migrate_legacy_payments(cursor):
    cursor.execute(
        """
        SELECT
            s.id,
            s.sale_date,
            COALESCE(s.payment_method, 'Cash'),
            COALESCE(s.amount_paid, s.total_amount, 0)
        FROM sales s
        LEFT JOIN payments p ON p.sale_id = s.id
        WHERE p.id IS NULL
            AND COALESCE(s.amount_paid, s.total_amount, 0) > 0
        """
    )
    sales_without_payments = cursor.fetchall()
    now = datetime.now().isoformat(timespec="seconds")

    for sale_id, sale_date, payment_method, amount_paid in sales_without_payments:
        cursor.execute(
            """
            INSERT INTO payments
            (sale_id, payment_date, payment_method, amount_paid, payment_note, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                sale_id,
                str(sale_date or date.today()),
                payment_method or "Cash",
                float(amount_paid or 0),
                "Migrated from old sale payment",
                now,
            ),
        )


def make_invoice_number(sale_id):
    return f"INV-{sale_id:06d}"


def run_query(query, params=()):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    columns = [column[0] for column in cursor.description]
    df = pd.DataFrame(cursor.fetchall(), columns=columns)
    conn.close()
    return df


def add_stock(
    size,
    brand,
    pattern_model,
    condition,
    quantity,
    buying_price,
    selling_price,
    supplier,
    date_added,
):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO stock
        (
            size,
            brand,
            pattern_model,
            condition,
            quantity,
            buying_price,
            selling_price,
            supplier,
            date_added
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            size,
            brand,
            pattern_model,
            condition,
            quantity,
            buying_price,
            selling_price,
            supplier,
            str(date_added),
        ),
    )
    conn.commit()
    conn.close()


def delete_stock_item(stock_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM stock WHERE id = ?", (stock_id,))
    conn.commit()
    conn.close()


def clear_all_app_data():
    conn = get_connection()
    cursor = conn.cursor()
    if using_postgres():
        cursor.execute("TRUNCATE payments, sale_items, sales, customers, stock RESTART IDENTITY CASCADE")
    else:
        cursor.execute("DELETE FROM payments")
        cursor.execute("DELETE FROM sale_items")
        cursor.execute("DELETE FROM sales")
        cursor.execute("DELETE FROM customers")
        cursor.execute("DELETE FROM stock")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('payments', 'sale_items', 'sales', 'customers', 'stock')")
    conn.commit()
    conn.close()


def get_or_create_customer(cursor, customer_type, name, phone, address, vehicle_type, notes):
    if customer_type == WALK_IN_CUSTOMER:
        return None, name.strip() or WALK_IN_CUSTOMER

    clean_name = name.strip()
    clean_phone = phone.strip()

    existing_customer_id = None
    if clean_phone:
        cursor.execute(
            """
            SELECT id FROM customers
            WHERE customer_type = ? AND phone = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (REGULAR_CUSTOMER, clean_phone),
        )
        row = cursor.fetchone()
        existing_customer_id = row[0] if row else None

    if existing_customer_id:
        cursor.execute(
            """
            UPDATE customers
            SET name = ?, address = ?, vehicle_type = ?, notes = ?
            WHERE id = ?
            """,
            (clean_name, address.strip(), vehicle_type.strip(), notes.strip(), existing_customer_id),
        )
        customer_id = existing_customer_id
    else:
        cursor.execute(
            """
            INSERT INTO customers
            (customer_type, name, phone, address, vehicle_type, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                REGULAR_CUSTOMER,
                clean_name,
                clean_phone,
                address.strip(),
                vehicle_type.strip(),
                notes.strip(),
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        customer_id = cursor.lastrowid

    return customer_id, clean_name


def calculate_payment_status(total_amount, amount_paid):
    balance = max(total_amount - amount_paid, 0.0)
    if amount_paid >= total_amount and total_amount > 0:
        status = "Paid"
    elif amount_paid > 0:
        status = "Part Payment"
    else:
        status = "Unpaid"
    return balance, status


def get_payment_methods_summary(payment_lines):
    totals = {}
    for payment in payment_lines:
        method = payment["payment_method"]
        totals[method] = totals.get(method, 0.0) + float(payment["amount_paid"])
    return "; ".join(f"{method} {format_currency(amount)}" for method, amount in totals.items())


def add_payment_to_current_sale(payment_date, payment_method, amount_paid, payment_note):
    payment = {
        "payment_date": str(payment_date),
        "payment_method": payment_method,
        "amount_paid": float(amount_paid),
        "payment_note": payment_note.strip(),
    }
    st.session_state.sale_payments.append(payment)


def get_payments_dataframe(payment_lines=None):
    payments = st.session_state.sale_payments if payment_lines is None else payment_lines
    if not payments:
        return pd.DataFrame()
    return pd.DataFrame(payments).rename(
        columns={
            "payment_date": "Payment Date",
            "payment_method": "Payment Method",
            "amount_paid": "Amount Paid",
            "payment_note": "Payment Note / Reference",
        }
    )


def update_sale_payment_totals(cursor, sale_id):
    cursor.execute(
        """
        SELECT COALESCE(total_amount, 0)
        FROM sales
        WHERE id = ?
        """,
        (sale_id,),
    )
    row = cursor.fetchone()
    if not row:
        raise ValueError("Sale not found.")

    total_amount = float(row[0] or 0)
    cursor.execute(
        """
        SELECT COALESCE(SUM(amount_paid), 0)
        FROM payments
        WHERE sale_id = ?
            AND COALESCE(payment_status, 'Active') = 'Active'
        """,
        (sale_id,),
    )
    amount_paid = float(cursor.fetchone()[0] or 0)
    balance, payment_status = calculate_payment_status(total_amount, amount_paid)

    cursor.execute(
        """
        SELECT payment_method, COALESCE(SUM(amount_paid), 0)
        FROM payments
        WHERE sale_id = ?
            AND COALESCE(payment_status, 'Active') = 'Active'
        GROUP BY payment_method
        ORDER BY MIN(id)
        """,
        (sale_id,),
    )
    payment_summary = "; ".join(
        f"{method} {format_currency(amount)}" for method, amount in cursor.fetchall()
    )

    cursor.execute(
        """
        UPDATE sales
        SET amount_paid = ?,
            balance = ?,
            payment_status = ?,
            payment_method = ?
        WHERE id = ?
        """,
        (amount_paid, balance, payment_status, payment_summary, sale_id),
    )
    return amount_paid, balance, payment_status


def save_sale_transaction(
    cart_items,
    payment_lines,
    customer_type,
    customer_name,
    phone,
    address,
    vehicle_type,
    notes,
    promised_payment_date,
    follow_up_note,
    sale_date,
):
    if not cart_items:
        return False, "Add at least one tyre item before saving the sale."

    if customer_type == REGULAR_CUSTOMER and not customer_name.strip():
        return False, "Customer name is required for a regular customer."

    for payment in payment_lines:
        if float(payment["amount_paid"]) <= 0:
            return False, "Payment amount must be greater than zero."
        if payment["payment_method"] not in PAYMENT_METHODS:
            return False, "Please select a valid payment method."

    conn = get_connection()
    cursor = conn.cursor()

    try:
        stock_ids = [int(item["stock_id"]) for item in cart_items]
        placeholders = ",".join("?" for _ in stock_ids)
        cursor.execute(
            f"""
            SELECT id, quantity
            FROM stock
            WHERE id IN ({placeholders})
            """,
            stock_ids,
        )
        available_quantities = {row[0]: row[1] for row in cursor.fetchall()}

        totals_by_stock = {}
        for item in cart_items:
            stock_id = int(item["stock_id"])
            totals_by_stock[stock_id] = totals_by_stock.get(stock_id, 0) + int(item["quantity_sold"])

        for stock_id, quantity_sold in totals_by_stock.items():
            available_quantity = available_quantities.get(stock_id)
            if available_quantity is None:
                raise ValueError("One of the selected stock items no longer exists.")
            if quantity_sold > available_quantity:
                raise ValueError(
                    f"Not enough stock for item ID {stock_id}. Available: {available_quantity}, requested: {quantity_sold}."
                )

        customer_id, saved_customer_name = get_or_create_customer(
            cursor,
            customer_type,
            customer_name,
            phone,
            address,
            vehicle_type,
            notes,
        )

        total_quantity = sum(int(item["quantity_sold"]) for item in cart_items)
        total_amount = sum(float(item["line_total"]) for item in cart_items)
        total_cost = sum(float(item["line_cost"]) for item in cart_items)
        total_profit = total_amount - total_cost
        amount_paid = sum(float(payment["amount_paid"]) for payment in payment_lines)
        balance, payment_status = calculate_payment_status(total_amount, amount_paid)
        payment_method = get_payment_methods_summary(payment_lines)
        first_item = cart_items[0]
        now = datetime.now().isoformat(timespec="seconds")

        cursor.execute(
            """
            INSERT INTO sales
            (
                invoice_number,
                customer_id,
                customer_type,
                customer_name,
                phone,
                address,
                vehicle_type,
                customer_notes,
                total_quantity,
                total_amount,
                total_cost,
                total_profit,
                payment_method,
                amount_paid,
                balance,
                payment_status,
                promised_payment_date,
                follow_up_note,
                sale_date,
                created_at,
                stock_id,
                size,
                brand,
                pattern_model,
                condition,
                quantity_sold,
                selling_price,
                buying_price,
                profit,
                sale_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "",
                customer_id,
                customer_type,
                saved_customer_name,
                phone.strip(),
                address.strip(),
                vehicle_type.strip(),
                notes.strip(),
                total_quantity,
                total_amount,
                total_cost,
                total_profit,
                payment_method,
                amount_paid,
                balance,
                payment_status,
                str(promised_payment_date) if promised_payment_date else "",
                follow_up_note.strip(),
                str(sale_date),
                now,
                int(first_item["stock_id"]),
                first_item["size"],
                first_item["brand"],
                first_item["pattern_model"],
                first_item["condition"],
                int(first_item["quantity_sold"]),
                float(first_item["selling_price"]),
                float(first_item["buying_price"]),
                float(first_item["line_profit"]),
                "Active",
            ),
        )
        sale_id = cursor.lastrowid
        invoice_number = make_invoice_number(sale_id)

        for payment in payment_lines:
            cursor.execute(
                """
                INSERT INTO payments
                (sale_id, payment_date, payment_method, amount_paid, payment_note, created_at, payment_status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sale_id,
                    payment["payment_date"],
                    payment["payment_method"],
                    float(payment["amount_paid"]),
                    payment["payment_note"],
                    now,
                    "Active",
                ),
            )

        for item in cart_items:
            cursor.execute(
                """
                INSERT INTO sale_items
                (
                    sale_id,
                    stock_id,
                    size,
                    brand,
                    pattern_model,
                    condition,
                    quantity_sold,
                    selling_price,
                    buying_price,
                    line_total,
                    line_cost,
                    line_profit,
                    item_status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sale_id,
                    int(item["stock_id"]),
                    item["size"],
                    item["brand"],
                    item["pattern_model"],
                    item["condition"],
                    int(item["quantity_sold"]),
                    float(item["selling_price"]),
                    float(item["buying_price"]),
                    float(item["line_total"]),
                    float(item["line_cost"]),
                    float(item["line_profit"]),
                    "Active",
                ),
            )
            cursor.execute(
                """
                UPDATE stock
                SET quantity = quantity - ?
                WHERE id = ?
                """,
                (int(item["quantity_sold"]), int(item["stock_id"])),
            )

        cursor.execute("UPDATE sales SET invoice_number = ? WHERE id = ?", (invoice_number, sale_id))
        conn.commit()
        return True, f"Sale saved as {invoice_number}. Balance: {format_naira(balance)}."
    except Exception as error:
        conn.rollback()
        return False, str(error)
    finally:
        conn.close()


def record_followup_payment(sale_id, payment_date, payment_method, amount_paid, payment_note):
    if float(amount_paid) <= 0:
        return False, "Payment amount must be greater than zero."
    if payment_method not in PAYMENT_METHODS:
        return False, "Please select a valid payment method."

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT invoice_number, COALESCE(total_amount, 0), COALESCE(amount_paid, 0)
            FROM sales
            WHERE id = ?
                AND COALESCE(sale_status, 'Active') = 'Active'
            """,
            (sale_id,),
        )
        sale = cursor.fetchone()
        if not sale:
            raise ValueError("Sale not found.")

        now = datetime.now().isoformat(timespec="seconds")
        cursor.execute(
            """
            INSERT INTO payments
            (sale_id, payment_date, payment_method, amount_paid, payment_note, created_at, payment_status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                sale_id,
                str(payment_date),
                payment_method,
                float(amount_paid),
                payment_note.strip(),
                now,
                "Active",
            ),
        )
        _, balance, payment_status = update_sale_payment_totals(cursor, sale_id)
        conn.commit()
        return True, f"Payment saved. New balance: {format_currency(balance)}. Status: {payment_status}."
    except Exception as error:
        conn.rollback()
        return False, str(error)
    finally:
        conn.close()


def delete_payment(payment_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT p.sale_id, COALESCE(s.sale_status, 'Active')
            FROM payments p
            JOIN sales s ON s.id = p.sale_id
            WHERE p.id = ?
                AND COALESCE(p.payment_status, 'Active') = 'Active'
            """,
            (payment_id,),
        )
        row = cursor.fetchone()
        if not row:
            raise ValueError("Payment not found or already removed.")

        sale_id, sale_status = row
        if sale_status != "Active":
            raise ValueError("Payments cannot be changed for a cancelled sale.")

        cursor.execute("DELETE FROM payments WHERE id = ?", (payment_id,))
        _, balance, payment_status = update_sale_payment_totals(cursor, sale_id)
        conn.commit()
        return True, f"Payment removed. New balance: {format_currency(balance)}. Status: {payment_status}."
    except Exception as error:
        conn.rollback()
        return False, str(error)
    finally:
        conn.close()


def cancel_sale(sale_id, cancellation_reason):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT COALESCE(sale_status, 'Active')
            FROM sales
            WHERE id = ?
            """,
            (sale_id,),
        )
        row = cursor.fetchone()
        if not row:
            raise ValueError("Sale not found.")
        if row[0] == "Cancelled":
            raise ValueError("This sale is already cancelled.")

        cursor.execute(
            """
            SELECT stock_id, COALESCE(quantity_sold, 0)
            FROM sale_items
            WHERE sale_id = ?
                AND COALESCE(item_status, 'Active') = 'Active'
            """,
            (sale_id,),
        )
        sale_items = cursor.fetchall()
        now = datetime.now().isoformat(timespec="seconds")

        for stock_id, quantity_sold in sale_items:
            cursor.execute(
                """
                UPDATE stock
                SET quantity = quantity + ?
                WHERE id = ?
                """,
                (int(quantity_sold or 0), int(stock_id)),
            )

        cursor.execute(
            """
            UPDATE sale_items
            SET item_status = 'Cancelled'
            WHERE sale_id = ?
            """,
            (sale_id,),
        )
        cursor.execute(
            """
            UPDATE payments
            SET payment_status = 'Cancelled',
                cancelled_at = ?
            WHERE sale_id = ?
            """,
            (now, sale_id),
        )
        cursor.execute(
            """
            UPDATE sales
            SET sale_status = 'Cancelled',
                cancellation_reason = ?,
                cancelled_at = ?,
                balance = 0,
                payment_status = 'Cancelled'
            WHERE id = ?
            """,
            (cancellation_reason.strip(), now, sale_id),
        )
        conn.commit()
        return True, "Sale cancelled. Stock quantities have been restored."
    except Exception as error:
        conn.rollback()
        return False, str(error)
    finally:
        conn.close()


def get_stock_dataframe(available_only=False):
    where_clause = "WHERE quantity > 0" if available_only else ""
    return run_query(
        f"""
        SELECT
            id,
            size,
            brand,
            COALESCE(pattern_model, '') AS pattern_model,
            condition,
            quantity,
            buying_price,
            selling_price,
            supplier,
            date_added
        FROM stock
        {where_clause}
        ORDER BY brand, pattern_model, size, id
        """
    )


def format_stock_label(row):
    pattern = row["pattern_model"] or ""
    return (
        f"ID {row['id']} | {str(row['brand']).title()} | {pattern.upper()} | "
        f"{str(row['size']).upper()} | {str(row['condition']).title()} | {row['quantity']} left"
    )


def format_naira(amount):
    try:
        value = float(amount or 0)
    except (TypeError, ValueError):
        value = 0
    return f"₦{round(value):,}"


def parse_naira_input(value):
    if value is None:
        return 0.0

    text = str(value).strip()
    if not text:
        return 0.0

    clean_text = (
        text.replace("₦", "")
        .replace("NGN", "")
        .replace("ngn", "")
        .replace(",", "")
        .replace(" ", "")
    )

    if not re.fullmatch(r"\d+(\.\d+)?", clean_text):
        return None

    amount = float(clean_text)
    if amount < 0:
        return None
    return amount


def format_currency(amount):
    return format_naira(amount)


def format_money_text(value):
    if pd.isna(value):
        return value

    def replace_match(match):
        return format_naira(match.group(1).replace(",", ""))

    return re.sub(r"NGN\s+([0-9,]+(?:\.[0-9]+)?)", replace_match, str(value))


def format_money_dataframe(df):
    if df.empty:
        return df

    money_columns = {
        "buying_price",
        "selling_price",
        "Buying Price",
        "Selling Price",
        "Line Total",
        "Line Cost",
        "Line Profit",
        "Total Amount",
        "Amount Paid",
        "Outstanding Balance",
        "Profit",
        "Total Cost",
        "Total Profit",
        "Running Total Paid",
        "Remaining Balance",
    }
    money_text_columns = {
        "Items Sold",
        "Payment Methods Used",
        "Payment History Summary",
    }

    display_df = df.copy()
    for column in display_df.columns:
        if column in money_columns:
            display_df[column] = display_df[column].apply(format_naira)
        elif column in money_text_columns:
            display_df[column] = display_df[column].apply(format_money_text)

    return display_df


def show_money_dataframe(df, **kwargs):
    st.dataframe(format_money_dataframe(df), **kwargs)


def show_dashboard():
    st.header("Dashboard")

    stock_df = run_query(
        """
        SELECT
            id,
            size,
            brand,
            COALESCE(pattern_model, '') AS "Pattern / Model",
            condition,
            quantity,
            buying_price,
            selling_price,
            supplier,
            date_added
        FROM stock
        """
    )
    sales_df = run_query(
        """
        SELECT
            COALESCE(total_quantity, quantity_sold, 0) AS total_quantity,
            COALESCE(total_profit, profit, 0) AS total_profit
        FROM sales
        WHERE COALESCE(sale_status, 'Active') = 'Active'
        """
    )

    total_stock = int(stock_df["quantity"].sum()) if not stock_df.empty else 0
    total_sales = int(sales_df["total_quantity"].sum()) if not sales_df.empty else 0
    total_profit = float(sales_df["total_profit"].sum()) if not sales_df.empty else 0.0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Tyres In Stock", total_stock)
    col2.metric("Total Tyres Sold", total_sales)
    col3.metric("Total Profit", format_currency(total_profit))

    st.subheader("Low Stock Alerts")
    low_stock_df = stock_df[stock_df["quantity"] <= LOW_STOCK_LIMIT] if not stock_df.empty else stock_df

    if low_stock_df.empty:
        st.success("No low-stock items right now.")
    else:
        st.warning(f"These items have {LOW_STOCK_LIMIT} tyres or fewer left.")
        show_money_dataframe(low_stock_df, width="stretch")


def show_add_stock():
    st.header("Add Tyre Stock")

    with st.form("add_stock_form"):
        size = st.text_input("Tyre size", placeholder="Example: 205/55R16")
        brand = st.text_input("Brand", placeholder="Example: Austone")
        pattern_model = st.text_input("Pattern / Model", placeholder="Example: AT115")
        condition = st.selectbox("Condition", ["New", "Used", "Retread"])
        quantity = st.number_input("Quantity", min_value=1, step=1)
        buying_price_input = st.text_input(
            "Buying price per tyre",
            placeholder="Example: 350000, 350,000, or ₦350,000",
        )
        selling_price_input = st.text_input(
            "Selling price per tyre",
            placeholder="Example: 360000, 360,000, or ₦360,000",
        )
        buying_price = parse_naira_input(buying_price_input)
        selling_price = parse_naira_input(selling_price_input)

        if buying_price is None:
            st.warning("Enter a valid buying price, for example 350000, 350,000, or ₦350,000.")
        if selling_price is None:
            st.warning("Enter a valid selling price, for example 360000, 360,000, or ₦360,000.")
        if buying_price is not None and selling_price is not None:
            profit_per_tyre = selling_price - buying_price
            total_stock_cost = buying_price * int(quantity)
            total_stock_value = selling_price * int(quantity)
            st.caption(
                f"Buying price: {format_naira(buying_price)} | "
                f"Selling price: {format_naira(selling_price)} | "
                f"Profit per tyre: {format_naira(profit_per_tyre)} | "
                f"Total stock cost: {format_naira(total_stock_cost)} | "
                f"Total stock value: {format_naira(total_stock_value)}"
            )
        supplier = st.text_input("Supplier", placeholder="Example: Lagos Tyre Market")
        date_added = st.date_input("Date added", value=date.today())

        submitted = st.form_submit_button("Save Stock")

    if submitted:
        if not size.strip() or not brand.strip():
            st.error("Please enter tyre size and brand.")
        elif buying_price is None or selling_price is None:
            st.error("Please enter valid buying and selling prices before saving.")
        elif selling_price < buying_price:
            st.error("Selling price should not be less than buying price.")
        else:
            add_stock(
                size.strip(),
                brand.strip(),
                pattern_model.strip(),
                condition,
                int(quantity),
                float(buying_price),
                float(selling_price),
                supplier.strip(),
                date_added,
            )
            st.success("Stock added successfully.")


def show_all_stock():
    st.header("All Stock")

    stock_df = run_query(
        """
        SELECT
            id,
            size,
            brand,
            COALESCE(pattern_model, '') AS "Pattern / Model",
            condition,
            quantity,
            buying_price,
            selling_price,
            supplier,
            date_added
        FROM stock
        ORDER BY id DESC
        """
    )

    if stock_df.empty:
        st.info("No stock has been added yet.")
    else:
        show_money_dataframe(stock_df, width="stretch")
        st.subheader("Delete Stock Item")
        st.warning("Deleting stock removes it from current stock only. Old sales reports keep their saved tyre details.")

        for row in stock_df.itertuples(index=False):
            row_id = int(row.id)
            pattern = f" {getattr(row, '_3')}" if getattr(row, "_3") else ""
            label = f"ID {row_id} - {row.brand}{pattern} {row.size} ({row.condition})"
            with st.expander(label):
                confirm = st.checkbox(
                    "I understand this stock item will be deleted.",
                    key=f"confirm_delete_stock_{row_id}",
                )
                if st.button("Delete this stock item", key=f"delete_stock_{row_id}", disabled=not confirm):
                    delete_stock_item(row_id)
                    st.success("Stock item deleted.")
                    st.rerun()

    st.subheader("Clear All Data")
    st.warning(
        "This clears stock, sales, sale items, and saved customers inside the app. "
        "It does not delete app.py, requirements.txt, README.md, or the database file."
    )
    with st.expander("Clear all app data"):
        confirmation_text = st.text_input("Type DELETE to confirm", key="clear_all_confirmation")
        if st.button("Clear all data", disabled=confirmation_text != "DELETE"):
            clear_all_app_data()
            st.success("All app records have been cleared. The database file is still in place.")
            st.rerun()


def show_search():
    st.header("Search Tyres")

    col1, col2, col3, col4 = st.columns(4)
    size = col1.text_input("Search by size")
    brand = col2.text_input("Search by brand")
    pattern_model = col3.text_input("Search by pattern/model")
    condition = col4.selectbox("Condition", ["Any", "New", "Used", "Retread"])

    query = """
        SELECT
            id,
            size,
            brand,
            COALESCE(pattern_model, '') AS "Pattern / Model",
            condition,
            quantity,
            buying_price,
            selling_price,
            supplier,
            date_added
        FROM stock
        WHERE 1 = 1
    """
    params = []

    if size.strip():
        query += " AND size LIKE ?"
        params.append(f"%{size.strip()}%")

    if brand.strip():
        query += " AND brand LIKE ?"
        params.append(f"%{brand.strip()}%")

    if pattern_model.strip():
        query += " AND pattern_model LIKE ?"
        params.append(f"%{pattern_model.strip()}%")

    if condition != "Any":
        query += " AND condition = ?"
        params.append(condition)

    query += " ORDER BY id DESC"
    results_df = run_query(query, params)

    if results_df.empty:
        st.info("No tyres match your search.")
    else:
        show_money_dataframe(results_df, width="stretch")


def add_item_to_cart(stock_row, quantity_sold, selling_price):
    line_total = float(selling_price) * int(quantity_sold)
    line_cost = float(stock_row["buying_price"]) * int(quantity_sold)
    item = {
        "stock_id": int(stock_row["id"]),
        "brand": stock_row["brand"],
        "pattern_model": stock_row["pattern_model"],
        "size": stock_row["size"],
        "condition": stock_row["condition"],
        "quantity_sold": int(quantity_sold),
        "selling_price": float(selling_price),
        "buying_price": float(stock_row["buying_price"]),
        "line_total": line_total,
        "line_cost": line_cost,
        "line_profit": line_total - line_cost,
    }
    st.session_state.sale_cart.append(item)


def get_cart_dataframe():
    if not st.session_state.sale_cart:
        return pd.DataFrame()
    cart_df = pd.DataFrame(st.session_state.sale_cart)
    return cart_df.rename(
        columns={
            "stock_id": "Stock ID",
            "brand": "Brand",
            "pattern_model": "Pattern / Model",
            "size": "Size",
            "condition": "Condition",
            "quantity_sold": "Quantity",
            "selling_price": "Selling Price",
            "buying_price": "Buying Price",
            "line_total": "Line Total",
            "line_cost": "Line Cost",
            "line_profit": "Line Profit",
        }
    )


def show_customer_fields(customer_type):
    customer_name = ""
    phone = ""
    address = ""
    vehicle_type = ""
    notes = ""

    if customer_type == WALK_IN_CUSTOMER:
        customer_name = st.text_input("Customer name (optional)", placeholder="Leave blank for Walk-in Customer")
    else:
        customers_df = run_query(
            """
            SELECT id, name, phone, address, vehicle_type, notes
            FROM customers
            WHERE customer_type = ?
            ORDER BY name
            """,
            (REGULAR_CUSTOMER,),
        )
        customer_choices = ["New regular customer"]
        customer_lookup = {}
        for row in customers_df.itertuples(index=False):
            label = f"{row.name} - {row.phone}" if row.phone else row.name
            customer_choices.append(label)
            customer_lookup[label] = row

        selected_customer = st.selectbox("Regular customer", customer_choices)
        if selected_customer != "New regular customer":
            selected = customer_lookup[selected_customer]
            customer_name = selected.name or ""
            phone = selected.phone or ""
            address = selected.address or ""
            vehicle_type = selected.vehicle_type or ""
            notes = selected.notes or ""

        customer_name = st.text_input("Customer name", value=customer_name)
        phone = st.text_input("Phone number", value=phone)
        address = st.text_input("Address / Location", value=address)
        vehicle_type = st.text_input("Vehicle type", value=vehicle_type, placeholder="Example: Toyota Camry")
        notes = st.text_area("Notes", value=notes)

    return customer_name, phone, address, vehicle_type, notes


def show_record_sale():
    st.header("Record Sale")

    if "sale_cart" not in st.session_state:
        st.session_state.sale_cart = []
    if "sale_payments" not in st.session_state:
        st.session_state.sale_payments = []

    stock_df = get_stock_dataframe(available_only=True)

    if stock_df.empty:
        st.info("There is no available stock to sell.")
    else:
        stock_df["label"] = stock_df.apply(format_stock_label, axis=1)

        st.subheader("Search Tyre From Stock")
        search_term = st.text_input(
            "Search by brand, pattern / model, size, condition, or stock ID",
            placeholder="Example: Austone, AT103, 315, 315/80R22.5, New, ID 2",
        )
        filtered_stock_df = stock_df.copy()
        if search_term.strip():
            search_value = search_term.strip().lower().replace("id ", "")
            search_text = (
                filtered_stock_df["id"].astype(str)
                + " "
                + filtered_stock_df["brand"].fillna("").astype(str)
                + " "
                + filtered_stock_df["pattern_model"].fillna("").astype(str)
                + " "
                + filtered_stock_df["size"].fillna("").astype(str)
                + " "
                + filtered_stock_df["condition"].fillna("").astype(str)
            ).str.lower()
            filtered_stock_df = filtered_stock_df[search_text.str.contains(search_value, regex=False)]

        if filtered_stock_df.empty:
            st.info("No available tyres match that search.")
        else:
            st.subheader("Add Item to Sale")
            selected_label = st.selectbox("Choose tyre from stock", filtered_stock_df["label"].tolist())
            selected_row = filtered_stock_df[filtered_stock_df["label"] == selected_label].iloc[0]
            st.caption(selected_label)
            col1, col2 = st.columns(2)
            quantity_sold = col1.number_input(
                "Quantity sold",
                min_value=1,
                max_value=int(selected_row["quantity"]),
                step=1,
            )
            selling_price_input = col2.text_input(
                "Selling price per tyre",
                value=format_naira(selected_row["selling_price"]),
                key=f"selling_price_{selected_row['id']}",
            )
            selling_price = parse_naira_input(selling_price_input)
            if selling_price is None:
                st.warning("Enter a valid selling price, for example 350000, 350,000, or ₦350,000.")
            else:
                line_total = selling_price * int(quantity_sold)
                line_profit = line_total - (float(selected_row["buying_price"]) * int(quantity_sold))
                st.caption(
                    f"Selling price: {format_naira(selling_price)} | "
                    f"Line total: {format_naira(line_total)} | "
                    f"Line profit: {format_naira(line_profit)}"
                )

            if st.button("Add Item to Sale"):
                existing_quantity = sum(
                    item["quantity_sold"]
                    for item in st.session_state.sale_cart
                    if item["stock_id"] == int(selected_row["id"])
                )
                if selling_price is None:
                    st.error("Please enter a valid selling price before adding this item.")
                elif existing_quantity + int(quantity_sold) > int(selected_row["quantity"]):
                    st.error("Not enough stock available for this tyre item.")
                else:
                    add_item_to_cart(selected_row, int(quantity_sold), float(selling_price))
                    st.success("Item added to current sale.")
                    st.rerun()

    st.subheader("Current Sale Items")
    cart_df = get_cart_dataframe()
    if cart_df.empty:
        st.info("No items added yet.")
    else:
        show_money_dataframe(cart_df, width="stretch")
        item_options = [
            f"{index + 1}. ID {item['stock_id']} | {item['brand']} | {item['pattern_model']} | {item['size']} x {item['quantity_sold']}"
            for index, item in enumerate(st.session_state.sale_cart)
        ]
        item_to_remove = st.selectbox("Remove item from current sale", item_options)
        if st.button("Remove selected item"):
            remove_index = item_options.index(item_to_remove)
            st.session_state.sale_cart.pop(remove_index)
            st.success("Item removed from current sale.")
            st.rerun()

    total_quantity = sum(item["quantity_sold"] for item in st.session_state.sale_cart)
    total_amount = sum(item["line_total"] for item in st.session_state.sale_cart)
    total_cost = sum(item["line_cost"] for item in st.session_state.sale_cart)
    total_profit = total_amount - total_cost

    st.subheader("Current Payments")
    with st.form("add_sale_payment_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        payment_date = col1.date_input("Payment date", value=date.today())
        payment_method = col2.selectbox("Payment method", PAYMENT_METHODS)
        payment_amount_input = col3.text_input(
            "Amount paid",
            placeholder="Example: 50000, 50,000, or ₦50,000",
        )
        payment_amount = parse_naira_input(payment_amount_input)
        if payment_amount is None:
            st.warning("Enter a valid payment amount, for example 50000, 50,000, or ₦50,000.")
        else:
            st.caption(f"Amount paid: {format_naira(payment_amount)}")
        payment_note = st.text_input("Payment note / reference (optional)")
        add_payment_submitted = st.form_submit_button("Add Payment")

    if add_payment_submitted:
        if payment_amount is None:
            st.error("Please enter a valid payment amount.")
        elif payment_amount <= 0:
            st.error("Enter an amount greater than zero.")
        else:
            add_payment_to_current_sale(payment_date, payment_method, float(payment_amount), payment_note)
            st.success("Payment added to current sale.")
            st.rerun()

    payments_df = get_payments_dataframe()
    if payments_df.empty:
        st.info("No payment added yet. Leave empty for an unpaid sale.")
    else:
        show_money_dataframe(payments_df, width="stretch")
        payment_options = [
            f"{index + 1}. {payment['payment_date']} | {payment['payment_method']} | {format_currency(payment['amount_paid'])}"
            for index, payment in enumerate(st.session_state.sale_payments)
        ]
        payment_to_remove = st.selectbox("Remove payment from current sale", payment_options)
        if st.button("Remove selected payment"):
            remove_index = payment_options.index(payment_to_remove)
            st.session_state.sale_payments.pop(remove_index)
            st.success("Payment removed from current sale.")
            st.rerun()

    total_paid = sum(payment["amount_paid"] for payment in st.session_state.sale_payments)
    balance, payment_status = calculate_payment_status(total_amount, total_paid)
    overpayment = max(total_paid - total_amount, 0.0) if total_amount > 0 else 0.0

    st.subheader("Sale Summary")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Quantity", total_quantity)
    col2.metric("Total Amount", format_currency(total_amount))
    col3.metric("Amount Paid", format_currency(total_paid))
    col4.metric("Outstanding Balance", format_currency(balance))

    col5, col6, col7 = st.columns(3)
    col5.metric("Total Cost", format_currency(total_cost))
    col6.metric("Total Profit", format_currency(total_profit))
    col7.metric("Payment Status", payment_status)

    if overpayment > 0:
        st.warning(f"Overpayment: {format_currency(overpayment)}. Confirm before saving this sale.")
        confirm_overpayment = st.checkbox("I confirm this overpayment is correct")
    else:
        confirm_overpayment = True

    st.subheader("Customer And Follow-up")
    customer_type = st.radio("Customer type", [WALK_IN_CUSTOMER, REGULAR_CUSTOMER], horizontal=True)
    customer_name, phone, address, vehicle_type, notes = show_customer_fields(customer_type)
    sale_date = st.date_input("Sale date", value=date.today())
    promised_payment_date = None
    follow_up_note = ""
    if balance > 0:
        promised_payment_date = st.date_input("Promised Payment Date", value=date.today())
        follow_up_note = st.text_area(
            "Payment Follow-up Note",
            placeholder="Example: Customer promised to pay balance after delivery",
        )
    else:
        st.caption("Promised Payment Date and Follow-up Note are only needed when there is an outstanding balance.")

    if st.button("Save Full Sale", disabled=not st.session_state.sale_cart or not confirm_overpayment):
        success, message = save_sale_transaction(
            st.session_state.sale_cart,
            st.session_state.sale_payments,
            customer_type,
            customer_name,
            phone,
            address,
            vehicle_type,
            notes,
            promised_payment_date,
            follow_up_note,
            sale_date,
        )

        if success:
            st.session_state.sale_cart = []
            st.session_state.sale_payments = []
            st.success(message)
            st.rerun()
        else:
            st.error(message)

    st.subheader("Recent Sales")
    recent_sales_df = get_sales_report_dataframe(limit=20)
    if recent_sales_df.empty:
        st.info("No sales have been recorded yet.")
    else:
        show_money_dataframe(recent_sales_df, width="stretch")


def get_sales_report_dataframe(limit=None, sale_status="Active"):
    limit_clause = f"LIMIT {int(limit)}" if limit else ""
    if using_postgres():
        return run_query(
            f"""
            SELECT
                s.id AS "Sale ID",
                s.invoice_number AS "Invoice Number",
                s.sale_date AS "Date",
                COALESCE(s.customer_type, ?) AS "Customer Type",
                COALESCE(s.customer_name, ?) AS "Customer Name",
                COALESCE(s.phone, '') AS "Phone Number",
                COALESCE(s.address, '') AS "Address / Location",
                STRING_AGG(
                    si.brand || ' ' ||
                    CASE
                        WHEN COALESCE(si.pattern_model, '') = '' THEN ''
                        ELSE si.pattern_model || ' '
                    END ||
                    si.size || ' (' || si.condition || ') x ' ||
                    si.quantity_sold::text || ' @ NGN ' ||
                    TO_CHAR(si.selling_price, 'FM999999999999990.00'),
                    '; '
                    ORDER BY si.id
                ) AS "Items Sold",
                COALESCE(s.total_amount, SUM(si.line_total), 0) AS "Total Amount",
                COALESCE(s.amount_paid, 0) AS "Amount Paid",
                COALESCE(s.balance, 0) AS "Outstanding Balance",
                COALESCE(s.total_profit, SUM(si.line_profit), 0) AS "Profit",
                COALESCE(s.payment_status, '') AS "Payment Status",
                COALESCE(s.promised_payment_date, '') AS "Promised Payment Date",
                COALESCE(payments.payment_methods, COALESCE(s.payment_method, '')) AS "Payment Methods Used",
                COALESCE(payments.payment_history, '') AS "Payment History Summary",
                COALESCE(s.sale_status, 'Active') AS "Sale Status",
                COALESCE(s.cancellation_reason, '') AS "Cancellation Reason",
                COALESCE(s.cancelled_at, '') AS "Cancelled At"
            FROM sales s
            LEFT JOIN sale_items si ON si.sale_id = s.id
                AND COALESCE(si.item_status, 'Active') = COALESCE(s.sale_status, 'Active')
            LEFT JOIN (
                SELECT
                    sale_id,
                    STRING_AGG(payment_method || ' ' || 'NGN ' || TO_CHAR(amount_paid, 'FM999999999999990.00'), '; ' ORDER BY id) AS payment_methods,
                    STRING_AGG(payment_date || ' | ' || payment_method || ' | NGN ' || TO_CHAR(amount_paid, 'FM999999999999990.00'), '; ' ORDER BY id) AS payment_history
                FROM payments
                WHERE COALESCE(payment_status, 'Active') = ?
                GROUP BY sale_id
            ) payments ON payments.sale_id = s.id
            WHERE COALESCE(s.sale_status, 'Active') = ?
            GROUP BY s.id, payments.payment_methods, payments.payment_history
            ORDER BY s.sale_date DESC, s.id DESC
            {limit_clause}
            """,
            (WALK_IN_CUSTOMER, WALK_IN_CUSTOMER, sale_status, sale_status),
        )

    return run_query(
        f"""
        SELECT
            s.id AS "Sale ID",
            s.invoice_number AS "Invoice Number",
            s.sale_date AS "Date",
            COALESCE(s.customer_type, ?) AS "Customer Type",
            COALESCE(s.customer_name, ?) AS "Customer Name",
            COALESCE(s.phone, '') AS "Phone Number",
            COALESCE(s.address, '') AS "Address / Location",
            GROUP_CONCAT(
                si.brand || ' ' ||
                CASE
                    WHEN COALESCE(si.pattern_model, '') = '' THEN ''
                    ELSE si.pattern_model || ' '
                END ||
                si.size || ' (' || si.condition || ') x ' ||
                si.quantity_sold || ' @ NGN ' ||
                printf('%.2f', si.selling_price),
                '; '
            ) AS "Items Sold",
            COALESCE(s.total_amount, SUM(si.line_total), 0) AS "Total Amount",
            COALESCE(s.amount_paid, 0) AS "Amount Paid",
            COALESCE(s.balance, 0) AS "Outstanding Balance",
            COALESCE(s.total_profit, SUM(si.line_profit), 0) AS "Profit",
            COALESCE(s.payment_status, '') AS "Payment Status",
            COALESCE(s.promised_payment_date, '') AS "Promised Payment Date",
            COALESCE(payments.payment_methods, COALESCE(s.payment_method, '')) AS "Payment Methods Used",
            COALESCE(payments.payment_history, '') AS "Payment History Summary",
            COALESCE(s.sale_status, 'Active') AS "Sale Status",
            COALESCE(s.cancellation_reason, '') AS "Cancellation Reason",
            COALESCE(s.cancelled_at, '') AS "Cancelled At"
        FROM sales s
        LEFT JOIN sale_items si ON si.sale_id = s.id
            AND COALESCE(si.item_status, 'Active') = COALESCE(s.sale_status, 'Active')
        LEFT JOIN (
            SELECT
                sale_id,
                GROUP_CONCAT(payment_method || ' ' || 'NGN ' || printf('%.2f', amount_paid), '; ') AS payment_methods,
                GROUP_CONCAT(payment_date || ' | ' || payment_method || ' | NGN ' || printf('%.2f', amount_paid), '; ') AS payment_history
            FROM payments
            WHERE COALESCE(payment_status, 'Active') = ?
            GROUP BY sale_id
        ) payments ON payments.sale_id = s.id
        WHERE COALESCE(s.sale_status, 'Active') = ?
        GROUP BY s.id
        ORDER BY s.sale_date DESC, s.id DESC
        {limit_clause}
        """,
        (WALK_IN_CUSTOMER, WALK_IN_CUSTOMER, sale_status, sale_status),
    )


def get_outstanding_balances_dataframe(filter_option="All"):
    today = str(date.today())
    where_clause = "WHERE COALESCE(s.balance, 0) > 0 AND COALESCE(s.sale_status, 'Active') = 'Active'"
    params = [WALK_IN_CUSTOMER, WALK_IN_CUSTOMER]

    if filter_option == "Due today":
        where_clause += " AND s.promised_payment_date = ?"
        params.append(today)
    elif filter_option == "Overdue":
        where_clause += " AND s.promised_payment_date <> '' AND s.promised_payment_date < ?"
        params.append(today)
    elif filter_option == "Upcoming":
        where_clause += " AND s.promised_payment_date <> '' AND s.promised_payment_date > ?"
        params.append(today)
    elif filter_option in ["Part Payment", "Unpaid"]:
        where_clause += " AND COALESCE(s.payment_status, '') = ?"
        params.append(filter_option)

    if using_postgres():
        return run_query(
            f"""
            SELECT
                s.id AS "Sale ID",
                s.invoice_number AS "Invoice Number",
                s.sale_date AS "Sale Date",
                COALESCE(s.customer_type, ?) AS "Customer Type",
                COALESCE(s.customer_name, ?) AS "Customer Name",
                COALESCE(s.phone, '') AS "Phone Number",
                COALESCE(s.total_amount, 0) AS "Total Amount",
                COALESCE(s.amount_paid, 0) AS "Amount Paid",
                COALESCE(s.balance, 0) AS "Outstanding Balance",
                COALESCE(s.promised_payment_date, '') AS "Promised Payment Date",
                COALESCE(s.payment_status, '') AS "Payment Status",
                COALESCE(s.follow_up_note, '') AS "Follow-up Note",
                COALESCE(items.items_sold, '') AS "Items Sold",
                COALESCE(items.brands, '') AS "Tyre Brands",
                COALESCE(items.patterns, '') AS "Pattern / Models",
                COALESCE(items.sizes, '') AS "Tyre Sizes"
            FROM sales s
            LEFT JOIN (
                SELECT
                    sale_id,
                    STRING_AGG(
                        brand || ' ' ||
                        CASE
                            WHEN COALESCE(pattern_model, '') = '' THEN ''
                            ELSE pattern_model || ' '
                        END ||
                        size || ' x ' || quantity_sold::text,
                        '; '
                        ORDER BY id
                    ) AS items_sold,
                    STRING_AGG(DISTINCT brand, ', ') AS brands,
                    STRING_AGG(DISTINCT COALESCE(pattern_model, ''), ', ') AS patterns,
                    STRING_AGG(DISTINCT size, ', ') AS sizes
                FROM sale_items
                WHERE COALESCE(item_status, 'Active') = 'Active'
                GROUP BY sale_id
            ) items ON items.sale_id = s.id
            {where_clause}
            ORDER BY
                CASE WHEN COALESCE(s.promised_payment_date, '') = '' THEN 1 ELSE 0 END,
                s.promised_payment_date,
                s.sale_date DESC,
                s.id DESC
            """,
            params,
        )

    return run_query(
        f"""
        SELECT
            s.id AS "Sale ID",
            s.invoice_number AS "Invoice Number",
            s.sale_date AS "Sale Date",
            COALESCE(s.customer_type, ?) AS "Customer Type",
            COALESCE(s.customer_name, ?) AS "Customer Name",
            COALESCE(s.phone, '') AS "Phone Number",
            COALESCE(s.total_amount, 0) AS "Total Amount",
            COALESCE(s.amount_paid, 0) AS "Amount Paid",
            COALESCE(s.balance, 0) AS "Outstanding Balance",
            COALESCE(s.promised_payment_date, '') AS "Promised Payment Date",
            COALESCE(s.payment_status, '') AS "Payment Status",
            COALESCE(s.follow_up_note, '') AS "Follow-up Note",
            COALESCE(items.items_sold, '') AS "Items Sold",
            COALESCE(items.brands, '') AS "Tyre Brands",
            COALESCE(items.patterns, '') AS "Pattern / Models",
            COALESCE(items.sizes, '') AS "Tyre Sizes"
        FROM sales s
        LEFT JOIN (
            SELECT
                sale_id,
                GROUP_CONCAT(
                    brand || ' ' ||
                    CASE
                        WHEN COALESCE(pattern_model, '') = '' THEN ''
                        ELSE pattern_model || ' '
                    END ||
                    size || ' x ' || quantity_sold,
                    '; '
                ) AS items_sold,
                GROUP_CONCAT(DISTINCT brand) AS brands,
                GROUP_CONCAT(DISTINCT COALESCE(pattern_model, '')) AS patterns,
                GROUP_CONCAT(DISTINCT size) AS sizes
            FROM sale_items
            WHERE COALESCE(item_status, 'Active') = 'Active'
            GROUP BY sale_id
        ) items ON items.sale_id = s.id
        {where_clause}
        ORDER BY
            CASE WHEN COALESCE(s.promised_payment_date, '') = '' THEN 1 ELSE 0 END,
            s.promised_payment_date,
            s.sale_date DESC,
            s.id DESC
        """,
        params,
    )


def get_payment_history_dataframe(sale_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT COALESCE(total_amount, 0)
        FROM sales
        WHERE id = ?
        """,
        (sale_id,),
    )
    sale = cursor.fetchone()
    if not sale:
        conn.close()
        return pd.DataFrame()

    total_amount = float(sale[0] or 0)
    payments_df = run_query(
        """
        SELECT
            id,
            payment_date,
            payment_method,
            amount_paid,
            COALESCE(payment_note, '') AS payment_note
        FROM payments
        WHERE sale_id = ?
            AND COALESCE(payment_status, 'Active') = 'Active'
        ORDER BY payment_date, id
        """,
        (sale_id,),
    )
    conn.close()

    if payments_df.empty:
        return payments_df

    running_total = 0.0
    remaining_balances = []
    running_totals = []
    for amount in payments_df["amount_paid"]:
        running_total += float(amount or 0)
        running_totals.append(running_total)
        remaining_balances.append(max(total_amount - running_total, 0.0))

    payments_df["running_total_paid"] = running_totals
    payments_df["remaining_balance"] = remaining_balances
    return payments_df.rename(
        columns={
            "id": "Payment ID",
            "payment_date": "Payment Date",
            "payment_method": "Payment Method",
            "amount_paid": "Amount Paid",
            "payment_note": "Payment Note / Reference",
            "running_total_paid": "Running Total Paid",
            "remaining_balance": "Remaining Balance",
        }
    )


def get_all_payment_history_dataframe():
    return run_query(
        """
        SELECT
            p.id AS "Payment ID",
            s.id AS "Sale ID",
            COALESCE(s.invoice_number, '') AS "Invoice Number",
            COALESCE(s.customer_name, ?) AS "Customer Name",
            COALESCE(s.phone, '') AS "Phone Number",
            p.payment_date AS "Payment Date",
            p.payment_method AS "Payment Method",
            p.amount_paid AS "Amount Paid",
            COALESCE(p.payment_note, '') AS "Payment Note / Reference"
        FROM payments p
        JOIN sales s ON s.id = p.sale_id
        WHERE COALESCE(p.payment_status, 'Active') = 'Active'
            AND COALESCE(s.sale_status, 'Active') = 'Active'
        ORDER BY p.payment_date DESC, p.id DESC
        """,
        (WALK_IN_CUSTOMER,),
    )


def filter_dataframe_by_search(df, search_value):
    if df.empty or not search_value.strip():
        return df
    search_text = search_value.strip().lower()
    combined = df.fillna("").astype(str).agg(" ".join, axis=1).str.lower()
    return df[combined.str.contains(search_text, regex=False)]


def filter_dataframe_by_date_range(df, column_name, start_date=None, end_date=None):
    if df.empty or column_name not in df.columns:
        return df
    filtered_df = df.copy()
    dates = pd.to_datetime(filtered_df[column_name], errors="coerce")
    if start_date:
        filtered_df = filtered_df[dates >= pd.to_datetime(str(start_date))]
        dates = dates.loc[filtered_df.index]
    if end_date:
        filtered_df = filtered_df[dates <= pd.to_datetime(str(end_date))]
    return filtered_df


def show_payment_history(sale_id, label, allow_delete=False):
    with st.expander(f"Payment History - {label}"):
        history_df = get_payment_history_dataframe(sale_id)
        if history_df.empty:
            st.info("No payments recorded for this sale yet.")
        else:
            payment_search = st.text_input(
                "Search this payment history",
                placeholder="Example: Cash, Bank Transfer, 2026-06-25, 50000, transfer ref",
                key=f"payment_history_search_{sale_id}",
            )
            visible_history_df = filter_dataframe_by_search(history_df, payment_search)
            show_money_dataframe(visible_history_df.drop(columns=["Payment ID"]), width="stretch")

            if allow_delete:
                st.subheader("Delete Wrong Payment")
                payment_options = {}
                for _, row in history_df.iterrows():
                    payment_id = int(row["Payment ID"])
                    label_text = (
                        f"{row['Payment Date']} | {row['Payment Method']} | "
                        f"{format_currency(row['Amount Paid'])}"
                    )
                    payment_options[label_text] = payment_id

                selected_payment = st.selectbox(
                    "Select payment to delete",
                    list(payment_options.keys()),
                    key=f"delete_payment_select_{sale_id}",
                )
                confirm_payment_delete = st.checkbox(
                    "I understand this payment record will be removed and the outstanding balance will be recalculated.",
                    key=f"confirm_delete_payment_{sale_id}",
                )
                if st.button(
                    "Delete selected payment",
                    key=f"delete_payment_button_{sale_id}",
                    disabled=not confirm_payment_delete,
                ):
                    success, message = delete_payment(payment_options[selected_payment])
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)


def show_outstanding_balances():
    st.header("Outstanding Balances")

    filter_option = st.radio(
        "Filter outstanding balances",
        ["All", "Due today", "Overdue", "Upcoming", "Part Payment", "Unpaid"],
        horizontal=True,
    )
    outstanding_df = get_outstanding_balances_dataframe(filter_option)
    search_term = st.text_input(
        "Search outstanding balances",
        placeholder="Example: Austone, AT103, Sodiq, 080, 2026-06-25, INV-000001, Part Payment",
    )

    with st.expander("Date filters"):
        col1, col2 = st.columns(2)
        use_sale_date_filter = col1.checkbox("Filter by sale date")
        use_promised_date_filter = col2.checkbox("Filter by promised payment date")

        sale_from = sale_to = promised_from = promised_to = None
        if use_sale_date_filter:
            sale_col1, sale_col2 = st.columns(2)
            sale_from = sale_col1.date_input("Sale date from", value=date.today())
            sale_to = sale_col2.date_input("Sale date to", value=date.today())
        if use_promised_date_filter:
            promised_col1, promised_col2 = st.columns(2)
            promised_from = promised_col1.date_input("Promised payment date from", value=date.today())
            promised_to = promised_col2.date_input("Promised payment date to", value=date.today())

    outstanding_df = filter_dataframe_by_search(outstanding_df, search_term)
    outstanding_df = filter_dataframe_by_date_range(outstanding_df, "Sale Date", sale_from, sale_to)
    outstanding_df = filter_dataframe_by_date_range(
        outstanding_df,
        "Promised Payment Date",
        promised_from,
        promised_to,
    )

    if outstanding_df.empty:
        st.info("No outstanding balances match this filter.")
        return

    show_money_dataframe(outstanding_df.drop(columns=["Sale ID"]), width="stretch")

    st.subheader("Record Balance Payment")
    sale_options = {}
    for _, row in outstanding_df.iterrows():
        sale_id = int(row["Sale ID"])
        invoice_number = row["Invoice Number"]
        customer_name = row["Customer Name"]
        balance = row["Outstanding Balance"]
        label = f"{invoice_number} | {customer_name} | Balance {format_currency(balance)}"
        sale_options[label] = sale_id

    selected_sale_label = st.selectbox("Select sale / invoice with outstanding balance", list(sale_options.keys()))
    selected_sale_id = sale_options[selected_sale_label]
    selected_row = outstanding_df[outstanding_df["Sale ID"] == selected_sale_id].iloc[0]

    col1, col2, col3 = st.columns(3)
    col1.metric("Current Total Amount", format_currency(selected_row["Total Amount"]))
    col2.metric("Amount Paid", format_currency(selected_row["Amount Paid"]))
    col3.metric("Balance", format_currency(selected_row["Outstanding Balance"]))

    with st.form("record_balance_payment_form"):
        col1, col2, col3 = st.columns(3)
        later_payment_date = col1.date_input("New payment date", value=date.today())
        later_payment_method = col2.selectbox("New payment method", PAYMENT_METHODS)
        later_payment_amount_input = col3.text_input(
            "New payment amount",
            placeholder="Example: 50000, 50,000, or ₦50,000",
        )
        later_payment_amount = parse_naira_input(later_payment_amount_input)
        if later_payment_amount is None:
            st.warning("Enter a valid payment amount, for example 50000, 50,000, or ₦50,000.")
        else:
            st.caption(f"New payment amount: {format_naira(later_payment_amount)}")
        later_payment_note = st.text_input("Payment note / reference")
        save_later_payment = st.form_submit_button("Save Payment")

    if save_later_payment:
        if later_payment_amount is None:
            st.error("Please enter a valid payment amount.")
        elif later_payment_amount <= 0:
            st.error("Enter a payment amount greater than zero.")
        else:
            success, message = record_followup_payment(
                selected_sale_id,
                later_payment_date,
                later_payment_method,
                float(later_payment_amount),
                later_payment_note,
            )
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)

    show_payment_history(selected_sale_id, selected_sale_label)


def show_sales_report():
    st.header("Sales Report")

    sales_df = get_sales_report_dataframe()

    if sales_df.empty:
        st.info("No sales have been recorded yet.")
    else:
        search_term = st.text_input(
            "Search sales",
            placeholder="Example: customer name, phone, INV-000001, Cash, Paid, Austone, AT103, 315/80R22.5",
        )
        col1, col2 = st.columns(2)
        status_filter = col1.selectbox("Payment status", ["Any", "Paid", "Part Payment", "Unpaid"])
        method_filter = col2.selectbox("Payment method", ["Any"] + PAYMENT_METHODS)

        with st.expander("Sale date filter"):
            use_sale_date_filter = st.checkbox("Filter sales by date")
            report_sale_from = report_sale_to = None
            if use_sale_date_filter:
                date_col1, date_col2 = st.columns(2)
                report_sale_from = date_col1.date_input("Sale report date from", value=date.today())
                report_sale_to = date_col2.date_input("Sale report date to", value=date.today())

        filtered_sales_df = filter_dataframe_by_search(sales_df, search_term)
        if status_filter != "Any":
            filtered_sales_df = filtered_sales_df[filtered_sales_df["Payment Status"] == status_filter]
        if method_filter != "Any":
            method_text = filtered_sales_df["Payment Methods Used"].fillna("").astype(str)
            filtered_sales_df = filtered_sales_df[method_text.str.contains(method_filter, case=False, regex=False)]
        filtered_sales_df = filter_dataframe_by_date_range(
            filtered_sales_df,
            "Date",
            report_sale_from,
            report_sale_to,
        )

        if filtered_sales_df.empty:
            st.info("No sales match this search or filter.")
        else:
            hidden_columns = ["Sale ID", "Sale Status", "Cancellation Reason", "Cancelled At"]
            show_money_dataframe(filtered_sales_df.drop(columns=hidden_columns), width="stretch")

        st.subheader("Payment History")
        payment_history_df = get_all_payment_history_dataframe()
        payment_search = st.text_input(
            "Search all payment records",
            placeholder="Example: customer, phone, invoice, payment date, Cash, amount, note/reference",
        )
        visible_payment_history_df = filter_dataframe_by_search(payment_history_df, payment_search)
        if visible_payment_history_df.empty:
            st.info("No payment records match this search.")
        else:
            show_money_dataframe(visible_payment_history_df.drop(columns=["Payment ID", "Sale ID"]), width="stretch")

        invoice_options = {}
        sales_lookup_df = run_query(
            """
            SELECT id, invoice_number, COALESCE(customer_name, ?) AS customer_name
            FROM sales
            WHERE COALESCE(sale_status, 'Active') = 'Active'
            ORDER BY sale_date DESC, id DESC
            """,
            (WALK_IN_CUSTOMER,),
        )
        for row in sales_lookup_df.itertuples(index=False):
            label = f"{row.invoice_number} | {row.customer_name}"
            invoice_options[label] = int(row.id)
        if invoice_options:
            selected_invoice = st.selectbox("Select invoice for detailed payment history", list(invoice_options.keys()))
            selected_sale_id = invoice_options[selected_invoice]
            show_payment_history(selected_sale_id, selected_invoice, allow_delete=True)

            st.subheader("Cancel/Delete This Sale")
            st.warning(
                "Only use this for a sale recorded by mistake. The sale will be marked Cancelled, "
                "payments will be marked Cancelled, and sold tyre quantities will be restored to stock."
            )
            with st.expander("Cancel/Delete selected sale"):
                cancellation_reason = st.text_area(
                    "Cancellation reason",
                    placeholder="Example: Sale entered by mistake",
                    key=f"cancel_reason_{selected_sale_id}",
                )
                confirm_cancel_sale = st.checkbox(
                    "I understand this will cancel/delete this sale and update stock records.",
                    key=f"confirm_cancel_sale_{selected_sale_id}",
                )
                delete_text = st.text_input(
                    "Type DELETE to confirm",
                    key=f"cancel_delete_text_{selected_sale_id}",
                )
                if st.button(
                    "Cancel/Delete This Sale",
                    key=f"cancel_sale_button_{selected_sale_id}",
                    disabled=not confirm_cancel_sale or delete_text != "DELETE",
                ):
                    success, message = cancel_sale(selected_sale_id, cancellation_reason)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

    cancelled_sales_df = get_sales_report_dataframe(sale_status="Cancelled")
    if not cancelled_sales_df.empty:
        st.subheader("Cancelled Sales")
        st.caption("Cancelled sales are kept for audit only and do not count in dashboard totals, revenue, profit, or outstanding balances.")
        show_money_dataframe(cancelled_sales_df.drop(columns=["Sale ID"]), width="stretch")


def main():
    st.set_page_config(page_title="Tyre Business App", layout="wide")

    if not require_login():
        return

    create_tables()

    st.title("Tyre Business App")
    st.caption("Simple local stock, sales, and profit tracker")

    if get_app_password() and st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    page = st.sidebar.radio(
        "Choose a page",
        [
            "Dashboard",
            "Add Stock",
            "View Stock",
            "Search Tyres",
            "Record Sale",
            "Outstanding Balances",
            "Sales Report",
        ],
    )

    if page == "Dashboard":
        show_dashboard()
    elif page == "Add Stock":
        show_add_stock()
    elif page == "View Stock":
        show_all_stock()
    elif page == "Search Tyres":
        show_search()
    elif page == "Record Sale":
        show_record_sale()
    elif page == "Outstanding Balances":
        show_outstanding_balances()
    elif page == "Sales Report":
        show_sales_report()


if __name__ == "__main__":
    main()
