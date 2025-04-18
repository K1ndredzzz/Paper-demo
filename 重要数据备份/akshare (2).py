import akshare as ak
import pandas as pd
from datetime import datetime

stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol="000002", period="daily", start_date="20250201", end_date='20250228', adjust="")
print(stock_zh_a_hist_df)

# 获取所有申万指数数据
index_hist_sw_df = ak.index_hist_sw(symbol="801180", period="day")

# 筛选指定日期范围的数据（2025年2月1日到2月28日）
start_date = pd.to_datetime('2025-02-01').date()
end_date = pd.to_datetime('2025-02-28').date()
filtered_df = index_hist_sw_df[(index_hist_sw_df['日期'] >= start_date) & (index_hist_sw_df['日期'] <= end_date)]
print(filtered_df)