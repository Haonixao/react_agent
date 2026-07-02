# ReAct agent

**Local Autonomous Agent for Web AI Chats**

A powerful local automation tool that turns your Web AI chat into a fully autonomous agent with direct access to your computer's terminal and file system.

## What is this?

This project creates a **closed-loop ReAct agent** that runs locally on your Windows machine. It connects to Chrome via the Chrome DevTools Protocol, monitors the chat, parses your tool calls, executes them on your system, and automatically pastes the results back into the chat.

It effectively gives the AI persistent, real-world execution capabilities.

## Features

- **Terminal Execution** — Run any PowerShell commands with full output capture
- **File Operations** — Safe read/write/patch any files on your system
- **Autonomous Loop** — Continuous monitoring and reaction to new messages
- **Smart Input Detection** — Automatic calibration of the chat input field
- **UTF-8 Support** — Full Unicode compatibility
- **Chrome Integration** — Works directly with an open Chrome instance

## Web AI chats tested

- **grok.com**
- **work.trae.ai**
- **perplexity.ai**
- **app.kilo.ai**
- **duck.ai**
- **gemini.google.com**
- **chat.deepseek.com**
- **chat.qwen.ai**
- **claude.ai**
- **chatgpt.com**
- **alice.yandex.ru**
- **Most likely, it can work on many others without modifications**

## Files

| File                | Purpose                                                 |
| ------------------- | ------------------------------------------------------- |
| `agent_executor.py` | Main autonomous loop (core)                             |
| `filetool.py`       | Safe file read/patch operations                         |
| `agent.md`          | Communication protocol specification (Send it to model) |
| `get_sys_info.py`   | System environment & hardware diagnostic tool           |
| `README.md`         | This documentation                                      |

## Quick Start

1. **Launch Chrome with debugging enabled:**
   ```powershell
   cd "C:\Program Files\Google\Chrome\Application"
   .\chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\Users\user\react_agent\chrome-data"
   ```

2. **Install dependencies:**
   ```powershell
   pip install websockets
   ```

3. **Run the agent:**
   ```powershell
   cd "C:\Users\user\react_agent"
   python agent_executor.py
   ```

4. **Calibrate input field:**
   - Type `[[INPUT_AREA]]` into the chat input box
   - The agent will detect it, remember the field, and clear it

The agent is now ready and will automatically respond to properly formatted tool calls.

## Communication Protocol

All agent responses must follow this structure:

```markdown
[[AGENT_START]]
MSGID: unique_identifier
Your thinking and response...

[[TOOL_START:TERMINAL]]
your powershell command
[[TOOL_END:TERMINAL]]

[[TOOL_START:FILE]]
read: C:\path\to\file
[[TOOL_END:FILE]]
[[AGENT_END]]
```

## Safety Notes

- The agent only executes commands you explicitly request through tool calls
- Keep the Chrome window active and visible when agent doing task
- Use with trusted AI models only

---
**Disclaimer**: This project is in the early MVP stage. You are fully responsible for the commands you allow the agent to execute and any consequences that may result.
