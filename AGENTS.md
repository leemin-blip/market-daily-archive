# Market Daily Archive 工作约定

开始本项目工作前，完整读取 `PROJECT.md`。项目级变更提交前同步维护知识库；普通日报不更新知识库。不要修改 Active 的 08:00 定时任务，不开发 V2.3，除非用户另行明确授权。

## “检查并补跑今日日报”

当用户使用这句话或要求恢复当天日报时：

1. 执行 `./scripts/check_and_recover_daily.sh --no-generate --json`。日期由脚本按 Asia/Singapore 计算；不要自行以纽约日期或固定日期替代。
2. 返回 0：向用户展示状态摘要和最终 URL。若已完整发布，原样告知“今日 Market Daily Archive 日报已完整发布，无需补跑。”不要再次生成、提交或推送。
3. **只有退出码 3 且 Blocked layer 为“生成”时**：完整读取当前 `prompts/daily_market_report.md`，按脚本返回的 Report date 在当前会话联网研究，生成完整 Markdown 到 `inbox/YYYY-MM-DD.md`。先确认该路径及正式日报仍不存在，不覆盖新出现的文件。使用当前会话的研究能力即可，无须新建任务或调用另一个生成会话。
4. 运行现有 Validator；只有通过后才再次执行同日期的恢复入口：`./scripts/check_and_recover_daily.sh --no-generate --date YYYY-MM-DD --json`。
5. 其他失败：按 Blocked layer 和 Next step 说明，不绕过 Validator，不重生成完整草稿，不自动覆盖不同内容，不强推，不造空提交，不把无关改动提交进仓库。

若生成本身异常或验证失败，停在该层，草稿只留在 Git 忽略的 inbox。网络、钥匙串或 .git 沙盒权限不足时，按应用审批机制申请本次操作所需权限；不要把访问失败直接解释为登录失效，不自动执行 `gh auth login` / `logout` 或修改认证配置。

本地终端直接运行不带 `--no-generate` 的入口时，脚本仅在确认本地及远程都没有日报后，尝试使用已有 Codex CLI 的只读、联网生成能力；生成失败不会进入归档。不要为测试而额外生成或公开虚构日报。
