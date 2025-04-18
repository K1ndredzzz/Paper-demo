import re
import time
import threading
import json
import os
from datetime import datetime
from main import post_thread, comment_thread_date, comment_thread_id

# 加载配置文件
def load_config():
    config_file = 'crawler_config.json'
    
    # 检查配置文件是否存在
    if not os.path.exists(config_file):
        print(f"警告: 配置文件 {config_file} 不存在，将使用默认配置。")
        return {
            "max_concurrent_threads": 3,
            "post_pages": {
                "start_page": 1,
                "end_page": 100
            },
            "comment_date_range": {
                "start_date": "2025-02-01",
                "end_date": "2025-02-28"
            },
            "delay_between_batches": 30,
            "mongodb": {
                "host": "localhost",
                "port": 27017
            },
            "stock_file": "industries.py"
        }
    
    # 加载配置文件
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print("成功加载配置文件。")
        return config
    except Exception as e:
        print(f"警告: 读取配置文件时出错: {str(e)}，将使用默认配置。")
        return {
            "max_concurrent_threads": 3,
            "post_pages": {
                "start_page": 1,
                "end_page": 100
            },
            "comment_date_range": {
                "start_date": "2025-02-01",
                "end_date": "2025-02-28"
            },
            "delay_between_batches": 30,
            "mongodb": {
                "host": "localhost",
                "port": 27017
            },
            "stock_file": "industries.py"
        }

