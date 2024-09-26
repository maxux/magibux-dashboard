#!/bin/bash

modules="dashboard persistance location relay temperatures pressures rtinfo tracker tracklog"

for module in $modules; do
    session="backend-${module}"

    tmux new-sess -s ${session} -d -c /root/dashboard/backend
    tmux send-keys -t ${session} "python ${module}.py" ENTER

    sleep 0.2
done

tmux new-sess -s dashboard-gateway -d -c /root/dashboard/webcontrol
tmux send-keys -t dashboard-gateway "python dashboard-gateway.py" ENTER

