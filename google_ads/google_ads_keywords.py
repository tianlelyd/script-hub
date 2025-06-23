import pandas as pd
from google.ads.googleads.client import GoogleAdsClient
import os
import yaml
import argparse
import logging

# 设置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config(yaml_path="google-ads.yaml"):
    """加载并验证配置文件"""
    if not os.path.exists(yaml_path):
        raise FileNotFoundError(f"找不到配置文件: {yaml_path}")
    
    with open(yaml_path, 'r') as file:
        config = yaml.safe_load(file)
        
    logger.info("当前配置信息:")
    for key, value in config.items():
        # 隐藏敏感信息
        if key in ["client_secret", "refresh_token"]:
            masked_value = value[:4] + "..." if value else None
            logger.info(f"{key}: {masked_value}")
        else:
            logger.info(f"{key}: {value}")
    
    # 检查客户ID格式
    if "login_customer_id" in config:
        customer_id = str(config["login_customer_id"])
        if not customer_id.isdigit():
            logger.warning(f"警告: 客户ID '{customer_id}' 包含非数字字符，这可能导致错误")
        logger.info(f"使用客户ID: {customer_id}")
    else:
        logger.warning("警告: 配置中缺少login_customer_id字段")
    
    return config

def get_keyword_stats(keywords_list, yaml_path="google-ads.yaml"):
    """
    批量获取关键词的月均搜索量
    
    Args:
        keywords_list: 要查询的关键词列表
        yaml_path: 配置文件路径
    
    Returns:
        包含关键词和搜索量的DataFrame
    """
    try:
        # 加载配置
        config = load_config(yaml_path)
        
        # 从yaml文件加载配置
        client = GoogleAdsClient.load_from_storage(yaml_path)
        
        # 获取客户ID
        if "login_customer_id" not in config:
            raise ValueError("配置中缺少login_customer_id字段")
            
        customer_id = str(config["login_customer_id"])
        
        logger.info(f"在请求中设置客户ID: {customer_id}")
        
        # 初始化关键词规划工具
        keyword_planner = client.get_service("KeywordPlanIdeaService")
        
        # 创建历史指标请求
        historical_metrics_request = client.get_type("GenerateKeywordHistoricalMetricsRequest")
        historical_metrics_request.customer_id = customer_id
        
        # 设置关键词列表
        historical_metrics_request.keywords.extend(keywords_list)
        
        # 设置搜索网络
        historical_metrics_request.keyword_plan_network = client.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH
        
        # 发送请求获取结果
        logger.info("正在发送API请求...")
        response = keyword_planner.generate_keyword_historical_metrics(
            request=historical_metrics_request
        )
        
        # 处理结果
        return process_keyword_results(response)
        
    except Exception as e:
        logger.error(f"错误: {str(e)}")
        handle_api_error(e)
        raise

def process_keyword_results(response):
    """处理API响应并转换为DataFrame"""
    results = []
    for result in response.results:
        metrics = result.keyword_metrics
        results.append({
            "keyword": result.text,
            "avg_monthly_searches": metrics.avg_monthly_searches,
            "competition": metrics.competition.name,
            "competition_index": metrics.competition_index,
            "low_top_of_page_bid": metrics.low_top_of_page_bid_micros / 1000000 if metrics.low_top_of_page_bid_micros else None,
            "high_top_of_page_bid": metrics.high_top_of_page_bid_micros / 1000000 if metrics.high_top_of_page_bid_micros else None
        })
        
        # 可选：如果需要月度搜索量数据
        # monthly_data = []
        # for month in metrics.monthly_search_volumes:
        #     monthly_data.append({
        #         "keyword": result.text,
        #         "year": month.year,
        #         "month": month.month.name,
        #         "monthly_searches": month.monthly_searches
        #     })
    
    # 转换为DataFrame并返回
    return pd.DataFrame(results)

def handle_api_error(error):
    """处理API错误并提供有用的错误信息"""
    if "DEVELOPER_TOKEN_NOT_APPROVED" in str(error) or "only approved for use with test accounts" in str(error):
        logger.error("\n开发者令牌权限错误:")
        logger.error("您的开发者令牌只被批准用于测试账户，但您正在尝试访问非测试账户。")
        logger.error("解决方案:")
        logger.error("1. 使用测试账户: 打开 https://ads.google.com/nav/selectaccount?sf=mt&hl=zh-cn 申请测试经理账号，并替换 login_customer_id 为测试经理账号ID")
        logger.error("2. 申请更高级别的访问权限: 访问 https://developers.google.com/google-ads/api/docs/first-call/dev-token 申请基本或标准访问权限")
    else:
        logger.error("请确保:")
        logger.error("1. 客户ID格式正确（纯数字，不包含破折号）")
        logger.error("2. 您的账户有权限访问该客户ID")
        logger.error("3. 开发者令牌有效且与该客户ID关联")

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='获取关键词的月均搜索量')
    parser.add_argument('--keywords', nargs='+', help='要作为附加查询的关键词列表')
    parser.add_argument('--output', help='输出CSV文件路径')
    args = parser.parse_args()
    
    # 默认关键词列表
    default_keywords = [
        "good morning images", "happy birthday images", "baby shower", 
        "image to text converter", "GPTs", "ai image upscaler", 
        "random images", "banana png", "translate text from image", "conversational"
    ]
    
    # 合并默认关键词和命令行附加关键词
    keywords = default_keywords.copy()
    if args.keywords:
        keywords.extend(args.keywords)
        logger.info(f"使用默认关键词 + 附加关键词，总共 {len(keywords)} 个关键词")
        logger.info(f"附加关键词: {args.keywords}")
    else:
        logger.info(f"仅使用默认关键词，总共 {len(keywords)} 个关键词")
    
    # 获取关键词数据
    keyword_stats = get_keyword_stats(keywords)
    
    # 设置pandas显示所有行
    pd.set_option('display.max_rows', None)
    pd.set_option('display.width', 120)
    
    # 显示结果
    print(keyword_stats)
    
    # 如果指定了输出文件，则保存到CSV
    if args.output:
        keyword_stats.to_csv(args.output, index=False)
        logger.info(f"结果已保存到 {args.output}")

if __name__ == "__main__":
    main()
