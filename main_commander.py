#!/usr/bin/env python3
import schedule
import time
from datetime import datetime
from core.market_judge import MarketJudge
from core.prophet_scanner import ProphetScanner
from core.data_updater import DataUpdater
from utils.notifier import TelegramNotifier

class MainCommander:
    def __init__(self):
        self.judge = MarketJudge()
        self.prophet = ProphetScanner()
        self.data_updater = DataUpdater()
        self.notifier = TelegramNotifier()
        self.market_status = "未知"
        self.max_position = "0%"
        
    def run_daily_operation(self):
        """每日作战流程"""
        print(f"{datetime.now()} - 开始每日作战流程")
        
        # 阶段一：盘前准备 (8:30)
        self.pre_market_preparation()
        
        # 阶段二：开盘作战 (9:15-10:00)
        schedule.every().day.at("09:15").do(self.open_battle)
        
        # 阶段三：盘中监控 (持续运行)
        schedule.every(1).minutes.do(self.intraday_monitoring)
        
        # 保持运行
        while True:
            schedule.run_pending()
            time.sleep(1)
    
    def pre_market_preparation(self):
        """盘前准备"""
        print("执行盘前准备...")
        
        # 1. 更新数据
        self.data_updater.update_all_stock_data()
        
        # 2. 天时裁决
        self.market_status, self.max_position = self.judge.get_market_status()
        
        # 3. 如果允许出战，寻找目标
        watchlist = []
        if self.market_status != "空仓模式":
            watchlist = self.prophet.morning_news_scan()
        
        # 4. 推送作战计划
        message = f"""
🎯 今日作战计划
⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}
📊 市场状态: {self.market_status}
💰 最大仓位: {self.max_position}
🎯 观察目标: {', '.join(watchlist) if watchlist else '暂无'}
        """
        self.notifier.send_message(message)
        
        print(f"盘前准备完成: {self.market_status}, 最大仓位: {self.max_position}")
    
    def open_battle(self):
        """开盘作战"""
        if self.market_status == "空仓模式":
            print("空仓模式，跳过开盘作战")
            return
            
        print("执行开盘作战...")
        
        # 这里需要实现具体的攻击逻辑
        # 暂时用打印代替
        print("开盘作战逻辑待实现...")
    
    def intraday_monitoring(self):
        """盘中监控"""
        if datetime.now().hour < 9 or datetime.now().hour >= 15:
            return
            
        # 简化的监控逻辑
        print(f"{datetime.now()} - 盘中监控执行中...")

if __name__ == "__main__":
    commander = MainCommander()
    commander.run_daily_operation()