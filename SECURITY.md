# Security Policy

Market Daily Archive is intended to be published from a public GitHub repository. Repository contents must therefore be treated as public information.

## Secrets and credentials

Never commit any of the following:

- API keys or access tokens
- passwords
- private keys or certificates
- `.env` files
- cloud, broker, data-provider, or AI-service credentials
- personal financial account data

Local environment and credential files are excluded by `.gitignore`, but ignore rules are not a substitute for reviewing changes before every commit.

GitHub Actions uses the repository secret `OPENAI_API_KEY` for the Plan B daily generator. Workflows must reference it only through GitHub Actions expressions and must never embed or copy its value into YAML, Markdown, `.env`, artifacts, step summaries, command arguments, or debug output. Shell tracing must remain disabled around secret-bearing steps, and API error handling must not print raw response bodies.

## Before committing

1. Review all files listed by `git status`.
2. Inspect the staged diff.
3. Check for `.env`, certificate, private-key, credential, and secret files.
4. Search for unexpected tokens, passwords, and API keys.

If a secret is committed, revoke or rotate it immediately. Removing it from the latest commit alone is not sufficient because it may remain in Git history.
