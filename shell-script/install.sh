#!/bin/sh
SERVER_URL="https://raw.githubusercontent.com/abdullah-al-jaber/verse-lingua/vanilla/server-script/main.py"
USER_URL="https://raw.githubusercontent.com/abdullah-al-jaber/verse-lingua/vanilla/user-script/main.js"
SERVER_PATH="/usr/bin/verse-lingua"
USER_PATH="/android/verse-lingua.js"

if [ "$(id -u)" -ne 0 ]; then
  echo "[ERROR] Failed to gain root permission !"
  exit 1
fi

curl -sSL "$SERVER_URL" -o "$SERVER_PATH" || { echo "Failed to download server script !"; exit 2; }
chmod +x "$SERVER_PATH" || { echo "Failed to make server script executable !"; exit 3; }

echo "Successfully installed server script !"

curl -sSL "$USER_URL" -o "$USER_PATH" || { echo "Failed to download user script !"; exit 4; }

echo "Successfully downloaded user script !"
echo "Please install user script ! PATH: $USER_PATH !"

# Final Version
