# lambda/index.py
import json
import os
import re
import urllib.request

# Lambda コンテキストからリージョンを抽出（不要になっても一応残す）
def extract_region_from_arn(arn):
    match = re.search('arn:aws:lambda:([^:]+):', arn)
    if match:
        return match.group(1)
    return "us-east-1"

# FastAPI のエンドポイント（/generate）
FASTAPI_URL = os.environ.get("FASTAPI_URL", "https://58ea-34-16-192-238.ngrok-free.app/generate")

def lambda_handler(event, context):
    try:
        print("Received event:", json.dumps(event))

        # ユーザー認証情報（必要に応じて）
        user_info = None
        if 'requestContext' in event and 'authorizer' in event['requestContext']:
            user_info = event['requestContext']['authorizer']['claims']
            print(f"Authenticated user: {user_info.get('email') or user_info.get('cognito:username')}")

        # リクエストのパース
        body = json.loads(event['body'])
        message = body['message']
        conversation_history = body.get('conversationHistory', [])

        print("Sending message to FastAPI:", message)

        # FastAPI に送るペイロード（正しい形式）
        request_payload = {
            "prompt": message,
            "max_new_tokens": 512,
            "temperature": 0.7,
            "top_p": 0.9,
            "do_sample": True
        }

        req = urllib.request.Request(
            url=FASTAPI_URL,
            data=json.dumps(request_payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )

        with urllib.request.urlopen(req) as res:
            response_body = json.loads(res.read().decode('utf-8'))

        assistant_response = response_body["generated_text"]
        response_time = response_body.get("response_time", None)

        conversation_history.append({
            "role": "assistant",
            "content": assistant_response
        })

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": True,
                "response": assistant_response,
                "response_time": response_time,
                "conversationHistory": conversation_history
            })
        }

    except Exception as error:
        print("Error:", str(error))
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": False,
                "error": str(error)
            })
        }
