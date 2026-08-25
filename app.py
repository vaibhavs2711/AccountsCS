"""
Cityscope Accounts & Commission System
Main Flask Application — All routes and configuration.
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
# Jinja2 globals / filters — available in every template
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
    """Login page — GET renders form, POST authenticates."""
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
    """Admin dashboard — stats, leaderboard, recent transactions."""
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
        target = get_monthly_target(emp['salary'], emp['team_type'])
        business = models.get_employee_business_for_month(emp['id'], month, year)
        pct = get_progress_percentage(business, target)
        leaderboard.append({
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
        target = get_monthly_target(emp['salary'], emp['team_type']) if emp['team_type'] else 0
        employees.append({
            **emp,
            'team_label': tc.get('label', emp['team_type'] or '—'),
            'salary_fmt': format_inr(emp['salary']),
            'target_fmt': format_inr(target),
            'joined': emp['created_at'].strftime('%d %b %Y') if emp['created_at'] else '—',
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

    # Validation
    if not all([name, email, password, team_type]):
        session['emp_error'] = 'All fields are required.'
        return redirect(url_for('admin_employees'))

    if team_type not in TEAM_CONFIG:
        session['emp_error'] = 'Invalid team type.'
        return redirect(url_for('admin_employees'))

    try:
        salary = float(salary_str)
    except ValueError:
        session['emp_error'] = 'Invalid salary value.'
        return redirect(url_for('admin_employees'))

    # Check unique email
    existing = models.get_user_by_email(email)
    if existing:
        session['emp_error'] = f'Email "{email}" is already registered.'
        return redirect(url_for('admin_employees'))

    hashed = hash_password(password)
    models.create_user(name, email, hashed, 'EMPLOYEE', team_type, salary)
    session['emp_success'] = f'Employee "{name}" added successfully!'
    return redirect(url_for('admin_employees'))


@app.route('/admin/transactions')
@admin_required
def admin_transactions():
    """List transactions + add form."""
    user = get_current_user()
    employees = models.get_all_employees()
    transactions = models.get_all_transactions()

    success = session.pop('txn_success', None)
    error = session.pop('txn_error', None)

    return render_template('admin/transactions.html',
        current_user=user,
        employees=employees,
        transactions=transactions,
        month_names=MONTH_NAMES,
        success=success,
        error=error,
    )


@app.route('/admin/transactions/add', methods=['POST'])
@admin_required
def admin_add_transaction():
    """Create a new transaction with calculated commission."""
    employee_id_str = request.form.get('employee_id', '')
    property_id = request.form.get('property_id', '').strip()
    property_name = request.form.get('property_name', '').strip()
    total_deal_str = request.form.get('total_deal_amount', '0')
    cs_commission_str = request.form.get('cityscope_commission', '0')
    buyer_pct_str = request.form.get('buyer_commission_percent', '0')
    seller_pct_str = request.form.get('seller_commission_percent', '0')
    gst_applied = request.form.get('gst_applied') == '1'

    # Validation
    if not all([employee_id_str, property_id, property_name]):
        session['txn_error'] = 'All required fields must be filled.'
        return redirect(url_for('admin_transactions'))

    if not property_id.upper().startswith('CSID'):
        session['txn_error'] = 'Property ID must start with "CSID".'
        return redirect(url_for('admin_transactions'))

    try:
        employee_id = int(employee_id_str)
        total_deal = float(total_deal_str)
        cs_commission = float(cs_commission_str)
        buyer_pct = float(buyer_pct_str)
        seller_pct = float(seller_pct_str)
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

    # Calculate commission
    net_commission, employee_commission = calculate_commission(
        cs_commission, gst_applied, employee['team_type']
    )

    # Date fields
    now = datetime.now()
    month = now.month
    year = now.year
    quarter = get_quarter(month)

    models.create_transaction({
        'property_id': property_id,
        'property_name': property_name,
        'total_deal_amount': total_deal,
        'cityscope_commission': cs_commission,
        'buyer_commission_percent': buyer_pct,
        'seller_commission_percent': seller_pct,
        'gst_applied': int(gst_applied),
        'net_commission': net_commission,
        'employee_commission': employee_commission,
        'month': month,
        'year': year,
        'quarter': quarter,
        'employee_id': employee_id,
    })

    session['txn_success'] = (
        f'Transaction for "{property_name}" added. '
        f'Employee commission: {format_inr(employee_commission)}'
    )
    return redirect(url_for('admin_transactions'))


@app.route('/admin/transactions/mark-paid/<int:id>', methods=['POST'])
@admin_required
def admin_mark_paid(id):
    """Mark a transaction's payment status as DONE."""
    models.mark_transaction_paid(id)
    session['txn_success'] = 'Transaction marked as paid.'
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


