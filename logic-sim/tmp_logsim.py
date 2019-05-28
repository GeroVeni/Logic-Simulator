#!/usr/bin/env python3
"""
Temporary script for working with gui before the parse.py is complete
"""

import getopt
import sys

import wx

from names import Names
from devices import Devices
from network import Network
from monitors import Monitors
from scanner import Scanner
from parse import Parser
from userint import UserInterface
from gui import Gui

path = "a"
# Initialise instances of the four inner simulator classes
names = Names()
devices = Devices(names)
network = Network(names, devices)
monitors = Monitors(names, devices, network)

# Add dummy singal traces
device_id = ["A", "B", "C", "D", "E", "F", "G", "H","I", "J", "K"]
output_id = ["1", "2"]
monitors.monitors_dictionary[(device_id[0], output_id[0])] = [
    monitors.devices.HIGH, monitors.devices.HIGH, monitors.devices.LOW,
    monitors.devices.RISING, monitors.devices.HIGH, monitors.devices.BLANK,
    monitors.devices.BLANK, monitors.devices.LOW, monitors.devices.HIGH,
    monitors.devices.LOW, monitors.devices.LOW, monitors.devices.LOW,
    monitors.devices.LOW, monitors.devices.LOW, monitors.devices.LOW,
    monitors.devices.HIGH]
monitors.monitors_dictionary[(device_id[1], output_id[1])] = [
    monitors.devices.LOW, monitors.devices.LOW, monitors.devices.HIGH,
    monitors.devices.LOW, monitors.devices.BLANK, monitors.devices.LOW,
    monitors.devices.RISING]
monitors.monitors_dictionary[(device_id[2], output_id[1])] = [
    monitors.devices.LOW, monitors.devices.LOW, monitors.devices.HIGH,
    monitors.devices.LOW, monitors.devices.BLANK, monitors.devices.LOW,
    monitors.devices.RISING]
monitors.monitors_dictionary[(device_id[3], output_id[1])] = [
    monitors.devices.LOW, monitors.devices.LOW, monitors.devices.HIGH,
    monitors.devices.LOW, monitors.devices.BLANK, monitors.devices.LOW,
    monitors.devices.RISING]
monitors.monitors_dictionary[(device_id[4], output_id[1])] = [
    monitors.devices.LOW, monitors.devices.LOW, monitors.devices.HIGH,
    monitors.devices.LOW, monitors.devices.BLANK, monitors.devices.LOW,
    monitors.devices.RISING]
monitors.monitors_dictionary[(device_id[5], output_id[1])] = [
    monitors.devices.LOW, monitors.devices.LOW, monitors.devices.HIGH,
    monitors.devices.LOW, monitors.devices.BLANK, monitors.devices.LOW,
    monitors.devices.RISING]
# monitors.monitors_dictionary[(device_id[6], output_id[0])] = [
#     monitors.devices.HIGH, monitors.devices.HIGH, monitors.devices.LOW,
#     monitors.devices.RISING, monitors.devices.HIGH, monitors.devices.BLANK,
#     monitors.devices.BLANK, monitors.devices.LOW, monitors.devices.HIGH,
#     monitors.devices.LOW, monitors.devices.LOW, monitors.devices.LOW,
#     monitors.devices.LOW, monitors.devices.LOW, monitors.devices.LOW,
#     monitors.devices.HIGH]
# monitors.monitors_dictionary[(device_id[7], output_id[0])] = [
#     monitors.devices.HIGH, monitors.devices.HIGH, monitors.devices.LOW,
#     monitors.devices.RISING, monitors.devices.HIGH, monitors.devices.BLANK,
#     monitors.devices.BLANK, monitors.devices.LOW, monitors.devices.HIGH,
#     monitors.devices.LOW, monitors.devices.LOW, monitors.devices.LOW,
#     monitors.devices.LOW, monitors.devices.LOW, monitors.devices.LOW,
#     monitors.devices.HIGH]
# monitors.monitors_dictionary[(device_id[8], output_id[0])] = [
#     monitors.devices.HIGH, monitors.devices.HIGH, monitors.devices.LOW,
#     monitors.devices.RISING, monitors.devices.HIGH, monitors.devices.BLANK,
#     monitors.devices.BLANK, monitors.devices.LOW, monitors.devices.HIGH,
#     monitors.devices.LOW, monitors.devices.LOW, monitors.devices.LOW,
#     monitors.devices.LOW, monitors.devices.LOW, monitors.devices.LOW,
#     monitors.devices.HIGH]
#
# monitors.monitors_dictionary[(device_id[9], output_id[0])] = [
#     monitors.devices.HIGH, monitors.devices.HIGH, monitors.devices.LOW,
#     monitors.devices.RISING, monitors.devices.HIGH, monitors.devices.BLANK,
#     monitors.devices.BLANK, monitors.devices.LOW, monitors.devices.HIGH,
#     monitors.devices.LOW, monitors.devices.LOW, monitors.devices.LOW,
#     monitors.devices.LOW, monitors.devices.LOW, monitors.devices.LOW,
#     monitors.devices.HIGH]
# monitors.monitors_dictionary[(device_id[10], output_id[0])] = [
#     monitors.devices.HIGH, monitors.devices.HIGH, monitors.devices.LOW,
#     monitors.devices.RISING, monitors.devices.HIGH, monitors.devices.BLANK,
#     monitors.devices.BLANK, monitors.devices.LOW, monitors.devices.HIGH,
#     monitors.devices.LOW, monitors.devices.LOW, monitors.devices.LOW,
#     monitors.devices.LOW, monitors.devices.LOW, monitors.devices.LOW,
#     monitors.devices.HIGH]

app = wx.App()
gui = Gui("Logic Simulator", path, names, devices, network, monitors)
gui.Show(True)
app.MainLoop()
