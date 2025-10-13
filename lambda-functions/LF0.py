import json
import boto3

# Initialize Lex client
lex_client = boto3.client('lexv2-runtime', region_name='us-east-2')

def lambda_handler(event, context):
    try:
        # Parse the incoming request body
        body = event
        session_id = body.get('sessionId', str(uuid.uuid4()))

        
        # Extract the user message
        user_message = body['messages'][0]['unstructured']['text']
        
        # Call Lex chatbot
        lex_response = lex_client.recognize_text(
            botId='YOUR_BOT_ID',           # Replace with your Lex bot ID   ID: ECFTRMJNQ0
            botAliasId='YOUR_BOT_ALIAS_ID', # Replace with your bot alias ID (often 'TSTALIASID' for test)  ID: TSTALIASID
            localeId='en_US',               # Replace if using different locale
            sessionId=session_id,
            text=user_message
        )
        
        # Extract Lex's response message
        lex_message = lex_response['messages'][0]['content'] if lex_response.get('messages') else "I didn't understand that."
        
        # Format response in the expected structure
        response_body = {
            "messages": [
                {
                    "type": "unstructured",
                    "unstructured": {
                        "text": lex_message
                    }
                }
            ]
        }
        
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps(response_body)
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "messages": [
                    {
                        "type": "unstructured",
                        "unstructured": {
                            "text": "Sorry, something went wrong. Please try again."
                        }
                    }
                ]
            })
        }