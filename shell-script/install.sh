#!/bin/sh
MAIN_NAME="verse-lingua"
MAIN_URL="https://abdullah-al-jaber.github.io/$MAIN_NAME/python-script/main.py"
MAIN_COMPLETION_URL="https://abdullah-al-jaber.github.io/$MAIN_NAME/shell-script/completion.fish"
MAIN_PATH="/usr/bin/$MAIN_NAME"
MAIN_COMPLETION_PATH="/etc/fish/completions/$MAIN_NAME.fish"

[ "$(id -u)" -eq 0 ] || {
    echo "Please execute with root privilege !" && exit
}

curl -sSL "$MAIN_URL" -o "$MAIN_PATH" || {
    echo "FAILURE: curl \"$MAIN_URL\" -o \"$MAIN_PATH\" !" && exit
}

chmod +x "$MAIN_PATH" || {
    echo "FAILURE: chmod +x \"$MAIN_PATH\" !" && exit
}

curl -sSL "$MAIN_COMPLETION_URL" -o "$MAIN_COMPLETION_PATH" || {
    echo "FAILURE: curl \"$MAIN_COMPLETION_URL\" -o \"$MAIN_COMPLETION_PATH\" !" && exit
}

echo "SUCCESS: INSTALL DONE !"
