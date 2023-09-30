# This variable will hold the command to be executed instead of the one the user entered
typeset -g PREPROCESSED_CMD=""
# This variable will hold the original command entered by the user
typeset -g ORIGINAL_CMD=""
# This flag indicates if the command should be suppressed
typeset -g SUPPRESS_CMD=false
# This var stores the current chat history
typeset -g CUR_CHAT_HISTORY=""

echo -e "\033[1;32mHi, I'm IntelliShell!\033[0m"
echo -e "\nRun commands like you usually would (ls, cd Home, etc.)"
echo -e "\nTalk to me with ? (?Explain how the ls command works in Linux)"
echo -e "\nAsk me to perform actions with : (:Make a file called test.txt)"

# Redefine the accept-line widget to preprocess the command
_preprocess_cmd_accept_line() {
    local cwd_pth="$HOME/.oh-my-zsh/custom/plugins/intellishell"
    # Capture the current buffer (command)
    local cmd="$BUFFER"
    echo -e "\nThinking..."

    # Get output of cmd.py
    intelli_out=$($cwd_pth/env/bin/python $cwd_pth/cmd.py "$cmd")
    exit_status=$?

    echo "---------------------------"
    if [[ $exit_status -eq 0 ]]; then
        echo -e "$intelli_out"
        echo "Are you sure you want to execute? (Y/n): "
        read should_exec < /dev/tty
        if [[ "${should_exec:l}" == 'n' ]]; then
            PREPROCESSED_CMD="echo"
            ORIGINAL_CMD=$BUFFER
            BUFFER=""
            SUPPRESS_CMD=true
        else
            SUPPRESS_CMD=false
        fi
    elif [[ $exit_status -eq 1 ]]; then
        CUR_CHAT_HISTORY="$CUR_CHAT_HISTORY!!!<>?user"$'\n'"$cmd"
        CUR_CHAT_HISTORY=$($cwd_pth/env/bin/python $cwd_pth/cmd.py --chat "$CUR_CHAT_HISTORY")
        parts=("${(@s/!!!<>?assistant/)CUR_CHAT_HISTORY}")
        last_part="${parts[-1]}"
        echo -e "$last_part"
        PREPROCESSED_CMD="echo"
        ORIGINAL_CMD=$BUFFER
        BUFFER=""
        SUPPRESS_CMD=true
    elif [[ $exit_status -eq 2 ]]; then
        echo -e "$intelli_out\n\n---------------------------"
        echo "This code is the planned action. Are you sure you want to execute? (Y/n): "
        read should_exec < /dev/tty
        if [[ "${should_exec:l}" != 'n' ]]; then
            echo "---------------------------"
            echo $intelli_out > .agent_action.py
            output=$($cwd_pth/env/bin/python .agent_action.py)
            echo $output
            echo "---------------------------"
            echo "Code execution complete."
            rm .agent_action.py
        fi
        PREPROCESSED_CMD="echo"
        ORIGINAL_CMD=$BUFFER
        BUFFER=""
        SUPPRESS_CMD=true
    fi

    zle .accept-line  # Call the original accept-line widget
}

# Use our custom accept-line in place of the default one
zle -N accept-line _preprocess_cmd_accept_line

# Add a hook for executing the preprocessed command just before the command prompt
precmd() {
    if [[ -n "$PREPROCESSED_CMD" ]]; then
        eval "$PREPROCESSED_CMD"
        print -s $ORIGINAL_CMD
        PREPROCESSED_CMD=""
        ORIGINAL_CMD=""
    fi
}

# If SUPPRESS_CMD is true, we clear the command just before it executes to suppress it
preexec() {
    if $SUPPRESS_CMD; then
        BUFFER=""
    fi
}