# 从industries.py文件中提取所有股票代码
def extract_stock_codes(stock_file):
    stock_codes = []
    
    with open(stock_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # 使用正则表达式匹配所有股票代码
    pattern = r"'代码': '(\d+)'"
    matches = re.findall(pattern, content)
    
    # 去除重复的股票代码
    return list(set(matches))

# 保存爬取进度
def save_progress(progress_file, completed, failed):
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump({
            'completed': completed,
            'failed': failed,
            'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }, f, ensure_ascii=False, indent=2)

# 加载爬取进度
def load_progress(progress_file):
    if not os.path.exists(progress_file):
        return [], []
    
    with open(progress_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get('completed', []), data.get('failed', [])

# 线程安全的爬取函数装饰器
def safe_crawl(func_name):
    def decorator(func):
        def wrapper(stock_code, *args, **kwargs):
            try:
                print(f"[{func_name}] 开始爬取股票 {stock_code}...")
                func(stock_code, *args, **kwargs)
                print(f"[{func_name}] 股票 {stock_code} 爬取成功!")
                return True
            except Exception as e:
                print(f"[{func_name}] 股票 {stock_code} 爬取失败: {str(e)}")
                return False
        return wrapper
    return decorator

# 包装线程函数
safe_post_thread = safe_crawl("发帖爬取")(post_thread)
safe_comment_thread_date = safe_crawl("评论爬取")(comment_thread_date)

# 批量爬取发帖信息
def batch_crawl_posts(stock_codes, max_threads=5, pages=(1, 100), progress_file='post_progress.json', delay=30):
    """
    批量爬取所有股票的发帖信息
    
    :param stock_codes: 股票代码列表
    :param max_threads: 最大线程数
    :param pages: 爬取页数范围，默认(1, 100)
    :param progress_file: 进度文件
    :param delay: 批次间延时（秒）
    """
    # 加载进度
    completed, failed = load_progress(progress_file)
    
    # 过滤掉已完成的股票
    pending_stocks = [code for code in stock_codes if code not in completed]
    
    print(f"待处理股票数量: {len(pending_stocks)}")
    print(f"已完成股票数量: {len(completed)}")
    print(f"失败股票数量: {len(failed)}")
    
    total_stocks = len(pending_stocks)
    processed = 0
    
    while processed < total_stocks:
        # 计算当前批次需要处理的股票数量
        batch_size = min(max_threads, total_stocks - processed)
        threads = []
        results = [False] * batch_size  # 存储每个线程的执行结果
        
        print(f"==== 处理第 {processed+1}-{processed+batch_size} 支股票的发帖信息 (共{total_stocks}支) ====")
        
        # 创建并启动线程
        for i in range(batch_size):
            stock_code = pending_stocks[processed + i]
            thread = threading.Thread(
                target=lambda idx=i, code=stock_code: results.__setitem__(idx, safe_post_thread(code, pages[0], pages[1]))
            )
            thread.start()
            threads.append(thread)
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 更新进度
        for i in range(batch_size):
            stock_code = pending_stocks[processed + i]
            if results[i]:
                completed.append(stock_code)
            else:
                failed.append(stock_code)
            
        # 保存进度
        save_progress(progress_file, completed, failed)
        
        processed += batch_size
        
        # 添加延时避免请求过于频繁
        if processed < total_stocks:
            print(f"休息 {delay} 秒后继续下一批...")
            time.sleep(delay)
    
    print("所有股票发帖信息爬取完成！")
    print(f"成功: {len(completed)}, 失败: {len(failed)}")
    if failed:
        print(f"失败的股票代码: {failed}")
    
    return completed, failed

# 批量爬取评论信息
def batch_crawl_comments(stock_codes, max_threads=5, date_range=('2025-02-01', '2025-02-28'), progress_file='comment_progress.json', delay=30):
    """
    批量爬取所有股票的评论信息
    
    :param stock_codes: 股票代码列表
    :param max_threads: 最大线程数
    :param date_range: 日期范围，默认(2025-02-01, 2025-02-28)
    :param progress_file: 进度文件
    :param delay: 批次间延时（秒）
    """
    # 加载进度
    completed, failed = load_progress(progress_file)
    
    # 过滤掉已完成的股票
    pending_stocks = [code for code in stock_codes if code not in completed]
    
    print(f"待处理股票数量: {len(pending_stocks)}")
    print(f"已完成股票数量: {len(completed)}")
    print(f"失败股票数量: {len(failed)}")
    
    total_stocks = len(pending_stocks)
    processed = 0
    
    while processed < total_stocks:
        # 计算当前批次需要处理的股票数量
        batch_size = min(max_threads, total_stocks - processed)
        threads = []
        results = [False] * batch_size  # 存储每个线程的执行结果
        
        print(f"==== 处理第 {processed+1}-{processed+batch_size} 支股票的评论信息 (共{total_stocks}支) ====")
        
        # 创建并启动线程
        for i in range(batch_size):
            stock_code = pending_stocks[processed + i]
            thread = threading.Thread(
                target=lambda idx=i, code=stock_code: results.__setitem__(idx, safe_comment_thread_date(code, date_range[0], date_range[1]))
            )
            thread.start()
            threads.append(thread)
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 更新进度
        for i in range(batch_size):
            stock_code = pending_stocks[processed + i]
            if results[i]:
                completed.append(stock_code)
            else:
                failed.append(stock_code)
            
        # 保存进度
        save_progress(progress_file, completed, failed)
        
        processed += batch_size
        
        # 添加延时避免请求过于频繁
        if processed < total_stocks:
            print(f"休息 {delay} 秒后继续下一批...")
            time.sleep(delay)
    
    print("所有股票评论信息爬取完成！")
    print(f"成功: {len(completed)}, 失败: {len(failed)}")
    if failed:
        print(f"失败的股票代码: {failed}")
    
    return completed, failed

# 重试爬取失败的股票
def retry_failed_stocks(task_type, max_threads=3, pages=(1, 100), date_range=('2025-02-01', '2025-02-28'), delay=30):
    if task_type == 'post':
        progress_file = 'post_progress.json'
        crawl_func = batch_crawl_posts
        args = (max_threads, pages, progress_file, delay)
    else:  # comment
        progress_file = 'comment_progress.json'
        crawl_func = batch_crawl_comments
        args = (max_threads, date_range, progress_file, delay)
    
    _, failed = load_progress(progress_file)
    
    if not failed:
        print(f"没有需要重试的{task_type}任务")
        return
    
    print(f"开始重试{len(failed)}个失败的{task_type}任务...")
    crawl_func(failed, *args)

if __name__ == "__main__":
    # 加载配置
    config = load_config()
    
    # 获取配置参数
    max_concurrent_threads = config.get("max_concurrent_threads", 3)
    post_pages = (
        config.get("post_pages", {}).get("start_page", 1),
        config.get("post_pages", {}).get("end_page", 100)
    )
    comment_date_range = (
        config.get("comment_date_range", {}).get("start_date", "2025-02-01"),
        config.get("comment_date_range", {}).get("end_date", "2025-02-28")
    )
    delay_between_batches = config.get("delay_between_batches", 30)
    stock_file = config.get("stock_file", "industries.py")
    
    # 显示配置信息
    print("==== 当前配置 ====")
    print(f"最大并发线程数: {max_concurrent_threads}")
    print(f"发帖爬取页数范围: {post_pages[0]}-{post_pages[1]}")
    print(f"评论爬取日期范围: {comment_date_range[0]} 至 {comment_date_range[1]}")
    print(f"批次间延时: {delay_between_batches}秒")
    print(f"股票列表文件: {stock_file}")
    print("================")
    
    # 提取股票代码
    stock_codes = extract_stock_codes(stock_file)
    print(f"从{stock_file}中提取到 {len(stock_codes)} 支股票")
    print(f"股票代码列表: {stock_codes}")
    
    # 询问用户要执行哪个任务
    print("\n请选择要执行的任务:")
    print("1. 爬取所有股票的发帖信息")
    print("2. 爬取所有股票的评论信息")
    print("3. 全部爬取（先爬发帖，再爬评论）")
    print("4. 重试失败的发帖任务")
    print("5. 重试失败的评论任务")
    
    choice = input("请输入选项(1-5): ").strip()
    
    if choice == '1':
        print("\n===== 开始爬取所有股票的发帖信息 =====")
        batch_crawl_posts(
            stock_codes, 
            max_concurrent_threads, 
            post_pages, 
            delay=delay_between_batches
        )
    elif choice == '2':
        print("\n===== 开始爬取所有股票的评论信息 =====")
        batch_crawl_comments(
            stock_codes, 
            max_concurrent_threads, 
            comment_date_range, 
            delay=delay_between_batches
        )
    elif choice == '3':
        print("\n===== 第一阶段：爬取所有股票的发帖信息 =====")
        batch_crawl_posts(
            stock_codes, 
            max_concurrent_threads, 
            post_pages, 
            delay=delay_between_batches
        )
        
        print("\n===== 第二阶段：爬取所有股票的评论信息 =====")
        batch_crawl_comments(
            stock_codes, 
            max_concurrent_threads, 
            comment_date_range, 
            delay=delay_between_batches
        )
    elif choice == '4':
        retry_failed_stocks(
            'post', 
            max_concurrent_threads, 
            post_pages, 
            delay=delay_between_batches
        )
    elif choice == '5':
        retry_failed_stocks(
            'comment', 
            max_concurrent_threads, 
            date_range=comment_date_range, 
            delay=delay_between_batches
        )
    else:
        print("无效的选项!") 