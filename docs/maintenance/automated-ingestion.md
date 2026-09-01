---
title: V2 自动入库
description: Market Daily Archive V2 每日入库与发布操作说明
---

# V2 自动入库与发布

V2 Plan B 采用 **Single Generation, Multiple Outputs / 一次生成，多个出口**：

```text
GitHub Actions（00:00 UTC / 08:00 SGT）
        ↓
OpenAI Responses API + Web Search
        ↓ 唯一 Markdown；仅在 runner 临时目录暂存
scripts/validate_daily.py（fail closed）
        ↓
scripts/import_daily.py
        ↓
日报文件 + 年/月索引 + 总档案 + MkDocs 导航
        ↓
严格构建 → commit → push main
        ↓
deploy-pages.yml → GitHub Pages → 线上正文验证
        ↓
ChatGPT 云端任务只读取同一份正式 Archive，不重新生成
```

AI 只负责研究和生成 Markdown。Validator、入库、导航、构建、提交、部署和页面验证全部保持确定性。

## 为什么采用 GitHub Actions + OpenAI API

隔离 canary 已证明 ChatGPT Cloud Scheduled Task 没有完成无人值守 GitHub 写入，不能作为可靠的云端交接层。Plan B 改由 GitHub Actions 调用 OpenAI 官方 Responses API；Responses API 支持内置 Web Search，生成器可在不依赖 Mac 的环境中实时研究。[Responses API](https://developers.openai.com/api/reference/cli/resources/responses/methods/create) · [OpenAI 模型目录](https://developers.openai.com/api/docs/models)

`prompts/daily_market_report.md` 仍是唯一长期 Prompt 真源。Workflow 读取文件正文，不复制 Master Prompt；`scripts/generate_daily.py` 只补充“必须联网研究、只返回完整 Markdown、失败不得返回残稿”的调用边界。

## 正式调度

- 目标频率：每天运行，每周 7 天。
- Cron：`0 0 * * *`，即 00:00 UTC / 08:00 Asia/Singapore，无 DST。
- 日报日期由 runner 使用 `Asia/Singapore` 计算；`workflow_dispatch` 可显式传入 ISO 日期用于补跑。
- 周末和美国休市日仍运行，并根据 Master Prompt 生成 `market_closed` 休市版日报。
- 在至少一次真实 `workflow_dispatch` 全链路验收前，计划任务由 repository variable `MARKET_DAILY_CRON_ENABLED` 安全门控；未设为字符串 `true` 时，cron run 只会跳过生产 job。

## API、模型和联网研究

- 接口：OpenAI Responses API，`POST /v1/responses`。
- 模型：`gpt-5.6-sol`，用于复杂、多来源的金融研究与长篇 Markdown 生成。
- 工具：正式 `web_search`；调用设置为 required，并在响应中验证确实出现 `web_search_call`。
- 完整性：只接受 `status=completed`、存在 Web Search 调用且正文非空的响应；`incomplete`、空输出、API/网络失败均停在 Generate。
- 隐私：`store: false`；API Key 只来自 GitHub Actions secret `OPENAI_API_KEY`。

## Secrets 与最小权限

- 必需 repository secret：`OPENAI_API_KEY`。
- 不把 Key 写入仓库、`.env`、日报、artifact、Actions Summary 或命令参数。
- Workflow 不启用 shell tracing，不输出 API 原始响应或错误正文。
- `GITHUB_TOKEN` 只授予 `contents: write` 和 `actions: write`：前者用于 main 提交，后者用于显式 dispatch/等待现有 Pages workflow。
- GitHub 使用 `GITHUB_TOKEN` 推送时不会递归触发新的 workflow；生成 workflow 在 push 后仅在对应 SHA 尚无 Pages run 时显式 dispatch `deploy-pages.yml`。

## Staging、幂等和并发

- AI 输出写入 `$RUNNER_TEMP/YYYY-MM-DD.md`，不进入 Git history，也不上传 artifact。Runner 结束后自动消失。
- Validator 通过后才调用既有 importer；未经验证的 AI 内容无法进入 `docs/`。
- 正式日报已存在时，先用 Validator 验证并幂等退出生成、入库、commit 和 push；不会再次消耗 API 或覆盖历史。
- 同日期不同内容仍由 importer 拒绝；自动流程没有“修订日报”入口。
- Workflow 使用固定 concurrency group `market-daily-generation` 串行化所有 schedule 与手动补跑，`cancel-in-progress: false`，避免取消一个正在发布的有效运行。
- Push 前重新读取 `origin/main`；若生成期间 main 已变化则停在 Push，不自动合并、不 rebase、不强推。

## 切换边界

Plan B 尚未通过真实 API 全链路验收，因此现有两个正式任务暂不修改或暂停：

- `美股市场日报` 仍保持原 08:00 配置；验收后才改为约 08:10，只读当天正式 Archive 并忠实展示，缺失时明确报告、不自行生成。
- `Market Daily Archive 日报入库` 仍保持 Active；验收后先暂停观察数天，不删除，保留回滚与本地恢复能力。
- V2.3 月报继续禁止启动。

只有在真实 `workflow_dispatch` 同时通过 Generate、Validate、Import、Build、Commit、Push、Deploy、Verify，且确认日志无 secret 泄漏后，才把 `MARKET_DAILY_CRON_ENABLED` 设为 `true` 并修改两个旧任务职责。

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

V2 支持手动检查与故障恢复；GitHub Actions 自动链路、手动 `workflow_dispatch` 与本地 fallback 共用同一套幂等、Validator 和 fail-closed 规则。原发布脚本继续保留，但 Plan B 的主要补跑入口改为云端 workflow。

在 Work / Codex 中说：**检查并补跑今日日报**。仓库根目录的 `AGENTS.md` 定义了这一操作的恢复流程。

也可以在项目目录直接运行：

```bash
./scripts/check_and_recover_daily.sh
```

无需填写日期或理解各个发布步骤。默认使用 Asia/Singapore 今天日期；先检查正式 Archive、远程 workflow 和已有草稿。只有确实不存在可用日报时才 dispatch 唯一 Generate workflow，不在 Work 会话再生成第二份。

| 检查到的状态 | 恢复动作 |
| --- | --- |
| 本地和远程都没有日报 | 触发 `generate-daily.yml` 的 `workflow_dispatch`；由 Responses API 唯一生成，再完成 Validator、入库、构建、提交与发布 |
| Generate workflow 已排队或运行 | 等待同一 run，不再次 dispatch，不在本地生成 |
| Generate workflow 失败 | 返回 run URL 与 Actions Summary 的 Blocked layer；不自动切换为第二个 AI 生成器 |
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

- Work / Codex 会话先使用 `--no-generate --json` 检查；只有退出码 3 才调用 `scripts/dispatch_daily_workflow.sh YYYY-MM-DD`。完整已有草稿或 Archive 不调用模型。
- `dispatch_daily_workflow.sh` 只创建一次 `workflow_dispatch` 并等待新 run；并发组会串行化与 cron 的重叠。失败保留在 Actions 日志与 Summary，不把未验证草稿保存成 artifact。
- 本地 Codex CLI 生成能力仍保留作为显式 fallback，但不会在 cloud workflow 失败后自动启用。只有用户查看失败层后明确要求本地恢复，才使用原 `check_and_recover_daily.sh` 链路。
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

Plan B 的仓库实现已经建立：`generate-daily.yml`、Responses API 生成器、runner 临时 staging、既有 Validator/importer、strict build、受限提交、远程 SHA、Pages dispatch 与最终正文验证。Cron 已登记为 00:00 UTC，但由 `MARKET_DAILY_CRON_ENABLED` 门控；缺少真实 API 全链路验收时不会接管生产。

当前仍需在 GitHub 设置 `OPENAI_API_KEY` secret，并至少成功执行一次真实 `workflow_dispatch`。在此之前，桌面端 `Market Daily Archive 日报入库` 与 ChatGPT 云端 `美股市场日报` 都保持原配置，未暂停、未改职责。验收成功后再启用 cron、把云端任务改为 08:10 只读展示，并暂停本地每日生成任务观察；不删除恢复能力，不开始 V2.3。
