import akshare as ak
import pandas as pd
import numpy as np
from tqdm import tqdm
import time
import re
import os
import json
from datetime import datetime

def get_stock_data_akshare(stock_codes, start_date, end_date):
    """使用akshare获取股票数据"""
    all_data = []
    
    for code in tqdm(stock_codes, desc="获取股票数据"):
        try:
            # 获取日K线数据
            df = ak.stock_zh_a_hist(symbol=code, period="daily", 
                                    start_date=start_date, end_date=end_date, 
                                    adjust="qfq")
            
            # 重命名列以统一格式
            df.rename(columns={
                '日期': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount',
                '振幅': 'amplitude',
                '涨跌幅': 'pct_change',
                '涨跌额': 'price_change',
                '换手率': 'turnover_rate'
            }, inplace=True)
            
            # 添加股票代码
            df['code'] = code
            all_data.append(df)
            
            # 避免频繁请求被限制
            time.sleep(0.5)
            
        except Exception as e:
            print(f"获取股票 {code} 数据时出错: {e}")
    
    # 合并所有股票数据
    if all_data:
        stock_data = pd.concat(all_data, ignore_index=True)
        
        # 确保日期格式一致
        stock_data['date'] = pd.to_datetime(stock_data['date'])
        
        # 计算收益率 (考虑交易日)
        # 首先按股票代码和日期排序
        stock_data = stock_data.sort_values(['code', 'date'])
        
        # 为每只股票计算未来交易日的收益率
        result_data = []
        
        # 分组处理每只股票
        for code, group in stock_data.groupby('code'):
            # 按日期排序
            group = group.sort_values('date')
            
            # 获取交易日序列
            trade_dates = group['date'].tolist()
            
            # 为每个交易日找到未来的第1、3、5个交易日的索引
            future_dates = {}
            for i, current_date in enumerate(trade_dates):
                # 初始化未来交易日
                future_dates[current_date] = {
                    't+1': None,
                    't+3': None,
                    't+5': None
                }
                
                # 寻找未来的交易日
                if i + 1 < len(trade_dates):
                    future_dates[current_date]['t+1'] = trade_dates[i + 1]
                if i + 3 < len(trade_dates):
                    future_dates[current_date]['t+3'] = trade_dates[i + 3]
                if i + 5 < len(trade_dates):
                    future_dates[current_date]['t+5'] = trade_dates[i + 5]
            
            # 创建价格映射: 日期 -> 收盘价
            price_map = dict(zip(group['date'], group['close']))
            
            # 计算收益率
            for _, row in group.iterrows():
                current_date = row['date']
                current_price = row['close']
                
                # 计算t+1收益率
                if future_dates[current_date]['t+1'] is not None:
                    future_price = price_map[future_dates[current_date]['t+1']]
                    row['forward_ret_1d'] = future_price / current_price - 1
                else:
                    row['forward_ret_1d'] = None
                
                # 计算t+3收益率
                if future_dates[current_date]['t+3'] is not None:
                    future_price = price_map[future_dates[current_date]['t+3']]
                    row['forward_ret_3d'] = future_price / current_price - 1
                else:
                    row['forward_ret_3d'] = None
                
                # 计算t+5收益率
                if future_dates[current_date]['t+5'] is not None:
                    future_price = price_map[future_dates[current_date]['t+5']]
                    row['forward_ret_5d'] = future_price / current_price - 1
                else:
                    row['forward_ret_5d'] = None
                
                result_data.append(row)
        
        # 将结果转换回DataFrame
        stock_data = pd.DataFrame(result_data)
        
        return stock_data
    else:
        raise ValueError("未能获取任何股票数据")


