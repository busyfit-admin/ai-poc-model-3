import json
import boto3
import urllib.parse
import re
import requests
from openai import OpenAI


api_key = '__YOUR_OPENAI'
aiclient = OpenAI(api_key=api_key)

# Initialize the DynamoDB resource
dynamodb = boto3.resource('dynamodb')

# Replace this with your actual DynamoDB table name
TABLE_NAME = os.environ['DYNAMODB_TABLE_NAME']


def lambda_handler(event, context):
    # Extract S3 object details from SQS message
    for record in event['Records']:
        s3_info = json.loads(record['body'])
        s3_bucket = s3_info['Records'][0]['s3']['bucket']['name']
        s3_key = urllib.parse.unquote_plus(s3_info['Records'][0]['s3']['object']['key'], encoding='utf-8')

        s3URL = f"https://{s3_bucket}.s3.amazonaws.com/{s3_key}"

        print(f"Processing image: {s3URL}")

        response = aiclient.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                "role": "user",
                "content": [
                    {"type": "text", "text": """
                        You are an Apparel Product Classification Analyst. Provide all the Product attributes in the image. 
                        Such as Colour, Detailed Description, Category, genderType Product etc. 
                        Provide the output in the below JSON Format only and no other details:
                        
                        {
                          "ProductAttributes": [
                            {
                              "attributeName": "Product Type",
                              "values": ["T-shirt", "jacket", "jeans", "dress", "sweater"]
                            },
                            {
                                "attributeName": "Product Description",
                                "values": ["A casual t-shirt with a graphic print on the front"]
                            }
                            {
                              "attributeName": "Size",
                              "values": ["Small (S)", "Medium (M)", "Large (L)", "Extra Large (XL)"]
                            },
                            {
                              "attributeName": "Color",
                              "values": ["Red", "Blue", "Black", "White", "Green"]
                            },
                            {
                              "attributeName": "Material",
                              "values": ["Cotton", "Polyester", "Wool", "Denim", "Leather"]
                            },
                            {
                              "attributeName": "Fit",
                              "values": ["Regular", "Slim", "Loose", "Skinny", "Relaxed"]
                            },
                            {
                              "attributeName": "Pattern",
                              "values": ["Solid", "Striped", "Plaid", "Floral", "Graphic Print"]
                            },
                            {
                              "attributeName": "Sleeve Length",
                              "values": ["Short sleeve", "Long sleeve", "Sleeveless", "3/4 sleeve"]
                            },
                            {
                              "attributeName": "Neckline",
                              "values": ["Round neck", "V-neck", "Crew neck", "Collar", "Turtleneck"]
                            },
                            {
                              "attributeName": "Occasion",
                              "values": ["Casual", "Formal", "Sportswear", "Business casual", "Party"]
                            },
                            {
                              "attributeName": "Closure Type",
                              "values": ["Zipper", "Buttons", "Elastic", "Drawstring", "Hook and eye"]
                            }
                          ]
                        }
                        """},
                    
                    
                    {
                    "type": "image_url",
                    "image_url": {
                        "url": s3URL,
                        },
                    },
                ],
                }
            ],
            max_tokens=300,
            )

        
        print(response.choices[0].message.content)
        extract_and_put_in_dynamodb(response.choices[0].message.content, TABLE_NAME)
        
    return {
        'statusCode': 200,
        'body': json.dumps(f'Processed image {s3_key} successfully.')
    }





def extract_and_put_in_dynamodb(ai_output, dynamodb_table):
    # Step 1: Extract the JSON part using regex
    print("Extracting JSON from AI output")
    json_pattern = r'```json(.*?)```'
    match = re.search(json_pattern, ai_output, re.DOTALL)
    
    print(match)
    if match:
        json_string = match.group(1).strip()
        
        print(json_string)
        # Step 2: Parse the extracted JSON
        try:
            product_attributes = json.loads(json_string)
            
            # Step 3: Put the data into DynamoDB
            table = dynamodb.Table(dynamodb_table)
            response = table.put_item(
                Item={
                    'ProductId': '12345',  
                    'ProductAttributes': product_attributes['ProductAttributes']
                }
            )
            print(f'Successfully inserted item into DynamoDB: {response}')
        except json.JSONDecodeError:
            print('Error: Failed to decode JSON from AI output')
    else:
        print('Error: No JSON found in AI output')