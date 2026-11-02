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
                    is_active TINYINT(1) NOT NULL DEFAULT 1,
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
                    basic_price DOUBLE NOT NULL DEFAULT 0,
                    cityscope_commission DOUBLE NOT NULL,
                    buyer_commission_amount DOUBLE NOT NULL DEFAULT 0,
                    buyer_commission_received DOUBLE NOT NULL DEFAULT 0,
                    buyer_commission_date DATE NULL,
                    seller_commission_amount DOUBLE NOT NULL DEFAULT 0,
                    seller_commission_received DOUBLE NOT NULL DEFAULT 0,
                    seller_commission_date DATE NULL,
                    buyer_gst_applied TINYINT(1) NOT NULL DEFAULT 0,
                    seller_gst_applied TINYINT(1) NOT NULL DEFAULT 0,
                    buyer_name VARCHAR(255) NULL,
                    seller_name VARCHAR(255) NULL,
                    buyer_is_broker TINYINT(1) NOT NULL DEFAULT 0,
                    seller_is_broker TINYINT(1) NOT NULL DEFAULT 0,
                    gst_applied TINYINT(1) NOT NULL DEFAULT 0,
                    net_commission DOUBLE NOT NULL,
                    employee_commission DOUBLE NOT NULL,
                    payment_status ENUM('PENDING', 'PARTIAL', 'DONE') NOT NULL DEFAULT 'PENDING',
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

            # --- Migrations for existing databases ---
            cur.execute("SHOW COLUMNS FROM transactions LIKE 'buyer_name'")
            if cur.fetchone() is None:
                cur.execute("ALTER TABLE transactions ADD COLUMN buyer_name VARCHAR(255) NULL")
                cur.execute("ALTER TABLE transactions ADD COLUMN seller_name VARCHAR(255) NULL")
                cur.execute("ALTER TABLE transactions ADD COLUMN buyer_is_broker TINYINT(1) NOT NULL DEFAULT 0")
                cur.execute("ALTER TABLE transactions ADD COLUMN seller_is_broker TINYINT(1) NOT NULL DEFAULT 0")
                print("✔ Buyer/Seller name & broker columns migrated on transactions.")
            # users table migrations
            cur.execute("SHOW COLUMNS FROM users LIKE 'team_type'")
            if cur.fetchone() is None:
                cur.execute("ALTER TABLE users ADD COLUMN team_type ENUM('CORE_TEAM', 'NORMAL_TEAM', 'RENT_TEAM') NULL")
                print("✔ Column 'team_type' migrated on users.")

            cur.execute("SHOW COLUMNS FROM users LIKE 'salary'")
            if cur.fetchone() is None:
                cur.execute("ALTER TABLE users ADD COLUMN salary DOUBLE NOT NULL DEFAULT 0")
                print("✔ Column 'salary' migrated on users.")

            cur.execute("SHOW COLUMNS FROM users LIKE 'target_multiplier'")
            if cur.fetchone() is None:
                cur.execute("ALTER TABLE users ADD COLUMN target_multiplier DOUBLE NOT NULL DEFAULT 7.0")
                print("✔ Column 'target_multiplier' migrated on users.")

            cur.execute("SHOW COLUMNS FROM users LIKE 'commission_rate'")
            if cur.fetchone() is None:
                cur.execute("ALTER TABLE users ADD COLUMN commission_rate DOUBLE NOT NULL DEFAULT 0.20")
                print("✔ Column 'commission_rate' migrated on users.")

            cur.execute("SHOW COLUMNS FROM users LIKE 'is_active'")
            if cur.fetchone() is None:
                cur.execute("ALTER TABLE users ADD COLUMN is_active TINYINT(1) NOT NULL DEFAULT 1")
                print("✔ Column 'is_active' migrated on users.")

            cur.execute("""
                ALTER TABLE transactions 
                MODIFY COLUMN payment_status ENUM('PENDING', 'PARTIAL', 'DONE') NOT NULL DEFAULT 'PENDING'
            """)
            
            cur.execute("SHOW COLUMNS FROM transactions LIKE 'basic_price'")
            if cur.fetchone() is None:
                cur.execute("ALTER TABLE transactions ADD COLUMN basic_price DOUBLE NOT NULL DEFAULT 0")
                print("✔ Column 'basic_price' migrated.")

            cur.execute("SHOW COLUMNS FROM transactions LIKE 'buyer_commission_received'")
            if cur.fetchone() is None:
                cur.execute("ALTER TABLE transactions ADD COLUMN buyer_commission_received DOUBLE NOT NULL DEFAULT 0")
                print("✔ Column 'buyer_commission_received' migrated.")

            cur.execute("SHOW COLUMNS FROM transactions LIKE 'buyer_commission_date'")
            if cur.fetchone() is None:
                cur.execute("ALTER TABLE transactions ADD COLUMN buyer_commission_date DATE NULL")
                print("✔ Column 'buyer_commission_date' migrated.")

            cur.execute("SHOW COLUMNS FROM transactions LIKE 'seller_commission_received'")
            if cur.fetchone() is None:
                cur.execute("ALTER TABLE transactions ADD COLUMN seller_commission_received DOUBLE NOT NULL DEFAULT 0")
                print("✔ Column 'seller_commission_received' migrated.")

            cur.execute("SHOW COLUMNS FROM transactions LIKE 'seller_commission_date'")
            if cur.fetchone() is None:
                cur.execute("ALTER TABLE transactions ADD COLUMN seller_commission_date DATE NULL")
                print("✔ Column 'seller_commission_date' migrated.")

            cur.execute("SHOW COLUMNS FROM transactions LIKE 'buyer_gst_applied'")
            if cur.fetchone() is None:
                cur.execute("ALTER TABLE transactions ADD COLUMN buyer_gst_applied TINYINT(1) NOT NULL DEFAULT 0")
                print("✔ Column 'buyer_gst_applied' migrated.")

            cur.execute("SHOW COLUMNS FROM transactions LIKE 'seller_gst_applied'")
            if cur.fetchone() is None:
                cur.execute("ALTER TABLE transactions ADD COLUMN seller_gst_applied TINYINT(1) NOT NULL DEFAULT 0")
                print("✔ Column 'seller_gst_applied' migrated.")

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

            # --- commission_payments ---
            cur.execute("""
                CREATE TABLE IF NOT EXISTS commission_payments (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    transaction_id INT NOT NULL,
                    party ENUM('BUYER', 'SELLER') NOT NULL,
                    amount DOUBLE NOT NULL,
                    payment_date DATE NOT NULL,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            print("✔ Table 'commission_payments' ensured.")

            # --- commission_payouts (tracks Cityscope paying employees their share) ---
            cur.execute("""
                CREATE TABLE IF NOT EXISTS commission_payouts (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    transaction_id INT NOT NULL,
                    employee_id INT NOT NULL,
                    amount DOUBLE NOT NULL,
                    paid_date DATE NOT NULL,
                    notes TEXT NULL,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE CASCADE,
                    FOREIGN KEY (employee_id) REFERENCES users(id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            print("✔ Table 'commission_payouts' ensured.")

            # --- advances (salary / commission advances to employees) ---
            cur.execute("""
                CREATE TABLE IF NOT EXISTS advances (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    employee_id INT NOT NULL,
                    advance_type ENUM('SALARY', 'COMMISSION') NOT NULL,
                    amount DOUBLE NOT NULL,
                    advance_date DATE NOT NULL,
                    reason TEXT NULL,
                    status ENUM('ACTIVE', 'SETTLED') NOT NULL DEFAULT 'ACTIVE',
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (employee_id) REFERENCES users(id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            print("✔ Table 'advances' ensured.")

            # --- Migration: emp_payout_status on transactions ---
            cur.execute("SHOW COLUMNS FROM transactions LIKE 'emp_payout_status'")
            if cur.fetchone() is None:
                cur.execute("ALTER TABLE transactions ADD COLUMN emp_payout_status ENUM('UNPAID', 'PAID') NOT NULL DEFAULT 'UNPAID'")
                print("✔ Column 'emp_payout_status' migrated on transactions.")

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

            # --- Seed dmistry@cityscope.in ---
            cur.execute("SELECT id FROM users WHERE email = %s", ('dmistry@cityscope.in',))
            if cur.fetchone() is None:
                hashed = hash_password('dmistry')
                cur.execute(
                    """INSERT INTO users (name, email, password, role)
                       VALUES (%s, %s, %s, %s)""",
                    ('D Mistry', 'dmistry@cityscope.in', hashed, 'ADMIN')
                )
                print("✔ Admin user seeded (dmistry@cityscope.in / dmistry).")
            else:
                print("ℹ Admin user dmistry@cityscope.in already exists — skipped.")

        print("\n✅ Seed completed successfully!")

    finally:
        conn.close()


if __name__ == '__main__':
    run_seed()
