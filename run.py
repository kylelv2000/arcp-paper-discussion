from waitress import serve
from app import app

if __name__ == '__main__':
    print("正在启动论文讲解安排系统...")
    print("访问地址: http://localhost:5000")
    serve(app, host='0.0.0.0', port=5000) 
