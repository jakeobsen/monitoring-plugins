<!--
 Copyright 2019 Morten Jakobsen. All rights reserved.
 Use of this source code is governed by a BSD-style
 license that can be found in the LICENSE file.
-->

# Monitoring plugins

This is my collection of monitoring plugins for munin and nagios that i use for various things both at work and at home.

## temprager.py

This plugin was specifically written to extract temperature data from the AVTECH TemPageR 4E running firmware v2.6.0. I have no idea if it works with later version of the firmware the other products AVTECH makes. Use it at your own risk.

The plugin works with both nagios and munin.

It has a few configuration options:

`self.graphTitle`
Name of graph in munin.

`self.tempWarning`
Integer value defining the upper limit for a temperature warning of type `warning`.

`self.tempCritical`
Integer value defining the upper limit for a temperature warning of type `critical`.

`self.isCentigrade`
Boolean value defining whether to use Celsius or Fahrenheit. `True` = `Celsius` and `False` = `Fahrenheit`

`self.temperatureSensor`
IP or hostname of temperature sensor.

`self.logFile`
Path to logfile.

`self.logLevel`
The default loglevel og the plugin. Setting this to `logging.INFO` will disable logging.

`self.outputTrace`
Boolean value defining whether to output stack traces to logfiles in case an error happens.

## Logrotate

It is highly recommended to use logrotate to all logfiles generated.

The easiest way to do this is to add a file to `/etc/logrotate.d/SERVICENAME` with the following content:

```
/var/log/logfilename.log {
  daily
  missingok
  rotate 7
  compress
  notifempty
  create 644 USERNAME adm
}
```

Replace USERNAME with the username of the service it runs as and replace in the logrotate filename with the name of the service.