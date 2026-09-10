# Browser Testing Guidelines

The developer prefers using **Vivaldi** instead of Chrome/Chromium for frontend and browser-based testing.

## Guidelines for AI Agents

1. **Do Not Use AI Browser Subagents**: Avoid invoking the default client browser subagent (`browser_subagent`), as it relies on a closed Chromium/Playwright sandbox that cannot be customized to launch Vivaldi and will fail in this environment.
2. **Playwright Executable Path**: When writing or modifying Playwright test scripts, explicitly configure the executable path to launch Vivaldi:
   - Primary Linux path: `/usr/bin/vivaldi` or `/usr/bin/vivaldi-stable`
3. **Manual Verification Fallback**: Prefer asking the user to manually verify changes in their browser (Vivaldi) or perform validation via API/terminal (`curl` or Node scripts).
