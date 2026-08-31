# Market Daily Archive — 项目知识库

## 1. 项目目标

建立一个长期可维护、可迁移、可全文检索的个人金融市场日报档案库。

```text
AI / 人工撰写
      ↓
每日市场日报（Markdown）
      ↓
GitHub 版本存档
      ↓
Material for MkDocs 构建
      ↓
GitHub Pages 阅读
```

长期目标是逐步形成可按日期、专题与市场事件回溯的 Personal Market Database。

## 2. 已确认的范围

### V1 — Completed / Accepted

- 每日一篇 Markdown 日报。
- 年 / 月 / 日三级档案结构。
- Material for MkDocs 书籍式导航。
- 中英文全文搜索。
- GitHub Actions 自动构建并部署到 GitHub Pages。
- 首篇真实日报 `2026-08-30` 已完成线上阅读验收。

### V2 – Automated Daily Ingestion

核心目标：让每天生成的 ChatGPT 市场日报自动写入 Market Daily Archive，并完成可验证、可恢复、可重复执行的发布。

- V2.1：自动创建日期文件并维护年 / 月 / 日导航与索引。
- V2.2：自动构建、commit、push、部署并验证远程页面。
- V2.3：月报；等待每日自动入库稳定运行后再开发。

云端阅读版与本地归档分工：`美股市场日报` 的目标是固定每天 08:00 Asia/Singapore 在 ChatGPT 输出日报，不依赖 Mac，也不发布 GitHub Pages；`Market Daily Archive 日报入库` 保持现有本地链路。两者只共享 `prompts/daily_market_report.md` 这一内容真源，不假设聊天输出会自动传给本地任务。

### 暂不包含

- V2.3 月报与月度市场回顾。
- 数据库、知识图谱或 AI 问答。

## 3. 技术栈

| 层级 | 选型 | 用途 |
| --- | --- | --- |
| 内容 | Markdown | 长期可读、可迁移、Git 友好 |
| 版本与远程存档 | Git / GitHub | 历史追踪与托管 |
| 静态网站 | Material for MkDocs | 书籍式导航、搜索与主题 |
| 自动化 | GitHub Actions | 构建与部署 |
| 托管 | GitHub Pages | 公开或私有可访问的网站 |
| 日报入库 | Python 3 标准库 | 校验、去重、写入与导航生成 |
| 发布编排 | Bash / Git / GitHub CLI / curl | 构建、提交、推送与端到端验证 |
| 任务调度 | ChatGPT 桌面端当前任务 heartbeat | 每天跟随设备本地时钟 08:00 运行；日报日期以 Asia/Singapore 为准 |

## 4. 目标目录结构

```text
market-daily/
├── AGENTS.md                  # Work/Codex 手动恢复口令与执行约定
├── PROJECT.md
├── README.md
├── SECURITY.md
├── requirements.txt
├── mkdocs.yml
├── inbox/                     # Git 忽略的日报输入暂存目录
├── prompts/
│   └── daily_market_report.md
├── scripts/
│   ├── import_daily.py
│   ├── publish_daily.sh
│   ├── check_and_recover_daily.sh
│   ├── recover_daily.py
│   └── validate_daily.py
├── tests/
│   ├── test_import_daily.py
│   ├── test_recover_daily.py
│   └── test_validate_daily.py
├── docs/
│   ├── index.md
│   ├── archive.md
│   ├── maintenance/
│   │   ├── daily-template.md
│   │   └── automated-ingestion.md
│   ├── topics/
│   │   └── index.md
│   ├── statistics/
│   │   └── index.md
│   └── 2026/
│       ├── index.md
│       └── 08/
│           ├── index.md
│           └── 2026-08-30.md
└── .github/
    └── workflows/
        └── deploy-pages.yml
```

## 5. 日报约定

- 文件名：`YYYY-MM-DD.md`。
- 存放路径：`docs/YYYY/MM/YYYY-MM-DD.md`。
- 日期标题使用 ISO 格式，避免跨地区歧义。
- 固定栏目：
  - 今日市场一句话
  - 市场 Dashboard
  - 美国国债、波动率与美国股市
  - 商品与重要市场新闻
  - 跨资产观察
  - Market Narrative
  - What to Watch
  - Sources
