#!/usr/bin/env python3
# Copyright 2019 Morten Jakobsen. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
# -*- coding: utf-8 -*-
#
# This plugin was specifically written to extract
# temperature data from the AVTECH TemPageR 4E
# running firmware v2.6.0. I have no idea if it
# works with later version of the firmware the other
# products AVTECH makes. Use it at your own risk.
#
# When this file is run, it will contact the TemPageR
# sensor and grab the data, if any exceptions happen
# they will be logged to the specified logfile.
# By default this script will log into the munin
# log directory.
# 
# If you use the default log path, I would highly
# recommend that you configure logrotation.
# The easiest way is to add the following logrotate
# snippet to the munin logrotate file.
#
# The snippet below will enable logrotation of the
# tempager.log file using the default munin logrotate
# ruleset.
#
# Add this to  /etc/logrotate.d/munin:
#
# /var/log/munin/tempager.log {
#   daily
#   missingok
#   rotate 7
#   compress
#   notifempty
#   create 640 munin adm
# }
#

import logging
from json import loads
from telnetlib import Telnet
from sys import argv, exit
from re import sub


class TemPageR():

    def __init__(self):
        """
        Configure object and fetch data
        """

        # ##         ## #
        # Configuration #
        # ##         ## #

        # Munin graph
        self.graphTitle = "Server Room Temperatures"
        self.grapWarning = 28
        self.graphCritical = 30
        self.temperatureScale = "c"

        # Sensor IP or hostname
        self.temperatureSensor = ""

        # Logging
        self.logFile = '/var/log/munin/tempager.log'
        self.logLevel = logging.INFO
        self.outputTrace = True

        ##               ## #
        # Configuration End #
        ##               ## #

        # Variable Initializations
        self.temperatures = []

    def fetch(self):
        """
        Fetch data from TemPageR sensor
        """
        # The temperature sensor does not return a proper HTTP response when calling the /getData.html page
        # The sensor does not return any headers, and only the body which is a single line of bad JSON data
        # This means the python requests plugin does not know how to handle the data. Instead I chose to use
        # the telnetlib module, and just send a raw http response and grab the response.
        try:
            tn = Telnet(self.temperatureSensor, 80)
            tn.write("GET /getData.html".encode('ascii') + b"\n\n")
        except Exception as e:
            logging.error("Something happened, exception: {}".format(e), exc_info=self.outputTrace)
            exit(2)

        # Here the code read the telnet response and decode it into a text string from ascii
        text = tn.read_all().decode('ascii')

        # The sensor returns gibberish JSON data that needs to be cleaned up
        # before it's parseable. This regex code cleans up the JSON
        # Replace all '{name:' with '{"name":'
        text = sub(r"{([a-z]*):", r'{"\1":', text)
        # Replace all ',date:' with ',"date":'
        text = sub(r",([a-z]*)", r',"\1"', text)
        # The second regex line introduce a small error in
        # the JSON which we clean up here - replace ',""{' with ',{'
        text = sub(',""{', ',{', text)

        # After the cleanup, the string should be parseable as JSON
        try:
            temp = loads(text)
        except Exception as e:
            logging.error("Unable to parse JSON string: {}".format(e), exc_info=self.outputTrace)
            exit(2)

        # Extract all data and stuff it into a dict
        if isinstance(temp, dict):
            if 'sensor' in temp:
                for sensor in temp["sensor"]:
                    self.temperatures.append({
                        'label': sensor['label'],
                        'temp': sensor['tempf' if self.temperatureScale == 'f' else "tempc"]
                    })

    def printConfig(self):
        # Fetch data from TemPageR
        self.fetch()

        # Format graph metadata output
        output = """graph_title {}
graph_vlabel degrees {}
graph_args --base 1000 -l 0
graph_category sensors""".format(self.graphTitle, format('Fahrenheit' if self.temperatureScale == 'f' else "Celsius"))

        # Graph sensor template
        msg = """temp{sensorId}.label {label}
temp{sensorId}.warning {warn}
temp{sensorId}.critical {crit}"""

        # Build graph meta data
        msg = '\n'.join(msg.format(sensorId=sId,
                                   label=sensor['label'], 
                                   warn=self.grapWarning,
                                   crit=self.graphCritical) for sId, sensor in enumerate(self.temperatures))
        
        # Assemble and print output
        print('\n'.join([output, msg]))

    def printTemp(self):
        """
        Print munin readings
        """
        # Fetch data from TemPageR
        self.fetch()

        # Format output
        output = '\n'.join("temp{}.value {}".format(sensorId, sensor['temp']) for sensorId, sensor in enumerate(self.temperatures))

        # Print output
        print(output, end='')


if __name__ == '__main__':
    # Initialize TemPageR
    temPager = TemPageR()

    # Configure logging
    logging.basicConfig(level=temPager.logLevel, filemode='w', filename=temPager.logFile)

    # Output config options or temp data
    if (argv[1] if len(argv) == 2 else "") == "config":
        temPager.printConfig()
    else:
        temPager.printTemp()
