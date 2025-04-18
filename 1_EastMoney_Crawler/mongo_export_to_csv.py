import os
import pandas as pd
from pymongo import MongoClient
import json

# 创建输出目录
output_dir = 'csv_output'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
    print(f'创建输出目录: {output_dir}')

# 加载MongoDB配置
config_file = 'crawler_config.json'
try:
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    mongo_config = config.get('mongodb', {'host': 'localhost', 'port': 27017})
    print(f"成功从{config_file}加载MongoDB配置")
except Exception as e:
    print(f"警告: 无法读取配置文件: {str(e)}，将使用默认配置")
    mongo_config = {'host': 'localhost', 'port': 27017}

# 连接MongoDB
try:
    client = MongoClient(mongo_config['host'], mongo_config['port'])
    print(f"成功连接到MongoDB: {mongo_config['host']}:{mongo_config['port']}")
except Exception as e:
    print(f"错误: 无法连接到MongoDB: {str(e)}")
    exit(1)

# 检查可用的数据库
databases = client.list_database_names()
print(f"可用数据库: {databases}")

# 选择数据库 (post_info 或 comment_info)
db_names = [db for db in databases if db in ['post_info', 'comment_info']]
if not db_names:
    print("错误: 未找到'post_info'或'comment_info'数据库")
    exit(1)

for db_name in db_names:
    db = client[db_name]
    print(f"\n处理数据库: {db_name}")
    
    # 获取集合列表
    collections = db.list_collection_names()
    print(f"找到{len(collections)}个集合: {collections}")
    
    if not collections:
        print(f"警告: 数据库'{db_name}'中没有集合")
        continue
    
    # 批量导出
    for collection_name in collections:
        try:
            # 获取集合数据
            collection = db[collection_name]
            document_count = collection.count_documents({})
            print(f"集合'{collection_name}'中有{document_count}条文档")
            
            if document_count == 0:
                print(f"警告: 集合'{collection_name}'为空，跳过")
                continue
            
            cursor = collection.find({})
            
            # 转换为DataFrame
            df = pd.DataFrame(list(cursor))
            
            # 如果DataFrame不为空
            if not df.empty:
                # 删除MongoDB的_id字段（如果不需要的话）
                if '_id' in df.columns:
                    df = df.drop('_id', axis=1)
                    
                # 保存为CSV
                output_file = os.path.join(output_dir, f'{collection_name}.csv')
                df.to_csv(output_file, index=False, encoding='utf-8-sig')
                print(f'已导出: {collection_name} -> {output_file} ({len(df)}行)')
            else:
                print(f"警告: 集合'{collection_name}'的DataFrame为空")
        except Exception as e:
            print(f"错误: 处理集合'{collection_name}'时出错: {str(e)}")

print('\n所有文件导出完成！')
print(f"CSV文件已保存到目录: {os.path.abspath(output_dir)}")
