import requests, json, time, os, asyncio
import numpy as np
import cv2
from common import *

img = cv2.imread("aria_cut.png")
y, x = 108, 960
h, w = img.shape[:2]
loop = asyncio.get_event_loop()
canvas = dataToImg(loop.run_until_complete(loadCanvas()), canvasShape)
block = canvas[y:y + h, x:x + w, :]

cv2.imshow("Block", block)
cv2.waitKey(0)