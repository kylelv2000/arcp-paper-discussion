import os
import sys
import subprocess
import webbrowser
from time import sleep

# 将项目根目录加入 sys.path 以防从 scripts 目录下运行时找不到 arcp 包
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def check_requirements():
    """检查是否安装了所有依赖"""
    try:
        import flask
        import flask_sqlalchemy
        import flask_login
        import flask_mail
        import dotenv
        from apscheduler.schedulers.background import BackgroundScheduler
        import waitress
        import arcp
        return True
    except ImportError as e:
        print(f"缺少必要的依赖: {str(e)}")
        print("正在尝试自动安装依赖...")
        import shutil
        uv_path = shutil.which("uv")
        if not uv_path:
            print("错误: 未检测到 uv 包管理器！本项目已全面转向 uv 进行依赖管理。")
            print("请先安装 uv (https://astral.sh/uv) 或手动在虚拟环境中同步依赖。")
            return False
            
        try:
            print("正在使用 uv sync 同步项目依赖...")
            # uv sync 会自动根据 pyproject.toml 和 uv.lock 安装所有依赖
            subprocess.check_call([uv_path, "sync"])
            return True
        except subprocess.CalledProcessError:
            print("使用 uv sync 同步依赖失败，请手动运行: uv sync")
            return False



def setup_database():
    """初始化数据库"""
    try:
        db_path = os.path.join('instance', 'paper_schedule.db')
        if not os.path.exists(db_path):
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
    print("网站地址: http://localhost:5001")
    print("管理员账号: admin")
    print("管理员密码: admin (首次登录请立即修改密码)")
    print("==================================================")
    print("按Ctrl+C停止服务")
    print("==================================================")
    
    # 打开浏览器
    sleep(1)
    webbrowser.open('http://localhost:5001')
    
    # 启动Flask应用
    os.environ['FLASK_APP'] = 'wsgi.py'
    os.environ['FLASK_ENV'] = 'development'
    subprocess.call([sys.executable, "-m", "flask", "run", "--host=0.0.0.0", "--port=5001"])



def setup_env():
    """检测并自动生成本地 instance/.env 配置文件"""
    instance_dir = 'instance'
    os.makedirs(instance_dir, exist_ok=True)
    
    env_path = os.path.join(instance_dir, '.env')
    example_path = os.path.join(instance_dir, '.env.example')
    
    if not os.path.exists(env_path):
        if os.path.exists(example_path):
            import shutil
            print("未检测到本地配置，正在自动生成 instance/.env 配置文件...")
            shutil.copyfile(example_path, env_path)
        else:
            print("警告: 未能在 instance/ 下找到 .env.example 模板。")

if __name__ == "__main__":
    print("正在启动论文讲解安排系统...")
    setup_env()
    
    if check_requirements() and setup_database():
        start_app()
    else:
        print("启动失败，请检查上述错误。")
        input("按Enter键退出...")
 