# ---------------------------------------------------------------------------
# EMPLOYEE ROUTES
# ---------------------------------------------------------------------------

@app.route('/employee')
@login_required
def employee_dashboard():
    """Employee dashboard — single-page with all sections."""
    employee = get_current_user()
    if employee['role'] == 'ADMIN':
        return redirect(url_for('admin_dashboard'))

    now = datetime.now()
    month, year = now.month, now.year
    quarter = get_quarter(month)
    fy_year = get_fy_year(month, year)

    tc = TEAM_CONFIG.get(employee['team_type'], {})
    team_label = tc.get('label', employee['team_type'] or '—')
    multiplier = tc.get('multiplier', 7)
    commission_rate = int(tc.get('commission_rate', 0.20) * 100)

    # Commission summary
    comm = models.get_commission_summary(employee['id'])

    # Monthly target
    m_target = get_monthly_target(employee['salary'], employee['team_type'])
    m_business = models.get_employee_business_for_month(employee['id'], month, year)
    m_pct = get_progress_percentage(m_business, m_target)
    m_remaining = max(0, m_target - m_business)

    # Quarterly target
    q_target = get_quarterly_target(employee['salary'], employee['team_type'])
    q_business = models.get_employee_business_for_quarter(
        employee['id'], quarter, fy_year
    )
    q_pct = get_progress_percentage(q_business, q_target)
    q_remaining = max(0, q_target - q_business)

    # Leaderboard (all employees, ranked by monthly progress)
    all_employees = models.get_all_employees()
    leaderboard = []
    for emp in all_employees:
        if not emp['team_type']:
            continue
        emp_target = get_monthly_target(emp['salary'], emp['team_type'])
        emp_business = models.get_employee_business_for_month(emp['id'], month, year)
        emp_pct = get_progress_percentage(emp_business, emp_target)
        leaderboard.append({
            'id': emp['id'],
            'name': emp['name'],
            'percentage': emp_pct,
            'color': get_progress_color(emp_pct),
        })
    leaderboard.sort(key=lambda x: x['percentage'], reverse=True)

    # Transactions
    transactions = models.get_transactions_by_employee(employee['id'])

    # Leave requests
    leave_requests = models.get_leaves_by_employee(employee['id'], limit=10)

    # Flash messages for leave form
    leave_success = session.pop('leave_success_emp', None)
    leave_error = session.pop('leave_error_emp', None)

    # Tomorrow date for date picker min
    tomorrow = (now + timedelta(days=1)).strftime('%Y-%m-%d')

    return render_template('employee/dashboard.html',
        employee=employee,
        team_label=team_label,
        salary_fmt=format_inr(employee['salary']),
        multiplier=multiplier,
        commission_rate=commission_rate,
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
        leaderboard=leaderboard,
        transactions=transactions,
        month_names=MONTH_NAMES,
        leave_requests=leave_requests,
        leave_success=leave_success,
        leave_error=leave_error,
        tomorrow=tomorrow,
    )


@app.route('/employee/leave/apply', methods=['POST'])
@login_required
def employee_apply_leave():
    """Apply for leave — enforces 72-hour rule."""
    employee = get_current_user()
    if employee['role'] == 'ADMIN':
        return redirect(url_for('admin_dashboard'))

    date_str = request.form.get('date_of_leave', '').strip()
    reason = request.form.get('reason', '').strip() or None

    if not date_str:
        session['leave_error_emp'] = 'Date of leave is required.'
        return redirect(url_for('employee_dashboard'))

    try:
        leave_date = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        session['leave_error_emp'] = 'Invalid date format.'
        return redirect(url_for('employee_dashboard'))

    now = datetime.now()
    hours_diff = (leave_date - now).total_seconds() / 3600

    if hours_diff < 72:
        # Block: within 72 hours
        session['leave_error_emp'] = 'Leave requests must be submitted at least 72 hours in advance.'
        # Still save it as blocked/rejected
        models.create_leave_request(
            employee_id=employee['id'],
            date_of_leave=date_str,
            reason=reason,
            blocked=True,
        )
        return redirect(url_for('employee_dashboard'))

    models.create_leave_request(
        employee_id=employee['id'],
        date_of_leave=date_str,
        reason=reason,
        blocked=False,
    )
    session['leave_success_emp'] = 'Leave request submitted successfully!'
    return redirect(url_for('employee_dashboard'))


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
