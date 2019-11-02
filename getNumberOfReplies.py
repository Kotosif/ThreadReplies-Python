import sys
import ctypes
import requests
import json
from time import sleep
import logging
import win32gui
import win32api
from threading import Thread
import re
from pushover import init, Client
from dotenv import load_dotenv
from os import getenv

def mBox(title, text):
    #create a message box with topmost style
    ctypes.windll.user32.MessageBoxW(0, text, title, 0x1000)
    return

def convertURL(text):
    if (text.endswith('json')):
            return text
    tokens = text.split('/')
    url = "http://a.4cdn.org/a/thread/"+tokens[-1]+".json"
    return url

def windowEnumerationCallback(hwnd, lparam):
    lparam.append((hwnd, win32gui.GetWindowText(hwnd), win32gui.GetWindowRect(hwnd)))

def getWindow(title):
    results = []
    windows = []
    win32gui.EnumWindows(windowEnumerationCallback, windows)
    for window in windows:
        if title in window[1]:
            return (window[0], window[2])
    return None

def getMonitors():
    return win32api.EnumDisplayMonitors(None, None)

def getActiveMonitor():
    # MonitorFromWindow constants 
    # https://msdn.microsoft.com/en-us/library/dd145064
    MONITOR_DEFAULTTONULL    = 0
    MONITOR_DEFAULTTOPRIMARY = 1
    MONITOR_DEFAULTTONEAREST = 2
    winID = ctypes.windll.user32.GetForegroundWindow()
    monitorID = ctypes.windll.user32.MonitorFromWindow(winID, 
            MONITOR_DEFAULTTONEAREST)
    return monitorID

def moveMessageBoxToActiveMonitor(windowHwnd, monitorID, monitors, windowRectangle):
    width = windowRectangle[2] - windowRectangle[0]
    height = windowRectangle[3] - windowRectangle[1]
    for monitor in monitors:
        if monitor[0].__int__() == monitorID:
            xMin, yMin, xMax, yMax = monitor[2]
            xMid = (xMin + xMax)//2
            yMid = (yMin + yMax)//2
            ctypes.windll.user32.MoveWindow(windowHwnd, xMid - width//2, yMid - height//2, width, height, True)

def displayMessageBox(title, content):
    monitorID = getActiveMonitor()
    t1 = Thread(target=mBox, args = (title, content))
    t1.start()
    sleep(0.5)
    window, windowRectangle = getWindow(title)
    moveMessageBoxToActiveMonitor(window, monitorID, getMonitors(), windowRectangle)
    return t1

def checkThreadPostCount(parsed_json):
    global thread_limit_reached_message_displayed
    number = parsed_json["posts"][0]["replies"]
    intNum = int(number)
    print( intNum )
    if intNum > LIMIT:
        t1 = displayMessageBox(title="WWD Postcount Alert", content=("Post count is more than %d" % LIMIT))
        t1.join()
        thread_limit_reached_message_displayed = True
    else:
        print("Not over limit yet")

def delayAndroidPushNotifications():
    global startup_delay_passed
    sleep(300)
    startup_delay_passed = True

def signupChecker(parsed_json, seen_posts, checkpoint, client):
    global startup_delay_passed
    # Collate the number of requests each post has
    posts = parsed_json["posts"][checkpoint:] # Start from a checkpoint
    reply_counter = {}
    for post in posts:
        if "com" in post:
            comment = post["com"]
            matches = re.findall(r"#p(\d+)\"", comment)
            for match in matches:
                if match in reply_counter:
                    reply_counter[match].append(post["no"])
                    if len(reply_counter[match]) > 2 and not match in seen_posts:
                        seen_posts.append(match)
                        if startup_delay_passed:
                            title = "WWD Signup Alert"
                            content = "Post number %s potentially a signup request\nPost:\n%s" % (match, comment)
                            t1 = displayMessageBox(title=title, content=content)
                            if not client is None:
                                # Send push notification
                                client.send_message(content, title=title)

                else:
                    reply_counter[match] = [post["no"]]
    # print(seen_posts)
    return max(parsed_json["posts"][0]["replies"] - 5, 1)
        

#Main
load_dotenv()
LIMIT = 495
filename = "url.txt"
logfilename = "log.txt"

logfile = open(logfilename, 'w').close() # Clear log file
logging.basicConfig(format='%(asctime)s %(message)s', filename=logfilename, 
        level=logging.ERROR)
text = open(filename, 'r')
url = text.read()
url = convertURL(url)

# Store which posts we've already marked as potential signups
seen_posts = []
checkpoint = 1 # 1 to ignore OP post

startup_delay_passed = False
thread_limit_reached_message_displayed = False

startup_delay_thread = Thread(target=delayAndroidPushNotifications, args=())
startup_delay_thread.daemon = True
startup_delay_thread.start()

# Initialise Pushover Client
client = None
try:
    client = Client(getenv("USER_KEY"), api_token=getenv("API_TOKEN"), device=getenv("DEVICE"))
    print("Pushover client initialised successfully")
except:
    logging.exception("An exception occured. Stack trace below")

while True:
    try:
        response = requests.get(url)
        parsed_json = json.loads(response.text)
        if not thread_limit_reached_message_displayed:
            checkThreadPostCount(parsed_json)
        checkpoint = signupChecker(parsed_json, seen_posts, checkpoint, client)
        sleep(10)
    except Exception:
        # The stack trace and exception will get captured and printed
        logging.exception("An exception occured. Stack trace below")
        sleep(2)

