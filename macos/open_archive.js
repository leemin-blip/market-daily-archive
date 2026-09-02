const app = Application.currentApplication();
app.includeStandardAdditions = true;

const projectRoot = "__PROJECT_ROOT__";
const pythonBin = "__PYTHON_BIN__";
const mkdocsBin = "__MKDOCS_BIN__";
const controller = `${projectRoot}/scripts/open_local_archive.py`;
const runLog = `${projectRoot}/inbox/.open-archive-last-run.log`;
const archiveUrl = "http://127.0.0.1:8000/";

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
  return lines.find((line) => line) || "未知错误";
}

function writeRunLog(message) {
  app.doShellScript(
    `/usr/bin/printf '%s\n' ${shellQuote(message)} > ${shellQuote(runLog)}`,
  );
}

try {
  const shellBody = [
    "umask 077",
    `cd ${shellQuote(projectRoot)}`,
    `echo "Python: ${pythonBin}"`,
    `echo "MkDocs: ${mkdocsBin}"`,
    `${shellQuote(pythonBin)} ${shellQuote(controller)} --repo-root ${shellQuote(projectRoot)} --mkdocs ${shellQuote(mkdocsBin)} --state-dir ${shellQuote(`${projectRoot}/inbox`)} 2>&1`,
    "launcher_status=$?",
    "/usr/bin/printf '\\n__MARKET_DAILY_OPEN_EXIT__=%s\\n' \"$launcher_status\"",
    "exit 0",
  ].join("\n");
  const rawOutput = app.doShellScript(
    `/usr/bin/env PATH=/usr/bin:/bin:/usr/sbin:/sbin LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 /bin/bash -c ${shellQuote(shellBody)}`,
  );
  const statusMatch = rawOutput.match(/__MARKET_DAILY_OPEN_EXIT__=(\d+)\s*$/);
  const exitCode = statusMatch ? Number(statusMatch[1]) : 70;
  const output = rawOutput.replace(/\n?__MARKET_DAILY_OPEN_EXIT__=\d+\s*$/, "");
  writeRunLog(`${output}\nLauncher exit code: ${exitCode}`);
  if (exitCode !== 0) {
    const launchError = new Error(output);
    launchError.launcherExitCode = exitCode;
    throw launchError;
  }
  app.openLocation(archiveUrl);
} catch (error) {
  try {
    if (error.launcherExitCode === undefined) {
      writeRunLog(
        `${String(error.message || error)}\nLauncher exit code: ${error.number || 1}`,
      );
    }
  } catch (_logError) {
    // The original launch error remains the user-facing failure.
  }
  app.displayDialog(`无法打开本地 Archive\n${lastUsefulLine(error.message || error)}`, {
    withTitle: "Market Daily Archive",
    buttons: ["知道了"],
    defaultButton: "知道了",
    withIcon: "stop",
  });
}
