"""Animation utilities for the overlay."""

import math
from typing import Tuple
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QObject, Property, Signal
from PySide6.QtGui import QColor


class AnimationController(QObject):
    """Controller for overlay animations."""
    
    # Signals for animation updates
    opacity_changed = Signal(float)
    scale_changed = Signal(float)
    rotation_changed = Signal(float)
    color_changed = Signal(QColor)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._opacity = 1.0
        self._scale = 1.0
        self._rotation = 0.0
        self._color = QColor("#00FFFF")
        
        # Animation objects
        self._opacity_anim: QPropertyAnimation = None
        self._scale_anim: QPropertyAnimation = None
        self._rotation_anim: QPropertyAnimation = None
    
    # Opacity property
    def get_opacity(self) -> float:
        return self._opacity
    
    def set_opacity(self, value: float):
        if self._opacity != value:
            self._opacity = value
            self.opacity_changed.emit(value)
    
    opacity = Property(float, get_opacity, set_opacity)
    
    # Scale property
    def get_scale(self) -> float:
        return self._scale
    
    def set_scale(self, value: float):
        if self._scale != value:
            self._scale = value
            self.scale_changed.emit(value)
    
    scale = Property(float, get_scale, set_scale)
    
    # Rotation property
    def get_rotation(self) -> float:
        return self._rotation
    
    def set_rotation(self, value: float):
        if self._rotation != value:
            self._rotation = value
            self.rotation_changed.emit(value)
    
    rotation = Property(float, get_rotation, set_rotation)
    
    def fade_to(self, target_opacity: float, duration_ms: int = 300):
        """Animate opacity to target value."""
        if self._opacity_anim:
            self._opacity_anim.stop()
        
        self._opacity_anim = QPropertyAnimation(self, b"opacity")
        self._opacity_anim.setDuration(duration_ms)
        self._opacity_anim.setStartValue(self._opacity)
        self._opacity_anim.setEndValue(target_opacity)
        self._opacity_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._opacity_anim.start()
    
    def scale_to(self, target_scale: float, duration_ms: int = 300):
        """Animate scale to target value."""
        if self._scale_anim:
            self._scale_anim.stop()
        
        self._scale_anim = QPropertyAnimation(self, b"scale")
        self._scale_anim.setDuration(duration_ms)
        self._scale_anim.setStartValue(self._scale)
        self._scale_anim.setEndValue(target_scale)
        self._scale_anim.setEasingCurve(QEasingCurve.Type.OutBack)
        self._scale_anim.start()
    
    def start_rotation(self, duration_ms: int = 2000):
        """Start continuous rotation."""
        if self._rotation_anim:
            self._rotation_anim.stop()
        
        self._rotation_anim = QPropertyAnimation(self, b"rotation")
        self._rotation_anim.setDuration(duration_ms)
        self._rotation_anim.setStartValue(0.0)
        self._rotation_anim.setEndValue(360.0)
        self._rotation_anim.setLoopCount(-1)  # Infinite
        self._rotation_anim.start()
    
    def stop_rotation(self):
        """Stop rotation animation."""
        if self._rotation_anim:
            self._rotation_anim.stop()
            self._rotation = 0.0
    
    def stop_all(self):
        """Stop all animations."""
        if self._opacity_anim:
            self._opacity_anim.stop()
        if self._scale_anim:
            self._scale_anim.stop()
        if self._rotation_anim:
            self._rotation_anim.stop()


class BreathingAnimation:
    """Breathing pulse effect calculator."""
    
    def __init__(self, min_value: float = 0.05, max_value: float = 0.1, duration_ms: int = 3000):
        self.min_value = min_value
        self.max_value = max_value
        self.duration_ms = duration_ms
        self._elapsed = 0
    
    def update(self, delta_ms: int) -> float:
        """Update and return current breathing value."""
        self._elapsed = (self._elapsed + delta_ms) % self.duration_ms
        # Sine wave for smooth breathing
        t = self._elapsed / self.duration_ms
        value = math.sin(t * 2 * math.pi) * 0.5 + 0.5
        return self.min_value + value * (self.max_value - self.min_value)
    
    def reset(self):
        """Reset animation to start."""
        self._elapsed = 0


class WaveformAnimation:
    """Audio waveform animation calculator."""
    
    def __init__(self, num_bars: int = 5):
        self.num_bars = num_bars
        self._phases = [i * (2 * math.pi / num_bars) for i in range(num_bars)]
        self._elapsed = 0
    
    def update(self, delta_ms: int, audio_level: float = 0.5) -> list:
        """Update and return bar heights (0-1 range)."""
        self._elapsed += delta_ms
        
        # Make the animation faster/more reactive
        import random
        heights = []
        center_idx = self.num_bars // 2
        
        for i in range(self.num_bars):
            # Distance from center bar
            dist = abs(center_idx - i)
            
            # Base height driven by audio level
            # Center bars are taller
            scale = 1.0 - (dist * 0.2) 
            
            # Add randomness for "jitter" effect
            jitter = random.uniform(0.8, 1.2)
            
            # Direct mapping from audio level
            height = audio_level * scale * jitter
            
            # Clamp
            heights.append(max(0.1, min(1.0, height)))
        
        return heights


def interpolate_color(color1: QColor, color2: QColor, t: float) -> QColor:
    """Interpolate between two colors."""
    t = max(0.0, min(1.0, t))
    r = int(color1.red() + (color2.red() - color1.red()) * t)
    g = int(color1.green() + (color2.green() - color1.green()) * t)
    b = int(color1.blue() + (color2.blue() - color1.blue()) * t)
    a = int(color1.alpha() + (color2.alpha() - color1.alpha()) * t)
    return QColor(r, g, b, a)


def ease_in_out_quad(t: float) -> float:
    """Quadratic ease in/out function."""
    if t < 0.5:
        return 2 * t * t
    return 1 - pow(-2 * t + 2, 2) / 2
