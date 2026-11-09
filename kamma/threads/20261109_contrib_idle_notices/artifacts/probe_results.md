# Phase 1 probe results (2026-11-09)

Probe app: throwaway Flet 1.0.1 app in the session scratchpad, mounted with `FLET_WEB_APP_PATH=probe`, port 8650, driven by headless Chromium through `playwright-cli`.

| Check | Result | Evidence |
|---|---|---|
| 1.1 probe serves | PASS | `curl` on `/probe/` printed 200 |
| 1.2 typing reaches a wrapper | PASS | 5 keys typed one by one gave 5 `dispatch_event` entries (`keyboard_event` on the page) and 5 `apply_patch` entries (`value` on the text field). The click gave one `dispatch_event` (`click`). Typing uses both paths. |
| 1.3 dialog and banner from a daemon thread | PASS | `page.run_task` from a daemon thread showed a modal `AlertDialog` and an `ft.Banner`; a later text change plus `page.update()` changed the banner text ("14 minutes"). Screenshots: `probe_dialog.png`, `probe_banner.png`. Opening or changing them added **no** wrapper entry. |
| 1.4 `launch_url("_dpd/target.html", web_only_window_name="_self")` | PASS (Chromium and Firefox) | Chromium: tab URL became `http://127.0.0.1:8650/probe/_dpd/target.html`, no popup block. Firefox 158 (system build, run by hand by the owner, because the test tool cannot drive it): the tab showed "target page", no popup block. Firefox was only checked for this navigation, not for typing. |
| 1.5 navigate then exit 3 s later | PASS | Tab landed on `target.html`; process gone; exit code 0 (`rc` file). |
| 1.6 `kill -9`, restart within 10 s, watch 60 s | INFO | The open tab reloaded and built a new session in the new process by itself ("page connected" in the new log). A retired tab that was not navigated would wake the editor on its own. The design navigates every held page first, so it does not depend on this. |

## Decisions

- `UI_ECHO_SECONDS` is **not needed**: showing and changing a dialog or banner produced no inbound message.
- Extra finding: a page that has left (tab navigated away or closed) keeps its session, but `page.session.connection` is `None`. `page.run_task` on it raises `AttributeError: 'NoneType' object has no attribute 'loop'`, not `RuntimeError`. Phase 3 must call `run_task` only on connected pages and catch every `Exception` around it. The plan's `_is_connected` and `try/except Exception` already cover this.
- Extra finding: navigating the tab sends `app_lifecycle_state_change` and `disconnect` events to `dispatch_event`. Tab hide or focus changes are likely to send the same event, so a background tab may count as activity. Phase 3.5 must check whether a hidden tab keeps the editor awake.
