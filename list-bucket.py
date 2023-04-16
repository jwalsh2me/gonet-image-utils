import boto3

s3 = boto3.resource('s3')
myBucket = s3.Bucket('gonet')

key_list = []

for object_summary in myBucket.objects.filter(Prefix="GONet058/"):
    key_list.append(object_summary.key)
    # print(object_summary.key)

print(len(key_list))
