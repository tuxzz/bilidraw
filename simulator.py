import requests, json, time, os, asyncio
import numpy as np
import cv2
from common import *

writePos = (80, 1028)

img = cv2.imread("aria_q.png")
mask = cv2.imread("aria_qmask.png")
mask = (~mask.transpose(2, 0, 1)[0]).astype(np.bool)
cv2.imwrite("omask.png", mask.astype(np.uint8) * 255)
imgData = imgToData(img)

async def main():
    canvas = dataToImg(await loadCanvas(), canvasShape)
    print("Canvas loaded")
    while True:
        (y, x), color = selectPix(canvas, img, mask, writePos)
        print("Selected pixel x = %d, y = %d, color = %s" % (x, y, color))
        canvas[y, x] = colorTable[color]
        cv2.imshow("", canvas)
        cv2.waitKey(1)
    cv2.waitKey(0)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())