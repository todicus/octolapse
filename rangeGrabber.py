# Gets a list of all the images between the specified dates.

startString		= "20140403050000"	# input
durationHours 	= 24
fileDateFormat 	= "%Y%m%d%H%M%S"

from datetime import datetime, timedelta
startTime 	= datetime.strptime(startString, fileDateFormat)
startString = startTime.strftime(fileDateFormat)
startInt 	= int(startString)

print(startTime)

endTime 	= startTime + timedelta(hours=durationHours)
endString 	= endTime.strftime(fileDateFormat)
endInt		= int(endString)

print("collecting images from {} to {}".format(startTime, endTime) )
print("collecting images from {} to {}".format(startString, endString) )

# get list of folders to search
startDateInt 	= int(startTime.strftime("%Y%m%d"))
endDateInt		= int(endTime.strftime("%Y%m%d"))
print(range(startDateInt, endDateInt))

testName = "20140404011102.jpg"
import os.path
newImageName = os.path.splitext(testName)[0]
print(int(newImageName))

if int(newImageName) > startInt and int(newImageName) < endInt:
	print "yes!"

#if testName
