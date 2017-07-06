#!/bin/sh

set -e

RAM_DISK_MB=1
RAM_DISK_NAME=RamDisk
MOUNTED_RAM_DISK_FOLDER="/Volumes/${RAM_DISK_NAME}"
# Unmount RAM disk
if [ "$1" = "-u" ]; then
    if [ -e "${MOUNTED_RAM_DISK_FOLDER}" ]; then
hdiutil detach "${MOUNTED_RAM_DISK_FOLDER}"
else
echo "RAM disk is not mounted yet."
fi
exit
fi
# Get RAM disk size from parameter
if [ "$1" != "" ]; then
RAM_DISK_MB="$1"
fi
if [ -e "${MOUNTED_RAM_DISK_FOLDER}" ]; then
echo "RAM disk is already mounted on ${MOUNTED_RAM_DISK_FOLDER}."
else
diskutil erasevolume HFS+ "${RAM_DISK_NAME}" $(hdiutil attach -nomount ram://$((RAM_DISK_MB*2048)))
fi
