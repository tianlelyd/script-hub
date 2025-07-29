import requests
import json
import os
from urllib.parse import quote

# 创建存储目录
output_dir = "managedsettings"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 从提供的JSON数据创建URL列表
urls_data = [
    {
        "index": 1,
        "text": "ManagedSettings",
        "href": "https://developer.apple.com/documentation/managedsettings"
    },
    {
        "index": 2,
        "text": "var siri: SiriSettings",
        "href": "https://developer.apple.com/documentation/managedsettings/managedsettingsstore/siri"
    },
    {
        "index": 3,
        "text": "Manage Settings on Devices in a Family Sharing Group",
        "href": "https://developer.apple.com/documentation/managedsettings/connectionwithframeworks"
    },
    {
        "index": 4,
        "text": "Confirming the Effective TV and Movie Ratings",
        "href": "https://developer.apple.com/documentation/managedsettings/readingmedia"
    },
    {
        "index": 5,
        "text": "ManagedSettingsStore",
        "href": "https://developer.apple.com/documentation/managedsettings/managedsettingsstore"
    },
    {
        "index": 6,
        "text": "init()",
        "href": "https://developer.apple.com/documentation/managedsettings/managedsettingsstore/init()"
    },
    {
        "index": 7,
        "text": "ManagedSettingsGroup",
        "href": "https://developer.apple.com/documentation/managedsettings/managedsettingsgroup"
    },
    {
        "index": 8,
        "text": "var account: AccountSettings",
        "href": "https://developer.apple.com/documentation/managedsettings/managedsettingsstore/account"
    },
    {
        "index": 9,
        "text": "AccountSettings",
        "href": "https://developer.apple.com/documentation/managedsettings/accountsettings"
    },
    {
        "index": 10,
        "text": "var lockAccounts: Bool?",
        "href": "https://developer.apple.com/documentation/managedsettings/accountsettings/lockaccounts-swift.property"
    },
    {
        "index": 11,
        "text": "static let lockAccounts: SettingMetadata<Bool>",
        "href": "https://developer.apple.com/documentation/managedsettings/accountsettings/lockaccounts-swift.type.property"
    },
    {
        "index": 12,
        "text": "var cellular: CellularSettings",
        "href": "https://developer.apple.com/documentation/managedsettings/managedsettingsstore/cellular"
    },
    {
        "index": 13,
        "text": "CellularSettings",
        "href": "https://developer.apple.com/documentation/managedsettings/cellularsettings"
    },
    {
        "index": 14,
        "text": "var lockAppCellularData: Bool?",
        "href": "https://developer.apple.com/documentation/managedsettings/cellularsettings/lockappcellulardata-swift.property"
    },
    {
        "index": 15,
        "text": "static let lockAppCellularData: SettingMetadata<Bool>",
        "href": "https://developer.apple.com/documentation/managedsettings/cellularsettings/lockappcellulardata-swift.type.property"
    },
    {
        "index": 16,
        "text": "var lockCellularPlan: Bool?",
        "href": "https://developer.apple.com/documentation/managedsettings/cellularsettings/lockcellularplan-swift.property"
    },
    {
        "index": 17,
        "text": "static let lockCellularPlan: SettingMetadata<Bool>",
        "href": "https://developer.apple.com/documentation/managedsettings/cellularsettings/lockcellularplan-swift.type.property"
    },
    {
        "index": 18,
        "text": "var lockESIM: Bool?",
        "href": "https://developer.apple.com/documentation/managedsettings/cellularsettings/lockesim-swift.property"
    },
    {
        "index": 19,
        "text": "static let lockESIM: SettingMetadata<Bool>",
        "href": "https://developer.apple.com/documentation/managedsettings/cellularsettings/lockesim-swift.type.property"
    },
    {
        "index": 20,
        "text": "var dateAndTime: DateAndTimeSettings",
        "href": "https://developer.apple.com/documentation/managedsettings/managedsettingsstore/dateandtime"
    },
    {
        "index": 21,
        "text": "DateAndTimeSettings",
        "href": "https://developer.apple.com/documentation/managedsettings/dateandtimesettings"
    },
    {
        "index": 22,
        "text": "var requireAutomaticDateAndTime: Bool?",
        "href": "https://developer.apple.com/documentation/managedsettings/dateandtimesettings/requireautomaticdateandtime-swift.property"
    },
    {
        "index": 23,
        "text": "static let requireAutomaticDateAndTime: SettingMetadata<Bool>",
        "href": "https://developer.apple.com/documentation/managedsettings/dateandtimesettings/requireautomaticdateandtime-swift.type.property"
    },
    {
        "index": 24,
        "text": "var passcode: PasscodeSettings",
        "href": "https://developer.apple.com/documentation/managedsettings/managedsettingsstore/passcode"
    },
    {
        "index": 25,
        "text": "PasscodeSettings",
        "href": "https://developer.apple.com/documentation/managedsettings/passcodesettings"
    },
    {
        "index": 26,
        "text": "var lockPasscode: Bool?",
        "href": "https://developer.apple.com/documentation/managedsettings/passcodesettings/lockpasscode-swift.property"
    },
    {
        "index": 27,
        "text": "static let lockPasscode: SettingMetadata<Bool>",
        "href": "https://developer.apple.com/documentation/managedsettings/passcodesettings/lockpasscode-swift.type.property"
    },
    {
        "index": 28,
        "text": "var shield: ShieldSettings",
        "href": "https://developer.apple.com/documentation/managedsettings/managedsettingsstore/shield"
    }
]

# 下载并保存每个URL
for item in urls_data:
    # 获取URL和文件名
    url = item["href"]
    filename = item["text"].replace(".", "_") + ".md"
    filepath = os.path.join(output_dir, filename)
    
    # 构建转换URL
    jina_url = f"https://r.jina.ai/{url}"
    
    try:
        print(f"下载中: {item['text']} ({jina_url})")
        response = requests.get(jina_url)
        
        if response.status_code == 200:
            # 保存Markdown内容到文件
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(response.text)
            print(f"成功保存: {filepath}")
        else:
            print(f"下载失败: {url}, 状态码: {response.status_code}")
    
    except Exception as e:
        print(f"处理 {url} 时出错: {str(e)}")

print("所有文件下载完成!")