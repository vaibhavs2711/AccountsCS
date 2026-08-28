"""
Cityscope Accounts — Business Logic
Indian FY calendar, commission calculations, currency formatting, progress colors.
"""

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MONTH_NAMES = [
    '', 'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
]

# Team configuration: multiplier for target, commission rate for employee share
TEAM_CONFIG = {
    'CORE_TEAM':   {'multiplier': 10, 'commission_rate': 0.30, 'label': 'Core Team'},
    'NORMAL_TEAM': {'multiplier': 7,  'commission_rate': 0.20, 'label': 'Normal Team'},
    'RENT_TEAM':   {'multiplier': 5,  'commission_rate': 0.20, 'label': 'Rent Team'},
}

GST_RATE = 0.06  # 6%

# Progress colour thresholds
PROGRESS_COLORS = [
    (70, '#27ae60'),   # Green  — 70%+
    (50, '#d4ac0d'),   # Amber  — 50-69%
    (30, '#c0392b'),   # Red    — 30-49%
    (0,  '#888888'),   # Grey   — 0-29%
]


# ---------------------------------------------------------------------------
# Indian Financial Year helpers
# ---------------------------------------------------------------------------

def get_quarter(month: int) -> int:
    """Return Indian FY quarter (1-4) for a calendar month (1-12).

    Q1: Apr-Jun, Q2: Jul-Sep, Q3: Oct-Dec, Q4: Jan-Mar
    """
    mapping = {
        4: 1, 5: 1, 6: 1,
        7: 2, 8: 2, 9: 2,
        10: 3, 11: 3, 12: 3,
        1: 4, 2: 4, 3: 4,
    }
    return mapping.get(month, 1)


def get_fy_year(month: int, year: int) -> int:
    """Return the starting year of the Indian FY.

    If month >= April → FY starts this year.
    If month < April  → FY started previous year.
    """
    return year if month >= 4 else year - 1


def get_fy_label(month: int, year: int) -> str:
    """Return a display label like 'FY 2025-26'."""
    fy = get_fy_year(month, year)
    return f"FY {fy}-{str(fy + 1)[-2:]}"


def get_quarter_months(quarter: int) -> list:
    """Return the three calendar months that belong to a given Indian FY quarter."""
    mapping = {
        1: [4, 5, 6],
        2: [7, 8, 9],
        3: [10, 11, 12],
        4: [1, 2, 3],
    }
    return mapping.get(quarter, [])


# ---------------------------------------------------------------------------
# Commission calculation
# ---------------------------------------------------------------------------

def calculate_commission(cityscope_commission: float, gst_applied: bool, team_type: str = None, commission_rate: float = None, factor: float = 1.0):
    """Calculate net commission and employee share.

    Returns (net_commission, employee_commission).
    """
    if gst_applied:
        net_commission = cityscope_commission * (1 - GST_RATE)
    else:
        net_commission = cityscope_commission

    if commission_rate is not None:
        rate = commission_rate
    else:
        rate = TEAM_CONFIG.get(team_type, {}).get('commission_rate', 0.20) if team_type else 0.20

    employee_commission = net_commission * rate * factor
    return round(net_commission, 2), round(employee_commission, 2)


# ---------------------------------------------------------------------------
# Target helpers
# ---------------------------------------------------------------------------

def get_monthly_target(salary: float, team_type: str = None, target_multiplier: float = None) -> float:
    """Monthly target = salary × multiplier."""
    if target_multiplier is not None:
        multiplier = target_multiplier
    else:
        multiplier = TEAM_CONFIG.get(team_type, {}).get('multiplier', 7) if team_type else 7.0
    return salary * multiplier


def get_quarterly_target(salary: float, team_type: str = None, target_multiplier: float = None) -> float:
    """Quarterly target = salary × multiplier × 3."""
    return get_monthly_target(salary, team_type, target_multiplier) * 3


# ---------------------------------------------------------------------------
# Currency formatting (Indian numbering system)
# ---------------------------------------------------------------------------

def format_inr(amount) -> str:
    """Format a number as Indian Rupees: ₹X,XX,XXX.

    Uses the Indian grouping system (last 3 digits, then groups of 2).
    """
    if amount is None:
        return '₹0'
    amount = float(amount)
    if amount < 0:
        return '-₹' + format_inr(-amount)[1:]
    s = str(int(round(amount)))
    if len(s) <= 3:
        return '₹' + s
    last3 = s[-3:]
    rest = s[:-3]
    groups = []
    while rest:
        groups.insert(0, rest[-2:])
        rest = rest[:-2]
    return '₹' + ','.join(groups) + ',' + last3


# ---------------------------------------------------------------------------
# Progress helpers
# ---------------------------------------------------------------------------

def get_progress_color(percentage: float) -> str:
    """Return hex colour based on progress percentage thresholds."""
    for threshold, colour in PROGRESS_COLORS:
        if percentage >= threshold:
            return colour
    return '#888888'


def get_progress_percentage(business_done: float, target: float) -> float:
    """Calculate progress as a percentage, capped display at 100 for the bar but raw for text."""
    if target <= 0:
        return 0.0
    return round((business_done / target) * 100, 1)
