#!/usr/bin/python

# Mashup from various authors:
# brainflakes, pageauc, peewee2, Kesthal

import StringIO
import subprocess
import os
import time
from datetime import datetime
from PIL import Image

# Packages for sending emails and attachments
import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

# Original code written by brainflakes and modified to exit
# image scanning for loop as soon as the sensitivity value is exceeded.
# this can speed taking of larger photo if motion detected early in scan
#
# Motion detection settings:
# need future changes to read values dynamically via command line parameter
# or xml file
# --------------------------
# Threshold:
# How much a pixel has to change by to be marked as "changed").
#
# Sensitivity:
# How many changed pixels before capturing an image) needs to be
# higher if noisy view.
#
# ForceCapture:
# Whether to force an image to be captured every forceCaptureTime seconds
#
# filepath:
# Location of folder to save photos
#
# filenamePrefix:
# String that prefixes the file name for easier identification of files.
threshold = 10
sensitivity = 180
forceCapture = True
forceCaptureTime = 60 * 60  # Once an hour
filepath = "/mnt/picam"
filenamePrefix = "capture"
# File photo size settings
saveWidth = 1280
saveHeight = 960
diskSpaceToReserve = 40 * 1024 * 1024  # Keep 40 mb free on disk

# email settings
emailFrom = ''
emailFromPwd = ''
emailTo = ''
emailSubject = 'MOTION DETECTED!!!'


# Send an email with a picture attached
def sendEmail(emailTo, filename):
    # Create the container (outer) email message
    msg = MIMEMultipart()
    msg['Subject'] = emailSubject
    msg['From'] = emailFrom
    msg['To'] = emailTo

    # Open the files in binary mode and let the MIMEImage class automatically
    # guess the specific image type
    fp = open(filename, 'rb')
    img = MIMEImage(fp.read(), name=os.path.basename(filename))
    fp.close()
    msg.attach(img)

    # Send the email via the Gmail SMTP server
    smtp = smtplib.SMTP('localhost:25')
    #smtp.starttls()
    #smtp.login(emailFrom, emailFromPwd)
    smtp.sendmail(emailFrom, emailTo, msg.as_string())
    smtp.quit()


# Capture a small test image (for motion detection)
def captureTestImage():
    command = "raspistill -w %s -h %s -t 0 -e bmp -o -" % (100, 75)
    imageData = StringIO.StringIO()
    imageData.write(subprocess.check_output(command, shell=True))
    imageData.seek(0)
    im = Image.open(imageData)
    buffer = im.load()
    imageData.close()
    return im, buffer


# Save a full size image to disk
def saveImage(width, height, diskSpaceToReserve):
    keepDiskSpaceFree(diskSpaceToReserve)
    time = datetime.now()
    filename = filepath + "/" + filenamePrefix + "-%04d%02d%02d-%02d%02d%02d.jpg" % ( time.year, time.month, time.day, time.hour, time.minute, time.second)
    subprocess.call("raspistill -mm matrix -hf -vf -w 1296 -h 972 -t 0 -e jpg -q 15 -o %s" % filename, shell=True)
    sendEmail(emailTo, filename)
    print "Captured %s" % filename


# Keep free space above given level
def keepDiskSpaceFree(bytesToReserve):
    if (getFreeSpace() < bytesToReserve):
        for filename in sorted(os.listdir(".")):
            if filename.startswith(fileNamePrefix) and filename.endswith(".jpg"):
                os.remove(filename)
                print "Deleted %s to avoid filling disk" % filename
                if (getFreeSpace() > bytesToReserve):
                    return


# Get available disk space
def getFreeSpace():
    st = os.statvfs(".")
    du = st.f_bavail * st.f_frsize
    return du

# Get first image
image1, buffer1 = captureTestImage()

# Reset last capture time
lastCapture = time.time()

# added this to give visual feedback of camera motion capture activity.
# Can be removed as required
os.system('clear')
print "            Motion Detection Started"
print "            ------------------------"
print "Pixel Threshold (How much)   = " + str(threshold)
print "Sensitivity (changed Pixels) = " + str(sensitivity)
print "File Path for Image Save     = " + filepath
print "---------- Motion Capture File Activity --------------"

while (True):

    # Get comparison image
    image2, buffer2 = captureTestImage()

    # Count changed pixels
    changedPixels = 0
    for x in xrange(0, 100):
        # Scan one line of image then check sensitivity for movement
        for y in xrange(0, 75):
            # Check green as it's the highest quality channel
            pixdiff = abs(buffer1[x, y][1] - buffer2[x, y][1])
            if pixdiff > threshold:
                changedPixels += 1

        # Changed logic - If movement sensitivity exceeded then
        # Save image and Exit before full image scan complete
        if changedPixels > sensitivity:
            lastCapture = time.time()
            saveImage(saveWidth, saveHeight, diskSpaceToReserve)
            break
        continue

    # Check force capture
    if forceCapture:
        if time.time() - lastCapture > forceCaptureTime:
            changedPixels = sensitivity + 1

    # Swap comparison buffers
    image1 = image2
    buffer1 = buffer2
