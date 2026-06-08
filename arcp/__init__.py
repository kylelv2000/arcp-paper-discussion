import sys
from flask import Flask
from arcp.config import Config
from arcp.extensions import db, mail, login_manager
from arcp.models import User
from arcp.routes import main_bp, admin_bp
from arcp.cli import register_cli_commands
from arcp.scheduler import init_scheduler

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 初始化扩展
    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)

    # 注册蓝图
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)

    # 注册 CLI 命令
    register_cli_commands(app)

    # 用户加载器
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # 避免在执行 CLI（如 db-init）时启动后台定时任务
    is_cli = len(sys.argv) > 1 and sys.argv[1] in ['db-init', 'change-password']
    
    if not is_cli:
        with app.app_context():
            init_scheduler(app)

    return app
