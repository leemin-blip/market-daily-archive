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

### 一键检查并补跑今日日报

V2 支持手动检查与故障恢复；自动 08:00 任务与手动恢复入口共用同一套幂等、Validator 和 fail-closed 规则。原有定时任务、发布脚本和部署 workflow 不变。

在 Work / Codex 中说：**检查并补跑今日日报**。仓库根目录的 `AGENTS.md` 定义了这一操作的恢复流程。

也可以在项目目录直接运行：

```bash
./scripts/check_and_recover_daily.sh
```

无需填写日期或理解各个发布步骤。默认使用 Asia/Singapore 今天日期；已有草稿或归档始终优先复用。只有不存在日报时才尝试生成。

| 检查到的状态 | 恢复动作 |
| --- | --- |
| 本地和远程都没有日报 | 动态读取 PROJECT.md 和最新版 Master Prompt；生成、Validator、入库、构建、提交与发布 |
| inbox 有完整草稿 | 先 Validator，复用草稿，不再生成 |
| 正式文件已存在但未提交，或导航只完成一部分 | 与现有入库器在临时目录生成的预期结果比对，仅补齐缺失的确定性导航，再严格构建和提交 |
| 本地已提交、push 失败 | 检查未推送历史只包含本次日报的确定性结果；复用原提交，构建并 push，核对远程 SHA |
| 远程已收到，Actions 排队或运行中 | 等待同一 SHA 的 workflow，不新建 commit |
| 对应 Actions 失败、取消或超时 | 远程 SHA 未变化时，最多重跑一次完整 workflow；继续失败则报告 Actions 层 |
| 对应 workflow 长时间未出现 | 等待约一分钟；确认现有 workflow 支持 workflow_dispatch 且远程 SHA 未变化后，仅触发一次 |
| Actions 成功但 Pages 不正常 | 有限重试 HTTP 检查；仍失败则报告 Pages 层，下次从验证继续，不重新生成或 commit |
| 今日已完整上线 | 返回“今日 Market Daily Archive 日报已完整发布，无需补跑。”；不生成、构建、commit、push 或重复部署 |

每次输出 Report date、Draft status、Validator status、Archive status、Local commit status、Remote push status、GitHub Actions status、GitHub Pages status 和 Final result。失败时另有 Blocked layer 与 Next step，区分 `生成 / Validator / Import / Build / Commit / Push / Actions / Pages`。未经过的层标为“未检查”，不会伪报成功。

最终页面必须为 HTTP 200，并匹配日报 H1、摘要和正文来源链接；仅在导航中出现日期不算成功。恢复前后直接查询远程 SHA，只有本地缺少对应提交对象时才 fetch；远程变化时停止并要求重试核验。

### 生成能力与安全边界

- Work / Codex 会话使用 `--no-generate --json` 检查；只有退出码 3 才由当前会话生成，然后再次调用同一恢复入口。完整已有草稿不调用模型。
- 本地终端入口在缺少日报时使用已安装并登录的 Codex CLI，启用实时搜索、只读沙盒，将最终响应写到 Git 忽略的临时目录。仅当生成器成功退出且 Validator 通过，才以不覆盖已有文件的方式接纳为正式 inbox 草稿。CLI、认证、额度或网络不可用时会明确停止，不需要也不会把 API Key 写入仓库。[OpenAI 非交互执行说明](https://learn.chatgpt.com/docs/non-interactive-mode)
- 生成失败或超时，即使留下看似完整的输出，也不自动发布。诊断输出留在 `inbox/.generation-日期-*/`；通过当前会话人工检查或重新生成后再恢复。
- 所有同日期内容比较沿用现有换行规范。真正不同的正文、来源或 front matter 禁止自动覆盖，包括本地提交、草稿与远程之间的冲突。
- 未提交内容必须精确匹配“现有入库器应用于已提交快照”的结果，才可以恢复；无关或混合的暂存内容、手工修改过的导航会停止，绝不自动 stash、reset 或顺带提交。
- 已完整发布的日报即使本地还有无关工作，也不会借补跑之名推送那些提交或修改那些文件。需要恢复时则要求工作区及未推送历史可以被严格归属于本次日报。
- 本地落后、分叉、删除已提交的日报、符号链接路径或检查期间发生并发变化均停止。多个手动恢复使用锁避免重叠；原 08:00 链路没有被改动，因此不要与其同时操作同一工作区。
- 网络或钥匙串访问受沙盒限制时，可能仍需要应用授权；这不代表必须重新登录。脚本复用已有 GH_CONFIG_DIR，不改 Git 认证配置。

高级入口：`--date YYYY-MM-DD` 指定需恢复的日期；`--json` 输出结构化摘要。退出码 0 表示完整发布或无需补跑，3 表示需要当前会话生成，1 表示某层失败，2 表示命令参数无效。操作不会自动开启月报功能。

### 原发布命令的恢复约定

- 同一天、相同内容再次导入：视为成功且不重复创建文件。
- 同一天、不同内容再次导入：安全失败，不覆盖已经发布的日报。
- 生成或质量校验失败：只允许在 Git 忽略的 `inbox/` 留下草稿用于诊断；仓库和远程不发生变化。修正或重新生成后可用同一日期重试。
- 本地 commit 成功但 push 失败：修复网络或认证后，使用同一命令重试；脚本会继续推送现有 commit。
- push 成功但部署验证失败：使用同一命令重试；脚本会重新核对同一提交对应的 Pages workflow 和线上页面。
- 本地分支落后或与远程分叉：停止自动流程，要求人工处理，不做自动合并或强制推送。

## 定时任务接入状态

仓库内的 Master Prompt、质量闸门、确定性入库和发布工具已经建立。桌面端任务 `Market Daily Archive 日报入库` 保持 Active，每天跟随设备本地时钟 08:00 运行。2026-08-31 首轮定时日报已成功发布并完成线上验证，但经历过沙盒认证访问的权限重试；仍需观察无权限介入时的稳定性。

新增手动恢复入口不替换定时任务，也不改变原发布脚本。应继续观察真实运行并完成无人值守验收，再决定是否进入月报开发。
