from flask_admin import AdminIndexView, expose
from flask_login import current_user
from ..models import User, Organization, current_utc_time, Plan
from sqlalchemy.exc import SQLAlchemyError
from flask_admin.contrib.sqla import ModelView
import os
import tempfile
from flask import flash, redirect, request, url_for, send_file, current_app
from functools import wraps
import shutil
from datetime import datetime, timedelta
from collections import defaultdict
from .. import db
from wtforms.validators import DataRequired, Email, Length
from wtforms import PasswordField, BooleanField, StringField, SelectField
from werkzeug.security import generate_password_hash

def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Недостаточно прав для входа в админ-панель', 'error')
            return redirect(url_for('views.begin_page'))   
        return f(*args, **kwargs)
    return decorated_function

class MyMainView(AdminIndexView):
    @expose('/')
    def admin_stats(self):
        if not self.is_accessible():
            return self.inaccessible_callback('admin_stats')
        
        try:
            user_data = User.query.count()
            organization_data = Organization.query.count()
            
            now = current_utc_time()
            threshold = now - timedelta(minutes=3)
            active_users = User.query.filter(User.last_active >= threshold).count()
            
            week_ago = now - timedelta(days=7)
            new_users = User.query.filter(User.begin_time >= week_ago).count()
            
            admins_count = User.query.filter_by(is_admin=True).count()
            auditors_count = User.query.filter_by(is_auditor=True).count()
            respondents_count = User.query.filter(
                User.is_admin == False, 
                User.is_auditor == False
            ).count()
            

            orgs_with_users = db.session.query(Organization).join(User).distinct().count()
            
            plan_data = Plan.query.count() if hasattr(Plan, 'query') else 0
            draft_plans = Plan.query.filter_by(is_draft=True).count() if hasattr(Plan, 'query') else 0
            approved_plans = Plan.query.filter_by(is_approved=True).count() if hasattr(Plan, 'query') else 0
            
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error in admin_stats: {str(e)}")
            user_data = organization_data = active_users = new_users = 0
            admins_count = auditors_count = respondents_count = orgs_with_users = 0
            plan_data = draft_plans = approved_plans = 0
            flash('Ошибка при получении статистики из базы данных', 'error')

        return self.render('admin/stats.html', 
                        user_data=user_data,
                        organization_data=organization_data,
                        active_users=active_users,
                        new_users=new_users,
                        admins_count=admins_count,
                        auditors_count=auditors_count,
                        respondents_count=respondents_count,
                        orgs_with_users=orgs_with_users,
                        plan_data=plan_data,
                        draft_plans=draft_plans,
                        approved_plans=approved_plans
                        )

    def is_accessible(self):
        if hasattr(current_user, 'type'):
            return current_user.is_authenticated and getattr(current_user, 'type', '') == "Администратор"
        else:
            return current_user.is_authenticated and getattr(current_user, 'is_admin', False)

    def inaccessible_callback(self, name, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        return redirect(url_for('views.begin_page'))

class BaseAdminView(ModelView):
    def is_accessible(self):
        if hasattr(current_user, 'type'):
            return current_user.is_authenticated and getattr(current_user, 'type', '') == "Администратор"
        else:
            return current_user.is_authenticated and getattr(current_user, 'is_admin', False)

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login'))
    
    page_size = 50
    can_view_details = True
    can_export = True
    export_max_rows = 1000
    export_types = ['csv', 'json']
    
    column_display_actions = True
    column_display_pk = False
    
    def handle_view_exception(self, exc):
        """Обработка исключений"""
        if isinstance(exc, SQLAlchemyError):
            current_app.logger.error(f"Database error in admin: {str(exc)}")
            flash(f'Ошибка базы данных: {str(exc)}', 'error')
            return True
        return super().handle_view_exception(exc)


class UserView(BaseAdminView):
    column_list = ['id', 'email', 'last_name', 'first_name', 'patronymic_name', 
                   'post', 'phone', 'organization', 'is_admin', 'is_auditor', 
                   'last_active', 'begin_time']
    column_default_sort = ('id', True)
    column_sortable_list = ('id', 'email', 'last_name', 'first_name', 'last_active', 'begin_time')
    
    can_delete = True
    can_create = True
    can_edit = True
    can_export = True
    
    export_max_rows = 500
    export_types = ['csv']
    
    # Определяем форму с пользовательскими полями
    form_columns = ['email', 'last_name', 'first_name', 'patronymic_name', 
                    'post', 'phone', 'organization', 'password', 
                    'is_admin', 'is_auditor']
    
    form_args = {
        'email': {
            'label': 'Email',
            'validators': [DataRequired(), Email(), Length(max=255)]
        },
        'last_name': {
            'label': 'Фамилия',
            'validators': [DataRequired(), Length(max=100)]
        },
        'first_name': {
            'label': 'Имя',
            'validators': [DataRequired(), Length(max=100)]
        },
        'patronymic_name': {
            'label': 'Отчество',
            'validators': [Length(max=100)]
        },
        'post': {
            'label': 'Должность',
            'validators': [Length(max=100)]
        },
        'phone': {
            'label': 'Телефон',
            'validators': [Length(max=20)]
        },
        'password': {
            'label': 'Пароль',
            'validators': [Length(min=6)]
        }
    }
    
    # Скрыть пароль в списке
    column_exclude_list = ['password', 'reset_password_token', 'reset_password_expires']
    
    # Поля для поиска
    column_searchable_list = ['email', 'last_name', 'first_name', 'patronymic_name', 'phone']
    
    # Фильтры
    column_filters = ['id', 'email', 'is_admin', 'is_auditor', 'organization_id']
    
    # Поля, которые можно редактировать прямо в списке
    column_editable_list = ['is_admin', 'is_auditor', 'post']
    
    create_modal = True
    edit_modal = True
    
    def on_model_change(self, form, model, is_created):
        # Хешируем пароль при создании или изменении
        if form.password.data:
            model.password = generate_password_hash(form.password.data)
        
        # Автоматически обновляем last_active при редактировании
        model.last_active = datetime.utcnow()
        
        # Если пользователь админ или аудитор, сбрасываем organization_id
        if model.is_admin or model.is_auditor:
            model.organization_id = None
    
    def on_form_prefill(self, form, id):
        # При редактировании скрываем поле пароля (оставляем пустым)
        form.password.data = ''
    
    # Улучшенное отображение организаций
    column_formatters = {
        'organization': lambda v, c, m, p: m.organization.name if m.organization else 'Не назначена'
    }
    
    # Настройка отображения булевых значений
    column_formatters_detail = {
        'is_admin': lambda v, c, m, p: 'Да' if m.is_admin else 'Нет',
        'is_auditor': lambda v, c, m, p: 'Да' if m.is_auditor else 'Нет'
    }

