"""
Cityscope Accounts — Database Models / CRUD Helpers
All direct MySQL interactions via pymysql.
"""

import pymysql
import pymysql.cursors
import config


# ---------------------------------------------------------------------------
# Connection helper
# ---------------------------------------------------------------------------

def get_db():
    """Return a new pymysql connection with DictCursor."""
    return pymysql.connect(
        host=config.MYSQL_HOST,
        port=config.MYSQL_PORT,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        database=config.MYSQL_DB,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )


# ============================= USERS =====================================

def get_user_by_email(email: str):
    """Fetch a single user by email. Returns dict or None."""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            return cur.fetchone()
    finally:
        db.close()


def get_user_by_id(user_id: int):
    """Fetch a single user by id. Returns dict or None."""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            return cur.fetchone()
    finally:
        db.close()


def get_all_employees():
    """Return all users with role EMPLOYEE, ordered by name."""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                "SELECT * FROM users WHERE role = 'EMPLOYEE' ORDER BY name"
            )
            return cur.fetchall()
    finally:
        db.close()


def get_employee_count():
    """Return count of employees."""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS cnt FROM users WHERE role = 'EMPLOYEE'")
            return cur.fetchone()['cnt']
    finally:
        db.close()


def create_user(name: str, email: str, password_hash: str, role: str,
                team_type: str, salary: float):
    """Insert a new user. Returns the new user id."""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                """INSERT INTO users (name, email, password, role, team_type, salary)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (name, email, password_hash, role, team_type, salary)
            )
            return cur.lastrowid
    finally:
        db.close()


# ========================== TRANSACTIONS ==================================

def create_transaction(data: dict):
    """Insert a new transaction. `data` must contain all required fields."""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                """INSERT INTO transactions
                   (property_id, property_name, total_deal_amount,
                    cityscope_commission, buyer_commission_percent,
                    seller_commission_percent, gst_applied, net_commission,
                    employee_commission, payment_status, month, year, quarter,
                    employee_id)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    data['property_id'], data['property_name'],
                    data['total_deal_amount'], data['cityscope_commission'],
                    data['buyer_commission_percent'], data['seller_commission_percent'],
                    data['gst_applied'], data['net_commission'],
                    data['employee_commission'], 'PENDING',
                    data['month'], data['year'], data['quarter'],
                    data['employee_id'],
                )
            )
            return cur.lastrowid
    finally:
        db.close()


def get_all_transactions():
    """Return all transactions with employee name, ordered by date desc."""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                """SELECT t.*, u.name AS employee_name, u.team_type
                   FROM transactions t
                   JOIN users u ON t.employee_id = u.id
                   ORDER BY t.transaction_date DESC"""
            )
            return cur.fetchall()
    finally:
        db.close()


def get_transactions_by_employee(employee_id: int):
    """Return all transactions for a specific employee, ordered by date desc."""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                """SELECT * FROM transactions
                   WHERE employee_id = %s
                   ORDER BY transaction_date DESC""",
                (employee_id,)
            )
            return cur.fetchall()
    finally:
        db.close()


def get_transactions_by_month(month: int, year: int):
    """Return transactions for a given month/year with employee info."""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                """SELECT t.*, u.name AS employee_name, u.team_type
                   FROM transactions t
                   JOIN users u ON t.employee_id = u.id
                   WHERE t.month = %s AND t.year = %s
                   ORDER BY t.transaction_date DESC""",
                (month, year)
            )
            return cur.fetchall()
    finally:
        db.close()


def get_transaction_count():
    """Return total number of transactions."""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS cnt FROM transactions")
            return cur.fetchone()['cnt']
    finally:
        db.close()


def get_pending_commission_total():
    """Return sum of employee_commission where status is PENDING."""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                """SELECT COALESCE(SUM(employee_commission), 0) AS total
                   FROM transactions WHERE payment_status = 'PENDING'"""
            )
            return cur.fetchone()['total']
    finally:
        db.close()


def mark_transaction_paid(transaction_id: int):
    """Set payment_status to DONE for a transaction."""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                "UPDATE transactions SET payment_status = 'DONE' WHERE id = %s",
                (transaction_id,)
            )
    finally:
        db.close()


