import cv2
import numpy as np


def userInput():
    return cv2.waitKey(1) & 0xFF


# Function to update video display
def updateDisplay(images, ballLocation, ballRadius, ballDistance, ballDirection, ballSpeed):

    # Grab dimensions of first image
    (h, w) = images[0].shape[:2]

	# Construct multiview display
    mvHeight = (h * 2) + (20) + (20 + 3) + (20 + 3)
    mvWidth = (w * 2) + 9
    output = np.zeros((mvHeight, mvWidth, 3), dtype="uint8")

    # Top Left
    cv2.putText(output, "Original", (280, 15), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)
    output[20:h+20, 3:w+3] = images[0]

	# Top Right
    cv2.putText(output, "Grayscale", (880, 15), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)
    output[20:h+20, w+6:w * 2 + 6] = images[1]

	# Bottom Left
    cv2.putText(output, "Mask", (280, 20+h+3+15), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)
    output[h+3+20+20:h*2+3+20+20, 3:w+3] = images[2]

	# Bottom Right
    cv2.putText(output, "Output", (880, 20+h+3+15), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)
    output[h+3+20+20:h*2+3+20+20, w+6:w * 2 + 6] = images[3]

	# Bottom
    cDisplay = ("{}".format(ballLocation)) if ballLocation is not None else "-"
    rDisplay = ("%2.1f" % ballRadius) if ballRadius is not None else "-"
    dDisplay = ("%2.1f" % ballDistance) if ballDistance is not None else "-"
    aDisplay = ("%2.1f" % ballDirection) if ballDirection is not None else "-"
    vDisplay = "-"
    cv2.putText(output, "Center: %s" % cDisplay, (90, mvHeight - 5), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)
    cv2.putText(output, "Radius: %s" % rDisplay, (290, mvHeight - 5), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)
    cv2.putText(output, "Distance: %s" % dDisplay, (420, mvHeight - 5), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)
    cv2.putText(output, "Direction: %s" % aDisplay, (620, mvHeight - 5), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)
    cv2.putText(output, "Velocity: %s" % vDisplay, (820, mvHeight - 5), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)

    return output
