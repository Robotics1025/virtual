"""Phase renderers for the overlay interface."""

import math
from typing import Optional
from PySide6.QtCore import Qt, QRectF, QPointF, QTimer
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QRadialGradient,
    QLinearGradient, QFont, QPainterPath
)
from PySide6.QtWidgets import QWidget

from .state_machine import OverlayState, OverlayStateMachine
from .config import OverlayConfig
from .animations import BreathingAnimation, WaveformAnimation, interpolate_color


class BaseRenderer:
    """Base class for phase renderers."""
    
    def __init__(self, config: OverlayConfig, state_machine: OverlayStateMachine):
        self.config = config
        self.state_machine = state_machine
    
    def render(self, painter: QPainter, rect: QRectF, opacity: float):
        """Render the phase. Override in subclasses."""
        pass


class IdleRenderer(BaseRenderer):
    """Renders the idle phase - breathing dot."""
    
    def __init__(self, config: OverlayConfig, state_machine: OverlayStateMachine):
        super().__init__(config, state_machine)
        self.breathing = BreathingAnimation(
            min_value=0.05,
            max_value=0.12,
            duration_ms=config.breathing_duration_ms
        )
        self._elapsed = 0
    
    def update(self, delta_ms: int):
        """Update breathing animation."""
        self._elapsed += delta_ms
    
    def render(self, painter: QPainter, rect: QRectF, opacity: float):
        """Render breathing dot."""
        center = rect.center()
        
        # Calculate breathing size
        breathing_value = self.breathing.update(16)  # ~60fps
        base_size = min(rect.width(), rect.height()) * 0.3
        size = base_size * (0.8 + breathing_value * 2)
        
        # Create radial gradient for glow effect
        gradient = QRadialGradient(center, size)
        color = QColor(self.config.colors.primary_glow)
        color.setAlphaF(opacity * breathing_value * 8)
        gradient.setColorAt(0, color)
        color.setAlphaF(0)
        gradient.setColorAt(1, color)
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(center, size, size)
        
        # Inner dot
        inner_size = base_size * 0.15
        inner_color = QColor(self.config.colors.primary_glow)
        inner_color.setAlphaF(opacity * 0.6)
        painter.setBrush(QBrush(inner_color))
        painter.drawEllipse(center, inner_size, inner_size)


class ListeningRenderer(BaseRenderer):
    """Renders the listening phase - waveform with mic icon."""
    
    def __init__(self, config: OverlayConfig, state_machine: OverlayStateMachine):
        super().__init__(config, state_machine)
        self.waveform = WaveformAnimation(num_bars=5)
    
    def render(self, painter: QPainter, rect: QRectF, opacity: float):
        """Render listening waveform."""
        center = rect.center()
        base_size = min(rect.width(), rect.height()) * 0.35
        
        # Outer glow ring
        ring_color = QColor(self.config.colors.listening)
        ring_color.setAlphaF(opacity * 0.3)
        pen = QPen(ring_color, 3)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(center, base_size, base_size)
        
        # Waveform bars
        audio_level = self.state_machine.audio_level
        heights = self.waveform.update(16, max(0.3, audio_level))
        
        bar_width = 6
        bar_spacing = 10
        total_width = len(heights) * bar_spacing
        start_x = center.x() - total_width / 2
        
        bar_color = QColor(self.config.colors.listening)
        bar_color.setAlphaF(opacity * 0.8)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(bar_color))
        
        max_height = base_size * 0.6
        for i, height in enumerate(heights):
            bar_height = max(4, height * max_height)
            x = start_x + i * bar_spacing
            y = center.y() - bar_height / 2
            painter.drawRoundedRect(
                QRectF(x, y, bar_width, bar_height),
                bar_width / 2, bar_width / 2
            )
        
        # "Listening..." text
        font = QFont("Segoe UI", 10)
        painter.setFont(font)
        text_color = QColor("#FFFFFF")
        text_color.setAlphaF(opacity * 0.7)
        painter.setPen(text_color)
        text_rect = QRectF(rect.x(), center.y() + base_size + 10, rect.width(), 20)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "Listening...")


