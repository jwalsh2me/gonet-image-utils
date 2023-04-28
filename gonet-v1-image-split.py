import os
import boto3
import botocore
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import numpy as np
import picamraw
from tifffile import tifffile
from picamraw import PiRawBayer, PiCameraVersion
import logging

#*  **** Add in the GONet v1 Source Camera ****
source_camera = "GONet058"

logging.basicConfig(level=logging.WARN, filename='/tmp/gonet-split.log')
source_image_bucket = "gonet"
tiff_bucket = "gonet.split.tiff"
jpeg_bucket = "gonet.split.jpeg"
#* **** Use your local aws profile is running locally ****
session = boto3.Session(profile_name='adler')
#* **** Use this one if on an EC2 Instance or Sagemaker Notebook with IAM Role/Policy ****
# session = boto3.Session()
s3 = session.resource('s3')
s3_client = session.client("s3")
src_bucket = s3.Bucket(source_image_bucket)
key_list = []
logfile = open("logfile.txt", "a")
dt = str(datetime.today().strftime('%Y-%m-%d %H-%M'))


# Get List of Images
for object_summary in src_bucket.objects.filter(Prefix=f"{source_camera}/"):
    key_list.append(object_summary.key)
    # print(object_summary.key) #* debug


def main():
    # for object_summary in src_bucket.objects.filter(Prefix=f"{source_camera}/"):
    #     key_list.append(object_summary.key)
    #     # print(object_summary.key) #* debug
    print(f"**** START:: {dt} ****")
    logfile.write(f"**** START:: {dt} ****" + "\n")
    counter = 0
    print(f"Images in Bucket Prefix:: {len(key_list)}")
    logfile.write(f"Images in Bucket Prefix:: {len(key_list)} from Camera:: {source_camera}" + "\n")

    for image in key_list[0:]:
        # print(image)
        counter += 1
        print(counter)
        image_name = (f"{image.split('/')[1].split('.')[0]}")
        # print(image_name)
        source_image_tmp = (f"/tmp/{image_name}.jpg")
        tiff_filename = (f"{image.split('/')[1].split('.')[0]}.tiff")
        jpeg_filename = (f"{image.split('/')[1].split('.')[0]}.jpeg")
        # print(f"TIFF Filename:: {tiff_filename}") # DEBUG

    # * Get the files
        try:
            s3_client.download_file(
                source_image_bucket, image, source_image_tmp)
        except Exception as e:
            print(f"ERROR Downloading:: {e}")
            # logging.exception('')
            logfile.write(f"ERROR Downloading:: {str(e)}" + "\n")
            continue
        try:
            source_image = picamraw.PiRawBayer(
                filepath=source_image_tmp,  camera_version=picamraw.PiCameraVersion.V1, sensor_mode=0)
            c = source_image.to_rgb()
            array = (64*c.astype(np.uint16))
            tifffile.imwrite((f"/tmp/{image_name}.tiff"),
                             array, photometric='rgb')
        except Exception as e:
            print(f"ERROR Splitting TIFF:: {e}")
            logging.exception('')
            logfile.write(
                f"ERROR Splitting TIFF {image_name}:: {str(e)}" + "\n")
            continue
        try:
            s3_client.upload_file(
                (f"/tmp/{tiff_filename}"), tiff_bucket, (f"{source_camera}/{tiff_filename}"))
            # print('TIFF Uploaded')
        except Exception as e:
            logging.exception('')
            print(f"ERROR uploading TIFF {tiff_filename}:: {e}" + "\n")
            continue
        # Splitting off the JPEG, saving and applying EXIF from source to JPEG
        try:
            jpeg = Image.open(source_image_tmp).convert("RGB")
            exif = jpeg.info['exif']
            # print('EXIF saved on JPEG')
            jpeg.save((f"/tmp/{jpeg_filename}"), 'JPEG', exif=exif)
        except Exception as e:
            logging.exception('')
            print(f"ERROR with Thumbnail {jpeg_filename}:: {e}" + "\n")
            continue
        try:
            s3_client.upload_file((f"/tmp/{jpeg_filename}"), jpeg_bucket,
                                  (f"{source_camera}/{jpeg_filename}"))
            # print('JPEG Uploaded')
        except Exception as e:
            logging.exception('')
            print(f"ERROR uploading Thumbnail {jpeg_filename}:: {e}" + "\n")
        try:
            os.remove(source_image_tmp)
            os.remove(f"/tmp/{tiff_filename}")
            os.remove(f"/tmp/{jpeg_filename}")
        except Exception as e:
            print(e)
            logfile.write(f"ERROR Cleaning up Temp:: {e}" + "\n")
            continue


try:
    main()
except Exception as e:
    print(f"ERROR:: {e}")
    logfile.write(f"ERROR:: {e}" + "\n")
    logging.exception('')
print(f"**** END:: {dt} ****")
logfile.write(f"**** END:: {dt} ****" + "\n")
logfile.close()
