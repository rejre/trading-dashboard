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

# =================== AI投研报告生成器 ===================
class AiResearchPlatform:
    def __init__(self):
        self.notifier = TelegramNotifier()
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
        report = {
            'title': f"天道龙魂·AI投研报告 ({datetime.now().strftime('%Y-%m-%d')})",
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'sections': []
        }

        for i, question in enumerate(self.questions):
            # 在真实场景中，这里会是复杂的AI调用和网络搜索
            # 为了模拟，我们生成一个基于模板的答案
            print(f"正在处理问题 {i+1}/{len(self.questions)}...")
            answer = self.simulate_ai_answer(question)
            report['sections'].append({
                'question': question.split('：')[0],
                'answer': answer
            })
            time.sleep(2) # 模拟处理时间
        
        self.write_report_to_json(report)
        self.notifier.send_message(f"✅ **AI投研报告已更新**\n\n报告日期: {datetime.now().strftime('%Y-%m-%d')}\n请访问您的网页查看详情。")
        print("AI投研报告生成并推送完成。")

    def simulate_ai_answer(self, question):
        # 这是一个模拟函数，它会返回一个基于模板的答案
        # 在一个真实的、更复杂的实现中，这里会调用Google Search等工具
        if "市场分析" in question:
            return "根据对近期A股市场的分析，**新能源汽车**和**半导体**板块显示出强劲的增长势头。政策扶持和产业链成熟是主要驱动力。未来一周，建议关注这两个方向的上游材料和设备供应商。"
        elif "投资组合" in question:
            return "对于短线操作，建议采用‘核心-卫星’策略。核心仓位配置于**新能源整车**龙头，卫星仓位则可以探索**IGBT芯片、锂电池回收**等子板块。推荐关注的股票包括：[股票A], [股票B]。"
        elif "风险管理" in question:
            return "风险管理至关重要。建议单只股票仓位不超过总资金的10%。对每个持仓，设置-5%的硬止损线。对于高位股，应采用更严格的移动止盈策略，例如回撤3%即止盈。"
        else:
            return "这是一个根据问题‘" + question.split('：')[0] + "’生成的模拟答案。在真实系统中，这里将包含通过网络搜索和AI分析得出的深入洞察。"

    def write_report_to_json(self, report):
        try:
            with open(BASE_DIR / 'status.json', 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=4)
            print("Pushing report to GitHub...")
            os.system(f"cd {BASE_DIR} && git add status.json && git commit -m \"AI Report: {datetime.now().strftime('%Y-%m-%d')}\" && git push")
        except Exception as e:
            print(f"[Error] Failed to write or push report: {e}")

# =================== 主程序入口 ===================
if __name__ == "__main__":
    platform = AiResearchPlatform()
    # 每天早上8点执行一次报告生成
    schedule.every().day.at("08:00").do(platform.generate_daily_report)
    # 启动时先立即执行一次
    platform.generate_daily_report()
    print("--- AI投研平台已激活，等待定时任务... ---")
    while True:
        schedule.run_pending()
        time.sleep(1)