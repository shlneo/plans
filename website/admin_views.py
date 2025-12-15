from typing import Self
from flask_admin import AdminIndexView, expose
from flask_login import current_user
from website.models import (
    User, Organization, current_utc_time, Plan, Ticket, Unit, 
    Direction, EconMeasure, EconExec, Indicator, IndicatorUsage, Notification
)
from sqlalchemy.exc import SQLAlchemyError
from flask_admin.contrib.sqla import ModelView
from flask import flash, redirect, url_for, current_app, request
from functools import wraps
from datetime import datetime, timedelta
from website import db
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange
from wtforms import PasswordField, SelectField, FloatField, IntegerField
from werkzeug.security import generate_password_hash
import decimal

def admin_required(f):
    """Декоратор для проверки прав администратора"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Необходимо авторизоваться', 'error')
            return redirect(url_for('auth.login'))
        
        is_admin = False
        if hasattr(current_user, 'is_admin'):
            is_admin = getattr(current_user, 'is_admin', False)
        
        if not is_admin:
            flash('Недостаточно прав для доступа к админ-панели', 'error')
            return redirect(url_for('views.begin_page'))
        
        return f(*args, **kwargs)
    return decorated_function

class MyMainView(AdminIndexView):
    @expose('/')
    @admin_required
    def index(self):
        """Главная страница админ-панели со статистикой"""
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
            
            plan_data = Plan.query.count()
            draft_plans = Plan.query.filter_by(is_draft=True).count()
            approved_plans = Plan.query.filter_by(is_approved=True).count()
            
            # Статистика по другим таблицам
            tickets_count = Ticket.query.count()
            units_count = Unit.query.count()
            directions_count = Direction.query.count()
            measures_count = EconMeasure.query.count()
            execs_count = EconExec.query.count()
            indicators_count = Indicator.query.count()
            usages_count = IndicatorUsage.query.count()
            notifications_count = Notification.query.count()
            
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error in admin stats: {str(e)}")
            user_data = organization_data = active_users = new_users = 0
            admins_count = auditors_count = respondents_count = orgs_with_users = 0
            plan_data = draft_plans = approved_plans = 0
            tickets_count = units_count = directions_count = measures_count = 0
            execs_count = indicators_count = usages_count = notifications_count = 0
            flash('Ошибка при получении статистики из базы данных', 'error')

        # Правильные endpoint'ы Flask-Admin
        # Формат: {view_class_name.lower()}.index_view
        endpoints = {
            'users': 'user.index_view',  # UserView -> user
            'organizations': 'organization.index_view',  # OrganizationView -> organization
            'plans': 'plan.index_view',  # PlanView -> plan
            'tickets': 'ticket.index_view',  # TicketView -> ticket
            'units': 'unit.index_view',  # UnitView -> unit
            'directions': 'direction.index_view',  # DirectionView -> direction
            'econ_measures': 'econmeasure.index_view',  # EconMeasureView -> econmeasure
            'econ_execs': 'econexec.index_view',  # EconExecView -> econexec
            'indicators': 'indicator.index_view',  # IndicatorView -> indicator
            'indicator_usages': 'indicatorusage.index_view',  # IndicatorUsageView -> indicatorusage
            'notifications': 'notification.index_view',  # NotificationView -> notification
        }

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
                        approved_plans=approved_plans,
                        tickets_count=tickets_count,
                        units_count=units_count,
                        directions_count=directions_count,
                        measures_count=measures_count,
                        execs_count=execs_count,
                        indicators_count=indicators_count,
                        usages_count=usages_count,
                        notifications_count=notifications_count,
                        profile_url=url_for('views.profile'),
                        current_time=datetime.utcnow(),
                        endpoints=endpoints
                        )
        
    def is_accessible(self):
        """Проверка доступности всей админ-панели"""
        if not current_user.is_authenticated:
            return False
        
        if hasattr(current_user, 'is_admin'):
            return getattr(current_user, 'is_admin', False)
        return False

    def inaccessible_callback(self, name, **kwargs):
        """Обработка случая, когда доступ запрещен"""
        if not current_user.is_authenticated:
            flash('Необходимо авторизоваться для доступа к админ-панели', 'error')
            return redirect(url_for('auth.login'))
        
        flash('Недостаточно прав для доступа к админ-панели', 'error')
        return redirect(url_for('views.begin_page'))

class SecureModelView(ModelView):
    """Базовый класс для всех защищенных админ-вьюх"""
    
    def is_accessible(self):
        """Проверка доступности"""
        if not current_user.is_authenticated:
            return False
        
        if hasattr(current_user, 'is_admin'):
            return getattr(current_user, 'is_admin', False)
        return False

    def inaccessible_callback(self, name, **kwargs):
        """Обработка запрета доступа"""
        if not current_user.is_authenticated:
            flash('Необходимо авторизоваться для доступа к админ-панели', 'error')
            return redirect(url_for('auth.login'))
        
        flash('Недостаточно прав для доступа к этому разделу', 'error')
        return redirect(url_for('views.begin_page'))
    
    # Конфигурация отображения
    page_size = 50
    can_view_details = True
    can_export = True
    export_max_rows = 1000
    export_types = ['csv', 'json']
    
    column_display_pk = False
    create_modal = False
    edit_modal = False
    details_modal = False
    
    def handle_view_exception(self, exc):
        """Обработка исключений"""
        if isinstance(exc, SQLAlchemyError):
            current_app.logger.error(f"Database error in admin: {str(exc)}")
            flash(f'Ошибка базы данных: {str(exc)}', 'error')
            return True
        return super().handle_view_exception(exc)

class UserView(SecureModelView):
    """Админ-панель для управления пользователями"""
    
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
    
    form_columns = ['email', 'last_name', 'first_name', 'patronymic_name', 
                    'post', 'phone', 'organization', 'password', 
                    'is_admin', 'is_auditor']
    
    form_args = {
        'email': {
            'label': 'Email',
            'validators': [DataRequired(), Email(), Length(max=255)],
            'description': 'Введите email пользователя'
        },
        'last_name': {
            'label': 'Фамилия',
            'validators': [DataRequired(), Length(max=100)],
            'description': 'Введите фамилию'
        },
        'first_name': {
            'label': 'Имя',
            'validators': [DataRequired(), Length(max=100)],
            'description': 'Введите имя'
        },
        'patronymic_name': {
            'label': 'Отчество',
            'validators': [Length(max=100)],
            'description': 'Введите отчество (необязательно)'
        },
        'post': {
            'label': 'Должность',
            'validators': [Length(max=100)],
            'description': 'Введите должность'
        },
        'phone': {
            'label': 'Телефон',
            'validators': [Length(max=20)],
            'description': 'Введите номер телефона'
        },
        'password': {
            'label': 'Пароль',
            'validators': [Length(min=4)],
            'description': 'Введите новый пароль (оставьте пустым, чтобы не менять)'
        }
    }
    
    # Делаем поле пароля необязательным при редактировании
    form_widget_args = {
        'password': {
            'placeholder': 'Оставьте пустым, чтобы не менять пароль'
        }
    }
    
    # Добавляем кастомный валидатор для пароля
    form_extra_fields = {
        'confirm_password': PasswordField(
            'Подтверждение пароля',
            validators=[Length(min=4)],
            description='Повторите пароль для подтверждения'
        )
    }
    
    column_exclude_list = ['password', 'reset_password_token', 'reset_password_expires']
    column_searchable_list = ['email', 'last_name', 'first_name', 'patronymic_name', 'phone']
    column_filters = ['id', 'email', 'is_admin', 'is_auditor', 'organization_id']
    
    column_formatters = {
        'organization': lambda v, c, m, p: m.organization.name if m.organization else 'Не назначена',
        'is_admin': lambda v, c, m, p: '✅ Да' if m.is_admin else '❌ Нет',
        'is_auditor': lambda v, c, m, p: '✅ Да' if m.is_auditor else '❌ Нет',
        'last_active': lambda v, c, m, p: m.last_active.strftime('%d.%m.%Y %H:%M') if m.last_active else '',
        'begin_time': lambda v, c, m, p: m.begin_time.strftime('%d.%m.%Y %H:%M') if m.begin_time else ''
    }
    
    def on_model_change(self, form, model, is_created):
        """Обработка изменений модели"""
        # Проверяем, был ли введен новый пароль
        password = form.password.data
        confirm_password = form.confirm_password.data if hasattr(form, 'confirm_password') else None
        
        # Если пароль введен при создании
        if is_created:
            if not password:
                flash('При создании пользователя необходимо указать пароль!', 'error')
                raise ValueError('Пароль обязателен при создании пользователя')
            if password != confirm_password:
                flash('Пароли не совпадают!', 'error')
                raise ValueError('Пароли не совпадают')
            model.password = generate_password_hash(password)
        
        # Если пароль введен при редактировании
        elif password:
            # Проверяем подтверждение пароля
            if confirm_password and password != confirm_password:
                flash('Пароли не совпадают!', 'error')
                raise ValueError('Пароли не совпадают')
            model.password = generate_password_hash(password)
        
        # Если пароль не меняли (пустое поле), оставляем старый
        # Не обновляем пароль, если поле пустое
        
        model.last_active = datetime.utcnow()
        if model.is_admin or model.is_auditor:
            model.organization_id = None
    
    def on_form_prefill(self, form, id):
        """Предзаполнение формы при редактировании"""
        # Получаем пользователя
        user = User.query.get(id)
        
        # Устанавливаем пустое значение для поля пароля
        # Это безопасно, так как в on_model_change мы проверяем, было ли поле заполнено
        form.password.data = ''
        
        # Если у формы есть поле подтверждения пароля, тоже очищаем его
        if hasattr(form, 'confirm_password'):
            form.confirm_password.data = ''
        
        # Сохраняем старый пароль в форме как скрытое значение
        # (если нужно для дополнительной логики)
        form._old_password = user.password if user else ''
    
    # Альтернативный подход: скрыть поле пароля при редактировании
    def get_edit_form(self):
        """Получить форму для редактирования с дополнительными настройками"""
        form = super().get_edit_form()
        
        # Делаем поле пароля необязательным при редактировании
        form.password.validators = [Length(min=6)]
        form.password.description = 'Введите новый пароль (оставьте пустым, чтобы не менять)'
        
        return form
    
    def get_create_form(self):
        """Получить форму для создания с дополнительными настройками"""
        form = super().get_create_form()
        
        # Делаем поле пароля обязательным при создании
        form.password.validators = [DataRequired(), Length(min=6)]
        form.password.description = 'Введите пароль для нового пользователя'
        
        return form
    
    
class OrganizationView(SecureModelView):
    """Админ-панель для управления организациями"""
    
    column_list = ['id', 'name', 'okpo', 'ynp', 'ministry_id', 'is_active', 'users']
    column_default_sort = ('id', True)
    column_sortable_list = ('id', 'name', 'okpo', 'is_active')
    
    can_delete = True
    can_create = True
    can_edit = True
    can_export = True
    
    form_columns = ['name', 'okpo', 'ynp', 'ministry_id', 'is_active']
    
    form_args = {
        'name': {
            'label': 'Полное наименование',
            'validators': [DataRequired(), Length(max=500)],
            'description': 'Полное название организации'
        },
        'okpo': {
            'label': 'ОКПО',
            'validators': [DataRequired(), Length(max=20)],
            'description': 'Код ОКПО организации'
        },
        'ynp': {
            'label': 'УНП',
            'validators': [Length(max=20)],
            'description': 'Учетный номер плательщика'
        },
        'ministry_id': {
            'label': 'Министерство',
            'validators': [Length(max=500)],
            'description': 'Вышестоящее министерство'
        },
        'is_active': {
            'label': 'Активна',
            'description': 'Активна ли организация'
        }
    }
    
    column_searchable_list = ['name', 'okpo', 'ynp', 'ministry_id']
    column_filters = ['id', 'is_active', 'ministry_id']
    
    column_formatters = {
        'is_active': lambda v, c, m, p: '✅ Да' if m.is_active else '❌ Нет',
        'users': lambda v, c, m, p: f'{len(m.users)} пользователей' if m.users else 'Нет пользователей'
    }

class PlanView(SecureModelView):
    """Админ-панель для управления планами"""
    
    column_list = ['id', 'name_org', 'okpo', 'year', 'email', 'fio', 
                   'is_draft', 'is_control', 'is_sent', 'is_error', 'is_approved',
                   'begin_time', 'change_time', 'sent_time', 'audit_time']
    column_default_sort = ('id', True)
    column_sortable_list = ('id', 'year', 'begin_time', 'change_time', 'sent_time', 'audit_time')
    
    can_delete = True
    can_create = True
    can_edit = True
    can_export = True
    
    form_columns = ['okpo', 'name_org', 'year', 'email', 'fio', 'phone',
                    'organization', 'user', 'energy_saving', 'share_fuel', 
                    'saving_fuel', 'share_energy', 'is_draft', 'is_control', 
                    'is_sent', 'is_error', 'is_approved', 'afch']
    
    form_args = {
        'okpo': {
            'label': 'ОКПО',
            'validators': [Length(max=20)],
            'description': 'Код ОКПО организации'
        },
        'name_org': {
            'label': 'Название организации',
            'validators': [Length(max=500)],
            'description': 'Название организации'
        },
        'year': {
            'label': 'Год',
            'validators': [DataRequired(), NumberRange(min=2000, max=2100)],
            'description': 'Год плана'
        },
        'email': {
            'label': 'Email',
            'validators': [DataRequired(), Email(), Length(max=255)],
            'description': 'Email ответственного'
        },
        'fio': {
            'label': 'ФИО',
            'validators': [DataRequired(), Length(max=255)],
            'description': 'ФИО ответственного'
        },
        'phone': {
            'label': 'Телефон',
            'validators': [Length(max=20)],
            'description': 'Телефон ответственного'
        }
    }
    
    column_searchable_list = ['okpo', 'name_org', 'email', 'fio', 'phone']
    column_filters = ['id', 'year', 'is_draft', 'is_control', 'is_sent', 
                      'is_error', 'is_approved', 'afch']
    
    column_formatters = {
        'is_draft': lambda v, c, m, p: '📝 Черновик' if m.is_draft else '',
        'is_control': lambda v, c, m, p: '👁 Контроль' if m.is_control else '',
        'is_sent': lambda v, c, m, p: '📤 Отправлен' if m.is_sent else '',
        'is_error': lambda v, c, m, p: '❌ Ошибка' if m.is_error else '',
        'is_approved': lambda v, c, m, p: '✅ Утвержден' if m.is_approved else '',
        'afch': lambda v, c, m, p: '🏭 АФЧ' if m.afch else '',
        'begin_time': lambda v, c, m, p: m.begin_time.strftime('%d.%m.%Y %H:%M') if m.begin_time else '',
        'change_time': lambda v, c, m, p: m.change_time.strftime('%d.%m.%Y %H:%M') if m.change_time else '',
        'sent_time': lambda v, c, m, p: m.sent_time.strftime('%d.%m.%Y %H:%M') if m.sent_time else '',
        'audit_time': lambda v, c, m, p: m.audit_time.strftime('%d.%m.%Y %H:%M') if m.audit_time else '',
        'organization': lambda v, c, m, p: m.organization.name if m.organization else '',
        'user': lambda v, c, m, p: f"{m.user.last_name} {m.user.first_name}" if m.user else ''
    }

class TicketView(SecureModelView):
    """Админ-панель для управления тикетами"""
    
    column_list = ['id', 'plan', 'begin_time', 'luck', 'is_owner', 'note']
    column_default_sort = ('begin_time', True)
    column_sortable_list = ('id', 'begin_time', 'luck', 'is_owner')
    
    can_delete = True
    can_create = True
    can_edit = True
    can_export = True
    
    form_columns = ['plan', 'luck', 'is_owner', 'note']
    
    form_args = {
        'plan': {
            'label': 'План',
            'description': 'Связанный план'
        },
        'luck': {
            'label': 'Успешно',
            'description': 'Успешно ли выполнен тикет'
        },
        'is_owner': {
            'label': 'Владелец',
            'description': 'Является ли пользователь владельцем'
        },
        'note': {
            'label': 'Примечание',
            'validators': [DataRequired(), Length(max=500)],
            'description': 'Текст примечания'
        }
    }
    
    column_searchable_list = ['note']
    column_filters = ['id', 'luck', 'is_owner', 'plan_id']
    
    column_formatters = {
        'luck': lambda v, c, m, p: '✅ Да' if m.luck else '❌ Нет',
        'is_owner': lambda v, c, m, p: '👤 Да' if m.is_owner else '👥 Нет',
        'begin_time': lambda v, c, m, p: m.begin_time.strftime('%d.%m.%Y %H:%M') if m.begin_time else '',
        'plan': lambda v, c, m, p: f"План #{m.plan.id} ({m.plan.name_org})" if m.plan else ''
    }

class UnitView(SecureModelView):
    """Админ-панель для управления единицами измерения"""
    
    column_list = ['id', 'code', 'name']
    column_default_sort = ('id', True)
    column_sortable_list = ('id', 'code', 'name')
    
    can_delete = True
    can_create = True
    can_edit = True
    can_export = True
    
    form_columns = ['code', 'name']
    
    form_args = {
        'code': {
            'label': 'Код',
            'validators': [DataRequired(), Length(max=400)],
            'description': 'Код единицы измерения'
        },
        'name': {
            'label': 'Название',
            'validators': [DataRequired(), Length(max=400)],
            'description': 'Название единицы измерения'
        }
    }
    
    column_searchable_list = ['code', 'name']
    column_filters = ['id', 'code']

class DirectionView(SecureModelView):
    """Админ-панель для управления направлениями"""
    
    column_list = ['id', 'code', 'name', 'unit', 'is_local', 'DateStart', 'DateEnd']
    column_default_sort = ('id', True)
    column_sortable_list = ('id', 'code', 'name', 'DateStart', 'DateEnd')
    
    can_delete = True
    can_create = True
    can_edit = True
    can_export = True
    
    form_columns = ['code', 'name', 'unit', 'is_local', 'DateStart', 'DateEnd']
    
    form_args = {
        'code': {
            'label': 'Код',
            'validators': [Length(max=400)],
            'description': 'Код направления'
        },
        'name': {
            'label': 'Название',
            'validators': [Length(max=400)],
            'description': 'Название направления'
        },
        'unit': {
            'label': 'Единица измерения',
            'description': 'Единица измерения'
        },
        'is_local': {
            'label': 'Локальный',
            'description': 'Является ли локальным'
        }
    }
    
    column_searchable_list = ['code', 'name']
    column_filters = ['id', 'is_local']
    
    column_formatters = {
        'is_local': lambda v, c, m, p: '🏠 Да' if m.is_local else '🌍 Нет',
        'DateStart': lambda v, c, m, p: m.DateStart.strftime('%d.%m.%Y') if m.DateStart else '',
        'DateEnd': lambda v, c, m, p: m.DateEnd.strftime('%d.%m.%Y') if m.DateEnd else '',
        'unit': lambda v, c, m, p: f"{m.unit.code} ({m.unit.name})" if m.unit else ''
    }

class EconMeasureView(SecureModelView):
    """Админ-панель для управления экономическими мерами"""
    
    column_list = ['id', 'plan', 'direction', 'year_econ', 'estim_econ', 'order']
    column_default_sort = ('id', True)
    column_sortable_list = ('id', 'year_econ', 'estim_econ', 'order')
    
    can_delete = True
    can_create = True
    can_edit = True
    can_export = True
    
    form_columns = ['plan', 'direction', 'year_econ', 'estim_econ', 'order']
    
    form_args = {
        'plan': {
            'label': 'План',
            'description': 'Связанный план'
        },
        'direction': {
            'label': 'Направление',
            'description': 'Направление меры'
        },
        'year_econ': {
            'label': 'Экономия в год',
            'validators': [Optional()],
            'description': 'Экономия в год'
        },
        'estim_econ': {
            'label': 'Расчетная экономия',
            'validators': [Optional()],
            'description': 'Расчетная экономия'
        },
        'order': {
            'label': 'Порядок',
            'validators': [Optional(), NumberRange(min=0)],
            'description': 'Порядок сортировки'
        }
    }
    
    column_searchable_list = []
    column_filters = ['id', 'order']
    
    column_formatters = {
        'plan': lambda v, c, m, p: f"План #{m.plan.id}" if m.plan else '',
        'direction': lambda v, c, m, p: f"{m.direction.code} - {m.direction.name}" if m.direction else ''
    }

class EconExecView(SecureModelView):
    """Админ-панель для управления экономическими исполнениями"""
    
    column_list = ['id', 'plan', 'econ_measures', 'name', 'Volume', 'EffTut', 'EffRub',
                   'ExpectedQuarter', 'EffCurrYear', 'Payback', 'is_local', 'is_corrected']
    column_default_sort = ('id', True)
    
    can_delete = True
    can_create = True
    can_edit = True
    can_export = True
    
    form_columns = ['plan', 'econ_measures', 'name', 'Volume', 'EffTut', 'EffRub',
                    'ExpectedQuarter', 'EffCurrYear', 'Payback', 'VolumeFin',
                    'BudgetState', 'BudgetRep', 'BudgetLoc', 'BudgetOther',
                    'MoneyOwn', 'MoneyLoan', 'MoneyOther', 'is_local', 'is_corrected', 'order']
    
    form_args = {
        'name': {
            'label': 'Название',
            'validators': [DataRequired(), Length(max=4000)],
            'description': 'Название исполнения'
        },
        'is_local': {
            'label': 'Локальный',
            'description': 'Является ли локальным'
        },
        'is_corrected': {
            'label': 'Корректированный',
            'description': 'Был ли скорректирован'
        },
        'order': {
            'label': 'Порядок',
            'validators': [Optional(), NumberRange(min=0)],
            'description': 'Порядок сортировки'
        }
    }
    
    column_searchable_list = ['name']
    column_filters = ['id', 'is_local', 'is_corrected']
    
    column_formatters = {
        'is_local': lambda v, c, m, p: '🏠 Да' if m.is_local else '🌍 Нет',
        'is_corrected': lambda v, c, m, p: '✏️ Да' if m.is_corrected else '📄 Нет',
        'plan': lambda v, c, m, p: f"План #{m.plan.id}" if m.plan else '',
        'econ_measures': lambda v, c, m, p: f"Мера #{m.econ_measures.id}" if m.econ_measures else ''
    }

class IndicatorView(SecureModelView):
    """Админ-панель для управления показателями"""
    
    column_list = ['id', 'code', 'name', 'unit', 'CoeffToTut', 'IsMandatory', 
                   'IsSummary', 'IsSendRealUnit', 'IsSelfProd', 'IsLocal', 
                   'IsRenewable', 'Group', 'RowN', 'DateStart', 'DateEnd']
    column_default_sort = ('id', True)
    
    can_delete = True
    can_create = True
    can_edit = True
    can_export = True
    
    form_columns = ['code', 'name', 'unit', 'CoeffToTut', 'IsMandatory', 
                    'IsSummary', 'IsSendRealUnit', 'IsSelfProd', 'IsLocal', 
                    'IsRenewable', 'Group', 'RowN', 'DateStart', 'DateEnd', 
                    'id_indicator_parent']
    
    form_args = {
        'code': {
            'label': 'Код',
            'validators': [Length(max=400)],
            'description': 'Код показателя'
        },
        'name': {
            'label': 'Название',
            'validators': [Length(max=400)],
            'description': 'Название показателя'
        },
        'unit': {
            'label': 'Единица измерения',
            'description': 'Единица измерения'
        }
    }
    
    column_searchable_list = ['code', 'name']
    column_filters = ['id', 'IsMandatory', 'IsSummary', 'IsSendRealUnit', 
                      'IsSelfProd', 'IsLocal', 'IsRenewable', 'Group']
    
    column_formatters = {
        'IsMandatory': lambda v, c, m, p: '✅ Да' if m.IsMandatory else '❌ Нет',
        'IsSummary': lambda v, c, m, p: '📊 Да' if m.IsSummary else '📈 Нет',
        'IsSendRealUnit': lambda v, c, m, p: '📤 Да' if m.IsSendRealUnit else '📥 Нет',
        'IsSelfProd': lambda v, c, m, p: '🏭 Да' if m.IsSelfProd else '🏢 Нет',
        'IsLocal': lambda v, c, m, p: '🏠 Да' if m.IsLocal else '🌍 Нет',
        'IsRenewable': lambda v, c, m, p: '♻️ Да' if m.IsRenewable else '⚡ Нет',
        'DateStart': lambda v, c, m, p: m.DateStart.strftime('%d.%m.%Y') if m.DateStart else '',
        'DateEnd': lambda v, c, m, p: m.DateEnd.strftime('%d.%m.%Y') if m.DateEnd else '',
        'unit': lambda v, c, m, p: f"{m.unit.code} ({m.unit.name})" if m.unit else ''
    }

class IndicatorUsageView(SecureModelView):
    """Админ-панель для управления использованием показателей"""
    
    column_list = ['id', 'plan', 'indicator', 'QYearPrev', 'QYearCurr', 'QYearNext']
    column_default_sort = ('id', True)
    
    can_delete = True
    can_create = True
    can_edit = True
    can_export = True
    
    form_columns = ['plan', 'indicator', 'QYearPrev', 'QYearCurr', 'QYearNext']
    
    form_args = {
        'plan': {
            'label': 'План',
            'description': 'Связанный план'
        },
        'indicator': {
            'label': 'Показатель',
            'description': 'Показатель'
        }
    }
    
    column_searchable_list = []
    column_filters = ['id']
    
    column_formatters = {
        'plan': lambda v, c, m, p: f"План #{m.plan.id}" if m.plan else '',
        'indicator': lambda v, c, m, p: f"{m.indicator.code} - {m.indicator.name}" if m.indicator else ''
    }

class NotificationView(SecureModelView):
    """Админ-панель для управления уведомлениями"""
    
    column_list = ['id', 'user', 'message', 'is_read', 'created_at']
    column_default_sort = ('created_at', True)
    column_sortable_list = ('id', 'created_at', 'is_read')
    
    can_delete = True
    can_create = True
    can_edit = True
    can_export = True
    
    form_columns = ['user', 'message', 'is_read']
    
    form_args = {
        'user': {
            'label': 'Пользователь',
            'description': 'Пользователь'
        },
        'message': {
            'label': 'Сообщение',
            'validators': [DataRequired(), Length(max=140)],
            'description': 'Текст уведомления'
        },
        'is_read': {
            'label': 'Прочитано',
            'description': 'Прочитано ли уведомление'
        }
    }
    
    column_searchable_list = ['message']
    column_filters = ['id', 'is_read', 'user_id']
    
    column_formatters = {
        'is_read': lambda v, c, m, p: '✅ Да' if m.is_read else '❌ Нет',
        'created_at': lambda v, c, m, p: m.created_at.strftime('%d.%m.%Y %H:%M') if m.created_at else '',
        'user': lambda v, c, m, p: f"{m.user.email}" if m.user else ''
    }