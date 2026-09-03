---
title: V2 自动入库
description: Market Daily Archive V2 每日入库与发布操作说明
---

# V2 自动入库与发布

## 当前推荐：复制一次，本地确定性入库

当前优先采用不需要 OpenAI API 的最低复杂度方案。每天的 ChatGPT「美股市场日报」仍只生成一份完整 Markdown。

### 日常推荐：Mac 一键 App

本机入口位于：

```text
macos/归档今日日报.app
```

把它拖到 Dock 后，每天只需：**使用 ChatGPT 日报消息自带的“复制”按钮复制完整回复 → 点击“归档今日日报”**。App 使用 macOS 内置 JXA/Standard Additions 读取 UTF-8 纯文本，并由 `scripts/extract_chatgpt_daily.py` 确定性定位日报边界：优先选择唯一 YAML `title: YYYY-MM-DD 市场日报`，没有合格 YAML 时才选择唯一精确 H1 `# YYYY-MM-DD 市场日报`。起点之前的 ChatGPT 说明文字被忽略；从日报起点到剪贴板末尾的原始字节先交给公共入库入口。多候选、代码块内候选或无法识别均 fail-closed，不会运行 importer。成功时通知“今日日报已成功归档”，失败对话框显示底层脚本返回的简短原因。最近一次完整 stdout/stderr、固定 PATH、shell 和退出码写入 Git 忽略的 `inbox/.archive-today-last-run.log`，便于定位 App 层故障；日志不进入 Archive 或 Git。

公共链路为 `Extract → Normalize → Validator → Import`。边界提取器本身不改正文；`scripts/normalize_daily.py` 只有一个白名单：唯一 `跨资产观察` 的全部非空行必须恰好是 2–5 个从 1 开始连续、顶格、无续行的 `N. text`，此时只把 `N. ` 改为 `- `，内容、顺序、数字、来源及其余字节不变。已经合规的 Markdown 字节不变；混合列表、跳号、缩进、续行、数量越界或章节歧义在 Normalize 层停止。Validator 规则没有放宽，同日期不同内容默认继续停在 Draft 层。

### 失败草稿恢复

若同日旧 inbox 已被当前 Validator 明确拒绝，生成端修复后可直接再次复制并运行同一入口。恢复器只在以下条件全部成立时工作：

1. 正式 `docs/YYYY/MM/YYYY-MM-DD.md` 不存在。
2. 新复制正文已完成 Extract 与白名单 Normalize，并先通过当前 Validator。
3. 旧 `inbox/YYYY-MM-DD.md` 可安全读取，且重新运行同一 Validator 后得到明确的 `ValidationFailure`。

满足条件后，旧稿以 `inbox/rejected/YYYY-MM-DD-rejected-NNN.md` 保存；`NNN` 从 `001` 递增，并用排他创建保证已有历史永不覆盖。旧稿字节复核无变化且正式 Archive 仍不存在后，新稿才原子替换 inbox，并继续 Validator、Importer 与 strict build。

若新稿也失败、旧稿仍通过 Validator、旧稿无法读取或 Validator 自身异常、正式 Archive 已存在，恢复立即停止；旧 inbox 和正式 Archive 都不会改变。无法证明失败不等于失败。`inbox/rejected/` 随整个 inbox 保持 Git 忽略，仅作为本机审计与人工恢复记录。

编译后的 `.app` 是 gitignored 本机文件。源码保存在 `macos/archive_today.js`；首次安装或项目路径变化后，可由维护者运行一次：

```bash
./scripts/install_macos_launcher.sh
```

这只是构建两个本地 launcher，不会读取日报、调用 AI/API、联网或修改任何任务。项目位于 `Documents` 时，最终编译的 App 首次运行需要用户允许一次 Documents 文件夹访问；重新编译会改变本机 App 签名，可能需要再次确认。

### 命令行备用入口

需要诊断时，仍可在仓库根目录运行：

```bash
pbpaste | ./scripts/import_chatgpt_daily.sh
```

脚本只处理标准输入中已经存在的日报，按顺序完成：

1. 拒绝空输入，并运行上述白名单 Markdown normalizer。
2. 提取并校验 `YYYY-MM-DD 市场日报` 日期。
3. 安全保存为 Git 忽略的 `inbox/YYYY-MM-DD.md`。
4. 运行既有 `scripts/validate_daily.py` 质量闸门。
5. 运行既有 `scripts/import_daily.py`，维护正式日报、索引与 MkDocs 导航。
6. 运行 `mkdocs build --strict`。

它不会调用 AI、OpenAI API、Git、GitHub CLI 或网络，也不会 commit、push 或发布。成功后运行：

```bash
mkdocs serve
```

即可在终端显示的本地地址浏览和全文搜索。若剪贴板中是同日期相同内容，命令可安全重跑；同日期不同内容仅允许走上文严格限定的失败草稿恢复，其他情况继续停止且不覆盖。Validator 或严格构建失败也会明确标出失败层；Validator 失败时不会开始正式入库。

当前两个既有定时任务保持原配置。两个 Mac App 与真实日报归档链路均已验收，项目进入稳定使用观察期，不修改或暂停现有任务。

### 本地阅读：打开 Market Daily Archive App

本机第二个原生入口位于：

```text
macos/打开 Market Daily Archive.app
```

单击后由 `scripts/open_local_archive.py` 使用 Python 标准库完成本地服务控制：

