# =========== 天道龙魂·闪电战 (最终版) ===========
# 作者: Gemini
# 这是一个自包含的独立脚本，包含了所有运行所需的代码。
# 请通过您电脑的终端直接运行此文件。

import sys
import os
import pandas as pd
import numpy as np
import akshare as ak
import requests
import schedule
import time
from datetime import datetime, timedelta
from pathlib import Path
from scipy.signal import find_peaks

import json

# =================== 配置模块 ===================
BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = BASE_DIR / "storage" / "stock_data"
LOG_DIR = BASE_DIR / "storage" / "logs"
for directory in [DATA_DIR, LOG_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

MARKET_JUDGE_CONFIG = {
    'index_ma_days': 20,
    'volume_threshold': 800000000000,
    'zt_profit_threshold': 1.5,
    'chain_height_threshold': 4
}

TELEGRAM_CONFIG = {
    'bot_token': '7591133084:AAFHp2GbKKaylvPeD5YEVSsHYBWhTRLDZbw',
    'chat_id': '1729192077'
}

# =================== 通知模块 ===================
class TelegramNotifier:
    def __init__(self):
        self.bot_token = TELEGRAM_CONFIG['bot_token']
        self.chat_id = TELEGRAM_CONFIG['chat_id']
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    def send_message(self, message):
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            requests.post(url, json=payload, timeout=10)
        except Exception as e:
            print(f"[Notifier Error] {e}")

# =================== 数据更新模块 ===================
class DataUpdater:
    def __init__(self, max_retries=3, retry_delay=5):
        self.data_dir = DATA_DIR
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def _make_request(self, func, *args, **kwargs):
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    return None

    def get_stock_data(self, code):
        file_path = self.data_dir / f"{code}.csv"
        if file_path.exists():
            return pd.read_csv(file_path)
        else:
            self.update_single_stock_data(code)
            if file_path.exists():
                return pd.read_csv(file_path)
            else:
                return None

    def update_single_stock_data(self, code):
        df = self._make_request(ak.stock_zh_a_hist, symbol=code, period="daily", adjust="qfq")
        if df is not None and not df.empty:
            file_path = self.data_dir / f"{code}.csv"
            df.to_csv(file_path, index=False)

# =================== 鹿希武策略模块 ===================
def find_trendline_and_channel(price_series, lookback_period=120, trough_distance=10):
    subset = price_series.tail(lookback_period)
    troughs, _ = find_peaks(-subset, distance=trough_distance, prominence=0.5)
    if len(troughs) < 2: return None
    troughs_indices = subset.index[troughs]
    last_trough_idx, second_last_trough_idx = troughs_indices[-1], troughs_indices[-2]
    p1 = (second_last_trough_idx, price_series[second_last_trough_idx])
    p2 = (last_trough_idx, price_series[last_trough_idx])
    if p2[1] <= p1[1]: return None
    slope = (p2[1] - p1[1]) / (p2[0] - p1[0])
    if slope < 0.05: return None
    intercept = p2[1] - slope * p2[0]
    highs_between_troughs, _ = find_peaks(price_series[p1[0]:p2[0]])
    if len(highs_between_troughs) == 0: return None
    highest_point_idx = price_series.index[p1[0]:p2[0]][highs_between_troughs].max()
    highest_point_price = price_series[highest_point_idx]
    upper_intercept = highest_point_price - slope * highest_point_idx
    return {'slope': slope, 'intercept': intercept, 'upper_intercept': upper_intercept}

class LuXiWuStrategy:
    def __init__(self, params={}):
        self.lookback_period = params.get('lookback_period', 120)
        self.trough_distance = params.get('trough_distance', 10)

    def check_entry(self, stock_data, date):
        hist_data = stock_data[stock_data['日期'] <= date.strftime('%Y-%m-%d')].copy()
        if len(hist_data) < 60: return False
        today = hist_data.iloc[-1]
        today_index = hist_data.index[-1]
        trend_params = find_trendline_and_channel(hist_data['收盘'], self.lookback_period, self.trough_distance)
        if not trend_params: return False
        trendline_price_today = trend_params['slope'] * today_index + trend_params['intercept']
        is_near_trendline = (today['最低'] <= trendline_price_today * 1.02) and (today['收盘'] > trendline_price_today * 0.98)
        if not is_near_trendline: return False
        hist_data['ma10'] = hist_data['收盘'].rolling(10).mean()
        if len(hist_data) < 10 or pd.isna(hist_data.iloc[-1]['ma10']): return False
        is_above_ma10 = today['收盘'] > hist_data.iloc[-1]['ma10']
        if not is_above_ma10: return False
        hist_data['vol_ma10'] = hist_data['成交量'].rolling(10).mean()
        if pd.isna(hist_data.iloc[-1]['vol_ma10']): return False
        is_volume_high = today['成交量'] > (hist_data.iloc[-1]['vol_ma10'] * 1.2)
        if not is_volume_high: return False
        is_positive_candle = today['收盘'] > today['开盘']
        if not is_positive_candle: return False
        return True

    def check_exit(self, stock_data, date, position_details):
        hist_data = stock_data[stock_data['日期'] <= date.strftime('%Y-%m-%d')]
        if len(hist_data) < 2: return None, 0
        today = hist_data.iloc[-1]
        today_index = hist_data.index[-1]
        trend_params = position_details.get('trend_params')
        if not trend_params: return None, 0
        lower_rail_price = trend_params['slope'] * today_index + trend_params['intercept']
        stop_loss_price = lower_rail_price * 0.98
        if today['收盘'] < stop_loss_price: return 'stop_loss', today['收盘']
        upper_rail_price = trend_params['slope'] * today_index + trend_params['upper_intercept']
        if today['最高'] >= upper_rail_price: return 'take_profit', upper_rail_price
        return None, 0

# =================== 天时裁决模块 ===================
class MarketJudge:
    def __init__(self, data_updater):
        self.config = MARKET_JUDGE_CONFIG
        self.data_updater = data_updater

    def get_market_status_for_date(self, date, index_data):
        score = 0
        hist_index_data = index_data[index_data['日期'] <= date.strftime('%Y-%m-%d')]
        if self._check_index_trend_hist(hist_index_data): score += 1
        if self._check_market_volume_hist(hist_index_data): score += 1
        if self._check_chain_height_hist(date): score += 1
        if self._check_north_money_hist(date): score += 1
        if score >= 3: return "进攻模式", score
        elif score >= 2: return "防守模式", score
        else: return "空仓模式", score

    def _check_index_trend_hist(self, hist_index_data):
        if len(hist_index_data) < self.config['index_ma_days']: return False
        current_price = hist_index_data.iloc[-1]['收盘']
        ma = hist_index_data['收盘'].rolling(self.config['index_ma_days']).mean().iloc[-1]
        return current_price > ma

    def _check_market_volume_hist(self, hist_index_data):
        today_volume = hist_index_data.iloc[-1]['成交额']
        return today_volume > self.config['volume_threshold']

    def _check_chain_height_hist(self, date):
        try:
            zt_pool = ak.stock_zt_pool_em(date=date.strftime("%Y%m%d"))
            if zt_pool.empty: return False
            return zt_pool['lbc'].max() >= self.config['chain_height_threshold']
        except Exception: return False

    def _check_north_money_hist(self, date):
        try:
            north_flow = ak.stock_hsgt_north_net_flow_in_em(symbol="北向资金")
            flow_on_date = north_flow[north_flow['日期'] == date.strftime('%Y-%m-%d')]
            if flow_on_date.empty: return False
            return flow_on_date.iloc[0]['净流入'] > 0
        except Exception: return False

# =================== 总指挥官模块 ===================
class MainCommander:
    def __init__(self):
        self.data_updater = DataUpdater()
        self.market_judge = MarketJudge(self.data_updater)
        self.strategy = LuXiWuStrategy(params={'trough_distance': 10})
        self.notifier = TelegramNotifier()
        self.stock_pool = [] # 将在盘前动态获取
        self.live_portfolio = {}
        self.market_status = "空仓模式"
        self.last_signals = [] # 用于存储最近的信号

    def write_status_to_json(self):
        status = {
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'market_status': self.market_status,
            'live_portfolio': self.live_portfolio,
            'last_signals': self.last_signals
        }
        # 将status对象序列化为JSON格式的字符串
        # 注意：直接序列化datetime对象会出错，所以所有时间都已转为字符串
        def default_serializer(o):
            if isinstance(o, (datetime, pd.Timestamp)):
                return o.isoformat()
            raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")

        with open(BASE_DIR / 'status.json', 'w', encoding='utf-8') as f:
            json.dump(status, f, ensure_ascii=False, indent=4, default=default_serializer)


    def run_live_operation(self):
        print("--- 天道龙魂·闪电战 信号系统已激活 ---")
        self.pre_market_preparation()
        schedule.every().day.at("09:00").do(self.pre_market_preparation)
        for minute in [":00", ":15", ":30", ":45"]:
            schedule.every().hour.at(minute).do(self.run_signal_check)
        schedule.every(1).hour.do(self.log_heartbeat)
        while True:
            schedule.run_pending()
            time.sleep(1)

    def pre_market_preparation(self):
        print(f"\n[{datetime.now()}] 正在执行盘前任务...")
        index_data = self.data_updater.get_stock_data("000001")
        if index_data is None: return
        index_data['日期'] = pd.to_datetime(index_data['日期'])
        status, score = self.market_judge.get_market_status_for_date(datetime.now(), index_data)
        if score >= 1: self.market_status = "进攻模式"
        else: self.market_status = "防守/空仓模式"
        
        # 获取最新的A股全市场列表，并自动排除ST股票
        try:
            all_stocks = ak.stock_info_a_code_name()
            # 剔除ST和*ST股票
            non_st_stocks = all_stocks[~all_stocks['name'].str.contains('ST')]
            self.stock_pool = non_st_stocks['code'].tolist()
            print(f"Successfully fetched {len(self.stock_pool)} stocks from the entire A-share market (ST stocks excluded).")
        except Exception as e:
            print(f"[Error] Failed to fetch full market components: {e}")
            self.stock_pool = [] # 如果获取失败，则股票池为空

        message = f"🔔 **天道龙魂-盘前计划**\n\n**日期**: {datetime.now().strftime('%Y-%m-%d')}\n**天时判断**: {self.market_status} (市场分数: {score})\n**扫描范围**: 全市场（已排除ST, 共{len(self.stock_pool)}只）"
        self.notifier.send_message(message)
        print(f"盘前检查完成. 今日状态: {self.market_status}")
        print(f"盘前检查完成. 今日状态: {self.market_status}")

    def run_signal_check(self):
        now = datetime.now()
        if not (now.time() >= datetime.strptime("09:30", "%H:%M").time() and now.time() <= datetime.strptime("15:00", "%H:%M").time()): return
        print(f"\n[{now}] 正在检查信号...")
        for code in list(self.live_portfolio.keys()):
            position_details = self.live_portfolio[code]
            stock_data = self.data_updater.get_stock_data(code)
            if stock_data is None: continue
            stock_data['日期'] = pd.to_datetime(stock_data['日期'])
            exit_type, exit_price = self.strategy.check_exit(stock_data, now, position_details)
            if exit_type:
                message = f"🚨 **卖出信号** 🚨\n\n**股票**: {code}\n**信号**: {exit_type.upper()}\n**价格**: {exit_price:.2f}"
                self.notifier.send_message(message)
                del self.live_portfolio[code]
        if self.market_status == "进攻模式" and len(self.live_portfolio) < 3:
            # 从沪深300中筛选出动量最高的候选股
            candidate_stocks = self.get_momentum_candidates()
            print(f"Offensive mode: Found {len(candidate_stocks)} momentum candidates.")

            for code in candidate_stocks:
                if code in self.live_portfolio: continue
                stock_data = self.data_updater.get_stock_data(code)
                if stock_data is None: continue
                stock_data['日期'] = pd.to_datetime(stock_data['日期'])
                if self.strategy.check_entry(stock_data, now):
                    hist_data = stock_data[stock_data['日期'] <= now.strftime('%Y-%m-%d')]
                    trend_params = find_trendline_and_channel(hist_data['收盘'], trough_distance=self.strategy.trough_distance)
                    if trend_params:
                        price = hist_data.iloc[-1]['收盘']
                        message = f"🎯 **买入信号** 🎯\n\n**股票**: {code}\n**策略**: 鹿希武趋势策略\n**价格**: {price:.2f}"
                        self.notifier.send_message(message)
                        self.live_portfolio[code] = {'buy_date': now, 'buy_price': price, 'trend_params': trend_params}
                        self.last_signals.append(message) # 记录信号
                        if len(self.live_portfolio) >= 3: break
        self.write_status_to_json() # 每次检查后都写入状态文件
    
    def get_momentum_candidates(self):
        """获取实时行情，并选出涨幅最高的前20名作为候选"""
        try:
            realtime_data = self.data_updater._make_request(ak.stock_zh_a_spot_em)
            if realtime_data is None or realtime_data.empty: return []
            
            # 只在我们的股票池（沪深300）中进行筛选
            candidates = realtime_data[realtime_data['代码'].isin(self.stock_pool)]
            
            # 按涨跌幅排序，选出前20名
            top_20 = candidates.sort_values(by='涨跌幅', ascending=False).head(20)
            return top_20['代码'].tolist()
        except Exception as e:
            print(f"[Error] Failed to get momentum candidates: {e}")
            return []
    def log_heartbeat(self):
        print(f"❤️ {datetime.now()}: 系统存活，心跳正常。")

# =================== 主程序入口 ===================
if __name__ == "__main__":
    commander = MainCommander()
    commander.run_live_operation()
