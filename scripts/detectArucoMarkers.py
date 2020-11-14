###########################
# Detect ArUco markers    #
###########################

# This script is used to detect and crop based on ArUco markers
# Created by Justin Miller on 4.13.2020
# Updated by Justin Miller on 11.13.2020

# USAGE:
# python3 detectArucoMarkers.py

# Import packages
import cv2
import cv2.aruco as aruco
import numpy as np

# Initialize table coordinates
dim = (640, 480)
tableCoords = [(0, 0), (dim[0]-1, 0), (dim[0]-1, dim[1]-1), (0, dim[1]-1)]

cap = cv2.VideoCapture(0)

while(True):

    # Capture video frame by frame
    ret, frame = cap.read()
    output1 = frame.copy()

    # Detect markers
    # `corners` is the list of corners returned in clockwise order: top left, top right, bottom right, bottom left
    # `ids` is a list of marker IDs of each of the detected markers
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    arucoDict = aruco.Dictionary_get(aruco.DICT_4X4_50)
    arucoParameters =  aruco.DetectorParameters_create()
    corners, ids, rejectedImgPoints = aruco.detectMarkers(gray, arucoDict, parameters=arucoParameters)
    #print(ids)

    # Display detected markers
    #if ids is not None:
        #output1 = aruco.drawDetectedMarkers(output1, corners, ids)

    # Make sure we found at least one markerId
    if ids is None:
        continue

    # Iterate through detected markers
    detectedMarkers = []
    for i in range(len(ids)):
        markerId = str(ids[i][0])
        marker = np.squeeze(corners[i])
        x0, y0 = marker[0]
        self.log("[DEBUG] Marker ID {}: {}".format(markerId, marker[0]))
        detectedMarkers.append([markerId, x0, y0])

    # Sort by marker ID (column 0)
    dm = np.array(detectedMarkers)
    dm = dm[dm[:,0].argsort(kind='mergesort')]

    print("{} ArUco markers detected".format(len(dm)))
    for i, m in enumerate(dm):
        print("MarkerId {} detected at ({}, {})".format(m[0], m[1], m[2]))

        # TODO: Display detected markers on output image...


    # Update coordinates if exactly 4 ArUco markers were found
    if len(dm) == 4:
        print("4 markers, update table coordinates")
        tableCoords = []
        for i, m in enumerate(dm):
            tableCoords.append((m[1], m[2]))
        print(tableCoords)

    # Apply projective transformation (also known as "perspective transformation" or "homography") to the
    # original image. This type of transformation was chosen because it preserves straight lines.
    # To do this, we first compute the transformational matrix (M) and then apply it to the original image.
    # The resulting frame will have an aspect ratio identical to the size (in pixels) of the foosball playing field
    origCoords = np.array(tableCoords, dtype="float32")
    finalCoords = np.array([tL, tR, bR, bL], dtype="float32")
    M = cv2.getPerspectiveTransform(origCoords, finalCoords)
    output2 = cv2.warpPerspective(origImg, M, dim)

    # Display the original and resulting frames
    cv2.imshow('Output1', output1)
    cv2.imshow('Output2', output2)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()