def get_index_data_akshare(index_codes, start_date, end_date):
    """使用akshare获取申万行业指数数据"""
    all_data = []
    
    for code in tqdm(index_codes, desc="获取行业指数数据"):
        try:
            # 优先使用正确的API - ak.index_hist_sw
            try:
                # 使用正确的API获取数据，注意这个API不接受start_date和end_date参数
                df = ak.index_hist_sw(symbol=code, period="day")
                
                if not df.empty:
                    print(f"使用index_hist_sw成功获取 {code} 数据")
                    
                    # 检查并规范化列名
                    # ak.index_hist_sw返回的数据包含这些列：'代码', '日期', '收盘', '开盘', '最高', '最低', '成交量', '成交额'
                    if '代码' in df.columns and '日期' in df.columns:
                        # 标准化列名映射
                        rename_dict = {
                            '代码': 'code',
                            '日期': 'date',
                            '开盘': 'open',
                            '收盘': 'close',
                            '最高': 'high',
                            '最低': 'low',
                            '成交量': 'volume',
                            '成交额': 'amount'
                        }
                        
                        # 重命名所有存在的列
                        rename_cols = {k: v for k, v in rename_dict.items() if k in df.columns}
                        df = df.rename(columns=rename_cols)
                        
                        # 确保日期列是datetime类型
                        if 'date' in df.columns:
                            df['date'] = pd.to_datetime(df['date'])
                            
                            # 过滤日期范围
                            start = pd.to_datetime(start_date)
                            end = pd.to_datetime(end_date)
                            df = df[(df['date'] >= start) & (df['date'] <= end)]
                            
                            if df.empty:
                                print(f"过滤后的 {code} 数据为空，可能日期范围内没有数据")
                                continue
                        else:
                            print(f"警告: {code} 数据中没有date列")
                            continue
                    else:
                        print(f"警告: {code} 数据列名不符合预期: {df.columns.tolist()}")
                        continue
                    
                    # 计算缺少的指标
                    if 'close' in df.columns:
                        # 计算涨跌幅 (如果不存在)
                        if 'pct_change' not in df.columns:
                            # 按日期排序
                            df = df.sort_values('date')
                            # 计算涨跌幅 = (当日收盘价/前日收盘价 - 1) * 100
                            df['pct_change'] = df['close'].pct_change() * 100
                            # 第一天的涨跌幅设为0
                            df['pct_change'] = df['pct_change'].fillna(0)
                    else:
                        print(f"警告: {code} 数据中没有close列")
                        continue
                    
                    # 添加board_code列
                    df['board_code'] = code
                    
                    # 打印前几行数据，用于调试
                    print(f"{code} 数据前3行:")
                    if len(df) >= 3:
                        print(df[['date', 'open', 'close']].head(3).to_string())
                    
                    all_data.append(df)
                else:
                    print(f"使用index_hist_sw获取 {code} 的数据为空")
                    df = None
            except Exception as e:
                print(f"尝试使用index_hist_sw获取 {code} 失败: {e}")
                df = None
                
                # 备选方法: 尝试使用带有swsi前缀的股票指数接口
                try:
                    sw_code = f"swsi{code}"
                    df = ak.stock_zh_index_daily(symbol=sw_code, start_date=start_date, end_date=end_date)
                    if not df.empty:
                        print(f"使用stock_zh_index_daily成功获取 {code} 数据")
                        
                        # 重命名列
                        df = df.rename(columns={
                            'date': 'date',
                            'open': 'open',
                            'close': 'close',
                            'high': 'high',
                            'low': 'low',
                            'volume': 'volume',
                            'amount': 'amount',
                            'change': 'pct_change'
                        })
                        
                        # 添加board_code列
                        df['board_code'] = code
                        
                        all_data.append(df)
                    else:
                        print(f"使用stock_zh_index_daily获取 {code} 的数据为空")
                except Exception as e2:
                    print(f"尝试使用stock_zh_index_daily获取 {code} 也失败: {e2}")
                    
                    # 最后尝试: 使用stock_zh_index_daily_em接口
                    try:
                        df = ak.stock_zh_index_daily_em(symbol=code, start_date=start_date, end_date=end_date)
                        if not df.empty:
                            print(f"使用stock_zh_index_daily_em成功获取 {code} 数据")
                            
                            # 重命名列
                            df = df.rename(columns={
                                '日期': 'date',
                                '开盘': 'open',
                                '收盘': 'close',
                                '最高': 'high',
                                '最低': 'low',
                                '成交量': 'volume',
                                '成交额': 'amount',
                                '涨跌幅': 'pct_change'
                            })
                            
                            # 添加board_code列
                            df['board_code'] = code
                            
                            all_data.append(df)
                        else:
                            print(f"使用stock_zh_index_daily_em获取 {code} 的数据为空")
                    except Exception as e3:
                        print(f"尝试使用stock_zh_index_daily_em获取 {code} 也失败: {e3}")
                        print(f"无法获取 {code} 的数据，跳过")
        
        except Exception as e:
            print(f"获取行业指数 {code} 数据时出错: {e}")
    
    # 合并所有行业指数数据
    if all_data:
        index_data = pd.concat(all_data, ignore_index=True)
        return index_data
    else:
        print("警告：未能获取任何行业指数数据")
        return pd.DataFrame()


