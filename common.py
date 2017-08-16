import requests, json, time, asyncio
import numpy as np
import cv2

canvasShape = 720, 1280

commonHeaders = {
    'Origin': 'https://live.bilibili.com',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.4',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://live.bilibili.com/pages/1702/pixel-drawing',
    'Connection': 'keep-alive',
}

colorTable = {
    # RGB
    "0": (0, 0, 0),
    "1": (255, 255, 255),
    "2": (170, 170, 170),
    "3": (85, 85, 85),
    "4": (251, 211, 199),
    "5": (255, 196, 206),
    "6": (250, 172, 142),
    "7": (255, 139, 131),
    "8": (244, 67, 54),
    "9": (233, 30, 99),
    "A": (226, 102, 158),
    "B": (156, 39, 176),
    "C": (103, 58, 183),
    "D": (63, 81, 181),
    "E": (0, 70, 112),
    "F": (5, 113, 151),
    "G": (33, 150, 243),
    "H": (0, 188, 212),
    "I": (59, 229, 219),
    "J": (151, 253, 220),
    "K": (22, 115, 0),
    "L": (5, 169, 60),
    "M": (137, 230, 66),
    "N": (215, 255, 7),
    "O": (255, 246, 209),
    "P": (248, 203, 140),
    "Q": (255, 235, 59),
    "R": (255, 193, 7),
    "S": (255, 152, 0),
    "T": (255, 87, 34),
    "U": (184, 63, 39),
    "V": (121, 85, 72),
}

nColorTable = {}
for k, v in colorTable.items():
    nColorTable[k] = v[::-1]
colorTable = nColorTable
del nColorTable

reversedColorTable = {}
for k, v in colorTable.items():
    reversedColorTable[v] = k
def _loadCanvasWrapper():
    return requests.get("https://api.live.bilibili.com/activity/v1/SummerDraw/bitmap", headers = commonHeaders, timeout = 10)
    
async def loadCanvas():
    loop = asyncio.get_event_loop()
    success = False
    iRetry = 0
    while(not success):
        if(iRetry > 0):
            print("Retry %d..." % iRetry)
        r = await loop.run_in_executor(None, _loadCanvasWrapper)
        if(r.status_code == 200):
            d = r.json()
            if(d["code"] == 0):
                success = True
            else:
                print("loadCanvas: Remote return code %d" % d["code"])
                await asyncio.sleep(3)
        else:
            print("loadCanvas: Remote return http code %d" % r.status_code)
            await ayncio.sleep(3)
        iRetry += 1
    return d["data"]["bitmap"]

def _getTimeRemainWrapper(cookies):
    return requests.get("http://api.live.bilibili.com/activity/v1/SummerDraw/status", headers = commonHeaders, cookies = cookies, timeout = 10)

async def getTimeRemain(cookies, cookieName):
    loop = asyncio.get_event_loop()
    success = False
    iRetry = 0
    while(not success):
        if(iRetry > 0):
            print("%s(getTimeRemain): Retry %d..." % (cookieName, iRetry))
        r = await loop.run_in_executor(None, _getTimeRemainWrapper, cookies)
        if(r.status_code == 200):
            d = r.json()
            if(d["code"] == 0):
                success = True
            else:
                print("%s(getTimeRemain): Remote return code %d" % (cookieName, d["code"]))
                await asyncio.sleep(1)
        else:
            print("%s(getTimeRemain): Remote return http code %d" % (cookieName, r.status_code))
            await asyncio.sleep(1)
        if(iRetry > 5 and d["code"] == -101):
            return "BLACKLIST"
        iRetry += 1
    return d["data"]["time"]

def _drawPixWrapper(payload, cookies):
    return requests.post("https://api.live.bilibili.com/activity/v1/SummerDraw/draw", headers = commonHeaders, data = payload, cookies = cookies, timeout = 10)

async def drawPix(x, y, data, cookies, cookieName):
    loop = asyncio.get_event_loop()
    assert len(data) == 1
    payload = {
        'x_min': x,
        'y_min': y,
        'x_max': x,
        'y_max': y,
        'color': data
    }
    success = False
    iRetry = 0
    while(not success):
        if(iRetry > 0):
            print("%s(drawPix): Retry %d..." % (cookieName, iRetry))
        r = await loop.run_in_executor(None, _drawPixWrapper, payload, cookies)
        if(r.status_code == 200):
            d = r.json()
            if(d["code"] == 0):
                return True
            elif(d["code"] == -101):
                print("%s(drawPix): Remote return code %d(Not login)" % (cookieName, d["code"]))
                await asyncio.sleep(3)
            elif(d["code"] == -400):
                print("%s(drawPix): Remote return code %d(Too fast)" % (cookieName, d["code"]))
                await asyncio.sleep(2)
            else:
                print("%s(drawPix): Remote return code %d(Unknown)" % (cookieName, d["code"]))
                await asyncio.sleep(3)
        else:
            print("%s(drawPix): Remote return http code %d" % (cookieName, r.status_code))
            await asyncio.sleep(3)
        if(iRetry > 5 and d["code"] == -101):
            return "BLACKLIST"
        elif(iRetry > 5 and d["code"] == -400):
            return "SKIP"
        iRetry += 1

def loadCookie(path):
    d = {}
    with open(path, "rb") as f:
        l = json.load(f)
        for x in l:
            d[x["name"]] = x["value"]
    return d

def dataToImg(data, shape):
    assert len(data) == shape[0] * shape[1]
    img = np.zeros((shape[0] * shape[1], 3), dtype = np.uint8)
    for i, x in enumerate(data):
        img[i] = colorTable[str(x)]
    return img.reshape(*shape, 3)

def imgToData(img):
    data = np.zeros(img.shape[0] * img.shape[1], dtype = np.uint8)
    img = img.reshape((img.shape[0] * img.shape[1], 3))
    for i, x in enumerate(img):
        data[i] = ord(reversedColorTable[tuple(x)])
    return data.tobytes().decode("utf-8")

def genDiffCache(canvas, img, mask, pos):
    cache = []
    assert mask.ndim == 2
    assert mask.shape == img.shape[:2]
    py, px = pos
    h, w = img.shape[:2]
    rect = canvas[py:py + h, px:px + w]
    idx = np.zeros((h, w, 2), dtype = np.int)
    for y in range(h):
        for x in range(w):
            idx[y, x] = (y, x)
    diff = idx[np.logical_and(np.any(rect != img, axis = 2), mask)]
    for y, x in diff:
        item = (y + py, x + px), reversedColorTable[tuple(img[y, x])]
        cache.append(item)
    
    return cache

def selectPixFromCache(cache):
    if(len(cache) == 0):
        return None
    iSelected = np.random.randint(len(cache))
    selected = cache[iSelected]
    del cache[iSelected]
    return selected, cache

def loadJsonImage(path):
    bitmap = json.load(open(path, "rb"))["bitmap"]
    img = np.zeros((*canvasShape, 3), dtype = np.uint8).reshape(canvasShape[0] * canvasShape[1], 3)
    mask = np.zeros(canvasShape, dtype = np.bool).reshape(canvasShape[0] * canvasShape[1])
    for i, x in enumerate(bitmap):
        if(x == "Z"):
            continue
        img[i] = colorTable[x]
        mask[i] = True
    return img.reshape((*canvasShape, 3)), mask.reshape(canvasShape)