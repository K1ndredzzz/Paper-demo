import pandas as pd
import numpy as np
import re
import jieba
import os
from datetime import datetime
from tqdm import tqdm
import argparse

def preprocess_comments(raw_data_path, output_path):
    """
    股票评论数据预处理函数
    
    参数:
        raw_data_path: 原始评论数据CSV文件路径
        output_path: 处理后的数据保存路径
    
    返回:
        处理后的数据DataFrame
    """
    print(f"开始读取原始评论数据: {raw_data_path}")
    # 读取原始评论数据，确保stock_code和board_code保持为字符串
    df = pd.read_csv(raw_data_path, encoding='utf-8', dtype={'stock_code': str, 'board_code': str})
    print(f"原始数据包含 {len(df)} 条记录")
    
    # 检查必要的列是否存在
    required_columns = ['stock_code', 'date', 'time', 'content']
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"输入数据缺少必要的列: {col}")
    
    # 再次确保stock_code和board_code为字符串类型
    if 'stock_code' in df.columns:
        df['stock_code'] = df['stock_code'].astype(str)
    if 'board_code' in df.columns:
        df['board_code'] = df['board_code'].astype(str)
    
    # 重命名content列为comment，以便后续处理
    df = df.rename(columns={'content': 'comment'})
    
    # 数据清洗：移除特殊字符、多余空格等
    print("进行数据清洗...")
    df['clean_comment'] = df['comment'].astype(str)
    df['clean_comment'] = df['clean_comment'].apply(lambda x: re.sub(r'[^\w\s]', '', x))
    df['clean_comment'] = df['clean_comment'].apply(lambda x: re.sub(r'\s+', ' ', x.strip()))
    
    # 广告过滤：定义可能的广告关键词
    print("进行广告内容过滤...")
    ad_keywords = ['开户', '加微信', '加QQ', '电报群', '推荐股', '老师', '信号', '指导', 
                  '带飞', '操作建议', '直播间', '免费分析', '牛股', '加我', '联系我',
                  '加群', '入群', '炒股群', '荐股', '提供技术', '提供消息', '内部消息']
    
    def filter_ads(text):
        for keyword in ad_keywords:
            if keyword in text:
                return True
        return False
    
    # 过滤广告和短内容
    original_count = len(df)
    df = df[~df['clean_comment'].apply(filter_ads)]
    df = df[df['clean_comment'].str.len() >= 5]  # 过滤过短的评论
    print(f"过滤广告和短评论后，剩余 {len(df)} 条记录 (移除了 {original_count - len(df)} 条)")
    
    # 添加时间特征
    print("添加时间特征...")
    # 合并日期和时间，并转换为datetime格式
    df['timestamp'] = df.apply(lambda row: f"{row['date']} {row['time']}", axis=1)
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    
    # 提取日期和小时信息
    df['date'] = df['timestamp'].dt.date
    df['hour'] = df['timestamp'].dt.hour
    df['dayofweek'] = df['timestamp'].dt.dayofweek  # 0=周一，6=周日
    
    # 处理缺失的时间戳
    missing_timestamp = df['timestamp'].isna().sum()
    if missing_timestamp > 0:
        print(f"警告: 有 {missing_timestamp} 条记录的时间戳格式无效，这些记录将使用原始date字段")
        df.loc[df['timestamp'].isna(), 'date'] = pd.to_datetime(df.loc[df['timestamp'].isna(), 'date']).dt.date
    
    # 分词处理
    print("进行中文分词...")
    # 添加金融领域的自定义词典（如果存在）
    if os.path.exists('finance_dict.txt'):
        jieba.load_userdict('finance_dict.txt')
        print("已加载金融领域自定义词典")
    
    # 使用tqdm显示分词进度
    tqdm.pandas(desc="分词处理")
    df['tokens'] = df['clean_comment'].progress_apply(lambda x: ' '.join(jieba.cut(x)))
    
    # 统计评论的基本信息
    df['comment_length'] = df['clean_comment'].apply(len)
    df['token_count'] = df['tokens'].apply(lambda x: len(x.split()))
    
    # 统计每个股票的评论数量
    stock_comment_counts = df['stock_code'].value_counts()
    print("\n每个股票的评论数量统计 (Top 10):")
    print(stock_comment_counts.head(10))
    
    # 按日期统计评论数量
    date_comment_counts = df['date'].value_counts().sort_index()
    print("\n每日评论数量统计 (前5天):")
    print(date_comment_counts.head())
    
    # 保存处理后的数据，确保stock_code和board_code仍然为字符串
    print(f"保存处理后的数据至: {output_path}")
    df.to_csv(output_path, index=False, encoding='utf-8')
    
    print("数据预处理完成!")
    return df

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='股票评论数据预处理工具')
    parser.add_argument('--input', type=str, required=True, help='输入CSV文件路径')
    parser.add_argument('--output', type=str, default='processed_comments.csv', help='输出CSV文件路径')
    args = parser.parse_args()
    
    # 执行预处理
    preprocess_comments(args.input, args.output)

if __name__ == "__main__":
    main() 