- 正常交易日核心指标包括 2Y / 10Y / 30Y Treasury、2Y–10Y 美债利差、Fed Rate Expectations、VIX / VXN、五档文字风险状态、主要美股指数、Russell 2000、SOX、DXY、WTI 和 Gold。
- 面向用户不得单独使用 `2s10s`；统一显示 `2Y–10Y 美债利差`。使用收益率曲线术语时必须同时用普通中文解释。
- 风险状态必须使用 `很低 / 较低 / 中等 / 较高 / 很高` 明确表达，图标或颜色只能辅助，不使用伪精确风险分数。
- 长期编辑原则：**核心指标每天记录，异常指标重点解释。** 正常波动留在 Dashboard，异常、背离或重大催化剂进入详细分析。
- 每条外部信息应尽可能保留原始来源链接。
- 自动入库要求首个 H1 包含同一 ISO 日期，且正文至少保留一个 HTTPS Markdown 来源链接。
- 新日报由入库工具同步加入 `mkdocs.yml`、首页、对应年/月索引和总档案页；自动生成区块不手工修改。
- 同日期相同内容可安全重复运行；同日期不同内容必须拒绝覆盖并转人工检查。
- 正式 Master Prompt 位于 `prompts/daily_market_report.md`，普通日报运行不得自行修改。
- 每篇自动日报必须声明 `report_type: trading_day` 或 `report_type: market_closed`，并在入库、提交和推送前通过 fail-closed 完整性校验；恢复流程可先查询 Git 状态，但不得据此跳过已有内容的校验。
- 单个非关键数据暂缺可以明确标注后继续；整篇为空、截断、日期错误或关键结构缺失必须停止发布。
- V2 支持手动检查与故障恢复；自动 08:00 任务与手动恢复入口共用同一套幂等、Validator 和 fail-closed 规则。入口为 `./scripts/check_and_recover_daily.sh`，会话口令为“检查并补跑今日日报”。

## 6. Roadmap

### V1 — Completed / Accepted

- [x] 检查工作区与现有仓库边界
- [x] 初始化独立本地 Git 仓库
- [x] 创建并确立 `PROJECT.md` 维护规则
- [x] 建立 Markdown 年 / 月 / 日目录
- [x] 配置 Material for MkDocs 与全文搜索
- [x] 配置 GitHub Actions 自动部署
- [x] 完成本地严格构建验证
- [x] 用户确认 GitHub 账号、仓库名、可见性和 Git author
- [x] 使用确认的 Git author 创建本地初始提交
- [x] 用户在 GitHub 创建 Public 仓库 `leemin-blip/market-daily-archive`
- [x] 添加目标远程并推送 `main`
- [x] 在 GitHub 仓库中确认 Pages 首次部署成功
- [x] 导入并发布首篇正式日报 `2026-08-30`
- [x] 完成首篇真实日报的页面、目录与阅读效果验收

### V2 – Automated Daily Ingestion（In Progress）

核心目标：让每天生成的 ChatGPT 市场日报自动写入 Market Daily Archive。

#### V2.1 — 自动入库

- [x] 固定每天设备本地时钟 08:00、每周 7 天运行；日报日期使用 Asia/Singapore
- [x] 将 Daily Market Report Master Prompt 纳入 Git 版本管理
- [x] 创建 Active 的 `Market Daily Archive 日报入库` 桌面端任务
- [x] 自动创建 `docs/YYYY/MM/YYYY-MM-DD.md`
- [x] 自动维护首页、总档案、年/月索引与 MkDocs 导航
- [x] 防止同一天不同内容重复导入，并支持相同内容幂等重跑
- [x] 保留日报标题、正文结构和来源链接
- [x] 增加发布前 fail-closed 完整性与来源校验
- [x] 在首次无人值守运行前完成正式日报模板、Master Prompt 1.1 与 Validator 定版
- [ ] 完成首次真实无人值守入库验收
- [x] Master Prompt 1.2 区分云端聊天输出与本地归档职责，不改变已定版字段和质量要求
- [x] 原「美股市场日报」云端任务恢复 Active，日历明确绑定每天 08:00 Asia/Singapore，仅保存动态读取 GitHub Prompt 的短指令
- [ ] 验收首次云端定时运行实际读取最新版 Prompt 并完成聊天日报

