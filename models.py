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
                    seller_commission_date, seller_gst_applied,
                    buyer_name, seller_name, buyer_is_broker, seller_is_broker,
                    gst_applied, net_commission,
                    employee_commission, payment_status, transaction_date, month, year, quarter,
                    employee_id)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    data['property_id'], data['property_name'], data.get('basic_price', 0),
                    data['cityscope_commission'], data.get('buyer_commission_amount', 0),
                    data.get('buyer_commission_received', 0), data.get('buyer_commission_date') or None,
                    data.get('buyer_gst_applied', 0),
                    data.get('seller_commission_amount', 0),
                    data.get('seller_commission_received', 0), data.get('seller_commission_date') or None,
                    data.get('seller_gst_applied', 0),
                    data.get('buyer_name') or None, data.get('seller_name') or None,
                    data.get('buyer_is_broker', 0), data.get('seller_is_broker', 0),
                    data.get('gst_applied', 0), data['net_commission'],
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
                    seller_commission_date = %s, seller_gst_applied = %s,
                    buyer_name = %s, seller_name = %s, buyer_is_broker = %s, seller_is_broker = %s,
                    gst_applied = %s, net_commission = %s,
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
                    data.get('seller_gst_applied', 0),
                    data.get('buyer_name') or None, data.get('seller_name') or None,
                    data.get('buyer_is_broker', 0), data.get('seller_is_broker', 0),
                    data.get('gst_applied', 0), data['net_commission'],
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


def get_pending_brokerage_total():
    """Return sum of pending brokerage (from buyers + sellers) across all transactions."""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                """SELECT 
                    COALESCE(SUM(GREATEST(0, buyer_commission_amount - buyer_commission_received) + 
                                 GREATEST(0, seller_commission_amount - seller_commission_received)), 0) AS total
                   FROM transactions 
                   WHERE (buyer_commission_amount > buyer_commission_received)
                      OR (seller_commission_amount > seller_commission_received)"""
            )
            return cur.fetchone()['total']
    finally:
        db.close()


def get_pending_brokerage_details():
    """Return summary and itemized breakdown of pending brokerage from clients.
    Each item represents a party (buyer or seller) from whom brokerage is pending,
    including the responsible employee and transaction details.
    """
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                """SELECT t.*, u.name AS employee_name, u.team_type
                   FROM transactions t
                   JOIN users u ON t.employee_id = u.id
                   WHERE (t.buyer_commission_amount > t.buyer_commission_received)
                      OR (t.seller_commission_amount > t.seller_commission_received)
                   ORDER BY t.transaction_date DESC, t.id DESC"""
            )
            rows = cur.fetchall()

            items = []
            total_pending = 0.0
            total_buyer_pending = 0.0
            total_seller_pending = 0.0
            distinct_deals = set()
            employees_set = set()

            for t in rows:
                b_total = float(t.get('buyer_commission_amount') or 0.0)
                b_recv = float(t.get('buyer_commission_received') or 0.0)
                b_pend = max(0.0, b_total - b_recv)

                s_total = float(t.get('seller_commission_amount') or 0.0)
                s_recv = float(t.get('seller_commission_received') or 0.0)
                s_pend = max(0.0, s_total - s_recv)

                emp_name = t.get('employee_name') or 'Unknown'
                deal_has_pending = False

                if b_pend > 0:
                    total_buyer_pending += b_pend
                    total_pending += b_pend
                    deal_has_pending = True
                    employees_set.add(emp_name)
                    items.append({
                        'transaction_id': t['id'],
                        'property_id': t['property_id'],
                        'property_name': t['property_name'],
                        'transaction_date': t.get('transaction_date'),
                        'employee_id': t['employee_id'],
                        'employee_name': emp_name,
                        'party_type': 'BUYER',
                        'party_role': 'Buyer',
                        'party_name': (t.get('buyer_name') or '').strip() or 'Buyer (Unspecified)',
                        'is_broker': bool(t.get('buyer_is_broker')),
                        'total_amount': b_total,
                        'received_amount': b_recv,
                        'pending_amount': b_pend,
                        'payment_status': t.get('payment_status', 'PENDING'),
                    })

                if s_pend > 0:
                    total_seller_pending += s_pend
                    total_pending += s_pend
                    deal_has_pending = True
                    employees_set.add(emp_name)
                    items.append({
                        'transaction_id': t['id'],
                        'property_id': t['property_id'],
                        'property_name': t['property_name'],
                        'transaction_date': t.get('transaction_date'),
                        'employee_id': t['employee_id'],
                        'employee_name': emp_name,
                        'party_type': 'SELLER',
                        'party_role': 'Seller',
                        'party_name': (t.get('seller_name') or '').strip() or 'Seller (Unspecified)',
                        'is_broker': bool(t.get('seller_is_broker')),
                        'total_amount': s_total,
                        'received_amount': s_recv,
                        'pending_amount': s_pend,
                        'payment_status': t.get('payment_status', 'PENDING'),
                    })

                if deal_has_pending:
                    distinct_deals.add(t['id'])

            # Sort items by pending_amount descending
            items.sort(key=lambda x: x['pending_amount'], reverse=True)

            return {
                'total_pending': total_pending,
                'buyer_pending': total_buyer_pending,
                'seller_pending': total_seller_pending,
                'deal_count': len(distinct_deals),
                'items': items,
                'records': items,
                'employees': sorted(list(employees_set)),
                'count': len(items)
            }
    finally:
        db.close()



