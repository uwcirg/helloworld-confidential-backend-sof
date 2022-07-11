import time
from flask import Blueprint, Flask

base_blueprint = Blueprint('base', __name__)

@base_blueprint.route('/time')
def get_current_time():
    return {"time": time.time()}
