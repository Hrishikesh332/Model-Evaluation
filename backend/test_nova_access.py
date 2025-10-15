
import boto3
import json
import time
from config import Config

def test_nova_access():

    print(f"🕐 Testing Nova access at {time.strftime('%H:%M:%S')}")
    print("=" * 50)
    
    try:
        if Config.AWS_ACCESS_KEY_ID and Config.AWS_SECRET_ACCESS_KEY:
            client = boto3.client(
                'bedrock-runtime',
                region_name=Config.AWS_DEFAULT_REGION,
                aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY
            )
        else:
            client = boto3.client('bedrock-runtime', region_name=Config.AWS_DEFAULT_REGION)

        request = {
            'schemaVersion': 'messages-v1',
            'messages': [
                {
                    'role': 'user',
                    'content': [
                        {
                            'text': 'Hello, this is a test message for Nova.'
                        }
                    ]
                }
            ],
            'inferenceConfig': {
                'maxTokens': 20,
                'temperature': 0.7
            }
        }
        
        response = client.invoke_model(
            modelId='amazon.nova-lite-v1:0',
            body=json.dumps(request)
        )
        
        response_body = json.loads(response['body'].read())
        result_text = response_body.get('output', {}).get('message', {}).get('content', [{}])[0].get('text', 'No response')
        
        print("🎉 SUCCESS! Nova model is now accessible!")
        print(f"   Response: {result_text}")
        print("\n✅ You can now use Nova in your application!")
        return True
        
    except Exception as e:
        if 'AccessDenied' in str(e):
            print("⏳ Still waiting for access to propagate...")
            print("   This is normal - can take 5-15 minutes")
            print("   Try again in a few minutes")
        else:
            print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_nova_access()
    
    if not success:
        print(f"\n💡 To test again, run:")
        print(f"   python test_nova_access.py")
        print(f"\n⏰ Or wait 5-10 minutes and try again")
