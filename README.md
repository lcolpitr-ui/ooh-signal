# OOH Signal — 户外广告投放信号情报系统

帮户外广告从业者**发现哪些品牌正在释放投放信号**，AI 自动打分排序，让销售优先跟进高意向客户。

## 核心功能

- **信号时间线** — 卡片式展示品牌动态，含 AI 投放评分（0-100）和推荐理由
- **AI 打分引擎** — 规则引擎 + DeepSeek LLM 深度语义分析
- **品牌识别** — 自动从新闻中提取品牌、行业、规模等信息
- **多源采集** — RSS、网页爬虫、商业数据源，持续扩展中
- **每日日报** — 自动生成高分信号汇总，支持 RSS 订阅
- **推送通知** — 支持企业微信、ServerChan、PushPlus、飞书

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Next.js 16 + React 19 + Tailwind v4 |
| 数据存储 | SQLite（本地）/ JSON（Vercel 部署） |
| AI 引擎 | DeepSeek API |
| 数据采集 | Python（feedparser + BeautifulSoup + requests） |
| CI/CD | GitHub Actions（定时采集 + 定时推送） |
| 部署 | Vercel（香港区域） |

## 数据源

### 已实现
| 来源 | 类型 | 采集方式 |
|------|------|---------|
| 36kr | 品牌扩张/融资 | RSS + 爬虫 |
| 钛媒体 | 行业动态 | RSS |
| 巨潮资讯 | 上市公司公告 | 爬虫 |
| 赢商网 | 品牌扩张/商业地产 | 爬虫 |
| 新浪财经 | 企业新闻 | 爬虫 |
| IT桔子 | 融资事件 | 爬虫 |

### 待扩展
微博、小红书、抖音、微信公众号等社交媒体信号源。

## 快速开始

### 环境要求

- Node.js 18+
- Python 3.11+
- DeepSeek API Key

### 安装

```bash
# 前端依赖
npm install

# Python 依赖
pip install -r scripts/requirements.txt
```

### 配置

```bash
cp .env.example .env.local
# 编辑 .env.local，填入 DEEPSEEK_API_KEY
```

### 初始化数据库

```bash
python scripts/init_db.py
```

### 运行采集

```bash
python scripts/collect.py
```

### 导出数据（Vercel 部署需要）

```bash
python scripts/export_json.py
```

### 启动开发服务器

```bash
npm run dev
```

访问 [http://localhost:3000](http://localhost:3000)

## 项目结构

```
├── public/data/          # JSON 数据（Vercel 部署用）
├── scripts/
│   ├── collectors/       # 数据采集器（RSS、爬虫）
│   ├── processors/       # AI 处理器（打分、品牌识别）
│   ├── config/           # 数据源配置
│   ├── collect.py        # 采集主入口
│   ├── export_json.py    # 导出 JSON
│   ├── generate_daily.py # 生成日报
│   └── push.py           # 推送通知
├── src/
│   ├── app/              # Next.js 页面 + API 路由
│   ├── components/       # React 组件
│   └── lib/              # 工具函数和数据加载
└── data/                 # SQLite 数据库 + 日报文件
```

## CI/CD

项目通过 GitHub Actions 自动运行：

- **collect.yml** — 每小时采集数据，生成日报，导出 JSON，自动提交
- **push.yml** — 每天早上 8 点推送高分信号通知

### 配置 Secrets

在 GitHub 仓库 Settings > Secrets 中添加：

| Secret | 说明 |
|--------|------|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 |
| `WECHAT_WEBHOOK` | 企业微信群机器人 Webhook |
| `SERVERCHAN_SENDKEY` | ServerChan 发送密钥 |
| `PUSHPLUS_TOKEN` | PushPlus Token |

## 部署

项目已配置 Vercel 部署（`vercel.json`），推送到 main 分支自动部署。

> 注意：Vercel 环境下使用静态 JSON 数据（通过 `export_json.py` 生成），SQLite 直连仅用于本地开发和 GitHub Actions。

## License

MIT
