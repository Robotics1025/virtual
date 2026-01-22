"""State machine for overlay phases."""

from enum import Enum, auto
from typing import Callable, Optional, List
from dataclasses import dataclass, field


class OverlayState(Enum):
    """Overlay display states/phases."""
    IDLE = auto()
    LISTENING = auto()
    PROCESSING = auto()
    ACTION = auto()
    GESTURE = auto()
    KEYPAD = auto()


@dataclass
class ActionData:
    """Data for action phase."""
    message: str = ""
    icon: Optional[str] = None


@dataclass
class GestureData:
    """Data for gesture phase."""
    hand_landmarks: List = field(default_factory=list)
    active_finger: Optional[int] = None
    hover_key: Optional[str] = None


@dataclass
class KeyData:
    """Data for a single key."""
    label: str
    code: str  # Value to send
    width: float = 1.0  # Width multiplier (1.0 = standard key)
    is_action: bool = False

@dataclass
class KeypadData:
    """Data for keypad phase."""
    active_key: Optional[str] = None
    # 5-row laptop layout
    rows: List[List[KeyData]] = field(default_factory=lambda: [
        # Row 1: Numbers
        [KeyData(k, k) for k in "`1234567890-="] + [KeyData("Back", "backspace", 2.0, True)],
        # Row 2: QWERTY
        [KeyData("Tab", "tab", 1.5, True)] + [KeyData(k, k) for k in "mwertyuiop[]\\"],
        # Row 3: ASDF (Fixed 'm' typo in row 2 to 'q' below)
        # Wait, 'mwertyuiop' -> 'qwertyuiop'
        # Correcting Row 2 manually
    ])

    def __post_init__(self):
        # Initialize full layout if rows is empty (default factory above is complex to write inline perfectly)
        if not self.rows:
            self._init_layout()
            
    def _init_layout(self):
        self.rows = [
            # Row 1
            [KeyData(c, c) for c in "`1234567890-="] + [KeyData("⌫", "backspace", 2.0, True)],
            # Row 2
            [KeyData("Tab", "tab", 1.5, True)] + [KeyData(c, c) for c in "qwertyuiop[]\\"],
            # Row 3
            [KeyData("Caps", "capslock", 1.8, True)] + [KeyData(c, c) for c in "asdfghjkl;'"] + [KeyData("Enter", "enter", 2.2, True)],
            # Row 4
            [KeyData("Shift", "shift", 2.3, True)] + [KeyData(c, c) for c in "zxcvbnm,./"] + [KeyData("Shift", "shift", 2.3, True)],
            # Row 5
            [KeyData("Ctrl", "ctrl", 1.5, True), KeyData("Win", "win", 1.5, True), KeyData("Alt", "alt", 1.5, True), 
             KeyData("SPACE", "space", 6.0), 
             KeyData("Alt", "alt", 1.5, True), KeyData("Fn", "fn", 1.5, True), KeyData("Ctrl", "ctrl", 1.5, True)]
        ]


class OverlayStateMachine:
    """Manages overlay state transitions."""
    
    def __init__(self):
        self._state = OverlayState.IDLE
        self._previous_state = OverlayState.IDLE
        self._listeners: List[Callable[[OverlayState, OverlayState], None]] = []
        
        # Phase-specific data
        self.action_data = ActionData()
        self.gesture_data = GestureData()
        self.keypad_data = KeypadData()
        self.audio_level: float = 0.0
    
    @property
    def state(self) -> OverlayState:
        """Current overlay state."""
        return self._state
    
    @property
    def previous_state(self) -> OverlayState:
        """Previous overlay state."""
        return self._previous_state
    
    def add_listener(self, callback: Callable[[OverlayState, OverlayState], None]):
        """Add state change listener. Callback receives (old_state, new_state)."""
        self._listeners.append(callback)
    
    def remove_listener(self, callback: Callable):
        """Remove state change listener."""
        if callback in self._listeners:
            self._listeners.remove(callback)
    
    def _notify_listeners(self, old_state: OverlayState, new_state: OverlayState):
        """Notify all listeners of state change."""
        for listener in self._listeners:
            try:
                listener(old_state, new_state)
            except Exception as e:
                print(f"Error in state listener: {e}")
    
    def transition_to(self, new_state: OverlayState):
        """Transition to a new state."""
        if new_state != self._state:
            self._previous_state = self._state
            self._state = new_state
            self._notify_listeners(self._previous_state, self._state)
    
    def set_idle(self):
        """Return to idle state."""
        self.transition_to(OverlayState.IDLE)
    
    def set_listening(self, audio_level: float = 0.0):
        """Enter listening state with optional audio level."""
        self.audio_level = audio_level
        self.transition_to(OverlayState.LISTENING)
    
    def update_audio_level(self, level: float):
        """Update audio level during listening."""
        self.audio_level = max(0.0, min(1.0, level))
    
    def set_processing(self):
        """Enter processing state."""
        self.transition_to(OverlayState.PROCESSING)
    
    def set_action(self, message: str, icon: Optional[str] = None):
        """Show action feedback."""
        self.action_data = ActionData(message=message, icon=icon)
        self.transition_to(OverlayState.ACTION)
    
    def set_gesture(self, landmarks: List = None, active_finger: int = None, hover_key: str = None):
        """Enter gesture mode."""
        self.gesture_data = GestureData(
            hand_landmarks=landmarks or [],
            active_finger=active_finger,
            hover_key=hover_key
        )
        self.transition_to(OverlayState.GESTURE)
    
    def update_gesture(self, landmarks: List = None, active_finger: int = None, hover_key: str = None):
        """Update gesture data without changing state."""
        if landmarks is not None:
            self.gesture_data.hand_landmarks = landmarks
        if active_finger is not None:
            self.gesture_data.active_finger = active_finger
        if hover_key is not None:
            self.gesture_data.hover_key = hover_key
    
    def set_keypad(self, active_key: Optional[str] = None):
        """Enter keypad mode."""
        self.keypad_data.active_key = active_key
        self.transition_to(OverlayState.KEYPAD)
    
    def update_keypad(self, active_key: Optional[str]):
        """Update active keypad key."""
        self.keypad_data.active_key = active_key
