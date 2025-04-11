import sqlite3
import os
import logging
import datetime
import uuid
import json
from typing import List, Dict, Any, Optional, Tuple

class AccountDbManager:
    """账号数据库管理器，用于管理账号数据的存储和检索"""
    
    def __init__(self, db_path="db/accounts.db"):
        """初始化账号数据库管理器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # 确保数据库目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # 初始化数据库
        self._init_database()
        
    def _init_database(self):
        """初始化数据库，创建必要的表"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 创建账号表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE,
                password TEXT,
                auth_source TEXT,
                membership TEXT,
                status TEXT,
                expire_time TEXT,
                refresh_token TEXT,
                access_token TEXT,
                quota TEXT,
                created_at TEXT,
                last_login TEXT,
                extra_data TEXT
            )
            ''')
            
            # 创建当前账号表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            ''')
            
            # 创建阈值设置表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS thresholds (
                key TEXT PRIMARY KEY,
                value INTEGER
            )
            ''')
            
            conn.commit()
            conn.close()
            self.logger.info("数据库初始化成功")
        except Exception as e:
            self.logger.error(f"初始化数据库失败: {str(e)}")
            
    def _get_connection(self):
        """获取数据库连接
        
        Returns:
            sqlite3.Connection: 数据库连接
        """
        return sqlite3.connect(self.db_path)
            
    def get_all_accounts(self) -> List[Dict[str, Any]]:
        """获取所有账号
        
        Returns:
            List[Dict[str, Any]]: 账号列表
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM accounts')
            accounts = []
            for row in cursor.fetchall():
                account = {
                    'id': row[0],
                    'email': row[1],
                    'password': row[2],
                    'auth_source': row[3],
                    'membership': row[4],
                    'status': row[5],
                    'expire_time': row[6],
                    'refresh_token': row[7],
                    'access_token': row[8],
                    'quota': row[9],
                    'created_at': row[10],
                    'last_login': row[11]
                }
                
                # 解析extra_data (JSON格式)
                if row[12]:
                    try:
                        extra_data = json.loads(row[12])
                        account.update(extra_data)
                    except:
                        pass
                        
                accounts.append(account)
                
            conn.close()
            return accounts
        except Exception as e:
            self.logger.error(f"获取所有账号失败: {str(e)}")
            return []
            
    def get_account_by_id(self, account_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取账号
        
        Args:
            account_id: 账号ID
            
        Returns:
            Optional[Dict[str, Any]]: 账号信息，不存在返回None
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM accounts WHERE id = ?', (account_id,))
            row = cursor.fetchone()
            
            if not row:
                conn.close()
                return None
                
            account = {
                'id': row[0],
                'email': row[1],
                'password': row[2],
                'auth_source': row[3],
                'membership': row[4],
                'status': row[5],
                'expire_time': row[6],
                'refresh_token': row[7],
                'access_token': row[8],
                'quota': row[9],
                'created_at': row[10],
                'last_login': row[11]
            }
            
            # 解析extra_data (JSON格式)
            if row[12]:
                try:
                    extra_data = json.loads(row[12])
                    account.update(extra_data)
                except:
                    pass
                    
            conn.close()
            return account
        except Exception as e:
            self.logger.error(f"根据ID获取账号失败: {str(e)}")
            return None
            
    def get_account_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """根据邮箱获取账号
        
        Args:
            email: 邮箱
            
        Returns:
            Optional[Dict[str, Any]]: 账号信息，不存在返回None
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM accounts WHERE email = ?', (email,))
            row = cursor.fetchone()
            
            if not row:
                conn.close()
                return None
                
            account = {
                'id': row[0],
                'email': row[1],
                'password': row[2],
                'auth_source': row[3],
                'membership': row[4],
                'status': row[5],
                'expire_time': row[6],
                'refresh_token': row[7],
                'access_token': row[8],
                'quota': row[9],
                'created_at': row[10],
                'last_login': row[11]
            }
            
            # 解析extra_data (JSON格式)
            if row[12]:
                try:
                    extra_data = json.loads(row[12])
                    account.update(extra_data)
                except:
                    pass
                    
            conn.close()
            return account
        except Exception as e:
            self.logger.error(f"根据邮箱获取账号失败: {str(e)}")
            return None
            
    def add_account(self, account: Dict[str, Any]) -> bool:
        """添加或更新账号
        
        Args:
            account: 账号信息
            
        Returns:
            bool: 是否成功
        """
        try:
            # 提取基本字段
            account_id = account.get('id') or str(uuid.uuid4())
            email = account.get('email')
            password = account.get('password', '')
            auth_source = account.get('auth_source', '')
            membership = account.get('membership', '')
            status = account.get('status', '正常')
            expire_time = account.get('expire_time', '')
            refresh_token = account.get('refresh_token', '')
            access_token = account.get('access_token', '')
            quota = account.get('quota', '')
            created_at = account.get('created_at') or datetime.datetime.now().isoformat()
            last_login = account.get('last_login') or datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 其他字段存储为JSON
            extra_fields = {k: v for k, v in account.items() if k not in [
                'id', 'email', 'password', 'auth_source', 'membership', 'status', 
                'expire_time', 'refresh_token', 'access_token', 'quota', 
                'created_at', 'last_login'
            ]}
            extra_data = json.dumps(extra_fields) if extra_fields else None
            
            # 检查账号是否已存在
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT id FROM accounts WHERE id = ?', (account_id,))
            existing_id = cursor.fetchone()
            
            if not existing_id and email:
                cursor.execute('SELECT id FROM accounts WHERE email = ?', (email,))
                existing_email = cursor.fetchone()
                if existing_email:
                    account_id = existing_email[0]
                    existing_id = existing_email
            
            # 插入或更新
            if existing_id:
                # 更新
                cursor.execute('''
                UPDATE accounts SET 
                    email = ?, password = ?, auth_source = ?, membership = ?,
                    status = ?, expire_time = ?, refresh_token = ?, access_token = ?,
                    quota = ?, last_login = ?, extra_data = ?
                WHERE id = ?
                ''', (
                    email, password, auth_source, membership, status, expire_time,
                    refresh_token, access_token, quota, last_login, extra_data,
                    account_id
                ))
            else:
                # 插入
                cursor.execute('''
                INSERT INTO accounts (
                    id, email, password, auth_source, membership, status,
                    expire_time, refresh_token, access_token, quota,
                    created_at, last_login, extra_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    account_id, email, password, auth_source, membership, status,
                    expire_time, refresh_token, access_token, quota,
                    created_at, last_login, extra_data
                ))
                
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            self.logger.error(f"添加账号失败: {str(e)}")
            return False
            
    def remove_account(self, account_id: str) -> bool:
        """删除账号
        
        Args:
            account_id: 账号ID
            
        Returns:
            bool: 是否成功
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 检查是否是当前账号
            cursor.execute('SELECT value FROM settings WHERE key = "current_account_id"')
            current_id = cursor.fetchone()
            
            # 删除账号
            cursor.execute('DELETE FROM accounts WHERE id = ?', (account_id,))
            
            # 如果删除的是当前账号，清除当前账号设置
            if current_id and current_id[0] == account_id:
                cursor.execute('DELETE FROM settings WHERE key = "current_account_id"')
                
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            self.logger.error(f"删除账号失败: {str(e)}")
            return False
            
    def set_current_account(self, account_id: str) -> bool:
        """设置当前账号
        
        Args:
            account_id: 账号ID
            
        Returns:
            bool: 是否成功
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 检查账号是否存在
            cursor.execute('SELECT id FROM accounts WHERE id = ?', (account_id,))
            if not cursor.fetchone():
                conn.close()
                return False
                
            # 设置当前账号
            cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
                           ('current_account_id', account_id))
            
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            self.logger.error(f"设置当前账号失败: {str(e)}")
            return False
            
    def get_current_account(self) -> Optional[Dict[str, Any]]:
        """获取当前账号
        
        Returns:
            Optional[Dict[str, Any]]: 当前账号信息，不存在返回None
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 获取当前账号ID
            cursor.execute('SELECT value FROM settings WHERE key = "current_account_id"')
            row = cursor.fetchone()
            
            if not row:
                # 如果没有当前账号，尝试获取第一个账号
                cursor.execute('SELECT id FROM accounts LIMIT 1')
                id_row = cursor.fetchone()
                if id_row:
                    account_id = id_row[0]
                    # 设置为当前账号
                    self.set_current_account(account_id)
                    account = self.get_account_by_id(account_id)
                    conn.close()
                    return account
                    
                conn.close()
                return None
                
            account_id = row[0]
            conn.close()
            
            # 获取账号信息
            return self.get_account_by_id(account_id)
        except Exception as e:
            self.logger.error(f"获取当前账号失败: {str(e)}")
            return None
            
    def update_thresholds(self, thresholds: Dict[str, int]) -> bool:
        """更新阈值设置
        
        Args:
            thresholds: 阈值设置
            
        Returns:
            bool: 是否成功
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            for key, value in thresholds.items():
                cursor.execute('INSERT OR REPLACE INTO thresholds (key, value) VALUES (?, ?)',
                               (key, value))
                
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            self.logger.error(f"更新阈值设置失败: {str(e)}")
            return False
            
    def get_thresholds(self) -> Dict[str, int]:
        """获取阈值设置
        
        Returns:
            Dict[str, int]: 阈值设置
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT key, value FROM thresholds')
            thresholds = {}
            for row in cursor.fetchall():
                thresholds[row[0]] = row[1]
                
            conn.close()
            
            # 默认值
            if "max_requests_per_minute" not in thresholds:
                thresholds["max_requests_per_minute"] = 60
            if "max_concurrent_sessions" not in thresholds:
                thresholds["max_concurrent_sessions"] = 3
            if "session_timeout_minutes" not in thresholds:
                thresholds["session_timeout_minutes"] = 30
                
            return thresholds
        except Exception as e:
            self.logger.error(f"获取阈值设置失败: {str(e)}")
            return {
                "max_requests_per_minute": 60,
                "max_concurrent_sessions": 3,
                "session_timeout_minutes": 30
            }
            
    def refresh_account_status(self) -> bool:
        """刷新所有账号状态
        
        检查所有账号的状态并更新，主要是检查授权是否有效、过期时间等。
        只刷新账号状态，不会尝试登录。
        
        Returns:
            bool: 是否成功刷新账号状态
        """
        try:
            accounts = self.get_all_accounts()
            for account in accounts:
                # 检查过期时间（如果有）
                if 'expire_time' in account:
                    expire_time_str = account['expire_time']
                    if expire_time_str != "未知" and expire_time_str != "永久":
                        # 尝试多种日期格式
                        expire_date = None
                        for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d"]:
                            try:
                                expire_date = datetime.datetime.strptime(expire_time_str, fmt)
                                break
                            except ValueError:
                                continue
                                
                        if expire_date:
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
                        else:
                            account['status'] = "日期格式错误"
                    elif expire_time_str == "永久":
                        account['status'] = "永久有效"
                    else:
                        account['status'] = "未知期限"
                else:
                    # 如果没有过期时间，默认为未知
                    account['status'] = "未知期限"
                    
                # 更新账号
                self.add_account(account)
                
            return True
        except Exception as e:
            self.logger.error(f"刷新账号状态失败: {str(e)}")
            return False
            
    def import_accounts_from_json(self, accounts_json: str) -> Tuple[int, int]:
        """从JSON导入账号
        
        Args:
            accounts_json: 账号JSON字符串
            
        Returns:
            Tuple[int, int]: (成功导入数, 失败数)
        """
        try:
            accounts = json.loads(accounts_json)
            if not isinstance(accounts, list):
                accounts = [accounts]
                
            success_count = 0
            fail_count = 0
            
            for account in accounts:
                if self.add_account(account):
                    success_count += 1
                else:
                    fail_count += 1
                    
            return success_count, fail_count
        except Exception as e:
            self.logger.error(f"从JSON导入账号失败: {str(e)}")
            return 0, 1
            
    def export_accounts_to_json(self) -> str:
        """导出账号到JSON字符串
        
        Returns:
            str: 账号JSON字符串
        """
        try:
            accounts = self.get_all_accounts()
            return json.dumps(accounts, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"导出账号到JSON失败: {str(e)}")
            return "[]" 