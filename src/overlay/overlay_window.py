"""Main overlay window for AirVoice."""

import sys
from typing import Optional
from PySide6.QtCore import Qt, QTimer, QRectF, Signal
from PySide6.QtGui import QPainter, QColor, QScreen
from PySide6.QtWidgets import QApplication, QWidget

from .state_machine import OverlayState, OverlayStateMachine
from .config import OverlayConfig, AccessibilityMode
from .animations import AnimationController
from .phase_renderer import (
    IdleRenderer, ListeningRenderer, ProcessingRenderer,
    ActionRenderer, GestureRenderer, KeypadRenderer
)


class OverlayWindow(QWidget):
    """Main overlay window - frameless, transparent, always-on-top, click-through."""
    
    state_changed = Signal(OverlayState, OverlayState)
    
    def __init__(self, config: Optional[OverlayConfig] = None):
        super().__init__()
        
        self.config = config or OverlayConfig()
        self.state_machine = OverlayStateMachine()
        self.animation = AnimationController(self)
        
        # Current opacity for rendering
        self._current_opacity = self.config.idle_opacity
        self._target_opacity = self.config.idle_opacity
        
        # Initialize renderers
        self.renderers = {
            OverlayState.IDLE: IdleRenderer(self.config, self.state_machine),
            OverlayState.LISTENING: ListeningRenderer(self.config, self.state_machine),
            OverlayState.PROCESSING: ProcessingRenderer(self.config, self.state_machine),
            OverlayState.ACTION: ActionRenderer(self.config, self.state_machine),
            OverlayState.GESTURE: GestureRenderer(self.config, self.state_machine),
            OverlayState.KEYPAD: KeypadRenderer(self.config, self.state_machine),
        }
        
        # Connect state changes
        self.state_machine.add_listener(self._on_state_changed)
        
        # Setup window
        self._setup_window()
        
        # Update timer (~60fps)
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._on_update)
        self.update_timer.start(16)
        
        # Action toast auto-hide timer
        self.action_timer = QTimer(self)
        self.action_timer.setSingleShot(True)
        self.action_timer.timeout.connect(self._hide_action)
    
    def _setup_window(self):
        """Configure window properties."""
        # Frameless, transparent, always-on-top
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
            # Qt.WindowType.WindowTransparentForInput (Initially set, but we manage it dynamically now)
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        
        # Transparent background
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        # Set size and position
        self._update_geometry()
    
    def _update_geometry(self):
        """Update window size and position."""
        screen = QApplication.primaryScreen()
        if screen:
            screen_geo = screen.geometry()
            
            # Window size
            size = self.config.indicator_size * 4  # Extra space for animations
            self.setFixedSize(size, size)
            
            # Position
            x, y = self.config.get_screen_position(screen_geo.width(), screen_geo.height())
            # Adjust for widget center
            x = x - size // 2 + self.config.indicator_size // 2
            y = y - size // 2 + self.config.indicator_size // 2
            self.move(x, y)
    
    def _on_state_changed(self, old_state: OverlayState, new_state: OverlayState):
        """Handle state transitions."""
        # Emit signal
        self.state_changed.emit(old_state, new_state)
        
        # Check accessibility mode
        if self.config.accessibility_mode == AccessibilityMode.AUDIO_ONLY:
            return
        
        # Determine target opacity
        opacity_map = {
            OverlayState.IDLE: self.config.idle_opacity,
            OverlayState.LISTENING: self.config.listening_opacity,
            OverlayState.PROCESSING: self.config.processing_opacity,
            OverlayState.ACTION: self.config.action_opacity,
            OverlayState.GESTURE: self.config.listening_opacity,
            OverlayState.KEYPAD: self.config.action_opacity,
        }
        
        self._target_opacity = opacity_map.get(new_state, self.config.idle_opacity)
        
        # Start animation
        self.animation.fade_to(self._target_opacity, self.config.fade_duration_ms)
        
        # Handle action auto-hide
        if new_state == OverlayState.ACTION:
            self.action_timer.start(self.config.toast_display_ms)
        
        # Update window size for keypad
        if new_state == OverlayState.KEYPAD:
            self._expand_for_keypad()
        elif old_state == OverlayState.KEYPAD:
            self._update_geometry()
            
        # Update interactive state
        self._update_input_passthrough()
    
    def _expand_for_keypad(self):
        """Expand window to fit keypad (Full Keyboard)."""
        screen = QApplication.primaryScreen()
        if screen:
            screen_geo = screen.geometry()
            # Wider landscape size for full keyboard
            width = 1000
            height = 400 
            self.setFixedSize(width, height)
            
            # Position at bottom center or center-center?
            # Config usually tries to center relative to screen, let's keep it centered
            x = (screen_geo.width() - width) // 2
            y = (screen_geo.height() - height) // 2
            
            # Or if strict config position is needed, we could use that, 
            # but keyboard usually sits better independently or center.
            # Using center for now.
            self.move(x, y)
    
    def _hide_action(self):
        """Auto-hide action and return to idle."""
        if self.state_machine.state == OverlayState.ACTION:
            self.state_machine.set_idle()
    
    def _update_input_passthrough(self):
        """Update window transparency for input based on state."""
        is_keypad = self.state_machine.state == OverlayState.KEYPAD
        
        # We need to toggle the WA_TransparentForMouseEvents attribute
        # and potentially re-show the window for flags to take effect?
        # Actually, WA_TransparentForMouseEvents is cleaner than WindowTransparentForInput flag toggling on some platforms
        
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, not is_keypad)
        
        # Ensure we don't steal focus but can receive clicks
        if is_keypad:
            self.setWindowFlag(Qt.WindowType.WindowTransparentForInput, False)
        else:
            self.setWindowFlag(Qt.WindowType.WindowTransparentForInput, True)
            
        self.show() # Refresh flags

    def mousePressEvent(self, event):
        """Handle mouse clicks for keypad."""
        if self.state_machine.state != OverlayState.KEYPAD:
            super().mousePressEvent(event)
            return

        renderer = self.renderers.get(OverlayState.KEYPAD)
        if renderer and hasattr(renderer, 'hit_test'):
            key = renderer.hit_test(event.position())
            if key:
                self.state_machine.update_keypad(key)
                # Visual feedback
                self.update()
                QTimer.singleShot(150, lambda: self.state_machine.update_keypad(None))
                
                # Handle key logic signal/callback? 
                # Ideally we emit a signal here that Main can listen to logic
                # For now, let's just print or let Main handle it via state change?
                # We need a signal "key_pressed"
                self.key_pressed.emit(key)
    
    # Define signal
    key_pressed = Signal(str)
    
    def _on_update(self):
        """Update animation and repaint."""
        # Update current opacity from animation
        self._current_opacity = self.animation.opacity
        
        # Update renderer-specific animations
        current_renderer = self.renderers.get(self.state_machine.state)
        if hasattr(current_renderer, 'update'):
            current_renderer.update(16)
        
        self.update()
    
    def paintEvent(self, event):
        """Render the overlay."""
        if self.config.accessibility_mode == AccessibilityMode.AUDIO_ONLY:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = QRectF(0, 0, self.width(), self.height())
        
        # Get current renderer
        current_state = self.state_machine.state
        renderer = self.renderers.get(current_state)
        
        # Render minimal mode
        if self.config.accessibility_mode == AccessibilityMode.MINIMAL:
            # Only render idle dot
            self.renderers[OverlayState.IDLE].render(painter, rect, self._current_opacity)
        elif renderer:
            renderer.render(painter, rect, self._current_opacity)
        
        painter.end()
    
    # Public API
    def set_position(self, position):
        """Change overlay position."""
        self.config.position = position
        self._update_geometry()
    
    def set_accessibility_mode(self, mode: AccessibilityMode):
        """Change accessibility mode."""
        self.config.accessibility_mode = mode
        self.update()
    
    def show_action(self, message: str, icon: Optional[str] = None):
        """Show action feedback toast."""
        self.state_machine.set_action(message, icon)
    
    def start_listening(self):
        """Enter listening mode."""
        self.state_machine.set_listening()
    
    def update_audio_level(self, level: float):
        """Update audio visualization level (0-1)."""
        self.state_machine.update_audio_level(level)
    
    def start_processing(self):
        """Enter processing mode."""
        self.state_machine.set_processing()
    
    def show_gesture(self, hover_key: Optional[str] = None):
        """Show gesture overlay."""
        self.state_machine.set_gesture(hover_key=hover_key)
    
    def show_keypad(self, active_key: Optional[str] = None):
        """Show keypad overlay."""
        self.state_machine.set_keypad(active_key)
    
    def update_keypad(self, active_key: Optional[str]):
        """Update active keypad key."""
        self.state_machine.update_keypad(active_key)
    
    def return_to_idle(self):
        """Return to idle state."""
        self.state_machine.set_idle()


def create_overlay(config: Optional[OverlayConfig] = None) -> OverlayWindow:
    """Create and return an overlay window instance."""
    return OverlayWindow(config)
