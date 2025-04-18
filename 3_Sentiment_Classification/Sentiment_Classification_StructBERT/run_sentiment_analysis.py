import pandas as pd
from sentiment_analyzer import StockSentimentAnalyzer
from visualize_sentiment import visualize_sentiment_distribution
from aggregate_sentiment import aggregate_sentiment_by_stock
from apply_sentiment import apply_sentiment_analysis
import argparse
import os

def run_complete_analysis(input_file, output_dir='./output', step=None):
    """
    运行股票评论情感分析流程，可分步骤执行

    Args:
        input_file: 输入评论CSV文件路径
        output_dir: 输出目录
        step: 指定要执行的步骤，可选值: '1', '2', 'all', None。
              '1': 仅生成 sentiment_results.csv
              '2': 仅生成 sentiment_distribution.png 和 sentiment_summary.csv (依赖 sentiment_results.csv)
              'all' 或 None: 执行所有步骤
    """
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    if step in ['1', 'all', None]:
        # 步骤 1: 应用情感分析并保存结果
        print("\n=== 步骤 1: 情感分析 ===")
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
        result_output = os.path.join(output_dir, 'sentiment_results.csv')
        result_df.to_csv(result_output, index=False)
        print(f"情感分析结果已保存至: {result_output}")
    else:
        print("跳过步骤 1: 情感分析")
        result_output = os.path.join(output_dir, 'sentiment_results.csv')
        if not os.path.exists(result_output):
            raise FileNotFoundError(f"找不到情感分析结果文件: {result_output}。请先执行步骤 1。")
        result_df = pd.read_csv(result_output, dtype={'stock_code': str})


    if step in ['2', 'all', None]:
        # 步骤 2: 生成可视化和汇总数据
        print("\n=== 步骤 2: 可视化和数据整合 ===")

        # 确保 result_df 已经被加载 (如果只运行步骤2，则从文件加载)
        if 'result_df' not in locals():
            result_output = os.path.join(output_dir, 'sentiment_results.csv')
            if not os.path.exists(result_output):
                raise FileNotFoundError(f"找不到情感分析结果文件: {result_output}。请先执行步骤 1。")
            result_df = pd.read_csv(result_output, dtype={'stock_code': str})


        # 生成情感分布可视化
        print("生成情感分布可视化...")
        viz_output = os.path.join(output_dir, 'sentiment_distribution.png')
        visualize_sentiment_distribution(result_df, viz_output)

        # 整合按股票和日期的情感数据
        print("整合情感数据...")
        summary_output = os.path.join(output_dir, 'sentiment_summary.csv')
        aggregate_sentiment_by_stock(result_df, summary_output)
        print(f"情感数据汇总结果已保存至: {summary_output}")

    else:
        print("跳过步骤 2: 可视化和数据整合")

    print(f"分析完成！结果已保存至目录: {output_dir}")


def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='股票评论情感分析流程，可分步骤执行')
    parser.add_argument('--input', required=True, help='输入评论CSV文件路径')
    parser.add_argument('--output_dir', default='./sentiment_output', help='输出目录')
    parser.add_argument('--step', type=str, default=None, choices=['1', '2', 'all'],
                        help="指定运行步骤: '1' (仅情感分析), '2' (仅可视化和整合), 'all' (全部), 默认执行全部")

    args = parser.parse_args()

    # 运行完整分析
    run_complete_analysis(args.input, args.output_dir, step=args.step)

if __name__ == "__main__":
    main() 