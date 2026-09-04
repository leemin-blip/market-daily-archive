# Market Daily Archive

个人金融市场日报档案库。内容以 Markdown 保存，通过 Material for MkDocs 生成可搜索的书籍式网站，并由 GitHub Actions 部署至 GitHub Pages。

项目设计、当前进度与后续路线请查看 [PROJECT.md](PROJECT.md)。

## 在线网站

[https://leemin-blip.github.io/market-daily-archive/](https://leemin-blip.github.io/market-daily-archive/)

## 本地预览

日常阅读可直接点击：

```text
macos/打开 Market Daily Archive.app
```

App 会检查 `http://127.0.0.1:8000/` 是否确实属于 Market Daily Archive。已运行时直接打开浏览器；未运行时在后台启动本项目的 MkDocs，等待页面验证成功后再打开。它不会重复启动第二个服务，也不会把占用 8000 的其他程序误认为 Archive。整个过程不需要 Terminal，App 退出后本地网站继续运行。

首次安装或项目路径、Python/MkDocs 环境变化后，运行一次 `./scripts/install_macos_launcher.sh` 会同时重建两个本机 App。命令行备用方式仍为：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
mkdocs serve
```

浏览器打开终端显示的本地地址即可预览。

## 构建检查

```bash
mkdocs build --strict
```

## V2 自动入库

正式日报生成规则保存在唯一真源 [`prompts/daily_market_report.md`](prompts/daily_market_report.md)。当前推荐最低复杂度流程是：在手机或 Mac 的专用 ChatGPT Project 中输入 `生成今日市场日报`，云端读取 GitHub 最新 Master Prompt 并只生成一次；需要归档时复制同一份回复，再使用下方 Mac 一键 App。需要诊断时仍可运行命令行备用入口：

```bash
pbpaste | ./scripts/import_chatgpt_daily.sh
```

该入口只在本机接收现有内容，依次执行 Extract、白名单 Normalize、日期检查、Validator、确定性 importer 与 `mkdocs build --strict`。它不调用 AI 或 OpenAI API，也不 commit、push 或发布；完成后可点击“打开 Market Daily Archive”在本地浏览和搜索。

同日不同内容默认仍拒绝覆盖。唯一自动恢复例外是：正式 Archive 尚不存在、新稿先通过当前 Validator、旧 inbox 再由同一 Validator 明确判定失败。此时旧稿会按不覆盖的递增序号保存在 Git 忽略的 `inbox/rejected/`，新稿才会替换 inbox 并继续入库。新稿失败、旧稿仍有效、旧稿无法读取或正式 Archive 已存在时都会 fail-closed。

### Mac 一键归档

仓库已提供并在本机生成原生 App：

```text
macos/归档今日日报.app
```

把 App 拖到 Dock 后，日常操作只有：**使用 ChatGPT 日报消息自带的“复制”按钮复制完整回复 → 点击“归档今日日报”**。App 优先从唯一 YAML `title: YYYY-MM-DD 市场日报` 定位正文，缺少可用 YAML 时才使用唯一精确 H1；日报前的 ChatGPT 说明文字会被忽略。之后只允许白名单 normalizer 把安全、连续的跨资产编号列表 marker 转成 `- `，条目内容和其余字节不变。多候选或不安全结构会 fail-closed，Validator 和同日防覆盖规则不变。成功会通知“今日日报已成功归档”，失败会显示简短原因，不打开 Terminal。完整的最近一次运行记录保存在 Git 忽略的 `inbox/.archive-today-last-run.log`，仅用于本机故障诊断。

两个 App 都是本机生成文件，不进入 Git，统一位于 `macos/`。需要重建时运行一次 `./scripts/install_macos_launcher.sh`；日常使用不需要运行安装命令。

GitHub Actions + OpenAI API 的 Plan B 代码继续保留，但 cron 保持门控且未启用。本机入库定时任务已暂停，正式 ChatGPT 日报任务也处于 disabled；日报只在专用 ChatGPT Project 中按需生成。两个 Mac App 与真实“复制回复”归档链路均已验收，项目继续处于稳定使用观察期。

Master Prompt 1.6 的生成端 Sources 使用 ChatGPT 平台原生可点击引用；本地 Archive Validator 仍要求标准 HTTPS Markdown 链接。Clipboard Bridge 尚未实现，必须先用完整真实日报证明纯文本与 HTML 引用能够无歧义对应，当前不会猜测或联网补链接。

发布前先执行 fail-closed 完整性校验：

```bash
python3 scripts/validate_daily.py \
  --date YYYY-MM-DD \
  --input inbox/YYYY-MM-DD.md
```

校验通过后，仓库提供确定性的日报入库与发布工具：

```bash
python3 scripts/import_daily.py \
  --date YYYY-MM-DD \
  --input inbox/YYYY-MM-DD.md \
  --summary "一行摘要"
```

完整的构建、提交、推送和 Pages 验证流程：

```bash
scripts/publish_daily.sh YYYY-MM-DD inbox/YYYY-MM-DD.md "一行摘要"
```

详细输入契约、重复导入保护和恢复方式见[自动入库说明](docs/maintenance/automated-ingestion.md)。
