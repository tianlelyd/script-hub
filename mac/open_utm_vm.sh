#!/bin/bash
# Get the VM ID from the command line
VM_ID='openwrt-diy'

# 10 seconds delay
sleep 10

# Start the VM with the given ID
/Applications/UTM.app/Contents/MacOS/utmctl start $VM_ID
