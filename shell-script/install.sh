#!/bin/sh
MAIN_NAME="verse-lingua"
SERVER_URL="https://raw.githubusercontent.com/abdullah-al-jaber/$MAIN_NAME/vanilla/server-script/main.py"
USER_URL="https://raw.githubusercontent.com/abdullah-al-jaber/$MAIN_NAME/vanilla/user-script/main.js"
SERVER_PATH="/usr/bin/$MAIN_NAME"
USER_PATH="/android/$MAIN_NAME.js"
MAIN_COMPLETION_PATH="/etc/fish/completions/$MAIN_NAME.fish"

if [ "$(id -u)" -ne 0 ]; then
	echo "Failed to gain root permission !"
	exit 1
fi

curl -sSL "$SERVER_URL" -o "$SERVER_PATH" || {
	echo "Failed to download server script !"
	exit 2
}
chmod +x "$SERVER_PATH" || {
	echo "Failed to make server script executable !"
	exit 3
}
register-python-argcomplete --shell fish "$MAIN_NAME" >"$MAIN_COMPLETION_PATH" || {
	echo "Failed to generate FISH completions !"
	exit 4
}

echo "Successfully installed server script !"

curl -sSL "$USER_URL" -o "$USER_PATH" || {
	echo "Failed to download user script !"
	exit 4
}

echo "Successfully downloaded user script !"
echo "Please install user script ! PATH: $USER_PATH !"

# Final Version
