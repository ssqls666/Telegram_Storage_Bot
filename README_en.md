# ⚠ This program is developed with AI assistance ⚠
# ☁️ Telegram_Storage_Bot - Telegram File Storage Bot

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)](https://core.telegram.org/bots)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/ssqls666/Telegram_Storage_Bot/pulls)

## 📸 Interface Preview

| Dashboard | Bot Management | Settings Page |
|-----------|----------------|---------------|
| Usage Pie Chart | Bot Token Configuration | Proxy Settings |
| Real-time Traffic Graph | User Storage Rankings | Whitelist/Blacklist Mode |
| Capacity Monitoring | Detailed Usage Breakdown | User Capacity Allocation |

## ✨ Core Features

### 🤖 Bot Commands

| Command | Description |
|---------|-------------|
| `/s` or `/start` | Start the bot |
| `/up` or `/update` | Upload files |
| `/dl` or `/download` | Download files |
| `/q` or `/query` | Check storage usage, list all files |
| `/h` or `/help` | Display help information |

### 📊 GUI Management Panel

- **Dashboard**  
  - Real-time total storage usage (pie chart)  
  - 10-minute network traffic graph (upload/download separated)  
  - Welcome message + current time

- **Settings Page**  
  - Proxy configuration (HTTP/SOCKS5/SOCKS4)  
  - User storage capacity (global default / per-user settings)  
  - Admin list management  
  - Whitelist/Blacklist mode (guest access permissions)

- **Bot Page**  
  - Add/remove bots (multiple bot support)  
  - Bot nickname settings  
  - Storage usage statistics & per-user breakdown

- **Files Page**  
  - Browse files in `/bot/{user_id}` directory  
  - Manual deletion, search functionality

### 🛡️ Security & Logging

- User file isolation: `/bot/{user_id}` separate directories  
- Pre-upload space verification, automatic rejection on quota exceeded  
- All operations logged to `/log/YYYY-MM-DD.log`  
- Admin identification via `tg_admin_ids` list

## 🚀 Quick Start

### Requirements

- Python 3.10 or higher  
- Telegram Bot Token (get from [@BotFather](https://t.me/BotFather))

### Installation & Running

1. **Clone the repository**

```bash
git clone https://github.com/ssqls666/Telegram_Storage_Bot.git
cd Telegram_Storage_Bot
