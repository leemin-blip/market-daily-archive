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

核心目标：让云端按需生成的单份 ChatGPT 市场日报进入 Market Daily Archive，并完成可验证、可恢复、可重复执行的确定性归档与发布。

- V2.1：自动创建日期文件并维护年 / 月 / 日导航与索引。
- V2.2：自动构建、commit、push、部署并验证远程页面。
- V2.3：月报；等待每日自动入库稳定运行后再开发。

当前采用“专用 ChatGPT Project + GitHub Master Prompt + 云端按需生成 + 本地确定性归档”：用户只在输入 `生成今日市场日报` 时触发云端研究；生成端在线读取 GitHub `main/prompts/daily_market_report.md`，本地不重复调用 AI。需要归档时，用户复制同一份日报并点击 `macos/归档今日日报.app`。Plan B 代码保留但不启用，旧定时生成路径停止。

当前已验收的日常使用流程：

1. 在手机或 Mac 的专用 ChatGPT Project 中输入 `生成今日市场日报`；云端读取 GitHub 最新 Master Prompt 后研究并生成。
2. 需要本地归档时，在 Mac 对同一份日报点击“复制回复”。
3. 点击 `macos/归档今日日报.app`，完成确定性的剪贴板处理、Validator、Import 和 MkDocs 构建。
4. 点击 `macos/打开 Market Daily Archive.app`，复用或启动本地 MkDocs，并在默认浏览器阅读和搜索。
5. 普通日常归档只更新本地 Archive，不自动 commit / push；需要发布到 GitHub Pages 时另行明确执行发布流程。

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
| 日报生成 | 专用 ChatGPT Project（云端按需） | 收到 `生成今日市场日报` 后读取 GitHub 最新 Master Prompt，只生成一份报告；本地不重复调用 AI |
| 当前本地交接 | macOS 剪贴板 + Bash | `pbpaste` 把现有 Markdown 交给 Validator 和 importer |
| Mac 日常入口 | JXA 编译的原生 `.app` | 一键归档剪贴板日报或启动并打开本地 MkDocs，不打开 Terminal |
| 发布编排 | Bash / Git / GitHub CLI / curl | 构建、提交、推送与端到端验证 |
| 保留的 Plan B | GitHub Actions + OpenAI Responses API | 代码保留；cron 门控，不设置 API Key，不启用 |
| 历史任务 | ChatGPT / Codex 定时任务 | 本机入库任务已暂停；正式云端日报任务不再作为启用的每日生成路径；临时任务与 canary 保持结束 / disabled |

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
├── macos/
│   ├── archive_today.js       # 原生一键 launcher 源码
│   ├── open_archive.js        # 本地 MkDocs 阅读 launcher 源码
│   ├── 归档今日日报.app        # 本机生成、Git 忽略，可拖入 Dock
│   └── 打开 Market Daily Archive.app
├── prompts/
│   └── daily_market_report.md
├── scripts/
│   ├── import_daily.py
│   ├── import_chatgpt_daily.sh
│   ├── extract_chatgpt_daily.py
│   ├── normalize_daily.py
│   ├── recover_rejected_draft.py
│   ├── open_local_archive.py
│   ├── install_macos_launcher.sh
│   ├── publish_daily.sh
│   ├── check_and_recover_daily.sh
│   ├── dispatch_daily_workflow.sh
│   ├── generate_daily.py
│   ├── recover_daily.py
│   ├── validate_daily.py
│   └── verify_daily_page.py
├── tests/
│   ├── test_generate_daily.py
│   ├── test_generate_workflow.py
│   ├── test_import_daily.py
│   ├── test_import_chatgpt_daily.py
│   ├── test_extract_chatgpt_daily.py
│   ├── test_normalize_daily.py
│   ├── test_open_local_archive.py
│   ├── test_macos_launcher.py
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
        ├── deploy-pages.yml
        └── generate-daily.yml
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
- 同日期相同内容可安全重复运行；同日期不同内容默认拒绝覆盖。唯一自动恢复例外是正式 Archive 不存在、新稿通过当前 Validator、旧 inbox 被同一 Validator 明确判定失败；旧稿必须先无覆盖地保存在 `inbox/rejected/`，任何无法证明的情况都 fail-closed。
- 正式 Master Prompt 位于 `prompts/daily_market_report.md`，普通日报运行不得自行修改。
- 每篇自动日报必须声明 `report_type: trading_day` 或 `report_type: market_closed`，并在入库、提交和推送前通过 fail-closed 完整性校验；恢复流程可先查询 Git 状态，但不得据此跳过已有内容的校验。
- 单个非关键数据暂缺可以明确标注后继续；整篇为空、截断、日期错误或关键结构缺失必须停止发布。
- V2 支持手动检查与故障恢复；按需生成与手动恢复入口继续共用同一套幂等、Validator 和 fail-closed 规则。入口为 `./scripts/check_and_recover_daily.sh`，会话口令为“检查并补跑今日日报”。
- 当前推荐半自动入口为 `pbpaste | ./scripts/import_chatgpt_daily.sh`：只接收已生成 Markdown，不调用 AI/API、不 push；同日期相同内容幂等，不同内容拒绝覆盖。
- Mac 日常入口为 `macos/归档今日日报.app`：只负责读取剪贴板、定位项目并调用上述脚本；不复制 Validator/importer 逻辑。
- 本地阅读入口为 `macos/打开 Market Daily Archive.app`：复用或后台启动唯一的本地 MkDocs 服务，验证页面身份后打开默认浏览器；不修改日报或运行入库流程。
- App 剪贴板边界解析优先使用唯一 YAML 日报标题，精确 H1 仅作兜底；只剥离起点前的 ChatGPT 包装文字。入库前仅允许白名单 normalizer 将唯一 `跨资产观察` 中 2–5 个从 1 开始连续、顶格、单行的 `N. ` marker 转为 `- `；条目内容与其余字节保持不变。歧义或不安全结构 fail-closed，Validator 不放宽。
- 失败草稿恢复仍复用同一入口：新稿必须先完成 Extract、Normalize 和 Validator；只有旧 inbox 被当前 Validator 明确拒绝且正式 Archive 不存在时，才按 `YYYY-MM-DD-rejected-NNN.md` 排他保留旧稿并继续入库。新稿失败、旧稿有效、读取/Validator 异常或已有 Archive 均不得替换。

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

