# SpeakStep Content

SpeakStep 的每日 B2 课程内容仓库。GitHub Actions 每天香港时间约 06:00 生成一课，
验证 JSON 后提交到 `feed/daily-lessons.json`。Mac 应用启动时会从该文件更新课程，
保持打开时也会定期再次检查。

## 第一次启用（只做一次）

1. 在 GitHub 新建公开仓库 `speakstep-content`。
2. 把本文件夹的全部内容上传到仓库根目录。
3. 打开仓库的 **Settings → Secrets and variables → Actions**。
4. 新建 Repository secret：名称 `OPENAI_API_KEY`，值为你的 OpenAI API 密钥。
5. 打开 **Actions → Publish daily B2 lesson → Run workflow**，先手动运行一次。
6. 看到绿色成功标记后，打开以下地址应显示 JSON：
   `https://raw.githubusercontent.com/sam823105-dev/speakstep-content/main/feed/daily-lessons.json`

## 成本与安全

- 默认模型是 `gpt-6-luna`，适合每天一次的成本敏感型结构化内容生成。
- API 密钥只放在 GitHub Secrets；不要写入 Swift、JSON 或提交记录。
- 生成内容在发布前会检查等级、时长、题目答案、跟读/对话所需字段。
- GitHub 的定时任务可能延迟几分钟，不能承诺精确到 06:00 整。

## 本地检查

```bash
python3 scripts/validate_feed.py
```

生成脚本必须有 `OPENAI_API_KEY` 才能调用 API。为了复现某一天，可以额外设置
`LESSON_DATE=2026-10-10`。模型也可以通过仓库变量 `OPENAI_MODEL` 修改。