def mark_transaction_paid(transaction_id: int):
    """Set payment_status to DONE, mark received amounts as fully paid, and recalculate commission."""
    txn = get_transaction_by_id(transaction_id)
    if not txn:
        return
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

    from commission import get_fy_year
    fy_year = get_fy_year(txn['month'], txn['year'])
    recalculate_employee_quarterly_commissions(txn['employee_id'], txn['quarter'], fy_year)


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


def update_user_password(user_id: int, password_hash: str):
    """Update password hash for a specific user."""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("UPDATE users SET password = %s WHERE id = %s", (password_hash, user_id))
    finally:
        db.close()


def delete_user(user_id: int):
    """Delete a user and all their associated records (leaves, transactions, commissions, payouts, advances)."""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("DELETE FROM leave_requests WHERE employee_id = %s", (user_id,))
            cur.execute("DELETE FROM commission_payouts WHERE employee_id = %s", (user_id,))
            cur.execute("DELETE FROM advances WHERE employee_id = %s", (user_id,))
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


def get_employee_fy_spillover_summary(employee_id: int, fy_year: int):
    """Calculate quarterly business, targets, spillover adjustments, and effective factors for an FY.

    Returns a list of dicts for Q1, Q2, Q3, Q4 with raw & adjusted performance.
    """
    employee = get_user_by_id(employee_id)
    if not employee or employee['role'] != 'EMPLOYEE':
        return []

    salary = employee['salary']
    multiplier = employee['target_multiplier']
    from commission import get_quarterly_target
    q_target = get_quarterly_target(salary, target_multiplier=multiplier)

    # 1. Fetch raw business for Q1, Q2, Q3, Q4 of this FY
    quarters_data = []
    for q in range(1, 5):
        txns = get_employee_transactions_for_quarter(employee_id, q, fy_year)
        raw_b = sum(t['cityscope_commission'] for t in txns)
        raw_pct = (raw_b / q_target * 100.0) if q_target > 0 else 100.0
        deficit = max(0.0, q_target - raw_b) if q_target > 0 else 0.0
        surplus = max(0.0, raw_b - q_target) if q_target > 0 else 0.0
        
        quarters_data.append({
            'q': q,
            'txns': txns,
            'target': q_target,
            'raw_business': raw_b,
            'raw_pct': round(raw_pct, 1),
            'rem_deficit': deficit,
            'rem_surplus': surplus,
            'spillover_received': 0.0,
            'spillover_given': 0.0,
        })

    # 2. Spillover Algorithm: Surplus from later quarters fills deficit of earlier quarters (closest preceding deficit first)
    for i in range(4):
        if quarters_data[i]['rem_surplus'] > 0:
            avail_surplus = quarters_data[i]['rem_surplus']
            for j in range(i - 1, -1, -1):
                if quarters_data[j]['rem_deficit'] > 0 and avail_surplus > 0:
                    transfer = min(avail_surplus, quarters_data[j]['rem_deficit'])
                    quarters_data[j]['spillover_received'] += transfer
                    quarters_data[j]['rem_deficit'] -= transfer
                    quarters_data[i]['spillover_given'] += transfer
                    avail_surplus -= transfer
            quarters_data[i]['rem_surplus'] = avail_surplus

    # 3. Calculate final adjusted totals & effective factor
    summary = []
    for qd in quarters_data:
        adj_b = qd['raw_business'] + qd['spillover_received'] - qd['spillover_given']
        adj_pct = (adj_b / qd['target'] * 100.0) if qd['target'] > 0 else 100.0
        
        if adj_pct >= 95.0:
            factor = 1.0
        else:
            factor = max(0.05, round(adj_pct / 100.0, 4))
            
        summary.append({
            'q': qd['q'],
            'target': qd['target'],
            'raw_business': qd['raw_business'],
            'raw_pct': qd['raw_pct'],
            'spillover_received': qd['spillover_received'],
            'spillover_given': qd['spillover_given'],
            'adjusted_business': adj_b,
            'adjusted_pct': round(adj_pct, 1),
            'factor': factor,
            'txns': qd['txns']
        })

    return summary


