#!/bin/sh
SERVER_PATH="/usr/bin/verse-lingua"
USER_PATH="/android/verse-lingua.js"

if [ "$(id -u)" -ne 0 ]; then
  echo "Failed to gain root permission !"
  exit 1
fi

rm $SERVER_PATH || { echo "Failed to remove server script !"; exit 2; }
echo "Successfully uninstalled server script !"

rm -f $USER_PATH || { echo "Failed to remove user script !"; exit 2; }
echo "Successfully removed server script !"

# Final Version
