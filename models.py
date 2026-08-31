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
                team_type: str, salary: float, target_multiplier: float = None, commission_rate: float = None):
    """Insert a new user. Returns the new user id."""
    from commission import TEAM_CONFIG
    if target_multiplier is None:
        target_multiplier = TEAM_CONFIG.get(team_type, {}).get('multiplier', 7.0) if team_type else 0.0
    if commission_rate is None:
        commission_rate = TEAM_CONFIG.get(team_type, {}).get('commission_rate', 0.20) if team_type else 0.0

    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                """INSERT INTO users (name, email, password, role, team_type, salary, target_multiplier, commission_rate)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (name, email, password_hash, role, team_type, salary, target_multiplier, commission_rate)
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
                   (property_id, property_name, basic_price,
                    cityscope_commission, buyer_commission_amount,
                    buyer_commission_received, buyer_commission_date, buyer_gst_applied,
                    seller_commission_amount, seller_commission_received,
                    seller_commission_date, seller_gst_applied, gst_applied, net_commission,
                    employee_commission, payment_status, transaction_date, month, year, quarter,
                    employee_id)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    data['property_id'], data['property_name'], data.get('basic_price', 0),
                    data['cityscope_commission'], data.get('buyer_commission_amount', 0),
                    data.get('buyer_commission_received', 0), data.get('buyer_commission_date') or None,
                    data.get('buyer_gst_applied', 0),
                    data.get('seller_commission_amount', 0),
                    data.get('seller_commission_received', 0), data.get('seller_commission_date') or None,
                    data.get('seller_gst_applied', 0), data.get('gst_applied', 0), data['net_commission'],
                    data['employee_commission'], data.get('payment_status', 'PENDING'),
                    data['transaction_date'], data['month'], data['year'], data['quarter'],
                    data['employee_id'],
                )
            )
            return cur.lastrowid
    finally:
        db.close()

def update_transaction(transaction_id: int, data: dict):
    """Update an existing transaction."""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                """UPDATE transactions SET
                    property_id = %s, property_name = %s, basic_price = %s,
                    cityscope_commission = %s, buyer_commission_amount = %s,
                    buyer_commission_received = %s, buyer_commission_date = %s, buyer_gst_applied = %s,
                    seller_commission_amount = %s, seller_commission_received = %s,
                    seller_commission_date = %s, seller_gst_applied = %s, gst_applied = %s, net_commission = %s,
                    employee_commission = %s, transaction_date = %s, month = %s, year = %s, quarter = %s,
                    employee_id = %s, payment_status = %s
                   WHERE id = %s""",
                (
                    data['property_id'], data['property_name'], data.get('basic_price', 0),
                    data['cityscope_commission'], data.get('buyer_commission_amount', 0),
                    data.get('buyer_commission_received', 0), data.get('buyer_commission_date') or None,
                    data.get('buyer_gst_applied', 0),
                    data.get('seller_commission_amount', 0),
                    data.get('seller_commission_received', 0), data.get('seller_commission_date') or None,
                    data.get('seller_gst_applied', 0), data.get('gst_applied', 0), data['net_commission'],
                    data['employee_commission'],
                    data['transaction_date'], data['month'], data['year'], data['quarter'],
                    data['employee_id'], data.get('payment_status', 'PENDING'),
                    transaction_id
                )
            )
    finally:
        db.close()


def get_all_transactions(sort='added'):
    """Return all transactions with employee name, ordered dynamically."""
    db = get_db()
    
    order_clause = "t.created_at DESC"
    if sort == 'date':
        order_clause = "t.transaction_date DESC"
    elif sort == 'updated':
        order_clause = "t.updated_at DESC"
        
    try:
        with db.cursor() as cur:
            cur.execute(
                f"""SELECT t.*, u.name AS employee_name, u.team_type
                   FROM transactions t
                   JOIN users u ON t.employee_id = u.id
                   ORDER BY {order_clause}"""
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
    """Set payment_status to DONE and mark received amounts as fully paid."""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                """UPDATE transactions SET 
                    payment_status = 'DONE',
                    buyer_commission_received = buyer_commission_amount,
                    seller_commission_received = seller_commission_amount,
                    buyer_commission_date = IFNULL(buyer_commission_date, CURRENT_DATE()),
                    seller_commission_date = IFNULL(seller_commission_date, CURRENT_DATE())
                   WHERE id = %s""",
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

def create_leave_request(employee_id: int, date_of_leave: str, reason: str, blocked: bool, status: str = 'PENDING'):
    """Insert a new leave request. date_of_leave should be a date string 'YYYY-MM-DD'."""
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


def delete_leave_request(leave_id: int):
    """Delete a leave request."""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                "DELETE FROM leave_requests WHERE id = %s",
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


def delete_transaction(transaction_id: int):
    """Delete a transaction by ID."""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("DELETE FROM transactions WHERE id = %s", (transaction_id,))
    finally:
        db.close()


def update_user(user_id: int, data: dict):
    """Update employee details in the database."""
    db = get_db()
    try:
        with db.cursor() as cur:
            if 'password_hash' in data:
                cur.execute(
                    """UPDATE users SET
                        name = %s, email = %s, salary = %s, team_type = %s,
                        target_multiplier = %s, commission_rate = %s, password = %s
                       WHERE id = %s""",
                    (data['name'], data['email'], data['salary'], data['team_type'],
                     data['target_multiplier'], data['commission_rate'], data['password_hash'], user_id)
                )
            else:
                cur.execute(
                    """UPDATE users SET
                        name = %s, email = %s, salary = %s, team_type = %s,
                        target_multiplier = %s, commission_rate = %s
                       WHERE id = %s""",
                    (data['name'], data['email'], data['salary'], data['team_type'],
                     data['target_multiplier'], data['commission_rate'], user_id)
                )
    finally:
        db.close()


def delete_user(user_id: int):
    """Delete a user and all their associated records (leaves, transactions, commissions)."""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("DELETE FROM leave_requests WHERE employee_id = %s", (user_id,))
            cur.execute("DELETE FROM transactions WHERE employee_id = %s", (user_id,))
            cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
    finally:
        db.close()


def get_transaction_by_id(txn_id: int):
    """Fetch transaction by ID."""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("SELECT * FROM transactions WHERE id = %s", (txn_id,))
            return cur.fetchone()
    finally:
        db.close()


def get_employee_transactions_for_quarter(employee_id: int, quarter: int, fy_year: int):
    """Return all transactions for an employee in a given FY quarter."""
    from commission import get_quarter_months
    months = get_quarter_months(quarter)
    
    db = get_db()
    try:
        with db.cursor() as cur:
            txns = []
            for m in months:
                cal_year = fy_year + 1 if m <= 3 else fy_year
                cur.execute(
                    """SELECT * FROM transactions
                       WHERE employee_id = %s AND month = %s AND year = %s""",
                    (employee_id, m, cal_year)
                )
                txns.extend(cur.fetchall())
            return txns
    finally:
        db.close()


def recalculate_employee_quarterly_commissions(employee_id: int, quarter: int, fy_year: int):
    """Recalculate employee commission for a specific quarter/year based on target progress."""
    employee = get_user_by_id(employee_id)
    if not employee or employee['role'] != 'EMPLOYEE':
        return

    salary = employee['salary']
    multiplier = employee['target_multiplier']
    commission_rate = employee['commission_rate']

    # Quarterly target
    from commission import get_quarterly_target, calculate_commission
    q_target = get_quarterly_target(salary, target_multiplier=multiplier)

    # Get all transactions for this quarter
    txns = get_employee_transactions_for_quarter(employee_id, quarter, fy_year)

    # Calculate total business done
    total_business = sum(t['cityscope_commission'] for t in txns)

    # Achievement percentage
    if q_target <= 0:
        progress = 100.0
    else:
        progress = (total_business / q_target) * 100.0

    # Adjustment factor
    if progress >= 95.0:
        factor = 1.0
    else:
        factor = max(0.05, round(progress / 100.0, 4))

    # Update each transaction in the database
    db = get_db()
    try:
        with db.cursor() as cur:
            for t in txns:
                # Recalculate employee commission
                _, new_emp_commission = calculate_commission(
                    buyer_amount=t.get('buyer_commission_amount', 0),
                    buyer_gst_applied=bool(t.get('buyer_gst_applied', False)),
                    seller_amount=t.get('seller_commission_amount', 0),
                    seller_gst_applied=bool(t.get('seller_gst_applied', False)),
                    commission_rate=commission_rate,
                    factor=factor
                )
                cur.execute(
                    "UPDATE transactions SET employee_commission = %s WHERE id = %s",
                    (new_emp_commission, t['id'])
                )
    finally:
        db.close()


def save_transaction_payments(transaction_id: int, party: str, amounts: list, dates: list):
    """Save payment installments for a specific transaction and party (BUYER or SELLER)."""
    db = get_db()
    try:
        with db.cursor() as cur:
            # Delete old installments
            cur.execute(
                "DELETE FROM commission_payments WHERE transaction_id = %s AND party = %s",
                (transaction_id, party)
            )
            # Insert new ones
            for amt_str, date_str in zip(amounts, dates):
                if not amt_str or not date_str:
                    continue
                try:
                    amount = float(amt_str)
                    if amount <= 0:
                        continue
                except ValueError:
                    continue
                cur.execute(
                    """INSERT INTO commission_payments (transaction_id, party, amount, payment_date)
                       VALUES (%s, %s, %s, %s)""",
                    (transaction_id, party, amount, date_str)
                )
    finally:
        db.close()


def get_transaction_payments_dict():
    """Fetch all payments and group them by transaction_id in a dictionary format."""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("SELECT * FROM commission_payments ORDER BY payment_date ASC")
            rows = cur.fetchall()
            payments_dict = {}
            for r in rows:
                txn_id = r['transaction_id']
                party = r['party']
                if txn_id not in payments_dict:
                    payments_dict[txn_id] = {'BUYER': [], 'SELLER': []}
                # Format payment date as string YYYY-MM-DD
                payment_date_str = r['payment_date'].strftime('%Y-%m-%d') if r['payment_date'] else ''
                payments_dict[txn_id][party].append({
                    'id': r['id'],
                    'amount': r['amount'],
                    'payment_date': payment_date_str
                })
            return payments_dict
    finally:
        db.close()


def settle_transaction(transaction_id: int):
    """Set payment_status to DONE without changing received amounts."""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                "UPDATE transactions SET payment_status = 'DONE' WHERE id = %s",
                (transaction_id,)
            )
    finally:
        db.close()

