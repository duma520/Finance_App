import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                             QMessageBox, QComboBox, QDateEdit)
from PyQt5.QtCore import Qt, QDate
import sqlite3

class FinanceApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("人民币收支管理系统")
        self.resize(800, 600)
        
        # 初始化数据库
        self.init_db()
        
        # 创建主界面
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        
        # 主布局
        self.main_layout = QVBoxLayout()
        self.main_widget.setLayout(self.main_layout)
        
        # 创建输入表单
        self.create_input_form()
        
        # 创建操作按钮
        self.create_action_buttons()
        
        # 创建数据表格
        self.create_data_table()
        
        # 加载数据
        self.load_data()

    def init_db(self):
        """初始化数据库"""
        self.conn = sqlite3.connect('finance.db')
        self.cursor = self.conn.cursor()
        
        # 创建表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,  -- 'income' or 'expense'
                amount REAL NOT NULL,
                category TEXT,
                description TEXT,
                date TEXT NOT NULL,
                related_id INTEGER,  -- 用于关联借款和还款
                status TEXT  -- 'pending' or 'settled'
            )
        ''')
        self.conn.commit()

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
        self.category_combo.addItems(["工资", "餐饮", "交通", "购物", "娱乐", "其他"])
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

    def update_form(self, type_text):
        """根据选择的类型更新表单"""
        if type_text == "还款":
            self.loan_combo.setVisible(True)
            self.update_loan_combo()
        else:
            self.loan_combo.setVisible(False)

    def update_loan_combo(self):
        """更新借款选择框"""
        self.loan_combo.clear()
        self.cursor.execute("SELECT id, amount, description FROM transactions WHERE type='借款' AND status='pending'")
        loans = self.cursor.fetchall()
        
        if not loans:
            self.loan_combo.addItem("无待还款借款", None)
        else:
            for loan in loans:
                self.loan_combo.addItem(f"借款ID:{loan[0]} 金额:{loan[1]} 描述:{loan[2]}", loan[0])

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

    def create_data_table(self):
        """创建数据表格"""
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "类型", "金额", "类别", "描述", "日期", "状态"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        self.main_layout.addWidget(self.table)

    def add_record(self):
        """添加新记录"""
        type_text = self.type_combo.currentText()
        amount_text = self.amount_edit.text()
        category = self.category_combo.currentText()
        date = self.date_edit.date().toString("yyyy-MM-dd")
        description = self.desc_edit.text()
        
        # 验证输入
        if not amount_text:
            QMessageBox.warning(self, "警告", "请输入金额!")
            return
        
        try:
            amount = float(amount_text)
        except ValueError:
            QMessageBox.warning(self, "警告", "金额必须是数字!")
            return
        
        # 根据类型处理
        if type_text == "借款":
            # 添加借款记录
            self.cursor.execute('''
                INSERT INTO transactions (type, amount, category, description, date, status)
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
                INSERT INTO transactions (type, amount, category, description, date, related_id)
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
                INSERT INTO transactions (type, amount, category, description, date)
                VALUES (?, ?, ?, ?, ?)
            ''', (db_type, amount, category, description, date))
            self.conn.commit()
            
            QMessageBox.information(self, "成功", f"{type_text}记录已添加!")
        
        # 清空输入并刷新数据
        self.amount_edit.clear()
        self.desc_edit.clear()
        self.load_data()
        self.update_loan_combo()

    def delete_record(self):
        """删除选中的记录"""
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "警告", "请选择要删除的记录!")
            return
        
        row = selected[0].row()
        record_id = int(self.table.item(row, 0).text())
        
        # 检查是否是借款记录且有未还清的还款
        self.cursor.execute('''
            SELECT type, status FROM transactions WHERE id=?
        ''', (record_id,))
        record_type, status = self.cursor.fetchone()
        
        if record_type == '借款' and status == 'pending':
            QMessageBox.warning(self, "警告", "不能删除未还清的借款记录!")
            return
        
        # 确认删除
        reply = QMessageBox.question(
            self, '确认', '确定要删除这条记录吗?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 如果是还款记录，需要重新计算关联借款的状态
            self.cursor.execute('''
                SELECT related_id FROM transactions WHERE id=?
            ''', (record_id,))
            related_id = self.cursor.fetchone()
            
            # 删除记录
            self.cursor.execute('''
                DELETE FROM transactions WHERE id=?
            ''', (record_id,))
            
            # 如果是还款记录，更新关联借款状态
            if related_id and related_id[0]:
                self.update_loan_status(related_id[0])
            
            self.conn.commit()
            self.load_data()
            self.update_loan_combo()

    def update_loan_status(self, loan_id):
        """更新借款状态"""
        self.cursor.execute('''
            SELECT SUM(amount) FROM transactions 
            WHERE type='还款' AND related_id=?
        ''', (loan_id,))
        total_repaid = self.cursor.fetchone()[0] or 0
        
        self.cursor.execute('''
            SELECT amount FROM transactions WHERE id=?
        ''', (loan_id,))
        loan_amount = self.cursor.fetchone()[0]
        
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
        
        # 标记为已结算
        self.cursor.execute('''
            UPDATE transactions SET status='settled' WHERE id=?
        ''', (record_id,))
        self.conn.commit()
        
        QMessageBox.information(self, "成功", "借款记录已标记为已结算!")
        self.load_data()
        self.update_loan_combo()

    def load_data(self):
        """加载数据到表格"""
        self.cursor.execute('''
            SELECT id, type, amount, category, description, date, 
                   CASE WHEN status IS NULL THEN '' ELSE status END
            FROM transactions
            ORDER BY date DESC
        ''')
        records = self.cursor.fetchall()
        
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
                
                self.table.setItem(row, col, item)
        
        self.table.resizeColumnsToContents()

    def closeEvent(self, event):
        """关闭窗口时关闭数据库连接"""
        self.conn.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FinanceApp()
    window.show()
    sys.exit(app.exec_())