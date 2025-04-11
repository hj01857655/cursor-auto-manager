from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                        QLabel, QLineEdit, QMessageBox, QGroupBox, QFormLayout,
                        QRadioButton, QButtonGroup, QCheckBox, QApplication)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import QFont, QIcon
import webbrowser
import time
import sys
import os
import json
import datetime

class BrowserAutomationThread(QThread):
    """浏览器自动化线程"""
    
    # 定义信号
    status_update = pyqtSignal(str)  # 状态更新信号
    auth_code_received = pyqtSignal(str)  # 授权码接收信号
    automation_finished = pyqtSignal(bool, str)  # 自动化完成信号(成功与否, 消息)
    browser_fingerprint = pyqtSignal(dict)  # 浏览器指纹信号
    
    def __init__(self, auth_url, login_type, email="", password=""):
        super().__init__()
        self.auth_url = auth_url
        self.login_type = login_type
        self.email = email
        self.password = password
        self.running = True
        self.fingerprint_data = {}
        
    def run(self):
        """线程运行函数"""
        try:
            self.status_update.emit("正在初始化浏览器自动化...")
            
            # 检查是否已安装必要的库
            try:
                import playwright
                from playwright.sync_api import sync_playwright
            except ImportError:
                self.status_update.emit("未安装playwright库，尝试安装中...")
                self.install_playwright()
                # 重新导入
                import playwright
                from playwright.sync_api import sync_playwright
                
            self.status_update.emit("初始化Chrome浏览器...")
            
            # 使用playwright打开浏览器
            with sync_playwright() as p:
                # 启动浏览器
                browser = p.chromium.launch(headless=False)
                
                # 创建上下文选项
                context_options = {}
                
                # 如果已经有指纹数据并包含user_agent，使用该user_agent
                if "user_agent" in self.fingerprint_data:
                    context_options["user_agent"] = self.fingerprint_data["user_agent"]
                    self.status_update.emit(f"使用保存的用户代理: {self.fingerprint_data['user_agent'][:30]}...")
                
                # 创建上下文，用于后续收集指纹
                context = browser.new_context(**context_options)
                
                # 如果存在预加载的Cookie，设置它们
                if "final_cookies" in self.fingerprint_data and isinstance(self.fingerprint_data["final_cookies"], list):
                    try:
                        cookies = self.fingerprint_data["final_cookies"]
                        if cookies:
                            self.status_update.emit(f"正在恢复 {len(cookies)} 个Cookie...")
                            context.add_cookies(cookies)
                    except Exception as e:
                        self.status_update.emit(f"恢复Cookie时出错: {str(e)}")
                
                # 收集浏览器指纹基本信息
                browser_version = browser.version
                self.fingerprint_data["browser_version"] = browser_version
                self.fingerprint_data["login_type"] = self.login_type
                self.fingerprint_data["timestamp"] = datetime.datetime.now().isoformat()
                
                page = context.new_page()
                
                try:
                    # 打开授权页面
                    self.status_update.emit(f"正在打开{self.login_type}授权页面...")
                    page.goto(self.auth_url)
                    
                    # 等待页面加载
                    self.status_update.emit("等待页面加载...")
                    
                    # 如果存在localStorage数据，尝试应用
                    if "local_storage" in self.fingerprint_data and isinstance(self.fingerprint_data["local_storage"], dict):
                        try:
                            local_storage = self.fingerprint_data["local_storage"]
                            if local_storage:
                                self.status_update.emit(f"正在恢复localStorage ({len(local_storage)} 个项目)...")
                                for key, value in local_storage.items():
                                    page.evaluate("""(key, value) => {
                                        try {
                                            localStorage.setItem(key, value);
                                            return true;
                                        } catch (e) {
                                            console.error('设置localStorage失败:', e);
                                            return false;
                                        }
                                    }""", key, value)
                        except Exception as e:
                            self.status_update.emit(f"恢复localStorage时出错: {str(e)}")
                    
                    # 收集页面初始Cookie和Storage
                    self.collect_browser_fingerprint(page)
                    
                    # 根据登录类型执行不同的自动化流程
                    if self.login_type == "邮箱":
                        self.status_update.emit("执行邮箱登录流程...")
                        
                        # 等待邮箱输入框出现
                        email_input = page.wait_for_selector("input[type='email']", timeout=30000)
                        
                        # 输入邮箱
                        if self.email:
                            email_input.fill(self.email)
                            self.status_update.emit(f"已输入邮箱: {self.email}")
                            self.fingerprint_data["email"] = self.email
                        else:
                            self.status_update.emit("请在浏览器中手动输入邮箱...")
                        
                        # 等待密码输入框出现（如果存在）
                        try:
                            password_input = page.wait_for_selector("input[type='password']", timeout=10000)
                            
                            # 输入密码
                            if self.password:
                                password_input.fill(self.password)
                                self.status_update.emit("已输入密码")
                            else:
                                self.status_update.emit("请在浏览器中手动输入密码...")
                                
                            # 尝试点击登录按钮
                            login_button = page.query_selector("button[type='submit']")
                            if login_button:
                                login_button.click()
                                self.status_update.emit("已点击登录按钮")
                                
                        except Exception:
                            self.status_update.emit("未找到密码输入框，可能需要先点击下一步...")
                        
                    elif self.login_type == "Google":
                        self.status_update.emit("执行Google授权登录流程...")
                        
                        # 首先检查是否在authenticator主页
                        if "authenticator.cursor.sh" in page.url:
                            try:
                                # 尝试查找并点击Google登录按钮
                                self.status_update.emit("检查authenticator页面中的Google按钮...")
                                google_btn = page.wait_for_selector("button[data-provider='google']", timeout=10000)
                                if google_btn:
                                    google_btn.click()
                                    self.status_update.emit("已点击Google登录按钮")
                            except Exception as e:
                                self.status_update.emit(f"在authenticator页面未找到Google按钮: {str(e)}")
                                
                        # 等待Google登录页面加载，可能是在第二个步骤或直接打开
                        try:
                            self.status_update.emit("等待Google登录页面...")
                            # 等待Google账号选择或登录页面元素
                            
                            # 检查是否出现Google账号选择页面
                            if page.query_selector("div[data-identifier]"):
                                self.status_update.emit("检测到Google账号选择页面")
                                # 收集Google登录相关指纹
                                self.collect_google_fingerprint(page)
                                # 点击第一个账号或者让用户选择
                                self.status_update.emit("请在浏览器中选择Google账号...")
                            else:
                                # 可能是登录表单
                                try:
                                    # 尝试查找邮箱输入框
                                    email_input = page.wait_for_selector("input[type='email']", timeout=10000)
                                    if email_input:
                                        self.status_update.emit("检测到Google登录页面")
                                        if self.email:
                                            email_input.fill(self.email)
                                            self.status_update.emit(f"已输入Google邮箱: {self.email}")
                                            self.fingerprint_data["email"] = self.email
                                            
                                            # 点击下一步按钮
                                            next_btn = page.query_selector("button[jsname='LgbsSe']")
                                            if next_btn:
                                                next_btn.click()
                                                self.status_update.emit("已点击下一步按钮")
                                                
                                                # 等待密码输入框出现
                                                try:
                                                    password_input = page.wait_for_selector("input[type='password']", timeout=10000)
                                                    if password_input and self.password:
                                                        password_input.fill(self.password)
                                                        self.status_update.emit("已输入Google密码")
                                                        
                                                        # 点击登录按钮
                                                        login_btn = page.query_selector("button[jsname='LgbsSe']")
                                                        if login_btn:
                                                            login_btn.click()
                                                            self.status_update.emit("已点击Google登录按钮")
                                                except Exception:
                                                    self.status_update.emit("未找到Google密码输入框或点击按钮失败")
                                        else:
                                            self.status_update.emit("请在浏览器中手动输入Google邮箱...")
                                except Exception:
                                    self.status_update.emit("无法识别Google登录页面元素，请手动登录...")
                        except Exception as e:
                            self.status_update.emit(f"处理Google登录页面时出错: {str(e)}")
                            
                        # 处理可能的授权确认页
                        try:
                            # 等待Google授权确认页面
                            self.status_update.emit("检查是否需要确认授权...")
                            # 这里可能需要根据实际页面结构调整选择器
                            confirm_btn = page.wait_for_selector("button[jsname='LgbsSe']", timeout=10000)
                            if confirm_btn:
                                confirm_btn.click()
                                self.status_update.emit("已点击Google授权确认按钮")
                        except Exception:
                            self.status_update.emit("未检测到Google授权确认页面或已自动确认")
                            
                        self.status_update.emit("Google授权流程执行完成，请等待跳转...")
                        
                    elif self.login_type == "Github":
                        self.status_update.emit("执行Github授权登录流程...")
                        
                        # GitHub登录流程可能有两种情况
                        # 1. 直接在GitHub页面上
                        try:
                            # 尝试查找GitHub登录表单
                            username_input = page.wait_for_selector("input[name='login']", timeout=10000)
                            password_input = page.wait_for_selector("input[name='password']", timeout=5000)
                            
                            if username_input and password_input:
                                self.status_update.emit("检测到GitHub登录页面")
                                
                                # 收集GitHub登录相关指纹
                                self.collect_github_fingerprint(page)
                                
                                # 填写GitHub凭据（如果有）
                                if self.email:
                                    username_input.fill(self.email)
                                    self.status_update.emit("已输入GitHub用户名")
                                    self.fingerprint_data["github_username"] = self.email
                                else:
                                    self.status_update.emit("请在GitHub页面手动输入用户名...")
                                
                                if self.password:
                                    password_input.fill(self.password)
                                    self.status_update.emit("已输入GitHub密码")
                                else:
                                    self.status_update.emit("请在GitHub页面手动输入密码...")
                                
                                # 尝试点击登录按钮
                                login_button = page.query_selector("input[name='commit']")
                                if login_button:
                                    login_button.click()
                                    self.status_update.emit("已点击GitHub登录按钮")
                        except Exception:
                            # 2. 或者在授权页面上点击GitHub按钮
                            try:
                                github_btn = page.wait_for_selector("button[data-provider='github']", timeout=5000)
                                github_btn.click()
                                self.status_update.emit("已点击Github登录按钮，请在浏览器中完成授权...")
                            except Exception:
                                self.status_update.emit("无法自动识别GitHub登录流程，请手动完成登录...")
                        
                        # 有时需要处理GitHub授权确认页面
                        try:
                            # 等待并点击授权按钮（如果出现）
                            authorize_btn = page.wait_for_selector("button[type='submit'][id='js-oauth-authorize-btn']", timeout=10000)
                            if authorize_btn:
                                authorize_btn.click()
                                self.status_update.emit("已点击GitHub授权确认按钮")
                        except Exception:
                            # 如果没有出现授权确认页，可能是已经授权过
                            self.status_update.emit("未检测到GitHub授权确认页面，继续处理...")
                    
                    # 等待授权完成，获取授权码
                    self.status_update.emit("请在浏览器中完成授权过程...")
                    self.status_update.emit("授权完成后，系统会自动获取授权码...")
                    
                    # 监控URL变化，查找授权码
                    try:
                        # 等待页面URL包含授权码参数
                        auth_code_found = False
                        settings_page_detected = False

                        for i in range(60):  # 最多等待60秒
                            if not self.running:
                                break
                                
                            current_url = page.url
                            self.status_update.emit(f"监控URL: {current_url[:60]}...")
                            
                            # 检查是否是设置页面
                            if "cursor.com/cn/settings" in current_url or "cursor.com/settings" in current_url:
                                self.status_update.emit("检测到已跳转到设置页面，尝试获取授权信息...")
                                settings_page_detected = True
                                # 收集设置页面的浏览器指纹
                                self.collect_final_fingerprint(page)
                                
                                # 尝试从设置页面提取授权信息
                                try:
                                    # 从设置页面中提取用户信息（如邮箱、订阅状态等）
                                    user_info = page.evaluate("""() => {
                                        try {
                                            // 尝试从localStorage中获取用户信息
                                            const userInfo = JSON.parse(localStorage.getItem('user') || '{}');
                                            // 尝试从localStorage中获取auth token
                                            const authToken = localStorage.getItem('auth_token') || '';
                                            // 尝试获取页面中用户信息元素
                                            const emailElement = document.querySelector('[data-testid="email"]');
                                            const email = emailElement ? emailElement.textContent.trim() : '';
                                            
                                            return {
                                                email: userInfo.email || email || '',
                                                authToken: authToken,
                                                isAuthenticated: !!authToken,
                                                planName: userInfo.planName || '',
                                                planExpiry: userInfo.planExpiry || ''
                                            };
                                        } catch (e) {
                                            console.error('提取用户信息时出错:', e);
                                            return {};
                                        }
                                    }""")
                                    
                                    if user_info and (user_info.get('email') or user_info.get('authToken')):
                                        self.fingerprint_data.update(user_info)
                                        self.status_update.emit(f"已从设置页面获取用户信息: {user_info.get('email') or '未知邮箱'}")
                                        
                                        # 如果找到有效的authToken，可以直接使用它作为授权信息
                                        if user_info.get('authToken'):
                                            auth_code = user_info.get('authToken')
                                            self.fingerprint_data["auth_code"] = auth_code
                                            self.status_update.emit("成功从设置页面获取授权令牌")
                                            self.auth_code_received.emit(auth_code)
                                            auth_code_found = True
                                            break
                                except Exception as e:
                                    self.status_update.emit(f"尝试从设置页面提取用户信息时出错: {str(e)}")
                            
                            # 检查URL中是否包含授权码参数
                            if "code=" in current_url:
                                # 从URL中提取授权码
                                import re
                                # 改进正则表达式，处理各种URL格式
                                code_match = re.search(r'[?&]code=([^&]+)', current_url)
                                if code_match:
                                    auth_code = code_match.group(1)
                                    self.fingerprint_data["auth_code"] = auth_code
                                    self.status_update.emit("成功从URL中获取授权码")
                                    self.auth_code_received.emit(auth_code)
                                    auth_code_found = True
                                    # 在获取到授权码后，再次收集指纹
                                    self.collect_final_fingerprint(page)
                                    break
                            
                            # 检查页面上是否有授权码元素
                            code_element = page.query_selector(".auth-code, .token, code, [data-test='auth-code']")
                            if code_element:
                                auth_code = code_element.text_content().strip()
                                if auth_code:
                                    self.fingerprint_data["auth_code"] = auth_code
                                    self.status_update.emit("成功从页面元素中获取授权码")
                                    self.auth_code_received.emit(auth_code)
                                    auth_code_found = True
                                    # 收集最终指纹
                                    self.collect_final_fingerprint(page)
                                    break
                                    
                            time.sleep(1)
                            
                        # 如果找到了设置页面但没有授权码，可能授权已经成功但未能提取到授权码
                        if settings_page_detected and not auth_code_found:
                            self.status_update.emit("已检测到设置页面，但未能提取到授权码")
                            # 尝试从localStorage获取其他可用的认证信息
                            try:
                                auth_info = page.evaluate("""() => {
                                    const possibleKeys = ['auth_token', 'accessToken', 'token', 'authCode', 'code'];
                                    for (const key of possibleKeys) {
                                        const value = localStorage.getItem(key);
                                        if (value && value.length > 10) return { key, value };
                                    }
                                    return null;
                                }""")
                                
                                if auth_info:
                                    self.fingerprint_data["auth_info"] = auth_info
                                    self.status_update.emit(f"找到可能的授权信息: {auth_info['key']}")
                                    self.auth_code_received.emit(auth_info['value'])
                                    auth_code_found = True
                            except Exception as e:
                                self.status_update.emit(f"尝试从localStorage提取授权信息时出错: {str(e)}")
                        
                        if auth_code_found:
                            # 发送指纹数据
                            self.browser_fingerprint.emit(self.fingerprint_data)
                            self.automation_finished.emit(True, "自动化登录成功")
                        elif not auth_code_found:
                            self.status_update.emit("未能在限定时间内获取授权码")
                    except Exception as e:
                        self.status_update.emit(f"监控URL获取授权码时出错: {str(e)}")
                    
                    # 如果上面的方法没有获取到授权码，尝试从页面内容中查找
                    if not auth_code_found:
                        try:
                            # 尝试多种选择器查找授权码
                            selectors = [
                                ".auth-code", 
                                ".token", 
                                "code", 
                                "[data-test='auth-code']",
                                "pre",  # 有时授权码会显示在<pre>标签中
                                ".code-display",
                                "[id*='code']",  # ID中包含code的元素
                                "[id*='auth']",  # ID中包含auth的元素
                                "[class*='code']",  # class中包含code的元素
                                "[class*='auth']",  # class中包含auth的元素
                                "[data-testid='token']", # 新增可能包含token的元素
                                "[data-testid='auth-token']" # 新增可能包含auth-token的元素
                            ]
                            
                            auth_code = None
                            for selector in selectors:
                                element = page.query_selector(selector)
                                if element:
                                    text = element.text_content().strip()
                                    if text and len(text) > 10:  # 授权码通常较长
                                        auth_code = text
                                        self.status_update.emit(f"在选择器 '{selector}' 中找到可能的授权码")
                                        break
                            
                            if auth_code:
                                self.fingerprint_data["auth_code"] = auth_code
                                self.status_update.emit(f"成功获取授权码")
                                self.auth_code_received.emit(auth_code)
                                # 收集最终指纹
                                self.collect_final_fingerprint(page)
                                # 发送指纹数据
                                self.browser_fingerprint.emit(self.fingerprint_data)
                                self.automation_finished.emit(True, "自动化登录成功")
                            else:
                                # 尝试从设置页面中提取用户信息（最后的尝试）
                                if "settings" in page.url:
                                    self.status_update.emit("尝试从设置页面直接提取用户信息...")
                                    try:
                                        # 提取当前页面中所有可能包含用户信息或授权码的数据
                                        page_data = page.evaluate("""() => {
                                            try {
                                                // 提取所有localStorage数据
                                                const storage = {};
                                                for (let i = 0; i < localStorage.length; i++) {
                                                    const key = localStorage.key(i);
                                                    storage[key] = localStorage.getItem(key);
                                                }
                                                
                                                // 提取所有可能的授权字段
                                                const authData = {
                                                    pageUrl: window.location.href,
                                                    pageTitle: document.title
                                                };
                                                
                                                // 提取页面上的关键信息
                                                const emailElements = document.querySelectorAll('[data-testid="email"], .email, [class*="email"], [id*="email"]');
                                                if (emailElements.length > 0) {
                                                    authData.visibleEmail = emailElements[0].textContent.trim();
                                                }
                                                
                                                // 提取可能的授权状态
                                                const authElements = document.querySelectorAll('[data-testid="subscription"], .subscription, [class*="subscription"], [class*="account"], [class*="plan"]');
                                                if (authElements.length > 0) {
                                                    authData.subscriptionInfo = authElements[0].textContent.trim();
                                                }
                                                
                                                return { storage, authData };
                                            } catch (e) {
                                                console.error('提取设置页面数据时出错:', e);
                                                return {};
                                            }
                                        }""")
                                        
                                        if page_data:
                                            # 存储提取到的所有数据
                                            self.fingerprint_data["settings_page_data"] = page_data
                                            
                                            # 尝试找到授权相关信息
                                            storage = page_data.get("storage", {})
                                            for key, value in storage.items():
                                                if any(term in key.lower() for term in ["auth", "token", "code", "session"]):
                                                    if value and len(value) > 10:
                                                        self.fingerprint_data["extracted_auth_info"] = {
                                                            "key": key,
                                                            "value": value
                                                        }
                                                        self.status_update.emit(f"从设置页面localStorage提取到可能的授权信息: {key}")
                                                        self.auth_code_received.emit(value)
                                                        auth_code_found = True
                                                        break
                                            
                                            # 如果找到了email等信息但没有授权码，也算部分成功
                                            auth_data = page_data.get("authData", {})
                                            if auth_data.get("visibleEmail"):
                                                self.status_update.emit(f"从设置页面提取到用户邮箱: {auth_data.get('visibleEmail')}")
                                                self.fingerprint_data["extracted_email"] = auth_data.get("visibleEmail")
                                    except Exception as e:
                                        self.status_update.emit(f"尝试从设置页面提取数据时出错: {str(e)}")
                                
                                # 如果仍未找到授权码，尝试从页面标题和内容中提取
                                if not auth_code_found:
                                    # 尝试查看页面标题，有时授权码会在标题中
                                    title = page.title()
                                    if "code" in title.lower():
                                        self.status_update.emit("从页面标题中提取授权码")
                                        self.fingerprint_data["auth_code"] = title.strip()
                                        self.auth_code_received.emit(title.strip())
                                        # 收集最终指纹
                                        self.collect_final_fingerprint(page)
                                        # 发送指纹数据
                                        self.browser_fingerprint.emit(self.fingerprint_data)
                                        self.automation_finished.emit(True, "自动化登录成功")
                                    else:
                                        self.status_update.emit("页面中未找到授权码元素")
                                        # 尝试从页面内容中提取，寻找类似授权码的字符串
                                        page_content = page.content()
                                        import re
                                        # 增强正则表达式，匹配更多格式的授权码
                                        code_matches = re.findall(r'code=([a-zA-Z0-9_\-]{20,})|token=([a-zA-Z0-9_\-\.]{20,})|"auth(?:Token|Code)":\s*"([a-zA-Z0-9_\-\.]{20,})"', page_content)
                                        flat_matches = [m for sublist in code_matches for m in sublist if m]
                                        
                                        if flat_matches:
                                            self.fingerprint_data["auth_code"] = flat_matches[0]
                                            self.status_update.emit("从页面内容中提取到可能的授权码")
                                            self.auth_code_received.emit(flat_matches[0])
                                            # 收集最终指纹
                                            self.collect_final_fingerprint(page)
                                            # 发送指纹数据
                                            self.browser_fingerprint.emit(self.fingerprint_data)
                                            self.automation_finished.emit(True, "自动化登录成功")
                                        else:
                                            # 即使没找到授权码，也发送已收集的指纹
                                            self.browser_fingerprint.emit(self.fingerprint_data)
                                            # 如果至少检测到了设置页面，算作部分成功
                                            if settings_page_detected:
                                                self.status_update.emit("在设置页面中没有找到明确的授权码，但已收集账户信息")
                                                self.automation_finished.emit(True, "已成功登录到设置页面，但未找到明确的授权码")
                                            else:
                                                self.status_update.emit("授权码未找到，请手动复制")
                                                self.automation_finished.emit(False, "未能获取有效授权码")
                        except Exception as e:
                            self.status_update.emit(f"尝试提取授权码时出错: {str(e)}")
                            # 即使出错，也发送已收集的指纹
                            self.browser_fingerprint.emit(self.fingerprint_data)
                            # 如果至少检测到了设置页面，算作部分成功
                            if settings_page_detected:
                                self.automation_finished.emit(True, "已成功登录到设置页面，但提取授权码时出错")
                            else:
                                self.automation_finished.emit(False, "尝试提取授权码失败")
                    
                    # 等待用户手动关闭或复制
                    self.status_update.emit("请在完成后手动关闭浏览器或复制授权码...")
                    
                    # 等待直到线程被终止
                    while self.running:
                        time.sleep(1)
                        # 检查页面是否还存在
                        try:
                            page.evaluate("1")  # 简单的JS表达式，测试页面是否还响应
                        except:
                            break
                        
                except Exception as e:
                    self.status_update.emit(f"自动化过程中出错: {str(e)}")
                    # 即使出错，也发送已收集的指纹
                    self.browser_fingerprint.emit(self.fingerprint_data)
                    self.automation_finished.emit(False, f"自动化失败: {str(e)}")
                finally:
                    try:
                        # 尝试在关闭前再次收集指纹
                        self.collect_final_fingerprint(page)
                        browser.close()
                    except:
                        pass
                    
        except Exception as e:
            self.status_update.emit(f"初始化浏览器自动化失败: {str(e)}")
            self.automation_finished.emit(False, f"初始化失败: {str(e)}")
    
    def collect_browser_fingerprint(self, page):
        """收集浏览器基本指纹"""
        try:
            # 收集用户代理
            user_agent = page.evaluate("() => navigator.userAgent")
            self.fingerprint_data["user_agent"] = user_agent
            
            # 收集平台信息
            platform_info = page.evaluate("() => navigator.platform")
            self.fingerprint_data["platform"] = platform_info
            
            # 收集语言信息
            language = page.evaluate("() => navigator.language")
            self.fingerprint_data["language"] = language
            
            # 收集屏幕信息
            screen_info = page.evaluate("() => ({width: screen.width, height: screen.height, colorDepth: screen.colorDepth})")
            self.fingerprint_data["screen"] = screen_info
            
            # 收集cookies
            cookies = page.context.cookies()
            if cookies:
                self.fingerprint_data["initial_cookies"] = cookies
                
            self.status_update.emit("已收集基本浏览器指纹信息")
        except Exception as e:
            self.status_update.emit(f"收集浏览器指纹时出错: {str(e)}")
            
    def collect_google_fingerprint(self, page):
        """收集Google登录相关指纹"""
        try:
            # 收集Google相关的Cookies
            cookies = page.context.cookies()
            google_cookies = [cookie for cookie in cookies if '.google.com' in cookie.get('domain', '')]
            if google_cookies:
                self.fingerprint_data["google_cookies"] = google_cookies
                
            # 收集页面上可能的Google账号信息
            accounts = page.query_selector_all("div[data-identifier]")
            if accounts:
                google_accounts = []
                for account in accounts:
                    identifier = account.get_attribute('data-identifier')
                    if identifier:
                        google_accounts.append(identifier)
                if google_accounts:
                    self.fingerprint_data["google_accounts"] = google_accounts
                    
            self.status_update.emit("已收集Google登录相关指纹")
        except Exception as e:
            self.status_update.emit(f"收集Google指纹时出错: {str(e)}")
            
    def collect_github_fingerprint(self, page):
        """收集GitHub登录相关指纹"""
        try:
            # 收集GitHub相关的Cookies
            cookies = page.context.cookies()
            github_cookies = [cookie for cookie in cookies if '.github.com' in cookie.get('domain', '')]
            if github_cookies:
                self.fingerprint_data["github_cookies"] = github_cookies
                
            self.status_update.emit("已收集GitHub登录相关指纹")
        except Exception as e:
            self.status_update.emit(f"收集GitHub指纹时出错: {str(e)}")
            
    def collect_final_fingerprint(self, page):
        """收集最终的所有浏览器指纹"""
        try:
            # 收集最终的所有cookies
            cookies = page.context.cookies()
            if cookies:
                self.fingerprint_data["final_cookies"] = cookies
                
            # 收集localStorage
            local_storage = page.evaluate("""() => {
                let result = {};
                for (let i = 0; i < localStorage.length; i++) {
                    const key = localStorage.key(i);
                    result[key] = localStorage.getItem(key);
                }
                return result;
            }""")
            if local_storage:
                self.fingerprint_data["local_storage"] = local_storage
                
            # 收集sessionStorage
            session_storage = page.evaluate("""() => {
                let result = {};
                for (let i = 0; i < sessionStorage.length; i++) {
                    const key = sessionStorage.key(i);
                    result[key] = sessionStorage.getItem(key);
                }
                return result;
            }""")
            if session_storage:
                self.fingerprint_data["session_storage"] = session_storage
                
            # 获取当前URL
            current_url = page.url
            self.fingerprint_data["last_url"] = current_url
            
            # 获取页面标题
            title = page.title()
            self.fingerprint_data["page_title"] = title
            
            # 如果是设置页面，收集额外信息
            if "settings" in current_url:
                try:
                    # 提取用户相关信息
                    user_info = page.evaluate("""() => {
                        try {
                            // 尝试获取用户数据
                            const userData = {};
                            
                            // 从localStorage中提取用户信息
                            try {
                                const user = localStorage.getItem('user');
                                if (user) userData.user = JSON.parse(user);
                            } catch (e) { console.error('解析user数据失败:', e); }
                            
                            // 从localStorage中提取auth token
                            userData.auth_token = localStorage.getItem('auth_token') || '';
                            
                            // 从localStorage中提取refresh token
                            userData.refresh_token = localStorage.getItem('refresh_token') || '';
                            
                            // 从localStorage中提取其他可能的授权信息
                            for (let i = 0; i < localStorage.length; i++) {
                                const key = localStorage.key(i);
                                if (key.includes('token') || key.includes('auth') || key.includes('session')) {
                                    userData[key] = localStorage.getItem(key);
                                }
                            }
                            
                            // 尝试从页面元素获取信息
                            const emailElements = document.querySelectorAll('[data-testid="email"], .email, [class*="email"], [id*="email"]');
                            if (emailElements.length > 0) {
                                userData.visible_email = emailElements[0].textContent.trim();
                            }
                            
                            // 尝试获取订阅信息
                            const subscriptionElements = document.querySelectorAll('[data-testid="subscription"], .subscription, [class*="subscription"], [id*="subscription"], [class*="plan"], [id*="plan"]');
                            if (subscriptionElements.length > 0) {
                                userData.subscription_info = subscriptionElements[0].textContent.trim();
                            }
                            
                            return userData;
                        } catch (e) {
                            console.error('获取用户信息时出错:', e);
                            return {};
                        }
                    }""")
                    
                    if user_info:
                        self.fingerprint_data["settings_user_info"] = user_info
                        self.status_update.emit("已从设置页面收集用户信息")
                        
                        # 如果从设置页面获取到了用户邮箱，保存它
                        if user_info.get("visible_email"):
                            self.fingerprint_data["email"] = user_info.get("visible_email")
                            
                        # 如果从设置页面获取到了auth_token，将其作为备选授权码
                        if user_info.get("auth_token") and not self.fingerprint_data.get("auth_code"):
                            self.fingerprint_data["auth_token"] = user_info.get("auth_token")
                            
                except Exception as e:
                    self.status_update.emit(f"从设置页面提取用户信息时出错: {str(e)}")
            
            self.status_update.emit("已收集完整的浏览器指纹信息")
        except Exception as e:
            self.status_update.emit(f"收集最终指纹时出错: {str(e)}")
    
    def stop(self):
        """停止线程"""
        self.running = False
        self.terminate()
        
    def install_playwright(self):
        """安装playwright库"""
        try:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
            subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
            self.status_update.emit("playwright安装成功")
        except Exception as e:
            self.status_update.emit(f"playwright安装失败: {str(e)}")
            raise
            
