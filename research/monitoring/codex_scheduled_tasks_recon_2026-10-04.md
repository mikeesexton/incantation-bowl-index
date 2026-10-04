# Recon: weekly unattended auction-site browsing with OpenAI Codex (as of 2026-10-04)

Prepared by Claude Code for DISC-004 on 2026-10-04 from OpenAI web documentation. Recheck before relying on it; the product changes fast. Design use: `docs/market_agent_pass.md`.

Scope: official OpenAI web documentation only. No local config or credential files were read.

Labels used below:
- **[DOC]** is stated in the cited page.
- **[SILENT]** means the docs say nothing on it.
- **[INFERENCE]** is my reading of how documented pieces combine. Test before relying on it.

## 0. Key context: the docs moved and the product was renamed

- **[DOC]** Every `developers.openai.com/codex/...` URL now returns a 308 redirect to `learn.chatgpt.com/docs/...`. For example, `/codex/app/automations` redirects to `https://learn.chatgpt.com/docs/automations?surface=app`, and `/codex/noninteractive` redirects to `https://learn.chatgpt.com/docs/non-interactive-mode`. I observed this with HTTP probes on 2026-10-04.
- **[DOC]** "Automations" are now called **Scheduled tasks**. The "Codex desktop app" is documented as the **ChatGPT desktop app**, with "Codex" and "ChatGPT Work" as modes inside it. Source: https://learn.chatgpt.com/docs/automations?surface=app
- **[DOC]** The changelog lists **Codex CLI 0.157.1** (2026-09-26). The latest GitHub release is `rust-v0.160.0` (2026-10-01). Sources: https://learn.chatgpt.com/docs/changelog and https://github.com/openai/codex/releases
- **[DOC]** "ChatGPT agent is no longer available." The help article points users to ChatGPT Work and the cloud browser instead. Source: https://help.openai.com/en/articles/11752874-chatgpt-agent
- **[DOC]** "GPT-5.5 retires from ChatGPT, ChatGPT Work, and Codex on all plans on October 14, 2026." Any scheduled task pinned to GPT-5.5 must be moved to another model. Source: https://learn.chatgpt.com/docs/automations?surface=app

## 1. Scheduled tasks (formerly Automations) in the desktop app

Source for this whole section unless noted: https://learn.chatgpt.com/docs/automations?surface=app

### How tasks are defined
- **[DOC]** You create and manage tasks in the **UI**: the **Scheduled** view in the desktop app sidebar, or on ChatGPT web.
- **[DOC]** You can also ask in a chat: "You can create and update scheduled tasks from a ChatGPT or Codex chat."
- **[DOC]** Skills can create or update scheduled tasks too.
- **[DOC]** "Codex CLI doesn't provide the Scheduled management interface." The IDE extension doesn't either.
- **[SILENT]** The docs describe no user-editable definition file and no import/export format.
- **[DOC]** Tasks can invoke a skill with `$skill-name`. The docs recommend skills as the way to keep tasks maintainable.

### Scheduling granularity
- **[DOC]** Standalone tasks support custom schedule controls. For advanced schedules you can edit an RFC 5545 RRULE, for example `RRULE:FREQ=MONTHLY;BYMONTHDAY=1;BYHOUR=9;BYMINUTE=0`.
- **[DOC]** Tasks scheduled inside a chat support "minute-based intervals for active follow-up loops, or daily and weekly schedules."
- **[INFERENCE]** A weekly RRULE such as `FREQ=WEEKLY;BYDAY=MO;BYHOUR=7;BYMINUTE=0` should work. The docs only show a monthly example.
- **[DOC]** Event triggers (Gmail, Slack, GitHub) are web and mobile only. They aren't available in the desktop app or the CLI.

### When the app is closed or the Mac is asleep
- **[DOC]** "Keep the computer on and the app running when a scheduled task needs local files."
- **[DOC]** "For project-scoped scheduled tasks, keep the machine powered on and the ChatGPT desktop app running. The selected project must still be available on disk."
- **[SILENT]** The docs don't say whether a run that was missed (app closed, Mac asleep) catches up later or is skipped.
- **[INFERENCE]** A local-repo weekly task will not run while the app is quit or the Mac is asleep.
- **[DOC]** There is an experimental `features.prevent_idle_sleep` setting: "Prevent the machine from sleeping while a turn is actively running (experimental; off by default)." It only applies once a turn is running; it doesn't wake the Mac. Source: https://learn.chatgpt.com/docs/config-file/config-reference
- **[DOC]** Web scheduled tasks run in the cloud but "can't work directly in a folder on your computer."

