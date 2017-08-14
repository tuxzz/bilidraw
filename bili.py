import requests, json, time, os, asyncio, threading
import numpy as np
import cv2
from common import *

writePos = (108, 960)

img = cv2.imread("aria_cut.png")
mask = cv2.imread("aria_mask.png")
mask = (~mask.transpose(2, 0, 1)[0]).astype(np.bool)
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

def selectPix(canvas, img, mask, pos):
    assert mask.ndim == 2
    assert mask.shape == img.shape[:2]
    py, px = pos
    h, w = img.shape[:2]
    rect = canvas[py:py + h, px:px + w]
    idx = np.zeros((h, w, 2), dtype = np.int)
    for y in range(h):
        for x in range(w):
            idx[y, x] = (y, x)
    diff = idx[np.logical_and(np.all(rect != img, axis = 2), mask)]
    
    if(len(diff) == 0):
        return 0, 0, A
    
    """# cut block
    blockSize = 16
    nBlock = int(np.ceil(h / blockSize)) * int(np.ceil(w / blockSize))
    blockList = [[] for i in range(nBlock)]
    for y, x in diff:
        iBlock = int(y / blockSize) * int(x / blockSize)
        blockList[iBlock].append((y, x))
    nBlockList = [x for x in blockList if len(x) > (blockSize * blockSize // 16)]
    if(len(nBlockList) == 0):
        blockList = [x for x in blockList if len(x) > 0]
    else:
        blockList = nBlockList
    del nBlockList
    
    # select from block
    if(len(blockList) > 1):
        iSelectedBlock = np.random.randint(0, min(len(blockList), 2))
    else:
        iSelectedBlock = 0
    iSelected = np.random.randint(len(blockList[iSelectedBlock]))
    selected = blockList[iSelectedBlock][iSelected]"""
    
    iSelected = np.random.randint(len(diff))
    selected = diff[iSelected]
    
    upRatio = diff.shape[0] / (img.shape[0] * img.shape[1])
    print("Unpainted %d of %d(%d unmasked)(%f%%)" % (diff.shape[0], img.shape[0] * img.shape[1], np.sum(mask), upRatio * 100))
    return (selected[0] + py, selected[1] + px), reversedColorTable[tuple(img[selected[0], selected[1]])]

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