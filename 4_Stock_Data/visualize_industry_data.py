#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
行业分析数据可视化脚本
用于生成各种行业分析图表，帮助理解行业表现和特征
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.font_manager import FontProperties
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter

# 设置中文字体
try:
    # 尝试使用微软雅黑字体
    font = FontProperties(fname=r"C:\Windows\Fonts\msyh.ttc", size=10)
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
except:
    print("警告: 无法加载微软雅黑字体，中文可能显示为方块")
    # 尝试使用其他方式解决中文显示问题
    plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
    plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

# 设置图表风格
sns.set(style="whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['figure.dpi'] = 100

# 创建输出目录
def create_output_dir(dir_name="figures"):
    """创建图表输出目录"""
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    return dir_name

# 加载数据
def load_data():
    """加载所有必要的数据文件"""
    data_files = {
        'stock_industry': 'output/merged_stock_industry_index.csv',
        'industry_stats': 'output/industry_statistics.csv',
        'industry_corr': 'output/industry_correlation.csv',
        'industry_daily': 'output/industry_daily_stats.csv',
        'stock_index_corr': 'output/stock_index_correlation.csv',
        'industry_beta': 'output/industry_beta.csv'
    }
    
    data = {}
    for key, file_path in data_files.items():
        try:
            data[key] = pd.read_csv(file_path)
            print(f"成功加载 {file_path}, 形状: {data[key].shape}")
        except Exception as e:
            print(f"无法加载 {file_path}: {e}")
            data[key] = None
    
    return data

# 绘制行业收益率对比图
def plot_industry_returns(data, output_dir):
    """绘制行业收益率对比图"""
    if data['industry_daily'] is None:
        print("无法绘制行业收益率对比图：缺少行业日均统计数据")
        return
    
    # 准备数据
    df = data['industry_daily'].sort_values('avg_daily_return', ascending=False)
    
    # 检查收益率数据是否已经是百分比形式
    # 查看第一个值的大小来判断，如果小于0.1，则可能是小数形式（如0.01表示1%）
    sample_value = df['avg_daily_return'].iloc[0] if len(df) > 0 else 0
    scale_factor = 1 if abs(sample_value) > 0.1 else 100  # 如果已经是百分比形式，则不再乘以100
    
    # 创建图表
    plt.figure(figsize=(12, 8))
    bars = plt.bar(df['industry'], df['avg_daily_return'] * scale_factor, color=sns.color_palette("viridis", len(df)))
    
    # 添加数据标签
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                 f'{height:.2f}%', ha='center', va='bottom')
    
    # 设置标题和标签
    plt.title('各行业平均日收益率对比', fontproperties=font, fontsize=16)
    plt.xlabel('行业', fontproperties=font, fontsize=12)
    plt.ylabel('平均日收益率 (%)', fontproperties=font, fontsize=12)
    plt.xticks(rotation=45, ha='right', fontproperties=font)
    plt.tight_layout()
    
    # 保存图表
    plt.savefig(f"{output_dir}/industry_returns.png")
    plt.close()
    print(f"行业收益率对比图已保存至 {output_dir}/industry_returns.png")

# 绘制行业波动率对比图
def plot_industry_volatility(data, output_dir):
    """绘制行业波动率对比图"""
    if data['industry_daily'] is None:
        print("无法绘制行业波动率对比图：缺少行业日均统计数据")
        return
    
    # 准备数据
    df = data['industry_daily'].sort_values('daily_volatility')
    
    # 检查波动率数据是否已经是百分比形式
    sample_value = df['daily_volatility'].iloc[0] if len(df) > 0 else 0
    scale_factor = 1 if abs(sample_value) > 0.1 else 100  # 如果已经是百分比形式，则不再乘以100
    
    # 创建图表
    plt.figure(figsize=(12, 8))
    bars = plt.bar(df['industry'], df['daily_volatility'] * scale_factor, color=sns.color_palette("rocket", len(df)))
    
    # 添加数据标签
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                 f'{height:.2f}%', ha='center', va='bottom')
    
    # 设置标题和标签
    plt.title('各行业日波动率对比', fontproperties=font, fontsize=16)
    plt.xlabel('行业', fontproperties=font, fontsize=12)
    plt.ylabel('日波动率 (%)', fontproperties=font, fontsize=12)
    plt.xticks(rotation=45, ha='right', fontproperties=font)
    plt.tight_layout()
    
    # 保存图表
    plt.savefig(f"{output_dir}/industry_volatility.png")
    plt.close()
    print(f"行业波动率对比图已保存至 {output_dir}/industry_volatility.png")

