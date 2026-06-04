# Bash completion for the app named after the snap
unset -f _init_completion
source <($SNAP/bin/modelctl completion bash)
