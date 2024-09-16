#!/bin/bash

sessname="camsync"

tmux kill-session -t ${sessname}
tmux new-sess -s ${sessname} -d -c /root -e TERMID=0

for i in {1..7}; do
    tmux split-window -t ${sessname} -c /root -e TERMID=$i
    tmux select-layout -t ${sessname} tiled
done

tmux set-option -t ${sessname} synchronize-panes on
tmux send-keys -t ${sessname} 'ssh 10.244.0.$((100 + $TERMID))' ENTER

tmux attach-session -t ${sessname}
