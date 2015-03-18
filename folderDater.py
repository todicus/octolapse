# Moves all images from the specified date into a folder of the same name.
#
# CLI: python folderDater.py --date 20150310 --encode True --uploade True
# crontab
# MAILTO="todicus@gmail.com"
# 4 0 * * * python folderDater.py -d 20150310 --encode True --upload True

from os import listdir, mkdir, getcwd, devnull
from os.path import isfile, exists, join
import re
import shutil
import commands     # for rotating images using sips (on OSX only I think)
import subprocess
import argparse
import datetime, pytz
import sys

# parse command line arguments
arg_parser = argparse.ArgumentParser()
arg_parser.add_argument('-d', '--date', type=int)
arg_parser.add_argument('-e', '--encode', dest='toEncode', action='store_true')
arg_parser.add_argument('-u', '--upload', dest='toUpload', action='store_true')
arg_parser.set_defaults(toEncode=False, toUpload=False)
args = arg_parser.parse_args()
date = str(args.date)

print args

homeFolder      = "/Users/octotod/"
dropboxFolder   = homeFolder+"Dropbox/"
timelapseFolder = dropboxFolder+"Timelapse/"
# doesn't work with "Timelapse Temp/"

# format the date as a nice human-readable string
dateObj = datetime.datetime.strptime(date, "%Y%m%d")
dateObj = pytz.timezone("US/Pacific").localize(dateObj)
titleStr = dateObj.strftime("Timelapse %A %B %d, %Y")
print(titleStr)

# get all actual files (not dirs) in timelapse folder
imageList = [f for f in listdir(timelapseFolder) if join(timelapseFolder, f).endswith(".jpg")]

# get the images with filenames containing the desired date string
dateList = [f for f in imageList if re.match(date, f)]
numImages = len(dateList)
print("{} images from {} found in {}".format(numImages, date, timelapseFolder))

if numImages > 0:
    print("\n--- moving images to date folder ---")
    # make new date folder
    newFolder = timelapseFolder + date
    if not exists(newFolder):
        mkdir(newFolder)

    FNULL = open(devnull, 'w')  # for supressing sips output

    imgNum = 0
    for img in dateList:
        imgPath = join(timelapseFolder, img)

        #rotateStr = 'sips -r 180 {0}'.format(imgPath)  # rotate image (slow)
        #subprocess.check_call(rotateStr.split())   # split converts to string array

        status = subprocess.call(['sips', '-r', '180', imgPath], stdout=FNULL, stderr=FNULL);
        if status==0:
            imgNum = imgNum + 1
            print("moved {0} ({1} / {2})".format(img, imgNum, numImages))
        else:
            print("failed to move {0}".format(img))

        # sips also recompresses smaller (but still looks great!)
        shutil.move(imgPath, timelapseFolder + date)                # move to date folder (very fast)
else:
    print "not moving any images"

# glob method is pretty slow
#import glob
#print glob.glob(timelapseFolder+"*.jpg")

scriptFolder = getcwd() # don't need with commands, do need with subprocess

# make video from folder
if args.toEncode:
    print("\n--- encoding folder to video ---")
    #encodeStr = 'python {0}/folder2videoCV2.py -d {1}'.format(scriptFolder, date)
    #print(encodeStr)

    p = subprocess.Popen(['python', scriptFolder+"/folder2videoCV2.py", '-d', date], stdout=subprocess.PIPE)
    #p = subprocess.Popen(encodeStr, stdout=subprocess.PIPE, shell=True)
    # grab stdout line by line as it becomes available; will loop until p terminates
    while p.poll() is None:
        #newLine, err = p.communicate()
        newLine = p.stdout.readline()   # blocks until it receives a newline; requires stdout.flush() in subprocess after print
        sys.stdout.write(newLine)
    print p.stdout.read()   # process any lingering output

if args.toUpload:
    print("\n--- uploading video to YouTube ---")
    recordingDate = dateObj.strftime("%Y-%m-%dT%H:%M:%S.000%z")  # ISO 8601 (YYYY-MM-DDThh:mm:ss.sssZ) 
    print(recordingDate)
    # python uploadYouTube.py --file ~/Movies/Timelapse/Hamilton/20150212.mov --title "Timelapse February 12th, 2015" --keywords "timelapse,san francisco,skyline,tenderloin"
    uploadStr = 'python {0}/uploadYouTube.py \
        --file ~/Movies/Timelapse/Hamilton/{1}.mp4 \
        --title \"{2}\" \
        --keywords "timelapse,san francisco,skyline,tenderloin" \
        --location "San Francisco, California" \
        --date {3}' \
        .format(scriptFolder, date, titleStr, recordingDate)
    print(uploadStr)
    status, message = commands.getstatusoutput(uploadStr)
    print(message)
