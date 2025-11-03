import requests
import json
from config.telegram_config import TELEGRAM_CONFIG

class TelegramNotifier:
    def __init__(self):
        self.bot_token = TELEGRAM_CONFIG['bot_token']
        self.chat_id = TELEGRAM_CONFIG['chat_id']
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    def send_message(self, message):
        """发送Telegram消息"""
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, json=payload)
            return response.status_code == 200
        except Exception as e:
            print(f"发送消息失败: {e}")
            return False
    
    def send_alert(self, title, content):
        """发送警报消息"""
        message = f"🚨 <b>{title}</b>\n{content}"
        return self.send_message(message)