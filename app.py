"""
Cityscope Accounts & Commission System
Main Flask Application - All routes and configuration.
"""

from datetime import datetime, timedelta
from flask import (
    Flask, render_template, request, redirect, url_for, session, flash
)

import config
from auth import (
    hash_password, verify_password, get_current_user,
    login_required, admin_required,
)
from commission import (
    TEAM_CONFIG, MONTH_NAMES, format_inr,
    get_quarter, get_fy_year, get_fy_label, get_quarter_months,
    calculate_commission, get_monthly_target, get_quarterly_target,
    get_progress_color, get_progress_percentage,
)
import models

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.permanent_session_lifetime = config.PERMANENT_SESSION_LIFETIME
app.config['SESSION_COOKIE_HTTPONLY'] = config.SESSION_COOKIE_HTTPONLY


# ---------------------------------------------------------------------------
# Jinja2 globals / filters - available in every template
# ---------------------------------------------------------------------------

app.jinja_env.globals.update(
    format_inr=format_inr,
    month_names=MONTH_NAMES,
    get_progress_color=get_progress_color,
)


# ---------------------------------------------------------------------------
# PUBLIC ROUTES
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    """Redirect based on session: ADMIN→/admin, EMPLOYEE→/employee, else→/login."""
    user = get_current_user()
    if user is None:
        return redirect(url_for('login'))
    if user['role'] == 'ADMIN':
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('employee_dashboard'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page - GET renders form, POST authenticates."""
    user = get_current_user()
    if user:
        if user['role'] == 'ADMIN':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('employee_dashboard'))

    error = None
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        user = models.get_user_by_email(email)
        if user and verify_password(password, user['password']):
            session.permanent = True
            session['user_id'] = user['id']
            if user['role'] == 'ADMIN':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('employee_dashboard'))
        error = 'Invalid email or password.'

    return render_template('login.html', error=error)


@app.route('/logout', methods=['POST'])
def logout():
    """Clear session and redirect to login."""
    session.clear()
    return redirect(url_for('login'))


# ---------------------------------------------------------------------------
# ADMIN ROUTES
# ---------------------------------------------------------------------------

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard - stats, leaderboard, recent transactions."""
    user = get_current_user()
    now = datetime.now()
    month, year = now.month, now.year

    # Stats
    employee_count = models.get_employee_count()
    transaction_count = models.get_transaction_count()
    pending_commission = format_inr(models.get_pending_commission_total())
    pending_leaves = models.get_pending_leave_count()

    # Leaderboard: each employee's business this month vs target
    employees = models.get_all_employees()
    leaderboard = []
    for emp in employees:
        if not emp['team_type']:
            continue
        tc = TEAM_CONFIG.get(emp['team_type'], {})
        target = get_monthly_target(emp['salary'], target_multiplier=emp['target_multiplier'])
        business = models.get_employee_business_for_month(emp['id'], month, year)
        pct = get_progress_percentage(business, target)
        leaderboard.append({
            'id': emp['id'],
            'name': emp['name'],
            'team_label': tc.get('label', emp['team_type']),
            'business_done_fmt': format_inr(business),
            'target_fmt': format_inr(target),
            'percentage': pct,
            'color': get_progress_color(pct),
        })
    leaderboard.sort(key=lambda x: x['percentage'], reverse=True)

    # Recent transactions this month (up to 10)
    recent_transactions = models.get_transactions_by_month(month, year)[:10]

    return render_template('admin/dashboard.html',
        current_user=user,
        current_month_name=MONTH_NAMES[month],
        current_year=year,
        employee_count=employee_count,
        transaction_count=transaction_count,
        pending_commission=pending_commission,
        pending_leaves=pending_leaves,
        leaderboard=leaderboard,
        recent_transactions=recent_transactions,
    )


@app.route('/admin/employees')
@admin_required
def admin_employees():
    """List employees + add form."""
    user = get_current_user()
    employees_raw = models.get_all_employees()
    employees = []
    for emp in employees_raw:
        tc = TEAM_CONFIG.get(emp['team_type'], {})
        target = get_monthly_target(emp['salary'], target_multiplier=emp['target_multiplier']) if emp['team_type'] else 0
        employees.append({
            **emp,
            'team_label': tc.get('label', emp['team_type'] or '-'),
            'salary_fmt': format_inr(emp['salary']),
            'target_fmt': format_inr(target),
            'joined': emp['created_at'].strftime('%d %b %Y') if emp['created_at'] else '-',
        })

    # Check for flash messages (success/error passed via session)
    success = session.pop('emp_success', None)
    error = session.pop('emp_error', None)

    return render_template('admin/employees.html',
        current_user=user,
        employees=employees,
        success=success,
        error=error,
    )


@app.route('/admin/employees/add', methods=['POST'])
@admin_required
def admin_add_employee():
    """Create a new employee."""
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    salary_str = request.form.get('salary', '0')
    team_type = request.form.get('team_type', '')
    target_mult_str = request.form.get('target_multiplier', '').strip()
    comm_rate_str = request.form.get('commission_rate', '').strip()

    # Validation
    if not all([name, email, password, team_type]):
        session['emp_error'] = 'All fields are required.'
        return redirect(url_for('admin_employees'))

    if team_type not in TEAM_CONFIG:
        session['emp_error'] = 'Invalid team type.'
        return redirect(url_for('admin_employees'))

    try:
        salary = float(salary_str)
        target_multiplier = float(target_mult_str) if target_mult_str else TEAM_CONFIG[team_type]['multiplier']
        commission_rate = (float(comm_rate_str) / 100.0) if comm_rate_str else TEAM_CONFIG[team_type]['commission_rate']
    except ValueError:
        session['emp_error'] = 'Invalid salary or multiplier value.'
        return redirect(url_for('admin_employees'))

    # Check unique email
    existing = models.get_user_by_email(email)
    if existing:
        session['emp_error'] = f'Email "{email}" is already registered.'
        return redirect(url_for('admin_employees'))

    hashed = hash_password(password)
    models.create_user(name, email, hashed, 'EMPLOYEE', team_type, salary, target_multiplier, commission_rate)
    session['emp_success'] = f'Employee "{name}" added successfully!'
    return redirect(url_for('admin_employees'))


@app.route('/admin/transactions')
@admin_required
def admin_transactions():
    """List transactions + add form."""
    user = get_current_user()
    
    sort_by = request.args.get('sort', 'added')
    
    employees = models.get_all_employees()
    transactions = models.get_all_transactions(sort=sort_by)
    payments = models.get_transaction_payments_dict()
    import json
    payments_json = json.dumps(payments)

    success = session.pop('txn_success', None)
    error = session.pop('txn_error', None)

    return render_template('admin/transactions.html',
        current_user=user,
        employees=employees,
        transactions=transactions,
        month_names=MONTH_NAMES,
        success=success,
        error=error,
        current_sort=sort_by,
        payments_json=payments_json,
    )


@app.route('/admin/transactions/save', methods=['POST'])
@admin_required
def admin_add_transaction():
    """Create or update a transaction with calculated commission."""
    transaction_id_str = request.form.get('transaction_id', '')
    employee_id_str = request.form.get('employee_id', '')
    property_id = request.form.get('property_id', '').strip()
    property_name = request.form.get('property_name', '').strip()
    basic_price_str = request.form.get('basic_price', '0')
    transaction_date_str = request.form.get('transaction_date', '').strip()
    cs_commission_str = request.form.get('cityscope_commission', '')
    buyer_amount_str = request.form.get('buyer_commission_amount', '')
    seller_amount_str = request.form.get('seller_commission_amount', '')
    buyer_gst_applied = request.form.get('buyer_gst_applied') == '1'
    seller_gst_applied = request.form.get('seller_gst_applied') == '1'
    buyer_name = request.form.get('buyer_name', '').strip() or None
    seller_name = request.form.get('seller_name', '').strip() or None
    buyer_is_broker = request.form.get('buyer_is_broker') == '1'
    seller_is_broker = request.form.get('seller_is_broker') == '1'

    # Retrieve payment installments
    buyer_payment_amounts = request.form.getlist('buyer_payment_amounts')
    buyer_payment_dates = request.form.getlist('buyer_payment_dates')
    seller_payment_amounts = request.form.getlist('seller_payment_amounts')
    seller_payment_dates = request.form.getlist('seller_payment_dates')

    # Validation
    if not all([employee_id_str, property_id, property_name, transaction_date_str]):
        session['txn_error'] = 'All required fields must be filled.'
        return redirect(url_for('admin_transactions'))

    if not property_id.upper().startswith('CSID'):
        session['txn_error'] = 'Property ID must start with "CSID".'
        return redirect(url_for('admin_transactions'))

    try:
        employee_id = int(employee_id_str)
        cs_commission = float(cs_commission_str) if cs_commission_str else 0.0
        buyer_amount = float(buyer_amount_str) if buyer_amount_str else 0.0
        seller_amount = float(seller_amount_str) if seller_amount_str else 0.0
        basic_price = float(basic_price_str) if basic_price_str else 0.0
    except ValueError:
        session['txn_error'] = 'Invalid numeric value(s).'
        return redirect(url_for('admin_transactions'))

    employee = models.get_user_by_id(employee_id)
    if not employee or employee['role'] != 'EMPLOYEE':
        session['txn_error'] = 'Invalid employee selected.'
        return redirect(url_for('admin_transactions'))

    if not employee['team_type']:
        session['txn_error'] = 'Selected employee has no team assigned.'
        return redirect(url_for('admin_transactions'))

    # Calculate received amounts and latest dates from installments lists
    buyer_received = 0.0
    buyer_dates = []
    for amt_str, date_str in zip(buyer_payment_amounts, buyer_payment_dates):
        if amt_str:
            try:
                buyer_received += float(amt_str)
            except ValueError:
                pass
        if date_str:
            buyer_dates.append(date_str)
    buyer_date = max(buyer_dates) if buyer_dates else None

    seller_received = 0.0
    seller_dates = []
    for amt_str, date_str in zip(seller_payment_amounts, seller_payment_dates):
        if amt_str:
            try:
                seller_received += float(amt_str)
            except ValueError:
                pass
        if date_str:
            seller_dates.append(date_str)
    seller_date = max(seller_dates) if seller_dates else None
    custom_comm_rate_str = request.form.get('custom_commission_rate', '').strip()
    custom_emp_comm_str = request.form.get('custom_employee_commission', '').strip()

    # Determine effective commission rate for this deal
    effective_comm_rate = employee.get('commission_rate', 0.20)
    if custom_comm_rate_str:
        try:
            effective_comm_rate = float(custom_comm_rate_str) / 100.0
        except ValueError:
            pass

    # Calculate commission
    net_commission, calculated_emp_commission = calculate_commission(
        buyer_amount=buyer_amount,
        buyer_gst_applied=buyer_gst_applied,
        seller_amount=seller_amount,
        seller_gst_applied=seller_gst_applied,
        commission_rate=effective_comm_rate
    )

    # Use manual fixed share if provided, otherwise calculated share
    if custom_emp_comm_str:
        try:
            employee_commission = float(custom_emp_comm_str)
        except ValueError:
            employee_commission = calculated_emp_commission
    else:
        employee_commission = calculated_emp_commission

    # Date fields
    try:
        txn_date = datetime.strptime(transaction_date_str, '%Y-%m-%d')
    except ValueError:
        session['txn_error'] = 'Invalid transaction date format.'
        return redirect(url_for('admin_transactions'))

    month = txn_date.month
    year = txn_date.year
    quarter = get_quarter(month)
    fy_year = get_fy_year(month, year)

    # Calculate payment status based on received amounts
    if (buyer_received >= buyer_amount) and (seller_received >= seller_amount):
        payment_status = 'DONE'
    elif (buyer_received > 0) or (seller_received > 0):
        payment_status = 'PARTIAL'
    else:
        payment_status = 'PENDING'

    transaction_data = {
        'property_id': property_id,
        'property_name': property_name,
        'basic_price': basic_price,
        'cityscope_commission': cs_commission,
        'buyer_commission_amount': buyer_amount,
        'buyer_commission_received': buyer_received,
        'buyer_commission_date': buyer_date,
        'seller_commission_amount': seller_amount,
        'seller_commission_received': seller_received,
        'seller_commission_date': seller_date,
        'buyer_gst_applied': int(buyer_gst_applied),
        'seller_gst_applied': int(seller_gst_applied),
        'buyer_name': buyer_name,
        'seller_name': seller_name,
        'buyer_is_broker': int(buyer_is_broker),
        'seller_is_broker': int(seller_is_broker),
        'gst_applied': 0,
        'net_commission': net_commission,
        'employee_commission': employee_commission,
        'payment_status': payment_status,
        'transaction_date': transaction_date_str,
        'month': month,
        'year': year,
        'quarter': quarter,
        'employee_id': employee_id,
    }

    if transaction_id_str:
        txn_id = int(transaction_id_str)
        models.update_transaction(txn_id, transaction_data)
        models.save_transaction_payments(txn_id, 'BUYER', buyer_payment_amounts, buyer_payment_dates)
        models.save_transaction_payments(txn_id, 'SELLER', seller_payment_amounts, seller_payment_dates)
        models.recalculate_employee_quarterly_commissions(employee_id, quarter, fy_year)
        updated_txn = models.get_transaction_by_id(txn_id)
        final_comm = updated_txn['employee_commission'] if updated_txn else employee_commission
        session['txn_success'] = (
            f'Transaction for "{property_name}" updated. '
            f'Employee commission: {format_inr(final_comm)}'
        )
    else:
        txn_id = models.create_transaction(transaction_data)
        models.save_transaction_payments(txn_id, 'BUYER', buyer_payment_amounts, buyer_payment_dates)
        models.save_transaction_payments(txn_id, 'SELLER', seller_payment_amounts, seller_payment_dates)
        models.recalculate_employee_quarterly_commissions(employee_id, quarter, fy_year)
        txns = models.get_transactions_by_employee(employee_id)
        final_comm = txns[0]['employee_commission'] if txns else employee_commission
        session['txn_success'] = (
            f'Transaction for "{property_name}" added. '
            f'Employee commission: {format_inr(final_comm)}'
        )
    return redirect(url_for('admin_transactions'))


@app.route('/admin/transactions/mark-paid/<int:id>', methods=['POST'])
@admin_required
def admin_mark_paid(id):
    """Mark a transaction's payment status as DONE."""
    models.mark_transaction_paid(id)
    session['txn_success'] = 'Transaction marked as paid.'
    return redirect(url_for('admin_transactions'))


@app.route('/admin/transactions/settle/<int:id>', methods=['POST'])
@admin_required
def admin_settle_transaction(id):
    """Settle a transaction as DONE keeping the currently received partial payments."""
    models.settle_transaction(id)
    session['txn_success'] = 'Transaction forced complete (settled).'
    return redirect(url_for('admin_transactions'))


@app.route('/admin/leaves')
@admin_required
def admin_leaves():
    """Leave requests management."""
    user = get_current_user()
    pending_leaves = models.get_pending_leave_requests()
    all_leaves = models.get_all_leave_requests()

    success = session.pop('leave_success', None)

    return render_template('admin/leaves.html',
        current_user=user,
        pending_leaves=pending_leaves,
        all_leaves=all_leaves,
        success=success,
    )


@app.route('/admin/leaves/approve/<int:id>', methods=['POST'])
@admin_required
def admin_approve_leave(id):
    """Approve a leave request."""
    models.approve_leave(id)
    session['leave_success'] = 'Leave request approved.'
    return redirect(url_for('admin_leaves'))


@app.route('/admin/leaves/reject/<int:id>', methods=['POST'])
@admin_required
def admin_reject_leave(id):
    """Reject a leave request."""
    models.reject_leave(id)
    session['leave_success'] = 'Leave request rejected.'
    return redirect(url_for('admin_leaves'))


@app.route('/admin/leaves/cancel/<int:id>', methods=['POST'])
@admin_required
def admin_cancel_leave(id):
    """Cancel (delete) a leave request."""
    models.delete_leave_request(id)
    session['leave_success'] = 'Leave request cancelled successfully.'
    return redirect(url_for('admin_leaves'))



def parse_period_filters(request_args):
    """Parse month, quarter, fy_year from request arguments with smart synchronization."""
    now = datetime.now()
    current_fy = get_fy_year(now.month, now.year)

    sel_fy = request_args.get('fy_year', type=int)
    sel_q = request_args.get('quarter', type=int)
    sel_m = request_args.get('month', type=int)

    # 1. Determine FY Year
    fy_year = sel_fy if sel_fy is not None else current_fy

    # 2. Determine Month & Quarter
    if sel_m and 1 <= sel_m <= 12:
        month = sel_m
        quarter = get_quarter(month)
    elif sel_q and 1 <= sel_q <= 4:
        quarter = sel_q
        month = get_quarter_months(quarter)[0]
    else:
        if fy_year == current_fy:
            month = now.month
            quarter = get_quarter(month)
        else:
            month = 4
            quarter = 1

    year = fy_year if month >= 4 else fy_year + 1

    available_fys = []
    for fy in range(current_fy - 3, current_fy + 2):
        available_fys.append({
            'year': fy,
            'label': f"FY {fy}-{str(fy + 1)[-2:]}"
        })

    return {
        'month': month,
        'year': year,
        'quarter': quarter,
        'fy_year': fy_year,
        'available_fys': available_fys,
        'selected_fy': sel_fy,
        'selected_quarter': sel_q,
        'selected_month': sel_m,
    }


@app.route('/admin/employee/<int:id>')
@admin_required
def admin_employee_detail(id):
    """Detailed view for a specific employee with historical month/quarter/FY filter."""
    user = get_current_user()
    employees_raw = models.get_all_employees()
    employee = next((e for e in employees_raw if e['id'] == id), None)
    if not employee:
        return "Employee not found", 404

    period = parse_period_filters(request.args)
    month, year = period['month'], period['year']
    quarter, fy_year = period['quarter'], period['fy_year']

    tc = TEAM_CONFIG.get(employee['team_type'], {})
    team_label = tc.get('label', employee['team_type'] or '-')
    multiplier = employee.get('target_multiplier', 7)
    commission_rate = int(employee.get('commission_rate', 0.20) * 100)

    comm = models.get_commission_summary(id)

    m_target = get_monthly_target(employee['salary'], target_multiplier=multiplier)
    m_business = models.get_employee_business_for_month(id, month, year)
    m_pct = get_progress_percentage(m_business, m_target)
    m_remaining = max(0, m_target - m_business)

    q_target = get_quarterly_target(employee['salary'], target_multiplier=multiplier)
    q_business = models.get_employee_business_for_quarter(id, quarter, fy_year)
    q_pct = get_progress_percentage(q_business, q_target)
    q_remaining = max(0, q_target - q_business)

    q_months = {
        1: [4, 5, 6],
        2: [7, 8, 9],
        3: [10, 11, 12],
        4: [1, 2, 3]
    }[quarter]
    
    q_breakdown = []
    for m in q_months:
        y = fy_year if m >= 4 else fy_year + 1
        b_done = models.get_employee_business_for_month(id, m, y)
        q_breakdown.append({
            'month_name': MONTH_NAMES[m],
            'business': b_done,
            'target': m_target
        })

    transactions = models.get_transactions_by_employee(id)
    leaves = models.get_leaves_by_employee(id)

    # Payout, advance & FY spillover data
    payout_summary = models.get_employee_payout_summary(id)
    advances = models.get_advances_by_employee(id)
    active_advances_total = models.get_active_advances_total(id)
    fy_spillover_summary = models.get_employee_fy_spillover_summary(id, fy_year)
    today = datetime.now().strftime('%Y-%m-%d')

    success = session.pop('emp_success', None)
    error = session.pop('emp_error', None)

    return render_template('admin/employee_detail.html',
        current_user=user,
        employee=employee,
        team_label=team_label,
        multiplier=multiplier,
        commission_rate=commission_rate,
        comm=comm,
        m_target=m_target,
        m_business=m_business,
        m_pct=m_pct,
        m_remaining=m_remaining,
        q_target=q_target,
        q_business=q_business,
        q_pct=q_pct,
        q_remaining=q_remaining,
        q_breakdown=q_breakdown,
        transactions=transactions,
        leaves=leaves,
        month_name=MONTH_NAMES[month],
        year=year,
        quarter=quarter,
        fy_year=fy_year,
        fy_label=get_fy_label(month, year),
        period=period,
        MONTH_NAMES=MONTH_NAMES,
        success=success,
        error=error,
        payout_summary=payout_summary,
        advances=advances,
        active_advances_total=active_advances_total,
        fy_spillover_summary=fy_spillover_summary,
        today=today,
    )

# ---------------------------------------------------------------------------
# COMMISSION PAYOUT ROUTES
# ---------------------------------------------------------------------------

@app.route('/admin/transactions/<int:id>/pay-employee', methods=['POST'])
@admin_required
def admin_pay_employee_commission(id):
    """Mark employee commission as paid for a transaction."""
    txn = models.get_transaction_by_id(id)
    if not txn:
        session['txn_error'] = 'Transaction not found.'
        return redirect(request.referrer or url_for('admin_transactions'))

    paid_date = request.form.get('paid_date', datetime.now().strftime('%Y-%m-%d'))
    notes = request.form.get('notes', '').strip() or None
    amount = txn['employee_commission']

    models.mark_employee_commission_paid(id, txn['employee_id'], amount, paid_date, notes)
    session['emp_success'] = f'Commission {format_inr(amount)} marked as paid.'
    return redirect(request.referrer or url_for('admin_employee_detail', id=txn['employee_id']))


@app.route('/admin/transactions/<int:id>/unpay-employee', methods=['POST'])
@admin_required
def admin_unpay_employee_commission(id):
    """Revert employee commission payout for a transaction."""
    txn = models.get_transaction_by_id(id)
    if not txn:
        session['txn_error'] = 'Transaction not found.'
        return redirect(request.referrer or url_for('admin_transactions'))

    models.mark_employee_commission_unpaid(id)
    session['emp_success'] = 'Commission payout reverted to unpaid.'
    return redirect(request.referrer or url_for('admin_employee_detail', id=txn['employee_id']))


# ---------------------------------------------------------------------------
# ADVANCE ROUTES
# ---------------------------------------------------------------------------

@app.route('/admin/employee/<int:id>/advance', methods=['POST'])
@admin_required
def admin_add_advance(id):
    """Record a salary or commission advance for an employee."""
    employee = models.get_user_by_id(id)
    if not employee or employee['role'] != 'EMPLOYEE':
        session['emp_error'] = 'Invalid employee.'
        return redirect(url_for('admin_employees'))

    advance_type = request.form.get('advance_type', 'SALARY')
    amount_str = request.form.get('amount', '0')
    advance_date = request.form.get('advance_date', datetime.now().strftime('%Y-%m-%d'))
    reason = request.form.get('reason', '').strip() or None

    if advance_type not in ('SALARY', 'COMMISSION'):
        session['emp_error'] = 'Invalid advance type.'
        return redirect(url_for('admin_employee_detail', id=id))

    try:
        amount = float(amount_str)
        if amount <= 0:
            raise ValueError
    except ValueError:
        session['emp_error'] = 'Invalid amount.'
        return redirect(url_for('admin_employee_detail', id=id))

    models.create_advance(id, advance_type, amount, advance_date, reason)
    session['emp_success'] = f'{advance_type.title()} advance of {format_inr(amount)} recorded.'
    return redirect(url_for('admin_employee_detail', id=id))


@app.route('/admin/advance/<int:id>/settle', methods=['POST'])
@admin_required
def admin_settle_advance(id):
    """Settle an advance."""
    advance = models.get_advance_by_id(id)
    if not advance:
        session['emp_error'] = 'Advance not found.'
        return redirect(request.referrer or url_for('admin_dashboard'))

    models.settle_advance(id)
    session['emp_success'] = 'Advance marked as settled.'
    return redirect(url_for('admin_employee_detail', id=advance['employee_id']))


@app.route('/admin/advance/<int:id>/delete', methods=['POST'])
@admin_required
def admin_delete_advance(id):
    """Delete an advance record."""
    advance = models.get_advance_by_id(id)
    if not advance:
        session['emp_error'] = 'Advance not found.'
        return redirect(request.referrer or url_for('admin_dashboard'))

    emp_id = advance['employee_id']
    models.delete_advance(id)
    session['emp_success'] = 'Advance deleted.'
    return redirect(url_for('admin_employee_detail', id=emp_id))


# ---------------------------------------------------------------------------
# EMPLOYEE ROUTES
# ---------------------------------------------------------------------------

@app.route('/employee')
@login_required
def employee_dashboard():
    """Employee dashboard."""
    employee = get_current_user()
    if employee['role'] == 'ADMIN':
        return redirect(url_for('admin_dashboard'))

    period = parse_period_filters(request.args)
    month, year = period['month'], period['year']
    quarter, fy_year = period['quarter'], period['fy_year']

    multiplier = employee['target_multiplier']

    # Commission summary
    comm = models.get_commission_summary(employee['id'])

    # Payout & advance data
    payout_summary = models.get_employee_payout_summary(employee['id'])
    advances = models.get_advances_by_employee(employee['id'])
    active_advances_total = models.get_active_advances_total(employee['id'])

    # Monthly target
    m_target = get_monthly_target(employee['salary'], target_multiplier=multiplier)
    m_business = models.get_employee_business_for_month(employee['id'], month, year)
    m_pct = get_progress_percentage(m_business, m_target)
    m_remaining = max(0, m_target - m_business)

    # Quarterly target
    q_target = get_quarterly_target(employee['salary'], target_multiplier=multiplier)
    q_business = models.get_employee_business_for_quarter(
        employee['id'], quarter, fy_year
    )
    q_pct = get_progress_percentage(q_business, q_target)
    q_remaining = max(0, q_target - q_business)

    # Transactions
    transactions = models.get_transactions_by_employee(employee['id'])

    return render_template('employee/dashboard.html',
        employee=employee,
        salary_fmt=format_inr(employee['salary']),
        pending_commission=format_inr(comm['pending']),
        received_commission=format_inr(comm['received']),
        current_month_name=MONTH_NAMES[month],
        current_year=year,
        current_quarter=quarter,
        fy_label=get_fy_label(month, year),
        monthly_business_fmt=format_inr(m_business),
        monthly_target_fmt=format_inr(m_target),
        monthly_pct=m_pct,
        monthly_color=get_progress_color(m_pct),
        monthly_remaining=format_inr(m_remaining),
        quarterly_business_fmt=format_inr(q_business),
        quarterly_target_fmt=format_inr(q_target),
        quarterly_pct=q_pct,
        quarterly_color=get_progress_color(q_pct),
        quarterly_remaining=format_inr(q_remaining),
        transactions=transactions,
        month_names=MONTH_NAMES,
        payout_summary=payout_summary,
        advances=advances,
        active_advances_total=active_advances_total,
        period=period,
        fy_year=fy_year,
    )


@app.route('/employee/leaves')
@login_required
def employee_leaves():
    """Employee leaves page."""
    employee = get_current_user()
    if employee['role'] == 'ADMIN':
        return redirect(url_for('admin_dashboard'))

    now = datetime.now()
    leave_requests = models.get_leaves_by_employee(employee['id'], limit=30)
    leave_success = session.pop('leave_success_emp', None)
    leave_error = session.pop('leave_error_emp', None)
    min_leave_date = (now.date() + timedelta(days=3)).strftime('%Y-%m-%d')
    today = now.strftime('%Y-%m-%d')

    return render_template('employee/leaves.html',
        employee=employee,
        leave_requests=leave_requests,
        leave_success=leave_success,
        leave_error=leave_error,
        tomorrow=min_leave_date,
        today=today,
    )


@app.route('/employee/leave/apply', methods=['POST'])
@login_required
def employee_apply_leave():
    """Apply for leave - enforces 3-day deadline rule (by 11:59 PM, 3 days prior)."""
    employee = get_current_user()
    if employee['role'] == 'ADMIN':
        return redirect(url_for('admin_dashboard'))

    date_str = request.form.get('date_of_leave', '').strip()
    reason = request.form.get('reason', '').strip() or None

    if not date_str:
        session['leave_error_emp'] = 'Date of leave is required.'
        return redirect(url_for('employee_leaves'))

    try:
        leave_date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        session['leave_error_emp'] = 'Invalid date format.'
        return redirect(url_for('employee_leaves'))

    now = datetime.now()

    # Deadline is 3 days prior to leave date at 11:59:59 PM
    # e.g., Leave on Thursday (Sep 4) -> Deadline is Monday (Sep 1) 11:59:59 PM
    deadline_date = leave_date_obj - timedelta(days=3)
    deadline_dt = datetime.combine(deadline_date, time(23, 59, 59))

    if now > deadline_dt:
        deadline_formatted = deadline_date.strftime('%A, %d %b %Y')
        leave_formatted = leave_date_obj.strftime('%A, %d %b %Y')
        session['leave_error_emp'] = f'Leave for {leave_formatted} had to be applied by {deadline_formatted} 11:59 PM.'
        models.create_leave_request(
            employee_id=employee['id'],
            date_of_leave=date_str,
            reason=reason,
            blocked=True,
            status='REJECTED'
        )
        return redirect(url_for('employee_leaves'))

    models.create_leave_request(
        employee_id=employee['id'],
        date_of_leave=date_str,
        reason=reason,
        blocked=False,
        status='APPROVED'
    )
    session['leave_success_emp'] = 'Leave request submitted and auto-approved!'
    return redirect(url_for('employee_leaves'))


@app.route('/employee/leave/cancel/<int:id>', methods=['POST'])
@login_required
def employee_cancel_leave(id):
    """Cancel a leave request if it belongs to the employee."""
    employee = get_current_user()
    if employee['role'] == 'ADMIN':
        return redirect(url_for('admin_dashboard'))

    # Basic security check: ensure the leave belongs to the current employee
    leaves = models.get_leaves_by_employee(employee['id'], limit=100)
    target_leave = next((l for l in leaves if l['id'] == id), None)

    if not target_leave:
        session['leave_error_emp'] = 'Leave request not found or access denied.'
        return redirect(url_for('employee_leaves'))

    # Only allow canceling APPROVED leaves
    if target_leave['status'] != 'APPROVED':
        session['leave_error_emp'] = 'Only approved leaves can be cancelled.'
        return redirect(url_for('employee_leaves'))

    # Optional: only allow canceling future leaves
    if target_leave['date_of_leave'] < datetime.now().date():
        session['leave_error_emp'] = 'Cannot cancel past leave requests.'
        return redirect(url_for('employee_leaves'))

    models.delete_leave_request(id)
    session['leave_success_emp'] = 'Leave request cancelled successfully.'
    return redirect(url_for('employee_leaves'))


@app.route('/employee/leaderboard')
@login_required
def employee_leaderboard():
    """Employee leaderboard page."""
    employee = get_current_user()
    if employee['role'] == 'ADMIN':
        return redirect(url_for('admin_dashboard'))

    now = datetime.now()
    month, year = now.month, now.year
    quarter = get_quarter(month)
    fy_year = get_fy_year(month, year)

    all_employees = models.get_all_employees()
    leaderboard_monthly = []
    leaderboard_quarterly = []

    for emp in all_employees:
        if not emp['team_type']:
            continue
        
        m_target = get_monthly_target(emp['salary'], target_multiplier=emp['target_multiplier'])
        m_business = models.get_employee_business_for_month(emp['id'], month, year)
        m_pct = get_progress_percentage(m_business, m_target)
        leaderboard_monthly.append({
            'id': emp['id'],
            'name': emp['name'],
            'percentage': m_pct,
            'color': get_progress_color(m_pct),
        })

        q_target = get_quarterly_target(emp['salary'], target_multiplier=emp['target_multiplier'])
        q_business = models.get_employee_business_for_quarter(emp['id'], quarter, fy_year)
        q_pct = get_progress_percentage(q_business, q_target)
        leaderboard_quarterly.append({
            'id': emp['id'],
            'name': emp['name'],
            'percentage': q_pct,
            'color': get_progress_color(q_pct),
        })

    leaderboard_monthly.sort(key=lambda x: x['percentage'], reverse=True)
    leaderboard_quarterly.sort(key=lambda x: x['percentage'], reverse=True)

    return render_template('employee/leaderboard.html',
        employee=employee,
        current_month_name=MONTH_NAMES[month],
        current_year=year,
        current_quarter=quarter,
        leaderboard_monthly=leaderboard_monthly,
        leaderboard_quarterly=leaderboard_quarterly,
    )


@app.route('/admin/leaderboard')
@admin_required
def admin_leaderboard():
    """Admin dedicated leaderboard page."""
    user = get_current_user()
    now = datetime.now()
    month, year = now.month, now.year
    quarter = get_quarter(month)
    fy_year = get_fy_year(month, year)

    employees = models.get_all_employees()
    leaderboard_monthly = []
    leaderboard_quarterly = []

    for emp in employees:
        if not emp['team_type']:
            continue
        tc = TEAM_CONFIG.get(emp['team_type'], {})
        
        m_target = get_monthly_target(emp['salary'], target_multiplier=emp['target_multiplier'])
        m_business = models.get_employee_business_for_month(emp['id'], month, year)
        m_pct = get_progress_percentage(m_business, m_target)
        leaderboard_monthly.append({
            'id': emp['id'],
            'name': emp['name'],
            'team_label': tc.get('label', emp['team_type']),
            'business_done': m_business,
            'target': m_target,
            'percentage': m_pct,
            'color': get_progress_color(m_pct),
        })

        q_target = get_quarterly_target(emp['salary'], target_multiplier=emp['target_multiplier'])
        q_business = models.get_employee_business_for_quarter(emp['id'], quarter, fy_year)
        q_pct = get_progress_percentage(q_business, q_target)
        leaderboard_quarterly.append({
            'id': emp['id'],
            'name': emp['name'],
            'team_label': tc.get('label', emp['team_type']),
            'business_done': q_business,
            'target': q_target,
            'percentage': q_pct,
            'color': get_progress_color(q_pct),
        })

    leaderboard_monthly.sort(key=lambda x: x['percentage'], reverse=True)
    leaderboard_quarterly.sort(key=lambda x: x['percentage'], reverse=True)

    return render_template('admin/leaderboard.html',
        current_user=user,
        current_month_name=MONTH_NAMES[month],
        current_year=year,
        current_quarter=quarter,
        leaderboard_monthly=leaderboard_monthly,
        leaderboard_quarterly=leaderboard_quarterly,
    )


@app.route('/admin/employee/<int:id>/update', methods=['POST'])
@admin_required
def admin_update_employee(id):
    """Update employee settings (salary, target multiplier, commission rate)."""
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    salary_str = request.form.get('salary', '0')
    team_type = request.form.get('team_type', '')
    target_multiplier_str = request.form.get('target_multiplier', '7.0')
    commission_rate_str = request.form.get('commission_rate', '20.0')
    new_password = request.form.get('new_password', '').strip()

    # Get optional error flash location
    success_redirect = request.form.get('success_redirect', '')

    if not all([name, email, team_type]):
        session['emp_error'] = 'Name, email and team type are required.'
        return redirect(url_for('admin_employee_detail', id=id))

    try:
        salary = float(salary_str)
        target_multiplier = float(target_multiplier_str)
        commission_rate = float(commission_rate_str) / 100.0
    except ValueError:
        session['emp_error'] = 'Invalid numeric value(s).'
        return redirect(url_for('admin_employee_detail', id=id))

    # Check if email exists for another user
    existing = models.get_user_by_email(email)
    if existing and existing['id'] != id:
        session['emp_error'] = f'Email "{email}" is already in use by another user.'
        return redirect(url_for('admin_employee_detail', id=id))

    data = {
        'name': name,
        'email': email,
        'salary': salary,
        'team_type': team_type,
        'target_multiplier': target_multiplier,
        'commission_rate': commission_rate
    }
    
    if new_password:
        data['password_hash'] = hash_password(new_password)

    models.update_user(id, data)
    
    # Recalculate quarterly commissions since details changed
    now = datetime.now()
    quarter = get_quarter(now.month)
    fy_year = get_fy_year(now.month, now.year)
    models.recalculate_employee_quarterly_commissions(id, quarter, fy_year)

    session['emp_success'] = 'Employee details updated successfully!'
    return redirect(url_for('admin_employee_detail', id=id))


@app.route('/admin/employee/<int:id>/delete', methods=['POST'])
@admin_required
def admin_delete_employee(id):
    """Delete an employee and all their associated records."""
    employee = models.get_user_by_id(id)
    if not employee or employee['role'] == 'ADMIN':
        session['emp_error'] = 'Cannot delete admin or non-existent user.'
        return redirect(url_for('admin_employees'))
        
    models.delete_user(id)
    session['emp_success'] = f'Employee {employee["name"]} deleted successfully.'
    return redirect(url_for('admin_employees'))


@app.route('/admin/transactions/<int:id>/delete', methods=['POST'])
@admin_required
def admin_delete_transaction(id):
    """Delete a transaction."""
    txn = models.get_transaction_by_id(id)
    if txn:
        models.delete_transaction(id)
        fy_year = get_fy_year(txn['month'], txn['year'])
        models.recalculate_employee_quarterly_commissions(txn['employee_id'], txn['quarter'], fy_year)
        session['txn_success'] = 'Transaction deleted successfully.'
    else:
        session['txn_error'] = 'Transaction not found.'
    return redirect(url_for('admin_transactions'))

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

