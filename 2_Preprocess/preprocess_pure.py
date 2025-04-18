import pandas as pd
import numpy as np
import re
import os
from datetime import datetime
from tqdm import tqdm
import argparse

def preprocess_comments_pure(raw_data_path, output_path):
    """
    股票评论数据简单预处理函数 - 只进行数据清洗，不进行分词
    
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
    required_columns = ['stock_code', 'date']
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"输入数据缺少必要的列: {col}")
    
    # 确保stock_code和board_code为字符串类型
    if 'stock_code' in df.columns:
        df['stock_code'] = df['stock_code'].astype(str)
    if 'board_code' in df.columns:
        df['board_code'] = df['board_code'].astype(str)
    
    # 如果有content列但没有comment列，重命名content列为comment
    if 'content' in df.columns and 'comment' not in df.columns:
        df = df.rename(columns={'content': 'comment'})
    
    # 确保comment列存在
    if 'comment' not in df.columns:
        print("警告: 数据中没有comment或content列，将创建空列")
        df['comment'] = ''
    
    # 数据清洗：移除特殊字符、多余空格等
    print("进行数据清洗...")
    df['comment'] = df['comment'].astype(str)
    
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
    df = df[~df['comment'].apply(filter_ads)]
    df = df[df['comment'].str.len() >= 5]  # 过滤过短的评论
    print(f"过滤广告和短评论后，剩余 {len(df)} 条记录 (移除了 {original_count - len(df)} 条)")
    
    # 处理日期格式
    print("处理日期格式...")
    # 将日期转换为datetime格式
    df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.date
    
    # 处理缺失的日期
    missing_date = df['date'].isna().sum()
    if missing_date > 0:
        print(f"警告: 有 {missing_date} 条记录的日期格式无效，这些记录将被移除")
        df = df.dropna(subset=['date'])
    
    # 确保所有需要的列都存在
    columns_to_keep = ['stock_code', 'date', 'board_code', 'source_type', 'comment']
    
    # 检查并处理可能缺失的列
    for col in columns_to_keep:
        if col not in df.columns:
            if col == 'source_type' and 'source' in df.columns:
                df['source_type'] = df['source']
            elif col != 'stock_code' and col != 'date':  # stock_code和date是必须的，其他可以为空
                print(f"警告: 列 '{col}' 不存在，将创建空列")
                df[col] = ''
    
    # 统计每个股票的评论数量
    stock_comment_counts = df['stock_code'].value_counts()
    print("\n每个股票的评论数量统计 (Top 10):")
    print(stock_comment_counts.head(10))
    
    # 按日期统计评论数量
    date_comment_counts = df['date'].value_counts().sort_index()
    print("\n每日评论数量统计 (前5天):")
    print(date_comment_counts.head())
    
    # 只保留需要的列
    df = df[columns_to_keep]
    
    # 保存处理后的数据
    print(f"保存处理后的数据至: {output_path}")
    df.to_csv(output_path, index=False, encoding='utf-8')
    
    print("数据预处理完成!")
    return df

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='股票评论数据简单预处理工具 - 只进行数据清洗')
    parser.add_argument('--input', type=str, required=True, help='输入CSV文件路径')
    parser.add_argument('--output', type=str, default='processed_pure_comments.csv', help='输出CSV文件路径')
    args = parser.parse_args()
    
    # 执行预处理
    preprocess_comments_pure(args.input, args.output)

if __name__ == "__main__":
    main() 