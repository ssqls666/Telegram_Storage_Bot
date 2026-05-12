If you are an English user :https://github.com/ssqls666/Telegram_Storage_Bot/blob/main/README_en.md
源项目名为 “清风网盘” ，后更改为 Telegram_Storage_Bot
# ⚠该程序使用ai辅助开发⚠
# ☁️ Telegram_Storage_Bot - Telegram 文件储存机器人

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)](https://core.telegram.org/bots)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/ssqls666/Telegram_Storage_Bot/pulls)

## 📸 界面预览

| 仪表盘 | 机器人管理 | 设置页面 |
|--------|------------|----------|
| 总用量圆饼图 | 机器人 Token 配置 | Proxy 代理设置 |
| 实时流量曲线 | 用户硬盘使用排行 | 黑白名单模式 |
| 容量使用监控 | 详细用量分布 | 用户容量分配 |


## ✨ 核心功能

### 🤖 机器人指令

| 指令 | 说明 |
|------|------|
| `/s` 或 `/start` | 启动机器人 |
| `/up` 或 `/update` | 上传文件 |
| `/dl` 或 `/download` | 下载文件 |
| `/q` 或 `/query` | 查询容量使用情况，列出所有文件 |
| `/h` 或 `/help` | 显示帮助信息 |

### 📊 图形化管理面板（GUI）

- **仪表盘**  
  - 实时显示总使用量（圆饼图）  
  - 10分钟网络流量曲线（上传/下载分离）  
  - 欢迎用户 + 当前时间

- **设置页**  
  - Proxy 代理配置（HTTP）  
  - 用户储存容量（全局默认 / 单独设置）  
  - 管理员列表管理  
  - 白名单/黑名单模式（游客使用权限）

- **机器人页**  
  - 添加/删除机器人（多个 Bot 支持）  
  - 备注机器人名称  
  - 硬盘使用统计 & 按用户明细展开

- **文件页**  
  - 浏览 `/bot/{用户ID}` 下的文件  
  - 手动删除、搜索

### 🛡️ 安全与日志

- 用户文件隔离：`/bot/{用户ID}` 独立目录  
- 上传前校验可用空间，超限自动拒绝  
- 全操作记录至 `/log/YYYY-MM-DD.log`  
- 管理员通过 `tg_admin_ids` 列表识别

## 🚀 快速开始

### 环境要求

- Python 3.10 或更高版本  
- Telegram Bot Token（通过 [@BotFather](https://t.me/BotFather) 获取）

### 安装与运行

1. **克隆项目**

```bash
git clone https://github.com/ssqls666/Telegram_Storage_Bot.git
cd Telegram_Storage_Bot
