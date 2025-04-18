import pandas as pd
import argparse

def aggregate_sentiment_by_stock(comments_with_sentiment, output_file=None):
    """
    按股票代码整合情感分析结果
    
    Args:
        comments_with_sentiment: 带有情感分析结果的DataFrame
        output_file: 输出CSV文件路径
        
    Returns:
        按股票和日期汇总的情感指标DataFrame
    """
    # 按股票代码和日期分组
    grouped = comments_with_sentiment.groupby(['stock_code', 'date'])
    
    # 计算汇总指标
    sentiment_summary = grouped.agg(
        avg_score=('sentiment_score', 'mean'),
        sentiment_std=('sentiment_score', 'std'),
        positive_ratio=('sentiment_polarity', lambda x: sum(x == 1) / len(x) if len(x) > 0 else 0),
        negative_ratio=('sentiment_polarity', lambda x: sum(x == -1) / len(x) if len(x) > 0 else 0),
        avg_intensity=('sentiment_intensity', 'mean'),
        comment_count=('sentiment_score', 'count')
    ).reset_index()
    
    # 计算情感净值
    sentiment_summary['sentiment_net'] = sentiment_summary['positive_ratio'] - sentiment_summary['negative_ratio']
    
    # 填充可能的缺失值
    sentiment_summary = sentiment_summary.fillna({
        'sentiment_std': 0,
        'avg_intensity': 0
    })
    
    # 保存结果
    if output_file:
        sentiment_summary.to_csv(output_file, index=False)
        print(f"汇总情感数据已保存至: {output_file}")
    
    return sentiment_summary

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='股票评论情感数据整合')
    parser.add_argument('--input', required=True, help='带情感分析结果的CSV文件路径')
    parser.add_argument('--output', default='sentiment_summary.csv', help='输出汇总CSV文件路径')
    
    args = parser.parse_args()
    
    # 加载数据
    df = pd.read_csv(args.input, dtype={'stock_code': str})
    
    # 整合数据
    aggregate_sentiment_by_stock(df, args.output)

if __name__ == "__main__":
    main() 