### Local repo or worktree
- **[DOC]** In a Git repo, each task runs either in the local project or "on a new worktree. Both options run in the background."
- **[DOC]** Worktrees isolate the task's changes from unfinished work. Local mode "can change files you are actively editing."
- **[DOC]** Frequent schedules can pile up worktrees. Archive runs you no longer need.
- **[DOC]** The 2026-03-12 changelog entry is the one that added the local-or-worktree choice. Source: https://learn.chatgpt.com/docs/changelog
- **[INFERENCE]** For a JSONL file that must land on `main`, local mode is simpler. Worktree mode leaves the output on a separate checkout that someone has to merge.

### Where results appear
- **[DOC]** "The **Scheduled** view acts as your inbox. Scheduled task runs with findings appear there, and an unread indicator shows when a run needs your attention."
- **[DOC]** Standalone tasks start a new chat for each run. In-chat tasks return to the same chat.

### Sandbox and approvals during unattended runs
- **[DOC]** "Scheduled tasks run unattended and use your default sandbox settings."
- **[DOC]** "Scheduled tasks use `approval_policy = "never"` when your organization policy allows it."
- **[DOC]** What each sandbox mode blocks:
  - **read-only:** tool calls fail "if they require modifying files, accessing network, or working with apps on your computer."
  - **workspace-write:** tool calls fail if they need to modify files outside the workspace, use the network, "or working with apps on your computer." Rules can allowlist specific commands.
  - **full access:** "elevated risk." The agent may change files, run commands and use the network without asking.
- **[INFERENCE]** Because approvals are set to never, nothing can stop to ask you. Two consequences:
  - Any website or app permission must be pre-approved before the run. That means the site allowlist in Settings > Browser or Computer Use, and "Always allow" for any app.
  - Under workspace-write, the phrase "working with apps on your computer" suggests Computer Use would fail.
  - **[SILENT]** The docs don't say explicitly whether the built-in browser or Computer Use can run inside a scheduled task.
- **[DOC]** In the default workspace-write sandbox, `<writable_root>/.git` is protected read-only. Source: https://learn.chatgpt.com/docs/agent-approvals-security
  - **[INFERENCE]** A sandboxed run can write the JSONL file but can't `git commit` unless you add a rule that allows git outside the sandbox, or commit afterwards in a separate step.

## 2. Ways to browse inside Codex

### 2a. Built-in browser (desktop app)
Sources: https://learn.chatgpt.com/docs/browser and https://help.openai.com/en/articles/20001277-using-the-built-in-browser-in-the-chatgpt-desktop-app

- **[DOC]** "Browser isn't available in Codex CLI or the Codex IDE extension."
- **[DOC]** It runs inside the desktop app with its own profile: "separate from your regular browser." Sign-in is supported.
- **[DOC]** It renders JavaScript. Computer Use can "open pages, click, type, inspect rendered state, take screenshots."
- **[DOC]** Site permissions: "ChatGPT asks before it uses a website unless you have already allowed that site." The allowed and blocked lists are in Settings > Browser.
- **[DOC]** It asks for confirmation before sensitive actions: submitting information, purchases, changing permissions, deleting data.
- **[DOC]** It can't automate file uploads.
- **[DOC]** There is an optional Developer mode that gives "full CDP access." It requires explicit approval before each use.

### 2b. Chrome / Edge / Brave / Opera / Vivaldi extension
Source: https://learn.chatgpt.com/docs/chrome-extension

- **[DOC]** It works in your real browser profile: "can read or act on sites where you're already signed in."
- **[DOC]** Site access options when ChatGPT asks: Allow once, Allow for this site, Allow for all sites (marked "Elevated Risk"), or Decline. The allowlist and blocklist are under Settings > Computer Use > Manage.
- **[SILENT]** The page doesn't cover scheduled or background use, CAPTCHAs, or CLI use.

### 2c. Computer Use (macOS and Windows desktop app)
Sources: https://learn.chatgpt.com/docs/computer-use and https://learn.chatgpt.com/use-cases/use-your-computer-with-codex

