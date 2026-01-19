# AirVoice Overlay Interface

## Phased, Floating, Transparent UI Design

## 1. Purpose

The AirVoice Overlay Interface is a lightweight, translucent, always-on-top
visual layer that:

- Shows system state (idle, listening, processing, acting)
- Reacts to voice and gestures
- Feels soft, futuristic, and non-intrusive
- Never blocks normal app usage
- Supports accessibility with audio-first design

Design inspiration:

- Samsung “Search a Song”
- Google Assistant listening UI
- Siri waveform
- VisionOS glass UI

## 2. Design Principles

1. Minimal and calm — never distracts
2. Transparent and glass-like
3. Animated, not static
4. Fades in/out smoothly
5. Click-through (does not block mouse)
6. Always-on-top
7. Optional visibility (can be hidden)

## 3. Interface Phases (States)

The UI is driven by system state.

### 3.1 Idle Phase

Purpose: show system is ready without distraction.

Visual:

- Very small glowing dot or ring
- 5–10% opacity
- Slow breathing animation
- Positioned in user-selected corner

Text: none

### 3.2 Listening Phase

Triggered when microphone is active.

Visual:

- Glowing ring expands
- Soft wave animation
- Microphone icon in center
- 40–60% opacity

Text:

- “Listening…”

Animation:

- Pulse synced with mic volume

### 3.3 Processing Phase

Triggered after voice input ends.

Visual:

- Ring rotates slowly
- Glow changes from soft blue → purple
- Wave fades

Text:

- “Understanding…”

### 3.4 Action Phase

Triggered when a command is executed.

Visual:

- Floating toast near indicator
- Soft rectangle with glass blur
- Fade in → hold → fade out

Text examples:

- “Typed: hello world”
- “Pressed Enter”
- “Deleted”

### 3.5 Gesture Phase

Triggered when hand is detected.

Visual:

- Faint outline of hand
- Highlight active finger
- Show key name when hovering

Text:

- Small floating label: “A”, “Enter”, etc.

### 3.6 Keypad Phase

Triggered when the virtual keypad is requested or when a gesture/voice command
enters keypad mode.

Visual:

- Floating 3x3 (or 4x3) keypad grid near the hand or in a user-selected corner
- Glassmorphism tiles with soft glow on active key
- Optional numeric row labels for orientation

Text:

- Small caption: “Keypad Mode”

Behavior:

- Keys highlight on hover and confirm on selection
- Fade in on enter, fade out on exit

## 4. Layer Structure

The overlay consists of 3 logical layers:

1. Status Layer
   - Idle / listening / processing indicator
   - Voice wave
2. Gesture Layer
   - Hand outline
   - Finger highlight
   - Virtual key hover
3. Feedback Layer
   - Toast messages
   - Temporary hints
4. Keypad Layer
   - Floating keypad grid
   - Active key highlight

All layers:

- Transparent background
- Borderless
- Always on top
- Click-through

## 5. Positioning

Default:

- Bottom-right corner

Options:

- Top-left
- Top-right
- Bottom-left
- Center floating
- Follow-hand mode (indicator floats near hand)

User can change in settings.

## 6. Animations

All transitions must be smooth:

| Transition             | Animation                  |
| ---------------------- | -------------------------- |
| Idle → Listening       | Glow expands + fade in     |
| Listening → Processing | Ring rotates + color shift |
| Processing → Action    | Toast fades in             |
| Action → Idle          | Fade out                   |
| Idle → Gesture         | Hand outline fades in      |
| Gesture → Idle         | Fade out                   |
| Idle → Keypad          | Keypad fades in            |
| Keypad → Idle          | Keypad fades out           |

No hard cuts. Always fade.

## 7. Accessibility

### Audio First

- Every visual action has spoken feedback.
- Visual overlay is optional for blind users.

### Modes

- Normal mode: full overlay
- Minimal mode: only tiny indicator
- Audio-only mode: no visuals

## 8. Visual Style Guide

### Colors

- Primary glow: soft cyan
- Listening: blue
- Processing: purple
- Action: white text on glass background
- Gesture highlight: green or white

### Effects

- Blur/glass effect
- Soft shadows
- Glow edges
- Low opacity

### Typography

- Simple, clean font
- Medium weight
- High contrast on glass

## 9. Behavior Rules

1. Overlay must never steal focus.
2. Overlay must never block clicks.
3. Overlay must auto-hide when idle.
4. Overlay must be fast and light.
5. Overlay must always reflect real system state.

## 10. Technical Implementation (Suggested)

### Window Behavior

- Frameless
- Transparent background
- Always-on-top
- Click-through
- Hardware accelerated if possible

### Recommended Tech

- PySide6 / PyQt6
- Or Electron + CSS glassmorphism
- Or Flutter Desktop

## 11. Example User Flow

1. User is coding.
2. Small glowing dot shows in corner (Idle).
3. User says: “Type hello world”.
4. UI fades to Listening phase.
5. UI pulses with voice.
6. UI switches to Processing.
7. UI shows Action toast: “Typed: hello world”.
8. UI fades back to Idle.
9. User pinches finger.
10. Hand outline appears.
11. “Enter” floats near finger.
12. UI fades back to Idle.

## 12. Definition of Done

Overlay interface is complete when:

- It fades between phases smoothly.
- It never blocks user interaction.
- It reflects voice and gesture state.
- It shows feedback without distraction.
- It can be hidden or minimized.
- It supports accessibility modes.

This UI is not just decoration — it is a living status layer that makes your
system feel intelligent, calm, and futuristic.
