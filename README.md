# SpeakStep Content

SpeakStep 的每日 B2 课程内容仓库。GitHub Actions 每天香港时间约 06:00 发布一课，
验证 JSON 后提交到 `feed/daily-lessons.json`。Mac 应用启动时会从该文件更新课程，
保持打开时也会定期再次检查。

## 当前的无密钥模式

不需要 `OPENAI_API_KEY`，也不需要在 GitHub Secrets 中保存任何密钥。工作流从
仓库内已经人工检查的 7 节 B2 课程中按日期轮换，适合先跑通第一版。它能保证
每天联网发布，但不会每天由 AI 创作全新内容；课程会以 7 天为周期复习。

打开 **Actions → Publish daily B2 lesson → Run workflow** 可以手动测试。看到绿色
成功标记后，打开以下地址应显示 JSON：
   `https://raw.githubusercontent.com/sam823105-dev/speakstep-content/main/feed/daily-lessons.json`

## 成本与安全

- 当前模式不调用任何付费 AI API，没有模型调用费，也没有密钥泄漏风险。
- 公开仓库使用标准 GitHub-hosted runner 时，GitHub Actions 分钟免费。
- 生成内容在发布前会检查等级、时长、题目答案、跟读/对话所需字段。
- GitHub 的定时任务可能延迟几分钟，不能承诺精确到 06:00 整。
- 当前课程库只有 7 节，重复是已知限制。扩充为 30 或 90 节后可减少重复。

## 本地检查

```bash
python3 scripts/validate_feed.py
```

为了复现某一天，可以设置 `LESSON_DATE=2026-10-17` 后运行生成脚本。课程库的
首个周期（2026-10-10 至 2026-10-16）会一直保留，供后续日期轮换使用。
