import click
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash
from getpass import getpass
from datetime import datetime
from arcp.extensions import db
from arcp.models import User, EmailConfig, Paper

@click.command('db-init')
@with_appcontext
def db_init():
    """初始化数据库并创建默认管理员和示例数据"""
    db.create_all()
    # 创建默认管理员账户
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', is_admin=True)
        admin.set_password('admin')
        db.session.add(admin)
        
        # 创建默认邮件配置
        if not EmailConfig.query.first():
            default_config = EmailConfig()
            db.session.add(default_config)
            
        # 添加示例数据
        sample_papers = [
            Paper(
                date=datetime.strptime('2024/9/9', '%Y/%m/%d').date(),
                presenter='贾富琦',
                title='A fast linear-arithmetic solver for DPLL(T)'
            ),
            Paper(
                date=datetime.strptime('2024/9/16', '%Y/%m/%d').date(),
                presenter='韩瑞',
                title='Learning to solve SMT formulas'
            )
        ]
        for paper in sample_papers:
            db.session.add(paper)
            
        db.session.commit()
        print('数据库初始化完成!')

@click.command('change-password')
@with_appcontext
def change_password():
    """交互式修改管理员密码"""
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        print('错误: 未找到管理员账户！')
        return
    
    print('正在更改管理员密码...')
    new_password = getpass('请输入新密码: ')
    if len(new_password) < 8:
        print('错误: 密码长度必须至少为8个字符')
        return
        
    confirm_password = getpass('请再次输入新密码: ')
    
    if new_password == confirm_password:
        admin.password_hash = generate_password_hash(new_password)
        db.session.commit()
        print('密码已成功更新！')
    else:
        print('错误: 两次输入的密码不一致')

def register_cli_commands(app):
    app.cli.add_command(db_init)
    app.cli.add_command(change_password)
