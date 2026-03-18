#!/bin/sh
MAIN_NAME="verse-lingua"
SERVER_PATH="/usr/bin/$MAIN_NAME"
USER_PATH="/android/$MAIN_NAME.js"
MAIN_COMPLETION_PATH="/etc/fish/completions/$MAIN_NAME.fish"

if [ "$(id -u)" -ne 0 ]; then
	echo "Failed to gain root permission !"
	exit 1
fi

rm $SERVER_PATH || {
	echo "Failed to remove server script !"
	exit 2
}
rm "$MAIN_COMPLETION_PATH" || {
	echo "Failed to remove FISH completions !"
	exit 3
}
echo "Successfully uninstalled server script !"

rm -f $USER_PATH || {
	echo "Failed to remove user script !"
	exit 4
}
echo "Successfully removed server script !"

# Final Version