class ProcessingRenderer(BaseRenderer):
    """Renders the processing phase - rotating ring with color shift."""
    
    def __init__(self, config: OverlayConfig, state_machine: OverlayStateMachine):
        super().__init__(config, state_machine)
        self._rotation = 0
        self._color_phase = 0
    
    def update(self, delta_ms: int):
        """Update rotation and color."""
        self._rotation = (self._rotation + delta_ms * 0.1) % 360
        self._color_phase = (self._color_phase + delta_ms * 0.001) % 1.0
    
    def render(self, painter: QPainter, rect: QRectF, opacity: float):
        """Render rotating processing ring."""
        center = rect.center()
        base_size = min(rect.width(), rect.height()) * 0.35
        
        # Color transition blue -> purple
        color1 = QColor(self.config.colors.listening)
        color2 = QColor(self.config.colors.processing)
        current_color = interpolate_color(color1, color2, self._color_phase)
        current_color.setAlphaF(opacity * 0.6)
        
        painter.save()
        painter.translate(center)
        painter.rotate(self._rotation)
        
        # Draw arc segments
        pen = QPen(current_color, 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        arc_rect = QRectF(-base_size, -base_size, base_size * 2, base_size * 2)
        
        # Draw multiple arcs for visual effect
        for i in range(4):
            start_angle = i * 90 * 16 + 20 * 16
            span_angle = 50 * 16
            painter.drawArc(arc_rect, start_angle, span_angle)
        
        painter.restore()
        
        # "Understanding..." text
        font = QFont("Segoe UI", 10)
        painter.setFont(font)
        text_color = QColor("#FFFFFF")
        text_color.setAlphaF(opacity * 0.7)
        painter.setPen(text_color)
        text_rect = QRectF(rect.x(), center.y() + base_size + 10, rect.width(), 20)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "Understanding...")


class ActionRenderer(BaseRenderer):
    """Renders the action phase - glass toast notification."""
    
    def render(self, painter: QPainter, rect: QRectF, opacity: float):
        """Render action toast."""
        message = self.state_machine.action_data.message
        if not message:
            return
        
        # Toast dimensions
        toast_width = min(self.config.toast_width, rect.width() - 20)
        toast_height = 50
        toast_x = rect.center().x() - toast_width / 2
        toast_y = rect.center().y() - toast_height / 2
        
        toast_rect = QRectF(toast_x, toast_y, toast_width, toast_height)
        
        # Glass background
        bg_color = QColor(255, 255, 255, int(40 * opacity))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(toast_rect, 12, 12)
        
        # Border glow
        border_color = QColor(255, 255, 255, int(60 * opacity))
        pen = QPen(border_color, 1)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(toast_rect, 12, 12)
        
        # Text
        font = QFont("Segoe UI", 11)
        painter.setFont(font)
        text_color = QColor(self.config.colors.action_text)
        text_color.setAlphaF(opacity * 0.95)
        painter.setPen(text_color)
        painter.drawText(toast_rect, Qt.AlignmentFlag.AlignCenter, message)


class GestureRenderer(BaseRenderer):
    """Renders the gesture phase - hand outline with highlights."""
    
    def render(self, painter: QPainter, rect: QRectF, opacity: float):
        """Render gesture overlay."""
        gesture_data = self.state_machine.gesture_data
        
        # Draw hover key label if present
        if gesture_data.hover_key:
            center = rect.center()
            
            # Floating label
            label_width = 60
            label_height = 40
            label_rect = QRectF(
                center.x() - label_width / 2,
                center.y() - label_height / 2,
                label_width,
                label_height
            )
            
            # Glass background
            bg_color = QColor(255, 255, 255, int(50 * opacity))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(bg_color))
            painter.drawRoundedRect(label_rect, 8, 8)
            
            # Key text
            font = QFont("Segoe UI", 16, QFont.Weight.Bold)
            painter.setFont(font)
            text_color = QColor(self.config.colors.gesture_highlight)
            text_color.setAlphaF(opacity * 0.9)
            painter.setPen(text_color)
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, gesture_data.hover_key)


