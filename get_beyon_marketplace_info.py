#!/usr/bin/env python3
"""
Helper script to get beyon-marketplace account information
Author: Mohamed Toraif
"""

import boto3
import json

def get_beyon_marketplace_info():
    """Get beyon-marketplace account information."""
    print("🔍 Getting beyon-marketplace Account Information")
    print("=" * 50)
    
    try:
        # Create session with beyon-marketplace profile
        session = boto3.Session(profile_name='beyon-marketplace')
        
        # Get STS client
        sts = session.client('sts')
        
        # Get caller identity
        identity = sts.get_caller_identity()
        
        account_id = identity['Account']
        user_arn = identity['Arn']
        
        print(f"✅ beyon-marketplace Account ID: {account_id}")
        print(f"✅ Current User/Role: {user_arn}")
        print()
        
        # Test Bedrock availability
        print("🧪 Testing Bedrock Availability...")
        try:
            bedrock = session.client('bedrock', region_name='us-east-1')
            models = bedrock.list_foundation_models()
            
            claude_models = [
                model for model in models['modelSummaries'] 
                if 'claude' in model['modelId'].lower()
            ]
            
            if claude_models:
                print(f"✅ Found {len(claude_models)} Claude models available")
                for model in claude_models[:3]:  # Show first 3
                    print(f"   - {model['modelId']}")
            else:
                print("⚠️  No Claude models found - may need to enable model access")
                
        except Exception as e:
            print(f"⚠️  Bedrock not accessible: {e}")
            print("   This might be normal if Bedrock isn't enabled yet")
        
        print()
        print("📋 Configuration for TorWAR:")
        print(f"   Account ID: {account_id}")
        print(f"   Role Name: TorWAR-BedrockAccess (suggested)")
        print(f"   Region: us-east-1")
        print()
        
        # Generate role ARN for reference
        role_arn = f"arn:aws:iam::{account_id}:role/TorWAR-BedrockAccess"
        print("🔗 Role ARN to create:")
        print(f"   {role_arn}")
        print()
        
        # Generate assume role policy for beyon-money-payer
        assume_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": "sts:AssumeRole",
                    "Resource": role_arn
                }
            ]
        }
        
        print("📝 Policy to add to beyon-money-payer role:")
        print(json.dumps(assume_policy, indent=2))
        
        return {
            'account_id': account_id,
            'user_arn': user_arn,
            'role_arn': role_arn,
            'bedrock_available': len(claude_models) > 0 if 'claude_models' in locals() else False
        }
        
    except Exception as e:
        print(f"❌ Error accessing beyon-marketplace: {e}")
        print()
        print("💡 Possible solutions:")
        print("   1. Check if beyon-marketplace profile is configured:")
        print("      aws configure list --profile beyon-marketplace")
        print("   2. Verify credentials are valid:")
        print("      aws sts get-caller-identity --profile beyon-marketplace")
        print("   3. Ensure you have access to the beyon-marketplace account")
        
        return None

if __name__ == "__main__":
    result = get_beyon_marketplace_info()
    
    if result:
        print("🎉 Ready to configure TorWAR!")
        print(f"   Visit: http://localhost:5000/ai-config")
        print(f"   Enter Account ID: {result['account_id']}")
        print(f"   Use Role Name: TorWAR-BedrockAccess")
    else:
        print("❌ Please fix the beyon-marketplace profile access first")
