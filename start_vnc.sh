#!/bin/bash

# Simple VNC setup for Replit
export DISPLAY=:0
export HOME=/home/runner

# Create VNC directory
mkdir -p ~/.vnc

# Kill any existing servers
vncserver -kill :0 2>/dev/null || true
killall Xvnc 2>/dev/null || true

# Start VNC server with simple config
Xvnc :0 -geometry 1280x720 -depth 24 -rfbport 5900 -SecurityTypes None &

# Wait for X server to start
sleep 2

# Start window manager
DISPLAY=:0 fluxbox &

# Keep running
echo "VNC server started on :0 (port 5900)"
tail -f /dev/null
