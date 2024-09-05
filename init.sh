#!/bin/bash

# FIXME: missing tracker and tracklog
modules="dashboard persistance location relay temperatures pressures rtinfo cameras"

for module in $modules; do
    session="backend-${module}"

    tmux new-sess -s ${session} -d -c /root/dashboard/backend
    tmux send-keys -t ${session} "python ${module}.py" ENTER

    sleep 0.2
done

# tmux new-sess -s dash-main -c /root/dashboard/backend -d 'python dashboard.py'
# tmux new-sess -s persistance -c /root/dashboard/backend -d 'python persistance.py'
# tmux new-sess -s locator -c /root/dashboard/backend -d 'python location.py'
# tmux new-sess -s relays -c /root/dashboard/backend -d 'python relay.py'
# tmux new-sess -s temperatures -c /root/dashboard/backend -d 'python temperatures.py'
# tmux new-sess -s pressures -c /root/dashboard/backend -d 'python pressures.py'
# tmux new-sess -s rtinfo-fetcher -c /root/dashboard/backend -d 'python rtinfo.py'
# tmux new-sess -s camupdate -c /root/dashboard/backend -d 'python cameras.py'
# tmux new-sess -s camera -d -c /home/camera/camstream
