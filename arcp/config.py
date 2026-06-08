import os
from dotenv import load_dotenv

# 获取项目根目录与 instance 目录路径
base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
instance_path = os.path.join(base_dir, 'instance')

# 自动创建 instance 文件夹以存放数据库与配置文件
os.makedirs(instance_path, exist_ok=True)

# 优先从 instance/.env 加载，其次回退到根目录下的 .env
instance_env = os.path.join(instance_path, '.env')
if os.path.exists(instance_env):
    load_dotenv(instance_env)
else:
    load_dotenv(os.path.join(base_dir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default_secret_key')
    
    # 数据库配置：本地与 Docker 统一存放于 instance 目录
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        db_url = f'sqlite:///{os.path.join(instance_path, "paper_schedule.db")}'

    SQLALCHEMY_DATABASE_URI = db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False


    # 邮件配置
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.example.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'user@example.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'password')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@example.com')
