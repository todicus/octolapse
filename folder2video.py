# Converts a folder full of images into a compressed video.
# 
# Crashes when run from launchd.
#
# Can run ffmpeg directly from CLI on filename=datestamp image sequence using:
#  ffmpeg -framerate 10 -f image2 -i %*.jpg -c:v libx264 video.mp4
#
# For more ffmpeg options, see: http://lukemiller.org/index.php/2014/10/ffmpeg-time-lapse-notes/

fps = '24' # doesn't like 12, 15 ("No handlers could be found for logger "libav.mpeg4")
rate = 80000000
useFullResolution = 0   # whether to save video at original capture resolution
outputW = 1440
outputH = 1080

from os import listdir
from os.path import join
import av
#sys.path.append('/usr/local/lib/python2.7/site-packages')
import cv2
import argparse
import sys

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

# get just the files in the date folder
print("getting image list from "+dateFolder)
imageList = [f for f in listdir(dateFolder) if join(dateFolder, f).endswith(".jpg")]

# setup the output file & stream
print("saving video to: "+saveFolder)
output = av.open(saveFolder+date+".mov", 'w')
stream = output.add_stream('mpeg4', fps)	# libx264 does not work
stream.bit_rate = rate
stream.pix_fmt = 'yuv420p'  # does not mean 420p resolution

# get video resolution from first image in folder
if useFullResolution:
	sizeImg = cv2.imread(dateFolder + imageList[0])
	print("using full resolution of {} x {} ".format(sizeImg.shape[0],sizeImg.shape[1]) )
	stream.height = sizeImg.shape[0]
	stream.width = 	sizeImg.shape[1]
else:
    print("using resolution of {} x {}".format(outputW, outputH))
    stream.height = outputH
    stream.width =  outputW

# add all images to the stream & push into the output file
numImages = len(imageList)
print("compiling {} images into a video".format(numImages))
if numImages > 0:
    imgNum = 0
    for imgName in imageList:
        path = dateFolder + imgName
        imgNum = imgNum + 1
        print("{} / {}".format(imgNum, numImages))
        sys.stdout.flush()
        img = cv2.imread(path)
        
        # TODO: draw timestamp with putText() from http://docs.opencv.org/modules/core/doc/drawing_functions.html
        # Or maybe: http://pillow.readthedocs.org/en/latest/reference/index.html

        # can swap color channels for cool effects!
        frame = av.VideoFrame.from_ndarray(img, format='bgr24')
        if not useFullResolution:
            frame = frame.reformat(outputW, outputH, 'bgr24')
        packet = stream.encode(frame)
        output.mux(packet)

    # close the output file
    output.close()
else:
    print("no images found, aborting encode")