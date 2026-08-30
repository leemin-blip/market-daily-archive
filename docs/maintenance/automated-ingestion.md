---
title: V2 自动入库
description: Market Daily Archive V2 每日入库与发布操作说明
---

# V2 自动入库与发布

V2 的最小可靠链路将“内容生成”和“仓库修改”分开：

```text
ChatGPT 桌面端项目级定时任务
        ↓ 生成 Markdown
inbox/YYYY-MM-DD.md（Git 忽略）
        ↓
scripts/import_daily.py
        ↓
日报文件 + 年/月索引 + 总档案 + MkDocs 导航
        ↓
scripts/publish_daily.sh
        ↓
严格构建 → commit → push → Actions → Pages → 线上验证
```

## 为什么使用本地项目级定时任务

OpenAI 官方文档说明，网页端定时任务不能直接操作本机目录；ChatGPT 桌面端的项目级定时任务可以在本地项目目录或隔离 worktree 中运行，但电脑需要保持开机且应用需要运行。定时任务仍受文件系统、网络和审批策略约束。[Scheduled tasks 官方文档](https://learn.chatgpt.com/docs/automations)

本项目不假设网页端 ChatGPT 任务能够无条件写入 GitHub，也不把 Token、API Key 或其他凭证写入仓库。

## 输入契约

每次入库需要：

- 明确的 ISO 日期：`YYYY-MM-DD`。
- 一份 Markdown 日报。
- 第一个 H1 标题中包含同一个 ISO 日期。
- 正文至少保留一个 HTTPS Markdown 来源链接。
- 可选的一行摘要，用于首页和档案索引。

日报正文不做重新排版；如果输入没有 YAML front matter，工具只会在文件顶部补充 `title` 和 `description`。

## 手动验证入库

先把待导入日报保存到被 Git 忽略的 `inbox/`：

```bash
mkdir -p inbox
```

然后只运行入库和导航更新：

```bash
python3 scripts/import_daily.py \
  --date 2026-08-31 \
  --input inbox/2026-08-31.md \
  --summary "当日市场主线摘要"
```

## 完整发布

完整流程会要求工作区干净，并自动执行严格构建、提交、推送、远程提交核对、Pages workflow 等待和线上页面验证：

```bash
scripts/publish_daily.sh \
  2026-08-31 \
  inbox/2026-08-31.md \
  "当日市场主线摘要"
```

## 重复执行与恢复

- 同一天、相同内容再次导入：视为成功且不重复创建文件。
- 同一天、不同内容再次导入：安全失败，不覆盖已经发布的日报。
- 本地 commit 成功但 push 失败：修复网络或认证后，使用同一命令重试；脚本会继续推送现有 commit。
- push 成功但部署验证失败：使用同一命令重试；脚本会重新核对同一提交对应的 Pages workflow 和线上页面。
- 本地分支落后或与远程分叉：停止自动流程，要求人工处理，不做自动合并或强制推送。

## 定时任务接入状态

仓库内的确定性入库和发布工具已经建立。真正的每日无人值守运行还需要：

1. 确认日报生成时间与现有 ChatGPT 日报提示词。
2. 在 ChatGPT 桌面端为本地项目创建定时任务。
3. 为该任务授予最小必要的工作区写入和 GitHub 网络权限。
4. 观察最初几次真实运行，再决定是否进入月报开发。
