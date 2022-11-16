import cv2 as cv
import numpy as np

cap = cv.VideoCapture(0)

hsv_low = (95, 119, 13)
hsv_high = (138, 214, 205)

while True:
    f, fraps = cap.read()
    img = cv.cvtColor(fraps, cv.COLOR_BGR2HSV)

    thresh = cv.inRange(img, hsv_low, hsv_high)

    cv.imshow('prep', thresh)