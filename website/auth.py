from flask import (
    Blueprint, jsonify, render_template, request, flash, redirect, session,
    url_for, send_file, Response, make_response
)

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


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        # remember = True if request.form.get('remember') else False

        if email and password:
            user = User.query.filter(func.lower(User.email) == func.lower(email)).first()
            if user and check_password_hash(user.password, password):
                login_user(user)
                flash('Авторизация прошла успешно.', 'success')
                return redirect(url_for('views.profile'))
            else:
                flash('Неправильный email или пароль.', 'error')
        else:
            flash('Введите данные для авторизации.', 'error')

        return render_template(
            'login.html',
            hide_header=True,
            hide_circle_buttons=True,
            current_user=current_user
        )
        
    return render_template(
        'login.html',
        hide_header=True,
        hide_circle_buttons=True,
        current_user=current_user
    )

@auth.route('/sign', methods=['POST', 'GET'])
def sign():
    if request.method == 'GET':
        return render_template('sign.html', 
                        hide_header=True,
                        hide_circle_buttons = True,
                            )

@auth.route('/kod', methods=['POST', 'GET'])
def kod():
    if request.method == 'GET':
        return render_template('kod.html', 
                        hide_header=True,
                        hide_circle_buttons = True,
                            )

@auth.route('/param', methods=['POST'])
def param():
    if request.method == 'GET':
        return render_template('param.html', 
                        hide_header=True,
                        hide_circle_buttons = True,
                            )
    
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