class KeypadRenderer(BaseRenderer):
    """Renders the keypad phase - QWERTY Keyboard."""
    
    def __init__(self, config: OverlayConfig, state_machine: OverlayStateMachine):
        super().__init__(config, state_machine)
        self._key_rects = {}  # Store key rects for hit testing

    def render(self, painter: QPainter, rect: QRectF, opacity: float):
        """Render keyboard grid."""
        keypad_data = self.state_machine.keypad_data
        # Ensure layout is initialized
        if not keypad_data.rows or len(keypad_data.rows) < 2:
            keypad_data._init_layout()
            
        rows = keypad_data.rows
        active_key = keypad_data.active_key
        
        base_key_size = 50 
        gap = 6
        
        # Calculate total dimensions to center the keyboard
        # Assuming max width approx 15 units * base_size
        max_row_width = 0
        total_height = len(rows) * (base_key_size + gap) - gap
        
        # Pre-calculate row widths to center each row
        row_widths = []
        for row in rows:
            w = sum(key.width * base_key_size for key in row) + (len(row) - 1) * gap
            row_widths.append(w)
            max_row_width = max(max_row_width, w)
            
        start_y = rect.center().y() - total_height / 2
        
        font = QFont("Segoe UI", 14, QFont.Weight.Medium)
        painter.setFont(font)
        
        self._key_rects.clear()

        current_y = start_y
        
        for r_idx, row in enumerate(rows):
            current_x = rect.center().x() - row_widths[r_idx] / 2
            
            for key_data in row:
                width = key_data.width * base_key_size
                height = base_key_size
                
                key_rect = QRectF(current_x, current_y, width, height)
                self._key_rects[key_data.code] = key_rect  # Key by code, not label
                
                # Active highlight
                is_active = key_data.code == active_key
                
                # Styling
                if is_active:
                    bg_color = QColor(self.config.colors.gesture_highlight)
                    bg_color.setAlphaF(opacity * 0.6)
                elif key_data.is_action:
                     bg_color = QColor(self.config.colors.processing)
                     bg_color.setAlphaF(opacity * 0.25)
                else:
                    bg_color = QColor(255, 255, 255, int(35 * opacity))
                
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(bg_color))
                painter.drawRoundedRect(key_rect, 6, 6)
                
                # Border
                border_color = QColor(255, 255, 255, int(50 * opacity))
                painter.setPen(QPen(border_color, 1))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRoundedRect(key_rect, 6, 6)
                
                # Label
                text_color = QColor("#FFFFFF")
                text_color.setAlphaF(opacity * 0.95)
                painter.setPen(text_color)
                painter.drawText(key_rect, Qt.AlignmentFlag.AlignCenter, key_data.label)
                
                current_x += width + gap
            
            current_y += base_key_size + gap
        
        # Caption
        caption_y = current_y + 10
        caption_rect = QRectF(rect.x(), caption_y, rect.width(), 20)
        caption_font = QFont("Segoe UI", 9)
        painter.setFont(caption_font)
        caption_color = QColor("#FFFFFF")
        caption_color.setAlphaF(opacity * 0.5)
        painter.setPen(caption_color)
        painter.drawText(caption_rect, Qt.AlignmentFlag.AlignCenter, "Keyboard Mode (Close with 'X' command or ⌫ long press)")

    def hit_test(self, pos: QPointF) -> Optional[str]:
        """Return the key code at the given position."""
        for code, rect in self._key_rects.items():
            if rect.contains(pos):
                return code
        return None
