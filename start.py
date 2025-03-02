import os
import sys
import subprocess
import webbrowser
from time import sleep

def check_requirements():
    """检查是否安装了所有依赖"""
    try:
        import flask
        import flask_sqlalchemy
        import flask_login
        import flask_mail
        import dotenv
        from apscheduler.schedulers.background import BackgroundScheduler
        return True
    except ImportError as e:
        print(f"缺少必要的依赖: {str(e)}")
        print("正在尝试安装依赖...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            return True
        except subprocess.CalledProcessError:
            print("安装依赖失败，请手动运行: pip install -r requirements.txt")
            return False

def setup_database():
    """初始化数据库"""
    try:
        if not os.path.exists('paper_schedule.db'):
            print("正在初始化数据库...")
            subprocess.check_call([sys.executable, "-m", "flask", "db-init"])
        return True
    except subprocess.CalledProcessError:
        print("初始化数据库失败，请手动运行: flask db-init")
        return False

def start_app():
    """启动应用"""
    print("正在启动应用...")
    print("==================================================")
    print("论文讲解安排系统")
    print("==================================================")
    print("网站地址: http://localhost:5000")
    print("管理员账号: admin")
    print("管理员密码: admin (首次登录请立即修改密码)")
    print("==================================================")
    print("按Ctrl+C停止服务")
    print("==================================================")
    
    # 打开浏览器
    sleep(1)
    webbrowser.open('http://localhost:5000')
    
    # 启动Flask应用
    os.environ['FLASK_APP'] = 'app.py'
    os.environ['FLASK_ENV'] = 'development'
    subprocess.call([sys.executable, "-m", "flask", "run", "--host=0.0.0.0"])

if __name__ == "__main__":
    print("正在启动论文讲解安排系统...")
    
    if check_requirements() and setup_database():
        start_app()
    else:
        print("启动失败，请检查上述错误。")
        input("按Enter键退出...") 
