#!/bin/bash

tmux new-sess -s dash-http -c /root/dashboard/frontend -d 'python -m http.server 80'
tmux new-sess -s rtinfo-webui -c /root/dashboard/monitoring -d 'python -m http.server 81'

tmux new-sess -s dash-main -c /root/dashboard/backend -d 'python dashboard.py'
tmux new-sess -s persistance -c /root/dashboard/backend -d 'python persistance.py'
tmux new-sess -s locator -c /root/dashboard/backend -d 'python location.py'
tmux new-sess -s sensors -c /root/dashboard/backend -d 'python sensors.py'

tmux new-sess -s rtinfo-websrv -c /root/dashboard/backend -d 'python dashboard-rtinfo.py'
tmux new-sess -s rtinfo-fetcher -c /root/dashboard/backend -d 'python rtinfo.py'
