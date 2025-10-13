import json
import boto3



# def lambda_handler(event, context):
#     print("Received event:", json.dumps(event, indent=2))

#     return {
#         "sessionState": {
#             "dialogAction": {"type": "Close"},
#             "intent": {
#                 "name": event["sessionState"]["intent"]["name"],
#                 "state": "Fulfilled"
#             }
#         },
#         "messages": [
#             {"contentType": "PlainText", "content": "Hello from Lambda!"}
#         ]
#     }

sqs = boto3.client('sqs')
QUEUE_URL = 'https://sqs.us-east-2.amazonaws.com/343725796131/DiningRequests'

def lambda_handler(event, context):
    print("Received event:", json.dumps(event, indent=2))

    # --- Detect Lex version ---
    if "sessionState" in event:  # Lex V2
        version = "V2"
        intent = event["sessionState"]["intent"]
        intent_name = intent["name"]
        slots = intent.get("slots", {})
    elif "currentIntent" in event:  # Lex V1
        version = "V1"
        intent_name = event["currentIntent"]["name"]
        slots = event["currentIntent"].get("slots", {})
    else:
        return {"statusCode": 400, "body": "Unknown Lex event format"}

    # --- Handle DiningSuggestionsIntent ---
    if intent_name == "DiningSuggestionsIntent":
        # Extract slot values safely for both Lex versions
        def get_value(slot):
            if isinstance(slot, dict):
                return slot.get("value", {}).get("interpretedValue") or slot.get("value") or slot.get("originalValue")
            return slot

        location = get_value(slots.get("Location"))
        cuisine = get_value(slots.get("Cuisine"))
        dining_time = get_value(slots.get("DiningTime"))
        num_people = get_value(slots.get("NumPeople"))
        email = get_value(slots.get("Email"))

        # Construct message for SQS
        message = {
            "Location": location,
            "Cuisine": cuisine,
            "DiningTime": dining_time,
            "NumPeople": num_people,
            "Email": email
        }

        sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps(message)
        )

        text = "You’re all set. Expect my suggestions shortly! Have a good day."
        if version == "V2":
            return {
                "sessionState": {
                    "dialogAction": {"type": "Close"},
                    "intent": {"name": intent_name, "state": "Fulfilled"}
                },
                "messages": [{"contentType": "PlainText", "content": text}]
            }
        else:  # Lex V1
            return {
                "dialogAction": {
                    "type": "Close",
                    "fulfillmentState": "Fulfilled",
                    "message": {"contentType": "PlainText", "content": text}
                }
            }


    # --- Default fallback ---
    return {
        "dialogAction": {
            "type": "Close",
            "fulfillmentState": "Fulfilled",
            "message": {"contentType": "PlainText", "content": "Sorry, I didn’t understand that."}
        }
    }