- [x] （Historical / Superseded）曾固定每天设备本地时钟 08:00、每周 7 天运行；已由 Decision 019 改为云端按需触发
- [x] 将 Daily Market Report Master Prompt 纳入 Git 版本管理
- [x] （Historical / Superseded）曾创建 Active 的 `Market Daily Archive 日报入库` 桌面端任务；已按 Decision 019 暂停但不删除
- [x] 自动创建 `docs/YYYY/MM/YYYY-MM-DD.md`
- [x] 自动维护首页、总档案、年/月索引与 MkDocs 导航
- [x] 防止同一天不同内容重复导入，并支持相同内容幂等重跑
- [x] 保留日报标题、正文结构和来源链接
- [x] 增加发布前 fail-closed 完整性与来源校验
- [x] 在首次无人值守运行前完成正式日报模板、Master Prompt 1.1 与 Validator 定版
- [ ] （Cancelled by Decision 019）首次真实无人值守入库验收
- [x] Master Prompt 1.2 区分云端聊天输出与本地归档职责，不改变已定版字段和质量要求
- [x] （Historical / Superseded）原「美股市场日报」云端任务曾恢复定时运行；已由 Decision 019 改为专用 ChatGPT Project 按需生成
- [ ] （Cancelled by Decision 019）首次云端定时运行验收
- [x] Canary 验证 ChatGPT Cloud Scheduled Task 未完成无人值守 GitHub 写入，放弃直接写仓库的方案 A
- [x] 实现 Plan B Responses API 唯一生成器、Web Search 与 runner 临时 staging
- [x] 新增 `generate-daily.yml`：08:00 SGT cron、手动 dispatch、并发串行、fail-closed 分层和确定性发布
- [x] Master Prompt 1.3 改为交付中立的一次生成规范，不再长期描述两套独立 AI 生成职责
- [x] 新增剪贴板半自动入口：stdin → inbox → Validator → deterministic importer → strict build
- [x] 新增 macOS 原生一键 App：复制完整日报后单击归档，无需打开 Terminal
- [x] 增加 Validator 前的白名单 Markdown normalizer，仅处理可证明安全的跨资产列表 marker 差异
- [x] 增加失败草稿安全恢复，并用 `2026-09-03` 真实生成质量故障完成用户验收（Accepted）
- [x] 新增“打开 Market Daily Archive”原生 App，并完成后台服务、页面身份和单实例真实验收（Accepted）
- [x] 完成“ChatGPT 复制回复 → 归档今日日报 App → Extract → Normalize → Validator → Import → MkDocs”真实使用验收（Accepted）
- [x] Master Prompt 1.6 改为云端按需触发及平台原生可点击来源契约；Archive Validator 保持不变
- [ ] （Deferred）如未来明确重新启用 Plan B，再设置 secret、验收 workflow 并开启 cron

#### V2.2 — 自动发布

