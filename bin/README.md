# Launchers

## Incantation Bowl Index.app

Double-click it, or drag it to the Dock. It opens the private research console at
`http://127.0.0.1:8765` in your browser.

- If the console is already running it just opens the browser — clicking twice
  never starts a second copy.
- If it is not running it starts it in the background and waits for it, then opens
  the browser. No Terminal window appears.
- The console reads the working database live, so what it shows is always current.
  There is nothing to rebuild first.
- It binds to localhost only and refuses non-local addresses. Never expose it.

The server keeps running after you close the browser; click the app again to
return to it. To stop it, run `bin/stop-console.command` or quit the `python`
process.

Logs: `data/private/console.log`. Set `IBI_PORT` to use a different port.

**If it fails to start** it shows a dialog explaining why — usually a missing
`.venv`, which is fixed once with:

```sh
python3 -m venv .venv && .venv/bin/python -m pip install -e .
```
