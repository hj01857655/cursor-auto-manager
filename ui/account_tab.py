from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                        QListWidget, QListWidgetItem, QLabel, QGroupBox, 
                        QFormLayout, QSpinBox, QMessageBox, QTableWidget,
                        QTableWidgetItem, QHeaderView, QAbstractItemView,
                        QMenu, QAction, QApplication, QDialog, QTextEdit)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QColor
from core.account_manager import AccountManager
import datetime

class AccountTab(QWidget):
    """账号管理界面"""
    
    def __init__(self, account_manager: AccountManager):
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
            "邮箱", "账号类型", "状态", "会员类型", "过期时间",
            "剩余天数", "剩余额度", "刷新令牌", "访问令牌"
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
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # 邮箱列可伸缩
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 其他列自适应内容
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)
        
        self.account_list_layout.addWidget(self.account_table)
        
        # 创建账号操作按钮
        self.account_buttons_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.refresh_accounts)
        self.account_buttons_layout.addWidget(self.refresh_btn)
        
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
            self.account_table.setItem(row_position, 0, email_item)
            
            # 创建账号类型单元格
            auth_source = account.get('auth_source', '未知')
            auth_source_item = QTableWidgetItem(auth_source)
            self.account_table.setItem(row_position, 1, auth_source_item)
            
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
                
            self.account_table.setItem(row_position, 2, status_item)
            
            # 创建会员类型单元格
            membership = account.get('membership', '未知')
            membership_item = QTableWidgetItem(membership)
            if membership == 'pro':
                membership_item.setText("Pro会员")
                membership_item.setForeground(QColor('#28a745'))  # 绿色
            elif membership == 'free_trial':
                membership_item.setText("试用版")
                membership_item.setForeground(QColor('#17a2b8'))  # 蓝色
                
            self.account_table.setItem(row_position, 3, membership_item)
            
            # 创建过期时间单元格
            expire_time = account.get('expire_time', '未知')
            expire_time_item = QTableWidgetItem(expire_time)
            self.account_table.setItem(row_position, 4, expire_time_item)
            
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
            self.account_table.setItem(row_position, 5, days_left_item)
            
            # 创建剩余额度单元格 (如果有的话)
            quota = account.get('quota', '无限制')
            quota_item = QTableWidgetItem(str(quota))
            self.account_table.setItem(row_position, 6, quota_item)
            
            # 创建令牌单元格
            refresh_token = account.get('refresh_token', '')
            refresh_token_display = f"{refresh_token[:10]}...{refresh_token[-10:]}" if refresh_token else "无"
            refresh_token_item = QTableWidgetItem(refresh_token_display)
            refresh_token_item.setToolTip(refresh_token)  # 设置完整令牌为工具提示
            self.account_table.setItem(row_position, 7, refresh_token_item)
            
            access_token = account.get('access_token', '')
            access_token_display = f"{access_token[:10]}...{access_token[-10:]}" if access_token else "无"
            access_token_item = QTableWidgetItem(access_token_display)
            access_token_item.setToolTip(access_token)  # 设置完整令牌为工具提示
            self.account_table.setItem(row_position, 8, access_token_item)
            
        # 标记当前账号
        current_account = self.account_manager.get_current_account()
        if current_account:
            current_id = current_account.get('id')
            for row in range(self.account_table.rowCount()):
                item = self.account_table.item(row, 0)
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
            item = self.account_table.item(row, 0)  # 获取第一列的单元格(邮箱)
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
            item = self.account_table.item(row, 0)  # 获取第一列的单元格(邮箱)
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
        
        # 对于令牌列添加特殊操作
        if current_column in [7, 8]:  # 刷新令牌或访问令牌列
            # 获取完整令牌
            account_id = self.account_table.item(current_row, 0).data(Qt.UserRole)
            account = self.get_account_by_id(account_id)
            
            token = None
            if current_column == 7 and account and 'refresh_token' in account:
                token = account['refresh_token']
            elif current_column == 8 and account and 'access_token' in account:
                token = account['access_token']
                
            if token:
                # 添加复制完整令牌动作
                copy_full_action = QAction("复制完整令牌", self)
                copy_full_action.triggered.connect(lambda: self.copy_cell_content(token))
                context_menu.addAction(copy_full_action)
                
                # 添加查看完整令牌动作
                view_full_action = QAction("查看完整令牌", self)
                view_full_action.triggered.connect(lambda: self.view_full_token(token))
                context_menu.addAction(view_full_action)
        
        # 显示菜单
        context_menu.exec_(self.account_table.viewport().mapToGlobal(position))
        
    def copy_cell_content(self, content):
        """复制内容到剪贴板"""
        clipboard = QApplication.clipboard()
        clipboard.setText(content)
        QMessageBox.information(self, "成功", "内容已复制到剪贴板")
        
    def view_full_token(self, token):
        """查看完整令牌"""
        dialog = QDialog(self)
        dialog.setWindowTitle("完整令牌")
        dialog.setMinimumSize(600, 200)
        
        layout = QVBoxLayout(dialog)
        
        # 添加文本框
        text_edit = QTextEdit()
        text_edit.setPlainText(token)
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)
        
        # 添加按钮
        button_layout = QHBoxLayout()
        
        copy_btn = QPushButton("复制")
        copy_btn.clicked.connect(lambda: self.copy_cell_content(token))
        button_layout.addWidget(copy_btn)
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        # 显示对话框
        dialog.exec_()
        
    def on_cell_double_clicked(self, row, column):
        """单元格双击事件"""
        # 如果是令牌列，显示完整令牌
        if column in [7, 8]:
            account_id = self.account_table.item(row, 0).data(Qt.UserRole)
            account = self.get_account_by_id(account_id)
            
            token = None
            if column == 7 and account and 'refresh_token' in account:
                token = account['refresh_token']
            elif column == 8 and account and 'access_token' in account:
                token = account['access_token']
                
            if token:
                self.view_full_token(token)
                
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
        account_id = self.account_table.item(row, 0).data(Qt.UserRole)
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
        
        # 添加刷新令牌
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
            
        # 添加访问令牌
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