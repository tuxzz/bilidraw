import requests, json, time, os, asyncio
import numpy as np
import cv2
from common import *

img = cv2.imread("th.png")
y, x = 544, 936
h, w = img.shape[:2]
loop = asyncio.get_event_loop()
canvas = dataToImg(loop.run_until_complete(loadCanvas()), canvasShape)
block = canvas[y:y + h, x:x + w, :]

cv2.imshow("Block", block)
cv2.waitKey(0)