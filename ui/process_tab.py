from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                        QLabel, QGroupBox, QFormLayout, QFileDialog, 
                        QLineEdit, QMessageBox)
from PyQt5.QtCore import Qt, QTimer
from core.process_manager import CursorProcessManager
from PyQt5.QtWidgets import QApplication

class ProcessTab(QWidget):
    """Cursor进程管理选项卡"""
    
    def __init__(self, parent=None):
        """初始化进程管理选项卡
        
        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        self.process_manager = CursorProcessManager()
        self.setup_ui()
        
        # 创建定时器，定期更新进程状态
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_process_status)
        self.status_timer.start(5000)  # 每5秒更新一次
        
        # 初始加载状态
        QTimer.singleShot(500, self.update_process_status)
        
    def setup_ui(self):
        """设置界面元素"""
        layout = QVBoxLayout(self)
        
        # 状态组
        self.status_group = QGroupBox("Cursor状态")
        status_layout = QFormLayout()
        
        self.status_label = QLabel("未知")
        self.exe_path_label = QLabel("未知")
        self.process_count_label = QLabel("0")
        
        status_layout.addRow("运行状态:", self.status_label)
        status_layout.addRow("可执行文件:", self.exe_path_label)
        status_layout.addRow("进程数量:", self.process_count_label)
        
        self.status_group.setLayout(status_layout)
        layout.addWidget(self.status_group)
        
        # 操作按钮组
        self.action_group = QGroupBox("操作")
        action_layout = QVBoxLayout()
        
        # 按钮行
        buttons_layout = QHBoxLayout()
        
        self.start_button = QPushButton("启动Cursor")
        self.start_button.clicked.connect(self.start_cursor)
        buttons_layout.addWidget(self.start_button)
        
        self.kill_button = QPushButton("关闭Cursor")
        self.kill_button.clicked.connect(self.kill_cursor)
        buttons_layout.addWidget(self.kill_button)
        
        self.restart_button = QPushButton("重启Cursor")
        self.restart_button.clicked.connect(self.restart_cursor)
        buttons_layout.addWidget(self.restart_button)
        
        self.refresh_button = QPushButton("刷新状态")
        self.refresh_button.clicked.connect(self.update_process_status)
        buttons_layout.addWidget(self.refresh_button)
        
        action_layout.addLayout(buttons_layout)
        
        # 工作区路径选择
        workspace_layout = QHBoxLayout()
        
        self.workspace_input = QLineEdit()
        self.workspace_input.setPlaceholderText("工作区路径（可选）")
        workspace_layout.addWidget(self.workspace_input)
        
        self.browse_button = QPushButton("浏览...")
        self.browse_button.clicked.connect(self.browse_workspace)
        workspace_layout.addWidget(self.browse_button)
        
        action_layout.addLayout(workspace_layout)
        
        self.action_group.setLayout(action_layout)
        layout.addWidget(self.action_group)
        
    def update_process_status(self):
        """更新进程状态信息"""
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            
            status = self.process_manager.get_cursor_status()
            
            # 更新状态标签
            if status["running"]:
                self.status_label.setText("运行中")
                self.status_label.setStyleSheet("color: #28a745;")  # 绿色
            else:
                self.status_label.setText("未运行")
                self.status_label.setStyleSheet("color: #dc3545;")  # 红色
                
            self.process_count_label.setText(str(status["process_count"]))
            
            if status["executable"]:
                self.exe_path_label.setText(status["executable"])
                self.exe_path_label.setStyleSheet("color: #333333;")  # 正常颜色
            else:
                self.exe_path_label.setText("未找到")
                self.exe_path_label.setStyleSheet("color: #ffc107;")  # 黄色
                
            # 调整按钮状态
            self.start_button.setEnabled(not status["running"])
            self.kill_button.setEnabled(status["running"])
            self.restart_button.setEnabled(status["executable_exists"])
            
            QApplication.restoreOverrideCursor()
            
        except Exception as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.warning(self, "错误", f"更新状态失败: {str(e)}")
            self.status_label.setText("错误")
            self.status_label.setStyleSheet("color: #dc3545;")  # 红色
        
    def start_cursor(self):
        """启动Cursor"""
        workspace_path = self.workspace_input.text().strip()
        workspace_path = workspace_path if workspace_path else None
        
        if self.process_manager.start_cursor(workspace_path):
            QMessageBox.information(self, "成功", "Cursor已启动")
        else:
            QMessageBox.warning(self, "错误", "启动Cursor失败")
            
        self.update_process_status()
        
    def kill_cursor(self):
        """关闭Cursor"""
        if QMessageBox.question(
            self, 
            "确认", 
            "确定要关闭所有Cursor进程吗？未保存的工作可能会丢失。",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            if self.process_manager.kill_cursor():
                QMessageBox.information(self, "成功", "所有Cursor进程已关闭")
            else:
                QMessageBox.warning(self, "错误", "关闭Cursor进程失败")
                
            self.update_process_status()
        
    def restart_cursor(self):
        """重启Cursor"""
        workspace_path = self.workspace_input.text().strip()
        workspace_path = workspace_path if workspace_path else None
        
        if QMessageBox.question(
            self, 
            "确认", 
            "确定要重启Cursor吗？未保存的工作可能会丢失。",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            if self.process_manager.restart_cursor(workspace_path):
                QMessageBox.information(self, "成功", "Cursor已重启")
            else:
                QMessageBox.warning(self, "错误", "重启Cursor失败")
                
            self.update_process_status()
            
    def browse_workspace(self):
        """浏览选择工作区路径"""
        directory = QFileDialog.getExistingDirectory(
            self, 
            "选择工作区目录", 
            ""
        )
        if directory:
            self.workspace_input.setText(directory)
            
    def showEvent(self, event):
        """显示事件处理"""
        super().showEvent(event)
        self.update_process_status()
        
    def hideEvent(self, event):
        """隐藏事件处理"""
        super().hideEvent(event)
        # 隐藏时暂停定时器
        self.status_timer.stop() 