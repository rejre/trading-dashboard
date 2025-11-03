import akshare as ak
import pandas as pd
import time
import os
from datetime import datetime
from config.settings import DATA_DIR

class DataUpdater:
    def __init__(self):
        self.data_dir = DATA_DIR
        
    def update_all_stock_data(self):
        """更新全市场股票数据"""
        try:
            stock_info = ak.stock_info_a_code_name()
            for index, row in stock_info.iterrows():
                code = row['code']
                self.update_single_stock_data(code)
                time.sleep(0.1)
            print(f"{datetime.now()} - 数据更新完成")
        except Exception as e:
            print(f"数据更新失败: {e}")
    
    def update_single_stock_data(self, code):
        """更新单只股票数据"""
        try:
            df = ak.stock_zh_a_hist(symbol=code, period="daily", adjust="qfq")
            if not df.empty:
                file_path = self.data_dir / f"{code}.csv"
                df.to_csv(file_path, index=False)
        except Exception as e:
            print(f"更新 {code} 数据失败: {e}")
    
    def get_realtime_data(self, code):
        """获取实时数据"""
        try:
            realtime_data = ak.stock_zh_a_spot_em()
            stock_data = realtime_data[realtime_data['代码'] == code]
            return stock_data.iloc[0] if not stock_data.empty else None
        except Exception as e:
            print(f"获取实时数据失败: {e}")
            return None

    def get_stock_data(self, code):
        """从本地CSV文件加载单只股票的历史数据"""
        file_path = self.data_dir / f"{code}.csv"
        if not os.path.exists(file_path):
            if not code.endswith(('.SZ', '.SH')):
                file_path_sz = self.data_dir / f"{code}.SZ.csv"
                if os.path.exists(file_path_sz):
                    file_path = file_path_sz
                else:
                    file_path_sh = self.data_dir / f"{code}.SH.csv"
                    if os.path.exists(file_path_sh):
                        file_path = file_path_sh
                    else:
                        return None
            else:
                return None

        try:
            df = pd.read_csv(file_path)
            return df
        except Exception as e:
            print(f"读取 {code} 数据文件失败: {e}")
            return None