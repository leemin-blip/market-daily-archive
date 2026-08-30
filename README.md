# Market Daily Archive

个人金融市场日报档案库。内容以 Markdown 保存，通过 Material for MkDocs 生成可搜索的书籍式网站，并由 GitHub Actions 部署至 GitHub Pages。

项目设计、当前进度与后续路线请查看 [PROJECT.md](PROJECT.md)。

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

## 新增日报

1. 复制 `docs/maintenance/daily-template.md` 到 `docs/YYYY/MM/YYYY-MM-DD.md`。
2. 完成日报内容并保留来源链接。
3. 将日报加入对应月份索引、`docs/archive.md` 和 `mkdocs.yml` 导航。
4. 运行严格构建检查后提交。
