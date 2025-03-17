from google_auth_oauthlib.flow import InstalledAppFlow
import os
import yaml

# 定义所需的OAuth2范围
SCOPES = ["https://www.googleapis.com/auth/adwords"]

# 创建OAuth2流程
flow = InstalledAppFlow.from_client_secrets_file(
    "client_secrets.json",  # 从Google Cloud Console下载的OAuth客户端信息
    scopes=SCOPES
)

# 运行本地服务器进行授权
flow.run_local_server(port=3000, prompt='consent')

# 获取凭据
credentials = flow.credentials

# 检查是否成功获取刷新令牌
if not credentials.refresh_token:
    print("警告: 未能获取刷新令牌。请确保您在授权时选择了'允许'选项，并且应用配置了正确的访问类型(access_type=offline)。")
    print("您可能需要在Google Cloud Console中撤销之前的授权，然后重新运行此脚本。")

# 创建yaml配置
config = {
    "client_id": credentials.client_id,
    "client_secret": credentials.client_secret,
    "refresh_token": credentials.refresh_token
}

# 打印配置信息而不是直接写入文件
print("请手动将以下配置信息保存到google-ads.yaml文件中:")
print("client_id:", config["client_id"])
print("client_secret:", config["client_secret"])
print("refresh_token:", config["refresh_token"])

# 自动更新google-ads.yaml文件中的refresh_token
yaml_path = "google-ads.yaml"
if os.path.exists(yaml_path):
    # 读取现有的yaml文件
    with open(yaml_path, "r") as yaml_file:
        yaml_config = yaml.safe_load(yaml_file)
    
    # 更新refresh_token
    if yaml_config:
        yaml_config["refresh_token"] = credentials.refresh_token
        # 写回文件
        with open(yaml_path, "w") as yaml_file:
            yaml.dump(yaml_config, yaml_file, default_flow_style=False)
        print(f"\n已自动更新 {yaml_path} 文件中的refresh_token")
    else:
        print(f"\n警告: {yaml_path} 文件存在但内容为空，无法更新")
else:
    print(f"\n警告: 未找到 {yaml_path} 文件，无法自动更新refresh_token")
    print("请手动创建文件并添加以下内容:")
    print("""
developer_token: YOUR_DEVELOPER_TOKEN
login_customer_id: YOUR_LOGIN_CUSTOMER_ID
client_id: {client_id}
client_secret: {client_secret}
refresh_token: {refresh_token}
use_proto_plus: true
    """.format(**config))

print("\n重要提示：")
print("1. 您必须将'login_customer_id'替换为您的实际Google Ads客户ID（不带破折号）")
print("2. 客户ID可以在Google Ads界面右上角的帮助图标旁边找到")
print("3. 格式应为纯数字，例如：1234567890，不要包含破折号或其他字符")
print("4. 'developer_token'也需要替换为您的实际开发者令牌")
print("5. 如果不设置正确的客户ID，API调用将失败并显示'Invalid customer ID'错误")

print("\n您也可以使用以下yaml格式:")
for key, value in config.items():
    print(f"{key}: {value}") 