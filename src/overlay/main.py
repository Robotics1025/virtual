"""Demo application for AirVoice Overlay Interface."""

import sys
import random
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from .overlay_window import OverlayWindow
from .config import OverlayConfig, Position
from .state_machine import OverlayState



from .voice_input import VoiceInputManager
from .commands import CommandProcessor

class AirVoiceOverlay:
    """Main application for AirVoice Overlay."""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.config = OverlayConfig()
        self.overlay = OverlayWindow(self.config)
        
        # Voice Input Manager
        self.voice_manager = VoiceInputManager()
        self._connect_signals()
        
        # Command Processor
        self.processor = CommandProcessor()
        

        
        # Reset timer (to go back to listening after action)
        self.reset_timer = QTimer()
        self.reset_timer.setSingleShot(True)
        self.reset_timer.timeout.connect(self._return_to_listening)


    def _connect_signals(self):
        """Connect voice manager signals to overlay."""
        self.voice_manager.listening_started.connect(self._on_listening_started)
        self.voice_manager.text_recognized.connect(self._on_text_recognized)
        self.voice_manager.audio_level_changed.connect(self.overlay.update_audio_level)
        self.overlay.key_pressed.connect(self._on_key_pressed)
        # self.voice_manager.error_occurred.connect(print) # Log errors to console

    def _on_listening_started(self):
        """Called when listening begins."""
        self.overlay.start_listening()
        # Visual feedback is now driven by real audio levels via signal

    def _on_text_recognized(self, text: str):
        """Called when text is recognized."""
        # Process command
        action, feedback = self.processor.process(text)
        
        if action == "keypad":
            self.overlay.show_keypad()
            return
        
        # Show action feedback
        self.overlay.show_action(feedback)
        
        # Schedule return to listening
        self.reset_timer.start(3000)

    def _on_key_pressed(self, key: str):
        """Handle keypad key press."""
        if key == 'C': # Close (legacy/shortcut)
            self.overlay.return_to_idle()
            self.reset_timer.start(100)
            return
            
        # Map special keys to pyautogui keys
        special_map = {
            "space": "space",
            "enter": "enter",
            "backspace": "backspace",
            "tab": "tab",
            "capslock": "capslock",
            "shift": "shift", # Toggle or hold? simple press for now
            "ctrl": "ctrl",
            "win": "win",
            "alt": "alt",
            "fn": None # Skip fn for now
        }
        
        if key in special_map:
            mapped = special_map[key]
            if mapped:
                import pyautogui
                pyautogui.press(mapped)
        else:
            # Regular typing
            self.processor.type_text(key)

    def _return_to_listening(self):
        """Return to listening state."""
        self.overlay.start_listening()


    def run(self):
        """Run the application."""
        self.overlay.show()
        
        # Start listening loop
        self.voice_manager.start_listening()
        
        return self.app.exec()


def main():
    """Entry point."""
    program = AirVoiceOverlay()
    sys.exit(program.run())



if __name__ == "__main__":
    main()
