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

from json import loads
from telnetlib import Telnet
from sys import argv, exit
from re import sub

class TemPageR():

    def __init__(self):
        """
        Configure object and fetch data
        """
        # Configuration
        self.graphTitle = "Server Room Temperatures"
        self.grapWarning = 27
        self.graphCritical = 30

        # Sensor IP
        self.temperatureSensor = ""

        # Initialization
        self.temperatures = {}
        self.fetch()


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
            print("Unable to connect ({})".format(e))
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
            temp = None
            print("Unable to parse JSON string ({})".format(e))
            exit(2)

        # Extract all data and stuff it into a dict
        if type(temp) is dict:
            if 'sensor' in temp:
                i = 0
                for sensor in temp["sensor"]:
                    self.temperatures[i] = {
                        'label': sensor['label'],
                        'tempc': sensor['tempc']
                    }
                    i += 1


    def printConfig(self):
        """
        Print munin config
        """
        print("graph_title {}".format(self.graphTitle))
        print("graph_vlabel degrees Celsius")
        print("graph_args --base 1000 -l 0")
        print("graph_category sensors")
        for sensorId,sensor in self.temperatures.items():
            print("temp{}.label {}".format(sensorId, sensor['label']))
            print("temp{}.warning {}".format(sensorId, self.grapWarning))
            print("temp{}.critical {}".format(sensorId, self.graphCritical))

    def printTemp(self):
        """
        Print munin readings
        """
        for sensorId,sensor in self.temperatures.items():
            print("temp{}.value {}".format(sensorId, sensor['tempc']))


if __name__ == '__main__':
    mode = argv[1] if len(argv) == 2 else ""

    temPager = TemPageR()

    if mode == "config":
        temPager.printConfig()
    else:
        temPager.printTemp()
