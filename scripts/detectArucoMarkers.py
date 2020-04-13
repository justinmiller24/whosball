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


def findMarkers(frame, arucoDictionary, arucoParameters):
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

    # Capture frame-by-frame
    ret, frame = cap.read()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    arucoDict = aruco.Dictionary_get(aruco.DICT_6X6_250)
    arucoParameters =  aruco.DetectorParameters_create()

    #lists of ids and the corners beloning to each id

    # "markerCorners" is the list of corners of the detected markers.
    # For each marker, its four corners are returned in their original order (which is clockwise starting with top left).
    # So, the first corner is the top left corner, followed by the top right, bottom right and bottom left.
    # "markerIds" is the list of ids of each of the detected markers in markerCorners.
    # Note that the returned markerCorners and markerIds vectors have the same size.
    corners, ids, rejectedImgPoints = aruco.detectMarkers(gray, arucoDict, parameters=arucoParameters)
    print(corners)

    if len(ids) > 0:
        #gray = aruco.drawDetectedMarkers(gray, corners)
        frameMarkers = aruco.drawDetectedMarkers(frame.copy(), corners, ids)

    # Display the resulting frame
    cv2.imshow('frame', frameMarkers)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()
