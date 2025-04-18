import pandas as pd
from sentiment_analyzer import StockSentimentAnalyzer
import argparse
from tqdm import tqdm

def apply_sentiment_analysis(comments_df, analyzer):
    """
    对评论数据应用情感分析模型
    
    Args:
        comments_df: 包含评论的DataFrame
        analyzer: 情感分析器实例
    
    Returns:
        添加了情感分析结果的DataFrame
    """
    # 获取评论文本列表
    comments = comments_df['comment'].tolist()
    
    # 批量进行情感分析
    print("开始情感分析...")
    sentiment_results = analyzer.predict_batch(comments)
    
    # 计算情感统计信息
    stats = analyzer.analyze_sentiment_statistics(sentiment_results)
    print("\n=== 情感分析统计信息 ===")
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"{key}: {value:.2f}")
        else:
            print(f"{key}: {value}")
    
    # 将情感分析结果添加到DataFrame
    comments_df['sentiment_score'] = [r['score'] for r in sentiment_results]
    comments_df['sentiment_polarity'] = [r['polarity'] for r in sentiment_results]
    comments_df['sentiment_intensity'] = [r['intensity'] for r in sentiment_results]
    comments_df['positive_prob'] = [r['positive_prob'] for r in sentiment_results]
    comments_df['negative_prob'] = [r['negative_prob'] for r in sentiment_results]
    
    return comments_df

def process_stock_comments(input_file, output_file=None):
    """
    处理股票评论数据并进行情感分析
    
    Args:
        input_file: 输入CSV文件路径
        output_file: 输出CSV文件路径
    """
    # 加载数据
    print(f"加载评论数据: {input_file}")
    comments_df = pd.read_csv(input_file, dtype={'stock_code': str})
    
    # 确保数据格式正确
    required_cols = ['stock_code', 'date', 'board_code', 'source_type', 'comment']
    for col in required_cols:
        if col not in comments_df.columns:
            raise ValueError(f"输入数据缺少必要列: {col}")
    
    # 初始化情感分析器
    print("初始化情感分析模型...")
    analyzer = StockSentimentAnalyzer()
    
    # 应用情感分析
    result_df = apply_sentiment_analysis(comments_df, analyzer)
    
    # 保存结果
    if output_file:
        result_df.to_csv(output_file, index=False)
        print(f"分析结果已保存至: {output_file}")
    
    return result_df

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='股票评论情感分析')
    parser.add_argument('--input', required=True, help='输入评论CSV文件路径')
    parser.add_argument('--output', default='sentiment_results.csv', help='输出结果CSV文件路径')
    
    args = parser.parse_args()
    
    # 处理评论数据
    process_stock_comments(args.input, args.output)

if __name__ == "__main__":
    main() 