#!/bin/bash
tmux new-sess -s dash-http -d 'cd /root/dashboard/frontend && python -m http.server 80'
tmux new-sess -s dash-main -d 'cd /root/dashboard/backend && python dashboard.py'
tmux new-sess -s locator -d 'cd /root/dashboard/backend && python location.py'