#### V2.2 — 自动发布

- [x] 严格构建、自动 commit 与 push
- [x] 核对本地与远程提交，等待 GitHub Pages workflow
- [x] 验证最终线上日报页面并提供可恢复重跑路径
- [x] 手动检查并补跑入口：识别阶段、复用草稿/提交、拒绝内容冲突、有限部署重试和逐层状态摘要
- [ ] 完成首次真实无人值守发布验收

#### V2.3 — 月报

- [ ] 自动月报与月度市场回顾（每日自动入库稳定后再开发）

### V3 — 个人市场数据库

- [ ] 历史数据分析
- [ ] 市场事件搜索
- [ ] 专题页面
- [ ] 统计与跨日报关联

## 7. Architecture Decisions

### Decision 001 — Markdown 作为长期内容格式

原因：可读、可迁移、Git 友好，并且不绑定特定笔记软件或数据库。

### Decision 002 — Material for MkDocs 作为阅读层

原因：适合年 / 月 / 日的书籍式导航，内置全文搜索，Markdown 写作体验稳定。

### Decision 003 — GitHub Actions 直接部署 GitHub Pages

原因：日报内容与部署配置共同版本化，推送到主分支即可自动构建，无需在本机保存部署凭据。

### Decision 004 — 先稳定 V1，再接入日报生成自动化

原因：确保任何来源生成的 Markdown 都能进入同一条稳定的存档与阅读链路，避免绑定单一生成方式。

### Decision 005 — 公开仓库不保存任何敏感凭证

原因：项目将通过公开 GitHub 仓库和 GitHub Pages 发布。API Key、Token、密码、`.env`、私钥和个人金融账户数据不得进入仓库；未来自动化如需凭证，只能通过 GitHub Actions repository / environment secrets 引用。

### Decision 006 — `PROJECT.md` 作为跨会话项目知识库

- **Decision**：将 `PROJECT.md` 固定为 Market Daily Archive 的主要项目知识库，并采用“项目级变化更新、普通内容变化不更新”的维护原则。
- **Reason**：确保新的 ChatGPT / Work 会话可以快速恢复项目上下文，同时避免文件退化为重复 Git 历史的流水账。
- **Date**：2026-08-30
- **Impact**：所有项目开发工作开始前必须先读取本文件；项目级修改提交前必须检查是否需要同步更新；新增长期决策必须使用编号 Decision 记录。

### Decision 007 — 桌面端本地定时任务编排确定性仓库工具

- **Decision**：使用 ChatGPT 桌面端本地项目定时任务生成日报并写入 Git 忽略的 `inbox/`，再由仓库内的 Python 入库器和 Bash 发布脚本完成文件、导航、Git 与 Pages 操作；不假设网页端 ChatGPT 任务可以直接写本机或 GitHub。
- **Reason**：OpenAI 官方说明网页端定时任务不能直接操作本机目录，而桌面端项目级任务可以在本地项目中运行。把内容生成与确定性仓库操作分离，可以少依赖、避免仓库凭证、支持幂等重跑和逐步恢复。
- **Date**：2026-08-30
- **Impact**：电脑和 ChatGPT 桌面应用需在运行时保持可用，任务需获得最小必要的工作区与 GitHub 网络权限；普通运行必须读取版本化 Master Prompt。未来月报可以复用标准化日期文件，但在每日链路稳定前不得开发。

### Decision 008 — 每天设备本地 08:00 调度，日报日期使用 Asia/Singapore

- **Decision**：任务每周 7 天跟随设备本地时钟 08:00 运行，以执行时的 `Asia/Singapore` 日期命名日报；周末和美国休市日生成休市版。当前设备时区为 `Asia/Shanghai`，与 SGT 同为 UTC+8。
- **Reason**：用户选择跟随设备本地时钟；当前实际执行时刻仍为 08:00 SGT，可在美国正常收盘后保留约 3–4 小时用于确认收盘数据、盘后新闻和媒体复盘，同时不受美国夏令时 / 冬令时切换影响。
- **Date**：2026-08-30
- **Impact**：所有日期判断、文件名和 H1 以新加坡日期为准；不得改用纽约时区。调度会跟随设备时区，如果设备以后离开 UTC+8，需要复核执行时刻。休市日仍执行，但不重复没有新交易产生的静态美股数据。

