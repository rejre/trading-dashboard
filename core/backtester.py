import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from .data_updater import DataUpdater
from .market_judge import MarketJudge
from .class_strategy_template import TemplateStrategy
from .strategy_luxiwu import find_trendline_and_channel

class Portfolio:
    """模拟投资组合，负责管理资金、持仓、交易和费用"""
    def __init__(self, data_updater, initial_capital=1000000, commission=0.0003):
        self.data_updater = data_updater
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.commission = commission
        self.positions = {}
        self.history = [] # 记录每日净值
        self.trades = []  # 记录已完成的交易

    def get_total_value(self, current_date):
        total_value = self.cash
        for code, details in self.positions.items():
            stock_data = self.data_updater.get_stock_data(code)
            if stock_data is not None:
                price_on_date = stock_data[stock_data['日期'] <= current_date.strftime('%Y-%m-%d')]
                if not price_on_date.empty:
                    current_price = price_on_date.iloc[-1]['收盘']
                    total_value += details['shares'] * current_price
        return total_value

    def buy(self, code, date, amount, trend_params):
        stock_data = self.data_updater.get_stock_data(code)
        if stock_data is None: return
        price_on_date = stock_data[stock_data['日期'] <= date.strftime('%Y-%m-%d')]
        if price_on_date.empty: return
        
        price = price_on_date.iloc[-1]['收盘']
        shares_to_buy = amount // price
        cost = shares_to_buy * price
        fee = cost * self.commission

        if self.cash >= cost + fee and shares_to_buy > 0:
            self.cash -= (cost + fee)
            self.positions[code] = {
                'shares': self.positions.get(code, {'shares': 0})['shares'] + shares_to_buy,
                'buy_date': date,
                'buy_price': price,
                'trend_params': trend_params
            }
            # print(f"{date.date()}: Bought {shares_to_buy} shares of {code} at {price:.2f}")

    def sell(self, code, date, price, reason):
        if code not in self.positions: return

        position = self.positions[code]
        shares_to_sell = position['shares']
        sale_value = shares_to_sell * price
        fee = sale_value * self.commission
        self.cash += (sale_value - fee)
        
        # 记录这笔已完成的交易
        profit = (price - position['buy_price']) * shares_to_sell - fee * 2
        self.trades.append({
            'code': code,
            'buy_date': position['buy_date'],
            'sell_date': date,
            'buy_price': position['buy_price'],
            'sell_price': price,
            'profit': profit,
            'reason': reason
        })
        del self.positions[code]
        # print(f"{date.date()}: Sold {shares_to_sell} shares of {code} at {price:.2f} (Reason: {reason})")

    def record_value(self, date):
        value = self.get_total_value(date)
        self.history.append({'date': date, 'value': value})

