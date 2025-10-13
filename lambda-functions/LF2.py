from opensearchpy import OpenSearch
import boto3
import json
import random

# === AWS Clients with Explicit Regions ===
sqs = boto3.client('sqs', region_name='us-west-2')          # SQS in Ohio
ses = boto3.client('ses', region_name='us-west-2')          # SES in Oregon
dynamodb = boto3.resource('dynamodb', region_name='us-east-2')  # DynamoDB in Ohio

# === Configuration ===
QUEUE_URL = 'https://sqs.us-west-2.amazonaws.com/343725796131/DiningRequests'
ES_HOST = 'search-restaurantsdomain-mdepwcqrnzjckoofti3mkscemq.us-west-2.es.amazonaws.com'
DYNAMO_TABLE_NAME = 'yelp-restaurants'

# === OpenSearch Connection ===
es = OpenSearch(
    hosts=[{'host': ES_HOST, 'port': 443}],
    http_auth=('Monish', 'Qweqazqsx!23'),
    use_ssl=True,
    verify_certs=True
)

def get_restaurant_ids(location, cuisine):
    """Query OpenSearch for restaurant IDs matching location and cuisine"""
    query = {
        "query": {
            "bool": {
                "must": [
                    {"match": {"Cuisine": cuisine}},
                    {"match": {"Location": location}}
                ]
            }
        }
    }
    res = es.search(index="restaurants", body=query, size=50)
    hits = res['hits']['hits']
    return [h['_source']['Restaurant_id'] for h in hits]


def get_restaurant_details(restaurant_ids):
    """Fetch restaurant details from DynamoDB"""
    table = dynamodb.Table(DYNAMO_TABLE_NAME)
    details = []
    for rid in restaurant_ids:
        resp = table.get_item(Key={'Restaurant_id': rid})
        if 'Item' in resp:
            details.append(resp['Item'])
    return details


def send_email(to_email, subject, body_text):
    """Send plain text email via SES"""
    response = ses.send_email(
        Source='monishsreekanth07@gmail.com',
        Destination={'ToAddresses': [to_email]},
        Message={
            'Subject': {'Data': subject},
            'Body': {'Text': {'Data': body_text}}
        }
    )
    print(f"Email sent! Message ID: {response['MessageId']}")


def lambda_handler(event, context):
    """Main Lambda handler"""
    messages = sqs.receive_message(
        QueueUrl=QUEUE_URL,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=5
    )

    if 'Messages' not in messages:
        print("No messages to process.")
        return

    for message in messages['Messages']:
        receipt_handle = message['ReceiptHandle']
        body = json.loads(message['Body'])

        location = body.get('Location')
        cuisine = body.get('Cuisine')
        dining_time = body.get('DiningTime')
        num_people = body.get('NumPeople')
        user_email = body.get('Email')

        if not all([location, cuisine, dining_time, num_people, user_email]):
            print("Missing required fields.")
            sqs.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=receipt_handle)
            continue

        print(f"Processing request for {user_email} ({cuisine}, {location})")

        # Step 1: Query OpenSearch
        restaurant_ids = get_restaurant_ids(location, cuisine)

        if not restaurant_ids:
            msg = f"Hello! Sorry, no {cuisine} restaurants found in {location}."
            send_email(user_email, f"{cuisine} Restaurant Suggestions", msg)
            sqs.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=receipt_handle)
            continue

        # Step 2: Query DynamoDB
        restaurants = get_restaurant_details(restaurant_ids)

        if not restaurants:
            msg = f"Hello! No restaurant details found in {location}."
            send_email(user_email, f"{cuisine} Restaurant Suggestions", msg)
            sqs.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=receipt_handle)
            continue

        # Pick up to 3 restaurants randomly
        suggestions = random.sample(restaurants, min(3, len(restaurants)))

        # Step 3: Build email content
        email_body = (
            f"Hello! Here are my {cuisine} restaurant suggestions for {num_people} people, "
            f"for today at {dining_time}:\n"
        )
        for idx, r in enumerate(suggestions, start=1):
            name = r.get('Name', 'Unknown')
            address = r.get('Address', 'Address not available')
            email_body += f"{idx}. {name}, located at {address}\n"

        # Step 4: Send email
        send_email(user_email, f"{cuisine} Restaurant Suggestions", email_body)
        sqs.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=receipt_handle)

        print(f"Successfully processed message for {user_email}")
