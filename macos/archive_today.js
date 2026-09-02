const app = Application.currentApplication();
app.includeStandardAdditions = true;

const projectRoot = "__PROJECT_ROOT__";
const importScript = `${projectRoot}/scripts/import_chatgpt_daily.sh`;
const extractorScript = `${projectRoot}/scripts/extract_chatgpt_daily.py`;
const runLog = `${projectRoot}/inbox/.archive-today-last-run.log`;

function shellQuote(value) {
  return `'${value.replace(/'/g, `'\\''`)}'`;
}

function lastUsefulLine(message) {
  const lines = String(message).split(/\r\n|\r|\n/).map((line) => line.trim());
  for (let index = lines.length - 1; index >= 0; index -= 1) {
    if (lines[index].startsWith("Final result: ")) {
      return lines[index].replace(/^Final result:\s*/, "");
    }
  }
  for (let index = lines.length - 1; index >= 0; index -= 1) {
    if (!lines[index]) continue;
    return lines[index];
  }
  return "未知错误";
}

function writeRunLog(message) {
  app.doShellScript(
    `/usr/bin/printf '%s\n' ${shellQuote(message)} > ${shellQuote(runLog)}`,
  );
}

try {
  const shellBody = [
    "set -o pipefail",
    "umask 077",
    `cd ${shellQuote(projectRoot)}`,
    'echo "Launcher PATH: $PATH"',
    'echo "Launcher shell: /bin/bash"',
    `echo "Clipboard parser: ${extractorScript}"`,
    `echo "Importer: ${importScript}"`,
    'clipboard_input=$(/usr/bin/mktemp "${TMPDIR:-/tmp}/market-daily-clipboard.XXXXXX")',
    'report_input=$(/usr/bin/mktemp "${TMPDIR:-/tmp}/market-daily-report.XXXXXX")',
    'cleanup_launcher() { /bin/rm -f "$clipboard_input" "$report_input"; }',
    "trap cleanup_launcher EXIT",
    '/usr/bin/pbpaste -Prefer txt 2>&1 > "$clipboard_input"',
    "clipboard_status=$?",
    'if [ "$clipboard_status" -ne 0 ]; then',
    '  echo "Clipboard status: FAILED"',
    '  echo "Final result: pbpaste could not read clipboard plain text. Nothing was imported."',
    '  launcher_status="$clipboard_status"',
    "else",
    `  /usr/bin/python3 ${shellQuote(extractorScript)} < "$clipboard_input" 2>&1 > "$report_input"`,
    "  extractor_status=$?",
    '  if [ "$extractor_status" -ne 0 ]; then',
    '    launcher_status="$extractor_status"',
    "  else",
    `    /bin/bash ${shellQuote(importScript)} < "$report_input" 2>&1`,
    "    launcher_status=$?",
    "  fi",
    "fi",
    "/usr/bin/printf '\\n__MARKET_DAILY_EXIT__=%s\\n' \"$launcher_status\"",
    "exit 0",
  ].join("\n");
  const rawOutput = app.doShellScript(
    `/usr/bin/env PATH=/usr/bin:/bin:/usr/sbin:/sbin LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 /bin/bash -c ${shellQuote(shellBody)}`,
  );
  const statusMatch = rawOutput.match(/__MARKET_DAILY_EXIT__=(\d+)\s*$/);
  const exitCode = statusMatch ? Number(statusMatch[1]) : 70;
  const output = rawOutput.replace(/\n?__MARKET_DAILY_EXIT__=\d+\s*$/, "");
  writeRunLog(`${output}\nLauncher exit code: ${exitCode}`);
  if (exitCode !== 0) {
    const importError = new Error(output);
    importError.launcherExitCode = exitCode;
    throw importError;
  }
  app.displayNotification("今日日报已成功归档", {
    withTitle: "Market Daily Archive",
  });
} catch (error) {
  try {
    if (error.launcherExitCode === undefined) {
      writeRunLog(
        `${String(error.message || error)}\nLauncher exit code: ${error.number || 1}`,
      );
    }
  } catch (_logError) {
    // The original import error remains the user-facing failure.
  }
  app.displayDialog(`归档失败\n${lastUsefulLine(error.message || error)}`, {
    withTitle: "Market Daily Archive",
    buttons: ["知道了"],
    defaultButton: "知道了",
    withIcon: "stop",
  });
}
