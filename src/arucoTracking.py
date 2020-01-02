# Detection of ArUco markers
# https://docs.opencv.org/3.4.6/d5/dae/tutorial_aruco_detection.html
# https://dzone.com/articles/marker-tracking-via-websockets-with-raspberry-pi

import asyncio
import cv2
import concurrent
import logging
import math
import numpy as np

from picamera.array import PiRGBArray
from picamera import PiCamera

RESOLUTION = (1088,1088)
FRAMERATE = 30

DICTIONARY = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_250)

# pi cam
CAMERA_MATRIX = np.array([[2.01976721e+03, 0.00000000e+00, 1.32299009e+03],[0.00000000e+00, 2.00413989e+03, 8.60071427e+02],[0.00000000e+00, 0.00000000e+00, 1.00000000e+00]])
DIST_COEFFS = np.array([-0.63653859,  0.2963752,  0.03228459, 0.0028887, 0.82956323])

PARAMETERS =  cv2.aruco.DetectorParameters_create()
MARKER_EDGE = 0.05

def angles_from_rvec(rvec):
    r_mat, _jacobian = cv2.Rodrigues(rvec)
    a = math.atan2(r_mat[2][1], r_mat[2][2])
    b = math.atan2(-r_mat[2][0], math.sqrt(math.pow(r_mat[2][1],2) + math.pow(r_mat[2][2],2)))
    c = math.atan2(r_mat[1][0], r_mat[0][0])
    return [a,b,c]

def calc_heading(rvec):
    angles = angles_from_rvec(rvec)
    degree_angle =  math.degrees(angles[2])
    if degree_angle < 0:
        degree_angle = 360 + degree_angle
    return degree_angle

def find_markers(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    corners, ids, rejectedImgPoints = cv2.aruco.detectMarkers(gray, DICTIONARY, parameters=PARAMETERS)
    rvecs, tvecs, _objPoints = cv2.aruco.estimatePoseSingleMarkers(corners, MARKER_EDGE, CAMERA_MATRIX, DIST_COEFFS)

    result = set()
    if ids is None:
        return result

    for i in range(0, len(ids)):
        try:
            id = str(ids[i][0])

            marker = np.squeeze(corners[i])

            x0, y0 = marker[0]
            x2, y2 = marker[2]
            x = int((x0 + x2)/2)
            y = int((y0 + y2)/2)

            heading = calc_heading(rvecs[i][0])
            result.add((id, x, y, heading))
        except Exception:
            traceback.print_exc()

    return result

class PositioningSystem:
    def __init__(self, on_update):
        self._on_update = on_update

    def start(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._capture())
        loop.run_forever()

    async def _capture(self):

        camera = PiCamera()
        camera.resolution = RESOLUTION
        camera.framerate = FRAMERATE

        rawCapture = PiRGBArray(camera, size=RESOLUTION)

        asyncio.sleep(0.1)

        logging.info("Start capturing from pi camera.")
        try:
            for capture in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):

                frame = capture.array
                markers = find_markers(frame)
                rawCapture.truncate(0)

                for marker in markers:
                    await self._on_update(marker)

        except:
            logging.error("Capturing stopped with an error.")

        finally:
            camera.close()


# Create a limited thread pool.
executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

async def track(on_track):
    ps = PositioningSystem(on_track)

    loop = asyncio.get_event_loop()
    loop.run_in_executor(executor, ps.start)
    return ps
