import sys
import ctypes
from time import sleep
import logging
import win32gui
import win32api
from threading import Thread
import re

class MessageBox:
    def mBox(self, title, text):
        # create a message box with topmost style
        ctypes.windll.user32.MessageBoxW(0, text, title, 0x1000)
        return

    def windowEnumerationCallback(self, hwnd, lparam):
        lparam.append((hwnd, win32gui.GetWindowText(hwnd), win32gui.GetWindowRect(hwnd)))

    def getWindow(self, title):
        results = []
        windows = []
        win32gui.EnumWindows(self.windowEnumerationCallback, windows)
        for window in windows:
            if title in window[1]:
                return (window[0], window[2])
        return None

    def getMonitors(self):
        return win32api.EnumDisplayMonitors(None, None)

    def getActiveMonitor(self):
        # MonitorFromWindow constants 
        # https://msdn.microsoft.com/en-us/library/dd145064
        MONITOR_DEFAULTTONULL    = 0
        MONITOR_DEFAULTTOPRIMARY = 1
        MONITOR_DEFAULTTONEAREST = 2
        winID = ctypes.windll.user32.GetForegroundWindow()
        monitorID = ctypes.windll.user32.MonitorFromWindow(winID, 
                MONITOR_DEFAULTTONEAREST)
        return monitorID

    def moveMessageBoxToActiveMonitor(self, windowHwnd, monitorID, monitors, windowRectangle):
        width = windowRectangle[2] - windowRectangle[0]
        height = windowRectangle[3] - windowRectangle[1]
        for monitor in monitors:
            if monitor[0].__int__() == monitorID:
                xMin, yMin, xMax, yMax = monitor[2]
                xMid = (xMin + xMax)//2
                yMid = (yMin + yMax)//2
                ctypes.windll.user32.MoveWindow(windowHwnd, xMid - width//2, yMid - height//2, width, height, True)

    def displayMessageBox(self, title, content):
        monitorID = self.getActiveMonitor()
        t1 = Thread(target=self.mBox, args = (title, content))
        t1.start()
        sleep(0.5)
        window, windowRectangle = self.getWindow(title)
        self.moveMessageBoxToActiveMonitor(window, monitorID, self.getMonitors(), windowRectangle)
        return t1
