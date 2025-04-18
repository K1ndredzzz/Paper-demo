import pandas as pd
import os
import re
from datetime import datetime
import ast

# 读取行业信息
industry_file = 'industries.py'
stock_to_industry = {}

# 解析industries.py文件中的INDUSTRY_STOCK_MAP字典
with open(industry_file, 'r', encoding='utf-8') as f:
    content = f.read()
    # 提取Python代码部分
    pattern = r'INDUSTRY_STOCK_MAP = \{.*?\}\s*\n\s*#'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        industry_map_str = match.group(0).replace('INDUSTRY_STOCK_MAP = ', '').strip()
        # 去掉末尾的 #
        industry_map_str = industry_map_str.rstrip(' \n#')
        # 将字符串转换为Python字典
        try:
            industry_map = ast.literal_eval(industry_map_str)
            # 构建股票代码到行业代码的映射
            for industry_name, industry_info in industry_map.items():
                industry_code = industry_info['code']
                for stock in industry_info['stocks']:
                    stock_code = stock['代码']
                    stock_to_industry[stock_code] = {
                        'board_code': industry_code,
                        'name': stock['名称']
                    }
        except Exception as e:
            print(f"解析行业数据时出错: {e}")
    else:
        print("无法在industries.py文件中找到INDUSTRY_STOCK_MAP字典")

# 获取所有csv_output目录下的post和comment文件
csv_dir = 'csv_input'
all_files = os.listdir(csv_dir) if os.path.exists(csv_dir) else []

post_files = [f for f in all_files if f.startswith('post_')]
comment_files = [f for f in all_files if f.startswith('comment_')]

# 创建一个新的DataFrame来存储合并后的数据
merged_data = []

# 处理所有帖子文件
for post_file in post_files:
    stock_code = post_file.replace('post_', '').replace('.csv', '')
    post_path = os.path.join(csv_dir, post_file)
    
    try:
        posts_df = pd.read_csv(post_path)
        
        for _, post in posts_df.iterrows():
            # 获取行业代码
            board_code = stock_to_industry.get(stock_code, {}).get('board_code', '')
            if not board_code:
                # 如果在映射中找不到，则尝试从URL中提取板块ID
                if isinstance(post.get('post_url', ''), str) and ',' in post.get('post_url', ''):
                    url_parts = post['post_url'].split(',')
                    if len(url_parts) >= 2:
                        board_code = url_parts[1]
                else:
                    board_code = stock_code  # 默认使用股票代码
            
            # 提取日期
            date_str = post['post_date']
            date_obj = None
            date_only = ""
            
            try:
                # 尝试解析日期格式
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                date_only = date_obj.strftime('%Y-%m-%d')
            except ValueError:
                try:
                    # 尝试解析日期时间格式
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                    date_only = date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    # 如果无法解析，保持原样
                    date_only = date_str
                    date_obj = None  # 确保设置为None，以便后续条件判断
            
            # 提取时间
            time_only = "00:00:00"  # 默认值
            
            # 尝试从post_time字段获取时间
            if 'post_time' in post and pd.notna(post['post_time']):
                time_str = str(post['post_time'])
                # 检查是否是有效的时间格式
                if re.match(r'^\d{1,2}:\d{2}(:\d{2})?$', time_str):
                    # 确保时间格式为HH:MM:SS
                    if time_str.count(':') == 1:
                        time_only = time_str + ":00"
                    else:
                        time_only = time_str
                else:
                    # 尝试从日期时间字符串中提取时间部分
                    if ' ' in date_str:
                        try:
                            time_part = date_str.split(' ')[1]
                            if re.match(r'^\d{1,2}:\d{2}(:\d{2})?$', time_part):
                                if time_part.count(':') == 1:
                                    time_only = time_part + ":00"
                                else:
                                    time_only = time_part
                        except:
                            pass
            
            # 只保留2025年02.01-02.28的数据
            if date_obj and date_obj.year == 2025 and date_obj.month == 2:
                merged_data.append({
                    'board_code': board_code,
                    'stock_code': stock_code,
                    'date': date_only,
                    'time': time_only,
                    'source_type': 'post',
                    'content': post['post_title']
                })
    except Exception as e:
        print(f"处理文件 {post_file} 时出错: {e}")

# 处理所有评论文件
for comment_file in comment_files:
    stock_code = comment_file.replace('comment_', '').replace('.csv', '')
    comment_path = os.path.join(csv_dir, comment_file)
    
    try:
        comments_df = pd.read_csv(comment_path)
        
        for _, comment in comments_df.iterrows():
            # 获取行业代码
            board_code = stock_to_industry.get(stock_code, {}).get('board_code', '')
            if not board_code:
                board_code = str(comment['post_id']) if pd.notna(comment.get('post_id', '')) else ''
            
            # 提取日期
            date_str = comment['comment_date']
            date_obj = None
            date_only = ""
            
            try:
                # 尝试解析日期格式
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                date_only = date_obj.strftime('%Y-%m-%d')
            except ValueError:
                try:
                    # 尝试解析日期时间格式
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                    date_only = date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    # 如果无法解析，保持原样
                    date_only = date_str
                    date_obj = None  # 确保设置为None，以便后续条件判断
            
            # 提取时间
            time_only = "00:00:00"  # 默认值
            
            # 尝试从comment_time字段获取时间
            if 'comment_time' in comment and pd.notna(comment['comment_time']):
                time_str = str(comment['comment_time'])
                # 检查是否是有效的时间格式
                if re.match(r'^\d{1,2}:\d{2}(:\d{2})?$', time_str):
                    # 确保时间格式为HH:MM:SS
                    if time_str.count(':') == 1:
                        time_only = time_str + ":00"
                    else:
                        time_only = time_str
                else:
                    # 尝试从日期时间字符串中提取时间部分
                    if ' ' in date_str:
                        try:
                            time_part = date_str.split(' ')[1]
                            if re.match(r'^\d{1,2}:\d{2}(:\d{2})?$', time_part):
                                if time_part.count(':') == 1:
                                    time_only = time_part + ":00"
                                else:
                                    time_only = time_part
                        except:
                            pass
            
            # 只保留2025年02.01-02.28的数据
            if date_obj and date_obj.year == 2025 and date_obj.month == 2:
                merged_data.append({
                    'board_code': board_code,
                    'stock_code': stock_code,
                    'date': date_only,
                    'time': time_only,
                    'source_type': 'comment',
                    'content': comment['comment_content']
                })
    except Exception as e:
        print(f"处理文件 {comment_file} 时出错: {e}")

# 创建合并后的DataFrame
merged_df = pd.DataFrame(merged_data)

# 确保列的顺序正确: board_code, stock_code, date, time, source_type, content
merged_df = merged_df[['board_code', 'stock_code', 'date', 'time', 'source_type', 'content']]

# 按日期和时间排序
merged_df.sort_values(by=['date', 'time'], ascending=[False, False], inplace=True)

# 保存合并后的数据
output_file = 'merged_all_stocks_202502.csv'
merged_df.to_csv(output_file, index=False, encoding='utf-8')

print(f"合并完成！数据已保存到 {output_file}")
print(f"合并了 {len(merged_data)} 条数据")
print(f"其中包含 {merged_df[merged_df['source_type'] == 'post'].shape[0]} 条帖子和 {merged_df[merged_df['source_type'] == 'comment'].shape[0]} 条评论") 