def recalculate_employee_quarterly_commissions(employee_id: int, quarter: int, fy_year: int):
    """Recalculate employee commission for all 4 quarters of an FY with spillover adjustment."""
    employee = get_user_by_id(employee_id)
    if not employee or employee['role'] != 'EMPLOYEE':
        return

    commission_rate = employee['commission_rate']
    summary = get_employee_fy_spillover_summary(employee_id, fy_year)

    from commission import calculate_commission
    db = get_db()
    try:
        with db.cursor() as cur:
            for qd in summary:
                factor = qd['factor']
                for t in qd['txns']:
                    new_net_comm, new_emp_commission = calculate_commission(
                        buyer_amount=t.get('buyer_commission_received', 0),
                        buyer_gst_applied=bool(t.get('buyer_gst_applied', False)),
                        seller_amount=t.get('seller_commission_received', 0),
                        seller_gst_applied=bool(t.get('seller_gst_applied', False)),
                        commission_rate=commission_rate,
                        factor=factor
                    )
                    cur.execute(
                        "UPDATE transactions SET net_commission = %s, employee_commission = %s WHERE id = %s",
                        (new_net_comm, new_emp_commission, t['id'])
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


# ========================= COMMISSION PAYOUTS ================================

def mark_employee_commission_paid(transaction_id: int, employee_id: int, amount: float, paid_date: str, notes: str = None):
    """Record that Cityscope paid the employee their commission for a transaction."""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                """INSERT INTO commission_payouts (transaction_id, employee_id, amount, paid_date, notes)
                   VALUES (%s, %s, %s, %s, %s)""",
                (transaction_id, employee_id, amount, paid_date, notes)
            )
            cur.execute(
                "UPDATE transactions SET emp_payout_status = 'PAID' WHERE id = %s",
                (transaction_id,)
            )
    finally:
        db.close()


def mark_employee_commission_unpaid(transaction_id: int):
    """Revert employee payout — delete payout record and set status back to UNPAID."""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                "DELETE FROM commission_payouts WHERE transaction_id = %s",
                (transaction_id,)
            )
            cur.execute(
                "UPDATE transactions SET emp_payout_status = 'UNPAID' WHERE id = %s",
                (transaction_id,)
            )
    finally:
        db.close()


