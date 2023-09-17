#!/bin/bash
# Copyright 2023 Morten Jakobsen. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
# -*- coding: utf-8 -*-

# ###################################################################### #

# The smart errors that is used to determine a failure is taken
# from the backblaze website that reports smart stats:
# https://www.backblaze.com/blog/hard-drive-smart-stats/
#
# It was not explained in detail of what values should be considered a
# failure rate (except for 187) - so I looked at their stats and took
# the values corresponding to 25% - or what seemed like sensible values.

# ###################################################################### #

# G-Mail username and password (use app passwords):
FROM_EMAIL_ADDRESS="noreply@example.com"
EMAIL_ACCOUNT_PASSWORD="hackme"

# Report recipient and sender name
TO_EMAIL_ADDRESS="example@example.com"
FRIENDLY_NAME="Example Name"

# ###################################################################### #

# Report output
mkdir -p /tmp/smartreport

# Filters for getting block device names
disks=$((
    /usr/sbin/blkid | cut -d: -f1 | grep sd | sed 's/[0-9]//' & \
    /usr/sbin/blkid | cut -d: -f1 | grep nvme | sed 's/p.//';
    ) | sed 's/\/dev\///' | uniq)

for disk in $disks; do /usr/sbin/smartctl -a /dev/$disk > /tmp/smartreport/$disk.txt; done

# Check each drive report for errors
for report in /tmp/smartreport/*.txt; do
    failure=0
    message=""

    # Get some basic information from the smart reports
    devname=$(echo $report | cut -d. -f1 | cut -d/ -f4)
    family=$(grep -i "Model Family" $report | cut -d: -f2 | xargs)
    model=$(grep -i "Device Model" $report | cut -d: -f2 | xargs)
    serial=$(grep -i "Serial Number" $report | cut -d: -f2 | xargs)

    # Grab error output
    e5=$(grep "5 Rea" $report | awk '{print $10}')
    e9=$(grep "9 Pow" $report | awk '{print $10}')
    e12=$(grep "12 Pow" $report | awk '{print $10}')
    e187=$(grep "187 Rep" $report | awk '{print $10}')
    e188=$(grep "188 Com" $report | awk '{print $10}')
    e197=$(grep "197 Cur" $report | awk '{print $10}')
    e198=$(grep "198 Off" $report | awk '{print $10}')

    # Check all errors against defined thresholds
    # This section might report "[: -ge: unary operator expected".
    # This is perfectly fine, it just means that specific error was not
    # found in the report for that blockdevice.
    [ $e5 -ge 20 ] && failure=1 \
        && message="$message\n  $e5 reallocated sectors reported - trigger level is 20"

    [ $e9 -ge 8760 ] && failure=1 \
        && message="$message\n  $e9 power on hours reported - trigger level is 8760"

    [ $e12 -ge 730 ] && failure=1 \
        && message="$message\n  $e12 power cycle count reported - trigger level is 730"

    [ $e187 -ge 1 ] && failure=1 \
        && message="$message\n  $e187 uncorrectable read errors reported - trigger level is 1"

    [ $e188 -ge 100 ] && failure=1 \
        && message="$message\n  $e188 command timeouts reported - trigger level is 100"

    [ $e197 -ge 1 ] && failure=1 \
        && message="$message\n  $e197 pending sectors reported - trigger level is 1"

    [ $e198 -ge 1 ] && failure=1 \
        && message="$message\n  $e198 offline uncorrectable sectors reported - trigger level is 1"

    # If a threshold is reached, report it
    if [ $failure -gt 0 ]; then
    {
        echo -e "One or more failure modes have been detected for /dev/$devname\n" \
        && echo "The serial number is: $serial" \
        && echo "The model number is: $model" \
        && echo -e "\n>>> You should consider replacing the drive. <<<\n" \
        && echo -e "The errors reported are:\n$message" \
        && echo -e "\n\n\n\nHere is the full SMART report:\n" \
        && cat $report
    } | /usr/bin/mailx -s "One or more important smart errors detected for $devname" \
                        -S smtp-use-starttls \
                        -S ssl-verify=ignore \
                        -S smtp-auth=login \
                        -S smtp=smtp://smtp.gmail.com:587 \
                        -S from="$FROM_EMAIL_ADDRESS($FRIENDLY_NAME)" \
                        -S smtp-auth-user=$FROM_EMAIL_ADDRESS \
                        -S smtp-auth-password=$EMAIL_ACCOUNT_PASSWORD \
                        -S ssl-verify=ignore \
                        -S nss-config-dir=/etc/pki/nssdb \
                        $TO_EMAIL_ADDRESS
    fi
done

# Delete report output folder
rm -rf /tmp/smartreport