class Backtester:
    def __init__(self, start_date, end_date, initial_capital=1000000, benchmark_code='000001', strategy_params={}, force_offensive_mode=False, market_judge_score_threshold=3):
        self.start_date = start_date
        self.end_date = end_date
        self.benchmark_code = benchmark_code
        self.force_offensive_mode = force_offensive_mode
        self.market_judge_score_threshold = market_judge_score_threshold
        self.data_updater = DataUpdater()
        self.market_judge = MarketJudge()
        self.portfolio = Portfolio(self.data_updater, initial_capital)
        self.strategy = TemplateStrategy(strategy_params)
        self.stock_pool = ['600519', '601318', '600036', '000651', '000858', '002475']

    def run(self):
        """执行回测"""
        print(f"Running Hybrid (TianDao+LuXiWu) Strategy backtest from {self.start_date.date()} to {self.end_date.date()}...")
        
        index_data = self.data_updater.get_stock_data(self.benchmark_code)
        if index_data is None: 
            print("Benchmark data not found, aborting backtest.")
            return

        index_data['日期'] = pd.to_datetime(index_data['日期'])
        trading_days = index_data[(index_data['日期'] >= self.start_date) & (index_data['日期'] <= self.end_date)]['日期']

        for today in trading_days:
            # --- 1. 检查现有持仓的卖出条件 ---
            for code in list(self.portfolio.positions.keys()):
                position_details = self.portfolio.positions[code]
                stock_data = self.data_updater.get_stock_data(code)
                if stock_data is None: continue
                stock_data['日期'] = pd.to_datetime(stock_data['日期'])

                exit_type, exit_price = self.strategy.check_exit(stock_data, today, position_details)
                if exit_type:
                    self.portfolio.sell(code, today, exit_price, exit_type)

            # --- 2. 获取当日天时，决定是否进攻 ---
            market_status = "进攻模式"
            score = 5 # 强制进攻时给予满分
            if not self.force_offensive_mode:
                market_status, _, score = self.market_judge.get_market_status()
                # print(f"{today.date()}: Market Status is '{market_status}' (Score: {score})")

            if score >= self.market_judge_score_threshold and len(self.portfolio.positions) < 3:
                # --- 3. 天命筛选（回测中使用动量作为代理）---
                candidate_stocks = self.get_momentum_candidates(today)

                for code in candidate_stocks:
                    if code in self.portfolio.positions: continue
                    
                    stock_data = self.data_updater.get_stock_data(code)
                    if stock_data is None: continue
                    stock_data['日期'] = pd.to_datetime(stock_data['日期'])

                    # --- 4. 刺客执行（鹿希武入场判断）---
                    if self.strategy.check_entry(stock_data, today):
                        hist_data = stock_data[stock_data['日期'] <= today.strftime('%Y-%m-%d')]
                        trend_params = find_trendline_and_channel(hist_data['收盘'], trough_distance=self.strategy.trough_distance)
                        if trend_params:
                            self.portfolio.buy(code, today, self.portfolio.cash * 0.2, trend_params)
                            if len(self.portfolio.positions) >= 3: break # 如果仓位满了，则不再买入

            # --- 5. 每日记录 ---
            self.portfolio.record_value(today)

    def get_momentum_candidates(self, today):
        """在回测中，作为天命预判官的代理，选出动量最高的股票"""
        momentums = {}
        for code in self.stock_pool:
            stock_data = self.data_updater.get_stock_data(code)
            if stock_data is None: continue
            stock_data['日期'] = pd.to_datetime(stock_data['日期'])
            hist_data = stock_data[(stock_data['日期'] <= today) & (stock_data['日期'] > today - timedelta(days=30))]
            if len(hist_data) < 10: continue

            price_10_days_ago = hist_data.iloc[0]['收盘']
            current_price = hist_data.iloc[-1]['收盘']
            momentum = (current_price - price_10_days_ago) / price_10_days_ago
            if momentum > 0: # 只考虑正动量的股票
                momentums[code] = momentum
        
        # 返回动量最高的前3名
        sorted_candidates = sorted(momentums.items(), key=lambda item: item[1], reverse=True)
        return [item[0] for item in sorted_candidates[:3]]


    def generate_report(self):
        print("\n--- Backtest Report ---")
        if not self.portfolio.history:
            print("No trades were made.")
            return

        # 1. 基础收益指标
        initial_value = self.portfolio.initial_capital
        final_value = self.portfolio.history[-1]['value']
        total_return_pct = (final_value - initial_value) / initial_value * 100

        # 2. 基准表现
        benchmark_data = self.data_updater.get_stock_data(self.benchmark_code)
        benchmark_return_pct = "N/A"
        if benchmark_data is not None:
            benchmark_data['日期'] = pd.to_datetime(benchmark_data['日期'])
            benchmark_slice = benchmark_data[(benchmark_data['日期'] >= self.start_date) & (benchmark_data['日期'] <= self.end_date)]
            if not benchmark_slice.empty:
                benchmark_start_price = benchmark_slice.iloc[0]['收盘']
                benchmark_end_price = benchmark_slice.iloc[-1]['收盘']
                benchmark_return_pct = (benchmark_end_price - benchmark_start_price) / benchmark_start_price * 100

        # 3. 风险与交易分析
        df_history = pd.DataFrame(self.portfolio.history)
        df_history['daily_return'] = df_history['value'].pct_change()
        
        # 夏普比率
        sharpe_ratio = (df_history['daily_return'].mean() / df_history['daily_return'].std()) * np.sqrt(252) if df_history['daily_return'].std() != 0 else 0

        # 最大回撤
        df_history['cumulative_max'] = df_history['value'].cummax()
        df_history['drawdown'] = (df_history['value'] - df_history['cumulative_max']) / df_history['cumulative_max']
        max_drawdown_pct = df_history['drawdown'].min() * 100

        # 交易统计
        total_trades = len(self.portfolio.trades)
        winning_trades = [t for t in self.portfolio.trades if t['profit'] > 0]
        losing_trades = [t for t in self.portfolio.trades if t['profit'] <= 0]
        win_rate_pct = len(winning_trades) / total_trades * 100 if total_trades > 0 else 0

        print(f"Period: {self.start_date.date()} to {self.end_date.date()}")
        print("\n--- Performance ---")
        print(f"Total Return:            {total_return_pct:.2f}%")
        print(f"Benchmark (CSI 300):   {benchmark_return_pct if isinstance(benchmark_return_pct, str) else f'{benchmark_return_pct:.2f}%'}")
        print(f"Max Drawdown:            {max_drawdown_pct:.2f}%")
        print(f"Sharpe Ratio:            {sharpe_ratio:.2f}")
        print("\n--- Trade Analysis ---")
        print(f"Total Trades:            {total_trades}")
        print(f"Win Rate:                {win_rate_pct:.2f}%")
