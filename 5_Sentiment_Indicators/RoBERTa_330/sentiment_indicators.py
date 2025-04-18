import pandas as pd
import numpy as np
import os
from tqdm import tqdm
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def filter_trading_days(df):
    """过滤非交易日数据"""
    # 确保日期列是datetime类型
    df['date'] = pd.to_datetime(df['date'])
    
    # 获取所有交易日
    trading_days = df[df['close'].notna()]['date'].unique()
    
    # 只保留交易日的数据
    df = df[df['date'].isin(trading_days)]
    
    return df

def calculate_stock_level_indicators(sentiment_df, market_df):
    """计算个股层面的情绪指标"""
    try:
        logger.info("开始计算个股情绪指标...")
        
        # 确保stock_code为字符串类型
        sentiment_df['stock_code'] = sentiment_df['stock_code'].astype(str).str.zfill(6)
        market_df['stock_code'] = market_df['stock_code'].astype(str).str.zfill(6)
        
        # 过滤非交易日数据
        market_df = filter_trading_days(market_df)
        sentiment_df = sentiment_df[sentiment_df['date'].isin(market_df['date'].unique())]
        
        # 按股票和日期分组计算情绪指标
        stock_sentiment = sentiment_df.groupby(['stock_code', 'date']).agg(
            avg_sentiment=('sentiment_score', 'mean'),
            sentiment_std=('sentiment_score', 'std'),
            positive_ratio=('sentiment_polarity', lambda x: sum(x == 1) / len(x) if len(x) > 0 else 0),
            negative_ratio=('sentiment_polarity', lambda x: sum(x == -1) / len(x) if len(x) > 0 else 0),
            avg_intensity=('sentiment_intensity', 'mean'),
            comment_count=('sentiment_score', 'count'),
            avg_positive_prob=('positive_prob', 'mean'),
            avg_negative_prob=('negative_prob', 'mean')
        ).reset_index()
        
        logger.info(f"计算得到 {len(stock_sentiment)} 条个股情绪记录")
        
        # 计算情绪净值和一致性
        stock_sentiment['sentiment_net'] = stock_sentiment['positive_ratio'] - stock_sentiment['negative_ratio']
        stock_sentiment['sentiment_consensus'] = 1 - stock_sentiment[['positive_ratio', 'negative_ratio']].std(axis=1)
        
        # 按股票分组计算动量指标
        stock_sentiment = stock_sentiment.sort_values(['stock_code', 'date'])
        
        # 添加动量指标
        for window in [3, 5, 10]:
            # 对每个股票分别计算移动平均
            ma_values = []
            std_values = []
            change_values = []
            
            for _, group in stock_sentiment.groupby('stock_code'):
                ma = group['avg_sentiment'].rolling(window=window, min_periods=1).mean()
                std = group['avg_sentiment'].rolling(window=window, min_periods=1).std()
                change = group['avg_sentiment'].pct_change(periods=window)
                
                ma_values.extend(ma.values)
                std_values.extend(std.values)
                change_values.extend(change.values)
            
            stock_sentiment[f'ma_{window}d'] = ma_values
            stock_sentiment[f'std_{window}d'] = std_values
            stock_sentiment[f'sentiment_change_{window}d'] = change_values
        
        # 合并市场数据
        logger.info("合并市场数据...")
        stock_daily = pd.merge(
            stock_sentiment,
            market_df[[
                'stock_code', 'date', 
                'open', 'close', 'high', 'low', 'volume', 'amount', 'amplitude', 'pct_change', 'price_change','turnover_rate',
                'industry', 'board_code', 'idx_close', 'idx_volume', 'idx_amount', 'idx_pct_change', 
                'forward_ret_1d', 'forward_ret_3d', 'forward_ret_5d'
            ]],
            on=['stock_code', 'date'],
            how='left'
        )
        
        logger.info(f"合并后得到 {len(stock_daily)} 条记录")
        return stock_daily
        
    except Exception as e:
        logger.error(f"计算个股情绪指标时出错: {str(e)}")
        raise