# 绘制行业夏普比率对比图
def plot_industry_sharpe(data, output_dir):
    """绘制行业夏普比率对比图"""
    if data['industry_daily'] is None:
        print("无法绘制行业夏普比率对比图：缺少行业日均统计数据")
        return
    
    # 准备数据
    df = data['industry_daily'].sort_values('sharpe_ratio', ascending=False)
    
    # 创建图表
    plt.figure(figsize=(12, 8))
    bars = plt.bar(df['industry'], df['sharpe_ratio'], color=sns.color_palette("mako", len(df)))
    
    # 添加数据标签
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                 f'{height:.2f}', ha='center', va='bottom')
    
    # 设置标题和标签
    plt.title('各行业夏普比率对比', fontproperties=font, fontsize=16)
    plt.xlabel('行业', fontproperties=font, fontsize=12)
    plt.ylabel('夏普比率', fontproperties=font, fontsize=12)
    plt.xticks(rotation=45, ha='right', fontproperties=font)
    plt.tight_layout()
    
    # 保存图表
    plt.savefig(f"{output_dir}/industry_sharpe.png")
    plt.close()
    print(f"行业夏普比率对比图已保存至 {output_dir}/industry_sharpe.png")

# 绘制行业相关性热图
def plot_industry_correlation(data, output_dir):
    """绘制行业相关性热图"""
    if data['industry_corr'] is None or data['industry_stats'] is None:
        print("无法绘制行业相关性热图：缺少行业相关性数据或行业统计数据")
        return
    
    # 准备数据
    corr_matrix = data['industry_corr'].copy()
    
    # 获取行业代码和行业名称的映射
    industry_mapping = dict(zip(data['industry_stats']['board_code'], data['industry_stats']['industry']))
    
    # 将第一列作为索引（行业代码）
    if 'board_code' in corr_matrix.columns:
        # 删除第一行，因为它可能包含列名
        if corr_matrix.iloc[0, 0] == 'board_code':
            corr_matrix = corr_matrix.iloc[1:].copy()
        # 设置索引
        corr_matrix.set_index('board_code', inplace=True)
    
    # 确保索引和列都是字符串类型，以便进行映射
    corr_matrix.index = corr_matrix.index.astype(str)
    corr_matrix.columns = corr_matrix.columns.astype(str)
    
    # 将数据转换为浮点数
    for col in corr_matrix.columns:
        corr_matrix[col] = corr_matrix[col].astype(float)
    
    # 创建新的带有行业名称的DataFrame
    corr_names = pd.DataFrame(
        data=corr_matrix.values,
        index=[industry_mapping.get(idx, idx) for idx in corr_matrix.index],
        columns=[industry_mapping.get(col, col) for col in corr_matrix.columns]
    )
    
    # 创建图表
    plt.figure(figsize=(12, 10))
    mask = np.triu(np.ones_like(corr_names, dtype=bool))  # 创建上三角掩码
    
    # 绘制热图
    sns.heatmap(corr_names, annot=True, fmt=".2f", cmap="coolwarm", 
                mask=mask, vmin=-1, vmax=1, center=0,
                square=True, linewidths=.5, cbar_kws={"shrink": .8})
    
    # 设置标题和标签
    plt.title('行业收益率相关性热图', fontproperties=font, fontsize=16)
    plt.xticks(rotation=45, ha='right', fontproperties=font)
    plt.yticks(rotation=0, fontproperties=font)
    plt.tight_layout()
    
    # 保存图表
    plt.savefig(f"{output_dir}/industry_correlation.png")
    plt.close()
    print(f"行业相关性热图已保存至 {output_dir}/industry_correlation.png")

