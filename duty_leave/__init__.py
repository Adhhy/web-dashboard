"""
Duty Leave Module - Flask Blueprints
Registers two blueprints: one for page views, one for API actions.
"""
from flask import Blueprint

# Blueprint for page views (HTML pages)
duty_leave_views = Blueprint('duty_leave_views', __name__)

# Blueprint for API actions (JSON responses)
duty_leave_api = Blueprint('duty_leave_api', __name__)

# Import routes to register them with the blueprints
from duty_leave import view_routes  # noqa
from duty_leave import api_routes   # noqa
