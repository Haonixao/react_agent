import asyncio
import json
import re
import sys
import websockets
import subprocess
import time
import http.client
import os

# Настройка окружения для корректной работы UTF-8
os.environ["PYTHONIOENCODING"] = "utf-8"

def get_dynamic_page_id():
    """Автоматически находит ID первой подходящей страницы через HTTP API Chrome"""
    try:
        conn = http.client.HTTPConnection("localhost", 9222)
        conn.request("GET", "/json")
        response = conn.getresponse()
        if response.status == 200:
            data = json.loads(response.read())
            for item in data:
                if item.get('type') == 'page' and 'url' in item:
                    print(f"[*] Found page: {item.get('title')} (ID: {item.get('id')})")
                    return item.get('id')
        return None
    except Exception as e:
        print(f"Error fetching page ID: {e}")
        return None

async def get_page_text(websocket):
    """Возвращает весь текст страницы"""
    await websocket.send(json.dumps({
        'id': 1,
        'method': 'Runtime.evaluate',
        'params': {'expression': 'document.body.innerText', 'returnByValue': True}
    }))
    response = await websocket.recv()
    return json.loads(response).get('result', {}).get('result', {}).get('value', '')

async def find_input_selector(websocket):
    """Ищет маркер на странице. Если находит - возвращает новый селектор и очищает поле."""
    js_find = """
    (function() {
        const marker = "[[INPUT_AREA]]";
        const potentials = document.querySelectorAll('textarea, input, [contenteditable="true"]');
        let target = null;
        for (let el of potentials) {
            if ((el.value || el.innerText || "").includes(marker)) { target = el; break; }
        }
        if (!target) return null;

        const getPath = (el) => {
            if (el.id) return '#' + el.id;
            const path = [];
            while (el && el.nodeType === Node.ELEMENT_NODE) {
                let selector = el.nodeName.toLowerCase();
                let sib = el, nth = 1;
                while (sib = sib.previousElementSibling) {
                    if (sib.nodeName.toLowerCase() == selector) nth++;
                }
                if (nth != 1) selector += ":nth-of-type(" + nth + ")";
                path.unshift(selector);
                el = el.parentNode;
            }
            return path.join(" > ");
        };
        const selector = getPath(target);

        target.focus();

        // 1. Выделяем всё (Ctrl+A)
        target.dispatchEvent(new KeyboardEvent('keydown', {
            key: 'a', code: 'KeyA', ctrlKey: true, bubbles: true
        }));

        // 2. Удаляем (Backspace)
        target.dispatchEvent(new KeyboardEvent('keydown', {
            key: 'Backspace', code: 'Backspace', bubbles: true
        }));

        if (target.isContentEditable) {
            const range = document.createRange();
            range.selectNodeContents(target);
            const sel = window.getSelection();
            sel.removeAllRanges();
            sel.addRange(range);
        } else {
            target.select();
        }

        document.execCommand('insertText', false, '');
        target.dispatchEvent(new Event('input', { bubbles: true }));
        target.dispatchEvent(new Event('change', { bubbles: true }));

        return selector;
    })()
    """
    await websocket.send(json.dumps({
        'id': 10,
        'method': 'Runtime.evaluate',
        'params': {'expression': js_find, 'returnByValue': True}
    }))
    response = await websocket.recv()
    return json.loads(response).get('result', {}).get('result', {}).get('value')

def system_send_enter():
    """Отправляет системное нажатие Enter через PowerShell"""
    try:
        # Небольшая задержка, чтобы браузер успел обработать фокус
        time.sleep(0.2)
        cmd = "$wshell = New-Object -ComObject WScript.Shell; $wshell.SendKeys('{ENTER}')"
        subprocess.run(["pwsh", "-NoProfile", "-Command", cmd], capture_output=True)
        return True
    except Exception as e:
        print(f"System Enter Error: {e}")
        return False

