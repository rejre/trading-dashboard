# -*- coding: utf-8 -*-
"""
一个基于类的、与现有回测系统兼容的策略模板。
"""

import pandas as pd
import numpy as np
import talib

class TemplateStrategy:
    """
    策略模板类。
    回测系统会创建这个类的一个实例，并调用它的 check_entry 和 check_exit 方法。
    """
    def __init__(self, params={}):
        """
        策略初始化。
        在这里定义策略需要用到的参数。
        :param params: 一个从外界传入的参数字典，例如: {'short_ma': 20, 'long_ma': 60}
        """
        print("--- 初始化 TemplateStrategy ---")
        # --- 可调参数 ---
        self.short_ma_period = params.get('short_ma', 20)
        self.long_ma_period = params.get('long_ma', 60)
        print(f"短期均线周期: {self.short_ma_period}, 长期均线周期: {self.long_ma_period}")

    def check_entry(self, stock_data, date):
        """
        检查给定日期是否满足所有【入场】条件。
        :param stock_data: 包含该股票所有历史数据的DataFrame。
        :param date: 当前回测的日期。
        :return: 如果满足入场条件，返回 True；否则返回 False。
        """
        # 筛选出当前日期及之前的数据
        hist_data = stock_data[stock_data['日期'] <= date.strftime('%Y-%m-%d')].copy()
        
        # 数据量不足，无法计算指标，直接返回
        if len(hist_data) < self.long_ma_period + 2:
            return False

        # --- 1. 计算指标 ---
        # 计算短期和长期移动平均线
        hist_data['short_ma'] = talib.MA(hist_data['收盘'], timeperiod=self.short_ma_period)
        hist_data['long_ma'] = talib.MA(hist_data['收盘'], timeperiod=self.long_ma_period)

        # 获取最近两个时间点的数据
        latest = hist_data.iloc[-1]
        previous = hist_data.iloc[-2]

        # --- 2. 编写入场逻辑 ---
        # 示例逻辑：金叉买入
        # 当天的短期均线 >= 长期均线
        # 昨天的短期均线 < 昨天的长期均线
        is_golden_cross = latest['short_ma'] >= latest['long_ma'] and previous['short_ma'] < previous['long_ma']

        if is_golden_cross:
            stock_code = hist_data.iloc[0].get('代码', 'Unknown')
            print(f"【入场信号】: {date.date()} - 股票代码: {stock_code} (金叉)")
            return True

        return False

    def check_exit(self, stock_data, date, position_details):
        """
        检查是否满足【出场】（止损或止盈）条件。
        :param stock_data: 包含该股票所有历史数据的DataFrame。
        :param date: 当前回测的日期。
        :param position_details: 一个包含持仓信息的字典，例如买入日期、价格等。
        :return: 如果满足出场条件，返回一个元组 (原因字符串, 价格)；否则返回 (None, 0)。
        """
        # 筛选出当前日期及之前的数据
        hist_data = stock_data[stock_data['日期'] <= date.strftime('%Y-%m-%d')].copy()

        # 数据量不足，无法计算指标，直接返回
        if len(hist_data) < self.long_ma_period + 2:
            return None, 0

        # --- 1. 计算指标 ---
        hist_data['short_ma'] = talib.MA(hist_data['收盘'], timeperiod=self.short_ma_period)
        hist_data['long_ma'] = talib.MA(hist_data['收盘'], timeperiod=self.long_ma_period)
        
        latest = hist_data.iloc[-1]
        previous = hist_data.iloc[-2]

        # --- 2. 编写出场逻辑 ---
        # 示例逻辑 1：死叉卖出
        is_death_cross = latest['short_ma'] <= latest['long_ma'] and previous['short_ma'] > previous['long_ma']
        if is_death_cross:
            stock_code = hist_data.iloc[0].get('代码', 'Unknown')
            print(f"【出场信号】: {date.date()} - 股票代码: {stock_code} (死叉)")
            return 'death_cross', latest['收盘'] # 以当日收盘价卖出

        # 示例逻辑 2：固定比例止损
        buy_price = position_details.get('buy_price', 0)
        stop_loss_price = buy_price * 0.9 # 10% 止损
        if latest['收盘'] < stop_loss_price:
            stock_code = hist_data.iloc[0].get('代码', 'Unknown')
            print(f"【出场信号】: {date.date()} - 股票代码: {stock_code} (止损)")
            return 'stop_loss', latest['收盘']

        return None, 0
