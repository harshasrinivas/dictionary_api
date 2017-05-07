import cv2
import argparse
from operator import xor
import imutils
import pickle

def callback(value):
    pass


def setup_trackbars(range_filter):
    cv2.namedWindow("Trackbars", 0)

    for i in ["MIN", "MAX"]:
        v = 0 if i == "MIN" else 255

        for j in range_filter:
            cv2.createTrackbar("%s_%s" % (j, i), "Trackbars", v, 255, callback)


def get_trackbar_values(range_filter):
    values = []

    for i in ["MIN", "MAX"]:
        for j in range_filter:
            v = cv2.getTrackbarPos("%s_%s" % (j, i), "Trackbars")
            values.append(v)

    return values


def main():
    range_filter = "HSV"
    camera = cv2.VideoCapture(0)

    setup_trackbars(range_filter)

    while True:
        ret, image = camera.read()

        if not ret:
            break
        image = imutils.resize(image, width = 2000)
        frame_to_thresh = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        v1_min, v2_min, v3_min, v1_max, v2_max, v3_max = get_trackbar_values(range_filter)
        thresh = cv2.inRange(frame_to_thresh, (v1_min, v2_min, v3_min), (v1_max, v2_max, v3_max))

        cv2.imshow("Original", imutils.resize(image, width = 600))
        cv2.imshow("Thresh", imutils.resize(thresh, width = 600))

        if cv2.waitKey(1) & 0xFF is ord('q'):
			thresh_vals = ((v1_min, v2_min, v3_min), (v1_max, v2_max, v3_max))
			with open('threshold.pickle', 'w') as handle:
				pickle.dump(thresh_vals, handle, protocol=pickle.HIGHEST_PROTOCOL)
			#handle.close()
			print v1_min, v1_max, v2_min, v2_max, v3_min, v3_max
			break


if __name__ == '__main__':
    main()