async def send_reply(websocket, text, selector):
    import base64
    formatted_text = "```\n" + text + "\n```"
    """Фокусирует поле через JS и вставляет текст через буфер обмена Windows"""
    js_focus = f"""
    (function() {{
        let target = document.querySelector({json.dumps(selector)});

        if (!target) {{
            const potentials = Array.from(document.querySelectorAll('textarea, input, [contenteditable="true"]'));
            const chatFields = potentials.filter(el => {{
                const rect = el.getBoundingClientRect();
                if (rect.width < 150 || rect.height < 30) return false;
                const attrs = (el.id + el.className + (el.placeholder || "") + (el.getAttribute('aria-label') || "")).toLowerCase();
                return !attrs.includes('search') && !attrs.includes('find');
            }});
            target = chatFields[0] || potentials[0];
        }}

        if (!target) return false;

        target.focus();
        return true;
    }})()
    """
    await websocket.send(json.dumps({
        'id': 3,
        'method': 'Runtime.evaluate',
        'params': {'expression': js_focus, 'returnByValue': True}
    }))
    await websocket.recv()

    try:
        b64_text = base64.b64encode(formatted_text.encode('utf-8')).decode('utf-8')
        ps_cmd = f"$text = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String('{b64_text}')); Set-Clipboard -Value $text; $wshell = New-Object -ComObject WScript.Shell; $wshell.SendKeys('^{{V}}');"
        subprocess.run(["pwsh", "-NoProfile", "-Command", ps_cmd], capture_output=True)
        time.sleep(0.1)
    except Exception as e:
        formatted_text = f"Clipboard Error: {e}\n"
        b64_text = base64.b64encode(formatted_text.encode('utf-8')).decode('utf-8')
        ps_cmd = f"$text = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String('{b64_text}')); Set-Clipboard -Value $text; $wshell = New-Object -ComObject WScript.Shell; $wshell.SendKeys('^{{V}}');"
        subprocess.run(["pwsh", "-NoProfile", "-Command", ps_cmd], capture_output=True)
        time.sleep(0.1)

def execute_command(cmd):
    print(f"  > Executing Terminal: {cmd}")
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        prefix = (
            "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
            "chcp 65001 > $null; "
            f"Set-Location '{script_dir}'; "
        )

        full_cmd = prefix + cmd

        result = subprocess.run(
            ["pwsh", "-NoProfile", "-Command", full_cmd],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60
        )

        output = result.stdout if result.stdout else ""
        if result.stderr:
            output += "\nError:\n" + result.stderr

        return output.strip()

    except Exception as e:
        return f"Execution Error: {str(e)}"

patched_files = {}  # path -> True (для защиты от двойного патча)

read_counter = 0

