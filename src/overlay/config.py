"""Configuration for AirVoice Overlay Interface."""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Tuple


class Position(Enum):
    """Overlay position on screen."""
    BOTTOM_RIGHT = auto()
    BOTTOM_LEFT = auto()
    BOTTOM_CENTER = auto()  # Default - center bottom of screen
    TOP_RIGHT = auto()
    TOP_LEFT = auto()
    CENTER = auto()
    FOLLOW_HAND = auto()


class AccessibilityMode(Enum):
    """Accessibility display modes."""
    NORMAL = auto()      # Full overlay
    MINIMAL = auto()     # Tiny indicator only
    AUDIO_ONLY = auto()  # No visuals


@dataclass
class ColorScheme:
    """Color scheme for overlay elements."""
    primary_glow: str = "#00FFFF"      # Soft cyan
    listening: str = "#4A90D9"          # Blue
    processing: str = "#9B59B6"         # Purple
    action_bg: str = "rgba(255,255,255,0.15)"
    action_text: str = "#FFFFFF"
    gesture_highlight: str = "#2ECC71"  # Green
    

@dataclass
class OverlayConfig:
    """User configuration for the overlay."""
    position: Position = Position.CENTER  # True center of screen
    accessibility_mode: AccessibilityMode = AccessibilityMode.NORMAL
    colors: ColorScheme = field(default_factory=ColorScheme)
    
    # Opacity settings - higher for better visibility
    idle_opacity: float = 0.4
    listening_opacity: float = 0.85
    processing_opacity: float = 0.9
    action_opacity: float = 0.95
    
    # Size settings
    indicator_size: int = 80
    toast_width: int = 300
    keypad_key_size: int = 60
    
    # Animation settings
    fade_duration_ms: int = 300
    breathing_duration_ms: int = 3000
    toast_display_ms: int = 2000
    
    # Window settings
    margin: int = 30
    
    def get_screen_position(self, screen_width: int, screen_height: int) -> Tuple[int, int]:
        """Calculate overlay position based on screen size."""
        margin = self.margin
        size = self.indicator_size
        
        positions = {
            Position.BOTTOM_RIGHT: (screen_width - size - margin, screen_height - size - margin),
            Position.BOTTOM_LEFT: (margin, screen_height - size - margin),
            Position.BOTTOM_CENTER: ((screen_width - size) // 2, screen_height - size - margin),
            Position.TOP_RIGHT: (screen_width - size - margin, margin),
            Position.TOP_LEFT: (margin, margin),
            Position.CENTER: ((screen_width - size) // 2, (screen_height - size) // 2),
            Position.FOLLOW_HAND: (screen_width - size - margin, screen_height - size - margin),
        }
        return positions.get(self.position, positions[Position.BOTTOM_RIGHT])
