# 推送配置指南

OOH Signal 支持三种微信推送方式，任选其一即可。

## 方式一：企业微信群机器人（推荐）

适合有企业微信群的团队。

### 配置步骤

1. 打开企业微信，进入目标群
2. 点击群名 → 群机器人 → 添加机器人
3. 输入机器人名称（如：OOH Signal）
4. 创建后复制 Webhook 地址

### 设置 GitHub Secrets

打开 https://github.com/lcolpitr-ui/ooh-signal/settings/secrets/actions

添加：
- Name: `WECHAT_WEBHOOK`
- Value: 你的 Webhook 地址

---

## 方式二：Server酱（个人微信）

适合推送到个人微信，免费版每天5条。

### 配置步骤

1. 打开 https://sct.ftqq.com/
2. 微信扫码登录
3. 点击「SendKey」复制 Key

### 设置 GitHub Secrets

添加：
- Name: `SERVERCHAN_SENDKEY`
- Value: 你的 SendKey

---

## 方式三：PushPlus（个人微信）

适合推送到个人微信，免费版每天200条。

### 配置步骤

1. 打开 https://www.pushplus.plus/
2. 微信扫码登录
3. 复制 Token

### 设置 GitHub Secrets

添加：
- Name: `PUSHPLUS_TOKEN`
- Value: 你的 Token

---

## 推送时间

默认每天早上 8:00 推送。如需修改，编辑 `.github/workflows/push.yml`：

```yaml
schedule:
  - cron: '0 8 * * *'  # 改成你想要的时间
```

## 手动触发

在 GitHub Actions 页面点击「Run workflow」即可手动推送。
