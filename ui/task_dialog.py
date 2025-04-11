from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                        QDialogButtonBox, QFormLayout, QGroupBox, QComboBox)
from PyQt5.QtCore import Qt

class TaskDialog(QDialog):
    """自定义任务对话框"""
    
    def __init__(self, parent=None):
        """初始化对话框
        
        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        self.setWindowTitle("添加自动化任务")
        self.resize(400, 300)
        self.setup_ui()
        
    def setup_ui(self):
        """设置界面元素"""
        layout = QVBoxLayout(self)
        
        # 任务类型选择
        self.task_type_group = QGroupBox("任务类型")
        task_type_layout = QFormLayout()
        
        self.task_type_combo = QComboBox()
        self.task_type_combo.addItem("Cursor登录", "login")
        self.task_type_combo.addItem("打开项目", "open_project")
        self.task_type_combo.addItem("运行命令", "run_command")
        self.task_type_combo.addItem("创建新项目", "create_project")
        self.task_type_combo.currentIndexChanged.connect(self.on_task_type_changed)
        
        task_type_layout.addRow("选择任务类型:", self.task_type_combo)
        self.task_type_group.setLayout(task_type_layout)
        layout.addWidget(self.task_type_group)
        
        # 任务参数
        self.params_group = QGroupBox("任务参数")
        self.params_layout = QFormLayout()
        self.params_group.setLayout(self.params_layout)
        layout.addWidget(self.params_group)
        
        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        # 初始化参数界面
        self.on_task_type_changed(0)
        
    def on_task_type_changed(self, index):
        """任务类型变更处理
        
        Args:
            index: 选择的索引
        """
        # 清除旧参数
        while self.params_layout.rowCount() > 0:
            self.params_layout.removeRow(0)
            
        task_type = self.task_type_combo.currentData()
            
        if task_type == "login":
            self.setup_login_params()
        elif task_type == "open_project":
            self.setup_open_project_params()
        elif task_type == "run_command":
            self.setup_run_command_params()
        elif task_type == "create_project":
            self.setup_create_project_params()
            
    def setup_login_params(self):
        """设置登录任务参数"""
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        
        self.params_layout.addRow("用户名:", self.username_input)
        self.params_layout.addRow("密码:", self.password_input)
        
    def setup_open_project_params(self):
        """设置打开项目任务参数"""
        self.project_path_input = QLineEdit()
        self.params_layout.addRow("项目路径:", self.project_path_input)
        
    def setup_run_command_params(self):
        """设置运行命令任务参数"""
        self.command_input = QLineEdit()
        self.params_layout.addRow("命令:", self.command_input)
        
    def setup_create_project_params(self):
        """设置创建项目任务参数"""
        self.project_name_input = QLineEdit()
        self.template_combo = QComboBox()
        self.template_combo.addItem("空项目", "empty")
        self.template_combo.addItem("Python项目", "python")
        self.template_combo.addItem("Web项目", "web")
        self.template_combo.addItem("React项目", "react")
        
        self.params_layout.addRow("项目名称:", self.project_name_input)
        self.params_layout.addRow("项目模板:", self.template_combo)
        
    def get_task_data(self):
        """获取任务数据
        
        Returns:
            dict: 任务数据字典
        """
        task_type = self.task_type_combo.currentData()
        task_data = {
            "type": task_type
        }
        
        if task_type == "login":
            task_data.update({
                "username": self.username_input.text(),
                "password": self.password_input.text()
            })
        elif task_type == "open_project":
            task_data.update({
                "project_path": self.project_path_input.text()
            })
        elif task_type == "run_command":
            task_data.update({
                "command": self.command_input.text()
            })
        elif task_type == "create_project":
            task_data.update({
                "project_name": self.project_name_input.text(),
                "template": self.template_combo.currentData()
            })
            
        return task_data 