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
names = None
devices = None
network = None
monitors = None

app = wx.App()
gui = Gui("Logic Simulator", path, names, devices, network, monitors)
gui.Show(True)
app.MainLoop()