- [x] 严格构建、自动 commit 与 push
- [x] 核对本地与远程提交，等待 GitHub Pages workflow
- [x] 验证最终线上日报页面并提供可恢复重跑路径
- [x] 手动检查并补跑入口：识别阶段、复用草稿/提交、拒绝内容冲突、有限部署重试和逐层状态摘要
- [x] 手动缺失日报优先复用聊天中已有 Markdown；Plan B dispatch 与本地第二次生成均不自动运行
- [ ] （Cancelled by Decision 019）首次真实无人值守发布验收

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
- **Status**：Historical；日报生成方式已由 Decision 019 取代，本机定时任务保留历史但处于暂停状态。

### Decision 008 — 每天设备本地 08:00 调度，日报日期使用 Asia/Singapore

- **Decision**：任务每周 7 天跟随设备本地时钟 08:00 运行，以执行时的 `Asia/Singapore` 日期命名日报；周末和美国休市日生成休市版。当前设备时区为 `Asia/Shanghai`，与 SGT 同为 UTC+8。
- **Reason**：用户选择跟随设备本地时钟；当前实际执行时刻仍为 08:00 SGT，可在美国正常收盘后保留约 3–4 小时用于确认收盘数据、盘后新闻和媒体复盘，同时不受美国夏令时 / 冬令时切换影响。
- **Date**：2026-08-30
- **Impact**：所有日期判断、文件名和 H1 以新加坡日期为准；不得改用纽约时区。调度会跟随设备时区，如果设备以后离开 UTC+8，需要复核执行时刻。休市日仍执行，但不重复没有新交易产生的静态美股数据。
- **Status**：Historical；固定调度已由 Decision 019 取消，但所有 report date 仍严格使用 Asia/Singapore。

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
- **Status**：作为迁移期旧任务边界保留；目标生产架构已由 Decision 013 取代，待 Plan B 真实验收后完成任务切换。

### Decision 013 — Single Generation, Multiple Outputs 使用 GitHub Actions + OpenAI API

- **Decision**：放弃 ChatGPT Cloud Scheduled Task 直接写 GitHub 的方案 A。Plan B 由 GitHub Actions 每天 00:00 UTC（08:00 Asia/Singapore）读取唯一 Master Prompt，通过 OpenAI Responses API 与 Web Search 生成一份 canonical Markdown；AI 输出只进入 runner 临时目录，Validator 通过后才由既有 importer、strict build、Git/Pages 与页面验证完成确定性发布。ChatGPT 阅读任务在验收后只展示当天正式 Archive，不再生成第二份日报。
- **Reason**：隔离 canary 的一次性云端任务有完成记录，但 canary 分支 SHA 未变化且目标文件不存在，证明当前无人值守 ChatGPT Cloud → GitHub 写入能力未通过。把生成放在 GitHub Actions 可去除 Mac 依赖、消除双生成，并让凭证、并发、失败层和远程状态可审计。
- **Date**：2026-09-01
- **Impact**：新增 `generate-daily.yml`、Responses API 生成器、临时 staging、云端 dispatch 辅助入口及测试；需要 repository secret `OPENAI_API_KEY`。Cron 已按最终时间登记但由 `MARKET_DAILY_CRON_ENABLED` 门控，至少一次真实手动全链路成功前不接管生产，也不修改或暂停两个旧任务。API/联网、Validator、Import、Build、Commit、Push、Deploy、Verify 任一失败均 fail closed；未经验证的 AI 输出不进入 Git history。V2.3 继续延后。

### Decision 014 — 剪贴板半自动入库作为当前最低复杂度路径

- **Decision**：当前优先使用 `pbpaste | ./scripts/import_chatgpt_daily.sh`，把 ChatGPT 已生成的一份完整 Markdown 交给本地 Validator、确定性 importer 和严格 MkDocs 构建。Plan B 代码保留但不启用，不设置 `OPENAI_API_KEY`，也不 dispatch Generate workflow。
- **Reason**：ChatGPT Cloud 无法可靠无人值守写 GitHub，而两个独立 AI 任务会重复研究、耗时且正文可能分叉。人工复制是当前最小且清晰的交接点，不需要新增 API、云端写权限或 Mac 端生成器。
- **Date**：2026-09-01
- **Impact**：聊天阅读版与本地 Archive 复用同一份 Markdown；本地入口不 commit、push 或发布，只保证 inbox、Validator、入库与 strict build。失败保持 fail closed，同日不同内容禁止覆盖。两个现有任务在用户实际验收脚本前均不暂停；V2.3 仍不开始。

### Decision 015 — macOS 原生 App 作为日常一键入口