- **[DOC]** It "can see and operate graphical user interfaces," including browsers, through a Computer Use plugin.
- **[DOC]** On macOS it needs Screen Recording and Accessibility permissions.
- **[DOC]** It asks permission per app. "Always allow" saves that permission for future tasks. It "may also ask for permission before taking sensitive or disruptive actions."
- **[DOC]** On macOS it runs in the background while you use other apps. On Windows it takes over the foreground.
- **[DOC]** Locked use lets it work "after your Mac locks, but only after you enable it."
  - It is scoped to "an active, trusted Computer Use turn."
  - It is framed around starting a task "from a connected device after your Mac's screen has locked."
- **[DOC]** It "can't automate terminal apps or ChatGPT itself, … can't authenticate as an administrator or approve security and privacy permission prompts."
- **[DOC]** "Stay present for account, security, privacy, network, payment, or credential-related settings."
- **[DOC]** "File edits and shell commands still follow … sandbox settings."
- **[SILENT]** The docs don't say whether Computer Use runs inside scheduled tasks. See the inference in section 1.

### 2d. Playwright or Chrome DevTools MCP servers
Source: https://learn.chatgpt.com/docs/extend/mcp?surface=cli

- **[DOC]** "The ChatGPT desktop app, Codex CLI, and IDE extension support MCP servers and share MCP configuration."
- **[DOC]** Playwright ("Control and inspect a browser") and Chrome DevTools are listed as example servers.
- **[DOC]** Both STDIO and Streamable HTTP servers are supported.
- **[DOC]** Config keys: `startup_timeout_sec` (default 10 s), `tool_timeout_sec` (default 60 s), and `default_tools_approval_mode` or per-tool `approval_mode` (auto, prompt, writes, approve).
- **[DOC]** The command network proxy "does not filter … MCP server connections, browser or Computer Use activity." Source: https://learn.chatgpt.com/docs/agent-approvals-security
- **[INFERENCE]**
  - An MCP-driven headless Chromium uses a separate network path from model shell commands, so a sandbox with networking off doesn't stop it.
  - **[SILENT]** The docs don't say whether a STDIO MCP server process runs inside the OS sandbox.
  - Playwright renders JavaScript-heavy sites.

### 2e. Network access: local sandbox vs Codex Cloud
- **[DOC]** Local: "the default workspace-write sandbox mode keeps network access turned off unless you enable it":
  ```toml
  [sandbox_workspace_write]
  network_access = true
  ```
  As a one-off: `-c 'sandbox_workspace_write.network_access=true'`.
  - With `features.network_proxy` turned on, a domain allowlist is enforced.
  - Source: https://learn.chatgpt.com/docs/agent-approvals-security
- **[DOC]** The beta permission profiles have their own setting, `permissions.<name>.network.enabled`. They don't combine with `sandbox_mode`. Source: https://learn.chatgpt.com/docs/permissions
- **[DOC]** Web search defaults to `"cached"`, which is an OpenAI index with no live fetch. `--search` or `web_search="live"` turns on live retrieval. Source: https://learn.chatgpt.com/docs/config-file/config-reference
- **[DOC]** Codex Cloud environments have a per-environment "Allow Codex to access internet" setting with a domain allowlist. The legacy Codex Cloud blocked the agent phase from the internet by default. Sources: https://learn.chatgpt.com/docs/environments/cloud-environments and https://learn.chatgpt.com/docs/cloud/internet-access
- **[DOC]** ChatGPT Work's cloud browser is a separate remote browser. "Can continue in the background, including after you close your computer." Source: https://help.openai.com/en/articles/20001280-using-cloud-browser-in-chatgpt
  - **[INFERENCE]** It can't write into the local repo directly.

### Which options render JavaScript-heavy sites
| Option | Renders JS? | Basis |
|---|---|---|
| Built-in browser | Yes | [DOC] "rendered state" |
| Chrome extension (real browser) | Yes | [INFERENCE] it is your actual browser |
| Computer Use | Yes | [INFERENCE] it drives a real browser |
| Cloud browser | Yes | [INFERENCE] full browser that "click[s] buttons, enter[s] information into forms" |
| Playwright MCP | Yes | [INFERENCE] headless Chromium |
| `curl` from a sandboxed command | No | [INFERENCE] |
| `web_search` tool | No | [INFERENCE] it is a search tool, not a renderer |

## 3. `codex exec` headless, for scheduling with launchd

