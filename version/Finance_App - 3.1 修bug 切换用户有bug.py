import sys
import sqlite3
import shutil
import os
import csv
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                             QMessageBox, QComboBox, QDateEdit, QTabWidget, QTextEdit,
                             QAction, QFileDialog, QDialog, QFormLayout, QDialogButtonBox,
                             QStackedWidget, QGroupBox, QInputDialog, QListWidget, QCheckBox)
from PyQt5.QtCore import Qt, QDate, QTimer, QSize
from PyQt5.QtGui import QIcon, QColor, QPixmap, QPainter
from PyQt5.QtChart import QChart, QChartView, QPieSeries, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis
import pypinyin
from PIL import Image
import io
import base64
from cryptography.fernet import Fernet
import calendar
from dateutil.relativedelta import relativedelta

class ProjectInfo:
    """项目信息元数据（集中管理所有项目相关信息）"""
    VERSION = "3.0.0"
    BUILD_DATE = "2025-05-26"
    AUTHOR = "杜玛"
    LICENSE = "MIT"
    COPYRIGHT = "© 永久 杜玛"
    URL = "https://github.com/duma520"
    MAINTAINER_EMAIL = "不提供"
    NAME = "人民币收支管理系统"
    DESCRIPTION = """人民币收支管理系统 - 一款功能完善的个人/家庭财务记账工具
主要功能：
• 记录收入、支出、借款、还款等各类财务交易
• 多用户支持，数据隔离存储
• 智能分类管理，支持自定义分类
• 强大的统计分析和报表功能
• 数据备份与恢复机制
• 借款还款跟踪管理
• 拼音首字母快速搜索
• 自动定期备份数据
• 操作历史撤销功能
• 预算管理
• 多账户管理
• 数据加密
• 收据图片管理
• 汇率转换
"""

    @classmethod
    def get_metadata(cls) -> dict:
        """获取主要元数据字典"""
        return {
            'version': cls.VERSION,
            'author': cls.AUTHOR,
            'license': cls.LICENSE,
            'url': cls.URL
        }

    @classmethod
    def get_header(cls) -> str:
        """生成标准化的项目头信息"""
        return f"{cls.NAME} {cls.VERSION} | {cls.LICENSE} License | {cls.URL}"

# 马卡龙色系定义
class MacaronColors:
    # 粉色系
    SAKURA_PINK = QColor(255, 183, 206)  # 樱花粉
    ROSE_PINK = QColor(255, 154, 162)    # 玫瑰粉
    
    # 蓝色系
    SKY_BLUE = QColor(162, 225, 246)    # 天空蓝
    LILAC_MIST = QColor(230, 230, 250)   # 淡丁香
    
    # 绿色系
    MINT_GREEN = QColor(181, 234, 215)   # 薄荷绿
    APPLE_GREEN = QColor(212, 241, 199)  # 苹果绿
    
    # 黄色/橙色系
    LEMON_YELLOW = QColor(255, 234, 165) # 柠檬黄
    BUTTER_CREAM = QColor(255, 248, 184) # 奶油黄
    PEACH_ORANGE = QColor(255, 218, 193) # 蜜桃橙
    
    # 紫色系
    LAVENDER = QColor(199, 206, 234)     # 薰衣草紫
    TARO_PURPLE = QColor(216, 191, 216)  # 香芋紫
    
    # 中性色
    CARAMEL_CREAM = QColor(240, 230, 221) # 焦糖奶霜

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("用户登录")
        self.setWindowIcon(QIcon("icon.ico"))
        self.resize(350, 250)
        
        layout = QVBoxLayout()
        
        # 用户选择
        self.user_combo = QComboBox()
        layout.addWidget(QLabel("选择用户:"))
        layout.addWidget(self.user_combo)
        
        # 新用户输入
        self.new_user_edit = QLineEdit()
        self.new_user_edit.setPlaceholderText("输入新用户名")
        layout.addWidget(QLabel("或创建新用户:"))
        layout.addWidget(self.new_user_edit)
        
        # 密码输入
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("输入密码")
        self.password_edit.setEchoMode(QLineEdit.Password)
        layout.addWidget(QLabel("密码:"))
        layout.addWidget(self.password_edit)
        
        # 记住密码
        self.remember_check = QCheckBox("记住密码")
        layout.addWidget(self.remember_check)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def load_users(self, users):
        self.user_combo.clear()
        self.user_combo.addItems(users)

class FinanceApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{ProjectInfo.NAME} {ProjectInfo.VERSION}")
        self.setWindowIcon(QIcon("icon.ico"))
        self.resize(1200, 800)

        # 初始化table属性
        self.table = None
        
        # 初始化多用户数据库
        self.init_user_db()
        
        # 显示登录对话框
        self.show_login_dialog()
        
        # 设置自动备份定时器
        self.backup_timer = QTimer()
        self.backup_timer.timeout.connect(self.auto_backup)
        self.backup_timer.start(3600000)  # 每小时自动备份一次
        
        # 操作历史栈
        self.operation_stack = []
        
        # 提醒定时器
        self.reminder_timer = QTimer()
        self.reminder_timer.timeout.connect(self.check_reminders)
        self.reminder_timer.start(60000)  # 每分钟检查一次提醒
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建主界面
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        
        # 主布局
        self.main_layout = QVBoxLayout()
        self.main_widget.setLayout(self.main_layout)
        
        # 创建搜索栏
        self.create_search_bar()
        
        # 创建标签页
        self.create_tabs()
        
        # 创建输入表单
        self.create_input_form()
        
        # 创建操作按钮
        self.create_action_buttons()
        
        # 加载数据
        self.load_data()
        self.update_statistics()

        # 设置定时清理临时文件（每6小时一次）
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self.cleanup_old_temp_files)
        self.cleanup_timer.start(6 * 3600 * 1000)  # 6小时

        # 确保初始加载时应用颜色
        QTimer.singleShot(100, lambda: [
            self.load_data(),
            self.update_statistics()
        ])

        # 创建状态栏
        self.statusBar().showMessage(f"🌈 欢迎使用{ProjectInfo.NAME} {ProjectInfo.VERSION}")
        # 设置状态栏样式
        self.statusBar().setStyleSheet("""
            QStatusBar {
                background-color: #f0f0f0;
                color: #333;
                font-size: 12px;
            }
        """)

    def init_user_db(self):
        """初始化用户数据库"""
        self.master_conn = sqlite3.connect('finance_master.db')
        self.master_cursor = self.master_conn.cursor()
        
        # 创建用户表（添加IF NOT EXISTS以避免重复创建）
        self.master_cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT,  -- 明确表示可空
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 检查并添加password列（如果不存在）
        self.master_cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in self.master_cursor.fetchall()]
        if 'password' not in columns:
            self.master_cursor.execute("ALTER TABLE users ADD COLUMN password TEXT")
    
        # 创建配置表（用于存储最后选择的用户等设置）
        self.master_cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')

        self.master_conn.commit()
        
        # 检查是否有默认用户
        self.master_cursor.execute("SELECT COUNT(*) FROM users")
        if self.master_cursor.fetchone()[0] == 0:
            self.master_cursor.execute("INSERT INTO users (username) VALUES (?)", ("默认用户",))
            self.master_conn.commit()

    def init_current_user_db(self, username):
        """初始化当前用户数据库"""
        self.current_user = username
        db_name = f'finance_{username}.db'
        
        # 检查是否需要加密数据库
        self.master_cursor.execute("SELECT password FROM users WHERE username=?", (username,))
        result = self.master_cursor.fetchone()
        password = result[0] if result else None  # 处理可能为NULL的情况
        self.db_encrypted = password is not None  # 只有当password不为None时才认为加密
        
        if self.db_encrypted:
            # 如果数据库加密，需要先解密
            key = self.get_encryption_key(password)
            self.cipher_suite = Fernet(key)
            
            # 检查数据库文件是否存在
            if os.path.exists(db_name):
                with open(db_name, 'rb') as f:
                    encrypted_data = f.read()
                decrypted_data = self.cipher_suite.decrypt(encrypted_data)
                
                # 创建临时数据库连接
                self.conn = sqlite3.connect(':memory:')
                self.conn.executescript(decrypted_data.decode('utf-8'))
            else:
                self.conn = sqlite3.connect(':memory:')
        else:
            self.conn = sqlite3.connect(db_name)
            
        self.cursor = self.conn.cursor()
        
        # 创建交易表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,  -- 'income' or 'expense' or 'loan' or 'repayment' or 'balance'
                amount REAL NOT NULL,
                category TEXT,
                description TEXT,
                date TEXT NOT NULL,
                related_id INTEGER,  -- 用于关联借款和还款
                status TEXT,  -- 'pending' or 'settled'
                account_id INTEGER DEFAULT 1,  -- 关联账户
                tags TEXT,  -- 标签，逗号分隔
                receipt_image TEXT,  -- 收据图片base64编码
                is_recurring INTEGER DEFAULT 0,  -- 是否为定期交易
                recurring_freq TEXT,  -- 定期频率: daily, weekly, monthly, yearly
                recurring_end TEXT,  -- 定期结束日期
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER REFERENCES users(id)
            )
        ''')

        # 检查并添加tags列（如果不存在）
        self.cursor.execute("PRAGMA table_info(transactions)")
        columns = [column[1] for column in self.cursor.fetchall()]
        
        # 确保account_id列存在
        if 'account_id' not in columns:
            self.cursor.execute("ALTER TABLE transactions ADD COLUMN account_id INTEGER DEFAULT 1")
        
        # 确保tags列存在
        if 'tags' not in columns:
            self.cursor.execute("ALTER TABLE transactions ADD COLUMN tags TEXT")

        # 创建分类表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                type TEXT NOT NULL,  -- 'income' or 'expense'
                user_id INTEGER REFERENCES users(id)
            )
        ''')
        
        # 创建账户表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                balance REAL DEFAULT 0,
                currency TEXT DEFAULT 'CNY',
                description TEXT,
                user_id INTEGER REFERENCES users(id)
            )
        ''')
        
        # 创建预算表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                month TEXT NOT NULL,  -- YYYY-MM格式
                user_id INTEGER REFERENCES users(id),
                UNIQUE(category, month)
            )
        ''')
        
        # 初始化默认分类
        self.cursor.execute("SELECT COUNT(*) FROM categories")
        if self.cursor.fetchone()[0] == 0:
            default_categories = [
                ('工资', 'income'),
                ('奖金', 'income'),
                ('投资', 'income'),
                ('其他', 'income'),
                ('餐饮', 'expense'),
                ('购物', 'expense'),
                ('娱乐', 'expense'),
                ('交通', 'expense'),
                ('住房', 'expense'),
                ('医疗', 'expense'),
                ('教育', 'expense'),
                ('其他', 'expense')
            ]
            for name, type_ in default_categories:
                self.cursor.execute(
                    "INSERT OR IGNORE INTO categories (name, type) VALUES (?, ?)",
                    (name, type_)
                )

        # 初始化默认账户
        self.cursor.execute("SELECT COUNT(*) FROM accounts")
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute(
                "INSERT INTO accounts (name, balance, currency) VALUES (?, ?, ?)",
                ("现金账户", 0, "CNY")
            )

        # 创建配置表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')

        self.conn.commit()

    def get_encryption_key(self, password):
        """从密码生成加密密钥"""
        # 使用PBKDF2从密码派生密钥
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.backends import default_backend
        import base64
        
        # 使用固定的salt（实际应用中应该为每个用户生成唯一的salt）
        salt = b'some_salt'
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def encrypt_database(self):
        """加密当前数据库"""
        if self.db_encrypted:
            return
            
        # 获取密码
        password, ok = QInputDialog.getText(
            self, "设置密码", "请输入数据库密码:",
            QLineEdit.Password
        )
        
        if not ok or not password:
            return
            
        # 生成加密密钥
        key = self.get_encryption_key(password)
        cipher_suite = Fernet(key)
        
        # 导出数据库内容
        db_name = f'finance_{self.current_user}.db'
        temp_conn = sqlite3.connect(db_name)
        temp_cursor = temp_conn.cursor()
        
        # 获取所有数据
        temp_cursor.execute("SELECT sql FROM sqlite_master WHERE type='table'")
        schema = "\n".join([row[0] for row in temp_cursor.fetchall()])
        
        # 获取所有数据
        data_dump = []
        temp_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in temp_cursor.fetchall()]
        
        for table in tables:
            temp_cursor.execute(f"SELECT * FROM {table}")
            data = temp_cursor.fetchall()
            columns = [desc[0] for desc in temp_cursor.description]
            
            for row in data:
                values = ", ".join([f"'{str(v)}'" if v is not None else "NULL" for v in row])
                data_dump.append(f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({values});")
        
        temp_conn.close()
        
        # 合并模式和数据进行加密
        full_dump = schema + "\n" + "\n".join(data_dump)
        encrypted_data = cipher_suite.encrypt(full_dump.encode('utf-8'))
        
        # 保存加密数据
        with open(db_name, 'wb') as f:
            f.write(encrypted_data)
            
        # 更新用户密码
        self.master_cursor.execute(
            "UPDATE users SET password=? WHERE username=?",
            (password, self.current_user)
        )
        self.master_conn.commit()
        
        self.db_encrypted = True
        self.cipher_suite = cipher_suite
        self.statusBar().showMessage("✅ 数据库已加密", 5000)

    def decrypt_database(self):
        """解密数据库"""
        if not self.db_encrypted:
            return
            
        # 获取密码
        password, ok = QInputDialog.getText(
            self, "输入密码", "请输入数据库密码:",
            QLineEdit.Password
        )
        
        if not ok or not password:
            return
            
        try:
            # 尝试解密
            key = self.get_encryption_key(password)
            cipher_suite = Fernet(key)
            
            db_name = f'finance_{self.current_user}.db'
            with open(db_name, 'rb') as f:
                encrypted_data = f.read()
                
            decrypted_data = cipher_suite.decrypt(encrypted_data)
            
            # 验证密码是否正确
            sqlite3.connect(':memory:').executescript(decrypted_data.decode('utf-8'))
            
            # 密码正确，移除加密
            with open(db_name, 'wb') as f:
                f.write(decrypted_data)
                
            # 移除用户密码
            self.master_cursor.execute(
                "UPDATE users SET password=NULL WHERE username=?",
                (self.current_user,)
            )
            self.master_conn.commit()
            
            self.db_encrypted = False
            self.cipher_suite = None
            self.statusBar().showMessage("✅ 数据库已解密", 5000)
            
            # 重新连接数据库
            self.close_current_db()
            self.init_current_user_db(self.current_user)
            self.load_data()
            
        except Exception as e:
            self.statusBar().showMessage(f"❌ 解密失败: 密码错误", 5000)

    def show_login_dialog(self):
        """显示登录对话框"""
        self.master_cursor.execute("SELECT username FROM users")
        users = [row[0] for row in self.master_cursor.fetchall()]
        
        login_dialog = LoginDialog(self)
        login_dialog.load_users(users)

        # 从主数据库中读取最后选择的用户
        try:
            self.master_cursor.execute("SELECT value FROM settings WHERE key='last_user'")
            last_user = self.master_cursor.fetchone()
            if last_user and last_user[0] in users:
                index = login_dialog.user_combo.findText(last_user[0])
                if index >= 0:
                    login_dialog.user_combo.setCurrentIndex(index)
        except sqlite3.OperationalError:
            # 如果settings表不存在，忽略错误
            pass
                    
        if login_dialog.exec_() == QDialog.Accepted:
            username = login_dialog.user_combo.currentText()
            new_user = login_dialog.new_user_edit.text().strip()
            password = login_dialog.password_edit.text()
            remember = login_dialog.remember_check.isChecked()
            
            if new_user:
                # 创建新用户
                try:
                    self.master_cursor.execute(
                        "INSERT INTO users (username, password) VALUES (?, ?)",
                        (new_user, password if remember else None)
                    )
                    self.master_conn.commit()
                    username = new_user
                except sqlite3.IntegrityError:
                    self.statusBar().showMessage("❌ 用户名已存在!", 5000) 
                    return self.show_login_dialog()

            # 保存最后选择的用户到主数据库
            try:
                self.master_cursor.execute(
                    "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                    ('last_user', username)
                )
                self.master_conn.commit()
            except sqlite3.OperationalError:
                # 如果settings表不存在，先创建表
                self.master_cursor.execute('''
                    CREATE TABLE IF NOT EXISTS settings (
                        key TEXT PRIMARY KEY,
                        value TEXT
                    )
                ''')
                self.master_conn.commit()
                # 再次尝试保存
                self.master_cursor.execute(
                    "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                    ('last_user', username)
                )
                self.master_conn.commit()
        
            self.init_current_user_db(username)
        else:
            sys.exit()

    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        # 用户管理
        user_action = QAction("切换用户", self)
        user_action.triggered.connect(self.switch_user)
        file_menu.addAction(user_action)
        
        # 数据库加密/解密
        encrypt_action = QAction("加密数据库", self)
        encrypt_action.triggered.connect(self.encrypt_database)
        file_menu.addAction(encrypt_action)
        
        decrypt_action = QAction("解密数据库", self)
        decrypt_action.triggered.connect(self.decrypt_database)
        file_menu.addAction(decrypt_action)
        
        # 备份操作
        backup_menu = file_menu.addMenu("备份")
        
        auto_backup_action = QAction("设置自动备份", self)
        auto_backup_action.triggered.connect(self.set_auto_backup)
        backup_menu.addAction(auto_backup_action)
        
        manual_backup_action = QAction("手动备份", self)
        manual_backup_action.triggered.connect(self.manual_backup)
        backup_menu.addAction(manual_backup_action)
        
        # 恢复操作
        restore_action = QAction("恢复数据", self)
        restore_action.triggered.connect(self.restore_data)
        file_menu.addAction(restore_action)
        
        # 导出数据
        export_menu = file_menu.addMenu("导出数据")
        
        export_csv_action = QAction("导出为CSV", self)
        export_csv_action.triggered.connect(self.export_to_csv)
        export_menu.addAction(export_csv_action)
        
        export_excel_action = QAction("导出为Excel", self)
        export_excel_action.triggered.connect(self.export_to_excel)
        export_menu.addAction(export_excel_action)
        
        # 退出操作
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu("编辑")
        
        # 撤销操作
        undo_action = QAction("撤销", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self.undo_last_operation)
        edit_menu.addAction(undo_action)
        
        # 分类管理
        category_action = QAction("管理分类", self)
        category_action.triggered.connect(self.manage_categories)
        edit_menu.addAction(category_action)
        
        # 账户管理
        account_action = QAction("管理账户", self)
        account_action.triggered.connect(self.manage_accounts)
        edit_menu.addAction(account_action)
        
        # 预算管理
        budget_action = QAction("管理预算", self)
        budget_action.triggered.connect(self.manage_budgets)
        edit_menu.addAction(budget_action)
        
        # 工具菜单
        tools_menu = menubar.addMenu("工具")
        
        # 汇率转换
        currency_action = QAction("汇率转换", self)
        currency_action.triggered.connect(self.currency_converter)
        tools_menu.addAction(currency_action)
        
        # 定期交易
        recurring_action = QAction("定期交易", self)
        recurring_action.triggered.connect(self.manage_recurring_transactions)
        tools_menu.addAction(recurring_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_tabs(self):
        """创建标签页"""
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)
        
        # 交易记录标签页
        self.transaction_tab = QWidget()
        self.tab_widget.addTab(self.transaction_tab, "交易记录")
        
        transaction_layout = QVBoxLayout()
        self.transaction_tab.setLayout(transaction_layout)
        
        # 确保table已创建
        if self.table is None:
            self.create_data_table()
        transaction_layout.addWidget(self.table)
        
        # 统计分析标签页
        self.stats_tab = QWidget()
        self.tab_widget.addTab(self.stats_tab, "统计分析")
        
        stats_layout = QVBoxLayout()
        self.stats_tab.setLayout(stats_layout)
        
        # 统计图表区域
        self.chart_view = QChartView()
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        stats_layout.addWidget(self.chart_view)
        
        # 统计文本区域
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        stats_layout.addWidget(self.stats_text)
        
        # 图表类型选择
        chart_type_layout = QHBoxLayout()
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems(["收支趋势", "分类占比", "借款还款", "预算执行"])
        self.chart_type_combo.currentIndexChanged.connect(self.update_statistics)
        chart_type_layout.addWidget(QLabel("图表类型:"))
        chart_type_layout.addWidget(self.chart_type_combo)
        
        # 时间范围选择
        self.stats_date_from = QDateEdit()
        self.stats_date_from.setDate(QDate.currentDate().addMonths(-1))
        self.stats_date_from.setCalendarPopup(True)
        self.stats_date_from.dateChanged.connect(self.update_statistics)
        chart_type_layout.addWidget(QLabel("从:"))
        chart_type_layout.addWidget(self.stats_date_from)
        
        self.stats_date_to = QDateEdit()
        self.stats_date_to.setDate(QDate.currentDate())
        self.stats_date_to.setCalendarPopup(True)
        self.stats_date_to.dateChanged.connect(self.update_statistics)
        chart_type_layout.addWidget(QLabel("到:"))
        chart_type_layout.addWidget(self.stats_date_to)
        
        stats_layout.addLayout(chart_type_layout)
        
        # 刷新统计按钮
        self.refresh_stats_btn = QPushButton("刷新统计")
        self.refresh_stats_btn.clicked.connect(self.update_statistics)
        stats_layout.addWidget(self.refresh_stats_btn)

    def create_search_bar(self):
        """创建搜索栏"""
        search_layout = QHBoxLayout()
        
        # 确保表格已创建
        if self.table is None:
            self.create_data_table()
    
        # 搜索框
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索描述、金额或分类...")
        self.search_edit.textChanged.connect(self.apply_filters)
        search_layout.addWidget(self.search_edit)
        
        # 类型筛选
        self.filter_type_combo = QComboBox()
        self.filter_type_combo.addItems(["所有类型", "收入", "支出", "借款", "还款"])
        self.filter_type_combo.currentIndexChanged.connect(self.apply_filters)
        search_layout.addWidget(QLabel("类型:"))
        search_layout.addWidget(self.filter_type_combo)
        
        # 分类筛选
        self.filter_category_combo = QComboBox()
        self.filter_category_combo.addItem("所有分类")
        self.filter_category_combo.currentIndexChanged.connect(self.apply_filters)
        search_layout.addWidget(QLabel("分类:"))
        search_layout.addWidget(self.filter_category_combo)
        
        # 账户筛选
        self.filter_account_combo = QComboBox()
        self.filter_account_combo.addItem("所有账户")
        self.filter_account_combo.currentIndexChanged.connect(self.apply_filters)
        search_layout.addWidget(QLabel("账户:"))
        search_layout.addWidget(self.filter_account_combo)
        
        # 状态筛选
        self.filter_status_combo = QComboBox()
        self.filter_status_combo.addItems(["所有状态", "待还款", "已结清"])
        self.filter_status_combo.currentIndexChanged.connect(self.apply_filters)
        search_layout.addWidget(QLabel("状态:"))
        search_layout.addWidget(self.filter_status_combo)

        # 日期范围选择
        self.date_range_combo = QComboBox()
        self.date_range_combo.addItems(["全部时间", "最近一周", "最近一月", "最近一年", "自定义"])
        self.date_range_combo.currentIndexChanged.connect(self.update_date_range)
        search_layout.addWidget(QLabel("时间范围:"))
        search_layout.addWidget(self.date_range_combo)

        # 日期范围
        self.date_from_edit = QDateEdit()
        self.date_from_edit.setDate(QDate.currentDate().addMonths(-1))
        self.date_from_edit.setCalendarPopup(True)
        self.date_from_edit.dateChanged.connect(self.apply_filters)
        search_layout.addWidget(QLabel("从:"))
        search_layout.addWidget(self.date_from_edit)
        
        self.date_to_edit = QDateEdit()
        self.date_to_edit.setDate(QDate.currentDate())
        self.date_to_edit.setCalendarPopup(True)
        self.date_to_edit.dateChanged.connect(self.apply_filters)
        search_layout.addWidget(QLabel("到:"))
        search_layout.addWidget(self.date_to_edit)
        
        self.main_layout.addLayout(search_layout)
        
        # 加载配置
        self.load_settings()
        
        # 加载分类数据
        self.load_categories()
        
        # 加载账户数据
        self.load_accounts()

    def load_categories(self):
        """加载分类数据到筛选框"""
        self.filter_category_combo.clear()
        self.filter_category_combo.addItem("所有分类")
        
        self.cursor.execute("SELECT DISTINCT name FROM categories ORDER BY name")
        categories = [row[0] for row in self.cursor.fetchall()]
        
        for category in categories:
            self.filter_category_combo.addItem(category)

    def load_accounts(self):
        """加载账户数据到筛选框"""
        self.filter_account_combo.clear()
        self.filter_account_combo.addItem("所有账户")
        
        self.cursor.execute("SELECT id, name FROM accounts ORDER BY name")
        accounts = self.cursor.fetchall()
        
        for account_id, account_name in accounts:
            self.filter_account_combo.addItem(account_name, account_id)

    def create_data_table(self):
        """创建数据表格"""
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels(["ID", "类型", "金额", "类别", "描述", "日期", "状态", "关联ID", "账户", "标签"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #e0e0e0;
                alternate-background-color: #f9f9f9;
            }
            QHeaderView::section {
                background-color: #4CAF50;
                color: white;
                padding: 5px;
                border: 1px solid #e0e0e0;
            }
            QTableWidget::item {
                padding: 5px;
            }
        """)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(4, 200)  # 描述列宽一些
        self.table.setColumnWidth(9, 150)  # 标签列宽一些

    def create_input_form(self):
        """创建输入表单"""
        form_layout = QHBoxLayout()
        
        # 类型选择
        self.type_combo = QComboBox()
        self.type_combo.addItems(["收入", "支出", "借款", "还款", "余额"])  # 添加"余额"选项
        form_layout.addWidget(QLabel("类型:"))
        form_layout.addWidget(self.type_combo)
        
        # 金额
        self.amount_edit = QLineEdit()
        self.amount_edit.setPlaceholderText("金额")
        form_layout.addWidget(QLabel("金额:"))
        form_layout.addWidget(self.amount_edit)
        
        # 类别
        self.category_combo = QComboBox()
        form_layout.addWidget(QLabel("类别:"))
        form_layout.addWidget(self.category_combo)
        
        # 账户选择
        self.account_combo = QComboBox()
        self.load_account_combo()
        form_layout.addWidget(QLabel("账户:"))
        form_layout.addWidget(self.account_combo)
        
        # 日期
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        form_layout.addWidget(QLabel("日期:"))
        form_layout.addWidget(self.date_edit)
        
        # 描述
        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("描述")
        form_layout.addWidget(QLabel("描述:"))
        form_layout.addWidget(self.desc_edit)
        
        # 标签
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("标签(逗号分隔)")
        form_layout.addWidget(QLabel("标签:"))
        form_layout.addWidget(self.tags_edit)
        
        # 关联借款选择（仅还款时显示）
        self.loan_combo = QComboBox()
        self.loan_combo.setVisible(False)
        form_layout.addWidget(QLabel("关联借款:"))
        form_layout.addWidget(self.loan_combo)
        
        # 收据图片按钮
        self.receipt_btn = QPushButton("添加收据")
        self.receipt_btn.clicked.connect(self.add_receipt_image)
        form_layout.addWidget(self.receipt_btn)
        
        # 定期交易复选框
        self.recurring_check = QCheckBox("定期交易")
        self.recurring_check.stateChanged.connect(self.toggle_recurring_fields)
        form_layout.addWidget(self.recurring_check)
        
        # 定期频率选择（默认隐藏）
        self.recurring_freq_combo = QComboBox()
        self.recurring_freq_combo.addItems(["每日", "每周", "每月", "每年"])
        self.recurring_freq_combo.setVisible(False)
        form_layout.addWidget(QLabel("频率:"))
        form_layout.addWidget(self.recurring_freq_combo)
        
        # 定期结束日期（默认隐藏）
        self.recurring_end_edit = QDateEdit()
        self.recurring_end_edit.setDate(QDate.currentDate().addYears(1))
        self.recurring_end_edit.setCalendarPopup(True)
        self.recurring_end_edit.setVisible(False)
        form_layout.addWidget(QLabel("结束于:"))
        form_layout.addWidget(self.recurring_end_edit)
        
        self.main_layout.addLayout(form_layout)
        
        # 类型改变时更新界面
        self.type_combo.currentTextChanged.connect(self.update_form)
        
        # 初始化类别
        self.update_category_combo()

        # 初始状态下如果是支出或借款类型，默认选择"其他"
        if self.type_combo.currentText() in ["支出", "借款"]:
            index = self.category_combo.findText("其他")
            if index >= 0:
                self.category_combo.setCurrentIndex(index)

    def load_account_combo(self):
        """加载账户下拉框"""
        self.account_combo.clear()
        self.cursor.execute("SELECT id, name FROM accounts ORDER BY name")
        accounts = self.cursor.fetchall()
        
        for account_id, account_name in accounts:
            self.account_combo.addItem(account_name, account_id)

    def toggle_recurring_fields(self, state):
        """显示/隐藏定期交易相关字段"""
        visible = state == Qt.Checked
        self.recurring_freq_combo.setVisible(visible)
        self.recurring_end_edit.setVisible(visible)
        
        # 调整标签位置
        for i in range(self.main_layout.count()):
            item = self.main_layout.itemAt(i)
            if item.widget() == self.recurring_freq_combo.parent():
                layout = item.layout()
                if layout:
                    for j in range(layout.count()):
                        widget = layout.itemAt(j).widget()
                        if widget and widget.text() in ["频率:", "结束于:"]:
                            widget.setVisible(visible)

    def add_receipt_image(self):
        """添加收据图片"""
        file_name, _ = QFileDialog.getOpenFileName(
            self, "选择收据图片", "", 
            "图片文件 (*.png *.jpg *.jpeg *.bmp)"
        )
        
        if file_name:
            try:
                # 压缩图片并转换为base64
                img = Image.open(file_name)
                img.thumbnail((800, 800))  # 限制图片大小
                
                buffered = io.BytesIO()
                img.save(buffered, format="JPEG", quality=70)
                img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
                
                # 显示缩略图
                pixmap = QPixmap(file_name)
                pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio)
                self.receipt_btn.setIcon(QIcon(pixmap))
                self.receipt_btn.setIconSize(QSize(100, 100))
                self.receipt_btn.setText("收据已添加")
                
                # 保存base64编码
                self.receipt_image_data = img_str
            except Exception as e:
                self.statusBar().showMessage(f"❌ 加载图片失败: {str(e)}", 5000)
                self.receipt_image_data = None

    def update_category_combo(self):
        """更新类别下拉框"""
        current_type = self.type_combo.currentText()
        type_map = {
            "收入": "income",
            "支出": "expense",
            "借款": "expense",  # 借款使用支出分类
            "还款": "income"   # 还款使用收入分类
        }
        db_type = type_map.get(current_type, "income")
        
        self.category_combo.clear()
        self.cursor.execute(
            "SELECT name FROM categories WHERE type=? ORDER BY name",
            (db_type,)
        )
        categories = [row[0] for row in self.cursor.fetchall()]
        
        # 确保"其他"类别总是可用
        if db_type == "expense" and "其他" not in categories:
            categories.append("其他")
        if db_type == "income" and "其他" not in categories:
            categories.append("其他")
            
        self.category_combo.addItems(categories)

        # 如果是支出或借款类型，默认选择"其他"类别
        if current_type in ["支出", "借款"] and "其他" in categories:
            index = self.category_combo.findText("其他")
            if index >= 0:
                self.category_combo.setCurrentIndex(index)

    def update_form(self, type_text):
        """根据选择的类型更新表单"""
        # 更新类别下拉框
        self.update_category_combo()
        
        # 显示/隐藏关联借款选择
        if type_text == "还款":
            self.loan_combo.setVisible(True)
            self.update_loan_combo()
        else:
            self.loan_combo.setVisible(False)
        
        # 如果是余额类型，禁用金额输入
        if type_text == "余额":
            self.amount_edit.setEnabled(False)
            self.amount_edit.clear()
        else:
            self.amount_edit.setEnabled(True)

    def update_loan_combo(self):
        """更新借款选择框"""
        self.loan_combo.clear()
        self.cursor.execute("""
            SELECT id, amount, description, date 
            FROM transactions 
            WHERE type='借款' AND status='pending'
            ORDER BY date
        """)
        loans = self.cursor.fetchall()
        
        if not loans:
            self.loan_combo.addItem("无待还款借款", None)
        else:
            for loan in loans:
                self.loan_combo.addItem(
                    f"ID:{loan[0]} 金额:{loan[1]} 日期:{loan[3]} 描述:{loan[2]}", 
                    loan[0]
                )

    def create_action_buttons(self):
        """创建操作按钮"""
        button_layout = QHBoxLayout()
        
        # 添加记录按钮
        self.add_button = QPushButton("添加记录")
        self.add_button.clicked.connect(self.add_record)
        button_layout.addWidget(self.add_button)
        
        # 删除记录按钮
        self.delete_button = QPushButton("删除记录")
        self.delete_button.clicked.connect(self.delete_record)
        button_layout.addWidget(self.delete_button)
        
        # 结算按钮（用于标记借款已还清）
        self.settle_button = QPushButton("标记为已结算")
        self.settle_button.clicked.connect(self.settle_record)
        button_layout.addWidget(self.settle_button)
        
        # 查看收据按钮
        self.view_receipt_btn = QPushButton("查看收据")
        self.view_receipt_btn.clicked.connect(self.view_receipt)
        self.view_receipt_btn.setEnabled(False)
        button_layout.addWidget(self.view_receipt_btn)
        
        # 刷新按钮
        self.refresh_button = QPushButton("刷新")
        self.refresh_button.clicked.connect(self.load_data)
        button_layout.addWidget(self.refresh_button)
        
        self.main_layout.addLayout(button_layout)

    def add_record(self):
        """添加新记录"""
        type_text = self.type_combo.currentText()
        amount_text = self.amount_edit.text().strip()
        category = self.category_combo.currentText()
        if not category:
            self.statusBar().showMessage("❌ 请选择类别!", 5000)
            self.category_combo.setFocus()
            return
        
        account_id = self.account_combo.currentData()
        date = self.date_edit.date().toString("yyyy-MM-dd")
        description = self.desc_edit.text().strip()
        tags = self.tags_edit.text().strip()
        is_recurring = self.recurring_check.isChecked()
        recurring_freq = self.recurring_freq_combo.currentText() if is_recurring else None
        recurring_end = self.recurring_end_edit.date().toString("yyyy-MM-dd") if is_recurring else None
        
        # 处理余额记录（特殊处理，不需要用户输入金额）
        if type_text == "余额":
            # 保存当前状态以便撤销
            self.save_state_before_change()
            
            # 计算截至该日期的余额
            self.cursor.execute("""
                SELECT 
                    SUM(CASE WHEN type='income' THEN amount ELSE 0 END) -
                    SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) +
                    SUM(CASE WHEN type='还款' THEN amount ELSE 0 END) -
                    SUM(CASE WHEN type='借款' THEN amount ELSE 0 END)
                FROM transactions
                WHERE date <= ? AND type != 'balance'
            """, (date,))
            
            amount = self.cursor.fetchone()[0] or 0
            
            # 添加余额记录
            self.cursor.execute('''
                INSERT INTO transactions 
                (type, amount, category, description, date, account_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', ('balance', amount, "余额统计", f"截至 {date} 的账户余额", date, account_id))
            self.conn.commit()
            
            self.statusBar().showMessage(f"✅ 余额记录已添加: {amount:.2f} 元", 5000)
            
            # 清空输入并刷新数据
            self.load_data()
            self.update_statistics()
            return
        
        # 对于非余额记录，验证金额输入
        if not amount_text:
            self.statusBar().showMessage("⚠️ 请输入金额!", 5000)
            self.amount_edit.setFocus()
            return
        
        try:
            amount = float(amount_text)
            if amount <= 0:
                self.statusBar().showMessage("❌ 金额必须大于0!", 5000)
                self.amount_edit.selectAll()
                self.amount_edit.setFocus()
                return
        except ValueError:
            self.statusBar().showMessage("❌ 金额必须是有效数字!", 5000)
            self.amount_edit.selectAll()
            self.amount_edit.setFocus()
            return
        
        # 日期不能晚于今天
        if self.date_edit.date() > QDate.currentDate():
            self.statusBar().showMessage("❌ 日期不能晚于今天!", 5000)
            self.date_edit.setFocus()
            return
        
        # 描述长度限制
        if len(description) > 100:
            self.statusBar().showMessage("❌ 描述不能超过100个字符!", 5000)
            self.desc_edit.selectAll()
            self.desc_edit.setFocus()
            return
        
        # 保存当前状态以便撤销
        self.save_state_before_change()
        
        # 根据类型处理
        if type_text == "借款":
            # 添加借款记录
            self.cursor.execute('''
                INSERT INTO transactions 
                (type, amount, category, description, date, status, account_id, tags, 
                 receipt_image, is_recurring, recurring_freq, recurring_end)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', ('借款', amount, category, description, date, 'pending', account_id, tags,
                  getattr(self, 'receipt_image_data', None), is_recurring, recurring_freq, recurring_end))
            self.conn.commit()
            
            self.statusBar().showMessage("✅ 借款记录已添加!", 5000)
        
        elif type_text == "还款":
            # 添加还款记录并关联借款
            loan_id = self.loan_combo.currentData()
            if not loan_id:
                self.statusBar().showMessage("❌ 没有可关联的借款!", 5000)
                return
            
            # 添加还款记录
            self.cursor.execute('''
                INSERT INTO transactions 
                (type, amount, category, description, date, related_id, account_id, tags, 
                 receipt_image, is_recurring, recurring_freq, recurring_end)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', ('还款', amount, category, description, date, loan_id, account_id, tags,
                  getattr(self, 'receipt_image_data', None), is_recurring, recurring_freq, recurring_end))
            
            # 检查是否还清
            self.cursor.execute('''
                SELECT SUM(amount) FROM transactions 
                WHERE type='还款' AND related_id=?
            ''', (loan_id,))
            total_repaid = self.cursor.fetchone()[0] or 0
            
            self.cursor.execute('''
                SELECT amount FROM transactions WHERE id=?
            ''', (loan_id,))
            loan_amount = self.cursor.fetchone()[0]
            
            if total_repaid >= loan_amount:
                # 标记借款为已结算
                self.cursor.execute('''
                    UPDATE transactions SET status='settled' WHERE id=?
                ''', (loan_id,))
                self.statusBar().showMessage("✅ 借款已全部还清!", 5000)
            else:
                self.statusBar().showMessage("✅ 还款记录已添加!", 5000)
            
            self.conn.commit()
        
        else:
            # 普通收入或支出
            db_type = 'income' if type_text == "收入" else 'expense'
            self.cursor.execute('''
                INSERT INTO transactions 
                (type, amount, category, description, date, account_id, tags, 
                 receipt_image, is_recurring, recurring_freq, recurring_end)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (db_type, amount, category, description, date, account_id, tags,
                  getattr(self, 'receipt_image_data', None), is_recurring, recurring_freq, recurring_end))
            self.conn.commit()
            
            self.statusBar().showMessage(f"✅ {type_text}记录已添加!", 5000)
        
        # 清空输入并刷新数据
        self.amount_edit.clear()
        self.desc_edit.clear()
        self.tags_edit.clear()
        self.receipt_btn.setIcon(QIcon())
        self.receipt_btn.setText("添加收据")
        self.receipt_image_data = None
        self.recurring_check.setChecked(False)
        
        # 更新账户余额
        self.update_account_balance(account_id)
        
        self.load_data()
        self.update_loan_combo()
        self.update_statistics()

    def update_account_balance(self, account_id):
        """更新账户余额"""
        if not account_id:
            return
            
        self.cursor.execute("""
            SELECT 
                SUM(CASE WHEN type='income' THEN amount ELSE 0 END) -
                SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) +
                SUM(CASE WHEN type='还款' THEN amount ELSE 0 END) -
                SUM(CASE WHEN type='借款' THEN amount ELSE 0 END)
            FROM transactions
            WHERE account_id=? AND type != 'balance'
        """, (account_id,))
        
        balance = self.cursor.fetchone()[0] or 0
        
        self.cursor.execute("""
            UPDATE accounts SET balance=? WHERE id=?
        """, (balance, account_id))
        self.conn.commit()

    def delete_record(self):
        """删除选中的记录(支持多选)"""
        selected_rows = set()
        for item in self.table.selectedItems():
            selected_rows.add(item.row())
        
        if not selected_rows:
            self.statusBar().showMessage("❌ 请选择要删除的记录!", 5000)
            return
        
        # 收集所有选中的记录ID
        record_ids = []
        account_ids = set()
        for row in selected_rows:
            record_id = int(self.table.item(row, 0).text())
            record_ids.append(record_id)
            
            # 获取账户ID
            account_item = self.table.item(row, 8)
            if account_item:
                account_id = account_item.data(Qt.UserRole)
                if account_id:
                    account_ids.add(account_id)
        
        # 检查是否有借款记录且有未还清的还款
        self.cursor.execute(f'''
            SELECT id, type, status FROM transactions 
            WHERE id IN ({','.join(['?']*len(record_ids))})
        ''', record_ids)
        
        pending_loans = []
        for record_id, record_type, status in self.cursor.fetchall():
            if record_type == '借款' and status == 'pending':
                pending_loans.append(str(record_id))
        
        if pending_loans:
            self.statusBar().showMessage(f"❌ 不能删除未还清的借款记录(ID: {', '.join(pending_loans)})!", 5000)
            return
        
        # 确认删除
        reply = QMessageBox.question(
            self, '确认', 
            f'确定要删除这 {len(record_ids)} 条记录吗?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 保存当前状态以便撤销
            self.save_state_before_change()
            
            # 获取所有还款记录的关联ID
            self.cursor.execute(f'''
                SELECT DISTINCT related_id FROM transactions 
                WHERE id IN ({','.join(['?']*len(record_ids))}) 
                AND related_id IS NOT NULL
            ''', record_ids)
            related_ids = [row[0] for row in self.cursor.fetchall() if row[0] is not None]
            
            # 删除记录
            self.cursor.execute(f'''
                DELETE FROM transactions 
                WHERE id IN ({','.join(['?']*len(record_ids))})
            ''', record_ids)
            
            # 更新关联借款状态
            for loan_id in related_ids:
                if loan_id:  # 确保loan_id不为None
                    self.update_loan_status(loan_id)
            
            self.conn.commit()
            
            # 更新账户余额
            for account_id in account_ids:
                self.update_account_balance(account_id)
            
            self.load_data()
            self.update_loan_combo()
            self.update_statistics()

    def update_loan_status(self, loan_id):
        """更新借款状态"""
        if not loan_id:  # 如果loan_id为空或None，直接返回
            return
        
        # 计算已还款总额
        self.cursor.execute('''
            SELECT SUM(amount) FROM transactions 
            WHERE type='还款' AND related_id=?
        ''', (loan_id,))
        total_repaid_result = self.cursor.fetchone()
        total_repaid = total_repaid_result[0] if total_repaid_result and total_repaid_result[0] is not None else 0
        
        # 获取借款金额
        self.cursor.execute('''
            SELECT amount FROM transactions WHERE id=?
        ''', (loan_id,))
        loan_amount_result = self.cursor.fetchone()
        
        # 如果找不到借款记录，直接返回
        if not loan_amount_result:
            return
        
        loan_amount = loan_amount_result[0]
        
        new_status = 'settled' if total_repaid >= loan_amount else 'pending'
        
        self.cursor.execute('''
            UPDATE transactions SET status=? WHERE id=?
        ''', (new_status, loan_id))
        self.conn.commit()

    def settle_record(self):
        """标记记录为已结算"""
        selected = self.table.selectedItems()
        if not selected:
            self.statusBar().showMessage("❌ 请选择要结算的记录!", 5000)
            return
        
        row = selected[0].row()
        record_id = int(self.table.item(row, 0).text())
        
        # 检查是否是借款记录
        self.cursor.execute('''
            SELECT type FROM transactions WHERE id=?
        ''', (record_id,))
        record_type = self.cursor.fetchone()[0]
        
        if record_type != '借款':
            self.statusBar().showMessage("❌ 只能结算借款记录!", 5000)
            return
        
        # 保存当前状态以便撤销
        self.save_state_before_change()
        
        # 标记为已结算
        self.cursor.execute('''
            UPDATE transactions SET status='settled' WHERE id=?
        ''', (record_id,))
        self.conn.commit()
        
        self.statusBar().showMessage("✅ 借款记录已标记为已结清!", 5000)
        self.load_data()
        self.update_loan_combo()
        self.update_statistics()

    def view_receipt(self):
        """查看收据图片"""
        selected = self.table.selectedItems()
        if not selected:
            self.statusBar().showMessage("❌ 请选择一条记录!", 5000)
            return
        
        row = selected[0].row()
        record_id = int(self.table.item(row, 0).text())
        
        self.cursor.execute('''
            SELECT receipt_image FROM transactions WHERE id=?
        ''', (record_id,))
        receipt_data = self.cursor.fetchone()[0]
        
        if not receipt_data:
            self.statusBar().showMessage("❌ 该记录没有收据图片!", 5000)
            return
            
        try:
            # 解码base64图片数据
            img_data = base64.b64decode(receipt_data)
            img = Image.open(io.BytesIO(img_data))
            
            # 创建临时文件
            temp_file = "temp_receipt.jpg"
            img.save(temp_file, "JPEG")
            
            # 显示图片
            os.startfile(temp_file)
        except Exception as e:
            self.statusBar().showMessage(f"❌ 显示收据失败: {str(e)}", 5000)

    def apply_filters(self):
        """应用筛选条件"""
        # 确保表格已初始化
        if not hasattr(self, 'table') or self.table is None:
            self.create_data_table()
            if not hasattr(self, 'table') or self.table is None:
                return
        
        search_text = self.search_edit.text().strip().lower()
        filter_type = self.filter_type_combo.currentText()
        filter_category = self.filter_category_combo.currentText()
        filter_account = self.filter_account_combo.currentData()
        filter_status = self.filter_status_combo.currentText()
        
        # 构建基础查询
        query = """
            SELECT t.id, t.type, t.amount, t.category, t.description, t.date, 
                CASE WHEN t.status IS NULL THEN '' ELSE t.status END,
                CASE WHEN t.related_id IS NULL THEN '' ELSE t.related_id END,
                a.name, t.tags
            FROM transactions t
            LEFT JOIN accounts a ON t.account_id = a.id
        """
        
        # 构建WHERE条件
        conditions = []
        params = []
        
        # 日期条件（如果不是"全部时间"）
        if self.date_range_combo.currentIndex() != 0:  # 不是"全部时间"
            date_from = self.date_from_edit.date().toString("yyyy-MM-dd")
            date_to = self.date_to_edit.date().toString("yyyy-MM-dd")
            conditions.append("t.date BETWEEN ? AND ?")
            params.extend([date_from, date_to])
        
        # 类型筛选
        if filter_type != "所有类型":
            type_map = {
                "收入": "income",
                "支出": "expense",
                "借款": "借款",
                "还款": "还款"
            }
            conditions.append("t.type=?")
            params.append(type_map[filter_type])
        
        # 分类筛选
        if filter_category != "所有分类":
            conditions.append("t.category=?")
            params.append(filter_category)
        
        # 账户筛选
        if filter_account:
            conditions.append("t.account_id=?")
            params.append(filter_account)
        
        # 状态筛选
        if filter_status == "待还款":
            conditions.append("t.status='pending'")
        elif filter_status == "已结清":
            conditions.append("t.status='settled'")
        
        # 搜索文本筛选
        if search_text:
            # 支持中文、拼音首字母和英文搜索
            search_conditions = []
            search_params = []
            
            # 1. 直接匹配描述
            search_conditions.append("t.description LIKE ?")
            search_params.append(f"%{search_text}%")
            
            # 2. 匹配金额
            search_conditions.append("CAST(t.amount AS TEXT) LIKE ?")
            search_params.append(f"%{search_text}%")
            
            # 3. 匹配分类
            search_conditions.append("t.category LIKE ?")
            search_params.append(f"%{search_text}%")
            
            # 4. 匹配标签
            search_conditions.append("t.tags LIKE ?")
            search_params.append(f"%{search_text}%")
            
            # 5. 匹配账户名
            search_conditions.append("a.name LIKE ?")
            search_params.append(f"%{search_text}%")
            
            # 6. 拼音首字母匹配
            # 获取所有描述和分类的拼音首字母
            self.cursor.execute("SELECT DISTINCT description FROM transactions")
            descriptions = [row[0] for row in self.cursor.fetchall()]
            
            self.cursor.execute("SELECT DISTINCT category FROM transactions")
            categories = [row[0] for row in self.cursor.fetchall()]
            
            # 检查是否有匹配的拼音首字母
            pinyin_descriptions = [
                desc for desc in descriptions 
                if desc and self.get_pinyin_abbr(desc).startswith(search_text)
            ]
            
            pinyin_categories = [
                cat for cat in categories 
                if cat and self.get_pinyin_abbr(cat).startswith(search_text)
            ]
            
            if pinyin_descriptions or pinyin_categories:
                pinyin_condition = []
                pinyin_params = []
                
                if pinyin_descriptions:
                    pinyin_condition.append("t.description IN (" + ",".join(["?"]*len(pinyin_descriptions)) + ")")
                    pinyin_params.extend(pinyin_descriptions)
                    
                if pinyin_categories:
                    if pinyin_descriptions:
                        pinyin_condition.append("OR")
                    pinyin_condition.append("t.category IN (" + ",".join(["?"]*len(pinyin_categories)) + ")")
                    pinyin_params.extend(pinyin_categories)
                
                search_conditions.append("(" + " ".join(pinyin_condition) + ")")
                search_params.extend(pinyin_params)
            
            conditions.append("(" + " OR ".join(search_conditions) + ")")
            params.extend(search_params)
        
        # 组合所有条件
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        # 排序
        query += " ORDER BY t.date ASC, t.id ASC"
        
        # 执行查询
        self.cursor.execute(query, params)
        records = self.cursor.fetchall()
        
        # 更新表格
        self.table.setRowCount(len(records))
        for row, record in enumerate(records):
            for col, value in enumerate(record):
                item = QTableWidgetItem(str(value) if value is not None else "")
                item.setTextAlignment(Qt.AlignCenter)
                
                # 根据类型设置颜色
                if col == 1:  # 类型列
                    if value == 'income':
                        item.setText("收入")
                        item.setForeground(Qt.darkGreen)
                        item.setBackground(MacaronColors.MINT_GREEN)
                    elif value == 'expense':
                        item.setText("支出")
                        item.setForeground(Qt.darkRed)
                        item.setBackground(MacaronColors.ROSE_PINK)
                    elif value == '借款':
                        item.setForeground(Qt.darkBlue)
                        item.setBackground(MacaronColors.LAVENDER)
                    elif value == '还款':
                        item.setForeground(Qt.darkMagenta)
                        item.setBackground(MacaronColors.SKY_BLUE)
                    elif value == 'balance':
                        item.setText("余额")
                        item.setForeground(Qt.darkYellow)
                        item.setBackground(MacaronColors.BUTTER_CREAM)  # 使用奶油黄背景
                
                # 状态列颜色
                if col == 6:  # 状态列
                    if value == 'pending':
                        item.setText("待还款")
                        item.setBackground(MacaronColors.LEMON_YELLOW)  # 柠檬黄背景
                    elif value == 'settled':
                        item.setText("已结清")
                        item.setBackground(MacaronColors.APPLE_GREEN)   # 苹果绿背景

                # 金额列右对齐
                if col == 2:
                    try:
                        # 将金额格式化为保留2位小数
                        formatted_amount = "{:.2f}".format(float(value))
                        item.setText(formatted_amount)
                    except (ValueError, TypeError):
                        item.setText(str(value))
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                
                # 账户列存储账户ID
                if col == 8 and record[8]:
                    item.setData(Qt.UserRole, self.filter_account_combo.findText(record[8]))
                
                self.table.setItem(row, col, item)
        
        # 如果有选中的行，启用查看收据按钮
        if hasattr(self, 'view_receipt_btn'):  # 添加属性检查
            if self.table.selectedItems():
                selected_row = self.table.selectedItems()[0].row()
                record_id = int(self.table.item(selected_row, 0).text())
                self.cursor.execute('''
                    SELECT receipt_image FROM transactions WHERE id=?
                ''', (record_id,))
                receipt_data = self.cursor.fetchone()[0]
                self.view_receipt_btn.setEnabled(bool(receipt_data))
            else:
                self.view_receipt_btn.setEnabled(False)
        
        self.table.resizeColumnsToContents()

    def get_pinyin_abbr(self, text):
        """获取中文文本的拼音首字母缩写"""
        if not text:
            return ""
        
        # 只处理中文字符
        abbr = []
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                # 中文字符，获取拼音首字母
                pinyin = pypinyin.lazy_pinyin(char)
                if pinyin and pinyin[0]:
                    abbr.append(pinyin[0][0].lower())
            else:
                # 非中文字符，直接保留
                abbr.append(char.lower())
        
        return "".join(abbr)

    def load_data(self):
        """加载数据"""
        if not hasattr(self, 'table') or self.table is None:
            self.create_data_table()
        self.apply_filters()  # 这里会应用颜色设置
        # 确保表格刷新
        self.table.viewport().update()

    def update_statistics(self):
        """更新统计信息"""
        date_from = self.stats_date_from.date().toString("yyyy-MM-dd")
        date_to = self.stats_date_to.date().toString("yyyy-MM-dd")
        chart_type = self.chart_type_combo.currentText()
        
        # 创建图表
        chart = QChart()
        chart.setTitle(f"统计图表 - {date_from} 至 {date_to}")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        stats_html = f"""
        <html>
        <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            h2 {{ color: #2c3e50; }}
            table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #4CAF50; color: white; }}
            tr:nth-child(even) {{ background-color: #f2f2f2; }}
            .positive {{ color: green; }}
            .negative {{ color: red; }}
            .chart-container {{ margin: 20px 0; }}
            .budget-over {{ background-color: #ffdddd; }}
            .budget-under {{ background-color: #ddffdd; }}
        </style>
        </head>
        <body>
        <h2>统计时间段: {date_from} 至 {date_to}</h2>
        """
        
        # 收支总额统计
        self.cursor.execute("""
            SELECT 
                SUM(CASE WHEN type='income' THEN amount ELSE 0 END),
                SUM(CASE WHEN type='expense' THEN amount ELSE 0 END),
                SUM(CASE WHEN type='借款' THEN amount ELSE 0 END),
                SUM(CASE WHEN type='还款' THEN amount ELSE 0 END)
            FROM transactions
            WHERE date BETWEEN ? AND ?
            AND type != 'balance'  -- 排除余额记录
        """, (date_from, date_to))
        
        total_income, total_expense, total_loans, total_repayments = self.cursor.fetchone()
        total_income = total_income or 0
        total_expense = total_expense or 0
        total_loans = total_loans or 0
        total_repayments = total_repayments or 0
        
        net_income = total_income + total_repayments - total_expense - total_loans
        
        stats_html += f"""
        <h3>收支总览</h3>
        <table>
            <tr><th>项目</th><th>金额</th></tr>
            <tr><td>总收入</td><td>{total_income:.2f} 元</td></tr>
            <tr><td>总支出</td><td>{total_expense:.2f} 元</td></tr>
            <tr><td>总借款</td><td>{total_loans:.2f} 元</td></tr>
            <tr><td>总还款</td><td>{total_repayments:.2f} 元</td></tr>
            <tr><td><b>净收入</b></td>
                <td class="{'positive' if net_income >= 0 else 'negative'}">
                    {net_income:.2f} 元
                </td>
            </tr>
        </table>
        """
        
        # 待还款统计
        self.cursor.execute("""
            SELECT SUM(t1.amount - IFNULL(t2.repaid, 0)) 
            FROM transactions t1
            LEFT JOIN (
                SELECT related_id, SUM(amount) as repaid 
                FROM transactions 
                WHERE type='还款' 
                GROUP BY related_id
            ) t2 ON t1.id = t2.related_id
            WHERE t1.type='借款' AND t1.status='pending'
            AND t1.date BETWEEN ? AND ?
        """, (date_from, date_to))
        
        pending_repayment = self.cursor.fetchone()[0] or 0
        
        stats_html += f"""
        <h3>借款状态</h3>
        <table>
            <tr><th>项目</th><th>金额</th></tr>
            <tr><td>总借款</td><td>{total_loans:.2f} 元</td></tr>
            <tr><td>已还款</td><td>{total_repayments:.2f} 元</td></tr>
            <tr><td>待还款</td><td>{pending_repayment:.2f} 元</td></tr>
        </table>
        """
        
        # 按类别统计
        if chart_type in ["收支趋势", "分类占比"]:
            self.cursor.execute("""
                SELECT 
                    category,
                    SUM(CASE WHEN type='income' THEN amount ELSE 0 END) as income,
                    SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) as expense
                FROM transactions
                WHERE date BETWEEN ? AND ?
                GROUP BY category
                ORDER BY (income + expense) DESC
            """, (date_from, date_to))
            
            category_stats = self.cursor.fetchall()
            
            stats_html += """
            <h3>分类统计</h3>
            <table>
                <tr><th>类别</th><th>收入</th><th>支出</th><th>合计</th></tr>
            """
            
            for category, income, expense in category_stats:
                total = income - expense
                stats_html += f"""
                <tr>
                    <td>{category}</td>
                    <td>{income:.2f}</td>
                    <td>{expense:.2f}</td>
                    <td class="{'positive' if total >= 0 else 'negative'}">
                        {total:.2f}
                    </td>
                </tr>
                """
            
            stats_html += "</table>"
            
            # 创建饼图或柱状图
            if chart_type == "分类占比":
                series = QPieSeries()
                for category, income, expense in category_stats:
                    if expense > 0:  # 只显示支出分类
                        series.append(category, expense)
                
                chart.addSeries(series)
                chart.setTitle("支出分类占比")
            else:
                # 收支趋势柱状图
                bar_series = QBarSeries()
                
                # 收入柱
                income_set = QBarSet("收入")
                for category, income, expense in category_stats:
                    income_set.append(income)
                bar_series.append(income_set)
                
                # 支出柱
                expense_set = QBarSet("支出")
                for category, income, expense in category_stats:
                    expense_set.append(expense)
                bar_series.append(expense_set)
                
                chart.addSeries(bar_series)
                
                # 设置X轴
                axis_x = QBarCategoryAxis()
                axis_x.append([category for category, income, expense in category_stats])
                chart.addAxis(axis_x, Qt.AlignBottom)
                bar_series.attachAxis(axis_x)
                
                # 设置Y轴
                axis_y = QValueAxis()
                if category_stats:  # 检查是否有数据
                    max_value = max(max(income for _, income, _ in category_stats), 
                                max(expense for _, _, expense in category_stats))
                else:
                    max_value = 100  # 设置一个默认值，避免空序列错误
                axis_y.setRange(0, max_value * 1.1)
                chart.addAxis(axis_y, Qt.AlignLeft)
                bar_series.attachAxis(axis_y)
                
                chart.setTitle("收支趋势")
        
        # 借款还款明细
        if chart_type == "借款还款":
            self.cursor.execute("""
                SELECT id, amount, description, date, status
                FROM transactions
                WHERE type='借款' AND date BETWEEN ? AND ?
                ORDER BY date ASC
            """, (date_from, date_to))
            
            loans = self.cursor.fetchall()
            
            if loans:
                stats_html += """
                <h3>借款明细</h3>
                <table>
                    <tr><th>ID</th><th>金额</th><th>描述</th><th>日期</th><th>状态</th><th>已还款</th></tr>
                """
                
                loan_ids = []
                loan_amounts = []
                repaid_amounts = []
                
                for loan in loans:
                    loan_id, amount, desc, date, status = loan
                    loan_ids.append(str(loan_id))
                    loan_amounts.append(amount)
                    
                    # 状态显示为中文
                    status_text = "待还款" if status == "pending" else "已结清" if status == "settled" else status

                    self.cursor.execute("""
                        SELECT SUM(amount) FROM transactions
                        WHERE type='还款' AND related_id=?
                    """, (loan_id,))
                    repaid = self.cursor.fetchone()[0] or 0
                    repaid_amounts.append(repaid)
                    
                    stats_html += f"""
                    <tr>
                        <td>{loan_id}</td>
                        <td>{amount:.2f}</td>
                        <td>{desc}</td>
                        <td>{date}</td>
                        <td>{status_text}</td>
                        <td>{repaid:.2f}</td>
                    </tr>
                    """
                
                stats_html += "</table>"
                
                # 创建借款还款柱状图
                bar_series = QBarSeries()
                
                # 借款柱
                loan_set = QBarSet("借款金额")
                for amount in loan_amounts:
                    loan_set.append(amount)
                bar_series.append(loan_set)
                
                # 还款柱
                repaid_set = QBarSet("已还款")
                for repaid in repaid_amounts:
                    repaid_set.append(repaid)
                bar_series.append(repaid_set)
                
                chart.addSeries(bar_series)
                
                # 设置X轴
                axis_x = QBarCategoryAxis()
                axis_x.append(loan_ids)
                chart.addAxis(axis_x, Qt.AlignBottom)
                bar_series.attachAxis(axis_x)
                
                # 设置Y轴
                axis_y = QValueAxis()
                max_value = max(max(loan_amounts), max(repaid_amounts))
                axis_y.setRange(0, max_value * 1.1)
                chart.addAxis(axis_y, Qt.AlignLeft)
                bar_series.attachAxis(axis_y)
                
                chart.setTitle("借款还款情况")
        
        # 预算执行情况
        if chart_type == "预算执行":
            # 获取当前月份
            current_month = QDate.currentDate().toString("yyyy-MM")
            
            # 获取预算数据
            self.cursor.execute("""
                SELECT category, amount FROM budgets
                WHERE month=?
            """, (current_month,))
            budgets = {row[0]: row[1] for row in self.cursor.fetchall()}
            
            # 获取实际支出
            self.cursor.execute("""
                SELECT category, SUM(amount) 
                FROM transactions 
                WHERE type='expense' AND strftime('%Y-%m', date)=?
                GROUP BY category
            """, (current_month,))
            expenses = {row[0]: row[1] for row in self.cursor.fetchall()}
            
            # 合并所有分类
            all_categories = set(budgets.keys()).union(set(expenses.keys()))
            
            if all_categories:
                stats_html += f"""
                <h3>{current_month} 预算执行情况</h3>
                <table>
                    <tr><th>分类</th><th>预算</th><th>实际支出</th><th>差额</th><th>完成度</th></tr>
                """
                
                budget_data = []
                expense_data = []
                categories = []
                
                for category in sorted(all_categories):
                    budget = budgets.get(category, 0)
                    expense = expenses.get(category, 0)
                    diff = budget - expense
                    percentage = (expense / budget * 100) if budget > 0 else 0
                    
                    row_class = "budget-over" if expense > budget else "budget-under"
                    
                    stats_html += f"""
                    <tr class="{row_class}">
                        <td>{category}</td>
                        <td>{budget:.2f}</td>
                        <td>{expense:.2f}</td>
                        <td>{diff:.2f}</td>
                        <td>{percentage:.1f}%</td>
                    </tr>
                    """
                    
                    budget_data.append(budget)
                    expense_data.append(expense)
                    categories.append(category)
                
                stats_html += "</table>"
                
                # 创建预算执行柱状图
                bar_series = QBarSeries()
                
                # 预算柱
                budget_set = QBarSet("预算")
                for amount in budget_data:
                    budget_set.append(amount)
                bar_series.append(budget_set)
                
                # 支出柱
                expense_set = QBarSet("实际支出")
                for amount in expense_data:
                    expense_set.append(amount)
                bar_series.append(expense_set)
                
                chart.addSeries(bar_series)
                
                # 设置X轴
                axis_x = QBarCategoryAxis()
                axis_x.append(categories)
                chart.addAxis(axis_x, Qt.AlignBottom)
                bar_series.attachAxis(axis_x)
                
                # 设置Y轴
                axis_y = QValueAxis()
                max_value = max(max(budget_data), max(expense_data))
                axis_y.setRange(0, max_value * 1.1)
                chart.addAxis(axis_y, Qt.AlignLeft)
                bar_series.attachAxis(axis_y)
                
                chart.setTitle("预算执行情况")
        
        stats_html += """
        </body>
        </html>
        """
        
        self.stats_text.setHtml(stats_html)
        self.chart_view.setChart(chart)

    def switch_user(self):
        """切换用户"""
        # 保存当前用户到主数据库
        if hasattr(self, 'current_user'):
            self.master_cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                ('last_user', self.current_user)
            )
            self.master_conn.commit()
        
        self.close_current_db()
        self.show_login_dialog()
        
        # 重新初始化界面
        self.create_menu_bar()
        self.create_search_bar()
        self.create_tabs()
        self.create_input_form()
        self.create_action_buttons()
        self.load_data()
        self.update_statistics()

    def close_current_db(self):
        """关闭当前用户数据库"""
        if hasattr(self, 'conn'):
            # 如果是加密数据库，保存加密数据
            if self.db_encrypted:
                # 导出内存数据库到文件
                db_name = f'finance_{self.current_user}.db'
                with open(db_name, 'wb') as f:
                    # 获取所有数据
                    temp_conn = sqlite3.connect(':memory:')
                    temp_cursor = temp_conn.cursor()
                    
                    # 获取所有数据
                    temp_cursor.execute("SELECT sql FROM sqlite_master WHERE type='table'")
                    schema = "\n".join([row[0] for row in temp_cursor.fetchall()])
                    
                    # 获取所有数据
                    data_dump = []
                    temp_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in temp_cursor.fetchall()]
                    
                    for table in tables:
                        temp_cursor.execute(f"SELECT * FROM {table}")
                        data = temp_cursor.fetchall()
                        columns = [desc[0] for desc in temp_cursor.description]
                        
                        for row in data:
                            values = ", ".join([f"'{str(v)}'" if v is not None else "NULL" for v in row])
                            data_dump.append(f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({values});")
                    
                    temp_conn.close()
                    
                    # 合并模式和数据进行加密
                    full_dump = schema + "\n" + "\n".join(data_dump)
                    encrypted_data = self.cipher_suite.encrypt(full_dump.encode('utf-8'))
                    f.write(encrypted_data)
            
            self.conn.close()

    def auto_backup(self):
        """自动备份数据"""
        backup_dir = "backups"
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        backup_name = f"{backup_dir}/finance_{self.current_user}_auto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        try:
            if self.db_encrypted:
                # 对于加密数据库，我们已经将数据保存在内存中
                pass
            else:
                shutil.copy2(f'finance_{self.current_user}.db', backup_name)
            print(f"自动备份成功: {backup_name}")
        except Exception as e:
            print(f"自动备份失败: {str(e)}")

    def manual_backup(self):
        """手动备份数据"""
        backup_dir = "backups"
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        backup_name = f"{backup_dir}/finance_{self.current_user}_manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        try:
            if self.db_encrypted:
                # 导出内存数据库
                with open(backup_name, 'wb') as f:
                    # 获取所有数据
                    temp_conn = sqlite3.connect(':memory:')
                    temp_cursor = temp_conn.cursor()
                    
                    # 获取所有数据
                    temp_cursor.execute("SELECT sql FROM sqlite_master WHERE type='table'")
                    schema = "\n".join([row[0] for row in temp_cursor.fetchall()])
                    
                    # 获取所有数据
                    data_dump = []
                    temp_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in temp_cursor.fetchall()]
                    
                    for table in tables:
                        temp_cursor.execute(f"SELECT * FROM {table}")
                        data = temp_cursor.fetchall()
                        columns = [desc[0] for desc in temp_cursor.description]
                        
                        for row in data:
                            values = ", ".join([f"'{str(v)}'" if v is not None else "NULL" for v in row])
                            data_dump.append(f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({values});")
                    
                    temp_conn.close()
                    
                    # 合并模式和数据进行加密
                    full_dump = schema + "\n" + "\n".join(data_dump)
                    encrypted_data = self.cipher_suite.encrypt(full_dump.encode('utf-8'))
                    f.write(encrypted_data)
            else:
                shutil.copy2(f'finance_{self.current_user}.db', backup_name)
            self.statusBar().showMessage(f"✅ 数据已备份为: {backup_name}", 5000)
        except Exception as e:
            self.statusBar().showMessage(f"❌ 备份失败: {str(e)}", 5000)

    def set_auto_backup(self):
        """设置自动备份间隔"""
        intervals = {
            "每小时": 3600000,
            "每天": 86400000,
            "每周": 604800000
        }
        
        interval, ok = QInputDialog.getItem(
            self, "设置自动备份", "选择自动备份间隔:",
            intervals.keys(), 0, False
        )
        
        if ok and interval:
            self.backup_timer.setInterval(intervals[interval])
            self.statusBar().showMessage(f"✅ 已设置为{interval}自动备份", 5000)

    def restore_data(self):
        """恢复数据库"""
        backup_dir = "backups"
        if not os.path.exists(backup_dir):
            self.statusBar().showMessage("⚠️ 备份目录不存在!", 5000)
            return
        
        file_name, _ = QFileDialog.getOpenFileName(
            self, "选择备份文件", backup_dir, 
            f"{self.current_user}的备份文件 (*finance_{self.current_user}_*.db)"
        )
        
        if file_name:
            reply = QMessageBox.question(
                self, '确认', '恢复数据将覆盖当前数据，确定要继续吗?',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                try:
                    self.close_current_db()
                    
                    if self.db_encrypted:
                        # 对于加密数据库，需要先解密备份
                        with open(file_name, 'rb') as f:
                            encrypted_data = f.read()
                        decrypted_data = self.cipher_suite.decrypt(encrypted_data)
                        
                        # 创建内存数据库
                        self.conn = sqlite3.connect(':memory:')
                        self.conn.executescript(decrypted_data.decode('utf-8'))
                    else:
                        shutil.copy2(file_name, f'finance_{self.current_user}.db')
                        self.conn = sqlite3.connect(f'finance_{self.current_user}.db')
                    
                    self.cursor = self.conn.cursor()
                    self.load_data()
                    self.update_statistics()
                    self.statusBar().showMessage("✅ 数据恢复成功!", 5000)
                except Exception as e:
                    self.statusBar().showMessage(f"❌ 恢复失败: {str(e)}", 5000)
                    self.conn = sqlite3.connect(f'finance_{self.current_user}.db')
                    self.cursor = self.conn.cursor()

    def save_state_before_change(self):
        """保存当前数据库状态以便撤销"""
        # 只保留最近的10次操作记录
        if len(self.operation_stack) >= 10:
            oldest_file = self.operation_stack.pop(0)
            try:
                os.remove(oldest_file)
            except:
                pass
        
        # 保存当前数据库状态
        backup_file = f"temp_undo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        
        if self.db_encrypted:
            # 导出内存数据库
            with open(backup_file, 'wb') as f:
                # 获取所有数据
                temp_conn = sqlite3.connect(':memory:')
                temp_cursor = temp_conn.cursor()
                
                # 获取所有数据
                temp_cursor.execute("SELECT sql FROM sqlite_master WHERE type='table'")
                schema = "\n".join([row[0] for row in temp_cursor.fetchall()])
                
                # 获取所有数据
                data_dump = []
                temp_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in temp_cursor.fetchall()]
                
                for table in tables:
                    temp_cursor.execute(f"SELECT * FROM {table}")
                    data = temp_cursor.fetchall()
                    columns = [desc[0] for desc in temp_cursor.description]
                    
                    for row in data:
                        values = ", ".join([f"'{str(v)}'" if v is not None else "NULL" for v in row])
                        data_dump.append(f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({values});")
                
                temp_conn.close()
                
                # 合并模式和数据进行加密
                full_dump = schema + "\n" + "\n".join(data_dump)
                encrypted_data = self.cipher_suite.encrypt(full_dump.encode('utf-8'))
                f.write(encrypted_data)
        else:
            shutil.copy2(f'finance_{self.current_user}.db', backup_file)
        
        self.operation_stack.append(backup_file)

    def undo_last_operation(self):
        """撤销最后一次操作"""
        if not self.operation_stack:
            self.statusBar().showMessage("❌ 没有可撤销的操作!", 5000)
            return
        
        backup_file = self.operation_stack.pop()
        
        try:
            self.close_current_db()
            
            if self.db_encrypted:
                # 解密备份文件
                with open(backup_file, 'rb') as f:
                    encrypted_data = f.read()
                decrypted_data = self.cipher_suite.decrypt(encrypted_data)
                
                # 创建内存数据库
                self.conn = sqlite3.connect(':memory:')
                self.conn.executescript(decrypted_data.decode('utf-8'))
            else:
                shutil.copy2(backup_file, f'finance_{self.current_user}.db')
                self.conn = sqlite3.connect(f'finance_{self.current_user}.db')
            
            self.cursor = self.conn.cursor()
            self.load_data()
            self.update_statistics()
            self.statusBar().showMessage("✅ 已撤销最后一次操作!", 5000)
            
            # 删除临时文件
            os.remove(backup_file)
        except Exception as e:
            self.statusBar().showMessage(f"❌ 撤销失败: {str(e)}", 5000)
            self.conn = sqlite3.connect(f'finance_{self.current_user}.db')
            self.cursor = self.conn.cursor()

    def manage_categories(self):
        """管理分类"""
        dialog = QDialog(self)
        dialog.setWindowTitle("管理分类")
        dialog.resize(400, 300)
        
        layout = QVBoxLayout()
        
        # 分类列表
        self.category_list = QListWidget()
        
        self.cursor.execute("""
            SELECT name, type FROM categories 
            ORDER BY type, name
        """)
        categories = self.cursor.fetchall()
        
        for name, type_ in categories:
            item = f"{name} ({'收入' if type_ == 'income' else '支出'})"
            self.category_list.addItem(item)
        
        layout.addWidget(self.category_list)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        # 添加分类
        add_btn = QPushButton("添加")
        add_btn.clicked.connect(lambda: self.add_category(dialog))
        button_layout.addWidget(add_btn)
        
        # 删除分类
        delete_btn = QPushButton("删除")
        delete_btn.clicked.connect(lambda: self.delete_category(dialog))
        button_layout.addWidget(delete_btn)
        
        # 关闭
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        dialog.exec_()
        
        # 更新分类下拉框
        self.load_categories()
        self.update_category_combo()

    def add_category(self, dialog):
        """添加新分类"""
        name, ok = QInputDialog.getText(
            dialog, "添加分类", "请输入分类名称:"
        )
        
        if ok and name:
            type_, ok = QInputDialog.getItem(
                dialog, "分类类型", "选择分类类型:",
                ["收入", "支出"], 0, False
            )
            
            if ok and type_:
                db_type = 'income' if type_ == '收入' else 'expense'
                
                try:
                    self.cursor.execute("""
                        INSERT INTO categories (name, type)
                        VALUES (?, ?)
                    """, (name, db_type))
                    self.conn.commit()
                    
                    # 更新列表
                    self.category_list.addItem(
                        f"{name} ({'收入' if db_type == 'income' else '支出'})"
                    )
                except sqlite3.IntegrityError:
                    self.statusBar().showMessage("⚠️ 分类已存在!", 5000)

    def delete_category(self, dialog):
        """删除分类"""
        selected = self.category_list.currentItem()
        if not selected:
            self.statusBar().showMessage("❌ 请选择要删除的分类!", 5000)
            return
        
        # 提取分类名称
        text = selected.text()
        name = text.split(" ")[0]
        
        # 检查是否有交易使用该分类
        self.cursor.execute("""
            SELECT COUNT(*) FROM transactions 
            WHERE category=?
        """, (name,))
        count = self.cursor.fetchone()[0]
        
        if count > 0:
            self.statusBar().showMessage(f"⚠️ 有{count}条交易记录使用此分类，无法删除!", 5000)
            return
        
        # 确认删除
        reply = QMessageBox.question(
            dialog, '确认', 
            f'确定要删除分类"{name}"吗?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.cursor.execute("""
                DELETE FROM categories 
                WHERE name=?
            """, (name,))
            self.conn.commit()
            
            # 从列表中移除
            self.category_list.takeItem(self.category_list.row(selected))

    def manage_accounts(self):
        """管理账户"""
        dialog = QDialog(self)
        dialog.setWindowTitle("管理账户")
        dialog.resize(500, 400)
        
        layout = QVBoxLayout()
        
        # 账户列表
        self.account_table = QTableWidget()
        self.account_table.setColumnCount(4)
        self.account_table.setHorizontalHeaderLabels(["ID", "账户名", "余额", "货币"])
        self.account_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.account_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        self.load_account_table()
        
        layout.addWidget(self.account_table)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        # 添加账户
        add_btn = QPushButton("添加")
        add_btn.clicked.connect(lambda: self.add_account(dialog))
        button_layout.addWidget(add_btn)
        
        # 编辑账户
        edit_btn = QPushButton("编辑")
        edit_btn.clicked.connect(lambda: self.edit_account(dialog))
        button_layout.addWidget(edit_btn)
        
        # 删除账户
        delete_btn = QPushButton("删除")
        delete_btn.clicked.connect(lambda: self.delete_account(dialog))
        button_layout.addWidget(delete_btn)
        
        # 关闭
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        dialog.exec_()
        
        # 更新账户下拉框
        self.load_accounts()
        self.load_account_combo()

    def load_account_table(self):
        """加载账户表格"""
        self.cursor.execute("""
            SELECT id, name, balance, currency FROM accounts
            ORDER BY name
        """)
        accounts = self.cursor.fetchall()
        
        self.account_table.setRowCount(len(accounts))
        for row, account in enumerate(accounts):
            for col, value in enumerate(account):
                item = QTableWidgetItem(str(value))
                
                # 余额列右对齐
                if col == 2:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    item.setText(f"{float(value):.2f}")
                
                self.account_table.setItem(row, col, item)
        
        self.account_table.resizeColumnsToContents()

    def add_account(self, dialog):
        """添加新账户"""
        dialog = QDialog(self)
        dialog.setWindowTitle("添加账户")
        
        layout = QFormLayout()
        
        # 账户名
        name_edit = QLineEdit()
        layout.addRow("账户名:", name_edit)
        
        # 初始余额
        balance_edit = QLineEdit("0")
        layout.addRow("初始余额:", balance_edit)
        
        # 货币
        currency_combo = QComboBox()
        currency_combo.addItems(["CNY", "USD", "EUR", "JPY", "GBP"])
        layout.addRow("货币:", currency_combo)
        
        # 描述
        desc_edit = QLineEdit()
        layout.addRow("描述:", desc_edit)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addRow(button_box)
        
        dialog.setLayout(layout)
        
        if dialog.exec_() == QDialog.Accepted:
            name = name_edit.text().strip()
            balance = balance_edit.text().strip()
            currency = currency_combo.currentText()
            desc = desc_edit.text().strip()
            
            if not name:
                self.statusBar().showMessage("❌ 请输入账户名!", 5000)
                return
                
            try:
                balance = float(balance)
            except ValueError:
                self.statusBar().showMessage("❌ 余额必须是有效数字!", 5000)
                return
                
            try:
                self.cursor.execute("""
                    INSERT INTO accounts (name, balance, currency, description)
                    VALUES (?, ?, ?, ?)
                """, (name, balance, currency, desc))
                self.conn.commit()
                
                self.statusBar().showMessage("✅ 账户已添加!", 5000)
                self.load_account_table()
            except sqlite3.IntegrityError:
                self.statusBar().showMessage("❌ 账户名已存在!", 5000)

    def edit_account(self, dialog):
        """编辑账户"""
        selected = self.account_table.selectedItems()
        if not selected:
            self.statusBar().showMessage("❌ 请选择要编辑的账户!", 5000)
            return
            
        row = selected[0].row()
        account_id = int(self.account_table.item(row, 0).text())
        
        # 获取账户信息
        self.cursor.execute("""
            SELECT name, balance, currency, description FROM accounts
            WHERE id=?
        """, (account_id,))
        account = self.cursor.fetchone()
        
        if not account:
            return
            
        name, balance, currency, desc = account
        
        # 创建编辑对话框
        edit_dialog = QDialog(self)
        edit_dialog.setWindowTitle("编辑账户")
        
        layout = QFormLayout()
        
        # 账户名
        name_edit = QLineEdit(name)
        layout.addRow("账户名:", name_edit)
        
        # 余额
        balance_edit = QLineEdit(f"{balance:.2f}")
        layout.addRow("余额:", balance_edit)
        
        # 货币
        currency_combo = QComboBox()
        currency_combo.addItems(["CNY", "USD", "EUR", "JPY", "GBP"])
        currency_combo.setCurrentText(currency)
        layout.addRow("货币:", currency_combo)
        
        # 描述
        desc_edit = QLineEdit(desc if desc else "")
        layout.addRow("描述:", desc_edit)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(edit_dialog.accept)
        button_box.rejected.connect(edit_dialog.reject)
        layout.addRow(button_box)
        
        edit_dialog.setLayout(layout)
        
        if edit_dialog.exec_() == QDialog.Accepted:
            new_name = name_edit.text().strip()
            new_balance = balance_edit.text().strip()
            new_currency = currency_combo.currentText()
            new_desc = desc_edit.text().strip()
            
            if not new_name:
                self.statusBar().showMessage("❌ 请输入账户名!", 5000)
                return
                
            try:
                new_balance = float(new_balance)
            except ValueError:
                self.statusBar().showMessage("❌ 余额必须是有效数字!", 5000)
                return
                
            try:
                self.cursor.execute("""
                    UPDATE accounts 
                    SET name=?, balance=?, currency=?, description=?
                    WHERE id=?
                """, (new_name, new_balance, new_currency, new_desc, account_id))
                self.conn.commit()
                
                self.statusBar().showMessage("✅ 账户已更新!", 5000)
                self.load_account_table()
            except sqlite3.IntegrityError:
                self.statusBar().showMessage("❌ 账户名已存在!", 5000)

    def delete_account(self, dialog):
        """删除账户"""
        selected = self.account_table.selectedItems()
        if not selected:
            self.statusBar().showMessage("❌ 请选择要删除的账户!", 5000)
            return
            
        row = selected[0].row()
        account_id = int(self.account_table.item(row, 0).text())
        account_name = self.account_table.item(row, 1).text()
        
        # 检查是否有交易关联此账户
        self.cursor.execute("""
            SELECT COUNT(*) FROM transactions 
            WHERE account_id=?
        """, (account_id,))
        count = self.cursor.fetchone()[0]
        
        if count > 0:
            self.statusBar().showMessage(f"❌ 有{count}条交易记录使用此账户，无法删除!", 5000)
            return
            
        # 确认删除
        reply = QMessageBox.question(
            dialog, '确认', 
            f'确定要删除账户"{account_name}"吗?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.cursor.execute("""
                DELETE FROM accounts 
                WHERE id=?
            """, (account_id,))
            self.conn.commit()
            
            self.statusBar().showMessage("✅ 账户已删除!", 5000)
            self.load_account_table()

    def manage_budgets(self):
        """管理预算"""
        dialog = QDialog(self)
        dialog.setWindowTitle("管理预算")
        dialog.resize(600, 400)
        
        layout = QVBoxLayout()
        
        # 月份选择
        month_layout = QHBoxLayout()
        month_layout.addWidget(QLabel("选择月份:"))
        
        self.budget_month_combo = QComboBox()
        # 添加当前月份和未来11个月
        current_date = QDate.currentDate()
        for i in range(12):
            month_date = current_date.addMonths(i)
            self.budget_month_combo.addItem(month_date.toString("yyyy-MM"), month_date)
        
        self.budget_month_combo.currentIndexChanged.connect(self.load_budgets)
        month_layout.addWidget(self.budget_month_combo)
        
        layout.addLayout(month_layout)
        
        # 预算表格
        self.budget_table = QTableWidget()
        self.budget_table.setColumnCount(3)
        self.budget_table.setHorizontalHeaderLabels(["分类", "预算金额", "实际支出"])
        self.budget_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.budget_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        self.load_budgets()
        
        layout.addWidget(self.budget_table)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        # 添加预算
        add_btn = QPushButton("添加预算")
        add_btn.clicked.connect(lambda: self.add_budget(dialog))
        button_layout.addWidget(add_btn)
        
        # 编辑预算
        edit_btn = QPushButton("编辑预算")
        edit_btn.clicked.connect(lambda: self.edit_budget(dialog))
        button_layout.addWidget(edit_btn)
        
        # 删除预算
        delete_btn = QPushButton("删除预算")
        delete_btn.clicked.connect(lambda: self.delete_budget(dialog))
        button_layout.addWidget(delete_btn)
        
        # 关闭
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        dialog.exec_()
        
        # 刷新统计
        self.update_statistics()

    def load_budgets(self):
        """加载预算数据"""
        selected_month = self.budget_month_combo.currentData().toString("yyyy-MM")
        
        # 获取所有支出分类
        self.cursor.execute("""
            SELECT name FROM categories 
            WHERE type='expense'
            ORDER BY name
        """)
        categories = [row[0] for row in self.cursor.fetchall()]
        
        # 获取预算数据
        self.cursor.execute("""
            SELECT category, amount FROM budgets
            WHERE month=?
        """, (selected_month,))
        budgets = {row[0]: row[1] for row in self.cursor.fetchall()}
        
        # 获取实际支出
        self.cursor.execute("""
            SELECT category, SUM(amount) 
            FROM transactions 
            WHERE type='expense' AND strftime('%Y-%m', date)=?
            GROUP BY category
        """, (selected_month,))
        expenses = {row[0]: row[1] for row in self.cursor.fetchall()}
        
        # 设置表格
        self.budget_table.setRowCount(len(categories))
        
        for row, category in enumerate(categories):
            # 分类列
            category_item = QTableWidgetItem(category)
            self.budget_table.setItem(row, 0, category_item)
            
            # 预算列
            budget = budgets.get(category, 0)
            budget_item = QTableWidgetItem(f"{budget:.2f}")
            budget_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.budget_table.setItem(row, 1, budget_item)
            
            # 实际支出列
            expense = expenses.get(category, 0)
            expense_item = QTableWidgetItem(f"{expense:.2f}")
            expense_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            # 如果实际支出超过预算，标记为红色
            if expense > budget and budget > 0:
                expense_item.setForeground(Qt.red)
            
            self.budget_table.setItem(row, 2, expense_item)
        
        self.budget_table.resizeColumnsToContents()

    def add_budget(self, dialog):
        """添加预算"""
        selected_month = self.budget_month_combo.currentData().toString("yyyy-MM")
        
        # 获取可用分类
        self.cursor.execute("""
            SELECT name FROM categories 
            WHERE type='expense' AND name NOT IN (
                SELECT category FROM budgets WHERE month=?
            )
            ORDER BY name
        """, (selected_month,))
        available_categories = [row[0] for row in self.cursor.fetchall()]
        
        if not available_categories:
            self.statusBar().showMessage("❌ 所有分类已设置预算!", 5000)
            return
            
        # 选择分类
        category, ok = QInputDialog.getItem(
            dialog, "选择分类", "请选择分类:", 
            available_categories, 0, False
        )
        
        if not ok or not category:
            return
            
        # 输入预算金额
        amount, ok = QInputDialog.getDouble(
            dialog, "设置预算", f"请输入{category}的预算金额:",
            min=0.01, max=1000000, decimals=2
        )
        
        if ok:
            try:
                self.cursor.execute("""
                    INSERT INTO budgets (category, amount, month)
                    VALUES (?, ?, ?)
                """, (category, amount, selected_month))
                self.conn.commit()
                
                self.statusBar().showMessage("✅ 预算已添加!", 5000)
                self.load_budgets()
            except sqlite3.IntegrityError:
                self.statusBar().showMessage("❌ 该分类本月预算已存在!", 5000)

    def edit_budget(self, dialog):
        """编辑预算"""
        selected = self.budget_table.selectedItems()
        if not selected:
            self.statusBar().showMessage("❌ 请选择要编辑的预算!", 5000)
            return
            
        row = selected[0].row()
        category = self.budget_table.item(row, 0).text()
        selected_month = self.budget_month_combo.currentData().toString("yyyy-MM")
        
        # 获取当前预算
        self.cursor.execute("""
            SELECT amount FROM budgets
            WHERE category=? AND month=?
        """, (category, selected_month))
        current_amount = self.cursor.fetchone()[0]
        
        # 输入新预算金额
        amount, ok = QInputDialog.getDouble(
            dialog, "编辑预算", f"请输入{category}的新预算金额:",
            value=current_amount, min=0.01, max=1000000, decimals=2
        )
        
        if ok:
            self.cursor.execute("""
                UPDATE budgets SET amount=?
                WHERE category=? AND month=?
            """, (amount, category, selected_month))
            self.conn.commit()
            
            self.statusBar().showMessage("✅ 预算已更新!", 5000)
            self.load_budgets()

    def delete_budget(self, dialog):
        """删除预算"""
        selected = self.budget_table.selectedItems()
        if not selected:
            self.statusBar().showMessage("❌ 请选择要删除的预算!", 5000)
            return
            
        row = selected[0].row()
        category = self.budget_table.item(row, 0).text()
        selected_month = self.budget_month_combo.currentData().toString("yyyy-MM")
        
        # 确认删除
        reply = QMessageBox.question(
            dialog, '确认', 
            f'确定要删除{selected_month}的"{category}"预算吗?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.cursor.execute("""
                DELETE FROM budgets 
                WHERE category=? AND month=?
            """, (category, selected_month))
            self.conn.commit()
            
            self.statusBar().showMessage("✅ 预算已删除!", 5000)
            self.load_budgets()

    def manage_recurring_transactions(self):
        """管理定期交易"""
        dialog = QDialog(self)
        dialog.setWindowTitle("定期交易管理")
        dialog.resize(800, 600)
        
        layout = QVBoxLayout()
        
        # 定期交易表格
        self.recurring_table = QTableWidget()
        self.recurring_table.setColumnCount(7)
        self.recurring_table.setHorizontalHeaderLabels(["ID", "类型", "金额", "分类", "频率", "下次执行", "结束日期"])
        self.recurring_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.recurring_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        self.load_recurring_transactions()
        
        layout.addWidget(self.recurring_table)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        # 执行选中
        execute_btn = QPushButton("执行选中")
        execute_btn.clicked.connect(lambda: self.execute_recurring_transaction(dialog))
        button_layout.addWidget(execute_btn)
        
        # 删除
        delete_btn = QPushButton("删除")
        delete_btn.clicked.connect(lambda: self.delete_recurring_transaction(dialog))
        button_layout.addWidget(delete_btn)
        
        # 关闭
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        dialog.exec_()

    def load_recurring_transactions(self):
        """加载定期交易"""
        self.cursor.execute("""
            SELECT id, type, amount, category, recurring_freq, 
                   date, recurring_end
            FROM transactions
            WHERE is_recurring=1
            ORDER BY date
        """)
        transactions = self.cursor.fetchall()
        
        self.recurring_table.setRowCount(len(transactions))
        for row, trans in enumerate(transactions):
            for col, value in enumerate(trans):
                item = QTableWidgetItem(str(value))
                
                # 类型列颜色
                if col == 1:  # 类型列
                    if value == 'income':
                        item.setText("收入")
                        item.setForeground(Qt.darkGreen)
                    elif value == 'expense':
                        item.setText("支出")
                        item.setForeground(Qt.darkRed)
                    elif value == '借款':
                        item.setForeground(Qt.darkBlue)
                    elif value == '还款':
                        item.setForeground(Qt.darkMagenta)
                
                # 金额列右对齐
                if col == 2:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    item.setText(f"{float(value):.2f}")
                
                self.recurring_table.setItem(row, col, item)
        
        self.recurring_table.resizeColumnsToContents()

    def execute_recurring_transaction(self, dialog):
        """执行选中的定期交易"""
        selected = self.recurring_table.selectedItems()
        if not selected:
            self.statusBar().showMessage("❌ 请选择要执行的定期交易!", 5000)
            return
            
        row = selected[0].row()
        trans_id = int(self.recurring_table.item(row, 0).text())
        
        # 获取交易详情
        self.cursor.execute("""
            SELECT type, amount, category, description, account_id, tags, 
                   receipt_image, recurring_freq, recurring_end
            FROM transactions
            WHERE id=?
        """, (trans_id,))
        trans = self.cursor.fetchone()
        
        if not trans:
            return
            
        type_, amount, category, desc, account_id, tags, receipt, freq, end_date = trans
        
        # 计算下次执行日期
        today = QDate.currentDate()
        next_date = self.calculate_next_date(today, freq)
        
        if not next_date:
            self.statusBar().showMessage("❌ 无法计算下次执行日期!", 5000)
            return
            
        # 检查是否已超过结束日期
        if end_date:
            end_qdate = QDate.fromString(end_date, "yyyy-MM-dd")
            if next_date > end_qdate:
                self.statusBar().showMessage("❌ 定期交易已超过结束日期!", 5000)
                return
        
        # 保存当前状态以便撤销
        self.save_state_before_change()
        
        # 添加新交易记录
        self.cursor.execute('''
            INSERT INTO transactions 
            (type, amount, category, description, date, account_id, tags, 
             receipt_image, is_recurring, recurring_freq, recurring_end)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
        ''', (type_, amount, category, desc, next_date.toString("yyyy-MM-dd"), 
              account_id, tags, receipt, freq, end_date))
        
        # 更新原定期交易的下次执行日期
        self.cursor.execute('''
            UPDATE transactions SET date=?
            WHERE id=?
        ''', (next_date.toString("yyyy-MM-dd"), trans_id))
        
        self.conn.commit()
        
        # 更新账户余额
        self.update_account_balance(account_id)
        
        self.statusBar().showMessage("✅ 定期交易已执行!", 5000)
        self.load_recurring_transactions()
        self.load_data()
        self.update_statistics()

    def calculate_next_date(self, last_date, freq):
        """计算下次执行日期"""
        if freq == "每日":
            return last_date.addDays(1)
        elif freq == "每周":
            return last_date.addDays(7)
        elif freq == "每月":
            return last_date.addMonths(1)
        elif freq == "每年":
            return last_date.addYears(1)
        return None

    def delete_recurring_transaction(self, dialog):
        """删除定期交易"""
        selected = self.recurring_table.selectedItems()
        if not selected:
            self.statusBar().showMessage("❌ 请选择要删除的定期交易!", 5000)
            return
            
        row = selected[0].row()
        trans_id = int(self.recurring_table.item(row, 0).text())
        
        # 确认删除
        reply = QMessageBox.question(
            dialog, '确认', 
            '确定要删除这个定期交易吗?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 保存当前状态以便撤销
            self.save_state_before_change()
            
            # 删除记录
            self.cursor.execute('''
                DELETE FROM transactions 
                WHERE id=?
            ''', (trans_id,))
            self.conn.commit()
            
            self.statusBar().showMessage("✅ 定期交易已删除!", 5000)
            self.load_recurring_transactions()
            self.load_data()
            self.update_statistics()

    def currency_converter(self):
        """汇率转换器"""
        dialog = QDialog(self)
        dialog.setWindowTitle("汇率转换")
        dialog.resize(400, 200)
        
        layout = QFormLayout()
        
        # 金额
        amount_edit = QLineEdit()
        amount_edit.setValidator(QtGui.QDoubleValidator())
        layout.addRow("金额:", amount_edit)
        
        # 从货币
        from_currency_combo = QComboBox()
        from_currency_combo.addItems(["CNY", "USD", "EUR", "JPY", "GBP"])
        layout.addRow("从:", from_currency_combo)
        
        # 到货币
        to_currency_combo = QComboBox()
        to_currency_combo.addItems(["CNY", "USD", "EUR", "JPY", "GBP"])
        to_currency_combo.setCurrentIndex(1)
        layout.addRow("到:", to_currency_combo)
        
        # 结果
        result_label = QLabel("0.00")
        result_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addRow("结果:", result_label)
        
        # 汇率信息
        rate_label = QLabel("汇率: 1 CNY = 0.14 USD")
        rate_label.setStyleSheet("font-size: 12px; color: #666;")
        layout.addRow(rate_label)
        
        # 转换按钮
        convert_btn = QPushButton("转换")
        convert_btn.clicked.connect(lambda: self.convert_currency(
            amount_edit, from_currency_combo, to_currency_combo, 
            result_label, rate_label
        ))
        layout.addRow(convert_btn)
        
        dialog.setLayout(layout)
        dialog.exec_()

    def convert_currency(self, amount_edit, from_currency_combo, to_currency_combo, 
                         result_label, rate_label):
        """执行货币转换"""
        try:
            amount = float(amount_edit.text())
        except ValueError:
            result_label.setText("无效金额")
            return
            
        from_currency = from_currency_combo.currentText()
        to_currency = to_currency_combo.currentText()
        
        # 这里应该调用汇率API，为了示例使用固定汇率
        exchange_rates = {
            "CNY": {"USD": 0.14, "EUR": 0.13, "JPY": 15.4, "GBP": 0.11, "CNY": 1},
            "USD": {"CNY": 7.1, "EUR": 0.93, "JPY": 110, "GBP": 0.79, "USD": 1},
            "EUR": {"CNY": 7.7, "USD": 1.07, "JPY": 118, "GBP": 0.85, "EUR": 1},
            "JPY": {"CNY": 0.065, "USD": 0.0091, "EUR": 0.0085, "GBP": 0.0072, "JPY": 1},
            "GBP": {"CNY": 9.1, "USD": 1.27, "EUR": 1.18, "JPY": 139, "GBP": 1}
        }
        
        if from_currency not in exchange_rates or to_currency not in exchange_rates[from_currency]:
            result_label.setText("不支持该货币转换")
            return
            
        rate = exchange_rates[from_currency][to_currency]
        result = amount * rate
        
        result_label.setText(f"{result:.2f}")
        rate_label.setText(f"汇率: 1 {from_currency} = {rate:.4f} {to_currency}")

    def export_to_csv(self):
        """导出数据为CSV"""
        file_name, _ = QFileDialog.getSaveFileName(
            self, "导出CSV", "", 
            "CSV文件 (*.csv)"
        )
        
        if not file_name:
            return
            
        if not file_name.endswith('.csv'):
            file_name += '.csv'
        
        try:
            with open(file_name, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # 写入标题行
                writer.writerow([
                    "ID", "类型", "金额", "分类", "描述", "日期", 
                    "状态", "关联ID", "账户", "标签", "收据图片"
                ])
                
                # 获取所有数据
                self.cursor.execute("""
                    SELECT t.id, t.type, t.amount, t.category, t.description, t.date, 
                           t.status, t.related_id, a.name, t.tags, t.receipt_image
                    FROM transactions t
                    LEFT JOIN accounts a ON t.account_id = a.id
                    ORDER BY t.date, t.id
                """)
                
                for row in self.cursor.fetchall():
                    writer.writerow(row)
                
            self.statusBar().showMessage(f"✅ 数据已导出到 {file_name}", 5000)
        except Exception as e:
            self.statusBar().showMessage(f"❌ 导出失败: {str(e)}", 5000)

    def export_to_excel(self):
        """导出数据为Excel"""
        try:
            import openpyxl
        except ImportError:
            self.statusBar().showMessage("❌ 请先安装openpyxl库: pip install openpyxl", 5000)
            return
            
        file_name, _ = QFileDialog.getSaveFileName(
            self, "导出Excel", "", 
            "Excel文件 (*.xlsx)"
        )
        
        if not file_name:
            return
            
        if not file_name.endswith('.xlsx'):
            file_name += '.xlsx'
        
        try:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "交易记录"
            
            # 写入标题行
            headers = [
                "ID", "类型", "金额", "分类", "描述", "日期", 
                "状态", "关联ID", "账户", "标签"
            ]
            ws.append(headers)
            
            # 获取所有数据
            self.cursor.execute("""
                SELECT t.id, t.type, t.amount, t.category, t.description, t.date, 
                       t.status, t.related_id, a.name, t.tags
                FROM transactions t
                LEFT JOIN accounts a ON t.account_id = a.id
                ORDER BY t.date, t.id
            """)
            
            for row in self.cursor.fetchall():
                ws.append(row)
            
            # 设置列宽
            for col in range(1, len(headers) + 1):
                column_letter = openpyxl.utils.get_column_letter(col)
                ws.column_dimensions[column_letter].width = 15
            
            wb.save(file_name)
            self.statusBar().showMessage(f"✅ 数据已导出到 {file_name}", 5000)
        except Exception as e:
            self.statusBar().showMessage(f"❌ 导出失败: {str(e)}", 5000)

    def check_reminders(self):
        """检查提醒"""
        today = QDate.currentDate().toString("yyyy-MM-dd")
        
        # 检查待还款借款
        self.cursor.execute("""
            SELECT id, amount, description, date 
            FROM transactions 
            WHERE type='借款' AND status='pending'
            ORDER BY date
        """)
        pending_loans = self.cursor.fetchall()
        
        # 检查预算超支
        current_month = QDate.currentDate().toString("yyyy-MM")
        self.cursor.execute("""
            SELECT b.category, b.amount, 
                   (SELECT SUM(amount) FROM transactions 
                    WHERE type='expense' AND category=b.category 
                    AND strftime('%Y-%m', date)=b.month) as expense
            FROM budgets b
            WHERE b.month=?
        """, (current_month,))
        budgets = self.cursor.fetchall()
        
        # 检查定期交易
        self.cursor.execute("""
            SELECT id, type, amount, category, description, date
            FROM transactions
            WHERE is_recurring=1 AND date <= ?
        """, (today,))
        recurring_trans = self.cursor.fetchall()
        
        # 如果有任何提醒，显示通知
        if pending_loans or budgets or recurring_trans:
            reminder_text = ""
            
            if pending_loans:
                reminder_text += f"待还款借款: {len(pending_loans)}笔\n"
                
            if budgets:
                over_budgets = [b for b in budgets if b[2] and b[2] > b[1]]
                if over_budgets:
                    reminder_text += f"预算超支: {len(over_budgets)}个分类\n"
                
            if recurring_trans:
                reminder_text += f"待执行定期交易: {len(recurring_trans)}笔\n"
            
            if reminder_text:
                QMessageBox.information(
                    self, "提醒", 
                    f"您有以下待处理事项:\n\n{reminder_text}\n请及时处理!"
                )

    def update_date_range(self, index):
        """更新日期范围"""
        today = QDate.currentDate()
        
        if index == 0:  # 全部时间
            self.cursor.execute("SELECT MIN(date), MAX(date) FROM transactions")
            min_date, max_date = self.cursor.fetchone()
            if min_date and max_date:
                self.date_from_edit.setDate(QDate.fromString(min_date, "yyyy-MM-dd"))
                self.date_to_edit.setDate(QDate.fromString(max_date, "yyyy-MM-dd"))
        elif index == 1:  # 最近一周
            self.date_from_edit.setDate(today.addDays(-7))
            self.date_to_edit.setDate(today)
        elif index == 2:  # 最近一月
            self.date_from_edit.setDate(today.addMonths(-1))
            self.date_to_edit.setDate(today)
        elif index == 3:  # 最近一年
            self.date_from_edit.setDate(today.addYears(-1))
            self.date_to_edit.setDate(today)
        
        # 保存配置
        self.save_settings()

    def load_settings(self):
        """加载配置"""
        try:
            # 加载日期范围配置
            self.cursor.execute("SELECT value FROM settings WHERE key='date_range'")
            result = self.cursor.fetchone()
            if result:
                index = int(result[0])
                self.date_range_combo.setCurrentIndex(index)
                self.update_date_range(index)
        except:
            pass

    def save_settings(self):
        """保存配置"""
        try:
            # 保存日期范围配置
            index = self.date_range_combo.currentIndex()
            self.cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                ('date_range', str(index))
            )
            self.conn.commit()
        except:
            pass

    def cleanup_old_temp_files(self, max_age_hours=24):
        """清理超过指定时间的临时文件"""
        import glob
        from datetime import datetime, timedelta
        
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        temp_files = glob.glob("temp_undo_*.db")
        
        for file in temp_files:
            try:
                # 从文件名中提取时间（格式：temp_undo_YYYYMMDD_HHMMSS.db）
                file_time_str = file.split('_')[2] + '_' + file.split('_')[3].split('.')[0]
                file_time = datetime.strptime(file_time_str, "%Y%m%d_%H%M%S")
                
                if file_time < cutoff_time:
                    os.remove(file)
                    print(f"已清理过期临时文件: {file}")
            except Exception as e:
                print(f"清理临时文件 {file} 失败: {str(e)}")

    def show_about(self):
        """显示关于对话框"""
        about_text = f"""
        <h2>{ProjectInfo.NAME} {ProjectInfo.VERSION}</h2>
        <p>{ProjectInfo.DESCRIPTION}</p>
        <p><b>作者:</b> {ProjectInfo.AUTHOR}</p>
        <p><b>许可证:</b> {ProjectInfo.LICENSE}</p>
        <p><b>版权:</b> {ProjectInfo.COPYRIGHT}</p>
        <p><b>网址:</b> <a href="{ProjectInfo.URL}">{ProjectInfo.URL}</a></p>
        <p><b>构建日期:</b> {ProjectInfo.BUILD_DATE}</p>
        """
        
        QMessageBox.about(self, "关于", about_text)

    def closeEvent(self, event):
        """关闭窗口时清理资源"""
        # 保存配置
        self.save_settings()

        # 停止定时器
        self.backup_timer.stop()
        self.reminder_timer.stop()
        self.cleanup_timer.stop()
        
        # 关闭数据库连接
        self.close_current_db()
        if hasattr(self, 'master_conn'):
            self.master_conn.close()
        
        # 清理临时撤销文件
        for file in self.operation_stack:
            try:
                os.remove(file)
            except:
                pass
        
        event.accept()

if __name__ == "__main__":
    import os
    import sys
    
    # 创建备份目录
    if not os.path.exists("backups"):
        os.makedirs("backups")
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # 使用Fusion风格，看起来更现代
    
    # 设置应用程序图标（需要准备一个money.png文件）
    if not hasattr(app, 'setWindowIcon'):
        app.setWindowIcon = lambda x: None
    
    window = FinanceApp()
    window.show()
    sys.exit(app.exec_())