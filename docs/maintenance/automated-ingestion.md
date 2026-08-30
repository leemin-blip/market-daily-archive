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
scripts/validate_daily.py（fail closed）
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

## 正式调度

- 频率：每天运行，每周 7 天。
- 时间：设备本地时钟 08:00。
- 当前设备时区：`Asia/Shanghai`（UTC+8），与 SGT 同一时刻。
- 日报日期边界：`Asia/Singapore`。不使用纽约日期，也不随美国夏令时或冬令时切换。
- 如果设备将来切换到非 UTC+8 时区，任务会跟随设备时钟；需要人工确认是否仍符合 08:00 SGT 的预期。
- 周末和美国休市日仍运行，并根据 Master Prompt 生成 `market_closed` 休市版日报。

正式生成规则由仓库中的 `prompts/daily_market_report.md` 版本化管理。普通日报运行不得修改 Master Prompt 或 `PROJECT.md`。

## 输入契约

每次入库需要：

- 明确的 ISO 日期：`YYYY-MM-DD`。
- 一份 Markdown 日报。
- 第一个 H1 标题中包含同一个 ISO 日期。
- 正文至少保留一个 HTTPS Markdown 来源链接。
- 可选的一行摘要，用于首页和档案索引。

日报正文不做重新排版；如果输入没有 YAML front matter，工具只会在文件顶部补充 `title` 和 `description`。

自动生成的正式日报还必须包含 `report_type: trading_day` 或 `report_type: market_closed`，并通过发布前质量闸门。

## 发布前质量闸门

完整发布脚本在任何 Git 或导航修改之前先运行：

```bash
python3 scripts/validate_daily.py \
  --date 2026-08-31 \
  --input inbox/2026-08-31.md
```

以下情况 fail closed，不入库、不 commit、不 push：

- 输出为空、明显截断或整个报告被代码块包裹。
- 新加坡执行日期或唯一 H1 错误。
- `report_type` 缺失或无效。
- 对应交易日 / 休市版的关键章节缺失或内容明显为空。
- Sources 缺失，或可靠 HTTPS Markdown 链接低于自动校验底线。
- 正常交易日 Dashboard 缺少应跟踪的指标标签。

单个非关键数据或来源暂时不可获得不等于整篇生成失败。只要报告结构完整、其余研究充分并达到来源底线，可以在对应位置明确写 `数据暂不可得`、`尚未确认` 或 `暂未发现单一明确催化剂` 后继续发布。不得猜测或用盘中值替代收盘值。

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
- 生成或质量校验失败：只允许在 Git 忽略的 `inbox/` 留下草稿用于诊断；仓库和远程不发生变化。修正或重新生成后可用同一日期重试。
- 本地 commit 成功但 push 失败：修复网络或认证后，使用同一命令重试；脚本会继续推送现有 commit。
- push 成功但部署验证失败：使用同一命令重试；脚本会重新核对同一提交对应的 Pages workflow 和线上页面。
- 本地分支落后或与远程分叉：停止自动流程，要求人工处理，不做自动合并或强制推送。

## 定时任务接入状态

仓库内的 Master Prompt、质量闸门、确定性入库和发布工具已经建立。桌面端任务 `Market Daily Archive 日报入库` 已处于 Active，每天跟随设备本地时钟 08:00 运行。首次运行仍需确保电脑与桌面应用保持运行，并具备最小必要的工作区写入和 GitHub 网络权限。

应观察最初几次真实运行并完成无人值守验收，再决定是否进入月报开发。
