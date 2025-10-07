from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import random
import smtplib
import string
from flask import flash, redirect, request, session, url_for
from sqlalchemy import func
from website import db
from website.models import User

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

def mes_on_email(message_body, recipient_email, email_type):
    sender = os.getenv('EMAILNAME')
    password = os.getenv('EMAILPASS')
    
    base_styles = """
        <style>
           body { 
                font-family: "Montserrat", sans-serif;   
                background: #eee;
                margin: 0; 
                padding: 0; 
            }
            hr{
                height: 1px;
                border: none;                  
                background-color: #d8d8d8;    
            }
            .email-container { 
                max-width: 600px; 
                margin: 30px auto; 
                background-color: #fff; 
                border-radius: 8px; 
                overflow: hidden; 
            }
            .logo-title{
                margin-top: 9px;
                display: flex;
                justify-content: center;
                gap: 11px;
                font-weight: 500;
                font-size: 17px;
            }
            .logo-title img{
                width: 50px;
                height: 50px;
            }
            .title{
                text-align: center;
                font-weight: 500;
                font-size: 17px;
                padding: 20px 50px;
            }
            .content { 
                padding: 20px 40px; 
                color: #333; 
                padding-top: 0;
            }
            .code { 
                text-align: center; 
                font-size: 32px; 
                font-weight: bold; 

                padding: 15px; 
                margin: 20px 0; 
            }
            .status { 
                text-align: center; 
                font-size: 17px; 
                font-weight: 600; 
                background-color: #000000; 
                padding: 5px 12px; 
                color: white;
                border-radius: 5px; 
                margin-left: 7px;
            }
            .footer {
                padding: 10px; 
                text-align: center; 
                font-size: 12px; 
                color: #777; 
            }
            .footer a { 
                color: #6441a5; 
                text-decoration: none; 
            }
        </style>
    """
    if email_type == "code":
        content = f"""
            <div class="content">
                <p>Здравствуйте!</p>
                <p>Кто-то пытается войти в ErespondentS используя вашу электронную почту.</p>
                <p>Код активации:</p>
                <div class="code">{message_body}</div>
            </div>
        """
    elif email_type == "pass":
        content = f"""
            <div class="content">
                <p>Здравствуйте!</p>
                <p>Кто-то пытается войти в ErespondentS используя вашу электронную почту.</p>
                <p>Ваш новый пароль :</p>
                <div class="code">{message_body}</div>
            </div>
        """
    elif email_type == "plan":
        content = f"""
        <p>Здравствуйте!</p>
        <p>Сообщение об изменении статуса отчета.</p>
        <p>Статус отчета изменен на:</p>
        <div class="code">{message_body}</div>
        """
    else:
        content = f"""
            <div>{message_body}</div>
        """   

    html_template = f"""
    <!DOCTYPE html>
    <html lang="ru">
        <head>
            <link rel="preconnect" href="https://fonts.googleapis.com">
            <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
            <link href="https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,100..900;1,100..900&display=swap" rel="stylesheet">
            {base_styles}
        </head>
        <body>
            <div class="email-container">
                <div class = "logo-title">
                    <img src="/static/img/Logo-black.svg" alt="">
                    <p>ErespondentS</p>
                </div>
                <hr>
                <div class = "title">Ваша учетная запись ErespondentS — Код активации</div>
                {content}
                <div class="footer">
                    <p>Дополнительную информацию можно найти <a href="">здесь</a>.</p>
                    <p>Спасибо,<br>Служба поддержки ErespondentS</p>
                </div>
            </div>
        </body>
    </html>
    """
    
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()

    try: 
        server.login(sender, password)
        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = recipient_email
        msg["Subject"] = "Оповещение"
        
        msg.attach(MIMEText(html_template, "html"))
        server.sendmail(sender, recipient_email, msg.as_string())
    
        # print("Письмо успешно отправлено")
        return "Email sent successfully"
    except Exception as _ex:
        # print(f"Ошибка при отправке письма: {_ex}")
        return f"{_ex}\nCheck log ..."
    finally:
        server.quit()

def gener_password():
    length=5
    characters = string.digits
    password = ''.join(random.choice(characters) for _ in range(length))
    return password

def send_activation_email(email):
    activation_code = gener_password()
    session['activation_code'] = activation_code
    mes_on_email(activation_code, email, 'code')

def sign_def(email, password1, password2):
    if email and password1:
        if User.query.filter(func.lower(User.email) == func.lower(email)).first():
            flash('Пользователь с таким email уже существует.', 'error')
            return redirect(url_for('auth.sign'))
        elif not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
            flash('Некорректный адрес электронной почты.', 'error')
            return redirect(url_for('auth.sign'))
        elif password1 != password2:
            flash('Ошибка в подтверждении пароля.', 'error')
            return redirect(url_for('auth.sign'))
        else:
            session['temp_user'] = {
                'email': email,
                'password': generate_password_hash(password1)
            }
            session.permanent = True
            send_activation_email(email) 
            flash('Регистрация прошла успешно! Проверьте свою почту для активации аккаунта.', 'success')
            return redirect(url_for('auth.code'))
    else:
        flash('Введите данные для регистрации.', 'error')
        return redirect(url_for('auth.sign'))

def activate_account():
    input_code = ''.join([
            request.form.get(f'activation_code_{i}', '') for i in range(5)
        ])
    if input_code == session.get('activation_code'):
        new_user = User(
            email=session['temp_user']['email'],
            password=session['temp_user']['password']
        )
        db.session.add(new_user)
        db.session.commit()
        session.pop('temp_user', None)
        session.pop('activation_code', None)
        flash('Аккаунт успешно активирован!', 'success')
        return redirect(url_for('views.login'))        
    else:
        flash('Некорректный код активации.', 'error')

