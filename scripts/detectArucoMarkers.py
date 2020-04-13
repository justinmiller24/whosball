###########################
# Detect ArUco markers    #
###########################

# This script is used to detect ArUco markers
# Created by Justin Miller on 4.13.2020

# USAGE:
# python3 detectArucoMarkers.py

# Import packages
import cv2
import cv2.aruco as aruco
import numpy as np


def findMarkerCenters(frame, arucoDictionary, arucoParameters):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    corners, ids, rejectedImgPoints = cv2.aruco.detectMarkers(gray, arucoDictionary, parameters=arucoParameters)

    result = set()
    if ids is None:
        return result

    for i in range(0, len(ids)):
        id = str(ids[i][0])

        marker = np.squeeze(corners[i])

        x0, y0 = marker[0]
        x2, y2 = marker[2]
        x = int((x0 + x2)/2)
        y = int((y0 + y2)/2)

        result.add((id, x, y))

    return result


cap = cv2.VideoCapture(0)

while(True):

    # Capture video frame by frame
    ret, frame = cap.read()
    output = frame.copy()

    # Detect markers
    # `corners` is the list of corners returned in clockwise order: top left, top right, bottom right, bottom left
    # `ids` is a list of marker IDs of each of the detected markers
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    arucoDict = aruco.Dictionary_get(aruco.DICT_4X4_50)
    arucoParameters =  aruco.DetectorParameters_create()
    corners, ids, rejectedImgPoints = aruco.detectMarkers(gray, arucoDict, parameters=arucoParameters)
    #print(ids)

    # Display detected markers
    if ids is not None:
        output = aruco.drawDetectedMarkers(output, corners, ids)

    # Display the resulting frame
    cv2.imshow('Output', output)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()
