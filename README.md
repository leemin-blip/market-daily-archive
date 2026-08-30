# Market Daily Archive

个人金融市场日报档案库。内容以 Markdown 保存，通过 Material for MkDocs 生成可搜索的书籍式网站，并由 GitHub Actions 部署至 GitHub Pages。

项目设计、当前进度与后续路线请查看 [PROJECT.md](PROJECT.md)。

## 在线网站

[https://leemin-blip.github.io/market-daily-archive/](https://leemin-blip.github.io/market-daily-archive/)

## 本地预览

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

仓库提供确定性的日报入库与发布工具：

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
