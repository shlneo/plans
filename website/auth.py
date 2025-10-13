from functools import wraps
from flask import (
    Blueprint, current_app, jsonify, render_template, request, flash, redirect, session,
    url_for, send_file, Response, make_response
)

import re

from flask_login import (
    login_user, logout_user, current_user,
    login_required, LoginManager
)

from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash

from website.user.account import mes_on_email

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

@auth.route('/resend-code', methods=['POST'])
def resend_code():
    from .user.account import gener_password, send_activation_email
    try:
        session.pop('activation_code', None)
        
        new_code = gener_password()
        session['activation_code'] = new_code
        
        email = session.get('temp_user', {}).get('email')
        if email:
            send_activation_email(email)
            flash('Новый код подтверждения отправлен на вашу почту.', 'success')
        else:
            flash('Ошибка: email не найден', 'error')
    
    except Exception as e:
        flash(f'Ошибка при отправке кода: {str(e)}', 'error')
    
    return redirect(url_for('auth.code'))

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


from itsdangerous import URLSafeTimedSerializer
from datetime import datetime, timedelta

@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'GET':
        return render_template('forgot_password.html', 
                            hide_header=True,
                            show_circle_buttons=True)
    
    elif request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
            token = serializer.dumps(email, salt='password-reset-salt')

            user.reset_password_token = token
            user.reset_password_expires = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()
            
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            
            mes_on_email(reset_url, email, 'reset_link')
     
        flash('Если email зарегистрирован, на него будет отправлена ссылка для сброса пароля.', 'success')
        return redirect(url_for('auth.forgot_password'))
    
@auth.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if request.method == 'GET':
        user = User.query.filter_by(reset_password_token=token).first()
        
        if not user:
            flash('Ссылка для сброса пароля недействительна.', 'error')
            return redirect(url_for('auth.forgot_password'))
        
        if user.reset_password_expires < datetime.utcnow():
            flash('Ссылка для сброса пароля устарела. Запросите новую.', 'error')
            return redirect(url_for('auth.forgot_password'))
        
        return render_template('reset_password.html', 
                            token=token,
                            hide_header=True,
                            show_circle_buttons=True)
    
    elif request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('password1')
        token_from_form = request.form.get('token')
        
        if token != token_from_form:
            flash('Неверный токен сброса пароля.', 'error')
            return redirect(url_for('auth.forgot_password'))
        
        if password != confirm_password:
            flash('Пароли не совпадают', 'error')
            return redirect(url_for('auth.reset_password', token=token))

        user = User.query.filter_by(reset_password_token=token).first()
        
        if not user:
            flash('Ссылка для сброса пароля недействительна.', 'error')
            return redirect(url_for('auth.forgot_password'))
        
        if user.reset_password_expires < datetime.utcnow():
            flash('Ссылка для сброса пароля устарела. Запросите новую.', 'error')
            return redirect(url_for('auth.forgot_password'))
        
        try:
            from werkzeug.security import generate_password_hash
            user.password = generate_password_hash(password)
            user.reset_password_token = None
            user.reset_password_expires = None
            db.session.commit()
            
            flash('Пароль успешно изменен. Теперь вы можете войти с новым паролем.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            flash('Произошла ошибка при изменении пароля. Попробуйте еще раз.', 'error')
            return redirect(url_for('auth.reset_password', token=token))