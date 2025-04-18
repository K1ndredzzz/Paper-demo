import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
import os
from datetime import datetime
import jieba.analyse
from wordcloud import WordCloud

def analyze_processed_data(data_path):
    """
    分析处理后的评论数据
    
    参数:
        data_path: 处理后的数据文件路径
    """
    print(f"读取处理后的数据: {data_path}")
    # 读取数据，确保stock_code和board_code保持为字符串
    df = pd.read_csv(data_path, encoding='utf-8', dtype={'stock_code': str, 'board_code': str})
    print(f"数据包含 {len(df)} 条记录，{df['stock_code'].nunique()} 只股票")
    
    # 创建输出目录
    output_dir = 'analysis_results'
    os.makedirs(output_dir, exist_ok=True)
    
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
    plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
    
    # 1. 评论长度分布
    plt.figure(figsize=(8, 6))
    sns.histplot(df['comment_length'], bins=50)
    plt.title('评论长度分布')
    plt.xlabel('评论长度（字符数）')
    plt.ylabel('频率')
    plt.savefig(f'{output_dir}/comment_length_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 2. 评论时间分布
    df['date'] = pd.to_datetime(df['date'])
    daily_counts = df.groupby(df['date'].dt.date).size()
    
    plt.figure(figsize=(8, 6))
    daily_counts.plot(kind='bar')
    plt.title('每日评论数量')
    plt.xlabel('日期')
    plt.ylabel('评论数量')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/daily_comment_counts.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 3. 每小时评论分布
    hourly_counts = df.groupby('hour').size()
    
    plt.figure(figsize=(8, 6))
    hourly_counts.plot(kind='bar')
    plt.title('每小时评论数量')
    plt.xlabel('小时')
    plt.ylabel('评论数量')
    plt.xticks(range(24))
    plt.savefig(f'{output_dir}/hourly_comment_counts.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 4. 热门股票评论数量
    stock_counts = df['stock_code'].value_counts().head(20)
    
    plt.figure(figsize=(8, 6))
    stock_counts.plot(kind='bar')
    plt.title('热门股票评论数量 (Top 20)')
    plt.xlabel('股票代码')
    plt.ylabel('评论数量')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/top_stocks_comment_counts.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 5. 提取关键词
    all_comments = ' '.join(df['clean_comment'].astype(str))
    keywords = jieba.analyse.extract_tags(all_comments, topK=50, withWeight=True)
    
    keywords_df = pd.DataFrame(keywords, columns=['keyword', 'weight'])
    plt.figure(figsize=(8, 6))
    sns.barplot(x='weight', y='keyword', data=keywords_df.sort_values('weight', ascending=False))
    plt.title('评论关键词权重 (Top 50)')
    plt.xlabel('权重')
    plt.ylabel('关键词')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/keywords_weight.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 6. 不同股票每日评论数变化
    top_stocks = stock_counts.index[:5]  # 取前5只热门股票
    
    plt.figure(figsize=(8, 6))
    for stock in top_stocks:
        stock_data = df[df['stock_code'] == stock]
        daily_stock_counts = stock_data.groupby(stock_data['date'].dt.date).size()
        plt.plot(daily_stock_counts.index, daily_stock_counts.values, label=stock)
    
    plt.title('热门股票每日评论数变化')
    plt.xlabel('日期')
    plt.ylabel('评论数量')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/top_stocks_daily_trend.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 生成词云
    word_freq = dict(keywords)
    try:
        # 尝试使用指定字体
        wc = WordCloud(
            font_path='simhei.ttf',  # 使用黑体
            width=1200,
            height=800,
            background_color='white',
            max_words=200,
            max_font_size=100,
            random_state=42,
            collocations=False,  # 避免重复词组
            contour_width=1,
            contour_color='steelblue'
        )
    except Exception as e:
        print(f"使用指定字体失败: {e}，尝试使用系统字体")
        # 如果指定字体失败，尝试使用系统字体
        wc = WordCloud(
            width=1200,
            height=800,
            background_color='white',
            max_words=200,
            max_font_size=100,
            random_state=42,
            collocations=False,
            contour_width=1,
            contour_color='steelblue'
        )
    
    # 生成主要词云
    wc.generate_from_frequencies(word_freq)
    
    plt.figure(figsize=(8, 6))
    plt.imshow(wc, interpolation='bilinear')
    plt.axis('off')
    plt.title('评论关键词词云')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/word_cloud.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 生成按股票分类的词云
    for stock_code in top_stocks:
        stock_comments = ' '.join(df[df['stock_code'] == stock_code]['clean_comment'].astype(str))
        if len(stock_comments) > 100:  # 确保有足够的文本
            stock_keywords = jieba.analyse.extract_tags(stock_comments, topK=100, withWeight=True)
            stock_word_freq = dict(stock_keywords)
            
            try:
                stock_wc = WordCloud(
                    font_path='simhei.ttf',
                    width=1000,
                    height=700,
                    background_color='white',
                    max_words=100,
                    max_font_size=100,
                    random_state=42,
                    collocations=False
                ).generate_from_frequencies(stock_word_freq)
                
                plt.figure(figsize=(8, 6))
                plt.imshow(stock_wc, interpolation='bilinear')
                plt.axis('off')
                plt.title(f'股票 {stock_code} 评论关键词词云')
                plt.tight_layout()
                plt.savefig(f'{output_dir}/word_cloud_{stock_code}.png', dpi=300, bbox_inches='tight')
                plt.close()
            except Exception as e:
                print(f"生成股票 {stock_code} 词云失败: {e}")
    
    print(f"分析完成，结果保存在 {output_dir} 目录")
    
    # 返回一些基本统计信息
    return {
        "评论总数": len(df),
        "股票数量": df['stock_code'].nunique(),
        "日期范围": f"{df['date'].min().date()} 至 {df['date'].max().date()}",
        "平均每日评论数": daily_counts.mean(),
        "评论高峰时段": hourly_counts.idxmax(),
        "热门股票": stock_counts.head(5).to_dict()
    }

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='预处理后的股票评论数据分析工具')
    parser.add_argument('--input', type=str, required=True, help='处理后的评论数据CSV文件路径')
    args = parser.parse_args()
    
    # 分析数据
    stats = analyze_processed_data(args.input)
    
    # 打印基本统计信息
    print("\n基本统计信息:")
    for key, value in stats.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    main() 