### Decision 009 — 发布前采用 fail-closed 质量闸门并允许非关键数据降级

- **Decision**：自动生成报告在任何入库或 Git 操作前必须通过 `scripts/validate_daily.py`；空白、截断、错日期、无效报告类型、关键结构或来源底线缺失均停止发布。单个非关键数据暂缺可明确标注后继续。
- **Reason**：日报生成失败不能等同于发布残缺日报；同时，因单个暂不可得的数据点阻塞整篇报告会降低自动化可用性。
- **Date**：2026-08-30
- **Impact**：失败草稿只留在 Git 忽略的 `inbox/`，不会 commit 或 push；修复后可按同日期重试。Master Prompt 必须输出 `report_type` 和标准章节，普通日报不会因一个明确标注的非关键缺失而自动失败。

### Decision 010 — 核心指标每日记录，异常指标重点解释

- **Decision**：正式 Dashboard 增加 30Y Treasury、DXY、Fed Rate Expectations 与 Russell 2000；面向用户将 `2s10s` 统一为 `2Y–10Y 美债利差`，增加五档文字风险状态和 `跨资产观察`。正常波动只做简洁记录，异常波动、资产背离或重大催化剂才进入详细分析。
- **Reason**：让非专业读者能快速理解收益率曲线和风险状态，同时用 30Y、美元、Fed 定价和小盘股补足财政/期限溢价、跨资产传导与市场宽度观察；控制日报长度，提升信息密度。
- **Date**：2026-08-30
- **Impact**：Master Prompt、日报模板与 Validator 必须保持这些结构一致；曲线术语需附普通中文解释，风险不得仅用 emoji / 颜色表达。Bitcoin、信用利差、MOVE 与 USD/JPY 暂不列入每日核心 Dashboard，重大事件时可临时分析。

### Decision 011 — 独立状态恢复入口复用确定性入库规则

- **Decision**：新增手动恢复检查器，不重构原 08:00 发布脚本或修改 Active 定时任务。复用现有 Validator、Markdown 比较规范及入库器；用已提交快照在临时目录运行入库器，证明未提交改动和未推送历史只属于本次日报后才继续。已完整发布时不重复生成、提交、推送或部署。
- **Reason**：原发布脚本的干净工作区前置条件不覆盖“已入库但未 commit”；简单重跑或放宽整个暂存区会误收无关改动。状态恢复需要精确识别阶段，而非从生成开始重复执行。
- **Date**：2026-08-31
- **Impact**：恢复可先做只读 Git 状态检查以识别已提交或远程日报，但已有内容必须先通过 Validator，任何正式入库/提交/推送必须通过相同质量闸门。Work 口令由 `AGENTS.md` 固定；缺少日报时当前会话生成，终端则尝试现有 Codex CLI 的只读实时搜索生成，无新增 API 凭证。Actions 仅针对当前远程 SHA 有限重试，Pages 检查 HTTP、H1、摘要和来源链接。冲突、无关改动、分叉、权限或并发异常停止并保留现场，不自动覆盖、合并或强推。

### Decision 012 — 云端阅读与本地归档分工，共享单一内容真源

- **Decision**：云端「美股市场日报」只在线读取 GitHub `main` 分支的 `prompts/daily_market_report.md`、研究并在聊天输出。任务指令只保存读取位置、固定新加坡调度、输出边界与读取失败规则，不复制完整 Master Prompt。本地入库任务、Validator、发布与恢复脚本保持原样。
- **Reason**：云端任务无法操作用户 Mac 目录，不应因本地归档步骤不可用而停止聊天阅读服务；同一内容规范应可被不同运行环境使用。
- **Date**：2026-08-31
- **Impact**：Master Prompt 1.2 将内容规则与交付权限分开。云端读取失败或不能取得完整最新版时明确报错，不使用旧副本生成。两个任务独立生成可能得到不同正文，但只有本地链路发布 Pages；不得自动把云端正文覆盖进同日期归档。云端已配置与否必须以真实任务状态及运行记录为准，发送配置请求不等于保存成功。

