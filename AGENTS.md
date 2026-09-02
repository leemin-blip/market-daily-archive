# Market Daily Archive 工作约定

开始本项目工作前，完整读取 `PROJECT.md`。项目级变更提交前同步维护知识库；普通日报不更新知识库。不要修改 Active 的 08:00 定时任务，不开发 V2.3，除非用户另行明确授权。

## “检查并补跑今日日报”

当用户使用这句话或要求恢复当天日报时：

1. 执行 `./scripts/check_and_recover_daily.sh --no-generate --json`。日期由脚本按 Asia/Singapore 计算；不要自行以纽约日期或固定日期替代。
2. 返回 0：向用户展示状态摘要和最终 URL。若已完整发布，原样告知“今日 Market Daily Archive 日报已完整发布，无需补跑。”不要再次生成、提交或推送。
3. **只有退出码 3 且 Blocked layer 为“生成”时**：不要 dispatch 保留但未启用的 Plan B，也不要生成第二份日报。请用户复制当天 ChatGPT「美股市场日报」的完整 Markdown，并运行 `pbpaste | ./scripts/import_chatgpt_daily.sh`；该入口复用同一 Validator 和 deterministic importer，只建立本地 Archive，不 push。
4. 本地导入成功后，再执行同日期的只读恢复入口：`./scripts/check_and_recover_daily.sh --no-generate --date YYYY-MM-DD --json`。需要远程发布时，明确报告本地已就绪以及尚缺 commit / push / Pages，由用户另行授权发布。
5. `generate-daily.yml`、`dispatch_daily_workflow.sh` 和本地生成代码仅作为 Plan B 保留。除非用户以后明确要求重新启用，否则不设置 API Key、不 dispatch、不调用任何 AI 或 OpenAI API。
6. 其他失败：按 Blocked layer 和 Next step 说明，不绕过 Validator，不重生成完整草稿，不自动覆盖不同内容，不强推，不造空提交，不把无关改动提交进仓库。

若生成本身异常或验证失败，停在该层，草稿只留在 Git 忽略的 inbox。网络、钥匙串或 .git 沙盒权限不足时，按应用审批机制申请本次操作所需权限；不要把访问失败直接解释为登录失效，不自动执行 `gh auth login` / `logout` 或修改认证配置。

日常 Mac 图形入口为 `macos/归档今日日报.app`，底层仍只调用 `scripts/import_chatgpt_daily.sh` 消费已经生成的完整 Markdown；命令行备用入口不变。不要为测试而额外生成或公开虚构日报。
