# Google Ads API 工具

这是一个用于与 Google Ads API 交互的 Python 工具集，主要用于获取关键词的搜索量数据和管理 Google Ads 账户认证。

## 功能特性

- **OAuth2 认证**: 自动化 Google Ads API 的认证流程
- **关键词分析**: 批量获取关键词的月均搜索量、竞争度等数据
- **配置管理**: 自动管理和更新认证配置
- **数据导出**: 支持将结果导出为 CSV 文件

## 文件说明

- `google_ads_auth.py`: Google Ads API OAuth2 认证脚本
- `google_ads_keywords.py`: 关键词数据获取和分析脚本
- `google-ads.yaml`: API 配置文件（包含认证信息）
- `client_secrets.json`: Google Cloud Console 下载的客户端密钥文件

## 前置要求

### 1. 安装依赖包

```bash
pip install google-ads pandas google-auth-oauthlib pyyaml
```

### 2. Google Cloud Console 设置

1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建新项目或选择现有项目
3. 启用 Google Ads API
4. 创建 OAuth 2.0 客户端 ID
5. 下载客户端密钥文件并重命名为 `client_secrets.json`

### 3. Google Ads 账户设置

1. 访问 [Google Ads](https://ads.google.com/)
2. 获取开发者令牌（Developer Token）
3. 记录您的客户 ID（Customer ID）

## 使用步骤

### 第一步：配置认证

1. 确保 `client_secrets.json` 文件在当前目录
2. 运行认证脚本：

```bash
python google_ads_auth.py
```

3. 脚本会自动打开浏览器，按照提示完成 OAuth2 认证
4. 认证成功后，脚本会自动更新 `google-ads.yaml` 文件

### 第二步：配置 google-ads.yaml

手动编辑 `google-ads.yaml` 文件，确保包含以下信息：

```yaml
client_id: YOUR_CLIENT_ID
client_secret: YOUR_CLIENT_SECRET
developer_token: YOUR_DEVELOPER_TOKEN
login_customer_id: 'YOUR_CUSTOMER_ID'
refresh_token: YOUR_REFRESH_TOKEN
test_account_id: 'YOUR_TEST_ACCOUNT_ID'  # 可选，用于测试
use_proto_plus: true
```

**重要提示：**
- `login_customer_id` 必须是纯数字格式（不包含破折号）
- `developer_token` 需要从 Google Ads 账户中获取
- 如果使用测试账户，请设置 `test_account_id`

### 第三步：获取关键词数据

#### 使用默认关键词：

```bash
python google_ads_keywords.py
```

#### 添加自定义关键词：

```bash
python google_ads_keywords.py --keywords "keyword1" "keyword2" "keyword3"
```

#### 导出结果到 CSV：

```bash
python google_ads_keywords.py --output results.csv
```

#### 组合使用：

```bash
python google_ads_keywords.py --keywords "AI tools" "machine learning" --output keyword_analysis.csv
```

## 输出数据说明

脚本会返回以下关键词数据：

- **keyword**: 关键词
- **avg_monthly_searches**: 月均搜索量
- **competition**: 竞争度（LOW/MEDIUM/HIGH）
- **competition_index**: 竞争度指数（0-100）
- **low_top_of_page_bid**: 页面顶部出价下限（美元）
- **high_top_of_page_bid**: 页面顶部出价上限（美元）

## 常见问题

### 1. 开发者令牌权限错误

**错误信息**: `DEVELOPER_TOKEN_NOT_APPROVED` 或 `only approved for use with test accounts`

**解决方案**:
- 使用测试账户：申请 [Google Ads 测试经理账号](https://ads.google.com/nav/selectaccount?sf=mt&hl=zh-cn)
- 申请更高级别权限：访问 [开发者令牌申请页面](https://developers.google.com/google-ads/api/docs/first-call/dev-token)

### 2. 客户 ID 格式错误

**错误信息**: `Invalid customer ID`

**解决方案**:
- 确保客户 ID 为纯数字格式（例如：1234567890）
- 不要包含破折号或其他字符
- 客户 ID 可在 Google Ads 界面右上角找到

### 3. 认证失败

**解决方案**:
1. 检查 `client_secrets.json` 文件是否正确
2. 确保在 Google Cloud Console 中正确配置了重定向 URI
3. 重新运行 `google_ads_auth.py` 进行认证