## 8. Project Maintenance Rules / 项目维护规则

本章节是所有后续 Market Daily Archive 开发工作的固定维护约定。

### 8.1 开始项目开发工作前

每次开始新的项目开发工作前，必须先完整读取 `PROJECT.md`，确认以下内容后再修改项目：

- 当前架构与技术栈。
- Roadmap 及所处的 V1 / V2 / V3 阶段。
- Current Status 与 Next Step。
- 已有 Architecture Decisions。
- 本章节中的项目维护规则。

### 8.2 项目级修改完成后

每完成一轮项目级修改，都必须在 Git commit 之前检查 `PROJECT.md` 是否需要同步更新。根据实际变化维护：

- Current Status。
- Next Step。
- Roadmap。
- Architecture Decisions。
- Change Log。

不要求每次同时修改全部栏目；只更新本轮实际发生变化且未来开发需要知道的内容。

### 8.3 必须更新 `PROJECT.md` 的情况

出现以下任一情况时，必须更新本文件：

- 新功能完成。
- Roadmap 项目完成或状态改变。
- 项目进入新的 V1 / V2 / V3 阶段。
- 架构或技术栈发生变化。
- 目录结构发生重要变化。
- 日报模板或内容规范发生长期变化。
- GitHub Actions、GitHub Pages 或自动化机制发生变化。
- 做出会影响未来开发的重要决策。
- 发现并解决值得未来参考的重要技术问题。
- Current Status 或 Next Step 发生变化。

### 8.4 通常不更新 `PROJECT.md` 的情况

以下普通内容变化通常只由 Git commit 记录，不更新本文件：

- 每天新增普通日报。
- 修改某一天日报的文字。
- 修复错别字。
- 不影响项目架构的小型内容调整。
- Git commit 已经能够充分记录的普通文件变化。

如果上述变化同时引发了长期规范、架构、状态或 Roadmap 变化，仍应按 8.3 更新本文件。

### 8.5 内容边界

`PROJECT.md` 只保存未来继续开发本项目时需要知道的信息，保持简洁，不作为完整 Git commit 日志。Change Log 仅记录有长期参考价值的项目级变化，不逐文件复述普通提交。

### 8.6 Architecture Decision 格式

新的长期架构或项目治理决策必须使用连续编号的 `Decision` 记录，并包含：

- **Decision**：做出了什么决定。
- **Reason**：为什么这样决定。
- **Date**：决定日期。
- **Impact**：对后续开发、内容或运维的影响。

### 8.7 跨会话知识库标准

`PROJECT.md` 是本项目跨 ChatGPT / Work 会话的主要知识库。任何新的 Work 会话都应能够仅通过阅读本文件理解：

- 这个项目是什么。
- 为什么采用当前设计。
- 当前做到哪里。
- 哪些功能已经完成。
- 下一步应该做什么。
- 有哪些重要规则和技术决策。

## 9. Current Status

当前阶段：**V2 – Automated Daily Ingestion**

已完成：

