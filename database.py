import boto3
from botocore.exceptions import NoCredentialsError
import os

# Environment variables
awssecret = os.environ["AWS_SECRET_ACCESS_KEY"]
awsaccess = os.environ["AWS_ACCESS_KEY_ID"]

def save_to_dynamodb(phone_number, secret_key):
    try:
        dynamodb = boto3.resource('dynamodb', region_name='us-west-1', aws_access_key_id=awsaccess,
                                  aws_secret_access_key=awssecret)

        # specify your table name
        table = dynamodb.Table('user_keys')

        # insert data into the table
        response = table.put_item(
           Item={
                'phone_number': phone_number,
                'lnbitsadmin': secret_key   # Include this key
            }
            
        )

        print("PutItem succeeded")

    except NoCredentialsError:
        print("No AWS Credentials were found.")

def get_from_dynamodb(phone_number):
    dynamodb = boto3.resource('dynamodb', region_name='us-west-1')
    table = dynamodb.Table('user_keys')
    print(table)

    try:
        response = table.get_item(
            Key={
                'phone_number': phone_number
            }
        )

    except:
        print('error')
        
    else:
        return response['Item']

def update_dynamodb(phone_number, key, value):
    try:
        dynamodb = boto3.resource('dynamodb', region_name='us-west-1', aws_access_key_id=awsaccess,
                                  aws_secret_access_key=awssecret)

        # specify your table name
        table = dynamodb.Table('user_keys')

        # update data in the table
        response = table.update_item(
           Key={
                'phone_number': phone_number,
            },
            UpdateExpression='SET #k = :v',
            ExpressionAttributeNames={
                '#k' : key
            },
            ExpressionAttributeValues={
                ':v' : value
            }
        )

        print("UpdateItem succeeded")

    except NoCredentialsError:
        print("No AWS Credentials were found.")

if __name__ == '__main__':
    phone_number = '+1234567890'
    key = 'lnaddress'
    value = 'lnbc1'

    update_dynamodb(phone_number, key, value)
    # save_to_dynamodb(phone_number, key, value)
    item = get_from_dynamodb(phone_number)
    print(item)