- **Decision**：用 macOS 内置 JXA 编译轻量 `.app`，负责读取剪贴板、定位项目目录并调用 `scripts/import_chatgpt_daily.sh`；编译后的 App 留在 `macos/` 且 Git 忽略，源码和可重复安装脚本进入版本管理。
- **Reason**：Shortcuts 需要额外导入和权限配置，Automator Quick Action 更依赖上下文；原生 App 可以直接双击或拖入 Dock，错误反馈明确，且不复制任何 Validator/importer 逻辑。当前机器的 AppleScript 编译器无法解析 Standard Additions，JXA 使用同一套 macOS 原生能力并可稳定编译。
- **Date**：2026-09-01
- **Impact**：日常流程缩短为“复制回复 → 点击 App”，无需 Terminal、网络或新依赖。Launcher 允许 ChatGPT 在正式日报前附带说明文字，但只在唯一 YAML 标题或精确 H1 边界可确定时剥离前缀，正文不做修复；项目移动后需重新运行一次安装脚本以刷新 App 内的项目路径。所有 Validator、幂等和 fail-closed 安全边界保持不变。

### Decision 016 — Validator 前只允许白名单 Markdown marker 规范化

- **Decision**：在剪贴板边界提取后、Validator 前运行确定性 normalizer。唯一允许的改写是：当唯一 `## 跨资产观察` 章节的全部非空行恰好为 2–5 个从 `1. ` 开始连续编号、顶格且无续行的完整结论时，仅把每个 `N. ` marker 转为 `- `。已经合规的内容保持字节不变。
- **Reason**：真实 ChatGPT“复制回复”正文虽然包含完整的 5 条跨资产结论，但输出为有序列表，导致严格 Validator 拒绝。该表现层差异可以在不解释或重写内容的前提下确定性消除。
- **Date**：2026-09-02
- **Impact**：公共入口固定为 `Extract → Normalize → Validator → Import`，App 与命令行复用同一实现。混合列表、跳号、缩进、续行、条目数量越界或章节歧义不会被猜测性修复；在 Normalize 或 Validator 层 fail-closed。同日期不同内容保护及 Validator 规则不变。

### Decision 017 — 原生 App 复用单一、经身份验证的本地 MkDocs 服务

- **Decision**：新增 `macos/打开 Market Daily Archive.app`，由 JXA 调用 Python 标准库控制器；控制器用文件锁串行检查/启动流程，只在 `127.0.0.1:8000` 返回 Market Daily Archive 的唯一页面标记时复用服务，否则端口空闲才以独立后台会话启动本项目 MkDocs。
- **Reason**：提供不依赖 Terminal 的一键本地阅读，同时避免 Finder/Dock PATH 差异、重复服务器以及把其他本地程序误识别为 Archive。
- **Date**：2026-09-02
- **Impact**：安装器同时编译两个 App，并嵌入安装时已验证的 Python/MkDocs 绝对路径。只允许同主机同端口的 MkDocs 本地重定向；其他占用 fail-closed。App 退出后 MkDocs 保持后台运行，日志、PID 和锁都留在 Git 忽略的 inbox；该入口不调用 AI/API、Importer、Git 或外部网络。

### Decision 018 — 只允许当前 Validator 已证明失败的 inbox 草稿被恢复

- **Decision**：保留同日期不同内容默认拒绝规则；仅当正式 Archive 不存在、新候选稿先通过当前 Validator、旧 inbox 由同一 Validator 明确抛出 `ValidationFailure` 时，允许自动恢复。替换前将旧稿按 `inbox/rejected/YYYY-MM-DD-rejected-NNN.md` 排他保存，复核旧稿字节未变化后再原子替换。
- **Reason**：真实日报的生成端质量问题可能在同一天修复，失败草稿若永久占据 inbox 会阻断合法重试；同时，Validator 运行异常、读取失败或旧稿仍有效都不能被误当成“已拒绝”。
- **Date**：2026-09-03
- **Impact**：日常 App 和命令行继续共用 `import_chatgpt_daily.sh`，不新增人工删除步骤。新稿失败不改变旧稿；正式 Archive 已存在、旧稿有效或失败无法证明时继续 fail-closed。rejected 历史不进入 Git，序号碰撞只会选择下一个名称，永不覆盖已有审计记录。Validator、Normalizer、Extract 与 Importer 本身不变。

### Decision 019 — 日报生成改为云端按需触发，本地只做确定性归档

