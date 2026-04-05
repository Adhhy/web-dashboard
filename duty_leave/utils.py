"""
Duty Leave Module - Utility Functions
Handles deadline checking, state display mapping, and badge CSS classes.
"""
from datetime import datetime, date


def is_past_deadline(created_at_str: str) -> bool:
    """
    Returns True if the request was created on a previous day (past midnight).
    'created_at' is stored as 'YYYY-MM-DD HH:MM:SS' in SQLite.
    """
    try:
        if isinstance(created_at_str, str):
            created_dt = datetime.strptime(created_at_str, '%Y-%m-%d %H:%M:%S')
        else:
            created_dt = created_at_str
        return created_dt.date() < date.today()
    except Exception:
        return False


def get_state_display(state: str) -> str:
    """Returns a human-readable label for a duty leave state."""
    mapping = {
        'PendingAdvisor':  'Awaiting Advisor Approval',
        'PendingFaculty':  'Awaiting Faculty Approval',
        'Approved':        'Approved',
        'Rejected':        'Rejected',
        'Locked':          'Locked (Pending Admin)',
        'Completed':       'Completed',
    }
    return mapping.get(state, state)


def get_state_badge_class(state: str) -> str:
    """Returns a CSS class suffix for the status pill."""
    mapping = {
        'PendingAdvisor': 'waiting',
        'PendingFaculty': 'waiting',
        'Approved':       'approved',
        'Rejected':       'rejected',
        'Locked':         'locked',
        'Completed':      'approved',
    }
    return mapping.get(state, 'waiting')


def format_periods(periods_str: str) -> str:
    """Convert comma-separated period numbers to display string like 'P1, P3, P5'."""
    if not periods_str:
        return ''
    parts = [p.strip() for p in periods_str.split(',')]
    return ', '.join(f'P{p}' if not p.startswith('P') else p for p in parts)


def today_str() -> str:
    """Returns today's date as 'YYYY-MM-DD'."""
    return date.today().isoformat()
