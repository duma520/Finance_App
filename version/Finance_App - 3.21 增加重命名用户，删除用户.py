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
                             QStackedWidget, QGroupBox, QInputDialog, QListWidget, QCheckBox,
                             QSpinBox
                             )
from PyQt5.QtCore import Qt, QDate, QTimer, QSize
from PyQt5.QtGui import QIcon, QColor, QPixmap, QPainter
from PyQt5.QtChart import QChart, QChartView, QPieSeries, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis
from PyQt5 import QtGui, QtWidgets
import pypinyin
from PIL import Image
import io
import base64
from cryptography.fernet import Fernet
import calendar
from dateutil.relativedelta import relativedelta

class ProjectInfo:
    """项目信息元数据（集中管理所有项目相关信息）"""
    VERSION = "3.21.0"
    BUILD_DATE = "2025-06-14"
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
        self.resize(350, 300)  # 增加高度以容纳更多控件
        
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
        
        # 添加管理用户按钮
        manage_users_btn = QPushButton("管理用户")
        manage_users_btn.clicked.connect(self.manage_users)
        layout.addWidget(manage_users_btn)
        
        self.setLayout(layout)
    
    def load_users(self, users):
        self.user_combo.clear()
        self.user_combo.addItems(users)
    
    def manage_users(self):
        """管理用户对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("管理用户")
        dialog.resize(400, 300)
        
        layout = QVBoxLayout()
        
        # 用户列表
        self.user_list = QListWidget()
        self.load_user_list()
        layout.addWidget(self.user_list)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        # 重命名按钮
        rename_btn = QPushButton("重命名")
        rename_btn.clicked.connect(lambda: self.rename_user(dialog))
        button_layout.addWidget(rename_btn)
        
        # 删除按钮
        delete_btn = QPushButton("删除")
        delete_btn.clicked.connect(lambda: self.delete_user(dialog))
        button_layout.addWidget(delete_btn)
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        dialog.exec_()
    
    def load_user_list(self):
        """加载用户列表"""
        self.user_list.clear()
        self.master_cursor.execute("SELECT username FROM users ORDER BY username")
        users = [row[0] for row in self.master_cursor.fetchall()]
        self.user_list.addItems(users)
    
    def rename_user(self, dialog):
        """重命名选中的用户"""
        selected = self.user_list.currentItem()
        if not selected:
            QMessageBox.warning(dialog, "警告", "请选择一个用户")
            return
        
        old_name = selected.text()
        new_name, ok = QInputDialog.getText(
            dialog, "重命名用户", "请输入新用户名:", 
            QLineEdit.Normal, old_name
        )
        
        if ok and new_name and new_name != old_name:
            try:
                # 检查新用户名是否已存在
                self.master_cursor.execute("SELECT username FROM users WHERE username=?", (new_name,))
                if self.master_cursor.fetchone():
                    QMessageBox.warning(dialog, "错误", "用户名已存在")
                    return
                
                # 重命名用户
                self.master_cursor.execute(
                    "UPDATE users SET username=? WHERE username=?",
                    (new_name, old_name)
                )
                
                # 重命名数据库文件
                old_db = f'finance_{old_name}.db'
                new_db = f'finance_{new_name}.db'
                if os.path.exists(old_db):
                    os.rename(old_db, new_db)
                
                self.master_conn.commit()
                self.load_user_list()
                self.load_users([row[0] for row in self.master_cursor.execute("SELECT username FROM users")])
                
                QMessageBox.information(dialog, "成功", f"用户 {old_name} 已重命名为 {new_name}")
            except Exception as e:
                QMessageBox.critical(dialog, "错误", f"重命名失败: {str(e)}")
                self.master_conn.rollback()
    
    def delete_user(self, dialog):
        """删除选中的用户"""
        selected = self.user_list.currentItem()
        if not selected:
            QMessageBox.warning(dialog, "警告", "请选择一个用户")
            return
        
        username = selected.text()
        
        # 确认对话框
        reply = QMessageBox.question(
            dialog, '确认删除', 
            f'确定要删除用户 "{username}" 吗？\n此操作会删除该用户的所有数据且不可恢复！',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # 删除用户
                self.master_cursor.execute(
                    "DELETE FROM users WHERE username=?",
                    (username,)
                )
                
                # 删除数据库文件
                db_file = f'finance_{username}.db'
                if os.path.exists(db_file):
                    os.remove(db_file)
                
                # 删除备份文件
                backup_files = [f for f in os.listdir("backups") if f.startswith(f"finance_{username}_")]
                for f in backup_files:
                    try:
                        os.remove(os.path.join("backups", f))
                    except:
                        pass
                
                self.master_conn.commit()
                self.load_user_list()
                self.load_users([row[0] for row in self.master_cursor.execute("SELECT username FROM users")])
                
                QMessageBox.information(dialog, "成功", f"用户 {username} 已删除")
            except Exception as e:
                QMessageBox.critical(dialog, "错误", f"删除失败: {str(e)}")
                self.master_conn.rollback()


class FinanceApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.backup_dir = "backups"
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
        
        # 设置自动备份数量限制，默认为30
        self.max_backups = 30
        
        self.setWindowTitle(f"{ProjectInfo.NAME} {ProjectInfo.VERSION}")
        # self.setWindowTitle(f"{ProjectInfo.NAME} {ProjectInfo.VERSION} - 当前用户: {self.current_user}")
        self.setWindowIcon(QIcon("icon.ico"))
        self.resize(1200, 800)

        # 初始化table属性
        self.table = None
        
        # 初始化多用户数据库
        self.init_user_db()
        
        # 显示登录对话框
        self.show_login_dialog()

        # 设置窗口标题包含当前用户
        self.update_window_title()

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

        # 创建UI组件（不调用reset_ui()）
        # self.create_search_bar()
        # self.create_tabs()
        # self.create_input_form()
        # self.create_action_buttons()

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
        password = result[0] if result else None
        self.db_encrypted = password is not None
        
        if self.db_encrypted:
            # 如果数据库加密，需要先解密
            key = self.get_encryption_key(password)
            self.cipher_suite = Fernet(key)
            
            # 检查数据库文件是否存在
            if os.path.exists(db_name):
                try:
                    with open(db_name, 'rb') as f:
                        encrypted_data = f.read()
                    decrypted_data = self.cipher_suite.decrypt(encrypted_data)
                    
                    # 创建临时数据库连接
                    self.conn = sqlite3.connect(':memory:')
                    self.conn.executescript(decrypted_data.decode('utf-8'))
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"数据库解密失败: {str(e)}")
                    self.conn = sqlite3.connect(':memory:')  # 创建空的内存数据库
            else:
                self.conn = sqlite3.connect(':memory:')
        else:
            # 非加密数据库直接连接
            self.conn = sqlite3.connect(db_name)
            
        self.cursor = self.conn.cursor()
        
        # 创建交易表（使用IF NOT EXISTS避免重复创建）
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

        # 检查并升级数据库结构
        self.upgrade_database_schema()

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
        
        # 初始化默认分类（如果表为空）
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
                try:
                    self.cursor.execute(
                        "INSERT OR IGNORE INTO categories (name, type) VALUES (?, ?)",
                        (name, type_)
                    )
                except sqlite3.Error as e:
                    print(f"添加默认分类失败: {str(e)}")

        # 初始化默认账户（如果表为空）
        self.cursor.execute("SELECT COUNT(*) FROM accounts")
        if self.cursor.fetchone()[0] == 0:
            try:
                self.cursor.execute(
                    "INSERT INTO accounts (name, balance, currency) VALUES (?, ?, ?)",
                    ("现金账户", 0, "CNY")
                )
            except sqlite3.Error as e:
                print(f"添加默认账户失败: {str(e)}")

        # 创建配置表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')

        # 创建数据库版本表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS db_version (
                version INTEGER PRIMARY KEY,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 检查当前数据库版本
        self.cursor.execute("SELECT version FROM db_version ORDER BY version DESC LIMIT 1")
        current_version = self.cursor.fetchone()
        current_version = current_version[0] if current_version else 0
        
        # 执行必要的升级
        if current_version < 1:
            try:
                self.upgrade_to_version_1()
                current_version = 1
            except sqlite3.Error as e:
                print(f"升级到版本1失败: {str(e)}")
        
        if current_version < 2:
            try:
                self.upgrade_to_version_2()
                current_version = 2
            except sqlite3.Error as e:
                print(f"升级到版本2失败: {str(e)}")
        
        # 更新数据库版本
        try:
            self.cursor.execute("INSERT OR REPLACE INTO db_version (version) VALUES (?)", (current_version,))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"更新数据库版本失败: {str(e)}")
            self.conn.rollback()

        # 升级旧的借款记录，设置默认值
        self.upgrade_old_loans()


    def upgrade_old_loans(self):
        """升级旧的借款记录，设置默认值"""
        self.cursor.execute('''
            UPDATE transactions 
            SET is_recurring = 0, 
                recurring_freq = NULL, 
                recurring_end = NULL,
                tags = '',
                receipt_image = NULL
            WHERE (is_recurring IS NULL OR tags IS NULL OR receipt_image IS NULL)
            AND type IN ('借款', '还款')
        ''')
        self.conn.commit()


    def upgrade_to_version_1(self):
        """升级到版本1：添加定期交易相关字段"""
        # 检查列是否已存在
        self.cursor.execute("PRAGMA table_info(transactions)")
        columns = [column[1] for column in self.cursor.fetchall()]
        
        if 'is_recurring' not in columns:
            self.cursor.execute("ALTER TABLE transactions ADD COLUMN is_recurring INTEGER DEFAULT 0")
        
        if 'recurring_freq' not in columns:
            self.cursor.execute("ALTER TABLE transactions ADD COLUMN recurring_freq TEXT")
        
        if 'recurring_end' not in columns:
            self.cursor.execute("ALTER TABLE transactions ADD COLUMN recurring_end TEXT")
        
        self.conn.commit()


    def upgrade_to_version_2(self):
        """升级到版本2：添加其他新字段"""
        # 检查列是否已存在
        self.cursor.execute("PRAGMA table_info(transactions)")
        columns = [column[1] for column in self.cursor.fetchall()]
        
        if 'tags' not in columns:
            self.cursor.execute("ALTER TABLE transactions ADD COLUMN tags TEXT")
        
        if 'receipt_image' not in columns:
            self.cursor.execute("ALTER TABLE transactions ADD COLUMN receipt_image TEXT")
        
        self.conn.commit()


    def upgrade_database_schema(self):
        """升级数据库结构，确保所有必要的列都存在"""
        # 获取当前表结构
        self.cursor.execute("PRAGMA table_info(transactions)")
        columns = {column[1]: column for column in self.cursor.fetchall()}
        
        # 定义需要添加的列及其默认值
        columns_to_add = [
            ('account_id', 'INTEGER', 'DEFAULT 1'),
            ('tags', 'TEXT', ''),
            ('receipt_image', 'TEXT', ''),
            ('is_recurring', 'INTEGER', 'DEFAULT 0'),
            ('recurring_freq', 'TEXT', ''),
            ('recurring_end', 'TEXT', '')
        ]
        
        # 添加缺失的列
        for column_name, column_type, column_default in columns_to_add:
            if column_name not in columns:
                sql = f"ALTER TABLE transactions ADD COLUMN {column_name} {column_type} {column_default}"
                self.cursor.execute(sql)
        
        # 更新所有旧记录的默认值
        for column_name, _, default_value in columns_to_add:
            if default_value and not default_value.startswith('DEFAULT'):
                sql = f"UPDATE transactions SET {column_name} = {default_value} WHERE {column_name} IS NULL"
                self.cursor.execute(sql)
        
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
    
        # 传递数据库连接给登录对话框
        login_dialog.master_cursor = self.master_cursor
        login_dialog.master_conn = self.master_conn

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
        # backup_menu = file_menu.addMenu("备份")
        
        # 备份恢复子菜单
        backup_menu = file_menu.addMenu("备份与恢复")
        
        # 自动备份设置
        auto_backup_action = QAction("设置自动备份", self)
        auto_backup_action.triggered.connect(self.setup_auto_backup_settings)
        backup_menu.addAction(auto_backup_action)
        
        # 手动备份
        manual_backup_action = QAction("手动备份", self)
        manual_backup_action.triggered.connect(self.manual_backup)
        backup_menu.addAction(manual_backup_action)
        
        # 恢复备份
        restore_action = QAction("恢复备份", self)
        restore_action.triggered.connect(self.show_restore_dialog)
        backup_menu.addAction(restore_action)
        
        # 恢复操作
        # restore_action = QAction("恢复数据", self)
        # restore_action.triggered.connect(self.restore_data)
        # file_menu.addAction(restore_action)
        
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

        # 新增账户结余标签页
        self.balance_tab = QWidget()
        self.tab_widget.addTab(self.balance_tab, "账户结余")
        self.create_balance_tab()  # 调用创建账户结余标签页的方法
        
        # 设置定时器定期更新账户结余
        self.balance_timer = QTimer()
        self.balance_timer.timeout.connect(self.update_account_balances)
        self.balance_timer.start(60000)  # 每分钟更新一次

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
        self.type_combo.addItems(["收入", "支出", "借款", "还款", "余额", "账户结余"])
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
        self.account_combo.addItem("全部结余", -1)
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
        
        # self.main_layout.addLayout(form_layout) 已经改成弹窗添加记录，所以这行不需要了
        
        # 类型改变时更新界面
        self.type_combo.currentTextChanged.connect(self.update_form)
        self.update_form(self.type_combo.currentText())
        
        # 初始化类别
        self.update_category_combo()

        # 初始状态下如果是支出或借款类型，默认选择"其他"
        if self.type_combo.currentText() in ["支出", "借款"]:
            index = self.category_combo.findText("其他")
            if index >= 0:
                self.category_combo.setCurrentIndex(index)

    def load_account_combo(self):
        """加载账户下拉框"""
        # 保留第一个"全部结余"选项
        while self.account_combo.count() > 1:
            self.account_combo.removeItem(1)
        
        self.cursor.execute("SELECT id, name FROM accounts ORDER BY name")
        accounts = self.cursor.fetchall()
        
        for account_id, account_name in accounts:
            self.account_combo.addItem(account_name, account_id)

    def load_account_combo_to(self, combo_box):
        """加载账户到指定的下拉框"""
        # 保留第一个"全部结余"选项
        combo_box.clear()
        combo_box.addItem("全部结余", -1)
        
        self.cursor.execute("SELECT id, name FROM accounts ORDER BY name")
        accounts = self.cursor.fetchall()
        
        for account_id, account_name in accounts:
            combo_box.addItem(account_name, account_id)


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
        
        # 处理账户下拉框状态
        if type_text == "余额":
            # 设置为"全部结余"并禁用
            index = self.account_combo.findData(-1)
            if index >= 0:
                self.account_combo.setCurrentIndex(index)
            self.account_combo.setEnabled(False)
        elif type_text == "账户结余":
            # 启用账户选择，确保不选择"全部结余"
            self.account_combo.setEnabled(True)
            if self.account_combo.currentData() == -1:
                self.account_combo.setCurrentIndex(1 if self.account_combo.count() > 1 else 0)
        else:
            # 其他类型正常启用
            self.account_combo.setEnabled(True)
            if self.account_combo.currentData() == -1:
                self.account_combo.setCurrentIndex(1 if self.account_combo.count() > 1 else 0)
        
        # 如果是余额类型，禁用金额输入
        if type_text in ["余额", "账户结余"]:
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
        
        # 添加记录按钮 - 修改为打开弹窗
        self.add_button = QPushButton("添加记录")
        self.add_button.clicked.connect(self.show_add_record_dialog)  # 改为调用弹窗方法
        button_layout.addWidget(self.add_button)
    
        # 编辑记录按钮
        self.edit_button = QPushButton("编辑记录")
        self.edit_button.clicked.connect(self.edit_record)
        button_layout.addWidget(self.edit_button)
    
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
        """原来的添加记录方法，现在只是调用弹窗"""
        self.show_add_record_dialog()


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
        """删除选中的记录（支持多选）"""
        selected_rows = set()
        for item in self.table.selectedItems():
            selected_rows.add(item.row())
        
        if not selected_rows:
            self.statusBar().showMessage("❌ 请选择要删除的记录！", 5000)
            return
        
        # 收集所有选中的记录ID和相关信息
        record_ids = []
        account_ids = set()
        min_date = None
        related_loans = set()  # 需要更新状态的借款ID
        
        for row in selected_rows:
            record_id = int(self.table.item(row, 0).text())
            record_ids.append(record_id)
            
            # 获取账户ID
            account_item = self.table.item(row, 8)
            if account_item and account_item.data(Qt.UserRole):
                account_ids.add(account_item.data(Qt.UserRole))
            
            # 获取记录日期（用于后续的余额更新）
            date_item = self.table.item(row, 5)
            if date_item:
                date_str = date_item.text()
                if not min_date or date_str < min_date:
                    min_date = date_str
            
            # 检查是否是还款记录
            type_item = self.table.item(row, 1)
            if type_item and type_item.text() == "还款":
                related_id_item = self.table.item(row, 7)
                if related_id_item and related_id_item.text().isdigit():
                    related_loans.add(int(related_id_item.text()))
        
        # 检查是否有未还清的借款记录
        self.cursor.execute(f"""
            SELECT id, description FROM transactions 
            WHERE id IN ({','.join(['?']*len(record_ids))}) 
            AND type='借款' AND status='pending'
        """, record_ids)
        
        pending_loans = self.cursor.fetchall()
        if pending_loans:
            loan_list = "\n".join([f"ID:{loan[0]} {loan[1]}" for loan in pending_loans])
            QMessageBox.warning(
                self, "无法删除", 
                f"不能删除未还清的借款记录：\n{loan_list}\n请先还清借款或标记为已结清。"
            )
            return
        
        # 确认删除
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText(f"确定要删除这 {len(record_ids)} 条记录吗？")
        msg.setWindowTitle("确认删除")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        
        if msg.exec_() != QMessageBox.Ok:
            return
        
        try:
            # 开始事务
            self.conn.execute("BEGIN TRANSACTION")
            
            # 1. 保存当前状态以便撤销
            self.save_state_before_change()
            
            # 2. 获取所有还款记录的关联借款ID（除了已收集的）
            self.cursor.execute(f"""
                SELECT DISTINCT related_id FROM transactions 
                WHERE id IN ({','.join(['?']*len(record_ids))}) 
                AND related_id IS NOT NULL
            """, record_ids)
            
            additional_loans = {row[0] for row in self.cursor.fetchall() if row[0] not in related_loans}
            related_loans.update(additional_loans)
            
            # 3. 删除记录
            self.cursor.execute(f"""
                DELETE FROM transactions 
                WHERE id IN ({','.join(['?']*len(record_ids))})
            """, record_ids)
            
            # 4. 更新所有关联借款的状态
            for loan_id in related_loans:
                self.update_loan_status(loan_id)
            
            # 5. 更新账户余额
            for account_id in account_ids:
                self.update_account_balance(account_id)
            
            # 6. 更新后续日期的余额记录
            if min_date:
                self.update_future_balances(min_date)
            
            # 提交事务
            self.conn.commit()
            
            # 更新UI
            self.update_account_balances()
            self.load_data()
            self.update_statistics()
            
            self.statusBar().showMessage(f"✅ 已删除 {len(record_ids)} 条记录", 5000)
            
        except sqlite3.Error as e:
            self.conn.rollback()
            self.statusBar().showMessage(f"❌ 删除失败：{str(e)}", 5000)
            print(f"[delete_record] SQL error: {str(e)}")
            
        except Exception as e:
            self.conn.rollback()
            self.statusBar().showMessage(f"❌ 系统错误：{str(e)}", 5000)
            print(f"[delete_record] System error: {str(e)}")


    def edit_record(self):
        """编辑选中的记录"""
        selected_rows = set()
        for item in self.table.selectedItems():
            selected_rows.add(item.row())
        
        if not selected_rows or len(selected_rows) > 1:
            self.statusBar().showMessage("❌ 请选择一条要编辑的记录!", 5000)
            return
        
        row = list(selected_rows)[0]
        record_id = int(self.table.item(row, 0).text())
        
        # 获取记录详情（包含新增的remaining字段）
        self.cursor.execute("""
            SELECT type, amount, category, description, date, account_id, tags, 
                receipt_image, is_recurring, recurring_freq, recurring_end, status, related_id,
                (SELECT t.amount - IFNULL(SUM(r.amount), 0) 
                FROM transactions r 
                WHERE r.type='还款' AND r.related_id=t.id)
                FROM transactions t
                WHERE id=?
        """, (record_id,))
        record = self.cursor.fetchone()
        
        if not record:
            self.statusBar().showMessage("❌ 记录不存在!", 5000)
            return
        
        # 创建编辑对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("编辑记录")
        dialog.resize(500, 350)
        
        layout = QFormLayout()
        
        # 类型选择
        type_combo = QComboBox()
        type_combo.addItems(["收入", "支出", "借款", "还款", "余额", "账户结余"])
        
        # 将数据库类型转换为显示文本
        type_mapping = {
            'income': '收入',
            'expense': '支出',
            '借款': '借款',
            '还款': '还款',
            'balance': '余额'
        }
        current_type = type_mapping.get(record[0], record[0])
        type_combo.setCurrentText(current_type)
        type_combo.setEnabled(False)  # 禁止修改类型
        layout.addRow("类型:", type_combo)
        
        # 金额
        amount_edit = QLineEdit(f"{record[1]:.2f}")
        if current_type in ['余额', '账户结余']:
            amount_edit.setEnabled(False)  # 余额类型不可编辑金额
        layout.addRow("金额:", amount_edit)
        
        # 类别
        category_combo = QComboBox()
        layout.addRow("类别:", category_combo)
        
        # 账户选择
        account_combo = QComboBox()
        self.load_account_combo_to(account_combo)
        layout.addRow("账户:", account_combo)
        
        # 日期
        date_edit = QDateEdit(QDate.fromString(record[4], "yyyy-MM-dd"))
        date_edit.setCalendarPopup(True)
        date_edit.setDisplayFormat("yyyy-MM-dd")
        layout.addRow("日期:", date_edit)
        
        # 描述
        desc_edit = QLineEdit(record[3])
        layout.addRow("描述:", desc_edit)
        
        # 标签
        tags_edit = QLineEdit(record[6] if record[6] else "")
        layout.addRow("标签:", tags_edit)
        
        # 如果是借款，显示剩余金额
        if current_type == '借款':
            remaining = record[-1] or record[1]  # 使用计算出的剩余金额或原始金额
            remaining_label = QLabel(f"剩余待还金额: {remaining:.2f}")
            remaining_label.setStyleSheet("color: #d9534f; font-weight: bold;")
            layout.addRow(remaining_label)
        
        # 如果是还款，显示关联借款信息
        if current_type == '还款' and record[12]:
            related_loan_id = record[12]
            self.cursor.execute("SELECT amount, description FROM transactions WHERE id=?", (related_loan_id,))
            loan_info = self.cursor.fetchone()
            if loan_info:
                loan_amount, loan_desc = loan_info
                loan_label = QLabel(f"关联借款ID: {related_loan_id} (金额: {loan_amount:.2f}, 描述: {loan_desc})")
                loan_label.setWordWrap(True)
                layout.addRow(loan_label)
                
                # 添加调整超额还款按钮
                adjust_button = QPushButton("调整超额还款")
                adjust_button.clicked.connect(lambda: self.adjust_overpayment(record_id))
                layout.addRow(adjust_button)
        
        # 更新类别下拉框
        def update_category_combo(type_text):
            type_map = {
                "收入": "income",
                "支出": "expense",
                "借款": "expense",
                "还款": "income"
            }
            db_type = type_map.get(type_text, "income")
            
            category_combo.clear()
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
                
            category_combo.addItems(categories)
            
            # 设置当前选中的类别
            if record[2]:
                index = category_combo.findText(record[2])
                if index >= 0:
                    category_combo.setCurrentIndex(index)
        
        update_category_combo(current_type)
        
        # 设置当前账户
        if record[5]:
            index = account_combo.findData(record[5])
            if index >= 0:
                account_combo.setCurrentIndex(index)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addRow(button_box)
        
        dialog.setLayout(layout)
        
        if dialog.exec_() == QDialog.Accepted:
            # 获取修改后的值
            try:
                amount = float(amount_edit.text())
            except ValueError:
                self.statusBar().showMessage("❌ 金额必须是有效数字!", 5000)
                return
            
            category = category_combo.currentText()
            account_id = account_combo.currentData()
            date = date_edit.date().toString("yyyy-MM-dd")
            description = desc_edit.text().strip()
            tags = tags_edit.text().strip()
            
            # 如果是还款记录，检查金额是否超过剩余应还金额
            if current_type == '还款' and record[12]:
                remaining = self.get_remaining_loan_amount(record[12])
                if amount > remaining:
                    QMessageBox.warning(self, "错误", 
                        f"还款金额不能超过剩余应还金额 {remaining:.2f} 元")
                    return
            
            # 日期不能晚于今天
            if date_edit.date() > QDate.currentDate():
                self.statusBar().showMessage("❌ 日期不能晚于今天!", 5000)
                return
            
            # 描述长度限制
            if len(description) > 100:
                self.statusBar().showMessage("❌ 描述不能超过100个字符!", 5000)
                return
            
            # 保存当前状态以便撤销
            self.save_state_before_change()
            
            # 更新记录
            self.cursor.execute("""
                UPDATE transactions 
                SET amount=?, category=?, description=?, date=?, 
                    account_id=?, tags=?
                WHERE id=?
            """, (amount, category, description, date, account_id, tags, record_id))
            
            # 如果编辑的是还款记录，更新关联借款状态
            if current_type == '还款' and record[12]:
                self.update_loan_status(record[12])
            
            self.conn.commit()
            
            # 更新账户余额
            if account_id:
                self.update_account_balance(account_id)
            
            # 更新后续日期的余额记录
            if current_type in ["income", "expense", "借款", "还款"]:
                self.update_future_balances(date)
            
            self.update_account_balances()
            self.statusBar().showMessage("✅ 记录已更新!", 5000)
            self.load_data()
            self.update_statistics()


    def update_loan_status(self, loan_id):
        """
        更新借款状态（pending/settled）
        基于已还款金额与借款金额的比较
        
        参数:
            loan_id (int): 要更新的借款记录ID
        
        返回值:
            bool: 更新成功返回True，失败返回False
        """
        try:
            if not loan_id or not isinstance(loan_id, int):
                raise ValueError("无效的借款ID")
            
            # 1. 获取借款原始金额和当前状态
            self.cursor.execute("""
                SELECT amount, status FROM transactions 
                WHERE id=? AND type='借款'
            """, (loan_id,))
            loan_info = self.cursor.fetchone()
            
            if not loan_info:
                self.statusBar().showMessage(f"❌ 未找到ID为 {loan_id} 的借款记录", 3000)
                return False
            
            loan_amount, current_status = loan_info
            
            # 2. 计算已还款总额
            self.cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) 
                FROM transactions 
                WHERE type='还款' AND related_id=?
            """, (loan_id,))
            repaid_amount = self.cursor.fetchone()[0]
            
            # 3. 计算剩余未还金额
            remaining_amount = loan_amount - repaid_amount
            remaining_amount = max(0, remaining_amount)  # 确保不为负数
            
            # 4. 确定新状态
            new_status = 'settled' if remaining_amount <= 0 else 'pending'
            
            # 5. 如果需要更新状态，则执行更新
            if new_status != current_status:
                self.cursor.execute("""
                    UPDATE transactions 
                    SET status=? 
                    WHERE id=?
                """, (new_status, loan_id))
                self.conn.commit()
                
                # 6. 如果完全还清，更新关联的所有还款记录状态
                if new_status == 'settled':
                    self.cursor.execute("""
                        UPDATE transactions 
                        SET status='settled' 
                        WHERE type='还款' AND related_id=?
                    """, (loan_id,))
                    self.conn.commit()
                
                # 更新相关账户余额
                self.cursor.execute("SELECT account_id FROM transactions WHERE id=?", (loan_id,))
                account_id = self.cursor.fetchone()[0]
                if account_id:
                    self.update_account_balance(account_id)
                
                self.statusBar().showMessage(
                    f"✅ 借款ID {loan_id} 状态已更新: {new_status} (剩余: {remaining_amount:.2f})", 
                    3000
                )
            
            return True
        
        except sqlite3.Error as e:
            self.conn.rollback()
            error_msg = f"数据库错误: {str(e)}"
            self.statusBar().showMessage(f"❌ {error_msg}", 5000)
            print(f"[update_loan_status] {error_msg}")
            return False
        
        except Exception as e:
            error_msg = f"系统错误: {str(e)}"
            self.statusBar().showMessage(f"❌ {error_msg}", 5000)
            print(f"[update_loan_status] {error_msg}")
            return False


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
                a.name, t.tags,
                CASE WHEN t.type='借款' THEN 
                    (SELECT t.amount - IFNULL(SUM(r.amount), 0) 
                    FROM transactions r 
                    WHERE r.type='还款' AND r.related_id=t.id)
                    ELSE NULL
                END as remaining
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

                        # 添加剩余金额信息
                        remaining = record[10]  # 新增的remaining列
                        if remaining is not None:
                            item.setText(f"借款 (剩余:{remaining:.2f})")

                    elif value == '还款':
                        item.setForeground(Qt.darkMagenta)
                        item.setBackground(MacaronColors.SKY_BLUE)
                    elif value == 'balance':
                        # 区分是余额还是账户结余
                        category = record[3]  # 获取category列的值
                        if category == "余额统计":
                            item.setText("余额")
                            item.setForeground(Qt.darkYellow)
                            item.setBackground(MacaronColors.BUTTER_CREAM)  # 使用奶油黄背景
                        else:
                            item.setText("账户结余")
                        item.setForeground(Qt.darkYellow)
                        item.setBackground(MacaronColors.BUTTER_CREAM)
                
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

        # 更新所有借款状态
        self.cursor.execute("SELECT id FROM transactions WHERE type='借款'")
        loans = self.cursor.fetchall()
        for loan_id, in loans:
            self.update_loan_status(loan_id)

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
        
        # 更新窗口标题
        self.update_window_title()
        
        # 重置并重新初始化界面
        self.reset_ui()


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
        """自动备份数据库"""
        backup_file = self.backup_database("auto")
        if backup_file:
            print(f"自动备份成功: {backup_file}")
        else:
            print("自动备份失败")

    def setup_auto_backup_timer(self, interval_hours=1):
        """设置自动备份定时器"""
        if hasattr(self, 'backup_timer'):
            self.backup_timer.stop()
        
        self.backup_timer = QTimer()
        self.backup_timer.timeout.connect(self.auto_backup)
        self.backup_timer.start(interval_hours * 3600000)  # 转换为毫秒

    def manual_backup(self):
        """手动备份数据库"""
        backup_file = self.backup_database("manual")
        if backup_file:
            self.statusBar().showMessage(f"✅ 手动备份成功: {os.path.basename(backup_file)}", 5000)


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

    def show_restore_dialog(self):
        """显示恢复备份对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("恢复数据库备份")
        dialog.resize(800, 600)
        
        layout = QVBoxLayout()
        
        # 备份列表表格
        backup_table = QTableWidget()
        backup_table.setColumnCount(5)
        backup_table.setHorizontalHeaderLabels(["选择", "备份日期", "类型", "大小", "详细信息"])
        backup_table.setSelectionBehavior(QTableWidget.SelectRows)
        backup_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # 加载备份文件
        backups = []
        for f in os.listdir(self.backup_dir):
            if f.startswith(f"finance_{self.current_user}_"):
                file_path = os.path.join(self.backup_dir, f)
                if os.path.isfile(file_path):
                    # 解析备份信息
                    parts = f.split('_')
                    backup_type = parts[2]  # auto or manual
                    timestamp = parts[3].split('.')[0]
                    try:
                        # 从文件名中提取年月日
                        backup_date = datetime.strptime(timestamp, '%Y%m%d')
                        backup_time = backup_date
                    except ValueError:
                        # 如果解析失败，使用文件修改时间
                        backup_time = datetime.fromtimestamp(os.path.getmtime(file_path))

                    size = os.path.getsize(file_path) / 1024  # KB
                    
                    # 获取数据库版本信息（如果可能）
                    version_info = "未知版本"
                    try:
                        if self.db_encrypted:
                            with open(file_path, 'rb') as f_obj:
                                encrypted_data = f_obj.read()
                                decrypted_data = self.cipher_suite.decrypt(encrypted_data)
                                temp_conn = sqlite3.connect(':memory:')
                                temp_conn.executescript(decrypted_data.decode('utf-8'))
                                temp_cursor = temp_conn.cursor()
                                temp_cursor.execute("SELECT version FROM db_version ORDER BY version DESC LIMIT 1")
                                version_result = temp_cursor.fetchone()
                                version_info = f"数据库版本: {version_result[0]}" if version_result else "未知版本"
                                temp_conn.close()
                        else:
                            temp_conn = sqlite3.connect(file_path)
                            temp_cursor = temp_conn.cursor()
                            temp_cursor.execute("SELECT version FROM db_version ORDER BY version DESC LIMIT 1")
                            version_result = temp_cursor.fetchone()
                            version_info = f"数据库版本: {version_result[0]}" if version_result else "未知版本"
                            temp_conn.close()
                    except:
                        version_info = "无法获取版本信息"
                    
                    backups.append((file_path, backup_time, backup_type, size, version_info))

        # 按时间排序，最新的在前
        backups.sort(key=lambda x: x[1], reverse=True)
        
        backup_table.setRowCount(len(backups))
        for row, (file_path, backup_time, backup_type, size, version_info) in enumerate(backups):
            # 选择复选框
            checkbox = QCheckBox()
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            backup_table.setCellWidget(row, 0, checkbox_widget)
            
            # 备份时间
            time_item = QTableWidgetItem(backup_time.strftime('%Y-%m-%d %H:%M:%S'))
            time_item.setData(Qt.UserRole, file_path)  # 存储完整文件路径
            backup_table.setItem(row, 1, time_item)
            
            # 备份类型
            type_item = QTableWidgetItem("自动" if backup_type == "auto" else "手动")
            backup_table.setItem(row, 2, type_item)
            
            # 大小
            size_item = QTableWidgetItem(f"{size:.1f} KB")
            size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            backup_table.setItem(row, 3, size_item)
            
            # 版本信息
            info_item = QTableWidgetItem(version_info)
            backup_table.setItem(row, 4, info_item)
        
        backup_table.resizeColumnsToContents()
        layout.addWidget(backup_table)
        
        # 筛选功能
        filter_layout = QHBoxLayout()
        
        # 备份类型筛选
        type_filter = QComboBox()
        type_filter.addItems(["所有类型", "自动", "手动"])
        type_filter.currentTextChanged.connect(lambda text: self.filter_backup_table(backup_table, backups, text, date_from.date(), date_to.date()))
        filter_layout.addWidget(QLabel("备份类型:"))
        filter_layout.addWidget(type_filter)
        
        # 日期范围筛选
        date_layout = QHBoxLayout()
        date_from = QDateEdit()
        date_from.setDate(QDate.currentDate().addMonths(-1))
        date_from.setCalendarPopup(True)
        date_from.dateChanged.connect(lambda: self.filter_backup_table(backup_table, backups, type_filter.currentText(), date_from.date(), date_to.date()))
        date_layout.addWidget(QLabel("从:"))
        date_layout.addWidget(date_from)
        
        date_to = QDateEdit()
        date_to.setDate(QDate.currentDate())
        date_to.setCalendarPopup(True)
        date_to.dateChanged.connect(lambda: self.filter_backup_table(backup_table, backups, type_filter.currentText(), date_from.date(), date_to.date()))
        date_layout.addWidget(QLabel("到:"))
        date_layout.addWidget(date_to)
        
        filter_layout.addLayout(date_layout)
        layout.addLayout(filter_layout)
        
        # 预览区域
        preview_label = QLabel("备份详细信息将显示在这里")
        preview_label.setWordWrap(True)
        preview_label.setStyleSheet("border: 1px solid #ccc; padding: 10px;")
        layout.addWidget(QLabel("备份详细信息:"))
        layout.addWidget(preview_label)
        
        # 选中备份时更新预览
        backup_table.itemSelectionChanged.connect(lambda: self.update_backup_preview(backup_table, preview_label))
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self.execute_restore(backup_table, dialog))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.setLayout(layout)
        dialog.exec_()

    def filter_backup_table(self, table, backups, filter_type, date_from, date_to):
        """筛选备份表格"""
        for row in range(table.rowCount()):
            file_path = table.item(row, 1).data(Qt.UserRole)
            backup_info = next((b for b in backups if b[0] == file_path), None)
            
            if not backup_info:
                continue
            
            _, backup_date, backup_type, _, _ = backup_info
            show_row = True
            
            # 类型筛选
            if filter_type == "自动" and backup_type != "auto":
                show_row = False
            elif filter_type == "手动" and backup_type != "manual":
                show_row = False
            
            # 日期筛选 - 使用QDate比较
            backup_qdate = QDate(backup_date.year, backup_date.month, backup_date.day)
            if backup_qdate < date_from or backup_qdate > date_to:
                show_row = False
            
            table.setRowHidden(row, not show_row)

    def update_backup_preview(self, table, preview_label):
        """更新备份预览信息"""
        selected = table.selectedItems()
        if not selected:
            preview_label.setText("请选择一个备份查看详细信息")
            return
        
        file_path = selected[0].data(Qt.UserRole)
        
        # 尝试获取数据库信息
        try:
            if self.db_encrypted:
                with open(file_path, 'rb') as f:
                    encrypted_data = f.read()
                    decrypted_data = self.cipher_suite.decrypt(encrypted_data)
                    temp_conn = sqlite3.connect(':memory:')
                    temp_conn.executescript(decrypted_data.decode('utf-8'))
            else:
                temp_conn = sqlite3.connect(file_path)
            
            temp_cursor = temp_conn.cursor()
            
            # 获取交易记录数量
            temp_cursor.execute("SELECT COUNT(*) FROM transactions")
            trans_count = temp_cursor.fetchone()[0]
            
            # 获取最早和最晚交易日期
            temp_cursor.execute("SELECT MIN(date), MAX(date) FROM transactions WHERE type != 'balance'")
            min_date, max_date = temp_cursor.fetchone()
            
            # 获取账户信息
            temp_cursor.execute("SELECT COUNT(*) FROM accounts")
            account_count = temp_cursor.fetchone()[0]
            
            # 获取数据库版本
            temp_cursor.execute("SELECT version FROM db_version ORDER BY version DESC LIMIT 1")
            version_result = temp_cursor.fetchone()
            db_version = version_result[0] if version_result else "未知"
            
            temp_conn.close()
            
            preview_text = f"""
            <b>备份文件:</b> {os.path.basename(file_path)}<br>
            <b>数据库版本:</b> {db_version}<br>
            <b>交易记录数:</b> {trans_count}<br>
            <b>交易日期范围:</b> {min_date} 至 {max_date}<br>
            <b>账户数量:</b> {account_count}
            """
            
            preview_label.setText(preview_text)
        except Exception as e:
            preview_label.setText(f"无法读取备份文件: {str(e)}")


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
        self.update_account_balances()

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
        currency_combo.addItems(["CNY", "USD", "EUR", "JPY", "GBP", "HKD", "TWD"])
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
        dialog.resize(400, 250)  # 增加高度以容纳更多内容
        
        layout = QFormLayout()
        
        # 金额
        amount_edit = QLineEdit()
        amount_edit.setValidator(QtGui.QDoubleValidator())
        layout.addRow("金额:", amount_edit)
        
        # 从货币
        from_currency_combo = QComboBox()
        from_currency_combo.addItems(["CNY", "USD", "EUR", "JPY", "GBP", "HKD", "TWD"])
        layout.addRow("从:", from_currency_combo)
        
        # 到货币
        to_currency_combo = QComboBox()
        to_currency_combo.addItems(["CNY", "USD", "EUR", "JPY", "GBP", "HKD", "TWD"])
        to_currency_combo.setCurrentIndex(1)
        layout.addRow("到:", to_currency_combo)
        
        # 自定义汇率部分
        custom_rate_group = QGroupBox("自定义汇率")
        custom_rate_layout = QFormLayout()
        
        custom_from_combo = QComboBox()
        custom_from_combo.addItems(["CNY", "USD", "EUR", "JPY", "GBP", "HKD", "TWD"])
        custom_rate_layout.addRow("从:", custom_from_combo)
        
        custom_to_combo = QComboBox()
        custom_to_combo.addItems(["CNY", "USD", "EUR", "JPY", "GBP", "HKD", "TWD"])
        custom_rate_layout.addRow("到:", custom_to_combo)
        
        custom_rate_edit = QLineEdit()
        custom_rate_edit.setPlaceholderText("输入汇率")
        custom_rate_edit.setValidator(QtGui.QDoubleValidator())
        custom_rate_layout.addRow("汇率:", custom_rate_edit)
        
        set_rate_btn = QPushButton("设置自定义汇率")
        custom_rate_layout.addRow(set_rate_btn)
        
        custom_rate_group.setLayout(custom_rate_layout)
        layout.addRow(custom_rate_group)
        
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
        
        # 设置自定义汇率按钮事件
        set_rate_btn.clicked.connect(lambda: self.set_custom_rate(
            custom_from_combo, custom_to_combo, custom_rate_edit,
            rate_label
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
        
        if from_currency == to_currency:
            result_label.setText(f"{amount:.2f}")
            rate_label.setText(f"汇率: 1 {from_currency} = 1 {to_currency}")
            return
        
        # 检查是否使用了自定义汇率
        rate_text = rate_label.text()
        if rate_text.startswith("自定义汇率"):
            try:
                # 从标签文本中提取汇率
                custom_rate = float(rate_text.split("=")[1].split()[0])
                result = amount * custom_rate
                result_label.setText(f"{result:.2f}")
                return
            except:
                pass
        
        # 默认汇率（这里应该调用汇率API，为了示例使用固定汇率）
        exchange_rates = {
            "CNY": {"USD": 0.14, "EUR": 0.13, "JPY": 15.4, "GBP": 0.11, "HKD": 1.08, "TWD": 4.34, "CNY": 1},
            "USD": {"CNY": 7.1, "EUR": 0.93, "JPY": 110, "GBP": 0.79, "HKD": 7.8, "TWD": 30.0, "USD": 1},
            "EUR": {"CNY": 7.7, "USD": 1.07, "JPY": 118, "GBP": 0.85, "HKD": 8.4, "TWD": 32.3, "EUR": 1},
            "JPY": {"CNY": 0.065, "USD": 0.0091, "EUR": 0.0085, "GBP": 0.0072, "HKD": 0.071, "TWD": 0.27, "JPY": 1},
            "GBP": {"CNY": 9.1, "USD": 1.27, "EUR": 1.18, "JPY": 139, "HKD": 9.9, "TWD": 38.1, "GBP": 1},
            "HKD": {"CNY": 0.92, "USD": 0.13, "EUR": 0.12, "JPY": 14.1, "GBP": 0.10, "TWD": 3.85, "HKD": 1},
            "TWD": {"CNY": 0.23, "USD": 0.033, "EUR": 0.031, "JPY": 3.7, "GBP": 0.026, "HKD": 0.26, "TWD": 1}
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
        
        # 构建提醒消息
        reminder_text = ""
        
        if pending_loans:
            reminder_text += f"待还款借款: {len(pending_loans)}笔 "
            
        if budgets:
            over_budgets = [b for b in budgets if b[2] and b[2] > b[1]]
            if over_budgets:
                reminder_text += f"预算超支: {len(over_budgets)}个分类 "
        
        if recurring_trans:
            reminder_text += f"待执行定期交易: {len(recurring_trans)}笔"
        
        # 如果有任何提醒，显示在状态栏
        if reminder_text:
            self.statusBar().showMessage(f"提醒: {reminder_text}", 60000)  # 显示60秒
        else:
            self.statusBar().clearMessage()


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

    def reset_ui(self):
        """重置UI界面"""
        # 清除主布局中的所有组件（安全方式）
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 重置关键组件
        self.table = None
        self.search_edit = None
        self.filter_type_combo = None
        self.filter_category_combo = None
        self.filter_account_combo = None
        self.filter_status_combo = None
        self.date_range_combo = None
        self.date_from_edit = None
        self.date_to_edit = None
        
        # 重新创建UI组件
        self.create_search_bar()
        self.create_tabs()
        self.create_input_form()
        self.create_action_buttons()
        
        # 加载数据
        self.load_data()
        self.update_statistics()

    def set_custom_rate(self, from_combo, to_combo, rate_edit, rate_label):
        """设置自定义汇率"""
        from_currency = from_combo.currentText()
        to_currency = to_combo.currentText()
        rate = rate_edit.text().strip()
        
        if not rate:
            QMessageBox.warning(self, "警告", "请输入汇率值")
            return
        
        try:
            rate = float(rate)
            if rate <= 0:
                QMessageBox.warning(self, "警告", "汇率必须大于0")
                return
                
            # 更新汇率显示
            rate_label.setText(f"自定义汇率: 1 {from_currency} = {rate:.4f} {to_currency}")
            rate_edit.clear()
        except ValueError:
            QMessageBox.warning(self, "警告", "请输入有效的汇率数字")

    def create_balance_tab(self):
        """创建账户结余标签页"""
        layout = QVBoxLayout()
        self.balance_tab.setLayout(layout)
        
        # 账户结余表格
        self.balance_table = QTableWidget()
        self.balance_table.setColumnCount(4)
        self.balance_table.setHorizontalHeaderLabels(["账户", "当前余额", "收入总计", "支出总计"])
        self.balance_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.balance_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.balance_table.setAlternatingRowColors(True)
        
        # 设置表格样式
        self.balance_table.setStyleSheet("""
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
        
        layout.addWidget(self.balance_table)
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新账户结余")
        refresh_btn.clicked.connect(self.calculate_and_update_balances)
        layout.addWidget(refresh_btn)
        
        # 初始加载数据
        self.update_account_balances()

    def update_account_balances(self):
        """更新账户结余显示（不进行计算）"""
        if not hasattr(self, 'balance_table'):
            return
        
        # 直接从accounts表获取余额
        self.cursor.execute("""
            SELECT a.id, a.name, a.balance,
                (SELECT SUM(amount) FROM transactions 
                WHERE account_id=a.id AND (type='income' OR type='还款')) as income,
                (SELECT SUM(amount) FROM transactions 
                WHERE account_id=a.id AND (type='expense' OR type='借款')) as expense
            FROM accounts a
            ORDER BY a.name
        """)
        
        accounts = self.cursor.fetchall()
        self.balance_table.setRowCount(len(accounts))
        
        for row, (account_id, name, balance, income, expense) in enumerate(accounts):
            self.balance_table.setItem(row, 0, QTableWidgetItem(name))
            
            balance_item = QTableWidgetItem(f"{balance or 0:.2f}")
            balance_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.balance_table.setItem(row, 1, balance_item)
            
            income_item = QTableWidgetItem(f"{income or 0:.2f}")
            income_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            income_item.setForeground(Qt.darkGreen)
            self.balance_table.setItem(row, 2, income_item)
            
            expense_item = QTableWidgetItem(f"{expense or 0:.2f}")
            expense_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            expense_item.setForeground(Qt.darkRed)
            self.balance_table.setItem(row, 3, expense_item)
        
        self.balance_table.resizeColumnsToContents()


    def calculate_and_update_balances(self):
        """计算并更新所有账户余额"""
        # 保存当前状态以便撤销
        self.save_state_before_change()
        
        # 获取所有账户
        self.cursor.execute("SELECT id, name FROM accounts")
        accounts = self.cursor.fetchall()
        
        for account_id, account_name in accounts:
            # 计算账户余额
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
            
            # 更新账户余额
            self.cursor.execute("""
                UPDATE accounts SET balance=? WHERE id=?
            """, (balance, account_id))
        
        self.conn.commit()
        self.update_account_balances()  # 更新UI显示
        self.statusBar().showMessage("✅ 账户余额已重新计算并更新", 5000)

    def update_future_balances(self, from_date):
        """更新从指定日期开始的所有余额记录"""
        # 1. 更新所有账户的总余额记录
        self.cursor.execute("""
            SELECT DISTINCT date FROM transactions
            WHERE type='balance' AND date >= ?
            ORDER BY date
        """, (from_date,))
        
        balance_dates = [row[0] for row in self.cursor.fetchall()]
        
        for balance_date in balance_dates:
            # 计算新的总余额
            self.cursor.execute("""
                SELECT 
                    SUM(CASE WHEN type='income' THEN amount ELSE 0 END) -
                    SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) +
                    SUM(CASE WHEN type='还款' THEN amount ELSE 0 END) -
                    SUM(CASE WHEN type='借款' THEN amount ELSE 0 END)
                FROM transactions
                WHERE date <= ? AND type != 'balance'
            """, (balance_date,))
            
            new_balance = self.cursor.fetchone()[0] or 0
            
            # 更新总余额记录
            self.cursor.execute("""
                UPDATE transactions 
                SET amount=?
                WHERE type='balance' AND date=? AND account_id IS NULL
            """, (new_balance, balance_date))
        
        # 2. 更新各账户的余额记录
        self.cursor.execute("SELECT id FROM accounts")
        account_ids = [row[0] for row in self.cursor.fetchall()]
        
        for account_id in account_ids:
            self.cursor.execute("""
                SELECT DISTINCT date FROM transactions
                WHERE type='balance' AND account_id=? AND date >= ?
                ORDER BY date
            """, (account_id, from_date))
            
            balance_dates = [row[0] for row in self.cursor.fetchall()]
            
            for balance_date in balance_dates:
                # 计算新的账户余额
                self.cursor.execute("""
                    SELECT 
                        SUM(CASE WHEN type='income' THEN amount ELSE 0 END) -
                        SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) +
                        SUM(CASE WHEN type='还款' THEN amount ELSE 0 END) -
                        SUM(CASE WHEN type='借款' THEN amount ELSE 0 END)
                    FROM transactions
                    WHERE date <= ? AND type != 'balance' AND account_id=?
                """, (balance_date, account_id))
                
                new_balance = self.cursor.fetchone()[0] or 0
                
                # 更新账户余额记录
                self.cursor.execute("""
                    UPDATE transactions 
                    SET amount=?
                    WHERE type='balance' AND date=? AND account_id=?
                """, (new_balance, balance_date, account_id))
        
        self.conn.commit()
        self.update_account_balances()  # 更新UI显示

    def show_add_record_dialog(self):
        """显示添加记录弹窗"""
        dialog = QDialog(self)
        dialog.setWindowTitle("添加新记录")
        dialog.resize(600, 400)
        
        layout = QVBoxLayout()
        
        # 创建表单布局
        form_layout = QFormLayout()
        
        # 类型选择
        type_combo = QComboBox()
        type_combo.addItems(["收入", "支出", "借款", "还款", "余额", "账户结余"])
        form_layout.addRow("类型:", type_combo)
        
        # 金额
        amount_edit = QLineEdit()
        amount_edit.setPlaceholderText("金额")
        form_layout.addRow("金额:", amount_edit)
        
        # 类别
        category_combo = QComboBox()
        form_layout.addRow("类别:", category_combo)
        
        # 账户选择
        account_combo = QComboBox()
        account_combo.addItem("全部结余", -1)
        self.load_account_combo_to(account_combo)
        form_layout.addRow("账户:", account_combo)
        
        # 日期
        date_edit = QDateEdit()
        date_edit.setDate(QDate.currentDate())
        date_edit.setCalendarPopup(True)
        form_layout.addRow("日期:", date_edit)
        
        # 描述
        desc_edit = QLineEdit()
        desc_edit.setPlaceholderText("描述")
        form_layout.addRow("描述:", desc_edit)
        
        # 标签
        tags_edit = QLineEdit()
        tags_edit.setPlaceholderText("标签(逗号分隔)")
        form_layout.addRow("标签:", tags_edit)
        
        # 关联借款选择（仅还款时显示）
        loan_combo = QComboBox()
        loan_combo.setVisible(False)
        form_layout.addRow("关联借款:", loan_combo)
        
        # 收据图片按钮
        receipt_btn = QPushButton("添加收据")
        receipt_image_data = None  # 存储收据图片数据
        
        def add_receipt():
            nonlocal receipt_image_data
            file_name, _ = QFileDialog.getOpenFileName(
                dialog, "选择收据图片", "", 
                "图片文件 (*.png *.jpg *.jpeg *.bmp)"
            )
            
            if file_name:
                try:
                    img = Image.open(file_name)
                    img.thumbnail((800, 800))
                    buffered = io.BytesIO()
                    img.save(buffered, format="JPEG", quality=70)
                    receipt_image_data = base64.b64encode(buffered.getvalue()).decode('utf-8')
                    
                    pixmap = QPixmap(file_name)
                    pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio)
                    receipt_btn.setIcon(QIcon(pixmap))
                    receipt_btn.setIconSize(QSize(100, 100))
                    receipt_btn.setText("收据已添加")
                except Exception as e:
                    QMessageBox.warning(dialog, "错误", f"加载图片失败: {str(e)}")
                    receipt_image_data = None
        
        receipt_btn.clicked.connect(add_receipt)
        form_layout.addRow(receipt_btn)
        
        # 定期交易复选框
        recurring_check = QCheckBox("定期交易")
        recurring_freq_combo = QComboBox()
        recurring_freq_combo.addItems(["每日", "每周", "每月", "每年"])
        recurring_freq_combo.setVisible(False)
        recurring_end_edit = QDateEdit()
        recurring_end_edit.setDate(QDate.currentDate().addYears(1))
        recurring_end_edit.setCalendarPopup(True)
        recurring_end_edit.setVisible(False)
        
        def toggle_recurring(state):
            visible = state == Qt.Checked
            recurring_freq_combo.setVisible(visible)
            recurring_end_edit.setVisible(visible)
            # 更新频率和结束日期的标签可见性
            for i in range(form_layout.rowCount()):
                item = form_layout.itemAt(i, QFormLayout.LabelRole)
                if item and item.widget() and item.widget().text() in ["频率:", "结束于:"]:
                    item.widget().setVisible(visible)
        
        recurring_check.stateChanged.connect(toggle_recurring)
    
        # 添加定期交易相关控件
        freq_label = QLabel("频率:")
        freq_label.setVisible(False)
        form_layout.addRow(freq_label, recurring_freq_combo)
        
        end_label = QLabel("结束于:")
        end_label.setVisible(False)
        form_layout.addRow(end_label, recurring_end_edit)

        form_layout.addRow(recurring_check)
        
        # 更新类别下拉框
        def update_category_combo(type_text):
            type_map = {
                "收入": "income",
                "支出": "expense",
                "借款": "expense",
                "还款": "income"
            }
            db_type = type_map.get(type_text, "income")
            
            category_combo.clear()
            self.cursor.execute(
                "SELECT name FROM categories WHERE type=? ORDER BY name",
                (db_type,)
            )
            categories = [row[0] for row in self.cursor.fetchall()]
            
            if db_type == "expense" and "其他" not in categories:
                categories.append("其他")
            if db_type == "income" and "其他" not in categories:
                categories.append("其他")
                
            category_combo.addItems(categories)
            
            # 如果是支出或借款类型，默认选择"其他"
            if type_text in ["支出", "借款"] and "其他" in categories:
                index = category_combo.findText("其他")
                if index >= 0:
                    category_combo.setCurrentIndex(index)
        
        type_combo.currentTextChanged.connect(update_category_combo)
        update_category_combo(type_combo.currentText())
        
        # 更新关联借款选择框
        def update_loan_combo():
            loan_combo.clear()
            self.cursor.execute("""
                SELECT id, amount, description, date 
                FROM transactions 
                WHERE type='借款' AND status='pending'
                ORDER BY date
            """)
            loans = self.cursor.fetchall()
            
            if not loans:
                loan_combo.addItem("无待还款借款", None)
            else:
                for loan in loans:
                    loan_combo.addItem(
                        f"ID:{loan[0]} 金额:{loan[1]} 日期:{loan[3]} 描述:{loan[2]}", 
                        loan[0]
                    )
        
        def update_form(type_text):
            """根据类型更新表单"""
            update_category_combo(type_text)
            
            if type_text == "还款":
                loan_combo.setVisible(True)
                update_loan_combo()
            else:
                loan_combo.setVisible(False)
            
            # 处理账户下拉框状态
            if type_text == "余额":
                index = account_combo.findData(-1)
                if index >= 0:
                    account_combo.setCurrentIndex(index)
                account_combo.setEnabled(False)
            elif type_text == "账户结余":
                account_combo.setEnabled(True)
                if account_combo.currentData() == -1:
                    account_combo.setCurrentIndex(1 if account_combo.count() > 1 else 0)
            else:
                account_combo.setEnabled(True)
                if account_combo.currentData() == -1:
                    account_combo.setCurrentIndex(1 if account_combo.count() > 1 else 0)
            
            # 余额类型禁用金额输入
            if type_text in ["余额", "账户结余"]:
                amount_edit.setEnabled(False)
                amount_edit.clear()
            else:
                amount_edit.setEnabled(True)
        
        type_combo.currentTextChanged.connect(update_form)
        update_form(type_combo.currentText())
        
        layout.addLayout(form_layout)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.setLayout(layout)
        
        if dialog.exec_() == QDialog.Accepted:
            # 收集表单数据
            type_text = type_combo.currentText()
            amount_text = amount_edit.text().strip()
            category = category_combo.currentText()
            account_id = account_combo.currentData()
            date = date_edit.date().toString("yyyy-MM-dd")
            description = desc_edit.text().strip()
            tags = tags_edit.text().strip()
            is_recurring = recurring_check.isChecked()
            recurring_freq = recurring_freq_combo.currentText() if is_recurring else None
            recurring_end = recurring_end_edit.date().toString("yyyy-MM-dd") if is_recurring else None
            
            # 调用原来的添加记录逻辑
            self.add_record_from_dialog(
                type_text, amount_text, category, account_id, date, 
                description, tags, receipt_image_data, is_recurring, 
                recurring_freq, recurring_end, loan_combo.currentData()
            )

    def add_record_from_dialog(self, type_text, amount_text, category, account_id, date, 
                            description, tags, receipt_image_data, is_recurring, 
                            recurring_freq, recurring_end, loan_id=None):
        """从弹窗添加记录的核心逻辑"""
        # 处理余额记录（计算所有账户总余额）
        if type_text == "余额":
            # 保存当前状态以便撤销
            self.save_state_before_change()
            
            # 计算所有账户的总余额
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
                VALUES (?, ?, ?, ?, ?, NULL)
            ''', ('balance', amount, "余额统计", f"截至 {date} 的总余额", date))
            self.conn.commit()
            
            self.statusBar().showMessage(f"✅ 总余额记录已添加: {amount:.2f} 元", 5000)
            
            # 清空输入并刷新数据
            self.load_data()
            self.update_statistics()
            return
        
        # 处理账户结余记录（计算特定账户余额）
        if type_text == "账户结余":
            # 保存当前状态以便撤销
            self.save_state_before_change()
            
            # 计算特定账户的余额
            self.cursor.execute("""
                SELECT 
                    SUM(CASE WHEN type='income' THEN amount ELSE 0 END) -
                    SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) +
                    SUM(CASE WHEN type='还款' THEN amount ELSE 0 END) -
                    SUM(CASE WHEN type='借款' THEN amount ELSE 0 END)
                FROM transactions
                WHERE date <= ? AND type != 'balance' AND account_id = ?
            """, (date, account_id))
            
            amount = self.cursor.fetchone()[0] or 0
            
            # 添加账户结余记录
            self.cursor.execute('''
                INSERT INTO transactions 
                (type, amount, category, description, date, account_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', ('balance', amount, "账户结余统计", f"截至 {date} 的账户结余", date, account_id))
            self.conn.commit()
            
            self.statusBar().showMessage(f"✅ 账户结余记录已添加: {amount:.2f} 元", 5000)
            
            # 清空输入并刷新数据
            self.load_data()
            self.update_statistics()
            return
        
        # 对于非余额/账户结余记录，验证金额输入
        if not amount_text:
            self.statusBar().showMessage("⚠️ 请输入金额!", 5000)
            return
        
        try:
            amount = float(amount_text)
            if amount <= 0:
                self.statusBar().showMessage("❌ 金额必须大于0!", 5000)
                return
        except ValueError:
            self.statusBar().showMessage("❌ 金额必须是有效数字!", 5000)
            return
        
        # 日期不能晚于今天
        if QDate.fromString(date, "yyyy-MM-dd") > QDate.currentDate():
            self.statusBar().showMessage("❌ 日期不能晚于今天!", 5000)
            return
        
        # 描述长度限制
        if len(description) > 100:
            self.statusBar().showMessage("❌ 描述不能超过100个字符!", 5000)
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
                receipt_image_data, is_recurring, recurring_freq, recurring_end))
            self.conn.commit()
            
            self.statusBar().showMessage("✅ 借款记录已添加!", 5000)
        
        elif type_text == "还款":
            # 添加还款记录并关联借款
            if not loan_id:
                self.statusBar().showMessage("❌ 没有可关联的借款!", 5000)
                return
            
            # 检查还款金额是否超过剩余应还金额
            remaining = self.get_remaining_loan_amount(loan_id)
            if amount > remaining:
                # 询问用户是否要处理超额部分
                reply = QMessageBox.question(
                    self, "超额还款", 
                    f"还款金额超过剩余应还金额 {remaining:.2f} 元，是否将超额部分({amount-remaining:.2f}元)记录为收入?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    try:
                        # 1. 添加还款记录（仅还剩余金额）
                        self.cursor.execute('''
                            INSERT INTO transactions 
                            (type, amount, category, description, date, related_id, account_id, tags, 
                            receipt_image, is_recurring, recurring_freq, recurring_end)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', ('还款', remaining, category, description, date, loan_id, account_id, tags,
                            receipt_image_data, 0, None, None))
                        
                        # 2. 添加收入记录（超额部分）
                        overpayment = amount - remaining
                        self.cursor.execute('''
                            INSERT INTO transactions 
                            (type, amount, category, description, date, account_id)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', ('income', overpayment, "退款", 
                            f"借款ID:{loan_id}还款超额退款", 
                            date, account_id))
                        
                        self.conn.commit()
                        self.statusBar().showMessage(f"✅ 还款记录已添加，超额部分({overpayment:.2f}元)已记录为收入!", 5000)
                    except Exception as e:
                        self.conn.rollback()
                        self.statusBar().showMessage(f"❌ 处理超额还款失败: {str(e)}", 5000)
                        return
                else:
                    return
            else:
                # 正常添加还款记录
                self.cursor.execute('''
                    INSERT INTO transactions 
                    (type, amount, category, description, date, related_id, account_id, tags, 
                    receipt_image, is_recurring, recurring_freq, recurring_end)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', ('还款', amount, category, description, date, loan_id, account_id, tags,
                    receipt_image_data, 0, None, None))
                
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
                receipt_image_data, is_recurring, recurring_freq, recurring_end))
            self.conn.commit()
            
            self.statusBar().showMessage(f"✅ {type_text}记录已添加!", 5000)
        
        # 更新账户余额和后续日期的余额记录
        if account_id and account_id != -1:  # 不更新"全部结余"的账户余额
            self.update_account_balance(account_id)
        
        # 更新后续日期的余额记录
        if type_text in ["收入", "支出", "借款", "还款"]:
            self.update_future_balances(date)
        
        self.update_account_balances()
        self.load_data()
        self.update_loan_combo()
        self.update_statistics()


    def update_window_title(self):
        """更新窗口标题以包含当前用户信息"""
        if hasattr(self, 'current_user'):
            self.setWindowTitle(f"{ProjectInfo.NAME} {ProjectInfo.VERSION} - 当前用户: {self.current_user}")
        else:
            self.setWindowTitle(f"{ProjectInfo.NAME} {ProjectInfo.VERSION}")

    def backup_database(self, backup_type="auto"):
        """执行数据库备份"""
        timestamp = datetime.now().strftime('%Y%m%d')  # 只使用年月日部分
        backup_name = f"{self.backup_dir}/finance_{self.current_user}_{backup_type}_{timestamp}.db"
        
        try:
            if self.db_encrypted:
                # 对于加密数据库，导出内存数据库
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
                # 对于非加密数据库，直接复制文件
                db_file = f'finance_{self.current_user}.db'
                shutil.copy2(db_file, backup_name)
            
            # 清理旧备份
            self.cleanup_old_backups()
            
            return backup_name
        except Exception as e:
            self.statusBar().showMessage(f"❌ 备份失败: {str(e)}", 5000)
            return None

    def cleanup_old_backups(self):
        """清理超过限制的旧备份"""
        # 获取所有备份文件
        backups = []
        for f in os.listdir(self.backup_dir):
            if f.startswith(f"finance_{self.current_user}_"):
                file_path = os.path.join(self.backup_dir, f)
                if os.path.isfile(file_path):
                    backups.append((file_path, os.path.getmtime(file_path)))
        
        # 按修改时间排序，最新的在前
        backups.sort(key=lambda x: x[1], reverse=True)
        
        # 删除超过限制的旧备份
        while len(backups) > self.max_backups:
            old_file = backups.pop()
            try:
                os.remove(old_file[0])
            except Exception as e:
                print(f"删除旧备份失败: {str(e)}")

    def execute_restore(self, backup_table, dialog):
        """执行备份恢复"""
        selected_backup = None
        
        # 查找选中的备份
        for row in range(backup_table.rowCount()):
            checkbox = backup_table.cellWidget(row, 0).findChild(QCheckBox)
            if checkbox and checkbox.isChecked():
                selected_backup = backup_table.item(row, 1).data(Qt.UserRole)
                break
        
        if not selected_backup:
            self.statusBar().showMessage("❌ 请选择一个备份文件!", 5000)
            return
        
        # 确认对话框
        reply = QMessageBox.question(
            self, '确认恢复',
            '恢复备份将覆盖当前数据库，确定要继续吗？',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 先备份当前数据库
            current_backup = self.backup_database("before_restore")
            
            try:
                # 关闭当前数据库连接
                if hasattr(self, 'conn'):
                    self.conn.close()
                
                if self.db_encrypted:
                    # 对于加密数据库，从备份文件加载到内存
                    with open(selected_backup, 'rb') as f:
                        encrypted_data = f.read()
                    decrypted_data = self.cipher_suite.decrypt(encrypted_data)
                    
                    self.conn = sqlite3.connect(':memory:')
                    self.conn.executescript(decrypted_data.decode('utf-8'))
                else:
                    # 对于非加密数据库，直接复制备份文件
                    shutil.copy2(selected_backup, f'finance_{self.current_user}.db')
                    self.conn = sqlite3.connect(f'finance_{self.current_user}.db')
                
                self.cursor = self.conn.cursor()
                
                # 重新加载数据
                self.load_data()
                self.update_statistics()
                self.update_account_balances()
                
                dialog.accept()
                self.statusBar().showMessage("✅ 数据库已从备份恢复!", 5000)
            except Exception as e:
                # 恢复失败，尝试恢复原来的数据库
                self.statusBar().showMessage(f"❌ 恢复失败: {str(e)}", 5000)
                
                if current_backup:
                    try:
                        if self.db_encrypted:
                            with open(current_backup, 'rb') as f:
                                encrypted_data = f.read()
                            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
                            
                            self.conn = sqlite3.connect(':memory:')
                            self.conn.executescript(decrypted_data.decode('utf-8'))
                        else:
                            shutil.copy2(current_backup, f'finance_{self.current_user}.db')
                            self.conn = sqlite3.connect(f'finance_{self.current_user}.db')
                        
                        self.cursor = self.conn.cursor()
                        self.statusBar().showMessage("✅ 已恢复原来的数据库", 5000)
                    except:
                        self.statusBar().showMessage("❌ 恢复失败且无法恢复原数据库!", 5000)
                        
                # 重新初始化数据库连接
                self.init_current_user_db(self.current_user)

    def setup_auto_backup_settings(self):
        """设置自动备份参数"""
        dialog = QDialog(self)
        dialog.setWindowTitle("自动备份设置")
        dialog.resize(400, 200)
        
        layout = QFormLayout()
        
        # 备份数量限制
        backup_count_spin = QSpinBox()
        backup_count_spin.setRange(1, 100)
        backup_count_spin.setValue(self.max_backups)
        layout.addRow("最大备份数量:", backup_count_spin)
        
        # 备份间隔
        interval_combo = QComboBox()
        interval_combo.addItems(["每小时", "每天", "每周", "每月"])
        interval_combo.setCurrentIndex(0)  # 默认每小时
        layout.addRow("备份间隔:", interval_combo)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addRow(button_box)
        
        dialog.setLayout(layout)
        
        if dialog.exec_() == QDialog.Accepted:
            self.max_backups = backup_count_spin.value()
            
            # 设置备份间隔
            interval_mapping = {
                "每小时": 1,
                "每天": 24,
                "每周": 168,
                "每月": 720
            }
            interval_hours = interval_mapping[interval_combo.currentText()]
            self.setup_auto_backup_timer(interval_hours)
            
            self.statusBar().showMessage(f"✅ 自动备份设置已保存: 保留{self.max_backups}份备份，每{interval_combo.currentText()}备份一次", 5000)

    def get_remaining_loan_amount(self, loan_id):
        """计算指定借款的剩余未还金额"""
        # 获取借款金额
        self.cursor.execute("SELECT amount FROM transactions WHERE id=?", (loan_id,))
        loan_amount = self.cursor.fetchone()[0]
        
        # 获取已还款总额
        self.cursor.execute("SELECT SUM(amount) FROM transactions WHERE type='还款' AND related_id=?", (loan_id,))
        repaid_amount = self.cursor.fetchone()[0] or 0
        
        # 计算剩余金额
        remaining = loan_amount - repaid_amount
        return max(0, remaining)  # 确保不为负数

    def adjust_overpayment(self, repayment_id):
        """调整超额还款"""
        # 获取还款记录详情
        self.cursor.execute("""
            SELECT amount, related_id FROM transactions WHERE id=?
        """, (repayment_id,))
        repayment = self.cursor.fetchone()
        
        if not repayment:
            return False
            
        repayment_amount, loan_id = repayment
        
        # 获取借款详情
        self.cursor.execute("""
            SELECT amount FROM transactions WHERE id=?
        """, (loan_id,))
        loan_amount = self.cursor.fetchone()[0]
        
        # 计算已还款总额（不包括当前还款记录）
        self.cursor.execute("""
            SELECT SUM(amount) FROM transactions 
            WHERE type='还款' AND related_id=? AND id != ?
        """, (loan_id, repayment_id))
        repaid_amount = self.cursor.fetchone()[0] or 0
        
        # 计算超额金额
        overpayment = (repaid_amount + repayment_amount) - loan_amount
        
        if overpayment <= 0:
            return False  # 没有超额
        
        # 保存当前状态以便撤销
        self.save_state_before_change()
        
        try:
            # 1. 调整当前还款记录金额
            adjusted_amount = repayment_amount - overpayment
            self.cursor.execute("""
                UPDATE transactions SET amount=?
                WHERE id=?
            """, (adjusted_amount, repayment_id))
            
            # 2. 创建一条新的收入记录来处理超额部分
            self.cursor.execute('''
                INSERT INTO transactions 
                (type, amount, category, description, date, account_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', ('income', overpayment, "退款", 
                f"借款ID:{loan_id}还款超额退款", 
                QDate.currentDate().toString("yyyy-MM-dd"),
                self.get_account_id_for_loan(loan_id)))
            
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            self.statusBar().showMessage(f"❌ 调整超额还款失败: {str(e)}", 5000)
            return False

    def get_account_id_for_loan(self, loan_id):
        """获取借款记录关联的账户ID"""
        self.cursor.execute("SELECT account_id FROM transactions WHERE id=?", (loan_id,))
        result = self.cursor.fetchone()
        return result[0] if result else None


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