class AuthDialog(QDialog):
    """授权登录对话框"""
    
    # 定义信号
    auth_success = pyqtSignal(dict)  # 授权成功信号，传递用户信息
    
    # 定义URL配置
    BASE_URL = "https://www.cursor.com/cn"
    AUTH_URL = "https://www.cursor.com/api/auth/login"  # 授权登录URL
    REGISTER_URL = "https://authenticator.cursor.sh/sign-up"  # 注册URL
    GITHUB_AUTH_BASE_URL = "https://authenticator.cursor.sh/api/login"  # GitHub授权基础URL
    GOOGLE_AUTH_BASE_URL = "https://authenticator.cursor.sh/api/login"  # Google授权基础URL
    AUTHENTICATOR_URL = "https://authenticator.cursor.sh/"  # 授权器基础URL
    SETTINGS_URL = "https://www.cursor.com/cn/settings"  # 设置页面URL
    
    # 新版授权URL（解码后）
    NEW_AUTH_URL = "https://authenticator.cursor.sh/?client_id=client_01GS6W3C96KW4WRS6Z93JCE2RJ&redirect_uri=https://cursor.com/api/auth/callback&response_type=code&state={\"returnTo\":\"/settings\"}"
    
    # 指纹存储配置
    FINGERPRINT_DIR = "fingerprints"  # 指纹文件存储目录
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 存储当前浏览器指纹
        self.current_fingerprint = {}
        
        self.setWindowTitle("Cursor授权登录")
        self.setMinimumWidth(400)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        
        # 创建布局
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # 添加说明文本
        info_text = """请选择登录方式并完成授权：
1. 选择登录方式（邮箱/Google/Github）
2. 点击"打开授权页面"按钮
3. 在浏览器中完成授权
4. 将授权码粘贴到下方输入框
5. 点击"验证授权"完成登录"""
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666666; padding: 10px;")
        layout.addWidget(info_label)
        
        # 创建登录方式选择区域
        login_group = QGroupBox("登录方式")
        login_layout = QVBoxLayout()
        
        self.login_type_group = QButtonGroup(self)
        
        self.email_radio = QRadioButton("邮箱登录")
        self.email_radio.setChecked(True)
        self.login_type_group.addButton(self.email_radio, 1)
        login_layout.addWidget(self.email_radio)
        
        self.google_radio = QRadioButton("Google授权登录")
        self.login_type_group.addButton(self.google_radio, 2)
        login_layout.addWidget(self.google_radio)
        
        self.github_radio = QRadioButton("Github授权登录")
        self.login_type_group.addButton(self.github_radio, 3)
        login_layout.addWidget(self.github_radio)
        
        # 添加自动化登录选项
        self.auto_login_check = QCheckBox("使用浏览器自动化登录")
        self.auto_login_check.setChecked(True)
        login_layout.addWidget(self.auto_login_check)
        
        # 添加保存/使用浏览器指纹选项
        self.save_fingerprint_check = QCheckBox("保存浏览器指纹")
        self.save_fingerprint_check.setChecked(True)
        self.save_fingerprint_check.setToolTip("保存浏览器指纹用于后续登录")
        login_layout.addWidget(self.save_fingerprint_check)
        
        self.use_fingerprint_check = QCheckBox("使用已保存的指纹")
        self.use_fingerprint_check.setChecked(True)
        self.use_fingerprint_check.setToolTip("使用已保存的浏览器指纹进行登录")
        login_layout.addWidget(self.use_fingerprint_check)
        
        # 添加邮箱登录的凭据输入（当选择邮箱登录并开启自动化时显示）
        self.credentials_group = QGroupBox("登录凭据（可选）")
        credentials_layout = QFormLayout()
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("输入邮箱地址")
        credentials_layout.addRow("邮箱:", self.email_input)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("输入密码")
        self.password_input.setEchoMode(QLineEdit.Password)
        credentials_layout.addRow("密码:", self.password_input)
        
        self.credentials_group.setLayout(credentials_layout)
        login_layout.addWidget(self.credentials_group)
        
        # 连接信号
        self.email_radio.toggled.connect(self.update_credentials_visibility)
        self.github_radio.toggled.connect(self.update_credentials_visibility)
        self.google_radio.toggled.connect(self.update_credentials_visibility)
        self.auto_login_check.toggled.connect(self.update_credentials_visibility)
        
        login_group.setLayout(login_layout)
        layout.addWidget(login_group)
        
        # 创建授权码输入区域
        auth_group = QGroupBox("授权信息")
        auth_layout = QFormLayout()
        
        self.auth_code_input = QLineEdit()
        self.auth_code_input.setPlaceholderText("请输入授权码")
        self.auth_code_input.setMinimumHeight(32)
        auth_layout.addRow("授权码:", self.auth_code_input)
        
        auth_group.setLayout(auth_layout)
        layout.addWidget(auth_group)
        
        # 创建按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.open_auth_btn = QPushButton("打开授权页面")
        self.open_auth_btn.setMinimumHeight(32)
        self.open_auth_btn.clicked.connect(self.open_auth_page)
        button_layout.addWidget(self.open_auth_btn)
        
        self.verify_btn = QPushButton("验证授权")
        self.verify_btn.setMinimumHeight(32)
        self.verify_btn.clicked.connect(self.verify_auth)
        button_layout.addWidget(self.verify_btn)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setMinimumHeight(32)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        # 添加状态标签
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # 初始化自动化线程
        self.automation_thread = None
        
        # 初始化UI状态
        self.update_credentials_visibility()
        
        # 确保指纹目录存在 - 移到status_label创建后执行
        self.ensure_fingerprint_dir()
        
        # 设置样式
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            
            QGroupBox {
                border: 2px solid #4a90e2;
                border-radius: 8px;
                margin-top: 12px;
                padding: 15px;
            }
            
            QGroupBox::title {
                color: #4a90e2;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                background: white;
                font-weight: bold;
            }
            
            QPushButton {
                padding: 8px 16px;
                border-radius: 4px;
                border: none;
                color: white;
                font-weight: bold;
                min-width: 80px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4a90e2, stop:1 #357abd);
            }
            
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #357abd, stop:1 #2d6da3);
            }
            
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2d6da3, stop:1 #357abd);
            }
            
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background: white;
            }
            
            QLineEdit:focus {
                border-color: #4a90e2;
            }
            
            QLineEdit:hover {
                border-color: #357abd;
            }
            
            QRadioButton, QCheckBox {
                margin-top: 2px;
                margin-bottom: 2px;
                font-size: 14px;
            }
            
            QRadioButton::indicator, QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            
            QCheckBox::indicator:checked {
                background-color: #4a90e2;
                border: 2px solid #4a90e2;
                border-radius: 2px;
            }
        """)
        
    def ensure_fingerprint_dir(self):
        """确保指纹存储目录存在"""
        try:
            if not os.path.exists(self.FINGERPRINT_DIR):
                os.makedirs(self.FINGERPRINT_DIR)
                self.status_label.setText(f"创建指纹存储目录: {self.FINGERPRINT_DIR}")
        except Exception as e:
            self.status_label.setText(f"创建指纹目录失败: {str(e)}")
            self.status_label.setStyleSheet("color: #dc3545;")
        
    def update_credentials_visibility(self):
        """根据选择更新登录凭据区域的可见性"""
        login_id = self.login_type_group.checkedId()
        is_email_selected = (login_id == 1)  # 邮箱登录
        is_github_selected = (login_id == 3)  # GitHub登录
        is_auto_login = self.auto_login_check.isChecked()
        
        # 只有选择邮箱登录或GitHub登录，并且开启自动化时才显示凭据区域
        self.credentials_group.setVisible((is_email_selected or is_github_selected) and is_auto_login)
        
        # 更新凭据输入框的标签
        if is_github_selected:
            self.credentials_group.setTitle("GitHub凭据（可选）")
            self.email_input.setPlaceholderText("输入GitHub用户名")
            self.password_input.setPlaceholderText("输入GitHub密码")
        else:
            self.credentials_group.setTitle("登录凭据（可选）")
            self.email_input.setPlaceholderText("输入邮箱地址")
            self.password_input.setPlaceholderText("输入密码")
        
    def open_auth_page(self):
        """打开授权页面"""
        # 获取登录方式
        login_id = self.login_type_group.checkedId()
        login_type = self.get_login_type_name()
        
        # 构建URL - 使用新版授权URL作为基础
        # 这是解码过的正确URL格式，确保returnTo为settings页面
        base_auth_url = "https://authenticator.cursor.sh/?client_id=client_01GS6W3C96KW4WRS6Z93JCE2RJ&redirect_uri=https://cursor.com/api/auth/callback&response_type=code&state={\"returnTo\":\"/settings\"}"
        
        if login_id == 1:  # 邮箱登录
            # 对于邮箱登录，直接使用标准授权URL
            auth_url = base_auth_url
        elif login_id == 2:  # Google登录
            # 对于Google登录也使用标准授权URL，在自动化过程中会点击Google按钮
            auth_url = base_auth_url
        elif login_id == 3:  # Github登录
            # GitHub登录也使用标准授权URL，在自动化过程中会点击GitHub按钮
            auth_url = base_auth_url
        else:
            auth_url = base_auth_url
        
        try:
            # 检查是否开启自动化
            if self.auto_login_check.isChecked():
                # 检查playwright是否已安装
                try:
                    import playwright
                except ImportError:
                    self.status_label.setText("正在安装playwright...")
                    self.status_label.setStyleSheet("color: #17a2b8;")
                    QApplication.processEvents()  # 更新UI
                    try:
                        import subprocess
                        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
                        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
                        self.status_label.setText("playwright安装成功")
                        # 重新导入playwright
                        import playwright
                    except Exception as e:
                        QMessageBox.warning(self, "错误", f"安装playwright失败: {str(e)}")
                        self.status_label.setText("安装playwright失败，将使用普通模式")
                        self.status_label.setStyleSheet("color: #dc3545;")
                        # 尝试使用Chrome浏览器打开
                        try:
                            # 获取父窗口的system_config
                            parent = self.parent()
                            if parent and hasattr(parent, 'system_config'):
                                chrome_path = parent.system_config.get_config("chrome", "executable_path", "")
                                if chrome_path and os.path.exists(chrome_path):
                                    # 使用Chrome打开
                                    import subprocess
                                    subprocess.Popen([chrome_path, auth_url])
                                    self.status_label.setText(f"已使用Chrome打开{login_type}授权页面，请在浏览器中完成授权")
                                    self.status_label.setStyleSheet("color: #17a2b8;")
                                    return
                            
                            # 如果无法使用Chrome，则使用默认浏览器
                            webbrowser.open(auth_url)
                            self.status_label.setText(f"已打开{login_type}授权页面，请在浏览器中完成授权")
                            self.status_label.setStyleSheet("color: #17a2b8;")
                        except Exception as ex:
                            # 切换到普通模式
                            webbrowser.open(auth_url)
                            self.status_label.setText(f"Chrome启动失败，已使用默认浏览器打开{login_type}授权页面")
                            self.status_label.setStyleSheet("color: #ffc107;")  # 黄色，表示警告
                        return
                        
                # 获取邮箱和密码（如果有）
                email = self.email_input.text().strip()
                password = self.password_input.text().strip()
                
                # 停止旧的自动化线程（如果有）
                if self.automation_thread and self.automation_thread.isRunning():
                    self.automation_thread.stop()
                    
                # 创建新的自动化线程
                self.automation_thread = BrowserAutomationThread(auth_url, login_type, email, password)
                
                # 如果选择使用已保存的指纹，尝试加载
                fingerprint_data = None
                if self.use_fingerprint_check.isChecked() and email:
                    fingerprint_data = self.load_fingerprint(login_type, email)
                    if fingerprint_data:
                        self.status_label.setText(f"正在使用已保存的{login_type}指纹进行登录...")
                        # 将加载的指纹传递给浏览器自动化线程
                        self.automation_thread.fingerprint_data = fingerprint_data
                
                # 连接信号
                self.automation_thread.status_update.connect(self.update_status)
                self.automation_thread.auth_code_received.connect(self.set_auth_code)
                self.automation_thread.automation_finished.connect(self.handle_automation_finished)
                self.automation_thread.browser_fingerprint.connect(self.handle_browser_fingerprint)
                
                # 启动线程
                self.automation_thread.start()
                
                self.status_label.setText(f"正在启动{login_type}自动化登录...")
                self.status_label.setStyleSheet("color: #17a2b8;")
            else:
                # 手动模式，尝试使用Chrome浏览器打开
                try:
                    # 获取父窗口的system_config
                    parent = self.parent()
                    if parent and hasattr(parent, 'system_config'):
                        chrome_path = parent.system_config.get_config("chrome", "executable_path", "")
                        if chrome_path and os.path.exists(chrome_path):
                            # 使用Chrome打开
                            import subprocess
                            subprocess.Popen([chrome_path, auth_url])
                            self.status_label.setText(f"已使用Chrome打开{login_type}授权页面，请在浏览器中完成授权")
                            self.status_label.setStyleSheet("color: #17a2b8;")
                            return
                    
                    # 如果无法获取Chrome路径，则使用默认浏览器
                    webbrowser.open(auth_url)
                    self.status_label.setText(f"已打开{login_type}授权页面，请在浏览器中完成授权")
                    self.status_label.setStyleSheet("color: #17a2b8;")
                except Exception as e:
                    webbrowser.open(auth_url)
                    self.status_label.setText(f"Chrome启动失败，已使用默认浏览器打开{login_type}授权页面")
                    self.status_label.setStyleSheet("color: #ffc107;")  # 黄色，表示警告
        except Exception as e:
            QMessageBox.warning(self, "错误", f"打开授权页面失败: {str(e)}")
            self.status_label.setText("打开授权页面失败")
            self.status_label.setStyleSheet("color: #dc3545;")
    
    @pyqtSlot(str)
    def update_status(self, message):
        """更新状态消息"""
        self.status_label.setText(message)
        self.status_label.setStyleSheet("color: #17a2b8;")
    
    @pyqtSlot(str)
    def set_auth_code(self, code):
        """设置授权码"""
        self.auth_code_input.setText(code)
    
    @pyqtSlot(bool, str)
    def handle_automation_finished(self, success, message):
        """处理自动化完成事件"""
        if success:
            self.status_label.setText(message)
            self.status_label.setStyleSheet("color: #28a745;")
        else:
            self.status_label.setText(message)
            self.status_label.setStyleSheet("color: #dc3545;")
    
    @pyqtSlot(dict)
    def handle_browser_fingerprint(self, fingerprint):
        """处理收集到的浏览器指纹"""
        # 保存当前收集到的指纹
        self.current_fingerprint = fingerprint
        
        # 如果勾选了保存指纹，就保存到文件
        if self.save_fingerprint_check.isChecked():
            self.save_fingerprint(fingerprint)
        
        # 打印指纹信息（可以在调试时使用）
        print(f"收集到的浏览器指纹: {len(fingerprint)} 个字段")
        
    def save_fingerprint(self, fingerprint):
        """保存浏览器指纹到文件"""
        try:
            # 确保目录存在
            self.ensure_fingerprint_dir()
            
            # 构建文件名
            login_type = fingerprint.get("login_type", "unknown")
            email = fingerprint.get("email", "unknown")
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"{login_type}_{email}_{timestamp}.json"
            filepath = os.path.join(self.FINGERPRINT_DIR, filename)
            
            # 保存指纹到文件
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(fingerprint, f, indent=2, ensure_ascii=False)
                
            self.status_label.setText(f"浏览器指纹已保存: {filename}")
            self.status_label.setStyleSheet("color: #28a745;")
            
            # 同时保存一个最新的指纹文件
            latest_filename = f"{login_type}_{email}_latest.json"
            latest_filepath = os.path.join(self.FINGERPRINT_DIR, latest_filename)
            with open(latest_filepath, 'w', encoding='utf-8') as f:
                json.dump(fingerprint, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.status_label.setText(f"保存指纹失败: {str(e)}")
            self.status_label.setStyleSheet("color: #dc3545;")
            
    def load_fingerprint(self, login_type, email):
        """加载指定类型和邮箱的最新指纹"""
        try:
            # 查找最新的指纹文件
            latest_filename = f"{login_type}_{email}_latest.json"
            filepath = os.path.join(self.FINGERPRINT_DIR, latest_filename)
            
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    fingerprint = json.load(f)
                self.status_label.setText(f"已加载{login_type}指纹: {email}")
                return fingerprint
            else:
                # 如果没有最新的，就查找匹配的所有指纹文件
                pattern = f"{login_type}_{email}_*.json"
                import glob
                matching_files = sorted(glob.glob(os.path.join(self.FINGERPRINT_DIR, pattern)), reverse=True)
                
                if matching_files:
                    # 使用最新的指纹文件
                    with open(matching_files[0], 'r', encoding='utf-8') as f:
                        fingerprint = json.load(f)
                    self.status_label.setText(f"已加载{login_type}历史指纹: {email}")
                    return fingerprint
                    
            self.status_label.setText(f"未找到{login_type}指纹: {email}")
            return None
        except Exception as e:
            self.status_label.setText(f"加载指纹失败: {str(e)}")
            self.status_label.setStyleSheet("color: #dc3545;")
            return None
    
    def get_login_type_name(self):
        """获取当前选择的登录方式名称"""
        login_id = self.login_type_group.checkedId()
        if login_id == 1:
            return "邮箱"
        elif login_id == 2:
            return "Google"
        elif login_id == 3:
            return "Github"
        return "未知"
            
    def verify_auth(self):
        """验证授权码"""
        auth_code = self.auth_code_input.text().strip()
        if not auth_code:
            QMessageBox.warning(self, "提示", "请输入授权码")
            return
            
        # 实现授权验证逻辑
        try:
            # 这里应该调用实际的授权验证API
            login_type = self.get_login_type_name()
            
            # 构建用户信息，包含浏览器指纹
            user_info = {
                "email": self.email_input.text().strip() or self.current_fingerprint.get("email", "test@example.com"),
                "status": "正常",
                "expire_time": "2024-12-31",
                "login_type": login_type,
                "fingerprint": self.current_fingerprint if self.current_fingerprint else {},
                "auth_code": auth_code
            }
            
            self.auth_success.emit(user_info)
            QMessageBox.information(self, "成功", f"{login_type}授权验证成功")
            
            # 停止自动化线程（如果有）
            if self.automation_thread and self.automation_thread.isRunning():
                self.automation_thread.stop()
                
            self.accept()
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"授权验证失败: {str(e)}")
            self.status_label.setText("授权验证失败")
            self.status_label.setStyleSheet("color: #dc3545;")
            
    def closeEvent(self, event):
        """对话框关闭事件"""
        # 停止自动化线程（如果有）
        if self.automation_thread and self.automation_thread.isRunning():
            self.automation_thread.stop()
        event.accept() 