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

### V1

- 每日一篇 Markdown 日报。
- 年 / 月 / 日三级档案结构。
- Material for MkDocs 书籍式导航。
- 中英文全文搜索。
- GitHub Actions 自动构建并部署到 GitHub Pages。

### 暂不包含

- 自动生成日报内容。
- 从 ChatGPT 自动写入 GitHub。
- 数据库、知识图谱或 AI 问答。

## 3. 技术栈

| 层级 | 选型 | 用途 |
| --- | --- | --- |
| 内容 | Markdown | 长期可读、可迁移、Git 友好 |
| 版本与远程存档 | Git / GitHub | 历史追踪与托管 |
| 静态网站 | Material for MkDocs | 书籍式导航、搜索与主题 |
| 自动化 | GitHub Actions | 构建与部署 |
| 托管 | GitHub Pages | 公开或私有可访问的网站 |

## 4. 目标目录结构

```text
market-daily/
├── PROJECT.md
├── README.md
├── SECURITY.md
├── requirements.txt
├── mkdocs.yml
├── docs/
│   ├── index.md
│   ├── archive.md
│   ├── maintenance/
│   │   └── daily-template.md
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
  - 市场摘要
  - 利率
  - 波动率（VIX / VXN）
  - 美股指数
  - Magnificent Seven
  - 半导体
  - 商品（WTI / 黄金）
  - 重要市场新闻
  - Sources
- 每条外部信息应尽可能保留原始来源链接。
- 新日报同时加入 `mkdocs.yml` 导航、对应月份索引和总档案页。

## 6. Roadmap

### V1 — 可用的日报网站

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

### V2 — 日报自动进入档案

- [ ] ChatGPT 日报自动写入 GitHub
- [ ] 自动维护导航与档案索引
- [ ] 自动生成月报与月度市场回顾

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

当前阶段：**V1 完成，首篇真实日报阅读效果测试**

已完成：

- 确认当前工作区为空且不是已有 Git 仓库，不会影响其他项目。
- 确认本机未安装 GitHub CLI，尚未绑定任何远程仓库。
- 初始化本地 Git 仓库并建立项目知识库。
- 建立 2026 / 08 / 2026-08-30 的年、月、日书籍式目录。
- 建立首页、总档案、专题、统计和日报模板页面。
- 配置 Material for MkDocs 中文界面、中英文全文搜索、明暗主题与导航。
- 配置 GitHub Actions 在 `main` 分支更新时严格构建并部署至 GitHub Pages。
- 使用 Material for MkDocs 9.7.7 完成 `mkdocs build --strict` 验证。
- 验证首页、档案页、年 / 月 / 日页面、日报模板和全文搜索索引均已生成。
- 验证搜索索引包含 `美债`、`VIX`、`NVDA`、`WTI` 和 `日报模板`。
- 确认目标为 Public 仓库 `leemin-blip/market-daily-archive`。
- 完成本地敏感文件名与常见 Key / Token 格式扫描，未发现命中。
- 加强 `.gitignore` 并建立 `SECURITY.md`，明确公开仓库的凭证管理规则。
- 使用 `leemin-blip` 和确认的 GitHub noreply 邮箱创建本地初始提交。
- 只读确认目标 GitHub 仓库为 Public、0 KB 且没有远程 refs，可安全执行首次推送。
- 已将 `origin` 设置为 `https://github.com/leemin-blip/market-daily-archive.git`，并确认 GitHub CLI 当前登录账号为 `leemin-blip`。
- 原 OAuth Token 有 `repo` 权限但缺少 `workflow` scope；GitHub 因此拒绝包含 `.github/workflows/deploy-pages.yml` 的推送，远程仓库未被修改。
- 授权刷新后旧 Token 已失效，但新 Token 未成功写回自定义 `GH_CONFIG_DIR`；目前需要对该目录完成一次完整 `gh auth login`。
- 完成 GitHub CLI 重新登录并获得 `repo` 与 `workflow` scope，通过 macOS Keychain 安全提供 Git 凭据。
- 将完整 `main` 历史推送至 `leemin-blip/market-daily-archive`。
- 为目标仓库启用 GitHub Pages，发布源设为 GitHub Actions workflow，并强制 HTTPS。
- GitHub Actions 构建与部署全部成功；公网首页和搜索索引均返回 HTTP 200。
- 正式网站：<https://leemin-blip.github.io/market-daily-archive/>
- 将 `2026-08-30` 结构示例替换为首篇正式周末版美股市场日报。
- 保留既定的深度分析与来源链接，并依据休市日规则聚焦利率、外汇、能源、资金流、欧洲风险和 AI 产业动态。
- 同步更新首页、总档案、年度与月度索引；既有 `2026 → 08 月 → 2026-08-30` 导航保持有效。
- 正式建立跨会话项目维护规则，并以 Decision 006 固定 `PROJECT.md` 的知识库定位、更新条件和决策记录格式。

下一步：等待首篇正式日报的实际阅读反馈。按本轮范围要求，暂不开发日报自动写入、月报或其他 V2 / V3 功能。

阻塞项：无。

## 10. Change Log

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
