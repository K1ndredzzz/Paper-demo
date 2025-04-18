import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import argparse

def visualize_sentiment_distribution(comments_with_sentiment, output_path='sentiment_distribution.png'):
    """
    可视化情感分布
    
    Args:
        comments_with_sentiment: 带有情感分析结果的DataFrame
        output_path: 输出图片路径
    """
    # 设置中文字体
    try:
        plt.rcParams['font.sans-serif'] = ['WenQuanYi Zen Hei', 'sans-serif']  # 使用文泉驿正黑, 如果找不到则使用系统默认 sans-serif
        plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
    except:
        print("警告: 未能正确设置中文字体，图表中的中文可能无法正确显示")
    
    # 创建图表
    plt.figure(figsize=(10, 8))
    
    # 绘制情感得分直方图
    plt.subplot(2, 1, 1)
    sns.histplot(comments_with_sentiment['sentiment_score'], kde=True, bins=30)
    plt.title('评论情感得分分布')
    plt.xlabel('情感得分')
    plt.ylabel('频率')
    
    # 绘制情感极性饼图
    plt.subplot(2, 2, 3)
    polarity_counts = comments_with_sentiment['sentiment_polarity'].value_counts()
    labels = ['负面' if p == -1 else '正面' if p == 1 else '中性' for p in polarity_counts.index]
    plt.pie(polarity_counts, labels=labels, autopct='%1.1f%%', startangle=90, colors=['#FF9999', '#99FF99'])
    plt.axis('equal')
    plt.title('情感极性分布')
    
    # 绘制情感强度箱线图
    plt.subplot(2, 2, 4)
    sns.boxplot(x='sentiment_polarity', y='sentiment_intensity', 
                data=comments_with_sentiment[comments_with_sentiment['sentiment_polarity'] != 0])
    plt.xticks([-1, 1], ['负面', '正面'])
    plt.title('不同极性的情感强度分布')
    plt.xlabel('情感极性')
    plt.ylabel('情感强度')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"情感分布图表已保存至: {output_path}")

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='股票评论情感分布可视化')
    parser.add_argument('--input', required=True, help='带情感分析结果的CSV文件路径')
    parser.add_argument('--output', default='sentiment_distribution.png', help='输出图片路径')
    
    args = parser.parse_args()
    
    # 加载数据
    df = pd.read_csv(args.input)
    
    # 可视化
    visualize_sentiment_distribution(df, args.output)

if __name__ == "__main__":
    main() 