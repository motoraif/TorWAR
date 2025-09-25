#!/usr/bin/env python3
"""
Debug Bedrock access issues
Author: Mohamed Toraif
"""

import boto3
import json
import sys

def test_bedrock_access_with_keys(access_key_id, secret_access_key, region='us-east-1'):
    """Test Bedrock access with specific access keys."""
    print("🔍 TESTING BEDROCK ACCESS WITH PROVIDED KEYS")
    print("=" * 60)
    
    try:
        # Create Bedrock client with provided keys
        bedrock_client = boto3.client(
            'bedrock-runtime',
            region_name=region,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key
        )
        
        print(f"✅ Bedrock client created successfully")
        print(f"   Region: {region}")
        print(f"   Access Key: {access_key_id[:8]}...")
        print()
        
        # Test 1: List available models
        print("1️⃣ Testing model availability...")
        try:
            bedrock_models = boto3.client(
                'bedrock',
                region_name=region,
                aws_access_key_id=access_key_id,
                aws_secret_access_key=secret_access_key
            )
            
            models = bedrock_models.list_foundation_models()
            claude_models = [
                model for model in models['modelSummaries'] 
                if 'claude' in model['modelId'].lower()
            ]
            
            print(f"   ✅ Found {len(claude_models)} Claude models")
            for model in claude_models[:5]:  # Show first 5
                print(f"      - {model['modelId']}")
            
        except Exception as e:
            print(f"   ❌ Model listing failed: {e}")
            print("   This might indicate permission issues")
        
        print()
        
        # Test 2: Try to invoke a model
        print("2️⃣ Testing model invocation...")
        
        # Try different Claude models
        test_models = [
            "anthropic.claude-3-haiku-20240307-v1:0",
            "anthropic.claude-3-sonnet-20240229-v1:0",
            "anthropic.claude-instant-v1",
            "anthropic.claude-v2"
        ]
        
        success = False
        for model_id in test_models:
            try:
                print(f"   Testing model: {model_id}")
                
                body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 50,
                    "messages": [
                        {
                            "role": "user",
                            "content": "Hello, please respond with 'Bedrock is working'"
                        }
                    ]
                }
                
                response = bedrock_client.invoke_model(
                    modelId=model_id,
                    body=json.dumps(body)
                )
                
                response_body = json.loads(response['body'].read())
                response_text = response_body['content'][0]['text']
                
                print(f"   ✅ SUCCESS with {model_id}")
                print(f"   Response: {response_text}")
                success = True
                break
                
            except Exception as e:
                print(f"   ❌ Failed with {model_id}: {e}")
                continue
        
        if not success:
            print("   ❌ All model tests failed")
            return False
        
        print()
        print("🎉 BEDROCK ACCESS TEST SUCCESSFUL!")
        return True
        
    except Exception as e:
        print(f"❌ Bedrock client creation failed: {e}")
        return False

def diagnose_common_issues():
    """Diagnose common Bedrock access issues."""
    print("\n" + "🔧 COMMON ISSUES DIAGNOSIS")
    print("=" * 60)
    
    print("❓ Possible reasons for configuration failure:")
    print()
    
    print("1️⃣ REGION ISSUES:")
    print("   ❌ Bedrock not available in selected region")
    print("   ✅ Try: us-east-1, us-west-2, eu-west-1")
    print()
    
    print("2️⃣ MODEL ACCESS:")
    print("   ❌ Claude models not enabled in Bedrock console")
    print("   ✅ Go to Bedrock console → Model access → Enable models")
    print()
    
    print("3️⃣ PERMISSION ISSUES:")
    print("   ❌ AmazonBedrockFullAccess might not include runtime permissions")
    print("   ✅ Ensure these permissions are included:")
    print("      - bedrock:InvokeModel")
    print("      - bedrock:InvokeModelWithResponseStream")
    print("      - bedrock:ListFoundationModels")
    print()
    
    print("4️⃣ ACCESS KEY ISSUES:")
    print("   ❌ Access keys might be inactive or expired")
    print("   ❌ Wrong access key format")
    print("   ✅ Verify keys are active in IAM console")
    print()
    
    print("5️⃣ ACCOUNT ISSUES:")
    print("   ❌ Account 445567094096 might have restrictions")
    print("   ❌ Bedrock service might not be enabled")
    print("   ✅ Check AWS Service Health Dashboard")
    print()
    
    print("6️⃣ NETWORK/FIREWALL:")
    print("   ❌ Corporate firewall blocking Bedrock endpoints")
    print("   ❌ VPC endpoints not configured")
    print("   ✅ Test from different network if possible")

def generate_test_commands():
    """Generate AWS CLI commands for testing."""
    print("\n" + "🧪 MANUAL TESTING COMMANDS")
    print("=" * 60)
    
    print("Test with AWS CLI (replace with your actual keys):")
    print()
    
    print("# Set environment variables")
    print("export AWS_ACCESS_KEY_ID=AKIA...")
    print("export AWS_SECRET_ACCESS_KEY=...")
    print("export AWS_DEFAULT_REGION=us-east-1")
    print()
    
    print("# Test 1: List available models")
    print("aws bedrock list-foundation-models --region us-east-1")
    print()
    
    print("# Test 2: Test model invocation")
    print('aws bedrock-runtime invoke-model \\')
    print('    --model-id anthropic.claude-3-haiku-20240307-v1:0 \\')
    print('    --body \'{"anthropic_version":"bedrock-2023-05-31","max_tokens":50,"messages":[{"role":"user","content":"Hello"}]}\' \\')
    print('    --region us-east-1 \\')
    print('    output.json')
    print()
    print("cat output.json")
    print()
    
    print("# Test 3: Check caller identity")
    print("aws sts get-caller-identity")

if __name__ == "__main__":
    print("🚨 BEDROCK ACCESS TROUBLESHOOTING")
    print("Account: 445567094096")
    print("Permission: AmazonBedrockFullAccess")
    print()
    
    if len(sys.argv) >= 3:
        access_key_id = sys.argv[1]
        secret_access_key = sys.argv[2]
        region = sys.argv[3] if len(sys.argv) > 3 else 'us-east-1'
        
        success = test_bedrock_access_with_keys(access_key_id, secret_access_key, region)
        
        if not success:
            diagnose_common_issues()
    else:
        print("💡 To test with your actual keys, run:")
        print("python3 debug_bedrock_access.py AKIA... your-secret-key us-east-1")
        print()
        diagnose_common_issues()
    
    generate_test_commands()
    
    print("\n" + "🔍 NEXT STEPS:")
    print("1. Test with AWS CLI commands above")
    print("2. Check Bedrock console for model access")
    print("3. Verify region availability")
    print("4. Check TorWAR logs for specific error messages")
    print("5. Try different regions if us-east-1 doesn't work")
