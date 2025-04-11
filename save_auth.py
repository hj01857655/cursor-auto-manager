#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
保存Cursor授权数据到JSON文件
"""

import json
import os
import sys
from core.account_manager import AccountManager

def main():
    """主函数"""
    # 要保存的授权数据
    auth_data = {
        "cursorAuth/cachedEmail": "hj6395759@gmail.com",
        "cursorAuth/cachedSignUpType": "Google",
        "cursorAuth/refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJnb29nbGUtb2F1dGgyfHVzZXJfMDFKUkhaWkpFSllETjMzUFlFWE1aNFE0ODIiLCJ0aW1lIjoiMTc0NDM2MTIyNiIsInJhbmRvbW5lc3MiOiJiMzg4OTg0Yy0wNTAyLTQ4MmIiLCJleHAiOjE3NDk1NDUyMjYsImlzcyI6Imh0dHBzOi8vYXV0aGVudGljYXRpb24uY3Vyc29yLnNoIiwic2NvcGUiOiJvcGVuaWQgcHJvZmlsZSBlbWFpbCBvZmZsaW5lX2FjY2VzcyIsImF1ZCI6Imh0dHBzOi8vY3Vyc29yLmNvbSJ9.YfPwTlO82MCUr1idn0S-E_voUeWEIxABjGrPx72eaxw",
        "cursorAuth/accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJnb29nbGUtb2F1dGgyfHVzZXJfMDFKUkhaWkpFSllETjMzUFlFWE1aNFE0ODIiLCJ0aW1lIjoiMTc0NDM2MTIyNiIsInJhbmRvbW5lc3MiOiJiMzg4OTg0Yy0wNTAyLTQ4MmIiLCJleHAiOjE3NDk1NDUyMjYsImlzcyI6Imh0dHBzOi8vYXV0aGVudGljYXRpb24uY3Vyc29yLnNoIiwic2NvcGUiOiJvcGVuaWQgcHJvZmlsZSBlbWFpbCBvZmZsaW5lX2FjY2VzcyIsImF1ZCI6Imh0dHBzOi8vY3Vyc29yLmNvbSJ9.YfPwTlO82MCUr1idn0S-E_voUeWEIxABjGrPx72eaxw",
        "cursorAuth/stripeMembershipType": "free_trial"
    }
    
    # 创建账号管理器
    manager = AccountManager()
    
    # 保存授权数据到JSON文件
    if manager.save_cursor_auth_to_json(auth_data):
        print("✅ 成功保存授权数据到 config/cursor_auth.json")
        
        # 从JWT令牌解析过期时间
        try:
            import base64
            import json
            import datetime
            
            # 优先使用刷新令牌
            token = auth_data.get("cursorAuth/refreshToken") or auth_data.get("cursorAuth/accessToken")
            
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
                print(f"🕒 令牌过期时间: {expire_date}")
                
                # 计算剩余天数
                days_left = (expire_date - datetime.datetime.now()).days
                if days_left > 0:
                    print(f"⏱️ 剩余有效期: {days_left}天")
                else:
                    print("⚠️ 令牌已过期")
        except Exception as e:
            print(f"⚠️ 解析令牌过期时间失败: {e}")
    else:
        print("❌ 保存授权数据失败")
        
    # 解析已保存的数据（测试读取功能）
    loaded_data = manager.load_cursor_auth_from_json()
    if loaded_data:
        print(f"✅ 成功从文件读取授权数据 ({len(loaded_data)}个键)")
    else:
        print("❌ 读取授权数据失败")
        
if __name__ == "__main__":
    main() 