import schedule
import time
import pandas as pd
from datetime import datetime, timedelta
from .market_judge import MarketJudge
from .strategy_luxiwu import LuXiWuStrategy, find_trendline_and_channel
from .data_updater import DataUpdater
from utils.notifier import TelegramNotifier

class MainCommander:
    def __init__(self):
        self.data_updater = DataUpdater()
        self.market_judge = MarketJudge(self.data_updater)
        self.strategy = LuXiWuStrategy(params={'trough_distance': 10})
        self.notifier = TelegramNotifier()
        self.stock_pool = ['600519', '601318', '600036', '000651', '000858', '002475']
        self.live_portfolio = {}
        self.market_status = "空仓模式"

    def run_live_operation(self):
        print("--- Live Signal System Activated ---")
        print(f"System started at {datetime.now()}\n")

        schedule.every().day.at("09:00").do(self.pre_market_preparation)
        for minute in [":00", ":15", ":30", ":45"]:
            schedule.every().hour.at(minute).do(self.run_signal_check)
        schedule.every(1).hour.do(self.log_heartbeat)

        self.pre_market_preparation()

        while True:
            schedule.run_pending()
            time.sleep(1)

    def pre_market_preparation(self):
        print(f"\n[{datetime.now()}] Running pre-market preparation...")
        index_data = self.data_updater.get_stock_data("000001")
        if index_data is None: 
            print("Could not get index data. Market status check failed.")
            return
        index_data['日期'] = pd.to_datetime(index_data['日期'])
        
        status, _, score = self.market_judge.get_market_status_for_date(datetime.now(), index_data)
        if score >= 1: # Using the optimal threshold
            self.market_status = "进攻模式"
        else:
            self.market_status = "防守/空仓模式"
        
        message = f"🔔 **天道龙魂-盘前计划**\n\n**日期**: {datetime.now().strftime('%Y-%m-%d')}\n**天时判断**: {self.market_status} (市场分数: {score})\n\n*系统将在交易时段内根据此状态执行操作。*"
        self.notifier.send_message(message)
        print(f"Pre-market check complete. Today's status: {self.market_status}")

    def run_signal_check(self):
        now = datetime.now()
        if not (now.time() >= datetime.strptime("09:30", "%H:%M").time() and now.time() <= datetime.strptime("15:00", "%H:%M").time()):
            return
        
        print(f"\n[{now}] Running signal check...")

        for code in list(self.live_portfolio.keys()):
            position_details = self.live_portfolio[code]
            stock_data = self.data_updater.get_stock_data(code)
            if stock_data is None: continue
            stock_data['日期'] = pd.to_datetime(stock_data['日期'])

            exit_type, exit_price = self.strategy.check_exit(stock_data, now, position_details)
            if exit_type:
                message = f"🚨 **卖出信号** 🚨\n\n**股票**: {code}\n**信号**: {exit_type.upper()}\n**价格**: {exit_price:.2f}\n**时间**: {now.strftime('%Y-%m-%d %H:%M:%S')}"
                self.notifier.send_message(message)
                del self.live_portfolio[code]

        if self.market_status == "进攻模式" and len(self.live_portfolio) < 3:
            print("Market is in OFFENSIVE MODE. Scanning for buy signals...")
            for code in self.stock_pool:
                if code in self.live_portfolio: continue
                
                stock_data = self.data_updater.get_stock_data(code)
                if stock_data is None: continue
                stock_data['日期'] = pd.to_datetime(stock_data['日期'])

                if self.strategy.check_entry(stock_data, now):
                    hist_data = stock_data[stock_data['日期'] <= now.strftime('%Y-%m-%d')]
                    trend_params = find_trendline_and_channel(hist_data['收盘'], trough_distance=self.strategy.trough_distance)
                    if trend_params:
                        price = hist_data.iloc[-1]['收盘']
                        message = f"🎯 **买入信号** 🎯\n\n**股票**: {code}\n**策略**: 鹿希武趋势策略\n**价格**: {price:.2f}\n**时间**: {now.strftime('%Y-%m-%d %H:%M:%S')}"
                        self.notifier.send_message(message)
                        self.live_portfolio[code] = {'buy_date': now, 'buy_price': price, 'trend_params': trend_params}
                        if len(self.live_portfolio) >= 3: break
        else:
            print("Market is in DEFENSIVE/HOLD MODE. No buy signals will be generated.")

    def log_heartbeat(self):
        print(f"❤️ Heartbeat: {datetime.now()} - System is alive and running.")
