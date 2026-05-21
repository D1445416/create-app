from flask import Blueprint

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
    pass

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
    pass

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    登出路由。
    POST:
        - 清除 session 中的使用者資訊。
        - 使用 flash 提示登出成功。
        - 302 重導向回首頁 '/'。
    """
    pass
