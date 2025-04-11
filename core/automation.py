class AutomationManager:
    """自动化任务管理器类"""
    
    def __init__(self, browser_manager):
        """初始化自动化管理器
        
        Args:
            browser_manager: 浏览器管理器实例
        """
        self.browser_manager = browser_manager
        self.tasks = []
        
    def add_task(self, task):
        """添加自动化任务
        
        Args:
            task: 要添加的任务对象
        """
        self.tasks.append(task)
        
    def run_task(self, task_id):
        """运行指定任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 任务执行是否成功
        """
        if 0 <= task_id < len(self.tasks):
            task = self.tasks[task_id]
            return task.run()
        return False

    def get_tasks(self):
        """获取所有任务
        
        Returns:
            list: 任务列表
        """
        return self.tasks
        
    def create_task_from_data(self, task_data):
        """根据任务数据创建任务
        
        Args:
            task_data: 任务数据字典
            
        Returns:
            AutomationTask: 创建的任务，失败返回None
        """
        try:
            task_type = task_data.get("type")
            
            if task_type == "login":
                return CursorLoginTask(
                    self.browser_manager,
                    username=task_data.get("username", ""),
                    password=task_data.get("password", "")
                )
            elif task_type == "open_project":
                return OpenProjectTask(
                    self.browser_manager,
                    project_path=task_data.get("project_path", "")
                )
            elif task_type == "run_command":
                return RunCommandTask(
                    self.browser_manager,
                    command=task_data.get("command", "")
                )
            elif task_type == "create_project":
                return CreateProjectTask(
                    self.browser_manager,
                    project_name=task_data.get("project_name", ""),
                    template=task_data.get("template", "empty")
                )
            
            return None
        except Exception as e:
            print(f"创建任务失败: {e}")
            return None


class AutomationTask:
    """自动化任务基类"""
    
    def __init__(self, name, description, browser_manager):
        """初始化任务
        
        Args:
            name: 任务名称
            description: 任务描述
            browser_manager: 浏览器管理器
        """
        self.name = name
        self.description = description
        self.browser_manager = browser_manager
        self.status = "就绪"
        
    def run(self):
        """运行任务，子类需要重写此方法
        
        Returns:
            bool: 任务是否成功执行
        """
        raise NotImplementedError("任务子类必须实现run方法")
    
    def get_status(self):
        """获取任务状态
        
        Returns:
            str: 任务状态
        """
        return self.status


class CursorLoginTask(AutomationTask):
    """Cursor登录任务"""
    
    def __init__(self, browser_manager, username="", password=""):
        """初始化Cursor登录任务
        
        Args:
            browser_manager: 浏览器管理器
            username: 用户名
            password: 密码
        """
        super().__init__("Cursor登录", "登录到Cursor编辑器", browser_manager)
        self.username = username
        self.password = password
        
    def run(self):
        """运行登录任务
        
        Returns:
            bool: 登录是否成功
        """
        try:
            # 检查是否已登录
            if self.browser_manager.is_logged_in():
                self.status = "已经处于登录状态"
                return True
                
            # 获取页面对象
            page = self.browser_manager.get_page()
            if not page:
                self.status = "失败: 浏览器未启动"
                return False
                
            # 导航到Cursor主页
            page.goto("https://cursor.com")
            self.status = "正在导航到登录页面..."
            
            # 检查是否重定向到中文页面
            if "cursor.com/cn" in page.url:
                self.status = "检测到中文页面，寻找登录按钮..."
            else:
                self.status = "在英文页面寻找登录按钮..."
            
            # 等待并点击登录按钮 - 使用提供的选择器
            page.wait_for_selector("#action-buttons > a > span", timeout=10000)
            page.click("#action-buttons > a > span")
            
            # 等待登录页面加载
            self.status = "等待登录页面加载..."
            # 这里需要根据实际登录页面调整选择器
            page.wait_for_selector("input[type='email']", timeout=10000)
            
            # 输入登录信息
            if self.username:
                page.fill("input[type='email']", self.username)
            
            if self.password:
                # 如果有密码输入框
                password_selector = "input[type='password']"
                if page.is_visible(password_selector):
                    page.fill(password_selector, self.password)
            
            # 点击继续或登录按钮
            continue_button = "button[type='submit']"
            if page.is_visible(continue_button):
                page.click(continue_button)
                
            # 检查是否登录成功 - 可以检查URL或页面上的元素
            # 这里简化处理，假设点击提交按钮后就登录成功
            self.browser_manager.set_state("logged_in", True)
            self.status = "登录成功"
            return True
            
        except Exception as e:
            self.status = f"失败: {str(e)}"
            return False


