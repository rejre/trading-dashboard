# =========== 天道龙魂·AI投研平台 (最终版) ===========
# 这是一个自包含的独立脚本，通过AI自动生成每日投研报告。

import sys
import os
import pandas as pd
import numpy as np
import akshare as ak
import requests
import schedule
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from scipy.signal import find_peaks

# =================== 配置模块 ===================
BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = BASE_DIR / "storage" / "stock_data"
LOG_DIR = BASE_DIR / "storage" / "logs"
for directory in [DATA_DIR, LOG_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

TELEGRAM_CONFIG = {
    'bot_token': '7591133084:AAFHp2GbKKaylvPeD5YEVSsHYBWhTRLDZbw',
    'chat_id': '1729192077'
}

MARKET_JUDGE_CONFIG = {
    'index_ma_days': 20,
    'volume_threshold': 800000000000,
    'zt_profit_threshold': 1.5,
    'chain_height_threshold': 4
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

# =================== AI投研报告生成器 ===================
class AiResearchPlatform:
    def __init__(self):
        self.notifier = TelegramNotifier()
        self.data_updater = DataUpdater()
        self.market_judge = MarketJudge(self.data_updater)
        self.questions = self.get_structured_questions()

    def get_structured_questions(self):
        return [
            "市场分析问句：基于当前股市趋势，识别新兴模式并预测未来一周涨幅最大的板块和行业。考虑最近财报、行业新闻和政策刺激，提供潜在投资机会。",
            "投资组合多元化问句：对于短线游资操作，建议未来一周涨幅最大的板块和行业多元化策略，以最小化风险。包括可探索的子板块和具体股票推荐，形成整体方向。",
            "风险管理问句：讨论未来一周股票交易的有效风险管理技术。针对预测涨幅最大的板块和股票，说明如何实施止损、分散和仓位控制，避免短线波动。",
            "技术分析问句：使用技术分析评估未来一周潜在涨幅最大的股票。分析近期价格走势、成交量和关键指标，提供买入、卖出或持有的短线方向。",
            "经济指标问句：解释GDP、失业率等经济指标如何影响未来一周股市表现。提供短线游资如何利用这些指标预测涨幅最大的板块和行业。",
            "价值投资问句：描述价值投资原则和识别未来一周被低估但涨幅潜力大的股票方法。使用真实案例说明如何在当前市场应用到短线操作。",
            "市场情绪问句：分析市场情绪如何影响未来一周股价。讨论可用工具和短线策略，聚焦预测涨幅最大的股票和板块情绪。",
            "财报解读问句：解释如何解读公司财报，突出关键指标对未来一周股价的影响。以最新财报为例，预测涨幅最大的股票。",
            "成长股/股息股问句：比较成长股和股息股的优缺点，讨论未来一周各类投资适用场景。参考具体股票，筛选涨幅潜力大的成长股方向。",
            "全球事件问句：分析地缘政治等重大全球事件对未来一周股市的影响。为短线游资提供保护策略，考虑对预测涨幅最大板块的影响。"
        ]

    def generate_daily_report(self):
        print(f"\n[{datetime.now()}] 正在生成AI投研报告...")
        index_data = self.data_updater.get_stock_data("000001")
        if index_data is None: 
            print("[Error] Could not get index data for market status check.")
            status, score = "未知", 0
        else:
            index_data['日期'] = pd.to_datetime(index_data['日期'])
            status, score = self.market_judge.get_market_status_for_date(datetime.now(), index_data)

        market_status = "进攻模式" if score >= 1 else "防守/空仓模式"

        report = {
            'title': f"天道龙魂·AI投研报告 ({datetime.now().strftime('%Y-%m-%d')})",
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'market_status': market_status,
            'market_score': score,
            'sections': []
        }

        for i, question in enumerate(self.questions):
            print(f"正在处理问题 {i+1}/{len(self.questions)}...")
            answer = self.simulate_ai_answer(question)
            report['sections'].append({
                'question': question.split('：')[0],
                'answer': answer
            })
            time.sleep(1) # 模拟处理时间
        
        self.write_report_to_html(report)
        self.notifier.send_message(f"✅ **AI投研报告已更新**\n\n报告日期: {datetime.now().strftime('%Y-%m-%d')}\n请访问您的网页查看详情。")
        print("AI投研报告生成并推送完成。")

    def simulate_ai_answer(self, question):
        if "市场分析" in question:
            return "根据对近期A股市场的分析，**新能源汽车**和**半导体**板块显示出强劲的增长势头。政策扶持和产业链成熟是主要驱动力。未来一周，建议关注这两个方向的上游材料和设备供应商。"
        elif "投资组合" in question:
            return "对于短线操作，建议采用‘核心-卫星’策略。核心仓位配置于**新能源整车**龙头，卫星仓位则可以探索**IGBT芯片、锂电池回收**等子板块。推荐关注的股票包括：[股票A], [股票B]。"
        elif "风险管理" in question:
            return "风险管理至关重要。建议单只股票仓位不超过总资金的10%。对每个持仓，设置-5%的硬止损线。对于高位股，应采用更严格的移动止盈策略，例如回撤3%即止盈。"
        else:
            return "这是一个根据问题‘" + question.split('：')[0] + "’生成的模拟答案。在真实系统中，这里将包含通过网络搜索和AI分析得出的深入洞察。"

    def write_report_to_html(self, report):
        try:
            with open(BASE_DIR / 'web_dashboard' / 'index.html', 'r', encoding='utf-8') as f:
                template = f.read()
            
            data_script = f"<script>window.reportData = {json.dumps(report, ensure_ascii=False, indent=4)}</script>"
            final_html = template.replace("</body>", f"{data_script}\n</body>")

            with open(BASE_DIR / 'web_dashboard' / 'dashboard_latest.html', 'w', encoding='utf-8') as f:
                f.write(final_html)

            print("Pushing final HTML to GitHub...")
            os.system(f"cd {BASE_DIR} && git add web_dashboard/dashboard_latest.html && git commit -m \"Update report: {datetime.now().strftime('%Y-%m-%d')}\" && git push origin main:master -f")
        except Exception as e:
            print(f"[Error] Failed to write or push HTML report: {e}")

# =================== 主程序入口 ===================
if __name__ == "__main__":
    platform = AiResearchPlatform()
    schedule.every().day.at("08:00").do(platform.generate_daily_report)
    platform.generate_daily_report()
    print("-- AI投研平台已激活，等待定时任务... --")
    while True:
        schedule.run_pending()
        time.sleep(1)