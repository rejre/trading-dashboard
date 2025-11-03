import akshare as ak
import pandas as pd
import requests
from datetime import datetime
import json
from config.settings import DATA_DIR

class ProphetScanner:
    def __init__(self):
        self.watchlist_file = DATA_DIR / "watchlist.json"
    
    def morning_news_scan(self):
        """早间新闻扫描"""
        try:
            # 使用akshare获取新闻（简化版）
            news = ak.stock_news_em()
            hot_news = news.head(10)
            
            potential_stocks = []
            for _, item in hot_news.iterrows():
                stocks = self._extract_stocks_from_news(item['新闻内容'])
                potential_stocks.extend(stocks)
                
            return list(set(potential_stocks))[:5]  # 返回前5只
            
        except Exception as e:
            print(f"新闻扫描失败: {e}")
            return []
    
    def bidding_analysis(self, watchlist):
        """集合竞价分析"""
        try:
            # 获取实时行情
            realtime_data = ak.stock_zh_a_spot_em()
            targets = []
            
            for code in watchlist:
                stock_data = realtime_data[realtime_data['代码'] == code]
                if not stock_data.empty:
                    stock = stock_data.iloc[0]
                    change_percent = stock['涨跌幅']
                    
                    # 竞价筛选条件
                    if 3 <= change_percent <= 7:
                        targets.append({
                            'code': code,
                            'name': stock['名称'],
                            'change_percent': change_percent,
                            'volume': stock['成交量']
                        })
            
            return targets[:3]  # 返回最强3只
            
        except Exception as e:
            print(f"竞价分析失败: {e}")
            return []
    
    def _extract_stocks_from_news(self, news_content):
        """从新闻内容中提取相关股票（简化版）"""
        # 这里需要实现自然语言处理来识别股票
        # 简化版：手动维护关键词-股票映射
        keyword_map = {
            '新能源': ['宁德时代', '比亚迪', '隆基绿能'],
            '人工智能': ['科大讯飞', '海康威视', '中兴通讯'],
            '芯片': ['中芯国际', '韦尔股份', '兆易创新']
        }
        
        found_stocks = []
        for keyword, stocks in keyword_map.items():
            if keyword in news_content:
                found_stocks.extend(stocks)
                
        return found_stocks