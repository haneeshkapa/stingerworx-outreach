#!/bin/bash

# VNC setup for Replit with password authentication
export DISPLAY=:0
export HOME=/home/runner

# Create VNC directory
mkdir -p ~/.vnc

# Set VNC password from environment variable
if [ -n "$VNC_PASSWORD" ]; then
    echo "$VNC_PASSWORD" | vncpasswd -f > ~/.vnc/passwd
    chmod 600 ~/.vnc/passwd
    echo "VNC password configured"
fi

# Kill any existing servers
vncserver -kill :0 2>/dev/null || true
killall Xvnc 2>/dev/null || true

# Start VNC server with password authentication
Xvnc :0 -geometry 1280x720 -depth 24 -rfbport 5900 -SecurityTypes VncAuth -PasswordFile ~/.vnc/passwd &

# Wait for X server to start
sleep 2

# Start window manager
DISPLAY=:0 fluxbox &

# Keep running
echo "VNC server started on :0 (port 5900) with authentication"
tail -f /dev/null