# 绘制行业Beta值对比图
def plot_industry_beta(data, output_dir):
    """绘制行业Beta值对比图"""
    if data['industry_beta'] is None:
        print("无法绘制行业Beta值对比图：缺少行业Beta值数据")
        return
    
    # 准备数据
    df = data['industry_beta'].sort_values('beta', ascending=False)
    
    # 创建图表
    plt.figure(figsize=(12, 8))
    bars = plt.bar(df['industry'], df['beta'], color=sns.color_palette("flare", len(df)))
    
    # 添加参考线
    plt.axhline(y=1.0, color='r', linestyle='--', alpha=0.7, label='市场Beta=1')
    
    # 添加数据标签
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                 f'{height:.2f}', ha='center', va='bottom')
    
    # 设置标题和标签
    plt.title('各行业平均Beta值对比', fontproperties=font, fontsize=16)
    plt.xlabel('行业', fontproperties=font, fontsize=12)
    plt.ylabel('Beta值', fontproperties=font, fontsize=12)
    plt.xticks(rotation=45, ha='right', fontproperties=font)
    plt.legend(prop=font)
    plt.tight_layout()
    
    # 保存图表
    plt.savefig(f"{output_dir}/industry_beta.png")
    plt.close()
    print(f"行业Beta值对比图已保存至 {output_dir}/industry_beta.png")

