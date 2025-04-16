import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

# 加载环境变量
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////app/data/paper_schedule.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 邮件配置
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.example.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'user@example.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'password')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@example.com')

db = SQLAlchemy(app)
mail = Mail(app)
login_manager = LoginManager(app)
login_manager.login_view = 'admin_login'

# 定义模型
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Paper(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    presenter = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class EmailConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    days_before = db.Column(db.Integer, default=1)
    notification_time = db.Column(db.Time, default=datetime.strptime('09:00', '%H:%M').time())
    enabled = db.Column(db.Boolean, default=True)

class EmailRecipient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 路由
@app.route('/')
def index():
    today = datetime.now().date()
    current_year = today.year
    
    # 获取所有论文，统一按日期升序排列
    papers = Paper.query.order_by(Paper.date).all()
    
    return render_template('index.html', papers=papers, today=today, current_year=current_year)

@app.route('/paper/add', methods=['GET', 'POST'])
def add_paper():
    if request.method == 'POST':
        date_str = request.form['date']
        presenter = request.form['presenter']
        title = request.form['title']
        
        try:
            date_obj = datetime.strptime(date_str, '%Y/%m/%d').date()
            new_paper = Paper(date=date_obj, presenter=presenter, title=title)
            db.session.add(new_paper)
            db.session.commit()
            flash('论文安排已添加', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'添加失败: {str(e)}', 'danger')
    
    return render_template('paper_form.html')

@app.route('/paper/edit/<int:id>', methods=['GET', 'POST'])
def edit_paper(id):
    paper = Paper.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            date_str = request.form['date']
            paper.date = datetime.strptime(date_str, '%Y/%m/%d').date()
            paper.presenter = request.form['presenter']
            paper.title = request.form['title']
            paper.updated_at = datetime.utcnow()
            db.session.commit()
            flash('论文安排已更新', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'更新失败: {str(e)}', 'danger')
    
    return render_template('paper_form.html', paper=paper)

@app.route('/paper/delete/<int:id>')
@login_required
def delete_paper(id):
    if not current_user.is_admin:
        flash('无权限删除论文安排', 'danger')
        return redirect(url_for('index'))
        
    paper = Paper.query.get_or_404(id)
    db.session.delete(paper)
    db.session.commit()
    flash('论文安排已删除', 'success')
    return redirect(url_for('index'))

@app.route('/papers/shift/<direction>')
def shift_papers(direction):
    today = datetime.now().date()
    # 获取所有未过期的论文安排
    future_papers = Paper.query.filter(Paper.date >= today).all()
    
    if not future_papers:
        flash('没有找到未来的论文安排', 'warning')
        return redirect(url_for('index'))
    
    # 根据方向决定是顺延还是提前
    days = 7 if direction == 'forward' else -7
    
    # 修改日期
    for paper in future_papers:
        paper.date = paper.date + timedelta(days=days)
    
    db.session.commit()
    
    if direction == 'forward':
        flash(f'已将{len(future_papers)}个未过期安排顺延一周', 'success')
    else:
        flash(f'已将{len(future_papers)}个未过期安排提前一周', 'success')
    
    return redirect(url_for('index'))

# 管理员路由
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
        
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password) and user.is_admin:
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        else:
            flash('登录失败，请检查用户名和密码', 'danger')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    flash('已退出登录', 'success')
    return redirect(url_for('index'))

