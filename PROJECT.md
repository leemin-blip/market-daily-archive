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
- [ ] 添加目标远程并推送 `main`
- [ ] 在 GitHub 仓库中确认 Pages 首次部署成功

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

## 8. 维护规则

每完成一个项目阶段，都必须同步更新：

1. `Roadmap` 中对应复选框。
2. `Current Status` 的阶段、已完成项和下一步。
3. `Change Log` 中的日期与变更摘要。

涉及架构、工具或目录约定的新决定时，同时新增一条 Architecture Decision。

## 9. Current Status

当前阶段：**V1 / 首次推送与 Pages 部署**

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

下一步：添加目标仓库为 `origin`、推送 `main` 并观察 GitHub Pages 首次部署结果。

阻塞项：无。目标仓库已由用户创建并确认为空仓库。

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
