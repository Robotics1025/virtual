import os
import sys
import subprocess
import webbrowser
import pyautogui
import time
from typing import Tuple

class CommandProcessor:
    """Processes recognized text and executes system commands."""
    
    def __init__(self):
        # Common app mappings (lowercase -> executable/command)
        self.app_map = {
            "vscode": "code",
            "visual studio code": "code",
            "notepad": "notepad",
            "calculator": "calc",
            "chrome": "chrome",
            "edge": "msedge",
            "explorer": "explorer",
            "cmd": "cmd",
            "terminal": "wt",
            "settings": "start ms-settings:",
            "whatsapp": "whatsapp:",  # Windows protocol handler
            "spotify": "spotify:",
        }

    def process(self, text: str) -> Tuple[str, str]:
        """
        Process the interpreted text.
        Returns: (action_description, status_message)
        """
        text = text.lower().strip()
        
        # 1. Open Applications
        if text.startswith("open "):
            app_name = text[5:].strip()
            return self._open_app(app_name)
            
        # 2. Web Search
        elif text.startswith("search ") or text.startswith("google "):
            query = text.replace("search ", "", 1).replace("google ", "", 1).strip()
            return self._web_search(query)
            
        # 3. Typing / Coding
        elif text.startswith("type ") or text.startswith("write "):
            content = text.replace("type ", "", 1).replace("write ", "", 1)
            return self.type_text(content)
            
        # 4. Keypad
        elif "keypad" in text:
            return "keypad", "Opening Keypad..."
            
        # Default: Just return what was said (maybe user just wants to see it)
        # OR: treat as typing if it looks like code?
        # For now, let's just log it.
        return "recognized", f"Heard: {text}"

    def _open_app(self, app_name: str) -> Tuple[str, str]:
        """Attempt to open an application."""
        # Check explicit map first
        if app_name in self.app_map:
            cmd = self.app_map[app_name]
            try:
                # shell=True allows running commands like "start ms-settings:" or protocol handlers
                subprocess.Popen(cmd, shell=True)
                return "opened", f"Opening {app_name}..."
            except Exception as e:
                return "error", f"Failed to open {app_name}"
        
        # Try generic start command (Windows key + run logic simulation)
        try:
            # os.startfile is Windows only
            # It can often open "word", "excel" if they are in path or registry
            pyautogui.press('win')
            time.sleep(0.2)
            pyautogui.write(app_name)
            time.sleep(0.5)
            pyautogui.press('enter')
            return "opened", f"Searching & Opening {app_name}..."
        except Exception as e:
            return "error", f"Could not find {app_name}"

    def _web_search(self, query: str) -> Tuple[str, str]:
        """Perform a Google search."""
        url = f"https://www.google.com/search?q={query}"
        webbrowser.open(url)
        return "searched", f"Searching: {query}"

    def type_text(self, text: str) -> Tuple[str, str]:
        """Type text into the active window."""
        # Small delay to ensure focus is correct (though voice overlay shouldn't steal focus)
        # pyautogui.write types distinct characters.
        pyautogui.write(text, interval=0.01)
        return "typed", f"Typed: {text}"
