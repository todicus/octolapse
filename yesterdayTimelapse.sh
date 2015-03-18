#!/bin/bash

# CV2 crashs on import when called from launchd environment, and this is because
# the python version used in launchd is /usr/bin/python --version >>> 2.7.5 and the
# the version is my bash shell is /usr/local/bin/python --version >>> 2.7.9. I can't
# figure out how to set the python path just for a session of launchd (I don't want
# to change the launchd evn perminently, as who knows what might need the system version
# of python!), so I just call the CV2 encoding from a specific PYTHONPATH.
#
# Another option, emplyed below, is setting up a virtualenv for the octolapse project.
# This creates a consistent Python environment from which to run all the scripts,
# and seems to be working even though all stdout output appears all at once on completion
# or error.
#
# I think the way forward is to make folder2videoCV2 an importable function, and then
# the call to folderDater (likely renamed octolapse.py) will be made from the bash
# script with the specific python path.


# paths
#IMAGEDIR="/Users/octotod/Dropbox/Timelapse"
#VIDEODIR="/Users/octotod/Movies/Timelapse/Hamilton"
#PYTHONPATH="/usr/local/bin/python"
CODEDIR="/Users/octotod/Dropbox/Code/Python/octolapse/"

# get target date
DATE=`date -v-1d +%Y%m%d`	# gets yesterday's date
#DATE=`date +%Y%m%d`
#DATE="20150226"	# for testing on a few images
echo "Processing images from $DATE"

# switch to octolapse directory
cd $CODEDIR

# need this to find virtualenv
PATH="/usr/local/bin:${PATH}"	# adding /Library/Python/2.7/site-packages/ does not find YouTube upload requirements
export PATH

# site option gets Numpy, but not httplib2 and other YouTube upload requirements
virtualenv -p $PYTHONPATH venv --system-site-packages --no-setuptools
source venv/bin/activate
# link to opencv installation
ln -s /usr/local/lib/python2.7/site-packages/cv2.so /usr/local/lib/python2.7/site-packages/cv.py ./venv/lib/python2.7/site-packages
# link to requirements for YouTube Upload
ln -s /Library/Python/2.7/site-packages/httplib2 ./venv/lib/python2.7/site-packages/
ln -s /Library/Python/2.7/site-packages/apiclient ./venv/lib/python2.7/site-packages/
ln -s /Library/Python/2.7/site-packages/oauth2client ./venv/lib/python2.7/site-packages/
ln -s /Library/Python/2.7/site-packages/uritemplate ./venv/lib/python2.7/site-packages/
#which python

python folderDater.py --date $DATE --encode --upload
#python folderDater.py --date $DATE 	# just organize files, don't encode or upload

deactivate	# deactivate virtualenv, not sure if required.
#rm -rf venv 	# remove virtualenv; not required as creation will not overwrite


# must specify python path for opencv
#$PYTHONPATH folder2videoCV2.py -d $DATE 	# works!
#python folder2videoCV2.py -d $DATE 		# does not work

# Instead of encoding with PyAV, which segfaults when run from launchd.
# ffmpeg uses all cores, maybe makes smaller files but hijacks the entire CPU.
# also no easy way to add timestamps based on source image filename.
#cd $IMAGEDIR/$DATE
#/usr/local/bin/ffmpeg -framerate 12 -pattern_type glob -i '*.jpg' -s:v 1440x1080 -c:v libx264 $VIDEODIR/$DATE.mp4
#ffmpeg -framerate 12 -f image2 -i %*.jpg -s:v 1440x1080 -c:v libx264 $VIDEODIR/$DATE.mp4

# Just test upload
#cd $CODEDIR
#python folderDater.py --date $DATE --upload
#python uploadYouTube.py --file ~/Movies/Timelapse/Hamilton/20150212.mov --title "Timelapse February 12th, 2015" --keywords "timelapse,san francisco,skyline,tenderloin"