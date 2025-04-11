# Cursor自动化管理工具

基于PyQt5和Playwright的Cursor自动化管理工具，用于自动化操作Cursor编辑器。

## 功能特点

- 基于PyQt5的图形界面
- 使用Playwright进行浏览器自动化
- 支持使用本地Chrome浏览器进行自动化
- 可配置的自动化任务
- 支持任务调度
- 账号信息仅保存在JSON文件中（不使用数据库）
- 完整的Cursor相关路径配置

## 安装

1. 安装依赖项：

```bash
pip install -r requirements.txt
```

2. 安装Playwright浏览器：

```bash
python -m playwright install
```

## 使用方法

运行主程序：

```bash
python main.py
```

## 配置说明

### Cursor配置

通过系统配置选项卡可以设置以下Cursor相关路径：

- **可执行文件路径**：Cursor可执行文件的路径
- **数据目录**：Cursor数据存储目录
- **配置文件**：Cursor配置文件路径
- **数据库文件**：Cursor状态数据库文件路径
- **机器ID路径**：机器ID文件路径
- **资源路径**：Cursor资源文件路径
- **更新程序路径**：Cursor更新程序路径
- **更新配置路径**：Cursor更新配置文件路径
- **产品配置路径**：Cursor产品配置文件路径

### 浏览器自动化配置

- **使用本地Chrome浏览器**：启用后将使用本地安装的Chrome浏览器进行自动化，而非Playwright内置的Chromium
- **无界面模式**：在无界面模式下运行浏览器
- **用户代理**：自定义浏览器标识(User-Agent)
- **窗口大小**：设置浏览器窗口尺寸
- **其他选项**：包括禁用GPU、禁用图片、无痕模式等

## 账号管理

账号信息仅保存在JSON文件中(`config/accounts.json`)，不会存储到数据库中，提高了数据安全性。

## 项目结构

```
cursor-auto-manager/
├── config/              # 配置文件
│   ├── __init__.py
│   ├── accounts.json    # 账号信息存储文件
│   ├── system_config.json # 系统配置文件
│   └── cursor_auth.json # Cursor原始授权数据
├── core/                # 核心功能
│   ├── __init__.py
│   ├── automation.py    # 自动化任务
│   ├── browser.py       # 浏览器管理器
│   ├── account_manager.py # 账号管理器
│   └── db_manager.py    # 数据库管理器
├── ui/                  # 用户界面
│   ├── __init__.py
│   ├── main_window.py   # 主窗口
│   └── system_config_tab.py # 系统配置选项卡
├── utils/               # 工具函数
│   ├── __init__.py
│   ├── system_config.py # 系统配置管理器
│   └── logger.py        # 日志管理
├── resources/           # 资源文件
│   └── icons/
├── main.py              # 主程序
├── requirements.txt     # 依赖项
└── README.md            # 说明文档
```

## 开发

### 添加新的自动化任务

在`core/automation.py`中添加新的任务类，并在UI中注册。

### 浏览器自动化

本工具默认使用本地Chrome浏览器进行自动化，可以在系统配置中修改相关设置。如果需要使用内置的Chromium，可以关闭"使用本地Chrome浏览器"选项。

## 系统要求

- Windows 10/11
- Python 3.8+
- Chrome浏览器（如需使用本地浏览器功能）

## 许可证

MIT 