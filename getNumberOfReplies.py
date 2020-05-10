import sys
import requests
import json
from time import sleep
import logging
from threading import Thread
import re
from pushover import init, Client
from dotenv import load_dotenv
from os import getenv
from html2text import html2text
from messagebox import MessageBox

def convertURL(text):
    if (text.endswith('json')):
            return text
    tokens = text.strip().split('/')
    url = "http://a.4cdn.org/a/thread/"+tokens[-1]+".json"
    return url

def checkThreadPostCount(parsed_json, client, messageBox):
    global thread_limit_reached_message_displayed
    number = parsed_json["posts"][0]["replies"]
    intNum = int(number)
    print(intNum)
    if intNum > LIMIT:
        title = "WWD Postcount Alert"
        content = ("Post count is more than %d" % LIMIT)
        t1 = messageBox.displayMessageBox(title=title, content=content)
        t1.join()
        if not client is None:
            # Send push notification
            client.send_message(content, title=title)
        thread_limit_reached_message_displayed = True
    else:
        print("Not over limit yet")

def delaySignUpNotifications():
    global startup_delay_passed
    sleep(300)
    startup_delay_passed = True

def searchPostByNo(posts, no):
    for post in posts:
        if post['no'] == no:
            return post

def stripReplyTags(comment):
    return re.sub(r">>\d+(  |\n)*", "", html2text(comment).strip())

def containsPhrases(phrases, comment):
    strippedComment = stripReplyTags(comment)
    for phrase in phrases:
        if len(re.findall(phrase, strippedComment)) > 0:
            return True
    return False

def containsSignUpPhrases(comment):
    signup_phrases = [r"(w|W)ho (wants|up) ", r"I'll pick one", r"link ref", r"Waifu \+ .+\?"]
    return containsPhrases(signup_phrases, comment)

def excludesPhrases(comment):
    exclude_phrases = [r"^(p|P)ost ", r"(?i)wips?"]
    return not containsPhrases(exclude_phrases, comment)

def signupChecker(startup_delay_passed, parsed_json, seen_posts, checkpoint, client, messageBox):
    # Collate the number of requests each post has
    posts = parsed_json["posts"][checkpoint:] # Start from a checkpoint
    reply_counter = {}
    for post in posts:
        if "com" in post:
            comment = post["com"]
            matches = re.findall(r"#p(\d+)\"", comment)
            for match in matches:
                if match in reply_counter:
                    reply_counter[match]['replies'].append(post["no"])
                    parentComment = reply_counter[match]['comment']
                    if not match in seen_posts and ((len(reply_counter[match]['replies']) > 0 and containsSignUpPhrases(parentComment)) or \
                    (len(reply_counter[match]['replies']) > 2 and excludesPhrases(parentComment))):
                        seen_posts.append(match)
                        if startup_delay_passed:
                            title = "WWD Signup Alert"
                            content = "Post number %s potentially a signup request\nPost:\n%s" % (match, html2text(parentComment))
                            t1 = messageBox.displayMessageBox(title=title, content=content)
                            if not client is None:
                                # Send push notification
                                client.send_message(content, title=title)
                else:
                    parentPost = searchPostByNo(parsed_json["posts"], int(match))
                    if not parentPost is None:
                        parentComment = ""
                        if 'com' in parentPost:
                            parentComment = parentPost['com']
                        reply_counter[match] = {'comment': parentComment, 'replies': []}
                        reply_counter[match]['replies'].append(post["no"])
    # print(seen_posts)
    return max(parsed_json["posts"][0]["replies"] - 5, 1)

# Global variables
thread_limit_reached_message_displayed = False
startup_delay_passed = False

# Main
if __name__ == "__main__":
    load_dotenv()
    LIMIT = 495
    filename = "url.txt"
    logfilename = "log.txt"
    SEND_PUSH_NOTIFICATIONS = False

    logfile = open(logfilename, 'w').close() # Clear log file
    logging.basicConfig(format='%(asctime)s %(message)s', filename=logfilename, 
            level=logging.ERROR)

    text = open(filename, 'r')
    url = text.read()
    url = convertURL(url)

    seen_posts = [] # Store which posts we've already marked as potential signups
    checkpoint = 1 # 1 to ignore OP post

    startup_delay_thread = Thread(target=delaySignUpNotifications, args=())
    startup_delay_thread.daemon = True
    startup_delay_thread.start()

    messageBox = MessageBox()

    # Initialise Pushover Client
    client = None
    if SEND_PUSH_NOTIFICATIONS:
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
                checkThreadPostCount(parsed_json, client, messageBox)
            checkpoint = signupChecker(startup_delay_passed, parsed_json, seen_posts, checkpoint, client, messageBox)
            sleep(10)
        except Exception:
            # The stack trace and exception will get captured and printed
            logging.exception("An exception occured. Stack trace below")
            sleep(2)