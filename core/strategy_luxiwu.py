import pandas as pd
import numpy as np
from scipy.signal import find_peaks

def find_trendline_and_channel(price_series, lookback_period=120, trough_distance=10):
    """
    在给定的价格序列中寻找两个最新的显著低点，并计算趋势线和通道。
    返回一个包含趋势线参数的字典，如果找不到有效趋势则返回None。
    """
    subset = price_series.tail(lookback_period)
    troughs, _ = find_peaks(-subset, distance=trough_distance, prominence=0.5)

    if len(troughs) < 2:
        return None

    # 将局部索引转换为原始price_series的索引
    troughs_indices = subset.index[troughs]
    last_trough_idx = troughs_indices[-1]
    second_last_trough_idx = troughs_indices[-2]

    p1 = (second_last_trough_idx, price_series[second_last_trough_idx])
    p2 = (last_trough_idx, price_series[last_trough_idx])

    if p2[1] <= p1[1]: return None

    slope = (p2[1] - p1[1]) / (p2[0] - p1[0])
    if slope < 0.05: return None # 过滤掉过于平缓的趋势

    intercept = p2[1] - slope * p2[0]

    # 寻找两低点之间的高点
    highs_between_troughs, _ = find_peaks(price_series[p1[0]:p2[0]])
    if len(highs_between_troughs) == 0: return None
    
    highest_point_idx = price_series.index[p1[0]:p2[0]][highs_between_troughs].max()
    highest_point_price = price_series[highest_point_idx]
    upper_intercept = highest_point_price - slope * highest_point_idx

    return {
        'slope': slope,
        'intercept': intercept,
        'upper_intercept': upper_intercept,
        'p1_idx': p1[0],
        'p2_idx': p2[0]
    }

class LuXiWuStrategy:
    """封装鹿希武趋势交易法的所有判断逻辑"""
    def __init__(self, params={}):
        self.lookback_period = params.get('lookback_period', 120)
        self.trough_distance = params.get('trough_distance', 10)
        self.slope_threshold = params.get('slope_threshold', 0.05)

    def check_entry(self, stock_data, date):
        """检查给定日期是否满足所有入场条件"""
        hist_data = stock_data[stock_data['日期'] <= date.strftime('%Y-%m-%d')].copy()
        if len(hist_data) < 60: return False # 需要足够历史数据

        today = hist_data.iloc[-1]
        today_index = hist_data.index[-1]

        # 1. 趋势判断
        trend_params = find_trendline_and_channel(hist_data['收盘'], self.lookback_period, self.trough_distance)
        if not trend_params:
            return False

        # 2. 位置判断 (回踩下轨)
        trendline_price_today = trend_params['slope'] * today_index + trend_params['intercept']
        is_near_trendline = (today['最低'] <= trendline_price_today * 1.02) and (today['收盘'] > trendline_price_today * 0.98)
        if not is_near_trendline:
            return False

        # 3. 均线判断
        hist_data['ma10'] = hist_data['收盘'].rolling(10).mean()
        is_above_ma10 = today['收盘'] > hist_data.iloc[-1]['ma10']
        if not is_above_ma10:
            return False

        # 4. 成交量判断
        hist_data['vol_ma10'] = hist_data['成交量'].rolling(10).mean()
        is_volume_high = today['成交量'] > (hist_data.iloc[-1]['vol_ma10'] * 1.2)
        if not is_volume_high:
            return False

        # 5. K线判断
        is_positive_candle = today['收盘'] > today['开盘']
        if not is_positive_candle:
            return False
        
        # 所有条件满足
        print(f"ENTRY SIGNAL: {date.date()} for {stock_data.iloc[0].get('代码', 'Unknown')}")
        return True

    def check_exit(self, stock_data, date, position_details):
        """检查是否满足止损或止盈条件"""
        hist_data = stock_data[stock_data['日期'] <= date.strftime('%Y-%m-%d')]
        if len(hist_data) < 2: return None, 0

        today = hist_data.iloc[-1]
        today_index = hist_data.index[-1]

        # 使用建仓时的趋势线来判断
        trend_params = position_details.get('trend_params')
        if not trend_params: return None, 0

        # 止损：收盘跌破下轨2%
        lower_rail_price = trend_params['slope'] * today_index + trend_params['intercept']
        stop_loss_price = lower_rail_price * 0.98
        if today['收盘'] < stop_loss_price:
            print(f"STOP LOSS: {date.date()} for {stock_data.iloc[0].get('代码', 'Unknown')}")
            return 'stop_loss', today['收盘']

        # 止盈：价格触及上轨
        upper_rail_price = trend_params['slope'] * today_index + trend_params['upper_intercept']
        if today['最高'] >= upper_rail_price:
            print(f"TAKE PROFIT: {date.date()} for {stock_data.iloc[0].get('代码', 'Unknown')}")
            return 'take_profit', upper_rail_price # 以触及价格止盈

        return None, 0