Sources: https://learn.chatgpt.com/docs/non-interactive-mode and https://learn.chatgpt.com/docs/developer-commands?surface=cli

### Flags
- **[DOC]** Default: "By default, codex exec runs in a read-only sandbox."
- **[DOC]** `--sandbox/-s read-only|workspace-write|danger-full-access`. `--full-auto` is deprecated; use `--sandbox workspace-write` instead.
- **[DOC]** `--dangerously-bypass-approvals-and-sandbox` (alias `--yolo`): "only use inside an isolated runner."
- **[DOC]** Approval policy is set with the global flag `--ask-for-approval never` / `-a never`, or with `approval_policy="never"` in config. The docs say to use `never` "for non-interactive runs."
  - **[SILENT]** The `codex exec` flag table doesn't list `-a`. Passing `-c approval_policy="never"` is the safest way to set it.
- **[DOC]** Network: `-c 'sandbox_workspace_write.network_access=true'`. Optionally add `features.network_proxy` with a domain allowlist.
- **[DOC]** Output flags:
  - `--json` streams JSONL events (`thread.started`, `turn.completed`, `item.*` including MCP tool calls, `error`).
  - `-o/--output-last-message <path>` writes the final message to a file.
  - `--output-schema <path>` constrains the final response to a JSON Schema.
  - The recommendation is to "Pair --json with --output-last-message."
- **[DOC]** Other flags:
  - `-C/--cd <path>`: working directory.
  - `--skip-git-repo-check`.
  - `--ephemeral`.
  - `--ignore-user-config` and `--ignore-rules`.
  - `-c key=value`: repeatable config override.
  - `-m`: model.
  - `exec resume --last`.
  - `codex exec -`: reads the prompt from stdin.
- **[DOC]** `--profile/-p <name>`: "Layer $CODEX_HOME/profile-name.config.toml on top of the base user config."
- **[DOC]** Authentication: `codex exec` "reuses saved CLI authentication by default." The alternative is `CODEX_API_KEY` set inline for just the one invocation.

### MCP under exec
- **[DOC]** MCP servers load under exec. "If you configure an enabled MCP server with `required = true` and it fails to initialize, codex exec exits with an error."
- **[SILENT]** How MCP tool approval prompts behave under `approval_policy=never` isn't spelled out for exec.
  - **[DOC]** The granular policy has an `mcp_elicitations` category. Setting an MCP tool's `approval_mode="approve"` avoids prompts. Source: https://learn.chatgpt.com/docs/config-file/config-reference
- **[INFERENCE]** `codex exec` plus a Playwright MCP server is the only documented headless path that renders JavaScript and can be driven by launchd. The built-in browser, the Chrome extension and Computer Use are desktop-app only.

### launchd
- **[SILENT]** OpenAI's docs don't mention launchd or cron. The non-interactive page lists "scheduled jobs" as a use case for exec.

## 4. User-agent identity and robots.txt

Source for the crawler descriptions: https://developers.openai.com/api/docs/bots (formerly platform.openai.com/docs/bots)

- **[DOC]** GPTBot (training), OAI-SearchBot (search) and OAI-AdsBot are crawlers controlled by robots.txt.
- **[DOC]** "ChatGPT-User" ("certain user actions in ChatGPT and Custom GPTs") "is not used for crawling the web in an automatic fashion. Because these actions are initiated by a user, robots.txt rules may not apply."
  - Its user-agent string is `Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; ChatGPT-User/1.0; +https://openai.com/bot`.
- **[DOC]** The cloud browser (ChatGPT Work, formerly ChatGPT agent/Operator) signs requests using RFC 9421 Web Bot Auth:
  - It sends `Signature`, `Signature-Input`, and `Signature-Agent: "https://chatgpt.com"`.
  - Keys are published at https://chatgpt.com/.well-known/http-message-signatures-directory.
  - CDNs list it as "ChatGPT Agent." Cloudflare identifies it with bot tag `chatgpt-agent`.
  - Source: https://help.openai.com/en/articles/11845367-chatgpt-agent-allowlisting
- **[SILENT]**
  - The docs give no user-agent string for the local built-in browser, the Chrome extension, Computer Use, or Codex CLI.
  - The docs don't say how robots.txt applies to them.