- **Decision**：停止每天自动生成日报。用户在手机或 Mac 的专用 ChatGPT Project 中输入 `生成今日市场日报` 时，云端才读取 GitHub `main/prompts/daily_market_report.md` 最新版本、按 Asia/Singapore 确定日期并联网研究；本地只消费这同一份结果，执行确定性归档、校验、构建和按需发布。
- **Reason**：定时生成不再符合用户的实际使用方式；云端按需生成可在 Mac 关机时从手机或 Mac 发起，同时避免本地与云端重复研究、内容分叉和不必要的自动化复杂度。GitHub Master Prompt 继续作为唯一长期真源，Project Instructions 只保存最短 bootstrap，不复制日报规则。
- **Date**：2026-09-04
- **Impact**：本机 `Market Daily Archive 日报入库` 自动任务暂停但不删除；正式 `美股市场日报` 不再作为每日启用的生成路径；临时重跑任务与 GitHub Write Canary 保持结束 / disabled，Plan B 保持 disabled。Master Prompt 1.6 使用云端按需触发和 ChatGPT 平台原生可点击来源契约；Archive Validator 的标准 HTTPS Markdown 链接门槛不变。Clipboard Bridge 必须等待完整真实日报 pasteboard 样本证明可无歧义转换后另行实施，本阶段不实现。V2.3 不开始。

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

当前阶段：**V2 – Automated Daily Ingestion / Stable Use Observation（稳定使用观察期）**

已完成：

