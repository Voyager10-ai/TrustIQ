# Dataset Creation Guide

## Overview

Since no public exam cheating detection dataset exists, ABIE uses a custom mini-dataset strategy. This directory contains both real and simulated exam behavior recordings for training and evaluation.

## Directory Structure

```
datasets/
├── normal/          # Normal exam behavior (baseline)
├── phone_cheat/     # Phone cheating simulation
├── whisper_cheat/   # Whispering simulation
├── ai_typing_cheat/ # AI-assisted answer typing
└── smart_glasses_cheat/ # Smart glasses simulation
```

## Recording Protocol

### Normal Behavior
- Record 10+ minutes of genuine exam taking
- Include: typing, reading, thinking pauses
- Save: video (webcam), audio (mic), keystrokes (log)

### Phone Cheating Simulation
- Glance down at phone periodically
- Check phone for 2-3 seconds at a time
- Record change in gaze pattern

### Whisper Cheating Simulation
- Whisper questions/answers to a second person
- Include varying volumes (barely audible to soft speaking)
- Record ambient vs whisper audio

### AI Typing Simulation
- Copy-paste text from an AI tool
- Note the sudden typing burst pattern
- Record keystroke timing differences

### Smart Glasses Simulation
- Show reflection artifacts in webcam
- Demonstrate illumination changes from display
- Record face detection anomalies

## File Format

Each recording should include:
- `video_TIMESTAMP.mp4` — Webcam recording
- `audio_TIMESTAMP.wav` — Microphone recording (16kHz, mono)
- `keystrokes_TIMESTAMP.json` — Keystroke timing data
- `metadata.json` — Session info, labels, notes
