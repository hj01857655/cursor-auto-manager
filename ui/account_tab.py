from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                        QListWidget, QListWidgetItem, QLabel, QGroupBox, 
                        QFormLayout, QSpinBox, QMessageBox, QTableWidget,
                        QTableWidgetItem, QHeaderView, QAbstractItemView,
                        QMenu, QAction, QApplication, QDialog, QTextEdit,
                        QLineEdit)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QColor
from core.account_manager_db import AccountManagerDb
import datetime

class AccountTab(QWidget):
    """账号管理界面"""
    
    def __init__(self, account_manager: AccountManagerDb):
        super().__init__()
        self.account_manager = account_manager
        
        # 创建主布局
        self.layout = QVBoxLayout(self)
        
        # 创建账号列表区域
        self.account_list_group = QGroupBox("账号列表")
        self.account_list_layout = QVBoxLayout()
        
        # 创建账号表格
        self.account_table = QTableWidget()
        self.account_table.setColumnCount(9)  # 设置列数
        self.account_table.setHorizontalHeaderLabels([
            "账号类型", "邮箱", "密码", "状态", "试用类型", "剩余额度",
            "剩余天数", "令牌", "过期时间"
        ])
        
        # 设置表格属性
        self.account_table.setSelectionBehavior(QAbstractItemView.SelectRows)  # 选择整行
        self.account_table.setSelectionMode(QAbstractItemView.SingleSelection)  # 单选
        self.account_table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # 不可编辑
        self.account_table.setAlternatingRowColors(True)  # 交替行颜色
        self.account_table.setContextMenuPolicy(Qt.CustomContextMenu)  # 启用自定义上下文菜单
        self.account_table.customContextMenuRequested.connect(self.show_context_menu)  # 连接菜单信号
        self.account_table.cellDoubleClicked.connect(self.on_cell_double_clicked)  # 连接双击信号
        
        # 设置表格列宽
        header = self.account_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 账号类型列
        header.setSectionResizeMode(1, QHeaderView.Interactive)  # 邮箱列可调整
        header.setStretchLastSection(True)  # 最后一列自动拉伸填充
        
        # 设置初始列宽
        self.account_table.setColumnWidth(0, 80)   # 账号类型
        self.account_table.setColumnWidth(1, 150)  # 邮箱
        self.account_table.setColumnWidth(2, 80)   # 密码
        self.account_table.setColumnWidth(3, 100)  # 状态
        self.account_table.setColumnWidth(4, 80)   # 试用类型
        self.account_table.setColumnWidth(5, 80)   # 剩余额度
        self.account_table.setColumnWidth(6, 80)   # 剩余天数
        self.account_table.setColumnWidth(7, 150)  # 令牌
        # 过期时间列会自动拉伸
        
        self.account_list_layout.addWidget(self.account_table)
        
        # 创建账号操作按钮
        self.account_buttons_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.refresh_accounts)
        self.account_buttons_layout.addWidget(self.refresh_btn)
        
        self.add_btn = QPushButton("添加账号")
        self.add_btn.clicked.connect(self.add_account)
        self.account_buttons_layout.addWidget(self.add_btn)
        
        self.edit_btn = QPushButton("编辑账号")
        self.edit_btn.clicked.connect(self.edit_account)
        self.account_buttons_layout.addWidget(self.edit_btn)
        
        self.switch_btn = QPushButton("切换账号")
        self.switch_btn.clicked.connect(self.switch_account)
        self.account_buttons_layout.addWidget(self.switch_btn)
        
        self.remove_btn = QPushButton("删除账号")
        self.remove_btn.clicked.connect(self.remove_account)
        self.account_buttons_layout.addWidget(self.remove_btn)
        
        self.view_token_btn = QPushButton("查看令牌")
        self.view_token_btn.clicked.connect(self.view_token)
        self.account_buttons_layout.addWidget(self.view_token_btn)
        
        self.account_list_layout.addLayout(self.account_buttons_layout)
        self.account_list_group.setLayout(self.account_list_layout)
        self.layout.addWidget(self.account_list_group)
        
        # 创建阈值设置区域
        self.threshold_group = QGroupBox("阈值设置")
        self.threshold_layout = QFormLayout()
        
        self.max_requests_spin = QSpinBox()
        self.max_requests_spin.setRange(1, 1000)
        self.max_requests_spin.setValue(60)
        self.max_requests_spin.valueChanged.connect(self.update_thresholds)
        self.threshold_layout.addRow("每分钟最大请求数:", self.max_requests_spin)
        
        self.max_sessions_spin = QSpinBox()
        self.max_sessions_spin.setRange(1, 10)
        self.max_sessions_spin.setValue(3)
        self.max_sessions_spin.valueChanged.connect(self.update_thresholds)
        self.threshold_layout.addRow("最大并发会话数:", self.max_sessions_spin)
        
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(1, 120)
        self.timeout_spin.setValue(30)
        self.timeout_spin.valueChanged.connect(self.update_thresholds)
        self.threshold_layout.addRow("会话超时时间(分钟):", self.timeout_spin)
        
        self.threshold_group.setLayout(self.threshold_layout)
        self.layout.addWidget(self.threshold_group)
        
        # 连接信号
        self.account_manager.account_list_updated.connect(self.update_account_list)
        self.account_manager.threshold_updated.connect(self.update_threshold_values)
        
        # 初始化界面
        self.refresh_accounts()
        
    @pyqtSlot(list)
    def update_account_list(self, accounts):
        """更新账号列表显示"""
        # 清空表格
        self.account_table.setRowCount(0)
        
        # 添加账号数据
        for account in accounts:
            row_position = self.account_table.rowCount()
            self.account_table.insertRow(row_position)
            
            # 创建邮箱单元格
            email_item = QTableWidgetItem(account.get('email', '未知邮箱'))
            email_item.setData(Qt.UserRole, account.get('id'))  # 存储账号ID用于后续操作
            self.account_table.setItem(row_position, 1, email_item)
            
            # 创建账号类型单元格
            auth_source = account.get('auth_source', '未知')
            auth_source_item = QTableWidgetItem(auth_source)
            self.account_table.setItem(row_position, 0, auth_source_item)
            
            # 创建密码单元格
            password = account.get('password', '未知')
            password_item = QTableWidgetItem(password)
            self.account_table.setItem(row_position, 2, password_item)
            
            # 创建状态单元格
            status = account.get('status', '未知')
            status_item = QTableWidgetItem(status)
            
            # 根据状态设置颜色
            if "正常" in status or "永久" in status:
                status_item.setForeground(QColor('#28a745'))  # 绿色
            elif "试用期" in status:
                status_item.setForeground(QColor('#17a2b8'))  # 蓝色
            elif "过期" in status:
                status_item.setForeground(QColor('#dc3545'))  # 红色
            elif "即将过期" in status:
                status_item.setForeground(QColor('#fd7e14'))  # 橙色
            else:
                status_item.setForeground(QColor('#ffc107'))  # 黄色
                
            self.account_table.setItem(row_position, 3, status_item)
            
            # 创建会员类型单元格
            membership = account.get('membership', '未知')
            membership_item = QTableWidgetItem(membership)
            if membership == 'pro':
                membership_item.setText("Pro会员")
                membership_item.setForeground(QColor('#28a745'))  # 绿色
            elif membership == 'free_trial':
                membership_item.setText("试用版")
                membership_item.setForeground(QColor('#17a2b8'))  # 蓝色
                
            self.account_table.setItem(row_position, 4, membership_item)
            
            # 创建剩余额度单元格 (如果有的话)
            quota = account.get('quota', '无限制')
            quota_item = QTableWidgetItem(str(quota))
            self.account_table.setItem(row_position, 5, quota_item)
            
            # 计算剩余天数
            days_left = "未知"
            try:
                if expire_time != "未知" and expire_time != "永久":
                    # 尝试解析过期时间
                    for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d"]:
                        try:
                            expire_date = datetime.datetime.strptime(expire_time, fmt)
                            days_left = (expire_date - datetime.datetime.now()).days
                            days_left = f"{days_left}天" if days_left >= 0 else "已过期"
                            break
                        except ValueError:
                            continue
                elif expire_time == "永久":
                    days_left = "永久"
            except Exception:
                days_left = "未知"
                
            days_left_item = QTableWidgetItem(str(days_left))
            self.account_table.setItem(row_position, 6, days_left_item)
            
            # 创建令牌单元格
            refresh_token = account.get('refresh_token', '')
            access_token = account.get('access_token', '')
            # 优先使用刷新令牌，如果没有则使用访问令牌
            token = refresh_token or access_token
            token_display = f"{token[:10]}...{token[-10:]}" if token else "无"
            token_item = QTableWidgetItem(token_display)
            token_item.setToolTip(token)  # 设置完整令牌为工具提示
            self.account_table.setItem(row_position, 7, token_item)
            
            # 创建过期时间单元格
            expire_time = account.get('expire_time', '未知')
            expire_time_item = QTableWidgetItem(expire_time)
            self.account_table.setItem(row_position, 8, expire_time_item)
            
        # 标记当前账号
        current_account = self.account_manager.get_current_account()
        if current_account:
            current_id = current_account.get('id')
            for row in range(self.account_table.rowCount()):
                item = self.account_table.item(row, 1)
                if item and item.data(Qt.UserRole) == current_id:
                    for col in range(self.account_table.columnCount()):
                        self.account_table.item(row, col).setBackground(QColor('#e7f1ff'))
                    break
            
    @pyqtSlot(dict)
    def update_threshold_values(self, thresholds):
        """更新阈值设置显示"""
        self.max_requests_spin.setValue(thresholds.get("max_requests_per_minute", 60))
        self.max_sessions_spin.setValue(thresholds.get("max_concurrent_sessions", 3))
        self.timeout_spin.setValue(thresholds.get("session_timeout_minutes", 30))
        
    def refresh_accounts(self):
        """刷新账号列表"""
        self.account_manager.refresh_account_status()
        
    def switch_account(self):
        """切换当前账号"""
        selected_rows = self.account_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            item = self.account_table.item(row, 1)  # 获取第一列的单元格(邮箱)
            account_id = item.data(Qt.UserRole)
            if self.account_manager.switch_account(account_id):
                QMessageBox.information(self, "成功", "账号切换成功")
                self.update_account_list(self.account_manager.accounts)  # 刷新表格
            else:
                QMessageBox.warning(self, "错误", "账号切换失败")
        else:
            QMessageBox.warning(self, "警告", "请先选择一个账号")
            
    def remove_account(self):
        """删除账号"""
        selected_rows = self.account_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            item = self.account_table.item(row, 1)  # 获取第一列的单元格(邮箱)
            account_id = item.data(Qt.UserRole)
            email = item.text()
            
            reply = QMessageBox.question(self, "确认", f"确定要删除账号 {email} 吗？",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.account_manager.remove_account(account_id)
        else:
            QMessageBox.warning(self, "警告", "请先选择一个账号")
            
    def update_thresholds(self):
        """更新阈值设置"""
        new_thresholds = {
            "max_requests_per_minute": self.max_requests_spin.value(),
            "max_concurrent_sessions": self.max_sessions_spin.value(),
            "session_timeout_minutes": self.timeout_spin.value()
        }
        self.account_manager.update_thresholds(new_thresholds)
        
    def show_context_menu(self, position):
        """显示上下文菜单"""
        # 获取当前选中的单元格
        selected_indexes = self.account_table.selectedIndexes()
        if not selected_indexes:
            return
            
        # 获取当前行和当前列
        current_row = selected_indexes[0].row()
        current_column = selected_indexes[0].column()
        
        # 获取单元格
        item = self.account_table.item(current_row, current_column)
        if not item:
            return
            
        # 创建菜单
        context_menu = QMenu(self)
        
        # 添加复制动作
        copy_action = QAction("复制内容", self)
        copy_action.triggered.connect(lambda: self.copy_cell_content(item.text()))
        context_menu.addAction(copy_action)
        
        # 对于Cookie列和令牌列添加特殊操作
        if current_column in [7]:  # Cookie列或令牌列
            # 获取完整内容
            account_id = self.account_table.item(current_row, 1).data(Qt.UserRole)
            account = self.get_account_by_id(account_id)
            
            content = None
            if current_column == 7:
                content = account.get('refresh_token', '') or account.get('access_token', '')
                
            if content:
                # 添加复制完整内容动作
                copy_full_action = QAction("复制完整内容", self)
                copy_full_action.triggered.connect(lambda: self.copy_cell_content(content))
                context_menu.addAction(copy_full_action)
                
                # 添加查看完整内容动作
                view_full_action = QAction("查看完整内容", self)
                view_full_action.triggered.connect(lambda: self.view_full_content(content, "令牌"))
                context_menu.addAction(view_full_action)
        
        # 显示菜单
        context_menu.exec_(self.account_table.viewport().mapToGlobal(position))
        
    def copy_cell_content(self, content):
        """复制内容到剪贴板"""
        clipboard = QApplication.clipboard()
        clipboard.setText(content)
        QMessageBox.information(self, "成功", "内容已复制到剪贴板")
        
    def view_full_content(self, content, content_type="内容"):
        """查看完整内容"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"完整{content_type}")
        dialog.setMinimumSize(600, 200)
        
        layout = QVBoxLayout(dialog)
        
        # 添加文本框
        text_edit = QTextEdit()
        text_edit.setPlainText(content)
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)
        
        # 添加按钮
        button_layout = QHBoxLayout()
        
        copy_btn = QPushButton("复制")
        copy_btn.clicked.connect(lambda: self.copy_cell_content(content))
        button_layout.addWidget(copy_btn)
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        # 显示对话框
        dialog.exec_()
        
    def on_cell_double_clicked(self, row, column):
        """单元格双击事件"""
        # 如果是令牌列，显示完整内容
        if column in [7]:
            account_id = self.account_table.item(row, 1).data(Qt.UserRole)
            account = self.get_account_by_id(account_id)
            
            content = None
            content_type = "令牌"
            if column == 7:
                # 令牌列优先使用刷新令牌，如果没有则使用访问令牌
                content = account.get('refresh_token', '') or account.get('access_token', '')
                
            if content:
                self.view_full_content(content, content_type)
                
    def get_account_by_id(self, account_id):
        """根据ID获取账号"""
        for account in self.account_manager.accounts:
            if account.get('id') == account_id:
                return account
        return None
        
    def view_token(self):
        """查看选中账号的令牌"""
        selected_rows = self.account_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先选择一个账号")
            return
            
        row = selected_rows[0].row()
        account_id = self.account_table.item(row, 1).data(Qt.UserRole)
        account = self.get_account_by_id(account_id)
        
        if not account:
            QMessageBox.warning(self, "错误", "获取账号信息失败")
            return
            
        refresh_token = account.get('refresh_token', '')
        access_token = account.get('access_token', '')
        
        if not refresh_token and not access_token:
            QMessageBox.information(self, "提示", "该账号没有令牌信息")
            return
            
        # 创建对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("账号令牌信息")
        dialog.setMinimumSize(800, 400)
        
        layout = QVBoxLayout(dialog)
        
        # 添加刷新令牌（如果有）
        if refresh_token:
            refresh_group = QGroupBox("刷新令牌")
            refresh_layout = QVBoxLayout()
            
            refresh_text = QTextEdit()
            refresh_text.setPlainText(refresh_token)
            refresh_text.setReadOnly(True)
            refresh_layout.addWidget(refresh_text)
            
            refresh_btn = QPushButton("复制刷新令牌")
            refresh_btn.clicked.connect(lambda: self.copy_cell_content(refresh_token))
            refresh_layout.addWidget(refresh_btn)
            
            refresh_group.setLayout(refresh_layout)
            layout.addWidget(refresh_group)
            
        # 添加访问令牌（如果有）
        if access_token:
            access_group = QGroupBox("访问令牌")
            access_layout = QVBoxLayout()
            
            access_text = QTextEdit()
            access_text.setPlainText(access_token)
            access_text.setReadOnly(True)
            access_layout.addWidget(access_text)
            
            access_btn = QPushButton("复制访问令牌")
            access_btn.clicked.connect(lambda: self.copy_cell_content(access_token))
            access_layout.addWidget(access_btn)
            
            access_group.setLayout(access_layout)
            layout.addWidget(access_group)
            
        # 添加关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        # 显示对话框
        dialog.exec_()

    def add_account(self):
        """添加新账号"""
        dialog = EditAccountDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            account_data = dialog.get_account_data()
            self.account_manager.add_account(account_data)
            self.update_account_list(self.account_manager.accounts)
            
    def edit_account(self):
        """编辑现有账号"""
        # 获取选中的账号
        selected_rows = self.account_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先选择一个账号")
            return
            
        row = selected_rows[0].row()
        account_id = self.account_table.item(row, 1).data(Qt.UserRole)
        account = self.get_account_by_id(account_id)
        
        if not account:
            QMessageBox.warning(self, "错误", "获取账号信息失败")
            return
            
        dialog = EditAccountDialog(self, account)
        if dialog.exec_() == QDialog.Accepted:
            account_data = dialog.get_account_data()
            self.account_manager.add_account(account_data)  # add_account 方法也用于更新现有账号
            self.update_account_list(self.account_manager.accounts)

class EditAccountDialog(QDialog):
    """账号编辑对话框"""
    
    def __init__(self, parent=None, account=None):
        """初始化对话框
        
        Args:
            parent: 父窗口
            account: 账号信息，如果为None则是添加新账号
        """
        super().__init__(parent)
        self.account = account or {}
        self.is_new = account is None
        
        # 设置窗口标题和大小
        self.setWindowTitle("添加账号" if self.is_new else "编辑账号")
        self.setMinimumSize(500, 450)
        
        # 创建布局
        layout = QVBoxLayout(self)
        
        # 创建表单
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setContentsMargins(10, 10, 10, 10)
        
        # 邮箱
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("请输入邮箱")
        self.email_input.setText(self.account.get("email", ""))
        form_layout.addRow("邮箱:", self.email_input)
        
        # 密码
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("请输入密码")
        self.password_input.setText(self.account.get("password", ""))
        self.password_input.setEchoMode(QLineEdit.Password)  # 密码模式
        form_layout.addRow("密码:", self.password_input)
        
        # 账号类型
        self.auth_source_input = QLineEdit()
        self.auth_source_input.setPlaceholderText("例如：google, github, microsoft等")
        self.auth_source_input.setText(self.account.get("auth_source", ""))
        form_layout.addRow("账号类型:", self.auth_source_input)
        
        # 会员类型
        self.membership_input = QLineEdit()
        self.membership_input.setPlaceholderText("例如：pro, free_trial等")
        self.membership_input.setText(self.account.get("membership", ""))
        form_layout.addRow("会员类型:", self.membership_input)
        
        # 状态
        self.status_input = QLineEdit()
        self.status_input.setPlaceholderText("例如：正常, 已过期等")
        self.status_input.setText(self.account.get("status", "正常"))
        form_layout.addRow("状态:", self.status_input)
        
        # 过期时间
        self.expire_time_input = QLineEdit()
        self.expire_time_input.setPlaceholderText("YYYY-MM-DD，或输入'永久'")
        self.expire_time_input.setText(self.account.get("expire_time", ""))
        form_layout.addRow("过期时间:", self.expire_time_input)
        
        # 刷新令牌
        self.refresh_token_input = QTextEdit()
        self.refresh_token_input.setPlaceholderText("刷新令牌（可选）")
        self.refresh_token_input.setText(self.account.get("refresh_token", ""))
        form_layout.addRow("刷新令牌:", self.refresh_token_input)
        
        # 访问令牌
        self.access_token_input = QTextEdit()
        self.access_token_input.setPlaceholderText("访问令牌（可选）")
        self.access_token_input.setText(self.account.get("access_token", ""))
        form_layout.addRow("访问令牌:", self.access_token_input)
        
        # 添加表单到主布局
        layout.addLayout(form_layout)
        
        # 添加按钮
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.save_btn)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
    def get_account_data(self):
        """获取表单中的账号数据"""
        return {
            "email": self.email_input.text(),
            "password": self.password_input.text(),
            "auth_source": self.auth_source_input.text(),
            "membership": self.membership_input.text(),
            "status": self.status_input.text(),
            "expire_time": self.expire_time_input.text(),
            "refresh_token": self.refresh_token_input.toPlainText(),
            "access_token": self.access_token_input.toPlainText(),
            "id": self.account.get("id") if not self.is_new else None,
            "last_login": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        } 