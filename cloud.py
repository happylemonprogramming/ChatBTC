'''Uploads file to Amazon AWS (S3) and returns authorized link'''

import os
import boto3

# Environment variables
awssecret = os.environ["AWS_SECRET_ACCESS_KEY"]
awsaccess = os.environ["AWS_ACCESS_KEY_ID"]

def serverlink(local_filepath):
    # Create an S3 client
    s3 = boto3.client('s3')

    filename = local_filepath  # This is the local file that you want to upload
    bucket_name = 'lightningsms'  # The name of your S3 bucket
    object_name = 'lightning.jpeg'  # The name you want the file to have on S3
    region = 'us-west-1' # Region where the server resides

    # Uploads the given file using a managed uploader, which will split up large
    # files automatically and upload parts in parallel.
    s3.upload_file(filename, bucket_name, object_name, ExtraArgs={'ContentType': "image/jpeg"})

    # Create Url
    url = s3.generate_presigned_url(
        ClientMethod='get_object',
        Params={
            'Bucket': bucket_name,
            'Key': object_name,
        }
    )

    return url

if __name__ == "__main__":
    print(serverlink('lightning.jpeg'))