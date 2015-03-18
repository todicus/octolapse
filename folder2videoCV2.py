#!/usr/local/bin/python

# Uses just OpenCV, which I hope will work with launchd. Also allows burning of
# timestamp based on image filename, and any other cool stuff you could do.
#
# Another nice Python library for video: http://zulko.github.io/moviepy/getting_started/clips.html#imagesequenceclip

import subprocess, sys
print "python version inside folder2videoCV2.py"
status = subprocess.call(['which', 'python'])
sys.stdout.flush()

toRotate = False

import cv2
from os import listdir
from os.path import join
import datetime, argparse

# parse command line arguments
arg_parser = argparse.ArgumentParser()
arg_parser.add_argument('-d', '--date', type=int)
args = arg_parser.parse_args()
date = str(args.date)

# set paths
homeFolder = "/Users/octotod/"
timelapseFolder = homeFolder + "Dropbox/Timelapse/"
dateFolder = timelapseFolder + date + "/"
saveFolder = homeFolder + "Movies/Timelapse/Hamilton/"

# get just the jpg files in the date folder
print("getting image list from "+dateFolder)
sys.stdout.flush()
imageList = [f for f in listdir(dateFolder) if join(dateFolder, f).endswith(".jpg")]

vidFrameSize = (1440, 1080)
codec = cv2.cv.CV_FOURCC('m', 'p', '4', 'v')
vidWriter = cv2.VideoWriter(saveFolder+date+".mp4", codec, 12, vidFrameSize)
pos = (12, 36)

if toRotate:
    (w, h) = vidFrameSize
    center = (w / 2, h / 2)
    rotationMatrix = cv2.getRotationMatrix2D(center, 180, 1.0)

# add all images to the stream & push into the output file
numImages = len(imageList)
print("compiling {} images into a video".format(numImages))
sys.stdout.flush()
imgNum = 0

for imgName in imageList:
    path = dateFolder + imgName
    imgNum = imgNum + 1
    print("{} / {}".format(imgNum, numImages))
    sys.stdout.flush()

    # get image
    img = cv2.imread(path)
    img = cv2.resize(img, vidFrameSize)
    if toRotate:
        img = cv2.warpAffine(img, rotationMatrix, (w, h))
    
    # burn timestamp
    dateObj = datetime.datetime.strptime(imgName, "%Y%m%d%H%M%S.jpg")
    timestamp = dateObj.strftime("%H:%M:%S")
    cv2.putText(img, timestamp, pos, cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,0,0), thickness=2, lineType=cv2.CV_AA)
    cv2.putText(img, timestamp, pos, cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255,255,255), thickness=1, lineType=cv2.CV_AA)
    
    vidWriter.write(img)

vidWriter.release()
del vidWriter
print("finished!")
sys.stdout.flush()