import numpy as np
import cv2
import imutils
from PIL import Image
import pytesseract
from autocorrect import spell
import requests
import json
import pyttsx
import pickle

with open('threshold.pickle', 'rb') as handle:
    val = pickle.load(handle)
orangeLower = val[0]
orangeUpper = val[1]

def clean(word):
	new_word = ""
	for c in word:
		if c.isalpha() or c == ' ':
			new_word += c
	return new_word.split(' ')[0]

def process(find_meaning = False):
	frame = cv2.imread('image.jpg')
	frame = imutils.resize(frame, width=2000)
	img = imutils.resize(frame, width = 2000)

	#HSV and threshold
	hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
	mask = cv2.inRange(hsv, orangeLower, orangeUpper)
	cv2.imwrite("step0.jpg", mask)


	#Erosion and dilation
	#Make this dynamic?
	mask = cv2.erode(mask, None, iterations=2)
	mask = cv2.dilate(mask, None, iterations=5)

	#Detect cue
	cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
	center = None

	x_main = 0
	y_main = 0
	if len(cnts) > 0:
		# find the largest contour in the mask, then use
		# it to compute the minimum enclosing circle and
		# centroid
		c = max(cnts, key=cv2.contourArea)
		((x, y), radius) = cv2.minEnclosingCircle(c)
		M = cv2.moments(c)
		center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
		# only proceed if the radius meets a minimum size
		if radius > 5:
			rect = cv2.minAreaRect(c)
			box = cv2.boxPoints(rect)
			box = np.int0(box)
			Ys = [i[1] for i in box]
			y_main = min(Ys)
			cv2.drawContours(frame,[box],0,(0,255,0),2)
	        # draw the circle and centroid on the frame,
	        # then update the list of tracked points
	        cv2.circle(frame, center, 5, (0, 0, 255), -1)

	#Word detection starts here
	image = cv2.medianBlur(img,7)
	th = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY);
	th1 = cv2.adaptiveThreshold(th,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,\
	            cv2.THRESH_BINARY_INV,11,2)
	cv2.imwrite("step1.jpg", th1)

	#Erode and dilate
	th1 = cv2.erode(th1, None, iterations = 1)
	th1 = cv2.dilate(th1, None, iterations = 6)
	cv2.imwrite('step2.jpg', th1)
	im2, cnts, hierarchy = cv2.findContours(th1.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

	#Getting the desired word out of all contours
	word_x = 0
	word_y = 0
	dist = 99999999
	fin_label = -1
	final_cnt = None
	for c in cnts:
		if cv2.contourArea(c) > 100000 or cv2.contourArea(c) < 500:
			continue
		M = cv2.moments(c)
		rect = cv2.minAreaRect(c)
		box = cv2.boxPoints(rect)
		box = np.int0(box)
		cv2.drawContours(frame,[box],0,(0,255,0),2)
		center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
		if(center[1] < y_main and (x - center[0])**2 + (y - center[1])**2 < dist ):
			#print center[0], center[1]
			dist = (x - center[0])**2 + (y - center[1])**2
			final_cnt = c

	#This is the bounding rect on image
	rect = cv2.minAreaRect(final_cnt)
	box = cv2.boxPoints(rect)
	box = np.int0(box)
	cv2.drawContours(frame,[box],0,(0,0,255),2)
	frame = imutils.resize(frame, width=600)
	cv2.imwrite('step3.jpg', frame)

	#Extracting and saving the word here
	W = rect[1][0]
	H = rect[1][1]

	Xs = [i[0] for i in box]
	Ys = [i[1] for i in box]
	x1 = min(Xs)
	x2 = max(Xs)
	y1 = min(Ys)
	y2 = max(Ys)

	angle = rect[2]
	if angle < -45:
	    angle += 90

	# Center of rectangle in source image
	center = ((x1+x2)/2,(y1+y2)/2)
	# Size of the upright rectangle bounding the rotated rectangle
	size = (x2-x1, y2-y1)
	M = cv2.getRotationMatrix2D((size[0]/2, size[1]/2), angle, 1.0)
	# Cropped upright rectangle
	cropped = cv2.getRectSubPix(img, size, center)
	cropped = cv2.warpAffine(cropped, M, size)
	croppedW = H if H > W else W
	croppedH = H if H < W else W
	# Final cropped & rotated rectangle
	croppedRotated = cv2.getRectSubPix(cropped, (int(croppedW),int(croppedH)), (size[0]/2, size[1]/2))
	cv2.imwrite("Word.jpg", croppedRotated)

	#Using OCR here
	word = pytesseract.image_to_string(Image.open('Word.jpg'), config='-psm 8')
	word = clean(word)
	print "Detected :", word
	print "Corrected :", spell(word)
	word = spell(word)

	#Using dictionary API here
	meaning = ""
	try:
		if find_meaning:
			r = requests.get("http://api.pearson.com/v2/dictionaries/ldoce5/entries?headword=" + word)
			result = json.loads(r.text)
			meaning = result["results"][0]["senses"][0]["definition"][0]
	except:
		meaning = "Trouble getting meaning"
	print meaning + "\n\n"

	#Read aloud here
	engine = pyttsx.init()
	engine.say("Word. " + word + ". Meaning. " + meaning)
	engine.runAndWait()



def check_box(orig_frame):
	frame = imutils.resize(orig_frame, width = 2000)
	#HSV and threshold
	hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
	mask = cv2.inRange(hsv, orangeLower, orangeUpper)


	#Erosion and dilation
	#Make this dynamic?
	mask = cv2.erode(mask, None, iterations=2)
	mask = cv2.dilate(mask, None, iterations=5)

	#Detect cue
	cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]

	if len(cnts) > 0:
		return True
	return False


count = 0;
camera = cv2.VideoCapture(0)
while True:
	(grabbed, frame) = camera.read()
	if grabbed == False:
		print "No camera"
		break
	hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
	mask = cv2.inRange(hsv, orangeLower, orangeUpper)
	if check_box(frame):
		count += 1;
		if(count >= 40):
			cv2.imwrite("image.jpg", frame)
			process(False)
			count = 0
	else:
		count = 0
	#print count
	cv2.imshow("video", frame)
	cv2.imshow("mask", mask)
	key = cv2.waitKey(1) & 0xFF
 
	# if the 'q' key is pressed, stop the loop
	if key == ord("q"):
		break
camera.release()
cv2.destroyAllWindows()
