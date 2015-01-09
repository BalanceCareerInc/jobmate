# -*-coding:utf8-*-
from flask import Blueprint, render_template
from models import User

bp = Blueprint('admin', __name__)


@bp.route('/')
def index():
    return render_template('admin/index.html')


@bp.route('/member')
def manage_members():
    users = User.scan()
    return render_template('admin/members.html', users=users)