def get_employee_business_for_month(employee_id: int, month: int, year: int) -> float:
    """Sum of cityscope_commission for an employee in a given month/year."""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                """SELECT COALESCE(SUM(cityscope_commission), 0) AS total
                   FROM transactions
                   WHERE employee_id = %s AND month = %s AND year = %s""",
                (employee_id, month, year)
            )
            return cur.fetchone()['total']
    finally:
        db.close()


def get_employee_business_for_quarter(employee_id: int, quarter: int, fy_year: int) -> float:
    """Sum of cityscope_commission for an employee in a given FY quarter.

    The fy_year is the starting year of the FY.
    Quarter months may span two calendar years (Q4: Jan-Mar of fy_year+1).
    """
    from commission import get_quarter_months
    months = get_quarter_months(quarter)

    db = get_db()
    try:
        with db.cursor() as cur:
            total = 0.0
            for m in months:
                # Q4 months (1,2,3) belong to fy_year+1 calendar year
                cal_year = fy_year + 1 if m <= 3 else fy_year
                cur.execute(
                    """SELECT COALESCE(SUM(cityscope_commission), 0) AS total
                       FROM transactions
                       WHERE employee_id = %s AND month = %s AND year = %s""",
                    (employee_id, m, cal_year)
                )
                total += cur.fetchone()['total']
            return total
    finally:
        db.close()


def get_commission_summary(employee_id: int):
    """Return (pending, received) commission totals for an employee."""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                """SELECT
                     COALESCE(SUM(CASE WHEN payment_status='PENDING' THEN employee_commission ELSE 0 END), 0) AS pending,
                     COALESCE(SUM(CASE WHEN payment_status='DONE' THEN employee_commission ELSE 0 END), 0) AS received
                   FROM transactions WHERE employee_id = %s""",
                (employee_id,)
            )
            return cur.fetchone()
    finally:
        db.close()


# ========================= LEAVE REQUESTS =================================

def create_leave_request(employee_id: int, date_of_leave: str, reason: str, blocked: bool):
    """Insert a new leave request. date_of_leave should be a date string 'YYYY-MM-DD'."""
    status = 'REJECTED' if blocked else 'PENDING'
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                """INSERT INTO leave_requests (employee_id, date_of_leave, reason, blocked, status)
                   VALUES (%s, %s, %s, %s, %s)""",
                (employee_id, date_of_leave, reason, int(blocked), status)
            )
            return cur.lastrowid
    finally:
        db.close()


def get_all_leave_requests():
    """Return all leave requests with employee name, ordered by applied_on desc."""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                """SELECT lr.*, u.name AS employee_name
                   FROM leave_requests lr
                   JOIN users u ON lr.employee_id = u.id
                   ORDER BY lr.applied_on DESC"""
            )
            return cur.fetchall()
    finally:
        db.close()


def get_pending_leave_requests():
    """Return leave requests with PENDING status."""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                """SELECT lr.*, u.name AS employee_name
                   FROM leave_requests lr
                   JOIN users u ON lr.employee_id = u.id
                   WHERE lr.status = 'PENDING'
                   ORDER BY lr.date_of_leave ASC"""
            )
            return cur.fetchall()
    finally:
        db.close()


def get_pending_leave_count():
    """Return count of pending leave requests."""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS cnt FROM leave_requests WHERE status = 'PENDING'")
            return cur.fetchone()['cnt']
    finally:
        db.close()


def get_leaves_by_employee(employee_id: int, limit: int = 10):
    """Return leave requests for an employee, ordered by date desc, limited."""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                """SELECT * FROM leave_requests
                   WHERE employee_id = %s
                   ORDER BY date_of_leave DESC
                   LIMIT %s""",
                (employee_id, limit)
            )
            return cur.fetchall()
    finally:
        db.close()


def approve_leave(leave_id: int):
    """Set leave status to APPROVED."""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                "UPDATE leave_requests SET status = 'APPROVED' WHERE id = %s",
                (leave_id,)
            )
    finally:
        db.close()


def reject_leave(leave_id: int):
    """Set leave status to REJECTED."""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                "UPDATE leave_requests SET status = 'REJECTED' WHERE id = %s",
                (leave_id,)
            )
    finally:
        db.close()
