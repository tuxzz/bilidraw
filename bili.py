import requests, json, time, os, asyncio, threading
import numpy as np
import cv2
from common import *

writePos = (80, 1028)

img = cv2.imread("aria_q.png")
mask = cv2.imread("aria_qmask.png")
mask = (~mask.transpose(2, 0, 1)[0]).astype(np.bool)
#mask = ~np.zeros(img.shape[:2], dtype = np.bool)
imgData = imgToData(img)

# load cookie and delete cookies that in blacklist
oCookiePathList = os.listdir("./accounts")
cookiePathList = []
cookieList = []
blacklistedCookieList = []
for cookies in oCookiePathList:
    if(os.path.splitext(cookies)[-1] != ".cookie"):
        continue
    cookiePathList.append(cookies)
    cookieList.append(loadCookie(os.path.join("./accounts", cookies)))
    del cookies
del oCookiePathList
if(os.path.isfile("black.json")):
    blacklistedCookieList = json.load(open("black.json", "r"))
    for x in blacklistedCookieList:
        if(x in cookiePathList):
            print("%s is blacklisted." % (x))
            i = cookiePathList.index(x)
            del cookieList[i], cookiePathList[i], i
        else:
            print("%s is not in cookieList and blacklisted." % (x))
        del x
if(len(cookieList) == 0):
    raise ValueError("No account available.")
cookieLock = threading.Lock()
print("********** Loaded %d cookie **********" % len(cookieList))

def placeIntoBlackList(cookieName):
    with cookieLock:
        assert not cookieName in blacklistedCookieList
        if(cookieName in cookiePathList):
            print("%s is blacklisted." % (cookieName))
            i = cookiePathList.index(cookieName)
            del cookieList[i], cookiePathList[i], i
        else:
            print("%s is not in cookieList and blacklisted." % (cookieName))
        blacklistedCookieList.append(cookieName)
        with open("black.json", "w") as f:
            f.write(json.dumps(blacklistedCookieList))

async def procressAccount(cookies, cookieName):
    timeRemain = await getTimeRemain(cookies, cookieName)
    if(timeRemain == "BLACKLIST"):
        placeIntoBlackList(cookieName)
        return
    latency = 1.0
    while(True):
        try:
            timeRemain = max(0.0, timeRemain - latency)
            if(timeRemain > 0.0):
                print("%s: Time remain: %lfs(Without latency %lfs)" % (cookieName, timeRemain, latency))
                await asyncio.sleep(timeRemain)
            
            t1 = time.time()
            print("%s: Woken up" % (cookieName))
            canvas = await loadCanvas()
            canvas = dataToImg(canvas, canvasShape)
            print("%s: Canvas Loaded" % (cookieName))
            (y, x), color = selectPix(canvas, img, mask, writePos)
            print("%s: Selected pixel x = %d, y = %d, color = %s" % (cookieName, x, y, color))
            dur = time.time() - t1
            latency = latency * 0.9 + dur * 0.1
            
            drawResult = await drawPix(x, y, color, cookies, cookieName)
            if(drawResult == "BLACKLIST"):
                placeIntoBlackList(cookieName)
                return
            elif(drawResult != "SKIP"):
                print("%s: Draw operation success." % (cookieName))
            timeRemain = await getTimeRemain(cookies, cookieName)
            if(timeRemain == "BLACKLIST"):
                placeIntoBlackList(cookieName)
                return
        except Exception as e:
            print("%s: Exception occurred => %s", (cookieName, str(e)))

async def main():
    loop = asyncio.get_event_loop()
    futureList = []
    for i, cookieName in enumerate(cookiePathList):
        futureList.append(asyncio.ensure_future(procressAccount(cookieList[i], cookieName)))
    print("Main: everything created.")
    while(True):
        newCookiePathList = os.listdir("./accounts")
        try:
            with cookieLock:
                if(os.path.isfile("black.json")):
                    blacklistedCookieList[:] = json.load(open("black.json", "r"))
                for cookiePath in newCookiePathList:
                    if(os.path.splitext(cookiePath)[-1] != ".cookie"):
                        continue
                    if((not cookiePath in cookiePathList) and (not cookiePath in blacklistedCookieList)):
                        cookies = loadCookie(os.path.join("./accounts", cookiePath))
                        cookieList.append(cookies)
                        cookiePathList.append(cookiePath)
                        futureList.append(asyncio.ensure_future(procressAccount(cookies, cookiePath)))
                        print("Main: Loaded new cookie %s" % (cookiePath))
                    elif(cookiePath in blacklistedCookieList):
                        print("Main: Rejected new cookie %s" % (cookiePath))
                    del cookiePath
        except Exception as e:
            print("Main: Exception when loading cookie => %s" % (str(e)))
        await asyncio.sleep(10)
    print("Main: About to exit.")

loop = asyncio.get_event_loop()
loop.run_until_complete(main())