- V1 已完成并通过 `2026-08-30` 真实日报的页面、目录和阅读效果验收。
- V2.1 确定性入库器已实现：日期校验、正确目录写入、正文与来源保留、导航生成和重复导入保护。
- V2.2 发布脚本已实现：严格构建、commit、push、远程 SHA 核对、Actions 等待和线上页面验证。
- 入库器单元测试和现有日报幂等重跑验证已通过；V1 网站严格构建保持成功。
- 自动入库架构与恢复方式已写入维护文档。
- 正式任务已创建并处于 Active：`Market Daily Archive 日报入库`，每天跟随设备本地时钟 08:00、每周 7 天运行；当前与 08:00 SGT 相同。
- Daily Market Report Master Prompt 已版本化保存于 `prompts/daily_market_report.md`。
- 发布链路已增加 fail-closed 质量闸门，并用自动测试覆盖完整交易日、休市版、非关键数据暂缺及残缺报告拒绝。
- 首次无人值守运行前的日报模板已正式定版：Master Prompt 升级至 1.1，Validator 与维护模板同步增加 30Y、DXY、Fed Rate Expectations、Russell 2000、文字风险状态和跨资产观察。
- `2026-08-30` 休市样板已按新版结构更新，并只补充有可靠来源支持的历史数据。
- `2026-08-31` 首轮定时日报已完成入库、提交、push、远程 SHA、Actions 和 Pages 验证；执行中曾因沙盒认证访问受限而授权重试，不据此宣称全程无人介入已验收。
- V2 支持“检查并补跑今日日报”：已有内容优先复用，按阶段恢复，并以相同 Validator、幂等和 fail-closed 规则控制发布；已完整发布返回无需补跑。独立恢复测试覆盖生成、部分入库、构建、推送与部署故障。
- Master Prompt 1.2 已明确云端阅读 / 本地归档边界，保留 1.1 的全部指标、章节和来源标准；云端只在线读取 GitHub 最新文件，不运行本地链路。
- 已通过原 ChatGPT 聊天的任务管理入口，将曾被改名的原云端任务恢复为「美股市场日报」并启用；回读确认日历时区明确为 Asia/Singapore，每天 08:00。默认时区元数据仍为 Asia/Shanghai，实际触发使用日历中显式指定的 Asia/Singapore；原通知和邮件偏好未改。没有新建任务，本地 heartbeat 保持原样。

尚未完成：

- 尚未完成首次真实无人值守入库与发布验收。
- V2.3 月报未开始。
- 云端首次定时运行尚待验收。原云端聊天已成功在线读取 GitHub Master Prompt，但普通聊天读取成功不能替代定时运行验收；任务接口未返回 next_run_time，不把按日历计算的下次时间冒充服务端回执。

下一步：继续观察后续设备本地 08:00（当前等同 08:00 SGT）运行，确认无需权限介入的连续入库、发布和线上验证；遇到故障使用手动恢复入口，保留明确的失败层和恢复结果。暂不开发月报。

云端下一步：检查首次按新配置触发的运行记录，确认在线读取 `main` 最新 Master Prompt、采用正确新加坡日期、完整输出并保留来源；读取失败应明确报告且不使用旧版。2026-08-31 配置完成时，按日历计算的下一次为 2026-09-01 08:00 Asia/Singapore，尚非已执行结果。

运行条件：电脑和 ChatGPT 桌面应用需保持运行，既有工作区和 GitHub 权限需可用；首次运行发生过权限重试，持续无人值守能力仍待验收。

## 10. Change Log

### 2026-08-31

- 确立云端阅读与本地归档分工；Master Prompt 1.2 消除本地交付要求对云端生成的歧义。确认原云端任务曾被改名为入库任务，通过原聊天的任务管理入口恢复名称、启用并回读固定 08:00 Asia/Singapore 配置；首次定时执行仍待验收。本地 Active 任务与全部入库、发布、恢复脚本未修改。
- 首轮定时日报在权限重试后完整发布，后续仍需观察真正无人值守运行的稳定性。
- 新增“检查并补跑今日日报”手动入口及 Work/Codex 口令约定；按生成、Validator、Import、Build、Commit、Push、Actions、Pages 层恢复，保护同日期内容和无关工作。
- 增加恢复故障测试及维护说明；复用既有入库器与 Validator，原 08:00 Active 定时任务、发布脚本及 Pages workflow 未修改，V2.3 未开始。

### 2026-08-30

