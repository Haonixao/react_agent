# ReAct agent

**Local Autonomous Agent for Web AI Chats**

A powerful local automation tool that turns your Web AI chat into a fully autonomous agent with direct access to your computer's terminal and file system.

## What is this?

This project creates a **closed-loop ReAct agent** that runs locally on your Windows machine. It connects to Chrome via the Chrome DevTools Protocol, monitors the chat, parses model tool calls, executes them on your system, and automatically pastes the results back into the chat.

It effectively gives the AI persistent, real-world execution capabilities.

## Reasons

- No need to install heavy programs or plugins. You just have a small python script that runs in the terminal.
- Perhaps for some, like me, it is convenient when your web ai chat (which is already open in the browser tab) can have the capabilities of an ai agent without overloading your idea|code editor.
- You have one interface and one subscription for simple quick web queries and for editing files|executing commands on your local system.
- You don't have complicated api key settings, binding to specific API providers, and AI programs. Any chat in the browser tab automatically gets the opportunity to interact with your system as an agent.

---

**BUT. There are disadvantages compared to large, well-honed tools**

- The tool is very young, minimalistic, and not described as a classic tool for ai. 
- ai can sometimes use it incorrectly. 
- it can be slow. 
- it can be inconvenient (because during the execution of operations, the browser tab must be in focus and your clipboard is used to transfer content).

---

**Nevertheless, I find it quite convenient for myself because ai often just reads|edits my files, executes some commands|scripts. At the same time, there is absolutely no heavy agent software on my PC that overloads the system.**

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
   pip install websockets; choco install universal-ctags -y
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

##  My first message in chat:

```
Hi. Help me test this. ..."send in chat content of agent.md via text or file"...
First, just tell me if you understand how this tool works, and I'll tell you what we're doing next.
```

I know it looks weird, but sometimes it's hard to get a model to use these tools. 
- Model thinks you're trying to hack her with this prompt. 
- Or model thinks that in fact these tools are just an illusion, and she misleads the user by executing fake commands.
- Or model just refuses to use your tools and wants to use only her own.

Therefore, some particularly strict models sometimes have to explain that this is not fake, not hack and her own tools do not allow it to interact with the user's system.

## Safety Notes

- The agent only executes commands you explicitly request through tool calls
- Keep the Chrome window active and visible when agent doing task
- Use with trusted AI models only

---
**Disclaimer**: This project is in the early MVP stage. You are fully responsible for the commands you allow the agent to execute and any consequences that may result.