- **[INFERENCE]** The likely identities are:
  - Chrome extension and Computer Use: your normal browser's user agent, cookies and IP.
  - Built-in browser: a Chromium-based user agent from your Mac's IP.
  - Playwright MCP: the user agent of the bundled Playwright browser (often a headless Chrome UA).
  - None of these is documented as carrying ChatGPT-User or Web Bot Auth signatures.
  - **[INFERENCE]** A recurring scripted keyword search sits closer to automated crawling than to the one-off "user-initiated" fetches that the ChatGPT-User text exempts. OpenAI's robots.txt carve-out is about its own ChatGPT-User agent and does not cover these tools.

## 5. Credits and usage

Source: https://learn.chatgpt.com/docs/pricing

- **[DOC]** "ChatGPT Work and Codex share usage." Local messages and cloud chats share one allowance. Plus has 5-hour windows and "Weekly limits may also apply." Pro "currently ha[s] no five-hour limit."
- **[DOC]** Usage depends on "model choice, context, reasoning, tool use, retrieval, and caching." "Limit the number of MCP servers … Every MCP server adds more context."
- **[DOC]** Credits are charged per million tokens. For example, GPT-6 Sol costs 50 credits for input and 250 for output, and GPT-6 Luna costs 2.5 and 12.5.
- **[DOC]** You can buy extra credits on Plus and Pro. Using an API key bills at API rates instead.
- **[DOC]** Computer Use, Chrome control, and Computer Use in the browser are marked "Limited*" (region-limited) on all plans.
- **[SILENT]** There is no separate per-run price for scheduled tasks or Computer Use.
- **[INFERENCE]** Each scheduled run consumes the shared allowance like a normal turn. Screenshot-heavy Computer Use runs will use more tokens.
- **[DOC]** For contrast, the retired ChatGPT agent counted "agent requests that are part of scheduled tasks" against a monthly cap. Source: https://help.openai.com/en/articles/11752874-chatgpt-agent

## 6. Bot challenges and CAPTCHAs

- **[DOC]** Cloud browser:
  - "Some sites block automated browsers or require a CAPTCHA. ChatGPT may not be able to complete a task on those sites."
  - "If ChatGPT is ever blocked for any reason, you can take over its computer."
  - Sources: https://learn.chatgpt.com/docs/browser and https://help.openai.com/en/articles/20001280-using-cloud-browser-in-chatgpt
- **[DOC]** "These restrictions are set by the website, not by ChatGPT … each website ultimately decides whether to allow cloud browser traffic."
  - The suggested fixes are to try another site or open the page in your own browser. Operators can allowlist the signed agent.
  - Source: https://help.openai.com/en/articles/20001280-using-cloud-browser-in-chatgpt
- **[DOC]** Legacy ChatGPT agent paused for login and asked the user to take over the browser. It also ran a "watch mode" that required supervision on certain sites. Source: https://help.openai.com/en/articles/11752874-chatgpt-agent
- **[SILENT]** There is no CAPTCHA guidance for the local built-in browser, the Chrome extension, Computer Use, or Playwright MCP.
- **[INFERENCE]**
  - In an unattended scheduled or exec run with approvals set to never, nobody is there to take over.
  - The task should detect a challenge page, log it as "blocked," and skip that site. It should not try to solve the challenge.
  - Computer Use's guidance to stay present for credential and security flows points the same way.

## Practical takeaways (all [INFERENCE])

1. **Desktop scheduled task, weekly RRULE, local mode, plus the built-in browser or Chrome.**
   - Pros: renders JavaScript, uses a real browser, and results land in the Scheduled inbox.
   - Cons: the Mac must be awake with the app running.
   - It is undocumented whether browser and Computer Use tools work under the task's never-approve sandbox. Pre-allowlist the auction domains and test with a manual "Run now."
   - A `.git` write needs a rule, or commit outside the task.
2. **launchd plus `codex exec` with a Playwright MCP server.**
   - Command: `codex exec -C <repo> -s workspace-write -c approval_policy="never" --json -o last.md` plus a schema.
   - Pros: works without the GUI, with documented flags and JSONL output.
   - Cons: the MCP browser identity and the sandboxing of MCP servers are undocumented, and launchd setup is your own.
3. **ChatGPT Work cloud browser scheduled from the web.**
   - Pros: runs while the Mac is off, and it is a signed, identifiable agent.
   - Cons: it can't write the local repo. It would have to hand results back by another route, such as a GitHub connector.