- V1 已完成并通过 `2026-08-30` 真实日报的页面、目录和阅读效果验收。
- V2.1 确定性入库器已实现：日期校验、正确目录写入、正文与来源保留、导航生成和重复导入保护。
- V2.2 发布脚本已实现：严格构建、commit、push、远程 SHA 核对、Actions 等待和线上页面验证。
- 入库器单元测试和现有日报幂等重跑验证已通过；V1 网站严格构建保持成功。
- 自动入库架构与恢复方式已写入维护文档。
- 本机 `Market Daily Archive 日报入库` 历史任务保留但已暂停，不再每天自动生成日报。
- Daily Market Report Master Prompt 已版本化保存于 `prompts/daily_market_report.md`。
- 发布链路已增加 fail-closed 质量闸门，并用自动测试覆盖完整交易日、休市版、非关键数据暂缺及残缺报告拒绝。
- 首次无人值守运行前的日报模板已正式定版：Master Prompt 升级至 1.1，Validator 与维护模板同步增加 30Y、DXY、Fed Rate Expectations、Russell 2000、文字风险状态和跨资产观察。
- `2026-08-30` 休市样板已按新版结构更新，并只补充有可靠来源支持的历史数据。
- `2026-08-31` 首轮定时日报已完成入库、提交、push、远程 SHA、Actions 和 Pages 验证；执行中曾因沙盒认证访问受限而授权重试，不据此宣称全程无人介入已验收。
- V2 支持“检查并补跑今日日报”：已有内容优先复用，按阶段恢复，并以相同 Validator、幂等和 fail-closed 规则控制发布；已完整发布返回无需补跑。独立恢复测试覆盖生成、部分入库、构建、推送与部署故障。
- Master Prompt 1.2 已明确云端阅读 / 本地归档边界，保留 1.1 的全部指标、章节和来源标准；云端只在线读取 GitHub 最新文件，不运行本地链路。
- 正式 ChatGPT `美股市场日报`（task ID `6a926a3bc8b08191b2716beb708e1c59`）已确认 `is_enabled: false`；保留的 schedule 为每天 09:15、`Asia/Shanghai`、`flexible_schedule`，不会再自动生成。任务已处于暂停状态，因此未重复修改。
- Isolated GitHub write canary 已完成：ChatGPT Cloud 一次性任务产生完成记录，但隔离分支 SHA 未前进、目标文件为 404，方案 A 未通过且未触碰 main、Pages 或两个正式任务。
- Plan B 仓库实现已完成：Responses API + Web Search 唯一生成器、runner 临时 staging、`generate-daily.yml`、既有 Validator/importer、strict build、受限提交、远程 SHA、Pages dispatch 与最终页面正文验证。
- Master Prompt 升级至 1.6：生成改为云端按需触发，report date 仍按 Asia/Singapore；`trading_day` 必须含至少 3 个来自本次实际研究的可点击平台原生来源引用。生成端不再强制 Archive 专用 Markdown URL 表示，但本地 Validator 的标准 HTTPS Markdown 链接门槛不变。
- 生成 workflow 已配置 `0 0 * * *`、固定 concurrency group 与八层 fail-closed Summary；真实手动验收前由 `MARKET_DAILY_CRON_ENABLED` 门控，不会直接接管每日生产。
- 手动恢复口令在缺失日报时优先要求复用 ChatGPT 聊天中已有 Markdown；不自动 dispatch Plan B，也不在本地生成第二份日报。
- 当前完整回归测试与 `mkdocs build --strict` 保持通过；测试覆盖 ChatGPT 边界提取、白名单 Normalize、生成端来源契约、Validator/Importer/恢复链路，以及本地 MkDocs 的正确页面复用、其他端口占用拒绝、启动就绪竞态、同源重定向约束和单实例行为。
- 新增本地半自动入口 `scripts/import_chatgpt_daily.sh`：直接消费 ChatGPT 已生成的完整 Markdown，安全写入 gitignored inbox，复用 Validator 和 deterministic importer，并执行 strict build；不调用 AI/API、Git 或 GitHub。
- 半自动入口的自动测试覆盖成功导入、空输入、同内容幂等、inbox/Archive 内容冲突、Validator fail-closed、日期不一致和构建失败。
- Plan B 代码保留但不启用：不设置 `OPENAI_API_KEY`、不 dispatch Generate workflow，cron 门控保持关闭。
- 已生成本机 `macos/归档今日日报.app`：读取剪贴板并调用既有入库脚本，成功时显示原生通知、失败时显示原生对话框，不打开 Terminal；源码、安装器和安全契约测试已纳入项目。
- 首次点击发现 launcher 错将 macOS `test` 写为 `/usr/bin/test`。最终修复已完全移除冗余的 `test` 前置检查，固定 App 的 PATH、shell 与系统命令路径，记录 gitignored 的完整运行日志，并在安装后尽力刷新 Launch Services；重新编译后的 App 不包含任何 `test` 调用。
- 第二次点击确认 App 的非交互 shell 未继承 Terminal 的 UTF-8 locale，导致 `pbpaste` 按非 UTF-8 编码输出中文。Launcher 已固定 `LANG/LC_ALL=en_US.UTF-8`、使用 `pbpaste -Prefer txt`，并优先提取 `Final result` 作为简短错误提示；编码失败停在 Input 层，没有运行 Validator 或修改 Archive。
- 第三次点击已越过编码层，但剪贴板未保留严格的 `# YYYY-MM-DD 市场日报` 标题。日期提取现可安全识别 front matter、宽松 H1 或首行中的唯一日期，再交给原 Validator 执行严格结构检查；无法识别时会明确提示使用 ChatGPT 消息自带的复制按钮。失败仍停在 Input 层，未修改 Archive。
- 程序注入纯 Markdown 的 App 全链路测试已通过，但不再视为 ChatGPT“复制回复”的真实验收。真实 pasteboard 诊断显示 ChatGPT 同时提供 HTML 和 UTF-8 纯文本，`pbpaste` 默认与 `-Prefer txt` 内容一致；该次回复在 YAML 前附带 999 个字符，并因同日期正文不同停在 Draft 层，日报本体还因 `跨资产观察` 使用编号列表而不满足 Validator。现有 `2026-09-01` inbox 与 Archive 未覆盖。
- Launcher 已增加确定性剪贴板边界提取：唯一 YAML 标题优先、唯一精确 H1 兜底，安全忽略前置说明而不改变正文；多候选、代码块内候选或无候选直接停止。App 已重新编译并反编译确认包含新版提取链路。今天只验证解析逻辑，真正无冲突归档验收留给下一个尚未归档日期。
- 新增 Validator 前的极小范围 deterministic normalizer：只把 `跨资产观察` 中可证明安全的 2–5 个连续 `N. ` marker 转为 `- `，不改变条目内容或其余字节；所有不确定结构 fail-closed，Validator 原规则保持不变。
- `2026-09-02` 真实 ChatGPT 草稿经独立字节证明后完成规范化：5 个 marker 是唯一差异，去除 marker 后章节 SHA-256 完全一致；随后通过原 Validator、deterministic importer 与严格构建，正式本地 Archive 已生成。
- 已生成 `macos/打开 Market Daily Archive.app`：Finder/Dock 启动时使用固定环境和已验证的 `.venv` 绝对路径，后台启动或复用本地 MkDocs，确认页面身份后打开默认浏览器。真实验收从关闭端口开始，首次启动 PID 52080，第二次仍为同一 PID，且监听数量始终为 1。
- **Accepted**：`ChatGPT 复制回复 → 归档今日日报.app → Extract → Normalize → Validator → Import → MkDocs` 已通过真实日报与真实 App 使用验收。
- **Accepted**：`打开 Market Daily Archive.app → 复用/启动单一本地 MkDocs → 验证页面身份 → 默认浏览器打开` 已通过真实双击与单实例验收。
- 当前推荐日常操作为“手机 / Mac 专用 ChatGPT Project 输入 `生成今日市场日报` → 云端生成 → 需要归档时在 Mac 复制回复 → 点击归档 App → 点击打开 Archive App”；进入稳定使用观察期。
- **Accepted**：`2026-09-03` 真实日报先因 Sources 缺少 URL 被 Validator 拒绝；生成端按 Master Prompt 1.5 修复后，用户通过真实“复制回复 → 归档今日日报.app”完成安全恢复。旧失败稿保留在 rejected history，正式 Archive 只有一个版本且通过 Validator；普通同日内容冲突仍拒绝。
- Decision 019 已确立云端按需生成与本地确定性归档边界；临时 `美股市场日报 临时重跑 20260904` 和 GitHub Write Canary 保持结束 / disabled，不删除历史。
- 云端 ChatGPT Project `Market Daily Archive` 已由用户创建，最短 bootstrap instruction 已保存；首次 `生成今日市场日报` 的真实云端验收等待 Master Prompt 1.6 推送到 GitHub `main` 后执行。