def execute_file_tool(content):
    print(" > Executing File Tool...")
    global read_counter

    try:
        content_stripped = content.strip()
        data = {}

        # 1. Пробуем JSON
        if content_stripped.startswith("{"):
            try:
                data = json.loads(content_stripped)
            except Exception as e:
                print(f" [!] JSON parse error: {e}")

        # 2. Если не JSON или пустой, пробуем YAML-style
        if not data:
            lines = content_stripped.splitlines()
            in_new_text = False
            in_old_text = False
            new_text_lines = []
            old_text_lines = []
            for line in lines:
                if in_old_text:
                    # Многострочный old_text — до явного начала new_text: |
                    if line.strip() == "new_text: |":
                        data["old_text"] = "\n".join(old_text_lines)
                        in_old_text = False
                        in_new_text = True
                        continue

                    old_text_lines.append(line)
                    continue
                if in_new_text:
                    new_text_lines.append(line)
                    continue
                if ":" not in line:
                    continue
                key, val = line.split(":", 1)
                key, val = key.strip().lower(), val.strip()
                if key in ["read", "patch", "symbols"]:
                    data["action"] = key
                    data["path"] = val.strip('"\'')
                elif key == "path":
                    data["path"] = val.strip('"\'')
                elif key in ["start", "end"]:
                    data[key] = int(val)
                elif key == "replace_all":
                    data["replace_all"] = val.lower() in ["true", "1", "yes"]
                elif key == "old_text":
                    if val == "|":
                        in_old_text = True
                        old_text_lines = []
                        if "action" not in data:
                            data["action"] = "patch"
                    else:
                        return "Error: incorrect patch format. Separator '|' expected"
                elif key == "new_text":
                    if val == "|":
                        in_new_text = True
                        if "action" not in data:
                            data["action"] = "patch"
                    else:
                        return "Error: incorrect patch format. Separator '|' expected"
            if in_old_text:
                data["old_text"] = "\n".join(old_text_lines)
            if in_new_text:
                data["new_text"] = "\n".join(new_text_lines)

        if not data:
            return "Error: Could not parse file tool parameters."

        action = data.get("action")
        path = data.get("path")

        # === Защита от двойного патча (только для start-end режима) ===
        if action == "patch" and data.get("old_text") is None:
            if path in patched_files:
                return f"Error: Double patch detected for {path} without read/symbols in between. This can lead to incorrect changes. Do read and then patch again"
            patched_files[path] = True
        elif action in ["read", "symbols"]:
            if path in patched_files:
                del patched_files[path]
            if action == "read":
                read_counter += 1

        script_dir = os.path.dirname(os.path.abspath(__file__))
        filetool_path = os.path.join(script_dir, "filetool.py")

        process = subprocess.Popen(
            [sys.executable, filetool_path],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8"
        )

        stdout, stderr = process.communicate(input=json.dumps(data))
        output = stdout.strip()
        if stderr:
            output += "\nError:\n" + stderr

        print(f"    [+] File Tool Output: {output[:50]}...")

        if read_counter > 10:
            read_counter = 0
        if read_counter == 1:
            output = "Note: \n*don't forget use read symbols mode to more practical answers\n* don't forget that patch by line range mode useful when you don't want to duplicate large amounts of code in old_text and in your context" + output

        return output

    except Exception as e:
        return f"File Tool Error: {str(e)}"


