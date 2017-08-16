import requests, json, time, os, asyncio
import numpy as np
import cv2
from common import *

writePos = (80, 1028)

img = cv2.imread("aria_q.png")
mask = cv2.imread("aria_qmask.png")
mask = (~mask.transpose(2, 0, 1)[0]).astype(np.bool)
#mask = ~np.zeros(img.shape[:2], dtype = np.bool)
imgData = imgToData(img)

async def main():
    canvas = dataToImg(await loadCanvas(), canvasShape)
    diffCache = genDiffCache(canvas, img, mask, writePos)
    print("Canvas loaded")
    while True:
        if(len(diffCache) == 0):
            break
        ((y, x), color), _ = selectPixFromCache(diffCache)
        print("Selected pixel x = %d, y = %d, color = %s, Unpainted %d" % (x, y, color, len(diffCache)))
        canvas[y, x] = colorTable[color]
        cv2.imshow("", canvas)
        cv2.waitKey(1)
    cv2.waitKey(0)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())