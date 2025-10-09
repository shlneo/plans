from functools import wraps
from flask import (
    Blueprint, jsonify, render_template, request, flash, redirect, session,
    url_for, send_file, Response, make_response
)

import re

from flask_login import (
    login_user, logout_user, current_user,
    login_required, LoginManager
)

from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash

from .models import User, Organization, Plan, Ticket, Unit, Direction, Indicator, EconMeasure, EconExec, IndicatorUsage, current_utc_time
from . import db

auth = Blueprint('auth', __name__)
login_manager = LoginManager()

def user_without_param():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Необходима авторизация.", "error")
                return redirect(url_for('auth.login'))

            has_missing = (
                not current_user.last_name or
                not current_user.first_name or
                not current_user.patronymic_name or
                not current_user.phone or
                not current_user.organization_id
            )

            if not has_missing:
                # flash("Доступ запрещён — все данные уже заполнены.", "error")
                return redirect(url_for('auth.profile'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def user_with_all_params():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Необходима авторизация.", "error")
                return redirect(url_for('auth.login'))
            all_filled = (
                current_user.last_name and
                current_user.first_name and
                current_user.phone and
                current_user.organization_id
            )
            if not all_filled:
                flash("Заполните недостающие данные.", "error")
                return redirect(url_for('auth.param'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if email and password:
            user = User.query.filter(func.lower(User.email) == func.lower(email)).first()
            if user and check_password_hash(user.password, password):
                login_user(user)
                if (
                    not user.last_name or
                    not user.first_name or
                    not user.phone or
                    not user.organization_id
                ):  
                    flash("Необходимо заполнить обязательные парамметры.", "error")
                    return redirect(url_for('auth.param'))
                flash('Авторизация прошла успешно.', 'success')
                return redirect(url_for('views.profile'))
            else:
                flash('Неправильный email или пароль.', 'error')
        else:
            flash('Введите данные для авторизации.', 'error')
        return render_template(
            'login.html',
            hide_header=True,
            show_circle_buttons=True,
            current_user=current_user
        )

    return render_template(
        'login.html',
        hide_header=True,
        show_circle_buttons=True,
        current_user=current_user
    )

@auth.route('/sign', methods=['POST', 'GET'])
def sign():
    if request.method == 'GET':
        return render_template('sign.html', 
                               hide_header=True,
                               show_circle_buttons=True)
    elif request.method == 'POST':
        email = request.form.get('email')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        
        from .user.account import sign_def
        return sign_def(email, password1, password2)

@auth.route('/code', methods=['POST', 'GET'])
def code():
    if request.method == 'GET':
        return render_template('code.html', 
                        hide_header=True,
                        show_circle_buttons = True,
                            )
    elif request.method == 'POST':
        from .user.account import activate_account
    return activate_account()

@auth.route('/param', methods=['GET', 'POST'])
@login_required
@user_without_param()
def param():
    if request.method == 'GET':
        return render_template('param.html', 
                        hide_header=True,
                        show_circle_buttons = True,
                            )
    elif request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        patronymic_name = request.form.get('patronymic_name')
        phone = request.form.get('phone')
        post = request.form.get('post')
        organization_id = request.form.get('organization_id')

        from .user.account import add_param
        return add_param(first_name, last_name, patronymic_name, phone, organization_id, post)
   
    
@auth.route('/edit-param', methods=['POST'])
def edit_param():
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    patronymic_name = request.form.get('patronymic_name')
    phone = request.form.get('phone')
    post = request.form.get('post')

    current_user.first_name = first_name
    current_user.last_name = last_name
    current_user.patronymic_name = patronymic_name
    current_user.phone = phone
    current_user.post = post
    db.session.commit()

    flash('Изменения внесены!', 'success')
    return redirect(request.referrer or url_for('views.profile'))

@auth.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    
    flash('Выполнен выход из аккаунта.', 'success')
    return redirect(url_for('auth.login'))