def get_employee_payout_summary(employee_id: int):
    """Return payout totals for an employee: total earned, total paid out, total unpaid."""
    db = get_db()
    try:
        with db.cursor() as cur:
            # Total earned commission
            cur.execute(
                """SELECT COALESCE(SUM(employee_commission), 0) AS total_earned
                   FROM transactions WHERE employee_id = %s""",
                (employee_id,)
            )
            total_earned = cur.fetchone()['total_earned']

            # Total paid out
            cur.execute(
                """SELECT COALESCE(SUM(employee_commission), 0) AS total_paid
                   FROM transactions WHERE employee_id = %s AND emp_payout_status = 'PAID'""",
                (employee_id,)
            )
            total_paid = cur.fetchone()['total_paid']

            # Total unpaid
            cur.execute(
                """SELECT COALESCE(SUM(employee_commission), 0) AS total_unpaid
                   FROM transactions WHERE employee_id = %s AND emp_payout_status = 'UNPAID'""",
                (employee_id,)
            )
            total_unpaid = cur.fetchone()['total_unpaid']

            return {
                'total_earned': total_earned,
                'total_paid': total_paid,
                'total_unpaid': total_unpaid,
            }
    finally:
        db.close()


def get_payouts_by_employee(employee_id: int):
    """Return all payout records for an employee, ordered by date desc."""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                """SELECT cp.*, t.property_name, t.property_id
                   FROM commission_payouts cp
                   JOIN transactions t ON cp.transaction_id = t.id
                   WHERE cp.employee_id = %s
                   ORDER BY cp.paid_date DESC""",
                (employee_id,)
            )
            return cur.fetchall()
    finally:
        db.close()


# ========================= ADVANCES ==========================================

def create_advance(employee_id: int, advance_type: str, amount: float, advance_date: str, reason: str = None):
    """Record a salary or commission advance given to an employee."""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                """INSERT INTO advances (employee_id, advance_type, amount, advance_date, reason)
                   VALUES (%s, %s, %s, %s, %s)""",
                (employee_id, advance_type, amount, advance_date, reason)
            )
            return cur.lastrowid
    finally:
        db.close()


def get_advances_by_employee(employee_id: int):
    """Return all advances for an employee, ordered by date desc."""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                """SELECT * FROM advances
                   WHERE employee_id = %s
                   ORDER BY advance_date DESC""",
                (employee_id,)
            )
            return cur.fetchall()
    finally:
        db.close()


def get_all_advances():
    """Return all advances with employee name, ordered by date desc."""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                """SELECT a.*, u.name AS employee_name
                   FROM advances a
                   JOIN users u ON a.employee_id = u.id
                   ORDER BY a.advance_date DESC"""
            )
            return cur.fetchall()
    finally:
        db.close()


def settle_advance(advance_id: int):
    """Mark an advance as settled."""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                "UPDATE advances SET status = 'SETTLED' WHERE id = %s",
                (advance_id,)
            )
    finally:
        db.close()


def delete_advance(advance_id: int):
    """Delete an advance record."""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("DELETE FROM advances WHERE id = %s", (advance_id,))
    finally:
        db.close()


def get_active_advances_total(employee_id: int) -> float:
    """Return sum of active (unsettled) advances for an employee."""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                """SELECT COALESCE(SUM(amount), 0) AS total
                   FROM advances WHERE employee_id = %s AND status = 'ACTIVE'""",
                (employee_id,)
            )
            return cur.fetchone()['total']
    finally:
        db.close()


def get_advance_by_id(advance_id: int):
    """Fetch an advance by ID."""
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("SELECT * FROM advances WHERE id = %s", (advance_id,))
            return cur.fetchone()
    finally:
        db.close()