1. 对 `inbox/.mkdocs-serve.lock` 加独占锁，避免同时点击造成竞态。
2. 检查 `127.0.0.1:8000`，并验证 HTTP 200 页面同时包含本站唯一标题与描述标记；只允许同一主机、同一端口内的单次 MkDocs 重定向。
3. 已确认是 Market Daily Archive 时直接复用，不启动第二个服务。
4. 端口被其他页面、无效 HTTP 服务或外部重定向占用时停止并显示可理解提示。
5. 端口空闲时，用安装器已经验证并写入 App 的绝对 Python/MkDocs 路径，在项目目录后台启动 `mkdocs serve --dev-addr 127.0.0.1:8000`。
6. 等待页面身份验证通过后，才由 macOS 打开默认浏览器的 `http://127.0.0.1:8000/`。

MkDocs 使用独立后台会话和已关闭的标准输入，App 退出后服务继续运行；PID 与服务器输出分别保存在 Git 忽略的 `inbox/.mkdocs-serve.pid` 和 `inbox/.mkdocs-serve.log`。最近一次 App 控制结果保存在 `inbox/.open-archive-last-run.log`。该入口不读取剪贴板、不修改日报、不运行 importer、不调用 AI/API/Git，也不访问外部网络。

`scripts/install_macos_launcher.sh` 会优先验证并嵌入项目 `.venv/bin/python` 与 `.venv/bin/mkdocs` 的绝对路径；若项目虚拟环境不可用，才使用安装时能解析到的 `python3` / `mkdocs` 绝对路径。Finder 或 Dock 启动时使用固定的最小 PATH 与 UTF-8 locale，不依赖交互式 Terminal 环境。项目移动或重建虚拟环境后需重新运行安装器。

## 保留但不启用的 Plan B

仓库保留 **Single Generation, Multiple Outputs / 一次生成，多个出口** 的 Plan B 代码：

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

### Plan B 的设计背景

隔离 canary 已证明 ChatGPT Cloud Scheduled Task 没有完成无人值守 GitHub 写入，不能作为可靠的云端交接层。Plan B 改由 GitHub Actions 调用 OpenAI 官方 Responses API；Responses API 支持内置 Web Search，生成器可在不依赖 Mac 的环境中实时研究。[Responses API](https://developers.openai.com/api/reference/cli/resources/responses/methods/create) · [OpenAI 模型目录](https://developers.openai.com/api/docs/models)

`prompts/daily_market_report.md` 仍是唯一长期 Prompt 真源。Workflow 读取文件正文，不复制 Master Prompt；`scripts/generate_daily.py` 只补充“必须联网研究、只返回完整 Markdown、失败不得返回残稿”的调用边界。

### Plan B 调度

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

Plan B 当前不启用，因此现有两个正式任务暂不修改或暂停：

- `美股市场日报` 仍保持原 08:00 配置。
- `Market Daily Archive 日报入库` 仍保持 Active；稳定使用观察期不修改或暂停。
- V2.3 月报继续禁止启动。

只有用户以后明确决定恢复 Plan B，才重新讨论 secret、真实 `workflow_dispatch` 验收和任务切换；当前不得设置或启用。

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

V2 支持手动检查与故障恢复。当前缺少日报时优先复用 ChatGPT 聊天里已经生成的完整 Markdown，通过 `import_chatgpt_daily.sh` 本地入库；不会自动触发 Plan B 或第二次 AI 生成。既有发布和 Plan B 工具继续保留。

在 Work / Codex 中说：**检查并补跑今日日报**。仓库根目录的 `AGENTS.md` 定义了这一操作的恢复流程。

也可以在项目目录直接运行：

```bash
./scripts/check_and_recover_daily.sh --no-generate --json
```

无需填写日期或理解各个发布步骤。默认使用 Asia/Singapore 今天日期；先检查正式 Archive、远程状态和已有草稿。若确实不存在可用日报，只读恢复入口会停止在“生成”层，并提示复制聊天中已经生成的日报，不会自动 dispatch 或重新生成。

| 检查到的状态 | 恢复动作 |
| --- | --- |
| 本地和远程都没有日报 | 停在“生成”层；复制现有 ChatGPT 日报并点击 `macos/归档今日日报.app`，命令行仅作诊断备用 |
| Plan B workflow 已排队或运行 | 只报告既有 run 状态，不再 dispatch，也不在本地生成 |
| Plan B workflow 失败 | 返回 run URL 与 Blocked layer；Plan B 保持未启用，不自动切换为第二个 AI 生成器 |
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

- Work / Codex 会话先使用 `--no-generate --json` 检查；退出码 3 时提示用户导入聊天中已有 Markdown。完整已有草稿或 Archive 不调用模型。
- `dispatch_daily_workflow.sh` 和本地 Codex CLI 生成能力仅作为 Plan B 代码保留；当前不自动调用。
- `import_chatgpt_daily.sh` 不生成、联网、commit 或 push；它只把既有正文通过同一质量与幂等规则变成本地 Archive。
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

Plan B 代码保留但不启用：不设置 `OPENAI_API_KEY`，`MARKET_DAILY_CRON_ENABLED` 继续保持未启用状态，也不手动 dispatch Generate workflow。桌面端 `Market Daily Archive 日报入库` 与 ChatGPT 云端 `美股市场日报` 当前都保持原配置，未暂停、未改职责。

两个 Mac App 与“复制回复 → Extract → Normalize → Validator → Import → MkDocs”真实链路均已验收。当前进入稳定使用观察期，只在出现真实故障时做必要修复；不修改或暂停现有任务，不删除或启用 Plan B，不开始 V2.3。
