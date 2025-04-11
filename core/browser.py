from playwright.sync_api import sync_playwright
import os
import logging

class BrowserManager:
    """浏览器管理器类，负责Playwright浏览器实例的创建和管理"""
    
    def __init__(self, system_config=None):
        """初始化浏览器管理器
        
        Args:
            system_config: 系统配置管理器实例，用于获取浏览器路径等配置
        """
        self.playwright = None
        self.browser = None
        self.page = None
        self.session_state = {}  # 存储会话状态信息
        self.system_config = system_config
        self.logger = logging.getLogger("BrowserManager")
        
    def start_browser(self, browser_type="chromium", headless=None):
        """启动浏览器
        
        Args:
            browser_type: 浏览器类型，可选值：chromium, firefox, webkit
            headless: 是否使用无头模式，如果为None则使用配置文件中的设置
            
        Returns:
            bool: 启动是否成功
        """
        try:
            # 从配置文件获取设置
            use_local_browser = True  # 默认使用本地浏览器
            if self.system_config:
                use_local_browser = self.system_config.get_config(
                    "chrome", "automation.use_local_browser", True)
                
                # 如果headless未指定，从配置文件获取
                if headless is None:
                    headless = self.system_config.get_config(
                        "chrome", "automation.headless", False)
            
            # 启动Playwright
            self.playwright = sync_playwright().start()
            
            # 获取浏览器实例
            browser_instance = getattr(self.playwright, browser_type)
            
            # 准备启动选项
            launch_options = {"headless": headless}
            
            # 检查是否使用自定义Chrome路径
            if browser_type == "chromium" and use_local_browser and self.system_config:
                chrome_path = self.system_config.get_config("chrome", "executable_path", "")
                if chrome_path and os.path.exists(chrome_path):
                    launch_options["executable_path"] = chrome_path
                    self.logger.info(f"使用本地Chrome浏览器: {chrome_path}")
                else:
                    self.logger.warning("本地Chrome浏览器路径无效，将使用默认浏览器")
            
            # 获取其他浏览器选项
            if self.system_config:
                # 获取窗口大小
                width = self.system_config.get_config("chrome", "automation.window_size.width", 1920)
                height = self.system_config.get_config("chrome", "automation.window_size.height", 1080)
                
                # 获取其他选项
                disable_gpu = self.system_config.get_config("chrome", "automation.disable_gpu", True)
                
                # 应用浏览器参数
                args = []
                if width and height:
                    args.append(f"--window-size={width},{height}")
                if disable_gpu:
                    args.append("--disable-gpu")
                    
                # 如果有参数，添加到启动选项
                if args:
                    launch_options["args"] = args
                    
            # 启动浏览器
            self.logger.info(f"正在启动浏览器 (类型: {browser_type}, 无头模式: {headless})")
            self.logger.debug(f"启动选项: {launch_options}")
            self.browser = browser_instance.launch(**launch_options)
            
            # 创建新页面并应用用户代理
            self.page = self.browser.new_page()
            
            # 设置用户代理
            if self.system_config:
                ua_enabled = self.system_config.get_config("chrome", "automation.user_agent.enabled", False)
                if ua_enabled:
                    ua_type = self.system_config.get_config("chrome", "automation.user_agent.type", "default")
                    ua_string = ""
                    
                    if ua_type == "custom":
                        ua_string = self.system_config.get_config("chrome", "automation.user_agent.custom", "")
                    elif ua_type != "default" and ua_type in ["chrome_windows", "chrome_mac", "chrome_android", "chrome_ios"]:
                        ua_string = self.system_config.get_config(
                            f"chrome.automation.user_agent.presets.{ua_type}", 
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                        )
                        
                    if ua_string:
                        self.logger.info(f"设置用户代理: {ua_string}")
                        self.page.set_extra_http_headers({"User-Agent": ua_string})
            
            # 记录成功日志
            self.logger.info(f"浏览器启动成功")
            
            # 重置会话状态
            self.session_state = {"logged_in": False}
            return True
        except Exception as e:
            self.logger.error(f"启动浏览器失败: {e}")
            return False
            
    def close(self):
        """关闭浏览器及所有资源"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        # 清空会话状态
        self.session_state = {}
            
    def navigate(self, url):
        """导航到指定URL
        
        Args:
            url: 目标URL
        """
        if self.page:
            self.page.goto(url)
            
    def get_page(self):
        """获取当前页面对象
        
        Returns:
            Page: Playwright页面对象
        """
        return self.page
        
    def set_state(self, key, value):
        """设置会话状态值
        
        Args:
            key: 状态键
            value: 状态值
        """
        self.session_state[key] = value
        
    def get_state(self, key, default=None):
        """获取会话状态值
        
        Args:
            key: 状态键
            default: 默认值
            
        Returns:
            任意: 状态值
        """
        return self.session_state.get(key, default)
        
    def is_logged_in(self):
        """检查是否已登录
        
        Returns:
            bool: 是否已登录
        """
        return self.get_state("logged_in", False) 