from flask import Flask, render_template, session, request, g, redirect, url_for
from flask_babel import Babel
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_babel import Babel, format_date
from .completion_db import create_database
from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman

import os
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
socketio = SocketIO()
bcrypt = Bcrypt()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()

LANGUAGES = {
    'en': 'English',
    'ru': 'Русский',
    'be': 'Беларуский'
}

def get_locale():
    if 'language' in session and session['language'] in LANGUAGES:
        return session['language']

    user = getattr(g, 'user', None)
    if user and hasattr(user, 'locale') and user.locale in LANGUAGES:
        return user.locale

    return request.accept_languages.best_match(LANGUAGES)

def get_timezone():
    user = getattr(g, 'user', None)
    if user is not None and hasattr(user, 'timezone'):
        return user.timezone
    return None

babel = Babel(
    locale_selector=get_locale,
    timezone_selector=get_timezone
)

def create_app():
    app = Flask(__name__, static_url_path='/static')

    app.config.update(
        SECRET_KEY=os.getenv('SECRET_KEY'),
        SQLALCHEMY_DATABASE_URI=f"postgresql://{os.getenv('postrgeuser')}:{os.getenv('postrgepass')}@localhost:5432/{os.getenv('postrgedbname')}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        BABEL_DEFAULT_LOCALE='ru',
        BABEL_TRANSLATION_DIRECTORIES='translations',
        LANGUAGES=LANGUAGES,
        SESSION_SQLALCHEMY=db,
        SESSION_PERMANENT=True,
        SESSION_TYPE='sqlalchemy',

        SEND_FILE_MAX_AGE_DEFAULT=0,  # Отключить кэширование в разработке
    )

    db.init_app(app)
    socketio.init_app(app)
    babel.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)
    csrf.init_app(app)
    

    Talisman(app, 
             force_https=False,  # True для продакшена
             content_security_policy=None)  # Временно отключить CSP
    
    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    with app.app_context():
        db.create_all()
        create_database(app, db)

    from .models import User, Organization, Plan, Ticket, Unit
    
    login_manager.init_app(app)
    login_manager.login_message = "Пожалуйста, авторизуйтесь для доступа к этой странице"
    login_manager.login_view = "auth.login"
    
    app.jinja_env.globals['format_date'] = format_date
    
    @app.context_processor
    def inject_get_locale():
        from . import get_locale
        return dict(get_locale=get_locale)
    
    # Добавьте обработчик для статических файлов
    @app.route('/static/<path:filename>')
    def custom_static(filename):
        from flask import send_from_directory
        return send_from_directory(app.static_folder, filename)
    
    # Middleware для добавления правильных заголовков
    @app.after_request
    def after_request(response):
        # Разрешить загрузку ресурсов с любого источника
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        
        # Отключить X-Frame-Options для мобильных устройств
        response.headers.remove('X-Frame-Options')
        
        return response
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html', hide_header=True), 404
    
    return app