#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re

def complete_translate_configuring_languages():
    """完整翻译 configuring-languages.html 文件中的英文内容"""
    
    # 完整的翻译映射表
    translations = {
        # Nested objects section
        "<h4 id=\"nested-objects\"><a class=\"header\" href=\"#nested-objects\">Nested objects</a></h4>":
            "<h4 id=\"nested-objects\"><a class=\"header\" href=\"#nested-objects\">嵌套对象</a></h4>",
        
        "When configuring language server options in Zed, it's important to use nested objects rather than dot-delimited strings.":
            "在 Zed 中配置语言服务器选项时，重要的是使用嵌套对象而非点分隔的字符串。",
        
        "This is particularly relevant when working with more complex configurations.":
            "这在处理更复杂的配置时尤其相关。",
        
        "Let's look at a real-world example using the TypeScript language server:":
            "让我们看一个使用 TypeScript 语言服务器的实际示例：",
        
        "Suppose you want to configure the following settings for TypeScript:":
            "假设您要为 TypeScript 配置以下设置：",
        
        "Enable strict null checks": "启用严格的空值检查",
        "Set the target ECMAScript version to ES2020": "将目标 ECMAScript 版本设置为 ES2020",
        
        "Here's how you would structure these settings in Zed's":
            "以下是在 Zed 的",
        
        # Configuration options section
        "<h4 id=\"possible-configuration-options\"><a class=\"header\" href=\"#possible-configuration-options\">Possible configuration options</a></h4>":
            "<h4 id=\"possible-configuration-options\"><a class=\"header\" href=\"#possible-configuration-options\">可能的配置选项</a></h4>",
        
        "Depending on how a particular language server is implemented, they may depend on different configuration options, both specified in the LSP.":
            "根据特定语言服务器的实现方式，它们可能依赖于 LSP 中指定的不同配置选项。",
        
        "Sent once during language server startup, requires server's restart to reapply changes.":
            "在语言服务器启动时发送一次，需要重启服务器以重新应用更改。",
        
        "For example, rust-analyzer and clangd rely on this way of configuring only.":
            "例如，rust-analyzer 和 clangd 仅依赖这种配置方式。",
        
        "May be queried by the server multiple times.":
            "可能会被服务器多次查询。",
        
        "Most of the servers would rely on this way of configuring only.":
            "大多数服务器仅依赖这种配置方式。",
        
        "Apart of the LSP-related server configuration options, certain servers in Zed allow configuring the way binary is launched by Zed.":
            "除了与 LSP 相关的服务器配置选项外，Zed 中的某些服务器允许配置 Zed 启动二进制文件的方式。",
        
        "Language servers are automatically downloaded or launched if found in your path, if you wish to specify an explicit alternate binary you can specify that in settings:":
            "语言服务器会自动下载或在路径中找到时启动，如果您希望指定明确的替代二进制文件，可以在设置中指定：",
        
        "Whether to fetch the binary from the internet, or attempt to find locally.":
            "是否从互联网获取二进制文件，还是尝试在本地查找。",
        
        # Enabling/Disabling section
        "You can toggle language server support globally or per-language:":
            "您可以全局或按语言切换语言服务器支持：",
        
        "This disables the language server for Markdown files, which can be useful for performance in large documentation projects.":
            "这会禁用 Markdown 文件的语言服务器，这对大型文档项目的性能很有用。",
        
        "You can configure this globally in your":
            "您可以在",
        
        "or inside a": "中全局配置，或在项目目录中的",
        
        "in your project directory.": "中配置。",
        
        # Formatting and Linting section
        "Zed provides support for code formatting and linting to maintain consistent code style and catch potential issues early.":
            "Zed 支持代码格式化和代码检查，以保持一致的代码风格并及早发现潜在问题。",
        
        "Zed supports both built-in and external formatters.":
            "Zed 支持内置和外部格式化工具。",
        
        "See": "查看",
        "docs for more.": "文档了解更多。",
        
        "You can configure formatters globally or per-language in your": 
            "您可以在您的设置中全局或按语言配置格式化工具",
        
        "This example uses Prettier for JavaScript and the language server's formatter for Rust, both set to format on save.":
            "此示例对 JavaScript 使用 Prettier，对 Rust 使用语言服务器的格式化工具，两者都设置为保存时格式化。",
        
        "To disable formatting for a specific language:":
            "要禁用特定语言的格式化：",
        
        # Linters section
        "Linting in Zed is typically handled by language servers.":
            "Zed 中的代码检查通常由语言服务器处理。",
        
        "Many language servers allow you to configure linting rules:":
            "许多语言服务器允许您配置代码检查规则：",
        
        "This configuration sets up ESLint to organize imports on save for JavaScript files.":
            "此配置设置 ESLint 在保存 JavaScript 文件时整理导入。",
        
        "To run linter fixes automatically on save:":
            "要在保存时自动运行代码检查修复：",
        
        # Integration section
        "Zed allows you to run both formatting and linting on save.":
            "Zed 允许您在保存时同时运行格式化和代码检查。",
        
        "Here's an example that uses Prettier for formatting and ESLint for linting JavaScript files:":
            "以下示例使用 Prettier 进行格式化，使用 ESLint 对 JavaScript 文件进行代码检查：",
        
        # Troubleshooting section
        "If you encounter issues with formatting or linting:":
            "如果您遇到格式化或代码检查问题：",
        
        "Check Zed's log file for error messages (Use the command palette:":
            "检查 Zed 的日志文件中的错误消息（使用命令面板：",
        
        "Ensure external tools (formatters, linters) are correctly installed and in your PATH":
            "确保外部工具（格式化工具、代码检查工具）已正确安装并在您的 PATH 中",
        
        "Verify configurations in both Zed settings and language-specific config files (e.g.,":
            "验证 Zed 设置和语言特定配置文件中的配置（例如，",
        
        # Syntax highlighting section
        "Zed offers customization options for syntax highlighting and themes, allowing you to tailor the visual appearance of your code.":
            "Zed 提供语法高亮和主题的自定义选项，允许您定制代码的视觉外观。",
        
        "Zed uses Tree-sitter grammars for syntax highlighting.":
            "Zed 使用 Tree-sitter 语法进行语法高亮。",
        
        "Override the default highlighting using the":
            "使用",
        
        "setting.": "设置覆盖默认高亮。",
        
        "This example makes comments italic and changes the color of strings:":
            "此示例使注释变为斜体并更改字符串的颜色：",
        
        # Theme selection
        "Change your theme:": "更改您的主题：",
        "Use the theme selector": "使用主题选择器",
        "Or set it in your": "或在您的设置中设置",
        
        "Create custom themes by creating a JSON file in": 
            "通过在指定目录中创建 JSON 文件来创建自定义主题",
        
        "Zed will automatically detect and make available any themes in this directory.":
            "Zed 将自动检测并提供此目录中的任何主题。",
        
        # Theme extensions
        "Zed supports theme extensions.":
            "Zed 支持主题扩展。",
        
        "Browse and install theme extensions from the Extensions panel":
            "从扩展面板浏览和安装主题扩展",
        
        "To create your own theme extension, refer to the":
            "要创建自己的主题扩展，请参考",
        
        "guide.": "指南。",
        
        # Language server features
        "Inlay hints provide additional information inline in your code, such as parameter names or inferred types.":
            "内嵌提示在您的代码中内联提供附加信息，如参数名称或推断类型。",
        
        "Configure inlay hints in your": "在您的设置中配置内嵌提示",
        
        "For language-specific inlay hint settings, refer to the documentation for each language.":
            "对于语言特定的内嵌提示设置，请参考每种语言的文档。",
        
        # Code actions
        "Code actions provide quick fixes and refactoring options.":
            "代码操作提供快速修复和重构选项。",
        
        "Access code actions using the":
            "使用",
        
        "command or by clicking the lightbulb icon that appears next to your cursor when actions are available.":
            "命令访问代码操作，或在有操作可用时单击光标旁边出现的灯泡图标。",
        
        # Go to definition and references
        "Use these commands to navigate your codebase:":
            "使用这些命令导航您的代码库：",
        
        # Rename symbol
        "To rename a symbol across your project:":
            "要在项目中重命名符号：",
        
        "Place your cursor on the symbol":
            "将光标放在符号上",
        "Use the": "使用",
        "command": "命令",
        "Enter the new name and press Enter":
            "输入新名称并按 Enter",
        
        "These features depend on the capabilities of the language server for each language.":
            "这些功能取决于每种语言的语言服务器功能。",
        
        "When renaming a symbol that spans multiple files, Zed will open a preview in a multibuffer.":
            "重命名跨多个文件的符号时，Zed 将在多缓冲区中打开预览。",
        
        "This allows you to review all the changes across your project before applying them.":
            "这允许您在应用更改之前查看项目中的所有更改。",
        
        "To confirm the rename, simply save the multibuffer.":
            "要确认重命名，只需保存多缓冲区。",
        
        "If you decide not to proceed with the rename, you can undo the changes or close the multibuffer without saving.":
            "如果您决定不继续重命名，可以撤消更改或关闭多缓冲区而不保存。",
        
        # Hover information
        "Use the": "使用",
        "command to display information about the symbol under the cursor.":
            "命令显示光标下符号的信息。",
        
        "This often includes type information, documentation, and links to relevant resources.":
            "这通常包括类型信息、文档和相关资源的链接。",
        
        # Workspace symbol search
        "The": "的",
        "command allows you to search for symbols (functions, classes, variables) across your entire project.":
            "命令允许您在整个项目中搜索符号（函数、类、变量）。",
        
        "This is useful for quickly navigating large codebases.":
            "这对于快速导航大型代码库很有用。",
        
        # Code completion
        "Zed provides intelligent code completion suggestions as you type.":
            "Zed 在您输入时提供智能代码完成建议。",
        
        "You can manually trigger completion with the":
            "您可以使用",
        
        "Use": "使用",
        "or": "或",
        "to accept suggestions.": "接受建议。",
        
        # Diagnostics
        "Language servers provide real-time diagnostics (errors, warnings, hints) as you code.":
            "语言服务器在您编码时提供实时诊断（错误、警告、提示）。",
        
        "View all diagnostics for your project using the":
            "使用",
        
        "command.": "命令查看项目的所有诊断。",
        
        # Additional translations for file associations section
        " starting with \"Dockerfile\"": " 开头的文件应用 Dockerfile 语法",
        
        # Additional fixes
        "<li>对任何以 \"Dockerfile\"</li>": "<li>对任何以 \"Dockerfile\" 开头的文件应用 Dockerfile 语法</li>",
    }
    
    # 读取文件
    file_path = '/Users/liyd/Tools/myspace/script-hub/zed_doc_cn/site/configuring-languages.html'
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 应用翻译
    for english, chinese in translations.items():
        content = content.replace(english, chinese)
    
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("完整翻译已应用到 configuring-languages.html")

if __name__ == "__main__":
    complete_translate_configuring_languages()