from arcp import create_app

app = create_app()

if __name__ == "__main__":
    # 如果直接以脚本运行 wsgi.py，优先使用 Waitress 生产服务器启动，以兼容原 run.py 功能
    try:
        from waitress import serve
        print("正在使用 Waitress 生产服务器启动系统...")
        print("访问地址: http://localhost:5001")
        serve(app, host='0.0.0.0', port=5001)
    except ImportError:
        print("警告: 未检测到 waitress，将以 Flask 开发调试服务器启动...")
        app.run(host='0.0.0.0', port=5001)
