from flask_admin.contrib.sqla import ModelView
from wtforms.validators import DataRequired, Email, Length, Optional
from werkzeug.security import generate_password_hash
from flask import redirect, url_for, flash
from flask_login import current_user
from wtforms import BooleanField, PasswordField, SelectField
from datetime import datetime

class UserView(ModelView):
    column_display_pk = True
    column_list = ['id', 'email', 'last_name', 'first_name', 'patronymic_name', 
                   'post', 'phone', 'organization', 'is_admin', 'is_auditor', 
                   'last_active', 'begin_time']
    
    can_delete = True
    can_create = True
    can_edit = True
    
    # ПРОСТОЙ подход: укажите только базовые поля
    form_columns = ['email', 'last_name', 'first_name', 'patronymic_name', 'post', 'phone']
    
    # ИСПРАВЛЕНО: используем правильный синтаксис для form_args
    form_args = {
        'email': {
            'label': 'Email',
            'validators': [DataRequired(), Email()]
        },
        'last_name': {
            'label': 'Фамилия',
            'validators': [DataRequired()]
        },
        'first_name': {
            'label': 'Имя', 
            'validators': [DataRequired()]
        }
        # Не указываем остальные поля здесь, если не нужны специальные настройки
    }
    
    column_searchable_list = ['email', 'last_name', 'first_name']
    
    # Отключаем все сложные настройки
    create_modal = False
    edit_modal = False
    
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin
    
    def inaccessible_callback(self, name, **kwargs):
        flash('Доступ запрещен. Требуются права администратора.', 'error')
        return redirect(url_for('views.login'))
    
    column_formatters = {
        'organization': lambda v, c, m, p: m.organization.name if m.organization else '-',
        'is_admin': lambda v, c, m, p: 'Да' if m.is_admin else 'Нет',
        'is_auditor': lambda v, c, m, p: 'Да' if m.is_auditor else 'Нет'
    }