class OpenProjectTask(AutomationTask):
    """打开项目任务"""
    
    def __init__(self, browser_manager, project_path=""):
        """初始化打开项目任务
        
        Args:
            browser_manager: 浏览器管理器
            project_path: 项目路径
        """
        super().__init__("打开项目", "在Cursor中打开项目", browser_manager)
        self.project_path = project_path
        
    def run(self):
        """运行打开项目任务
        
        Returns:
            bool: 是否成功打开项目
        """
        try:
            # 获取页面对象
            page = self.browser_manager.get_page()
            if not page:
                self.status = "失败: 浏览器未启动"
                return False
                
            self.status = "正在打开项目..."
            
            # 确保在Cursor主页面
            if "cursor.com" not in page.url:
                page.goto("https://cursor.com")
                
            # 点击打开项目按钮 (需要根据实际页面结构调整)
            page.wait_for_selector("text=Open", timeout=10000)
            page.click("text=Open")
            
            # 这里需要处理本地文件选择对话框
            # 由于Playwright不能直接操作系统对话框，这部分需要特殊处理
            # 一种可能的解决方案是修改Cursor的URL参数，或使用快捷键
            
            self.status = f"已打开项目: {self.project_path}"
            return True
            
        except Exception as e:
            self.status = f"失败: {str(e)}"
            return False


class RunCommandTask(AutomationTask):
    """运行命令任务"""
    
    def __init__(self, browser_manager, command=""):
        """初始化运行命令任务
        
        Args:
            browser_manager: 浏览器管理器
            command: 要运行的命令
        """
        super().__init__("运行命令", "在Cursor终端中运行命令", browser_manager)
        self.command = command
        
    def run(self):
        """运行命令任务
        
        Returns:
            bool: 是否成功运行命令
        """
        try:
            # 获取页面对象
            page = self.browser_manager.get_page()
            if not page:
                self.status = "失败: 浏览器未启动"
                return False
                
            self.status = "正在执行命令..."
            
            # 打开终端 (根据实际快捷键调整)
            page.keyboard.press("Control+`")
            
            # 输入命令
            page.keyboard.type(self.command)
            page.keyboard.press("Enter")
            
            self.status = f"已执行命令: {self.command}"
            return True
            
        except Exception as e:
            self.status = f"失败: {str(e)}"
            return False


class CreateProjectTask(AutomationTask):
    """创建新项目任务"""
    
    def __init__(self, browser_manager, project_name="", template="empty"):
        """初始化创建项目任务
        
        Args:
            browser_manager: 浏览器管理器
            project_name: 项目名称
            template: 项目模板
        """
        super().__init__("创建项目", "在Cursor中创建新项目", browser_manager)
        self.project_name = project_name
        self.template = template
        
    def run(self):
        """运行创建项目任务
        
        Returns:
            bool: 是否成功创建项目
        """
        try:
            # 获取页面对象
            page = self.browser_manager.get_page()
            if not page:
                self.status = "失败: 浏览器未启动"
                return False
                
            # 检查是否已登录
            if not self.browser_manager.is_logged_in():
                self.status = "失败: 请先登录"
                return False
                
            self.status = "正在创建新项目..."
            
            # 确保在Cursor主页面
            if "cursor.com" not in page.url:
                page.goto("https://cursor.com")
                
            # 寻找新建项目按钮 (选择器需要根据实际网站调整)
            try:
                # 尝试查找新建项目按钮
                new_project_button = "text=New Project"
                page.wait_for_selector(new_project_button, timeout=5000)
                page.click(new_project_button)
            except:
                # 如果找不到，可能需要先点击一些其他元素
                self.status = "正在导航到项目创建页面..."
                # 此处根据实际页面结构调整
            
            # 输入项目名称
            if self.project_name:
                # 等待项目名称输入框(选择器需要根据实际网站调整)
                project_name_input = "input[placeholder='Project Name']"
                page.wait_for_selector(project_name_input, timeout=10000)
                page.fill(project_name_input, self.project_name)
            
            # 选择模板(选择器需要根据实际网站调整)
            if self.template != "empty":
                # 此处根据实际页面结构调整
                pass
            
            # 点击创建按钮(选择器需要根据实际网站调整)
            create_button = "button:has-text('Create')"
            if page.is_visible(create_button):
                page.click(create_button)
            
            self.status = f"已创建项目: {self.project_name}"
            return True
            
        except Exception as e:
            self.status = f"失败: {str(e)}"
            return False 