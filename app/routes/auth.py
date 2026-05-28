from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.user import UserModel
import sqlite3

# 建立身分驗證 Blueprint
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    使用者註冊路由。
    GET:
        - 渲染並返回 'register.html' 表單。
    POST:
        - 接收表單欄位 (username, password, email)。
        - 檢查格式、是否重複註冊。
        - 使用 generate_password_hash 加密密碼，調用 UserModel 寫入。
        - 註冊成功重導向至 '/login'，失敗則導回並拋出錯誤訊息。
    """
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        # 基本輸入驗證
        if not username or not email or not password:
            flash('所有欄位皆為必填！', 'danger')
            return render_template('register.html')

        if len(password) < 6:
            flash('密碼長度必須至少為 6 個字元！', 'danger')
            return render_template('register.html')

        try:
            # 加密密碼雜湊
            password_hash = generate_password_hash(password)
            # 建立使用者
            UserModel.create(username, password_hash, email)
            flash('註冊成功！請使用您的帳號進行登入。', 'success')
            return redirect(url_for('auth.login'))
        except sqlite3.IntegrityError:
            flash('該使用者帳號或電子郵件已被註冊！', 'danger')
            return render_template('register.html')
        except Exception as e:
            flash(f'註冊過程發生未知錯誤：{str(e)}', 'danger')
            return render_template('register.html')

    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    使用者登入路由。
    GET:
        - 渲染並返回 'login.html' 表單。
    POST:
        - 接收表單欄位 (username, password)。
        - 調用 UserModel.get_by_username 查找使用者。
        - 使用 check_password_hash 驗證密碼雜湊。
        - 驗證成功後，將用戶 ID 與 username 寫入 session。
        - 302 重導向回首頁 '/'，失敗顯示錯誤訊息。
    """
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash('請輸入帳號與密碼！', 'danger')
            return render_template('login.html')

        try:
            # 查詢使用者
            user = UserModel.get_by_username(username)
            if user and check_password_hash(user['password_hash'], password):
                # 登入成功，將資訊寫入 session
                session.clear()
                session['user_id'] = user['id']
                session['username'] = user['username']
                flash(f'歡迎回來，{username}！', 'success')
                return redirect(url_for('main.index'))
            else:
                flash('帳號或密碼輸入錯誤，請再試一次。', 'danger')
                return render_template('login.html')
        except Exception as e:
            flash(f'登入過程發生錯誤：{str(e)}', 'danger')
            return render_template('login.html')

    return render_template('login.html')

@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    """
    登出路由。
    GET/POST:
        - 清除 session 中的使用者資訊。
        - 使用 flash 提示登出成功。
        - 302 重導向回首頁 '/'。
    """
    session.clear()
    flash('您已成功登出系統。', 'success')
    return redirect(url_for('main.index'))
