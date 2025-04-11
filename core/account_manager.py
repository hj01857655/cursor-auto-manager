from PyQt5.QtCore import QObject, pyqtSignal
import json
import os
import logging
import uuid
import datetime
from typing import Dict, List, Optional
from core.db_manager import DbManager

class AccountManager(QObject):
    """账号管理器类"""
    
    # 定义信号
    account_list_updated = pyqtSignal(list)
    current_account_changed = pyqtSignal(dict)
    threshold_updated = pyqtSignal(dict)
    
    # 存储账号信息的键
    AUTH_KEY = "cursor.auth.accounts"
    AUTH_CURRENT_KEY = "cursor.auth.current_account"
    THRESHOLDS_KEY = "cursor.auth.thresholds"
    
    # Cursor 授权相关的键
    CURSOR_AUTH_EMAIL = "cursorAuth/cachedEmail"
    CURSOR_AUTH_SIGNUP_TYPE = "cursorAuth/cachedSignUpType"
    CURSOR_AUTH_REFRESH_TOKEN = "cursorAuth/refreshToken"
    CURSOR_AUTH_ACCESS_TOKEN = "cursorAuth/accessToken"
    CURSOR_AUTH_MEMBERSHIP = "cursorAuth/stripeMembershipType"
    
    def __init__(self):
        super().__init__()
        self.accounts: List[Dict] = []
        self.current_account: Optional[Dict] = None
        self.thresholds = {
            "max_requests_per_minute": 60,
            "max_concurrent_sessions": 3,
            "session_timeout_minutes": 30
        }
        self.logger = logging.getLogger(__name__)
        self.db_manager = DbManager()
        self.load_accounts()
        
    def load_accounts(self):
        """从JSON文件加载账号列表"""
        try:
            # 尝试从配置文件加载
            self._load_accounts_from_file()
                
            # 发送更新信号
            self.account_list_updated.emit(self.accounts)
            self.threshold_updated.emit(self.thresholds)
            
        except Exception as e:
            self.logger.error(f"加载账号列表失败: {e}")
            # 创建空的账号列表
            self.accounts = []
            self.current_account = None
    
    def _load_from_cursor_auth_data(self, data):
        """从Cursor原生授权数据加载账号信息
        
        Args:
            data: 从数据库获取的键值对数据
        """
        try:
            # 检查所需的键是否存在
            if self.CURSOR_AUTH_EMAIL in data:
                email = data.get(self.CURSOR_AUTH_EMAIL)
                if not email:
                    return
                
                # 构建账号信息
                account = {
                    "id": str(uuid.uuid4()),
                    "email": email,
                    "auth_source": data.get(self.CURSOR_AUTH_SIGNUP_TYPE, "未知"),
                    "status": "正常",
                    "last_login": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # 添加令牌信息
                if self.CURSOR_AUTH_ACCESS_TOKEN in data:
                    account["access_token"] = data[self.CURSOR_AUTH_ACCESS_TOKEN]
                if self.CURSOR_AUTH_REFRESH_TOKEN in data:
                    account["refresh_token"] = data[self.CURSOR_AUTH_REFRESH_TOKEN]
                    
                # 添加会员类型信息
                if self.CURSOR_AUTH_MEMBERSHIP in data:
                    membership = data[self.CURSOR_AUTH_MEMBERSHIP]
                    account["membership"] = membership
                    
                # 解析令牌中的过期时间
                expire_date = None
                if self.CURSOR_AUTH_ACCESS_TOKEN in data or self.CURSOR_AUTH_REFRESH_TOKEN in data:
                    # 优先使用刷新令牌，因为它通常有更长的有效期
                    token = data.get(self.CURSOR_AUTH_REFRESH_TOKEN) or data.get(self.CURSOR_AUTH_ACCESS_TOKEN)
                    if token:
                        try:
                            # 解析JWT令牌
                            import base64
                            import json
                            
                            # 获取JWT有效载荷部分（第二部分）
                            payload = token.split('.')[1]
                            # 添加padding
                            payload += '=' * (4 - len(payload) % 4)
                            # 解码
                            decoded = base64.b64decode(payload).decode('utf-8')
                            # 解析JSON
                            payload_data = json.loads(decoded)
                            
                            # 获取过期时间（exp字段）
                            if 'exp' in payload_data:
                                # JWT的exp是Unix时间戳（秒）
                                exp_timestamp = payload_data['exp']
                                expire_date = datetime.datetime.fromtimestamp(exp_timestamp)
                                self.logger.info(f"从令牌解析到过期时间: {expire_date}")
                        except Exception as e:
                            self.logger.error(f"解析令牌过期时间失败: {e}")
                
                # 根据解析到的过期时间或会员类型设置过期时间
                if expire_date:
                    account["expire_time"] = expire_date.strftime("%Y-%m-%d %H:%M:%S")
                    # 计算剩余天数
                    days_left = (expire_date - datetime.datetime.now()).days
                    if days_left <= 0:
                        account["status"] = "已过期"
                    elif days_left <= 7:
                        account["status"] = f"即将过期({days_left}天)"
                    else:
                        account["status"] = "正常"
                elif account.get("membership") == "pro":
                    account["expire_time"] = "永久"
                    account["status"] = "永久有效"
                elif account.get("membership") == "free_trial":
                    # 试用期设置为从当前时间开始14天（如果无法从令牌获取）
                    trial_expire_date = datetime.datetime.now() + datetime.timedelta(days=14)
                    account["expire_time"] = trial_expire_date.strftime("%Y-%m-%d")
                    account["status"] = "试用期"
                else:
                    account["expire_time"] = "未知"
                    account["status"] = "未知期限"
                        
                # 检查是否已存在相同邮箱的账号
                existing_acc = next((acc for acc in self.accounts if acc.get("email") == email), None)
                if existing_acc:
                    # 更新现有账号
                    existing_acc.update(account)
                    self.logger.info(f"从Cursor授权数据更新账号: {email}")
                else:
                    # 添加新账号
                    self.accounts.append(account)
                    self.logger.info(f"从Cursor授权数据加载账号: {email}")
                    
                # 设置为当前账号
                self.current_account = existing_acc if existing_acc else account
                
                # 保存到JSON文件
                self.save_accounts()
                
                return True
                
        except Exception as e:
            self.logger.error(f"从Cursor授权数据加载账号失败: {e}")
        
        return False
            
    def _load_accounts_from_file(self):
        """从配置文件加载账号"""
        try:
            config_path = os.path.join("config", "accounts.json")
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.accounts = data.get("accounts", [])
                    self.thresholds = data.get("thresholds", self.thresholds)
                    
                    # 尝试获取当前账号
                    current_account_id = data.get("current_account_id")
                    if current_account_id:
                        self.current_account = next((acc for acc in self.accounts if acc.get("id") == current_account_id), None)
                    elif self.accounts:
                        self.current_account = self.accounts[0]
                        
                    self.logger.info(f"从配置文件加载了 {len(self.accounts)} 个账号")
        except Exception as e:
            self.logger.error(f"从配置文件加载账号失败: {e}")
            
    def _save_accounts_to_file(self):
        """保存账号列表到配置文件"""
        try:
            # 确保config目录存在
            config_dir = "config"
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
                
            config_path = os.path.join(config_dir, "accounts.json")
            
            # 创建保存数据
            save_data = {
                "accounts": self.accounts,
                "thresholds": self.thresholds
            }
            
            # 保存当前账号ID
            if self.current_account:
                save_data["current_account_id"] = self.current_account.get("id")
                
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(save_data, f, indent=4, ensure_ascii=False)
                
            self.logger.info(f"已保存 {len(self.accounts)} 个账号到配置文件")
            return True
        except Exception as e:
            self.logger.error(f"保存账号到配置文件失败: {e}")
            return False
            
    def save_accounts(self):
        """保存账号信息到JSON文件"""
        # 保存到文件
        self._save_accounts_to_file()
        
        # 发送更新信号
        self.account_list_updated.emit(self.accounts)
            
    def add_account(self, account: Dict):
        """添加新账号或更新已有账号
        
        Args:
            account: 账号信息字典，必须包含id或email字段作为唯一标识
            
        Returns:
            bool: 是否成功添加或更新
        """
        # 确保账号有唯一标识
        if not account.get('id') and not account.get('email'):
            self.logger.error("添加账号失败：账号必须包含id或email字段")
            return False
            
        # 查找是否已存在相同账号（通过id或email）
        existing_account = None
        if account.get('id'):
            existing_account = next((acc for acc in self.accounts if acc.get('id') == account.get('id')), None)
            
        if not existing_account and account.get('email'):
            existing_account = next((acc for acc in self.accounts if acc.get('email') == account.get('email')), None)
            
        # 如果账号已存在，则更新信息
        if existing_account:
            # 更新现有账号信息，保留原有的id
            account_id = existing_account.get('id')
            existing_account.update(account)
            
            # 确保id不变
            if account_id:
                existing_account['id'] = account_id
                
            self.logger.info(f"更新账号信息: {existing_account.get('email')}")
        else:
            # 添加新账号
            # 确保有唯一ID
            if not account.get('id'):
                account['id'] = str(uuid.uuid4())
                
            # 确保有时间戳
            if not account.get('created_at'):
                account['created_at'] = datetime.datetime.now().isoformat()
                
            # 添加到账号列表
            self.accounts.append(account)
            self.logger.info(f"添加新账号: {account.get('email')}")
            
        # 保存并通知更新
        self.save_accounts()
        
        # 如果没有当前账号，则将新添加的账号设为当前账号
        if not self.current_account:
            self.switch_account(account.get('id'))
            
        return True
        
    def remove_account(self, account_id: str):
        """删除账号"""
        self.accounts = [acc for acc in self.accounts if acc.get("id") != account_id]
        # 如果删除的是当前账号，重置当前账号
        if self.current_account and self.current_account.get("id") == account_id:
            self.current_account = self.accounts[0] if self.accounts else None
            if self.current_account:
                self.current_account_changed.emit(self.current_account)
        self.save_accounts()
        
    def switch_account(self, account_id: str):
        """切换当前账号"""
        for account in self.accounts:
            if account.get("id") == account_id:
                self.current_account = account
                self.current_account_changed.emit(account)
                # 保存当前账号信息
                self.save_accounts()
                return True
        return False
        
    def update_thresholds(self, new_thresholds: Dict):
        """更新阈值设置"""
        self.thresholds.update(new_thresholds)
        self.save_accounts()
        self.threshold_updated.emit(self.thresholds)
        
    def get_current_account(self):
        """获取当前账号"""
        # 如果没有当前账号但有账号列表，设置第一个为当前账号
        if not self.current_account and self.accounts:
            self.current_account = self.accounts[0]
            self.current_account_changed.emit(self.current_account)
            self.save_accounts()
        return self.current_account
        
    def refresh_account_status(self):
        """刷新所有账号状态
        
        检查所有账号的状态并更新，主要是检查授权是否有效、过期时间等。
        只刷新账号状态，不会尝试登录。
        
        Returns:
            bool: 是否成功刷新账号状态
        """
        if not self.accounts:
            self.logger.info("没有账号需要刷新")
            self.account_list_updated.emit(self.accounts)
            return True
            
        try:
            for account in self.accounts:
                # 检查授权码是否存在
                if not account.get('auth_code'):
                    account['status'] = "未授权"
                    continue
                    
                # 检查过期时间（如果有）
                if 'expire_time' in account:
                    import datetime
                    try:
                        # 尝试解析过期时间字符串
                        expire_time_str = account['expire_time']
                        if expire_time_str != "未知" and expire_time_str != "永久":
                            # 尝试多种日期格式
                            for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d"]:
                                try:
                                    expire_date = datetime.datetime.strptime(expire_time_str, fmt)
                                    break
                                except ValueError:
                                    continue
                            else:
                                # 如果所有格式都失败，设置一个默认状态
                                account['status'] = "日期格式错误"
                                continue
                                
                            # 比较过期时间和当前时间
                            now = datetime.datetime.now()
                            if expire_date < now:
                                account['status'] = "已过期"
                            else:
                                # 计算剩余天数
                                days_left = (expire_date - now).days
                                if days_left <= 7:
                                    account['status'] = f"即将过期({days_left}天)"
                                else:
                                    account['status'] = "正常"
                        elif expire_time_str == "永久":
                            account['status'] = "永久有效"
                        else:
                            account['status'] = "未知期限"
                    except Exception as e:
                        self.logger.error(f"检查账号过期时间出错: {e}")
                        account['status'] = "检查出错"
                else:
                    # 如果没有过期时间，默认为未知
                    account['status'] = "未知期限"
                
            # 保存更新后的账号信息
            self.save_accounts()
            
            # 更新当前账号
            self.get_current_account()
            
            # 发送账号列表更新信号
            self.account_list_updated.emit(self.accounts)
            self.logger.info(f"刷新了 {len(self.accounts)} 个账号的状态")
            return True
        except Exception as e:
            self.logger.error(f"刷新账号状态时出错: {e}")
            # 尽管出错，仍然发送更新信号
            self.account_list_updated.emit(self.accounts)
            return False 

    def logout(self, account_id=None):
        """退出登录
        
        Args:
            account_id: 要退出的账号ID，如果为None则退出当前账号
            
        Returns:
            bool: 是否成功退出
        """
        # 如果未指定ID，则使用当前账号ID
        if not account_id and self.current_account:
            account_id = self.current_account.get("id")
            
        if not account_id:
            self.logger.warning("退出登录失败：未指定账号ID且当前无登录账号")
            return False
            
        # 查找账号
        target_account = None
        for acc in self.accounts:
            if acc.get("id") == account_id:
                target_account = acc
                break
                
        if not target_account:
            self.logger.warning(f"退出登录失败：未找到ID为{account_id}的账号")
            return False
            
        # 更新账号状态
        target_account["status"] = "已退出登录"
        
        # 清除敏感信息
        if "access_token" in target_account:
            del target_account["access_token"]
        if "refresh_token" in target_account:
            del target_account["refresh_token"]
            
        # 如果退出的是当前账号，清除当前账号
        if self.current_account and self.current_account.get("id") == account_id:
            self.current_account = None
            
        # 保存更新
        self.save_accounts()
        self.logger.info(f"已成功退出账号: {target_account.get('email')}")
        
        return True 

    def save_cursor_auth_to_json(self, auth_data):
        """将Cursor原始授权数据直接保存到JSON文件
        
        Args:
            auth_data: Cursor授权数据字典
            
        Returns:
            bool: 是否成功保存
        """
        try:
            # 确保config目录存在
            config_dir = "config"
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
                
            # 保存到JSON文件
            cursor_auth_path = os.path.join(config_dir, "cursor_auth.json")
            with open(cursor_auth_path, "w", encoding="utf-8") as f:
                json.dump(auth_data, f, indent=4, ensure_ascii=False)
                
            self.logger.info(f"已成功保存Cursor原始授权数据到: {cursor_auth_path}")
            return True
        except Exception as e:
            self.logger.error(f"保存Cursor原始授权数据失败: {e}")
            return False
            
    def load_cursor_auth_from_json(self):
        """从JSON文件加载Cursor原始授权数据
        
        Returns:
            dict: Cursor授权数据字典
        """
        try:
            cursor_auth_path = os.path.join("config", "cursor_auth.json")
            if os.path.exists(cursor_auth_path):
                with open(cursor_auth_path, "r", encoding="utf-8") as f:
                    auth_data = json.load(f)
                    self.logger.info(f"已从JSON文件加载Cursor原始授权数据")
                    return auth_data
            return {}
        except Exception as e:
            self.logger.error(f"加载Cursor原始授权数据失败: {e}")
            return {} 