async def main_loop():
    page_id = get_dynamic_page_id()
    if not page_id:
        print("Error: Could not find page. Check if Chrome is open with --remote-debugging-port=9222")
        return

    uri = f'ws://localhost:9222/devtools/page/{page_id}'
    last_processed_msgid = None

    try:
        async with websockets.connect(uri) as websocket:
            print(f"--- MSGID-based Agent Executor Started (Page: {page_id}) ---")
            print("[*] Monitoring for messages and [[INPUT_AREA]] for calibration...")

            input_selector = None
            last_processed_msgid = None
            agent_end_wait_couner = 0

            while True:
                # 1. Постоянно ищем маркер для калибровки/перекалибровки
                new_selector = await find_input_selector(websocket)
                if new_selector:
                    input_selector = new_selector
                    print(f"\n[*] Input selector updated: {input_selector}")

                # 2. Если селектор еще ни разу не был найден, просто ждем
                if not input_selector:
                    await asyncio.sleep(1)
                    continue

                full_text = await get_page_text(websocket)

                # Ищем последнее сообщение агента
                if "[[AGENT_START]]" in full_text:
                    # Извлекаем все после последнего START
                    parts = full_text.split("[[AGENT_START]]")
                    last_part = parts[-1]

                    # ВАЖНО: Ждем завершения сообщения (AGENT_END)
                    if "[[AGENT_END]]" not in last_part:
                        if agent_end_wait_couner > 60:
                            error_text = (
                                    f"Error: last [[AGENT_START]] was more then {agent_end_wait_couner} seconds ago but [[AGENT_END]] was not created."
                                )
                            print(f"\n[!] {error_text}")
                        # Сообщение еще печатается, ждем
                        await asyncio.sleep(1)
                        agent_end_wait_couner += 1
                        continue
                    else:
                        agent_end_wait_couner = 0

                    # Теперь у нас есть полное сообщение между START и END
                    last_msg = last_part.split("[[AGENT_END]]")[0]

                    # Извлекаем MSGID (более гибко)
                    msgid_match = re.search(r"MSGID:?\s*([a-zA-Z0-9_-]+)", last_msg, re.IGNORECASE)
                    if msgid_match:
                        current_msgid = msgid_match.group(1)

                        # === Извлекаем предпоследний MSGID ===
                        pr_msgid = None
                        if len(parts) >= 2:  # значит есть как минимум два блока START
                            prev_part = parts[-2]

                            # Проверяем, что предпоследний блок тоже завершён
                            if "[[AGENT_END]]" in prev_part:
                                prev_msg = prev_part.split("[[AGENT_END]]")[0]
                                pr_match = re.search(r"MSGID:?\s*([a-zA-Z0-9_-]+)", prev_msg, re.IGNORECASE)
                                if pr_match:
                                    pr_msgid = pr_match.group(1)

                        if current_msgid != last_processed_msgid:
                            print(f"\n[!] New message detected (MSGID: {current_msgid})")

                            if pr_msgid is not None and last_processed_msgid is not None and pr_msgid != last_processed_msgid:
                                error_text = (
                                    "Error: Multiple [[AGENT_START]] / [[AGENT_END]] blocks were sent.\n"
                                    f"Previous unprocessed MSGID: {pr_msgid}\n"
                                    "Only one [[AGENT_START]] ... [[AGENT_END]] block per message is allowed.\n"
                                    "Please group all tool calls inside a single block and try again."
                                )
                                await send_reply(websocket, error_text, input_selector)
                                system_send_enter()
                                last_processed_msgid = current_msgid
                                await asyncio.sleep(2)
                                continue

                            # Глубокая очистка и нормализация текста
                            # 1. Удаляем невидимые Unicode-разделители
                            clean_msg = re.sub(r'[\u200b-\u200d\ufeff]', '', last_msg)

                            # Ищем TOOL CALLS (TERMINAL)
                            terminal_pattern = r'\[+[^\]]*TOOL_START\s*:\s*TERMINAL[^\]]*\]+(.*?)\[+[^\]]*TOOL_END\s*:\s*TERMINAL[^\]]*\]+'
                            terminal_calls = re.findall(terminal_pattern, clean_msg, re.DOTALL | re.IGNORECASE)

                            # Ищем TOOL CALLS (FILE)
                            file_pattern = r'\[+[^\]]*TOOL_START\s*:\s*FILE[^\]]*\]+(.*?)\[+[^\]]*TOOL_END\s*:\s*FILE[^\]]*\]+'
                            file_calls = re.findall(file_pattern, clean_msg, re.DOTALL | re.IGNORECASE)

                            if terminal_calls or file_calls:
                                print(f"  > Found {len(terminal_calls)} terminal and {len(file_calls)} file tool(s).")
                                final_reply = []

                                for content in file_calls:
                                    output = execute_file_tool(content)
                                    final_reply.append(f"[[TOOL_START:FILE]]\n{output}\n[[TOOL_END:FILE]]")

                                for cmd_raw in terminal_calls:
                                    cmd = cmd_raw.strip()
                                    cmd = re.sub(r'```[a-zA-Z]*\n?', '', cmd)
                                    cmd = cmd.replace('```', '').strip()
                                    if not cmd: 
                                        continue
                                    output = execute_command(cmd)
                                    final_reply.append(f"[[TOOL_START:TERMINAL]]\nCommand: {cmd}\n{output}\n[[TOOL_END:TERMINAL]]")

                                await send_reply(websocket, "\n\n".join(final_reply), input_selector)
                                await asyncio.sleep(1)
                                await send_reply(websocket, "".join("[[Result complete]]"), input_selector)
                                system_send_enter()
                                print("  > Response sent. Waiting for agent's next move...")

                                last_processed_msgid = current_msgid
                                await asyncio.sleep(1)
                            else:
                                print(f"  > No tools found in MSGID {current_msgid}. Marking as processed.")
                                last_processed_msgid = current_msgid
                        else:
                            # Тот же ID, ничего не делаем
                            pass
                    else:
                        # Сообщение есть, но MSGID еще не написан или отсутствует
                        print("\r[*] Waiting for MSGID in last message...", end="")

                await asyncio.sleep(1)

    except Exception as e:
        print(f"\nPipeline Error: {e}")
        print("Attempting to reconnect in 5 seconds...")
        await asyncio.sleep(5)
        await main_loop()

if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        print("\n[!] Shutdown requested by user. Exiting...")
        sys.exit(0)
