# 意大利语每日学习推送

这个项目会每天意大利时间早上 9:00，通过 Telegram Bot 推送一份适合中文母语者的意大利语生活词汇学习内容。

## 功能

- 每天随机选择一个生活主题
- 每次推送 5 个意大利语单词
- 每个词包含中文意思、意大利语例句和中文翻译
- 每天附带一个小练习
- 使用本地 `words.json` 作为词库
- 使用 `.state.json` 记录历史，尽量避免连续重复主题或完全一样的 5 个词组合
- 支持中文显示

## 文件说明

- `main.py`：主程序，负责读取词库、生成内容、定时推送
- `words.json`：本地词库
- `.env.example`：环境变量示例
- `requirements.txt`：Python 依赖
- `README.md`：使用说明

## 1. 创建 Telegram Bot

1. 在 Telegram 搜索 `@BotFather`
2. 发送 `/newbot`
3. 按提示设置 bot 名称
4. BotFather 会给你一个 token，格式大概像：

```text
123456789:ABCDEF_your_token_here
```

## 2. 获取 CHAT_ID

1. 在 Telegram 打开你刚创建的 bot
2. 给 bot 发送任意一句话，比如 `你好`
3. 在浏览器打开下面的网址，把 `<YOUR_TOKEN>` 换成你的 token：

```text
https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
```

4. 在返回结果里找到 `chat` 里的 `id`，这就是 `TELEGRAM_CHAT_ID`

如果你要推送到群组，需要先把 bot 拉进群，并在群里发一条消息，然后同样用 `getUpdates` 找群的 `chat.id`。群组 id 通常是负数。

## 3. 配置环境变量

复制 `.env.example` 为 `.env`：

```bash
cp .env.example .env
```

然后编辑 `.env`：

```env
TELEGRAM_BOT_TOKEN=你的 Telegram Bot token
TELEGRAM_CHAT_ID=你的 chat id
SEND_ON_START=false
```

不要把 `.env` 发给别人，也不要上传到公开仓库。

## 4. 安装依赖

建议使用虚拟环境：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 5. 运行

```bash
python main.py
```

程序启动后，会在每天意大利时间早上 9:00 自动推送。

如果你想启动时立刻测试推送一次，把 `.env` 里的配置改成：

```env
SEND_ON_START=true
```

测试成功后，建议再改回：

```env
SEND_ON_START=false
```

## 6. 长期运行建议

这个程序需要保持运行，才能每天自动推送。你可以把它放在服务器、树莓派、NAS，或者一台长期不关机的电脑上运行。

最简单的方式是开着终端运行：

```bash
python main.py
```

如果你希望它后台长期运行，可以后续再加 `systemd`、Docker、macOS LaunchAgent 或云服务器部署配置。

## Railway 部署

项目已经包含 Railway 所需文件：

- `Procfile`
- `runtime.txt`
- `railway.json`
- `requirements.txt`
- `.gitignore`

`.env` 和 `.state.json` 已经放进 `.gitignore`，不要上传到 GitHub。

### 上传到 GitHub

```bash
git init
git add .
git commit -m "Deploy Italian learning Telegram bot"
git branch -M main
git remote add origin https://github.com/你的用户名/你的仓库名.git
git push -u origin main
```

### 连接 Railway

1. 打开 Railway
2. 点击 `New Project`
3. 选择 `Deploy from GitHub repo`
4. 选择这个项目仓库
5. Railway 会自动识别 Python 项目并安装依赖

### Railway 环境变量

在 Railway 项目的 `Variables` 里添加：

```env
TELEGRAM_BOT_TOKEN=你的 Telegram Bot token
TELEGRAM_CHAT_ID=你的 chat id
```

不需要在 Railway 上传 `.env` 文件。

### 启动

Railway 会使用 `railway.json` 中的启动命令：

```bash
python main.py
```

部署完成后，程序会持续运行：

- 每天意大利时间 09:00 自动推送
- 收到 `/start` 后发送测试消息并立刻推送一次当天词汇
- 使用 `Europe/Rome` 时区

## 自定义词库

你可以直接编辑 `words.json` 增加主题或单词。每个单词需要保持下面这些字段：

```json
{
  "italian": "bonifico",
  "chinese": "银行转账",
  "example_it": "Vorrei fare un bonifico.",
  "example_zh": "我想做一笔银行转账。"
}
```
