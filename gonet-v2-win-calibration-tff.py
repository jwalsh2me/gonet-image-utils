#!/usr/bin/env python
import numpy as np
from tifffile import tifffile
from PIL import Image
import sys
# import re
import os

"""
    Based on th Original file located at
    https://colab.research.google.com/drive/1tCvs7-J3Z6l_WhY5DjnFxnGBEARXPv5p

    This has been updated to run under Windows following the GONet Downloader Utility
    It will carry over the %USERPROFILE% and %folder% vars from the batch file

"""

folder = os.environ.get('folder')
userprofile = os.environ.get('USERPROFILE')
print(f"Destination Folder is:: {folder}")

out_dir = (f'{userprofile}\\{folder}\\tiffs\\')
# jpeg_out_dir = (f'{userprofile}\\{folder}\\jpegs\\')
in_dir = (f'{userprofile}\\{folder}\\')


## Isolate the files to only those larger than 4MB
file_list = [fn for fn in os.listdir(in_dir) if not None]
file_list = [fn for fn in file_list if os.stat(in_dir+"/"+fn).st_size > 4000000] ## only images that aren't small
file_list = sorted([fn for fn in file_list if (fn[-4:]==".jpg")]) ## only raw jpg images
print(len(file_list))

if not os.path.exists(out_dir):
    os.makedirs(out_dir)

files_converted = 0
for fn in file_list:
    imageInFileName=in_dir+"/"+fn
    imageOutFileName=out_dir + fn.rsplit('.',1)[0]+'.tiff'
    # imageOutJpg = jpeg_out_dir + fn.rsplit('.',1)[0]+'.jpeg'

    file = open(imageInFileName, "rb")
    rawFileOffset = 18711040
    rawHeaderSize = 32768
    rawDataOffset = rawFileOffset - rawHeaderSize
    RELATIVETOEND = 2

    file.seek(-rawDataOffset,RELATIVETOEND)
    pixelsPerLine=4056
    pixelsPerColumn=3040
    usedLineBytes=int(pixelsPerLine*12/8)

    s=np.zeros((pixelsPerLine,pixelsPerColumn),dtype='uint16')
    # do this at least 3040 times though the precise number of lines is a bit unclear
    for i in range(pixelsPerColumn):

        # read in 6112 bytes, but only 6084 will be used
        bdLine = file.read(6112)
        gg=np.array(list(bdLine[0:usedLineBytes]),dtype='uint16')
        s[0::2,i] = (gg[0::3]<<4) + (gg[2::3]&15)
        s[1::2,i] = (gg[1::3]<<4) + (gg[2::3]>>4)

    # form superpixel array
    sp=np.zeros((int(pixelsPerLine/2),int(pixelsPerColumn/2),3),dtype='uint16')
    sp[:,:,0]=s[1::2,1::2]                      # red
    sp[:,:,1]=(s[0::2,1::2]+s[1::2,0::2])/2     # green
    sp[:,:,2]=s[0::2,0::2]                      # blue
    sp = np.multiply(sp,16) ## adjusting the image to be saturated correctly(it was imported from 12bit into a 16bit) so it is a factor of 16 dimmer than should be, i.e this conversion

    sp=sp.transpose()

    # now we need to write it to a tiff file
    array = ((sp+0.5).astype('uint16'))
    tifffile.imwrite(imageOutFileName, array, photometric='rgb')

    # # Now make the JPG --- not needed in Calibration so removed
    # jpeg = Image.open(imageInFileName).convert("RGB")
    # # exif = jpeg.info['exif']
    # # print('EXIF saved on JPEG')
    # jpeg.save((imageOutJpg), 'JPEG')


    ## to be able to keep track of progress
    files_converted += 1
    if files_converted % 10 == 0:
        print(f'Files Converted:: {files_converted}')