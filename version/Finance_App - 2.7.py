import sys
import sqlite3
import shutil
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                             QMessageBox, QComboBox, QDateEdit, QTabWidget, QTextEdit,
                             QAction, QFileDialog, QDialog, QFormLayout, QDialogButtonBox,
                             QStackedWidget, QGroupBox, QInputDialog, QListWidget)
from PyQt5.QtCore import Qt, QDate, QTimer
from PyQt5.QtGui import QIcon, QColor
import pypinyin

class ProjectInfo:
    """项目信息元数据（集中管理所有项目相关信息）"""
    VERSION = "2.7.0"
    BUILD_DATE = "2025-05-15"
    AUTHOR = "杜玛"
    LICENSE = "MIT"
    COPYRIGHT = "© 永久 杜玛"
    URL = "https://github.com/duma520"
    MAINTAINER_EMAIL = "不提供"
    NAME = "人民币收支管理系统"
    DESCRIPTION = "人民币收支管理系统"


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
        self.resize(300, 200)
        
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
        
        self.resize(1000, 700)


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

    def init_user_db(self):
        """初始化用户数据库"""
        self.master_conn = sqlite3.connect('finance_master.db')
        self.master_cursor = self.master_conn.cursor()
        
        # 创建用户表
        self.master_cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
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
        
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        
        # 创建交易表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,  -- 'income' or 'expense' or 'loan' or 'repayment'
                amount REAL NOT NULL,
                category TEXT,
                description TEXT,
                date TEXT NOT NULL,
                related_id INTEGER,  -- 用于关联借款和还款
                status TEXT,  -- 'pending' or 'settled'
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER REFERENCES users(id)
            )
        ''')
        
        # 创建分类表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                type TEXT NOT NULL,  -- 'income' or 'expense'
                user_id INTEGER REFERENCES users(id)
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
                ('其他', 'expense')
            ]
            for name, type_ in default_categories:
                self.cursor.execute(
                    "INSERT OR IGNORE INTO categories (name, type) VALUES (?, ?)",
                    (name, type_)
                )

        # 创建配置表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')

        self.conn.commit()

    def show_login_dialog(self):
        """显示登录对话框"""
        self.master_cursor.execute("SELECT username FROM users")
        users = [row[0] for row in self.master_cursor.fetchall()]
        
        login_dialog = LoginDialog(self)
        login_dialog.load_users(users)
        
        if login_dialog.exec_() == QDialog.Accepted:
            username = login_dialog.user_combo.currentText()
            new_user = login_dialog.new_user_edit.text().strip()
            
            if new_user:
                # 创建新用户
                try:
                    self.master_cursor.execute(
                        "INSERT INTO users (username) VALUES (?)",
                        (new_user,)
                    )
                    self.master_conn.commit()
                    username = new_user
                except sqlite3.IntegrityError:
                    QMessageBox.warning(self, "警告", "用户名已存在!")
                    return self.show_login_dialog()
            
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
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        stats_layout.addWidget(self.stats_text)
        
        # 图表类型选择
        chart_type_layout = QHBoxLayout()
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems(["收支趋势", "分类占比", "借款还款"])
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

    def load_categories(self):
        """加载分类数据到筛选框"""
        self.filter_category_combo.clear()
        self.filter_category_combo.addItem("所有分类")
        
        self.cursor.execute("SELECT DISTINCT name FROM categories ORDER BY name")
        categories = [row[0] for row in self.cursor.fetchall()]
        
        for category in categories:
            self.filter_category_combo.addItem(category)

    def create_data_table(self):
        """创建数据表格"""
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["ID", "类型", "金额", "类别", "描述", "日期", "状态", "关联ID"])
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

    def create_input_form(self):
        """创建输入表单"""
        form_layout = QHBoxLayout()
        
        # 类型选择
        self.type_combo = QComboBox()
        self.type_combo.addItems(["收入", "支出", "借款", "还款"])
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
        
        # 关联借款选择（仅还款时显示）
        self.loan_combo = QComboBox()
        self.loan_combo.setVisible(False)
        form_layout.addWidget(QLabel("关联借款:"))
        form_layout.addWidget(self.loan_combo)
        
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
            QMessageBox.warning(self, "警告", "请选择类别!")
            self.category_combo.setFocus()
            return
        
        date = self.date_edit.date().toString("yyyy-MM-dd")
        description = self.desc_edit.text().strip()
        
        # 验证输入
        if not amount_text:
            QMessageBox.warning(self, "警告", "请输入金额!")
            self.amount_edit.setFocus()
            return
        
        try:
            amount = float(amount_text)
            if amount <= 0:
                QMessageBox.warning(self, "警告", "金额必须大于0!")
                self.amount_edit.selectAll()
                self.amount_edit.setFocus()
                return
        except ValueError:
            QMessageBox.warning(self, "警告", "金额必须是有效数字!")
            self.amount_edit.selectAll()
            self.amount_edit.setFocus()
            return
        
        # 日期不能晚于今天
        if self.date_edit.date() > QDate.currentDate():
            QMessageBox.warning(self, "警告", "日期不能晚于今天!")
            self.date_edit.setFocus()
            return
        
        # 描述长度限制
        if len(description) > 100:
            QMessageBox.warning(self, "警告", "描述不能超过100个字符!")
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
                (type, amount, category, description, date, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', ('借款', amount, category, description, date, 'pending'))
            self.conn.commit()
            
            QMessageBox.information(self, "成功", "借款记录已添加!")
        
        elif type_text == "还款":
            # 添加还款记录并关联借款
            loan_id = self.loan_combo.currentData()
            if not loan_id:
                QMessageBox.warning(self, "警告", "没有可关联的借款!")
                return
            
            # 添加还款记录
            self.cursor.execute('''
                INSERT INTO transactions 
                (type, amount, category, description, date, related_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', ('还款', amount, category, description, date, loan_id))
            
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
                QMessageBox.information(self, "成功", "借款已全部还清!")
            else:
                QMessageBox.information(self, "成功", "还款记录已添加!")
            
            self.conn.commit()
        
        else:
            # 普通收入或支出
            db_type = 'income' if type_text == "收入" else 'expense'
            self.cursor.execute('''
                INSERT INTO transactions 
                (type, amount, category, description, date)
                VALUES (?, ?, ?, ?, ?)
            ''', (db_type, amount, category, description, date))
            self.conn.commit()
            
            QMessageBox.information(self, "成功", f"{type_text}记录已添加!")
        
        # 清空输入并刷新数据
        self.amount_edit.clear()
        self.desc_edit.clear()
        self.load_data()
        self.update_loan_combo()
        self.update_statistics()

    def delete_record(self):
        """删除选中的记录(支持多选)"""
        selected_rows = set()
        for item in self.table.selectedItems():
            selected_rows.add(item.row())
        
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请选择要删除的记录!")
            return
        
        # 收集所有选中的记录ID
        record_ids = []
        for row in selected_rows:
            record_id = int(self.table.item(row, 0).text())
            record_ids.append(record_id)
        
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
            QMessageBox.warning(
                self, "警告", 
                f"不能删除未还清的借款记录(ID: {', '.join(pending_loans)})!"
            )
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
            QMessageBox.warning(self, "警告", "请选择要结算的记录!")
            return
        
        row = selected[0].row()
        record_id = int(self.table.item(row, 0).text())
        
        # 检查是否是借款记录
        self.cursor.execute('''
            SELECT type FROM transactions WHERE id=?
        ''', (record_id,))
        record_type = self.cursor.fetchone()[0]
        
        if record_type != '借款':
            QMessageBox.warning(self, "警告", "只能结算借款记录!")
            return
        
        # 保存当前状态以便撤销
        self.save_state_before_change()
        
        # 标记为已结算
        self.cursor.execute('''
            UPDATE transactions SET status='settled' WHERE id=?
        ''', (record_id,))
        self.conn.commit()
        
        QMessageBox.information(self, "成功", "借款记录已标记为已结清!")
        self.load_data()
        self.update_loan_combo()
        self.update_statistics()

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
        filter_status = self.filter_status_combo.currentText()
        
        # 构建基础查询
        query = """
            SELECT id, type, amount, category, description, date, 
                CASE WHEN status IS NULL THEN '' ELSE status END,
                CASE WHEN related_id IS NULL THEN '' ELSE related_id END
            FROM transactions
        """
        
        # 构建WHERE条件
        conditions = []
        params = []
        
        # 日期条件（如果不是"全部时间"）
        if self.date_range_combo.currentIndex() != 0:  # 不是"全部时间"
            date_from = self.date_from_edit.date().toString("yyyy-MM-dd")
            date_to = self.date_to_edit.date().toString("yyyy-MM-dd")
            conditions.append("date BETWEEN ? AND ?")
            params.extend([date_from, date_to])
        
        # 类型筛选
        if filter_type != "所有类型":
            type_map = {
                "收入": "income",
                "支出": "expense",
                "借款": "借款",
                "还款": "还款"
            }
            conditions.append("type=?")
            params.append(type_map[filter_type])
        
        # 分类筛选
        if filter_category != "所有分类":
            conditions.append("category=?")
            params.append(filter_category)
        
        # 状态筛选
        if filter_status == "待还款":
            conditions.append("status='pending'")
        elif filter_status == "已结清":
            conditions.append("status='settled'")
        
        # 搜索文本筛选
        if search_text:
            # 支持中文、拼音首字母和英文搜索
            search_conditions = []
            search_params = []
            
            # 1. 直接匹配描述
            search_conditions.append("description LIKE ?")
            search_params.append(f"%{search_text}%")
            
            # 2. 匹配金额
            search_conditions.append("CAST(amount AS TEXT) LIKE ?")
            search_params.append(f"%{search_text}%")
            
            # 3. 匹配分类
            search_conditions.append("category LIKE ?")
            search_params.append(f"%{search_text}%")
            
            # 4. 拼音首字母匹配
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
                    pinyin_condition.append("description IN (" + ",".join(["?"]*len(pinyin_descriptions)) + ")")
                    pinyin_params.extend(pinyin_descriptions)
                    
                if pinyin_categories:
                    if pinyin_descriptions:
                        pinyin_condition.append("OR")
                    pinyin_condition.append("category IN (" + ",".join(["?"]*len(pinyin_categories)) + ")")
                    pinyin_params.extend(pinyin_categories)
                
                search_conditions.append("(" + " ".join(pinyin_condition) + ")")
                search_params.extend(pinyin_params)
            
            conditions.append("(" + " OR ".join(search_conditions) + ")")
            params.extend(search_params)
        
        # 组合所有条件
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        # 排序
        query += " ORDER BY date DESC, id DESC"
        
        # 执行查询
        self.cursor.execute(query, params)
        records = self.cursor.fetchall()
        
        # 更新表格
        self.table.setRowCount(len(records))
        for row, record in enumerate(records):
            for col, value in enumerate(record):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                
                # 根据类型设置颜色
                if col == 1:  # 类型列
                    if value == 'income':
                        item.setText("收入")
                        item.setForeground(Qt.darkGreen)
                        item.setBackground(MacaronColors.MINT_GREEN)  # 薄荷绿背景
                    elif value == 'expense':
                        item.setText("支出")
                        item.setForeground(Qt.darkRed)
                        item.setBackground(MacaronColors.ROSE_PINK)   # 玫瑰粉背景
                    elif value == '借款':
                        item.setForeground(Qt.darkBlue)
                        item.setBackground(MacaronColors.LAVENDER)   # 薰衣草紫背景
                    elif value == '还款':
                        item.setForeground(Qt.darkMagenta)
                        item.setBackground(MacaronColors.SKY_BLUE)   # 天空蓝背景
                
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
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                
                self.table.setItem(row, col, item)
        
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
        
        # 借款还款明细
        if chart_type == "借款还款":
            self.cursor.execute("""
                SELECT id, amount, description, date, status
                FROM transactions
                WHERE type='借款' AND date BETWEEN ? AND ?
                ORDER BY date
            """, (date_from, date_to))
            
            loans = self.cursor.fetchall()
            
            if loans:
                stats_html += """
                <h3>借款明细</h3>
                <table>
                    <tr><th>ID</th><th>金额</th><th>描述</th><th>日期</th><th>状态</th><th>已还款</th></tr>
                """
                
                for loan in loans:
                    loan_id, amount, desc, date, status = loan
                    
                    # 状态显示为中文
                    status_text = "待还款" if status == "pending" else "已结清" if status == "settled" else status

                    self.cursor.execute("""
                        SELECT SUM(amount) FROM transactions
                        WHERE type='还款' AND related_id=?
                    """, (loan_id,))
                    repaid = self.cursor.fetchone()[0] or 0
                    
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
        
        stats_html += """
        </body>
        </html>
        """
        
        self.stats_text.setHtml(stats_html)

    def switch_user(self):
        """切换用户"""
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
            self.conn.close()

    def auto_backup(self):
        """自动备份数据"""
        backup_dir = "backups"
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        backup_name = f"{backup_dir}/finance_{self.current_user}_auto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        try:
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
            shutil.copy2(f'finance_{self.current_user}.db', backup_name)
            QMessageBox.information(self, "成功", f"数据已备份为: {backup_name}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"备份失败: {str(e)}")

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
            QMessageBox.information(self, "成功", f"已设置为{interval}自动备份")

    def restore_data(self):
        """恢复数据库"""
        backup_dir = "backups"
        if not os.path.exists(backup_dir):
            QMessageBox.warning(self, "警告", "备份目录不存在!")
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
                    shutil.copy2(file_name, f'finance_{self.current_user}.db')
                    self.conn = sqlite3.connect(f'finance_{self.current_user}.db')
                    self.cursor = self.conn.cursor()
                    self.load_data()
                    self.update_statistics()
                    QMessageBox.information(self, "成功", "数据恢复成功!")
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"恢复失败: {str(e)}")
                    self.conn = sqlite3.connect(f'finance_{self.current_user}.db')
                    self.cursor = self.conn.cursor()

    def save_state_before_change(self):
        """保存当前数据库状态以便撤销"""
        # 只保留最近的10次操作记录
        if len(self.operation_stack) >= 10:
            self.operation_stack.pop(0)
        
        # 保存当前数据库状态
        backup_file = f"temp_undo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2(f'finance_{self.current_user}.db', backup_file)
        self.operation_stack.append(backup_file)

    def undo_last_operation(self):
        """撤销最后一次操作"""
        if not self.operation_stack:
            QMessageBox.warning(self, "警告", "没有可撤销的操作!")
            return
        
        backup_file = self.operation_stack.pop()
        
        try:
            self.close_current_db()
            shutil.copy2(backup_file, f'finance_{self.current_user}.db')
            self.conn = sqlite3.connect(f'finance_{self.current_user}.db')
            self.cursor = self.conn.cursor()
            self.load_data()
            self.update_statistics()
            QMessageBox.information(self, "成功", "已撤销最后一次操作!")
            
            # 删除临时文件
            os.remove(backup_file)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"撤销失败: {str(e)}")
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
                    QMessageBox.warning(dialog, "警告", "分类已存在!")

    def delete_category(self, dialog):
        """删除分类"""
        selected = self.category_list.currentItem()
        if not selected:
            QMessageBox.warning(dialog, "警告", "请选择要删除的分类!")
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
            QMessageBox.warning(
                dialog, "警告", 
                f"有{count}条交易记录使用此分类，无法删除!"
            )
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

    def closeEvent(self, event):
        """关闭窗口时清理资源"""
        # 保存配置
        self.save_settings()

        # 停止自动备份定时器
        self.backup_timer.stop()
        
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