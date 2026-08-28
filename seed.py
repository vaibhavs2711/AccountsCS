"""
Cityscope Accounts — Seed Script
Creates the database (if needed), tables, and seeds the admin user.
Safe to run multiple times (idempotent).
"""

import pymysql
import config
from auth import hash_password


def run_seed():
    # ------------------------------------------------------------------
    # 1. Create the database if it doesn't exist
    # ------------------------------------------------------------------
    conn = pymysql.connect(
        host=config.MYSQL_HOST,
        port=config.MYSQL_PORT,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        autocommit=True,
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{config.MYSQL_DB}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            print(f"✔ Database '{config.MYSQL_DB}' ensured.")
    finally:
        conn.close()

    # ------------------------------------------------------------------
    # 2. Connect to the database and create tables
    # ------------------------------------------------------------------
    conn = pymysql.connect(
        host=config.MYSQL_HOST,
        port=config.MYSQL_PORT,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        database=config.MYSQL_DB,
        autocommit=True,
    )
    try:
        with conn.cursor() as cur:
            # --- users ---
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    password VARCHAR(255) NOT NULL,
                    role ENUM('ADMIN', 'EMPLOYEE') NOT NULL DEFAULT 'EMPLOYEE',
                    team_type ENUM('CORE_TEAM', 'NORMAL_TEAM', 'RENT_TEAM') NULL,
                    salary DOUBLE NOT NULL DEFAULT 0,
                    target_multiplier DOUBLE NOT NULL DEFAULT 7.0,
                    commission_rate DOUBLE NOT NULL DEFAULT 0.20,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            print("✔ Table 'users' ensured.")

            # --- transactions ---
            cur.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    property_id VARCHAR(255) NOT NULL,
                    property_name VARCHAR(255) NOT NULL,
                    cityscope_commission DOUBLE NOT NULL,
                    buyer_commission_amount DOUBLE NOT NULL DEFAULT 0,
                    seller_commission_amount DOUBLE NOT NULL DEFAULT 0,
                    gst_applied TINYINT(1) NOT NULL DEFAULT 0,
                    net_commission DOUBLE NOT NULL,
                    employee_commission DOUBLE NOT NULL,
                    payment_status ENUM('PENDING', 'DONE') NOT NULL DEFAULT 'PENDING',
                    transaction_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    month INT NOT NULL,
                    year INT NOT NULL,
                    quarter INT NOT NULL,
                    employee_id INT NOT NULL,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (employee_id) REFERENCES users(id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            print("✔ Table 'transactions' ensured.")

            # --- leave_requests ---
            cur.execute("""
                CREATE TABLE IF NOT EXISTS leave_requests (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    employee_id INT NOT NULL,
                    date_of_leave DATE NOT NULL,
                    applied_on DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    reason TEXT NULL,
                    status ENUM('PENDING', 'APPROVED', 'REJECTED') NOT NULL DEFAULT 'PENDING',
                    blocked TINYINT(1) NOT NULL DEFAULT 0,
                    FOREIGN KEY (employee_id) REFERENCES users(id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            print("✔ Table 'leave_requests' ensured.")

            # ----------------------------------------------------------
            # 3. Seed admin user (skip if already exists)
            # ----------------------------------------------------------
            cur.execute("SELECT id FROM users WHERE email = %s", ('admin@cityscope.in',))
            if cur.fetchone() is None:
                hashed = hash_password('admin123')
                cur.execute(
                    """INSERT INTO users (name, email, password, role)
                       VALUES (%s, %s, %s, %s)""",
                    ('Admin', 'admin@cityscope.in', hashed, 'ADMIN')
                )
                print("✔ Admin user seeded (admin@cityscope.in / admin123).")
            else:
                print("ℹ Admin user already exists — skipped.")

        print("\n✅ Seed completed successfully!")

    finally:
        conn.close()


if __name__ == '__main__':
    run_seed()