@app.route('/admin/change_password', methods=['POST'])
@login_required
def change_admin_password_web():
    if not current_user.is_admin:
        flash('无权限修改密码', 'danger')
        return redirect(url_for('index'))
        
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    # 验证当前密码
    if not current_user.check_password(current_password):
        flash('当前密码不正确', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    # 验证新密码长度
    if len(new_password) < 8:
        flash('新密码长度必须至少为8个字符', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    # 验证两次输入的新密码是否一致
    if new_password != confirm_password:
        flash('两次输入的新密码不一致', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    # 修改密码
    current_user.set_password(new_password)
    db.session.commit()
    flash('密码已成功修改', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('无权限访问此页面', 'danger')
        return redirect(url_for('index'))
        
    email_config = EmailConfig.query.first()
    if not email_config:
        email_config = EmailConfig()
        db.session.add(email_config)
        db.session.commit()
        
    recipients = EmailRecipient.query.all()
    return render_template('admin_dashboard.html', email_config=email_config, recipients=recipients)

@app.route('/admin/email_config', methods=['POST'])
@login_required
def update_email_config():
    if not current_user.is_admin:
        return jsonify({'status': 'error', 'message': '无权限'}), 403
        
    email_config = EmailConfig.query.first()
    if not email_config:
        email_config = EmailConfig()
        db.session.add(email_config)
    
    email_config.days_before = int(request.form['days_before'])
    time_str = request.form['notification_time']
    email_config.notification_time = datetime.strptime(time_str, '%H:%M').time()
    email_config.enabled = 'enabled' in request.form
    
    db.session.commit()
    flash('邮件通知设置已更新', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/recipient/add', methods=['POST'])
@login_required
def add_recipient():
    if not current_user.is_admin:
        return jsonify({'status': 'error', 'message': '无权限'}), 403
        
    email = request.form['email']
    if EmailRecipient.query.filter_by(email=email).first():
        flash('该邮箱已存在', 'warning')
        return redirect(url_for('admin_dashboard'))
        
    new_recipient = EmailRecipient(email=email)
    db.session.add(new_recipient)
    db.session.commit()
    flash('收件人已添加', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/recipient/delete/<int:id>')
@login_required
def delete_recipient(id):
    if not current_user.is_admin:
        return jsonify({'status': 'error', 'message': '无权限'}), 403
        
    recipient = EmailRecipient.query.get_or_404(id)
    db.session.delete(recipient)
    db.session.commit()
    flash('收件人已删除', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/send_notification_now')
@login_required
def send_notification_now():
    if not current_user.is_admin:
        flash('无权限访问此功能', 'danger')
        return redirect(url_for('index'))
    
    # 获取最近的讲解安排
    today = datetime.now().date()
    upcoming_paper = Paper.query.filter(Paper.date >= today).order_by(Paper.date).first()
    
    if not upcoming_paper:
        flash('没有找到未来的论文讲解安排', 'warning')
        return redirect(url_for('admin_dashboard'))
    
    # 获取后续3次的安排
    future_papers = Paper.query.filter(Paper.date > upcoming_paper.date).order_by(Paper.date).limit(3).all()
    
    # 准备邮件内容
    subject = f"论文讲解提醒: {upcoming_paper.date.strftime('%Y/%m/%d')}"
    recipients = [r.email for r in EmailRecipient.query.all()]
    
    if not recipients:
        flash('没有收件人，请先添加收件人', 'warning')
        return redirect(url_for('admin_dashboard'))
    
    body = f"""
    提醒：下次论文讲解安排
    
    时间：{upcoming_paper.date.strftime('%Y/%m/%d')}
    讲解人：{upcoming_paper.presenter}
    论文名称：{upcoming_paper.title}
    
    未来安排：
    """
    
    for paper in future_papers:
        body += f"\n{paper.date.strftime('%Y/%m/%d')} - {paper.presenter} - {paper.title}"
    
    body += """

    请访问我们的网站 https://arcp.kylelv.com/ 查看和编辑具体安排。
    """
    
    try:
        msg = Message(subject=subject, recipients=recipients, body=body)
        mail.send(msg)
        flash('通知邮件已成功发送', 'success')
    except Exception as e:
        flash(f'邮件发送失败: {str(e)}', 'danger')
    
    return redirect(url_for('admin_dashboard'))

# 发送邮件通知的函数
def send_notification():
    with app.app_context():
        config = EmailConfig.query.first()
        if not config or not config.enabled:
            return
            
        today = datetime.now().date()
        target_date = today + timedelta(days=config.days_before)
        
        # 查找最近的讲解安排
        upcoming_paper = Paper.query.filter(Paper.date >= today).order_by(Paper.date).first()
        if not upcoming_paper:
            return
            
        # 只有在目标日期等于论文讲解日期时才继续
        if upcoming_paper.date == target_date:
            current_time = datetime.now().time()
            notification_time = config.notification_time
            
            # 计算当前时间与通知时间的时间差（分钟）
            # current_minutes = current_time.hour * 60 + current_time.minute
            # notification_minutes = notification_time.hour * 60 + notification_time.minute
            
            # 只在通知时间的前后30分钟内发送通知
            # 这样确保即使定时任务每小时运行一次，通知也只会发送一次
            # if abs(current_minutes - notification_minutes) <= 30:
            if True:
                # 获取后续3次的安排
                future_papers = Paper.query.filter(Paper.date > upcoming_paper.date).order_by(Paper.date).limit(3).all()
                
                # 准备邮件内容
                subject = f"论文讲解提醒: {upcoming_paper.date.strftime('%Y/%m/%d')}"
                recipients = [r.email for r in EmailRecipient.query.all()]
                
                if not recipients:
                    return
                    
                body = f"""
                提醒：下次论文讲解安排
                
                时间：{upcoming_paper.date.strftime('%Y/%m/%d')}
                讲解人：{upcoming_paper.presenter}
                论文名称：{upcoming_paper.title}
                
                未来安排：
                """
                
                for paper in future_papers:
                    body += f"\n{paper.date.strftime('%Y/%m/%d')} - {paper.presenter} - {paper.title}"
                    
                body += """

                请访问我们的网站 https://arcp.kylelv.com/ 查看和编辑具体安排。
                """
                
                msg = Message(subject=subject, recipients=recipients, body=body)
                mail.send(msg)

# 初始化数据库
@app.cli.command('db-init')
def db_init():
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

# 定时任务
scheduler = BackgroundScheduler()
scheduler.add_job(func=send_notification, trigger='interval', hours=24)
scheduler.start()

# 确保应用退出时关闭定时任务
atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    app.run(debug=True) 