# 绘制行业指数走势图
def plot_industry_index_trends(data, output_dir):
    """绘制行业指数走势图"""
    if data['stock_industry'] is None:
        print("无法绘制行业指数走势图：缺少股票行业数据")
        return
    
    # 准备数据
    df = data['stock_industry'].copy()
    df['date'] = pd.to_datetime(df['date'])
    
    # 计算每个行业每天的平均指数收盘价
    industry_daily = df.groupby(['date', 'industry'])['idx_close'].mean().unstack()
    
    # 创建图表
    plt.figure(figsize=(14, 10))
    
    # 绘制每个行业的指数走势
    for industry in industry_daily.columns:
        plt.plot(industry_daily.index, industry_daily[industry], label=industry, linewidth=2)
    
    # 设置日期格式
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=5))
    
    # 设置标题和标签
    plt.title('各行业指数走势对比', fontproperties=font, fontsize=16)
    plt.xlabel('日期', fontproperties=font, fontsize=12)
    plt.ylabel('指数收盘价', fontproperties=font, fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.legend(prop=font, loc='upper left', bbox_to_anchor=(1, 1))
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # 保存图表
    plt.savefig(f"{output_dir}/industry_index_trends.png")
    plt.close()
    print(f"行业指数走势图已保存至 {output_dir}/industry_index_trends.png")

# 绘制行业成交量趋势图
def plot_industry_volume_trends(data, output_dir):
    """绘制行业成交量趋势图"""
    if data['stock_industry'] is None:
        print("无法绘制行业成交量趋势图：缺少股票行业数据")
        return
    
    # 准备数据
    df = data['stock_industry'].copy()
    df['date'] = pd.to_datetime(df['date'])
    
    # 计算每个行业每天的平均成交量
    industry_volume = df.groupby(['date', 'industry'])['idx_volume'].mean().unstack()
    
    # 创建图表
    plt.figure(figsize=(14, 10))
    
    # 绘制每个行业的成交量趋势
    for industry in industry_volume.columns:
        plt.plot(industry_volume.index, industry_volume[industry], label=industry, linewidth=2)
    
    # 设置日期格式
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=5))
    
    # 设置标题和标签
    plt.title('各行业成交量趋势对比', fontproperties=font, fontsize=16)
    plt.xlabel('日期', fontproperties=font, fontsize=12)
    plt.ylabel('成交量', fontproperties=font, fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.legend(prop=font, loc='upper left', bbox_to_anchor=(1, 1))
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # 保存图表
    plt.savefig(f"{output_dir}/industry_volume_trends.png")
    plt.close()
    print(f"行业成交量趋势图已保存至 {output_dir}/industry_volume_trends.png")

# 绘制个股与行业指数相关性分布图
def plot_stock_index_correlation(data, output_dir):
    """绘制个股与行业指数相关性分布图"""
    if data['stock_index_corr'] is None:
        print("无法绘制个股与行业指数相关性分布图：缺少相关性数据")
        return
    
    # 准备数据
    df = data['stock_index_corr'].copy()
    
    # 创建图表
    plt.figure(figsize=(14, 10))
    
    # 按行业分组绘制箱线图
    sns.boxplot(x='industry', y='correlation', data=df, palette="Set3")
    
    # 添加散点图显示每只股票的相关性
    sns.stripplot(x='industry', y='correlation', data=df, 
                 size=4, color=".3", linewidth=0, alpha=0.7)
    
    # 添加参考线
    plt.axhline(y=0.5, color='r', linestyle='--', alpha=0.7, label='相关性=0.5')
    plt.axhline(y=0.8, color='g', linestyle='--', alpha=0.7, label='相关性=0.8')
    
    # 设置标题和标签
    plt.title('个股与行业指数相关性分布', fontproperties=font, fontsize=16)
    plt.xlabel('行业', fontproperties=font, fontsize=12)
    plt.ylabel('相关性系数', fontproperties=font, fontsize=12)
    plt.xticks(rotation=45, ha='right', fontproperties=font)
    plt.legend(prop=font)
    plt.tight_layout()
    
    # 保存图表
    plt.savefig(f"{output_dir}/stock_index_correlation.png")
    plt.close()
    print(f"个股与行业指数相关性分布图已保存至 {output_dir}/stock_index_correlation.png")

# 绘制个股Beta值分布图
def plot_stock_beta_distribution(data, output_dir):
    """绘制个股Beta值分布图"""
    if data['stock_index_corr'] is None:
        print("无法绘制个股Beta值分布图：缺少相关性数据")
        return
    
    # 准备数据
    df = data['stock_index_corr'].copy()
    
    # 创建图表
    plt.figure(figsize=(14, 10))
    
    # 按行业分组绘制箱线图
    sns.boxplot(x='industry', y='beta', data=df, palette="Set2")
    
    # 添加散点图显示每只股票的Beta值
    sns.stripplot(x='industry', y='beta', data=df, 
                 size=4, color=".3", linewidth=0, alpha=0.7)
    
    # 添加参考线
    plt.axhline(y=1.0, color='r', linestyle='--', alpha=0.7, label='Beta=1')
    
    # 设置标题和标签
    plt.title('个股Beta值分布', fontproperties=font, fontsize=16)
    plt.xlabel('行业', fontproperties=font, fontsize=12)
    plt.ylabel('Beta值', fontproperties=font, fontsize=12)
    plt.xticks(rotation=45, ha='right', fontproperties=font)
    plt.legend(prop=font)
    plt.tight_layout()
    
    # 保存图表
    plt.savefig(f"{output_dir}/stock_beta_distribution.png")
    plt.close()
    print(f"个股Beta值分布图已保存至 {output_dir}/stock_beta_distribution.png")

# 绘制行业收益率与波动率散点图
def plot_return_vs_volatility(data, output_dir):
    """绘制行业收益率与波动率散点图"""
    if data['industry_daily'] is None:
        print("无法绘制行业收益率与波动率散点图：缺少行业日均统计数据")
        return
    
    # 准备数据
    df = data['industry_daily'].copy()
    
    # 创建图表
    plt.figure(figsize=(12, 8))
    
    # 绘制散点图
    sns.scatterplot(x='daily_volatility', y='avg_daily_return', 
                   data=df, s=100, hue='industry', palette="deep")
    
    # 添加文本标签
    for i, row in df.iterrows():
        plt.text(row['daily_volatility'] + 0.0005, row['avg_daily_return'] + 0.0005, 
                row['industry'], fontproperties=font, fontsize=9)
    
    # 添加参考线
    plt.axhline(y=0, color='r', linestyle='--', alpha=0.5)
    plt.axvline(x=0, color='r', linestyle='--', alpha=0.5)
    
    # 设置标题和标签
    plt.title('行业收益率与波动率关系', fontproperties=font, fontsize=16)
    plt.xlabel('日波动率', fontproperties=font, fontsize=12)
    plt.ylabel('平均日收益率', fontproperties=font, fontsize=12)
    plt.legend(prop=font, title='行业', title_fontproperties=font)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # 保存图表
    plt.savefig(f"{output_dir}/return_vs_volatility.png")
    plt.close()
    print(f"行业收益率与波动率散点图已保存至 {output_dir}/return_vs_volatility.png")

# 主函数
def main():
    """主函数：加载数据并生成所有图表"""
    print("开始生成行业分析可视化图表...")
    
    # 创建输出目录
    output_dir = create_output_dir("figures")
    print(f"图表将保存至 {output_dir} 目录")
    
    # 加载数据
    data = load_data()
    
    # 生成各种图表
    plot_industry_returns(data, output_dir)
    plot_industry_volatility(data, output_dir)
    plot_industry_sharpe(data, output_dir)
    plot_industry_correlation(data, output_dir)
    plot_industry_beta(data, output_dir)
    plot_industry_index_trends(data, output_dir)
    plot_industry_volume_trends(data, output_dir)
    plot_stock_index_correlation(data, output_dir)
    plot_stock_beta_distribution(data, output_dir)
    plot_return_vs_volatility(data, output_dir)
    
    print("所有图表生成完成！")

if __name__ == "__main__":
    main() 