尚未完成：

- 专用 ChatGPT Project 已建立；首次按需生成真实云端验收尚待执行。
- 完整日报的 clipboard bridge 尚未实现；必须先用真实完整日报验证 plain text 与 `public.html` 的引用数量、顺序、显示文字和 URL 可无歧义对应。
- V2.3 月报未开始。

下一步：本次改动推送 GitHub `main` 后，用户在已建立的专用 ChatGPT Project 中输入 `生成今日市场日报`，验证云端读取 Master Prompt 1.6、按需生成且来源引用符合新契约。验收后再采集一份完整真实日报的 plain text + `public.html` 样本；只有证明引用能无歧义确定性转换时才考虑 Clipboard Bridge。继续不启用 Plan B、不设置 `OPENAI_API_KEY`、不开发 V2.3 月报。

运行条件：云端按需生成不依赖 Mac 开机；本地归档仍需要 Mac、本地仓库、Python 3、MkDocs 和用户把完整聊天日报复制到剪贴板。当前 App 尚不能把 ChatGPT 平台原生引用转换为 Validator 所需的 Markdown HTTPS 链接，因此 Clipboard Bridge 验收完成前，该表示差异仍会 fail-closed。App 不调用 OpenAI API 或联网补来源；Plan B 的历史实现保留但不启用。

## 10. Change Log

### 2026-09-04

- 采用 Decision 019：日报生成从 scheduled generation 改为专用 ChatGPT Project 中的 cloud on-demand generation。本机 `Market Daily Archive 日报入库` 任务已暂停但不删除；正式云端 `美股市场日报`（task ID `6a926a3bc8b08191b2716beb708e1c59`）确认已是 disabled，保留的 schedule 为每天 09:15、Asia/Shanghai；临时重跑任务和 GitHub Write Canary 保持结束 / disabled，Plan B 保持 disabled。
- Master Prompt 升级至 1.6：移除固定 08:00 生成职责，按每次调用时的 Asia/Singapore 日期生成；`trading_day` 强制至少 3 个来自本次实际研究的可点击平台原生来源引用，禁止只有来源名称、猜测 URL 或伪造引用。Archive Validator 仍要求标准 HTTPS Markdown 链接，未作放宽。
- 专用 ChatGPT Project 的 bootstrap 只负责读取 GitHub `main/prompts/daily_market_report.md` 最新版本并严格执行，读取或版本确认失败即停止，不保存 Master Prompt 副本。Clipboard Bridge 延后至完整真实日报 pasteboard 映射可被无歧义证明后再决定是否实现；Current Status 保持 Stable Use Observation，V2.3 未开始。
- 用户已建立云端 ChatGPT Project `Market Daily Archive` 并保存 bootstrap instruction；首次按需生成真实云端验收安排在 Prompt 1.6 推送到 GitHub `main` 之后。

### 2026-09-03

- 新增失败草稿安全恢复：新稿先通过原 Validator，旧 inbox 必须被同一 Validator 明确拒绝且正式 Archive 不存在；旧稿按排他递增序号保存在 gitignored `inbox/rejected/` 后才允许替换。`2026-09-03` 真实用户流程已完成验收：旧失败稿完整保留、新稿通过 Validator 并生成唯一正式 Archive。新稿失败、旧稿有效、无法证明失败、历史名称碰撞或已有 Archive 均 fail-closed；Extract、Normalize、Validator、Importer 与定时任务不变。
- 真实日报因 Sources 只有来源名称和文章标题、整篇没有任何 URL 而被 Validator 正确拒绝。Master Prompt 升级至 1.5，在既有 Source rules 内明确 trading-day 至少 3 个 `[标题](https://...)`、URL 必须来自本次实际研究、无 URL 的名称或标题不计数、不得猜测链接，并要求输出完整日报前自检；Extract、Normalize、Validator、Importer 与失败 draft 均未修改。