- 确定 GitHub + Markdown + Material for MkDocs + GitHub Pages 总体架构。
- 确定 V1 / V2 / V3 Roadmap。
- 检查工作区边界：当前目录为空、无现有 Git 仓库、无远程仓库。
- 初始化项目知识库和独立本地 Git 仓库。
- 建立年 / 月 / 日内容结构、日报模板和首篇结构示例。
- 配置 Material for MkDocs 书籍式导航与中英文全文搜索。
- 配置 GitHub Actions 构建、上传 Pages artifact 并部署至 `github-pages` 环境。
- 本地严格构建首次发现 `docs/templates/` 为 MkDocs 保留目录；已将模板迁移至 `docs/maintenance/daily-template.md`，确保模板可正常导航与搜索。
- 完成配置语法、生成页面和中英文搜索索引验证；V1 本地实现完成。
- 用户确认 GitHub 目标、Public 可见性与 Git author；只读检查显示目标公开仓库尚不存在。
- 扫描本地文件未发现敏感凭证，并补充公开仓库安全规则与忽略项。
- 严格构建和提交前安全检查通过，创建本地 V1 初始提交 `5bb3f74`。
- 用户创建目标 Public 仓库；只读验证确认仓库为空，不会覆盖任何远程内容。
- 添加正确的 `origin` 后尝试首次推送；HTTPS 无登录凭据，SSH 无可用公钥，推送安全停止且远程仍为空。
- 找到用户安装的 GitHub CLI 2.98.0 并确认已登录 `leemin-blip`；推送因缺少 `workflow` scope 被 GitHub 拒绝，设备授权刷新因当前环境网络超时未完成。
- 用户批准 `workflow` 授权后，旧 Token 已失效但新凭据未写回；确认默认配置为空，必须继续使用自定义 `GH_CONFIG_DIR` 重新登录。
- 完成 GitHub CLI 重新登录；确认凭据保存在 macOS Keychain，具备 `repo` 与 `workflow` scope。
- 首次推送 `main` 成功。
- 首次部署发现 Pages 尚未启用；通过 GitHub Pages API 将发布源设为 `workflow` 后重跑成功。
- 验证公网首页、全文搜索索引和 HTTPS 网站地址；V1 完成。
- 只读核对本地 `HEAD`、`origin/main` 与 GitHub `main`，三者均为 `e9a0497792bf35603edd8b661cf9550ac4905cb7`，且工作区干净。
- 将 `2026-08-30` 结构示例替换为首篇正式日报；保留完整周末市场分析和可点击来源链接。
- 更新首页、总档案、2026 年索引和 08 月索引，正式日报可沿 `2026 → 08 月 → 2026-08-30` 打开。
- 明确本轮仅测试一篇真实日报的阅读效果，不启动 V2 / V3 自动化、月报或其他扩展。
- 建立完整的 Project Maintenance Rules，明确开发前读取、提交前检查、必须更新与通常不更新的边界，以及 Architecture Decision 的标准格式。
- V1 首篇真实日报的页面、目录和阅读效果通过验收；V1 正式标记为 Completed / Accepted，项目进入 `V2 – Automated Daily Ingestion`。
- 采用“ChatGPT 桌面端本地定时任务 + Git 忽略 inbox + 确定性仓库工具”架构，避免假设网页端任务能够直接操作本机或 GitHub。
- 完成 V2.1 入库器：自动日期路径、首页与年/月/日导航、来源保留、幂等重跑和重复内容保护。
- 完成 V2.2 发布脚本：严格构建、commit、push、远程 SHA、GitHub Pages workflow 与线上页面验证，并记录失败恢复路径。
- 增加入库器自动测试与 V2 操作文档；月报继续延后至每日链路稳定后。
- 固定每天跟随设备本地时钟 08:00、每周 7 天运行；当前设备为 Asia/Shanghai，与 08:00 SGT 相同，文件名和标题日期继续使用新加坡日期。
- 将正式 Daily Market Report Master Prompt 保存为 `prompts/daily_market_report.md`，统一交易日、休市日、数据、叙事、观察事项、来源和 Markdown 输出规范。
- 增加独立的 fail-closed 发布前质量闸门，区分“非关键数据暂缺”和“整篇生成失败”；残缺内容不会进入 Git。
- 创建并激活 `Market Daily Archive 日报入库` 桌面端 heartbeat 任务；首次真实无人值守运行仍待验收。
- 在首次 08:00 无人值守运行前完成正式日报模板定版：增加 30Y Treasury、DXY、Fed Rate Expectations、Russell 2000 和跨资产观察，将 `2s10s` 改为清晰的 `2Y–10Y 美债利差`，并要求五档文字风险状态。
- 确立“核心指标每天记录，异常指标重点解释”的长期编辑原则；同步更新 Master Prompt 1.1、维护模板、Validator、测试与 `2026-08-30` 展示样板。
