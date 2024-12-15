#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import pymysql
from dotenv import load_dotenv

def get_db_config(prefix):
    """从环境变量获取数据库配置"""
    return {
        'host': os.getenv(f'{prefix}_HOST'),
        'port': int(os.getenv(f'{prefix}_PORT')),
        'user': os.getenv(f'{prefix}_USER'),
        'password': os.getenv(f'{prefix}_PASSWORD'),
        'db': os.getenv(f'{prefix}_DATABASE')
    }

def get_table_count(connection, table_name):
    """获取表的总行数"""
    with connection.cursor() as cursor:
        sql = f"SELECT COUNT(*) FROM `{table_name}`"
        cursor.execute(sql)
        result = cursor.fetchone()
        return result[0]

def compare_tables():
    """比较两个数据库中表的行数"""
    # 加载环境变量
    load_dotenv()
    
    # 获取源数据库和目标数据库的配置
    source_config = get_db_config('SOURCE_DB')
    target_config = get_db_config('TARGET_DB')
    
    try:
        # 连接源数据库
        source_conn = pymysql.connect(**source_config)
        print(f"[INFO] 成功连接源数据库 {source_config['host']}:{source_config['port']}")
        
        # 连接目标数据库
        target_conn = pymysql.connect(**target_config)
        print(f"[INFO] 成功连接目标数据库 {target_config['host']}:{target_config['port']}")
        
        # 获取源数据库中的所有表
        with source_conn.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
        # 比较每个表的行数
        print("\n开始比较表行数...")
        print("-" * 60)
        print(f"{'表名':<30} {'源库行数':<15} {'目标库行数':<15} {'是否一致'}")
        print("-" * 60)
        
        for table in tables:
            table_name = table[0]
            try:
                source_count = get_table_count(source_conn, table_name)
                target_count = get_table_count(target_conn, table_name)
                is_match = source_count == target_count
                status = "✓" if is_match else "✗"
                
                print(f"{table_name:<30} {source_count:<15} {target_count:<15} {status}")
                
                if not is_match:
                    print(f"[警告] 表 {table_name} 行数不一致!")
                    
            except Exception as e:
                print(f"[错误] 处理表 {table_name} 时出错: {str(e)}")
                
    except Exception as e:
        print(f"[错误] {str(e)}")
        sys.exit(1)
        
    finally:
        # 关闭数据库连接
        if 'source_conn' in locals():
            source_conn.close()
        if 'target_conn' in locals():
            target_conn.close()

def print_usage():
    print("""
使用说明:
1. 请先配置.env文件,包含以下环境变量:
   SOURCE_DB_HOST=源数据库主机
   SOURCE_DB_PORT=源数据库端口
   SOURCE_DB_USER=源数据库用户名
   SOURCE_DB_PASSWORD=源数据库密码
   SOURCE_DB_DATABASE=源数据库名称
   
   TARGET_DB_HOST=目标数据库主机
   TARGET_DB_PORT=目标数据库端口
   TARGET_DB_USER=目标数据库用户名
   TARGET_DB_PASSWORD=目标数据库密码
   TARGET_DB_DATABASE=目标数据库名称

2. 运行脚本: python compare_tables.py
""")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print_usage()
        sys.exit(0)
        
    compare_tables()