### 2026-09-02

- 两个 Mac App 与真实日报归档流程完成用户实际验收：半自动链路和本地阅读入口正式标记为 Accepted，项目进入稳定使用观察期；当前推荐流程固定为“复制回复 → 归档 App → 打开 Archive App”，本阶段不再增加功能。
- 基于真实 `2026-09-02` inbox 取证，新增 Validator 前的白名单 Markdown normalizer：仅转换唯一跨资产章节中 2–5 个连续、顶格、单行 `N. ` marker，混合或不确定结构 fail-closed；Validator、幂等与同日冲突保护不变。真实草稿的非 marker 字节一致性证明、Validator、入库和严格构建均通过。
- 新增并编译 `打开 Market Daily Archive.app`：以固定本机环境启动/复用后台 MkDocs，页面身份与同源重定向验证通过后打开默认浏览器，其他 8000 端口占用 fail-closed。真实两次 App 启动保持同一 PID 和单一监听服务；现有任务、Plan B、日报内容及 Git 远程均未改变。

### 2026-09-01

- 基于真实 ChatGPT“复制回复”pasteboard 取证，新增 fail-closed 日报边界提取器并接入、重新编译 Mac App：唯一 YAML 标题优先、精确 H1 兜底，只忽略日报前说明文字，正文原字节不变；补充歧义、代码块、优先级和 Validator 严格性测试。Master Prompt 升至 1.4，明确 `跨资产观察` 必须使用 `- ` 项目符号。`2026-09-01` 内容冲突未覆盖，首次真实无冲突验收延后到新日期。
- 完成程序注入纯 Markdown 的 Mac App 全链路测试：系统剪贴板 → 已编译 App → inbox → Validator → deterministic importer → `mkdocs build --strict` 全部成功；实际重建正式日报且 SHA-256 与输入一致，相同内容重跑不改写文件或导航。该结果验证了 launcher 之后的确定性链路，但不替代真实 ChatGPT“复制回复”验收。最终 launcher 移除全部 `test` 前置调用、固定运行环境并新增 gitignored 完整运行日志；现有任务、Plan B 和 V2.3 均未改变。
- 新增 macOS 原生一键归档 App：自动读取剪贴板并调用既有半自动入口，显示简洁成功/失败对话框，不打开 Terminal；JXA 源码、可重复安装器与 2 项安全契约测试进入版本管理，编译后的 App 保持 Git 忽略。现有任务、Plan B 和 V2.3 均未改变。
- 修复首次 App 点击暴露的 macOS 系统命令路径问题：`test` 从不存在的 `/usr/bin/test` 改为 `/bin/test`，重新编译并增加防回归检查；故障发生在入库前，未产生日报或导航变化。
- 修复 App 非交互 shell 的剪贴板编码：显式设置 UTF-8 locale、优先读取纯文本，并改进 CR/LF 错误摘要；此前 UnicodeDecodeError 停在 Input 层，未进入 Validator 或 Archive。
- 改进剪贴板 Markdown 诊断：日期提取可从 front matter、宽松 H1 或首行取得唯一候选，但不放宽 Validator；缺少原始 Markdown 时明确提示使用 ChatGPT 消息自带的复制按钮，并新增 2 项测试。
- 实施最低复杂度半自动入库：新增 `pbpaste | ./scripts/import_chatgpt_daily.sh`，复用既有 Validator、deterministic importer 和 strict build，不调用 AI/API、不 push；增加冲突、幂等、校验和构建失败测试及维护文档。Plan B 代码保留但不启用，两个现有任务不修改、不暂停。
- Isolated GitHub write canary 未通过：ChatGPT Cloud Scheduled Task 有一次完成记录，但隔离分支未产生 commit、目标文件不存在；main、Pages 和两个正式任务均未改变，因此正式放弃方案 A。
- 实施 Plan B 的 Single Generation, Multiple Outputs 仓库链路：GitHub Actions + OpenAI Responses API/Web Search 唯一生成，runner 临时 staging 后复用 Validator、importer、strict build、Git/Pages 和最终正文验证。
- 新增 08:00 SGT cron、手动 dispatch、并发串行、八层 fail-closed Summary、API/空输出/截断/幂等/冲突/workflow 自动测试与云端补跑入口；59 项测试和严格构建通过，API Key 仅允许使用 GitHub secret。
- Master Prompt 升级至 1.3，移除两套独立生成职责；真实 API 全链路验收前 cron 保持门控，两个旧任务不修改、不暂停，V2.3 不开始。

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
