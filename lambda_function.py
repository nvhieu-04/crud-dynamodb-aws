import json
import boto3
import base64
import botocore
from botocore.errorfactory import ClientError
from decimal import Decimal
import uuid
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('usersAPI')

class DecimalEncoder(json.JSONEncoder):
  def default(self, obj):
    if isinstance(obj, Decimal):
      return str(obj)
    return json.JSONEncoder.default(self, obj)

def lambda_handler(event, context):
    print(event)
    auth = event['headers']['authorization']
    if(auth != 'Basic aGlldTpoaWV1MTIz'):
        return {
            'statusCode': 401,
            'body': json.dumps('Invalid authorization')
        }
    method = event['routeKey']
    if method == 'GET /users':
        response = table.scan()
        if 'Items' not in response:
            return {
                'statusCode': 500,
                'body': json.dumps('No data')
            }
        if response['Count'] == 0:
            return {
                'statusCode': 500,
                'body': json.dumps('No data')
            }
        data = response['Items']
        return {
                    'statusCode': 200,
                    'body': json.dumps(data,cls=DecimalEncoder)
        }   
    elif method == 'GET /users/{id}':
        user_id = event['pathParameters']['id']
        response = table.get_item(Key={'id': user_id})
        if 'Item' not in response:
            return {
                'statusCode': 500,
                'body': json.dumps('Account not Exist')
            }
        user = response['Item']
        return {
            'statusCode': 201,
            'body': json.dumps(user, cls=DecimalEncoder)
        }
    elif method == 'POST /users':
        user = json.loads(event['body'])
        print(user['id'])
        name = user.get('name', '')
        phone = user.get('phone', '')
        id = user.get('id', '')
        if id == '':
            return {
                'statusCode': 400,
                'body': json.dumps('Id is required')
            }
        
        if name == '' or phone == '':
            return {
                'statusCode': 400,
                'body': json.dumps('Name and phone number are required')
            }
        if len(name) < 6:
            return {
                'statusCode': 400,
                'body': json.dumps('Length of username must be greater than 6')
            }
        if name[0].isnumeric():
            return {
                'statusCode': 400,
                'body': json.dumps('Name must not start with a number')
            }
        if name[0].islower():
            return {
                'statusCode': 400,
                'body': json.dumps('Name must not start with a lowercase letter')
            }
        response = table.get_item(
            Key={
                'id': user['id']
            }
        )
        print(response)
        #Validation phone number
        if len(phone) != 10:
            return {
                'statusCode': 400,
                'body': json.dumps('Phone number must be 10 digits')
            }
        if phone[0] != '0':
            return {
                'statusCode': 400,
                'body': json.dumps('Phone number must start with 0')
            }
        
        if 'Item' in response:
            return {
                'statusCode': 500,
                'body': json.dumps('Account Exist')
            }
        else:
            user = {
                'id': user['id'],
                'name': user['name'],
                'phone': user['phone']
            }
            table.put_item(Item=user)
            return {
                'statusCode': 201,
                'body': json.dumps('User created successfully')
            } 
    elif method == 'PUT /users/{id}':
        user_id = event['pathParameters']['id']
        user = json.loads(event['body'])
        userupdate = {
                'id': user.get('id', ''),
                'name': user.get('name', ''),
                'phone': user.get('phone', ''),
            }
        if userupdate['id'] == '':
            return {
                'statusCode': 400,
                'body': json.dumps('Id is required')
            }
        if userupdate['name'] == '' or userupdate['phone'] == '':
            return {
                'statusCode': 400,
                'body': json.dumps('Name and phone number are required')
            }
        table.update_item(
            Key={'id': user_id},
            UpdateExpression="set #name=:n, phone=:p",
            ExpressionAttributeValues={
                ':n': userupdate['name'],
                ':p': userupdate['phone']
            },
            ExpressionAttributeNames={
                "#name": "name"
            },
            ReturnValues="UPDATED_NEW"
        )
        return {
            'statusCode': 200,
            'body': json.dumps('User updated successfully')
        }
    elif method == 'DELETE /users/{id}':
        user_id = event['pathParameters']['id']
        if user_id == '':
            return {
                'statusCode': 400,
                'body': json.dumps('Id is required')
            }
        response = table.get_item(
            Key={
                'id': user_id
            }
        )
        if 'Item' not in response:
            return {
                'statusCode': 500,
                'body': json.dumps('Account not Exist')
            }
        table.delete_item(Key={'id': user_id})
        s3 = boto3.resource('s3')
        bucket = s3.Bucket('myawsbucket-1244')
        bucket.objects.filter(Prefix='userId'+ user_id + '/').delete()
        return{
            'statusCode': 200,
            'body': json.dumps('User deleted successfully')
        }
    elif method == 'POST /users/images':
        data = json.loads(event['body'])
        id = data.get('id', '')
        if id == '':
            return {
                'statusCode': 400,
                'body': json.dumps('Id is required')
            }
        response = table.get_item(Key={'id': id})
        if 'Item' not in response:
            return {
                'statusCode': 500,
                'body': json.dumps('Account not Exist')
            }
        filename = data.get('filename', '')
        base64data = data.get('base64data', '')
        if filename == '' or base64data == '':
            return {
                'statusCode': 400,
                'body': json.dumps('Filename and base64data are required')
            }
        file = filename + str(uuid.uuid4())
        s3 = boto3.client('s3')
        try:
            s3.head_object(Bucket='myawsbucket-1244',
                            Key= 'userId'+ id + '/' + file + '.jpg')
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "404":
                s3 = boto3.resource('s3')
                s3.Object('myawsbucket-1244', 'userId'+ id + '/' + file + '.jpg').put(Body=base64.b64decode(base64data))
                table.update_item(
                    Key={'id': id},
                    UpdateExpression="set #filename=:f",
                    ExpressionAttributeValues={
                        ':f': file
                    },
                    ExpressionAttributeNames={
                        "#filename": "filename"
                    },
                    ReturnValues="UPDATED_NEW"
                )
                return {
                    'statusCode': 200,
                    'body': json.dumps('Image uploaded successfully')
                }
            else:
                return {
                    'statusCode': 500,
                    'body': json.dumps('Error')
                }
        return {
            'statusCode': 500,
            'body': json.dumps('File Exist')
        }
    elif method == 'GET /users/images/{id}':
        user_id = event['pathParameters']['id']
        if user_id == '':
            return {
                'statusCode': 400,
                'body': json.dumps('Id is required')
            }
        response = table.get_item(Key={
            'id': user_id
            })
        if 'Item' not in response:
            return {
                'statusCode': 500,
                'body': json.dumps('Account not Exist')
            }
        data = response['Item']
        print(data)
        s3 = boto3.client('s3')
        filename = data.get('filename', '')
        print(filename)
        if filename == '':
            return {
                'statusCode': 404,
                'body': json.dumps('File not found')
            }
        #Check file exist()
        try:
            s3.head_object(Bucket='myawsbucket-1244', Key='userId'+ user_id + '/' + filename + '.jpg')
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "404":
                return {
                    'statusCode': 404,
                    'body': json.dumps('File not found')
                }
            else:
                return {
                    'statusCode': 500,
                    'body': json.dumps('Error')
                }
        # url = s3.generate_presigned_url(
        #     ClientMethod='get_object',
        #     Params={
        #         'Bucket': 'myawsbucket-1244',
        #         'Key': filename + '.jpg',
        #     }
        # )
        # print(url)
        # return {
        #     'statusCode': 200,
        #     'body': json.dumps(url)
        # }
        url = s3.get_object(
            Bucket='myawsbucket-1244', 
            Key='userId'+ user_id + '/' + filename + '.jpg',
            )
        print(url)
        convertBase64 = base64.b64encode(url['Body'].read())
        value = {
            'filename': filename + '.jpg',
            'base64data': convertBase64.decode('utf-8'),
        }
        return {
            'statusCode': 200,
            'body': json.dumps(value)
        }
    elif method == 'DELETE /users/images/{id}':
        user_id = event['pathParameters']['id']
        if user_id == '':
            return {
                'statusCode': 400,
                'body': json.dumps('Id is required')
            }
        response = table.get_item(Key={'id': user_id})
        if 'Item' not in response:
            return {
                'statusCode': 500,
                'body': json.dumps('Account not Exist')
            }
        data = response['Item']
        s3 = boto3.client('s3')
        filename = data.get('filename', '')
        if filename == '':
            return {
                'statusCode': 404,
                'body': json.dumps('File not found')
            }
        #Check file exist()
        try:
            s3.head_object(Bucket='myawsbucket-1244', Key='userId'+ user_id + '/' + filename + '.jpg')
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "404":
                return {
                    'statusCode': 404,
                    'body': json.dumps('File not found')
                }
            else:
                return {
                    'statusCode': 500,
                    'body': json.dumps('Error')
                }
            
        s3.delete_objects(
            Bucket='myawsbucket-1244',
            Delete={
                'Objects': [
                    {
                        'Key': 'userId'+ user_id + '/' + filename + '.jpg'
                    }
                ]
            }
        )
        table.update_item(
            Key={'id': user_id},
            UpdateExpression="set #filename=:f",
            ExpressionAttributeValues={
                ':f': ''
            },
            ExpressionAttributeNames={
                "#filename": "filename"
            },
            ReturnValues="UPDATED_NEW"
        )
        return {
            'statusCode': 200,
            'body': json.dumps('Image deleted successfully')
        }
    elif method == 'PUT /users/images':
        data = json.loads(event['body'])
        filename = data.get('filename', '')
        base64data = data.get('base64data', '')
        user_id = data.get('id', '')
        if user_id == '':
            return {
                'statusCode': 400,
                'body': json.dumps('Id is required')
            }
        response = table.get_item(Key={'id': user_id})
        if 'Item' not in response:
            return {
                'statusCode': 500,
                'body': json.dumps('Account not Exist')
            }
        
        if filename == '' or base64data == '':
            return {
                'statusCode': 400,
                'body': json.dumps('Filename and base64data are required')
            }
        s3 = boto3.client('s3')
        try:
            s3.head_object(Bucket='myawsbucket-1244', Key='userId'+ user_id + '/' + filename + '.jpg')
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "404":
                return {
                    'statusCode': 404,
                    'body': json.dumps('File not found')
                }
            else:
                return {
                    'statusCode': 500,
                    'body': json.dumps('Error')
                }
        s3 = boto3.resource('s3')
        s3.Object('myawsbucket-1244', 'userId'+ user_id + '/' + filename + '.jpg').put(Body=base64.b64decode(base64data))
        return {
            'statusCode': 200,
            'body': json.dumps('Image updated successfully')
        }
    else:
        return {
            'statusCode': 400,
            'body': json.dumps('Invalid HTTP method')
        }