def load_industry_mapping():
    """从industries.py加载行业映射关系，返回股票代码和对应的行业代码"""
    industry_map = []
    
    try:
        with open('industries.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 提取INDUSTRY_STOCK_MAP字典内容
        match = re.search(r'INDUSTRY_STOCK_MAP\s*=\s*\{(.*?)\}(?=\s*#\s*行业代码)', content, re.DOTALL)
        if match:
            industry_dict_str = "{" + match.group(1) + "}"
            
            # 处理字典格式使其可被eval解析
            # 去除注释，规范化引号
            cleaned_str = re.sub(r'#.*?\n', '\n', industry_dict_str)
            cleaned_str = cleaned_str.replace("'", '"')
            
            # 解析并从industry_dict中提取股票代码和行业代码信息
            try:
                # 提取每个行业板块及其代码
                industry_matches = re.finditer(r"'([^']+)':\s*{\s*'code':\s*'(\d+)'", content, re.DOTALL)
                
                # 创建行业名称到代码的映射
                industry_code_map = {}
                for match in industry_matches:
                    industry_name = match.group(1)
                    board_code = match.group(2)
                    industry_code_map[industry_name] = board_code
                
                # 提取每个行业的股票
                industry_stocks = re.finditer(r"'([^']+)':\s*{[^}]*?'stocks':\s*\[(.*?)\]", content, re.DOTALL)
                
                for match in industry_stocks:
                    industry_name = match.group(1)
                    stocks_section = match.group(2)
                    board_code = industry_code_map.get(industry_name)
                    
                    if board_code:
                        # 提取股票代码
                        code_matches = re.finditer(r"'代码':\s*'(\d+)'", stocks_section)
                        for code_match in code_matches:
                            stock_code = code_match.group(1)
                            industry_map.append({
                                'code': stock_code,
                                'board_code': board_code,
                                'industry': industry_name  # 保留行业名称以备参考
                            })
                
            except Exception as parse_err:
                print(f"解析industry_dict失败: {parse_err}")
                # 备选方案：手动解析
                # 这里可以添加更多硬编码的行业映射规则
    
    except Exception as e:
        print(f"加载industries.py文件失败: {e}")
        # 备选方案：创建一个简单的映射
        backup_industry_map = [
            {'code': '000725', 'board_code': '801080', 'industry': '电子'},
            {'code': '002049', 'board_code': '801080', 'industry': '电子'},
            {'code': '600276', 'board_code': '801150', 'industry': '医药生物'},
            {'code': '600196', 'board_code': '801150', 'industry': '医药生物'},
            {'code': '601398', 'board_code': '801780', 'industry': '银行'},
            {'code': '601288', 'board_code': '801780', 'industry': '银行'},
            {'code': '600048', 'board_code': '801180', 'industry': '房地产'},
            {'code': '001979', 'board_code': '801180', 'industry': '房地产'},
            {'code': '600519', 'board_code': '801120', 'industry': '食品饮料'},
            {'code': '000858', 'board_code': '801120', 'industry': '食品饮料'},
            {'code': '300750', 'board_code': '801730', 'industry': '电气设备'},
            {'code': '002594', 'board_code': '801730', 'industry': '电气设备'},
            {'code': '002415', 'board_code': '801750', 'industry': '计算机'},
            {'code': '300059', 'board_code': '801750', 'industry': '计算机'},
            {'code': '601899', 'board_code': '801050', 'industry': '有色金属'},
            {'code': '603993', 'board_code': '801050', 'industry': '有色金属'}
        ]
        industry_map = backup_industry_map
    
    # 确保返回的是DataFrame
    if not industry_map:
        print("警告：未能提取到行业映射数据，使用备用数据")
        industry_map = [
            {'code': '000725', 'board_code': '801080', 'industry': '电子'},
            {'code': '600276', 'board_code': '801150', 'industry': '医药生物'},
            {'code': '601398', 'board_code': '801780', 'industry': '银行'},
            {'code': '600048', 'board_code': '801180', 'industry': '房地产'},
            {'code': '600519', 'board_code': '801120', 'industry': '食品饮料'},
            {'code': '300750', 'board_code': '801730', 'industry': '电气设备'},
            {'code': '002415', 'board_code': '801750', 'industry': '计算机'},
            {'code': '601899', 'board_code': '801050', 'industry': '有色金属'}
        ]
    
    return pd.DataFrame(industry_map)


def extract_stock_codes():
    """从industries.py提取所有股票代码"""
    stock_codes = []
    
    try:
        # 从行业映射中提取股票代码
        industry_mapping = load_industry_mapping()
        stock_codes = industry_mapping['code'].unique().tolist()
    except Exception as e:
        print(f"提取股票代码失败: {e}")
        # 备选方案：返回一些常见的股票代码
        stock_codes = [
            '000725', '002049', '600745', '002371', '603986',  # 电子
            '600276', '600196', '300760', '300015', '000538',  # 医药生物
            '601398', '601288', '601988', '601939', '600036',  # 银行
            '600048', '001979', '600606', '000002', '600383',  # 房地产
            '600519', '000858', '600887', '603288', '000568',  # 食品饮料
            '300750', '002594', '601012', '300014', '601877',  # 电气设备
            '002415', '300059', '600570', '002230', '600588',  # 计算机
            '601899', '603993', '600111', '600219', '000630'   # 有色金属
        ]
    
    return stock_codes


def organize_industry_data(stock_data, industry_mapping=None):
    """整理行业数据，合并行业代码信息"""
    if industry_mapping is None:
        # 如果没有提供行业映射，尝试从industries.py加载
        industry_mapping = load_industry_mapping()
    elif isinstance(industry_mapping, str):
        # 如果提供了文件路径，从文件加载
        industry_mapping = pd.read_csv(industry_mapping)
    
    # 如果股票数据包含'股票代码'列，但没有'code'列
    if '股票代码' in stock_data.columns and 'code' not in stock_data.columns:
        stock_data['code'] = stock_data['股票代码']
    
    # 合并行业信息，使用board_code而不是industry
    stock_data = pd.merge(stock_data, industry_mapping[['code', 'board_code', 'industry']], on='code', how='left')
    
    # 处理行业代码缺失值
    stock_data['board_code'] = stock_data['board_code'].fillna('000000')  # 使用000000作为未知行业的代码
    
    # 删除冗余的'股票代码'列
    if '股票代码' in stock_data.columns and 'code' in stock_data.columns:
        stock_data = stock_data.drop(columns=['股票代码'])
    
    # 将'code'列重命名为'stock_code'并移到第一列
    stock_data = stock_data.rename(columns={'code': 'stock_code'})
    
    # 获取所有列名
    cols = stock_data.columns.tolist()
    # 将'stock_code'移到第一位
    cols.remove('stock_code')
    cols = ['stock_code'] + cols
    # 重新排序列
    stock_data = stock_data[cols]
    
    return stock_data


def save_data(data, file_path):
    """保存数据到CSV文件"""
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
    
    # 确保数据完整性
    if isinstance(data, pd.DataFrame) and not data.empty:
        # 如果是股票或合并数据，检查关键列
        key_cols = ['volume', 'amount', 'amplitude', 'pct_change', 'price_change']
        existing_cols = [col for col in key_cols if col in data.columns]
        
        if existing_cols:
            print(f"保存文件 {file_path} 前的关键列信息:")
            for col in existing_cols:
                null_count = data[col].isnull().sum()
                print(f"  - '{col}' 列: {len(data[col])} 行, {null_count} 个空值")
                if len(data[col]) > 0:
                    print(f"    数据范围: {data[col].min()} 至 {data[col].max()}")
        
        # 检查行数和列数
        print(f"保存数据集: {len(data)} 行, {len(data.columns)} 列")
        
        # 保存前验证没有意外的列名重复
        if len(data.columns) != len(set(data.columns)):
            duplicates = [col for col in data.columns if list(data.columns).count(col) > 1]
            print(f"警告：检测到重复列名：{duplicates}")
            # 重命名重复列
            new_data = data.copy()
            for i, col in enumerate(new_data.columns):
                if col in duplicates:
                    count = list(new_data.columns[:i]).count(col)
                    if count > 0:
                        new_data = new_data.rename(columns={col: f"{col}_{count}"})
            data = new_data
    
    # 保存数据
    data.to_csv(file_path, index=False, encoding='utf-8')
    print(f"数据已保存至: {file_path}")
    
    # 验证保存的文件
    try:
        saved_data = pd.read_csv(file_path)
        print(f"验证: 成功读取保存的文件，包含 {len(saved_data)} 行, {len(saved_data.columns)} 列")
    except Exception as e:
        print(f"警告: 无法验证保存的文件: {e}")


def generate_industry_report(organized_data, output_dir):
    """生成行业统计报告"""
    # 计算各行业的基本统计数据
    industry_stats = organized_data.groupby(['board_code', 'industry']).agg(
        stock_count=('stock_code', 'nunique'),
        avg_price=('close', 'mean'),
        avg_volume=('volume', 'mean'),
        avg_pct_change=('pct_change', 'mean'),
        avg_turnover=('turnover_rate', 'mean'),
        max_price=('close', 'max'),
        min_price=('close', 'min'),
        volatility=('pct_change', 'std')
    ).reset_index()
    
    # 保存行业统计数据
    industry_stats.to_csv(f"{output_dir}/industry_statistics.csv", index=False, encoding='utf-8')
    print(f"行业统计报告已保存至: {output_dir}/industry_statistics.csv")
    
    # 计算行业间的相关性
    # 首先计算每日行业平均收益率
    daily_industry_returns = organized_data.groupby(['date', 'board_code'])['pct_change'].mean().unstack()
    
    # 计算相关性矩阵
    if daily_industry_returns.shape[0] > 1:  # 确保有足够数据计算相关性
        correlation_matrix = daily_industry_returns.corr()
        correlation_matrix.to_csv(f"{output_dir}/industry_correlation.csv", encoding='utf-8')
        print(f"行业收益率相关性矩阵已保存至: {output_dir}/industry_correlation.csv")
    
    # 计算各行业的日均收益率和波动率
    daily_stats = organized_data.groupby(['board_code', 'industry', 'date'])['pct_change'].mean().reset_index()
    industry_daily_stats = daily_stats.groupby(['board_code', 'industry']).agg(
        avg_daily_return=('pct_change', 'mean'),
        daily_volatility=('pct_change', 'std'),
        max_daily_return=('pct_change', 'max'),
        min_daily_return=('pct_change', 'min')
    ).reset_index()
    
    # 计算夏普比率(简化版，假设无风险利率为0)
    industry_daily_stats['sharpe_ratio'] = industry_daily_stats['avg_daily_return'] / industry_daily_stats['daily_volatility']
    
    # 保存日均统计数据
    industry_daily_stats.to_csv(f"{output_dir}/industry_daily_stats.csv", index=False, encoding='utf-8')
    print(f"行业日均统计数据已保存至: {output_dir}/industry_daily_stats.csv")
    
    # 如果有指数数据，计算行业与指数的相关性
    if 'idx_close' in organized_data.columns:
        # 计算个股收益率与行业指数收益率的相关性
        # 为此需要先对每只股票计算与其对应行业指数的相关系数
        stock_idx_correlation = []
        
        for stock_code in organized_data['stock_code'].unique():
            stock_data = organized_data[organized_data['stock_code'] == stock_code]
            if stock_data.empty or 'idx_pct_change' not in stock_data.columns:
                continue
                
            # 计算相关系数
            correlation = stock_data['pct_change'].corr(stock_data['idx_pct_change'])
            beta = stock_data['pct_change'].cov(stock_data['idx_pct_change']) / stock_data['idx_pct_change'].var()
            
            # 获取行业信息
            board_code = stock_data['board_code'].iloc[0]
            industry_name = stock_data['industry'].iloc[0]
            
            stock_idx_correlation.append({
                'stock_code': stock_code,
                'board_code': board_code,
                'industry': industry_name,
                'correlation': correlation,
                'beta': beta
            })
        
        # 转换为DataFrame并保存
        if stock_idx_correlation:
            corr_df = pd.DataFrame(stock_idx_correlation)
            corr_df.to_csv(f"{output_dir}/stock_index_correlation.csv", index=False, encoding='utf-8')
            print(f"个股与行业指数相关性数据已保存至: {output_dir}/stock_index_correlation.csv")
            
            # 计算行业平均Beta值
            industry_beta = corr_df.groupby(['board_code', 'industry'])['beta'].mean().reset_index()
            industry_beta.to_csv(f"{output_dir}/industry_beta.csv", index=False, encoding='utf-8')
            print(f"行业平均Beta值已保存至: {output_dir}/industry_beta.csv")
    
    # 返回汇总数据
    summary = {
        'industry_stats': industry_stats,
        'industry_daily_stats': industry_daily_stats
    }
    
    # 生成总结报告
    print("\n分析总结:")
    # 找出表现最好和最差的行业
    best_industry = industry_daily_stats.sort_values('avg_daily_return', ascending=False).iloc[0]
    worst_industry = industry_daily_stats.sort_values('avg_daily_return').iloc[0]
    
    print(f"- 表现最好的行业: {best_industry['industry']}({best_industry['board_code']}) (日均收益率: {best_industry['avg_daily_return']:.2f}%)")
    print(f"- 表现最差的行业: {worst_industry['industry']}({worst_industry['board_code']}) (日均收益率: {worst_industry['avg_daily_return']:.2f}%)")
    
    # 找出最稳定的行业（波动率最小）
    most_stable = industry_daily_stats.sort_values('daily_volatility').iloc[0]
    print(f"- 最稳定的行业: {most_stable['industry']}({most_stable['board_code']}) (日波动率: {most_stable['daily_volatility']:.2f}%)")
    
    # 风险调整后表现最好的行业（夏普比率最高）
    best_sharpe = industry_daily_stats.sort_values('sharpe_ratio', ascending=False).iloc[0]
    print(f"- 风险调整后表现最好的行业: {best_sharpe['industry']}({best_sharpe['board_code']}) (夏普比率: {best_sharpe['sharpe_ratio']:.2f})")
    
    return summary


def merge_index_data(stock_data, index_data):
    """将行业指数数据合并到股票数据中，按照指定的列顺序排列"""
    if index_data.empty:
        print("警告：没有行业指数数据可合并")
        return stock_data
    
    # 记录合并前的信息
    print(f"合并前股票数据形状: {stock_data.shape}")
    print(f"合并前行业指数数据形状: {index_data.shape}")
    
    # 打印行业指数数据的前几行，用于调试
    print("行业指数数据前3行:")
    print(index_data.head(3).to_string())
    
    # 确保日期格式一致
    stock_data['date'] = pd.to_datetime(stock_data['date'])
    index_data['date'] = pd.to_datetime(index_data['date'])
    
    # 确保列名一致性
    # 处理股票数据中可能的列名差异
    if '股票代码' in stock_data.columns and 'stock_code' not in stock_data.columns:
        stock_data['stock_code'] = stock_data['股票代码']
    elif 'code' in stock_data.columns and 'stock_code' not in stock_data.columns:
        stock_data['stock_code'] = stock_data['code']
    
    # 检查行业指数数据中的列名
    print(f"行业指数数据列名: {index_data.columns.tolist()}")
    
    # 如果行业指数数据中已经有标准化的列名，则不需要重命名
    if 'open' in index_data.columns and 'close' in index_data.columns:
        print("行业指数数据已有标准化列名")
    else:
        # 确保行业指数数据中的列名符合预期
        index_columns_mapping = {
            '代码': 'code',
            '日期': 'date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '成交额': 'amount',
            '涨跌幅': 'pct_change'
        }
        
        # 重命名行业指数数据中的列
        rename_dict = {k: v for k, v in index_columns_mapping.items() if k in index_data.columns}
        if rename_dict:
            index_data = index_data.rename(columns=rename_dict)
            print(f"重命名后的行业指数数据列名: {index_data.columns.tolist()}")
    
    # 确保行业指数数据中有board_code列
    if 'board_code' not in index_data.columns and 'code' in index_data.columns:
        index_data['board_code'] = index_data['code']
    
    # 检查open和close列的值，确保它们正确
    if 'open' in index_data.columns and 'close' in index_data.columns:
        print("行业指数数据示例 (open vs close):")
        print(index_data[['date', 'open', 'close']].head(3).to_string())
    
    # 创建一个新的DataFrame，只包含我们需要的列
    index_columns = ['date', 'board_code', 'close', 'open', 'high', 'low', 'volume', 'amount', 'pct_change']
    index_data_selected = index_data[index_columns].copy()
    
    # 重命名行业指数数据列，添加idx_前缀（除了date和board_code）
    rename_dict = {col: f'idx_{col}' for col in index_columns if col not in ['date', 'board_code']}
    index_data_renamed = index_data_selected.rename(columns=rename_dict)
    
    print(f"行业指数数据包含以下列: {index_data_renamed.columns.tolist()}")
    
    # 根据日期和行业代码合并数据
    merged_data = pd.merge(
        stock_data,
        index_data_renamed,
        on=['date', 'board_code'],
        how='left'
    )
    
    # 检查合并后的数据
    print(f"合并后数据形状: {merged_data.shape}")
    
    # 检查是否有空值
    for col in merged_data.columns:
        null_count = merged_data[col].isnull().sum()
        if null_count > 0:
            print(f"列 '{col}' 有 {null_count} 个空值 (占比 {null_count/len(merged_data)*100:.2f}%)")
    
    # 按照指定的列顺序重排列
    desired_columns = [
        'stock_code', 'date', 'open', 'close', 'high', 'low', 'volume', 'amount', 
        'amplitude', 'pct_change', 'price_change', 'turnover_rate', 
        'forward_ret_1d', 'forward_ret_3d', 'forward_ret_5d', 
        'board_code', 'industry', 
        'idx_close', 'idx_open', 'idx_high', 'idx_low', 'idx_volume', 'idx_amount', 'idx_pct_change'
    ]
    
    # 只保留实际存在的列
    final_columns = [col for col in desired_columns if col in merged_data.columns]
    
    # 检查是否有缺失的列
    missing_columns = [col for col in desired_columns if col not in merged_data.columns]
    if missing_columns:
        print(f"警告: 以下列在合并后的数据中不存在: {missing_columns}")
    
    # 重排列
    merged_data = merged_data[final_columns]
    
    print(f"最终数据包含以下列: {merged_data.columns.tolist()}")
    
    return merged_data


def check_data_integrity(file_path):
    """检查数据文件的完整性，确保包含所有必要的列"""
    try:
        # 读取数据
        df = pd.read_csv(file_path)
        
        # 检查行数和列数
        print(f"\n数据完整性检查 - {file_path}:")
        print(f"总行数: {len(df)}")
        print(f"总列数: {len(df.columns)}")
        
        # 检查关键列是否存在
        key_cols = ['stock_code', 'date', 'open', 'close', 'high', 'low', 'volume', 
                    'amount', 'amplitude', 'pct_change', 'price_change', 'turnover_rate']
        
        missing_cols = [col for col in key_cols if col not in df.columns]
        if missing_cols:
            print(f"警告: 缺少关键列: {missing_cols}")
        else:
            print("所有关键列均存在")
        
        # 检查数据的完整性（无空值）
        for col in key_cols:
            if col in df.columns:
                null_count = df[col].isnull().sum()
                if null_count > 0:
                    print(f"警告: '{col}' 列有 {null_count} 个空值 (占比 {null_count/len(df)*100:.2f}%)")
        
        # 检查日期范围
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            print(f"日期范围: {df['date'].min()} 至 {df['date'].max()}")
        
        # 显示前5行数据示例（主要关注交易信息列）
        display_cols = ['stock_code', 'date', 'volume', 'amount', 'amplitude', 'pct_change', 'price_change']
        display_cols = [col for col in display_cols if col in df.columns]
        if display_cols:
            print("\n数据示例 (前5行):")
            print(df[display_cols].head(5).to_string())
        
        # 检查行业分布
        if 'board_code' in df.columns and 'industry' in df.columns:
            industry_counts = df.groupby(['board_code', 'industry'])['stock_code'].nunique()
            print("\n行业分布:")
            for (board_code, industry), count in industry_counts.items():
                print(f"- {industry}({board_code}): {count}只股票")
        
        return True
    except Exception as e:
        print(f"数据完整性检查失败: {e}")
        return False


def main():
    """主函数：获取股票数据并整理行业信息"""
    # 创建输出目录
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    # 定义日期范围（扩展到03.07以确保能计算02.28的t+5收益率）
    start_date = "20250201"
    end_date = "20250307"
    
    print(f"开始获取{start_date}至{end_date}的股票数据...")
    
    # 1. 从industry.md提取股票代码
    stock_codes = extract_stock_codes()
    print(f"已提取{len(stock_codes)}只股票代码")
    
    # 2. 获取股票市场数据
    try:
        stock_data = get_stock_data_akshare(stock_codes, start_date, end_date)
        save_data(stock_data, f"{output_dir}/stock_market_data.csv")
    
        # 3. 获取行业信息
        industry_mapping = load_industry_mapping()
        save_data(industry_mapping, f"{output_dir}/industry_mapping.csv")
    
        # 4. 整理行业数据
        organized_data = organize_industry_data(stock_data, industry_mapping)
        
        # 5. 获取申万行业指数
        board_codes = industry_mapping['board_code'].unique().tolist()
        print(f"需要获取{len(board_codes)}个行业指数的数据")
        
        try:
            index_data = get_index_data_akshare(board_codes, start_date, end_date)
            if not index_data.empty:
                save_data(index_data, f"{output_dir}/industry_index_data.csv")
                print("\n成功获取行业指数数据")
                print(f"- 指数数量: {index_data['board_code'].nunique()}")
                print(f"- 日期范围: {index_data['date'].min()} 至 {index_data['date'].max()}")
                
                # 6. 合并股票数据和行业指数数据
                final_data = merge_index_data(organized_data, index_data)
                save_data(final_data, f"{output_dir}/stock_industry_data.csv")
                print("已合并股票数据和行业指数数据")
            else:
                print("\n警告：未能获取到行业指数数据，仅保存股票数据")
                save_data(organized_data, f"{output_dir}/stock_industry_data.csv")
        except Exception as e:
            print(f"获取行业指数数据失败: {e}")
            # 如果获取指数数据失败，仍然保存股票数据
            save_data(organized_data, f"{output_dir}/stock_industry_data.csv")
    
        print("\n数据处理完成!")
        final_data = pd.read_csv(f"{output_dir}/stock_industry_data.csv")  # 重新加载以确保使用最终数据
        print(f"- 股票数量: {final_data['stock_code'].nunique()}")
        print(f"- 行业数量: {final_data['board_code'].nunique()}")
        print(f"- 日期范围: {pd.to_datetime(final_data['date']).min()} 至 {pd.to_datetime(final_data['date']).max()}")
        
        # 显示每个行业的股票数量
        industry_counts = final_data.groupby(['board_code', 'industry'])['stock_code'].nunique().reset_index()
        print("\n各行业股票数量:")
        for _, row in industry_counts.iterrows():
            print(f"- {row['industry']}({row['board_code']}): {row['stock_code']}只")
            
        # 计算一些基本统计数据
        print("\n基本统计数据:")
        print("- 平均收盘价: {:.2f}".format(final_data['close'].mean()))
        print("- 平均成交量: {:.2f}".format(final_data['volume'].mean()))
        print("- 平均涨跌幅: {:.2f}%".format(final_data['pct_change'].mean()))
        print("- 平均换手率: {:.2f}%".format(final_data['turnover_rate'].mean()))
        
        # 分析期间内股票表现
        print("\n统计日期区间内各行业股票表现:")
        industry_performance = final_data.groupby(['board_code', 'industry'])['pct_change'].mean().reset_index().sort_values('pct_change', ascending=False)
        for _, row in industry_performance.iterrows():
            print(f"- {row['industry']}({row['board_code']}): {row['pct_change']:.2f}%")
        
        # 7. 生成行业统计报告
        print("\n生成行业统计报告...")
        industry_report = generate_industry_report(final_data, output_dir)
        
        # 8. 最终数据完整性检查
        check_data_integrity(f"{output_dir}/stock_industry_data.csv")
        
    except Exception as e:
        import traceback
        print(f"执行过程中出错: {e}")
        print("\n详细错误信息:")
        traceback.print_exc()


if __name__ == "__main__":
    main()
