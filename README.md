# Hands Free dictionary
A computer vision based utility that allows user to point at the word in a document whose meaning is desired and automatically detect the cue, detect the word and print and read aloud it's meaning in real time.

# How to use
1) Install opencv and tesseract for your system
2) run	pip install requirements.txt

Run calibrate.py to set HSV values so that only your cue is visible. A python pickle file is created and used for getting the HSV values while execution.
Now run main.py and point at the desired word using the cue.


