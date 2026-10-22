#!/bin/sh
MAIN_NAME="verse-lingua"
MAIN_PATH="/usr/bin/$MAIN_NAME"
MAIN_COMPLETION_PATH="/etc/fish/completions/$MAIN_NAME.fish"

[ "$(id -u)" -eq 0 ] || {
    echo "Please execute with root privilege !" && exit
}

rm "$MAIN_PATH" || {
    echo "FAILURE: rm \"$MAIN_PATH\" !" && exit
}

rm "$MAIN_COMPLETION_PATH" || {
    echo "FAILURE: rm \"$MAIN_COMPLETION_PATH\" !" && exit
}

echo "SUCCESS: UNINSTALL DONE !"