def calculate_industry_level_indicators(stock_daily, market_df):
    """计算行业层面的情绪指标"""
    try:
        logger.info("开始计算行业情绪指标...")
        
        # 确保board_code为字符串类型
        stock_daily['board_code'] = stock_daily['board_code'].astype(str)
        market_df['board_code'] = market_df['board_code'].astype(str)
        
        # 按行业和日期分组计算行业情绪指标
        industry_daily = stock_daily.groupby(['board_code', 'date']).agg(
            # 情绪指标
            ind_avg_sentiment=('avg_sentiment', 'mean'),
            ind_sentiment_std=('avg_sentiment', 'std'),
            ind_positive_ratio=('positive_ratio', 'mean'),
            ind_negative_ratio=('negative_ratio', 'mean'),
            ind_sentiment_net=('sentiment_net', 'mean'),
            ind_sentiment_consensus=('sentiment_consensus', 'mean'),
                        
            # 股票覆盖
            stock_count=('stock_code', 'nunique'),
            total_comments=('comment_count', 'sum')
        ).reset_index()
        
        logger.info(f"计算得到 {len(industry_daily)} 条行业情绪记录")
        
        # 计算行业情绪分散度
        industry_daily['sentiment_dispersion'] = industry_daily['ind_sentiment_std'] / abs(industry_daily['ind_avg_sentiment'])
        
        # 合并行业指数数据
        logger.info("合并行业指数数据...")
        industry_daily = pd.merge(
            industry_daily,
            market_df[[
                'date', 'board_code', 
                'idx_close', 'idx_open', 'idx_high', 'idx_low','idx_volume', 'idx_amount', 'idx_pct_change'
            ]].drop_duplicates(),
            on=['board_code', 'date'],
            how='left'
        )
        
        # 计算行业情绪动量
        industry_daily = industry_daily.sort_values(['board_code', 'date'])
        
        # 添加行业动量指标
        for window in [3, 5, 10]:
            # 对每个行业分别计算移动平均
            ma_values = []
            change_values = []
            
            for _, group in industry_daily.groupby('board_code'):
                ma = group['ind_avg_sentiment'].rolling(window=window, min_periods=1).mean()
                change = group['ind_avg_sentiment'].pct_change(periods=window)
                
                ma_values.extend(ma.values)
                change_values.extend(change.values)
            
            industry_daily[f'ind_ma_{window}d'] = ma_values
            industry_daily[f'ind_sentiment_change_{window}d'] = change_values
        
        logger.info(f"最终得到 {len(industry_daily)} 条行业情绪记录")
        return industry_daily
        
    except Exception as e:
        logger.error(f"计算行业情绪指标时出错: {str(e)}")
        raise

def build_sentiment_indicators(sentiment_results_path, merged_market_path, output_dir='./output'):
    """
    构建个股和行业层面的情绪指标，并输出为两个CSV文件
    
    Args:
        sentiment_results_path (str): 情感分析结果文件路径
        merged_market_path (str): 合并市场数据文件路径
        output_dir (str): 输出目录
    
    Returns:
        tuple: (个股数据文件路径, 行业数据文件路径)
    """
    try:
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        logger.info("开始构建情绪指标...")
        
        # 读取原始数据，确保stock_code和board_code为字符串类型
        logger.info(f"读取情感分析结果文件: {sentiment_results_path}")
        sentiment_df = pd.read_csv(sentiment_results_path, dtype={'stock_code': str, 'board_code': str})
        logger.info(f"读取市场数据文件: {merged_market_path}")
        market_df = pd.read_csv(merged_market_path, dtype={'stock_code': str, 'board_code': str})
        
        # 确保日期格式一致
        for df in [sentiment_df, market_df]:
            df['date'] = pd.to_datetime(df['date'])
        
        # 1. 构建个股日度数据
        logger.info("构建个股情绪指标...")
        stock_daily_data = calculate_stock_level_indicators(sentiment_df, market_df)
        
        # 2. 构建行业日度数据
        logger.info("构建行业情绪指标...")
        industry_daily_data = calculate_industry_level_indicators(stock_daily_data, market_df)
        
        # 保存结果
        stock_output_path = os.path.join(output_dir, 'stock_daily_sentiment.csv')
        industry_output_path = os.path.join(output_dir, 'industry_daily_sentiment.csv')
        
        logger.info(f"保存个股数据至: {stock_output_path}")
        stock_daily_data.to_csv(stock_output_path, index=False)
        
        logger.info(f"保存行业数据至: {industry_output_path}")
        industry_daily_data.to_csv(industry_output_path, index=False)
        
        logger.info("情绪指标构建完成!")
        return stock_output_path, industry_output_path
        
    except Exception as e:
        logger.error(f"构建情绪指标时出错: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        # 设置输入输出路径
        sentiment_results_path = "sentiment_results.csv"
        merged_market_path = "merged_stock_industry_index.csv"
        output_dir = "./output"
        
        # 检查输入文件是否存在
        if not os.path.exists(sentiment_results_path):
            raise FileNotFoundError(f"情感分析结果文件不存在: {sentiment_results_path}")
        if not os.path.exists(merged_market_path):
            raise FileNotFoundError(f"市场数据文件不存在: {merged_market_path}")
        
        # 运行情绪指标构建
        stock_file, industry_file = build_sentiment_indicators(
            sentiment_results_path,
            merged_market_path,
            output_dir
        )
        
    except Exception as e:
        logger.error(f"程序执行出错: {str(e)}")
        raise 