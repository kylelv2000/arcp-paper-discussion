from app import db, User
from werkzeug.security import generate_password_hash
from getpass import getpass
import sys

def change_admin_password():
    # 获取管理员用户
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        print('未找到管理员账户！')
        return
    
    # 输入新密码
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

if __name__ == "__main__":
    print("=== 论文讲解安排系统 - 管理员密码修改工具 ===")
    try:
        change_admin_password()
    except Exception as e:
        print(f"发生错误: {str(e)}")
        sys.exit(1) 
