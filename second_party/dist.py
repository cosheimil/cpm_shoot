import cv2 as cv

DIST_ONE_M = 630

tresh_high = (150, 150, 255)
tresh_low = (0, 0, 0)

photo = cv.imread("./img/cross.jpg")
cv.imshow("orig", photo)
only_object = cv.inRange(photo, tresh_low, tresh_high)
moment = cv.moments(only_object, 1)
area = int(moment["m00"])
print(area / DIST_ONE_M * 1)
cv.waitKey(0)
