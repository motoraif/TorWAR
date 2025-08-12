"""
TorWAR Bedrock Integration with Cross-Account Support
Author: Mohamed Toraif
Description: AWS Bedrock integration for intelligent, actionable recommendations
Supports cross-account Bedrock access for centralized AI services
"""

import boto3
import json
from datetime import datetime
from aws_helper import get_aws_session

class BedrockRecommendationAnalyzer:
    """AI-powered recommendation analysis using AWS Bedrock with multiple authentication methods."""
    
    def __init__(self, bedrock_account_id=None, bedrock_role_name=None, bedrock_region='us-east-1', 
                 access_key_id=None, secret_access_key=None):
        self.bedrock_client = None
        self.model_id = "anthropic.claude-3-sonnet-20240229-v1:0"  # Default model
        self.bedrock_account_id = bedrock_account_id
        self.bedrock_role_name = bedrock_role_name or 'BedrockAccessRole'
        self.bedrock_region = bedrock_region
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.auth_method = None  # 'keys' or 'role' or 'same-account'
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Bedrock client with multiple authentication methods."""
        try:
            # Try access keys first if provided
            if self.access_key_id and self.secret_access_key:
                print(f"DEBUG: Attempting Bedrock access with access keys")
                try:
                    self.bedrock_client = boto3.client(
                        'bedrock-runtime',
                        region_name=self.bedrock_region,
                        aws_access_key_id=self.access_key_id,
                        aws_secret_access_key=self.secret_access_key
                    )
                    self.auth_method = 'keys'
                    print(f"DEBUG: Bedrock client initialized with access keys")
                    return
                except Exception as e:
                    print(f"DEBUG: Access key authentication failed: {e}")
            
            # Try cross-account role if configured
            if self.bedrock_account_id and not (self.access_key_id and self.secret_access_key):
                print(f"DEBUG: Attempting cross-account Bedrock access to account {self.bedrock_account_id}")
                try:
                    aws_session = get_aws_session()
                    if not aws_session:
                        print("DEBUG: Failed to create AWS session for cross-account access")
                        return
                    
                    # Create STS client to assume cross-account role
                    sts_client = aws_session.client('sts')
                    
                    # Assume role in the Bedrock account
                    role_arn = f"arn:aws:iam::{self.bedrock_account_id}:role/{self.bedrock_role_name}"
                    print(f"DEBUG: Assuming role: {role_arn}")
                    
                    assumed_role = sts_client.assume_role(
                        RoleArn=role_arn,
                        RoleSessionName='TorWAR-Bedrock-Session',
                        DurationSeconds=3600  # 1 hour session
                    )
                    
                    # Create Bedrock client with assumed role credentials
                    credentials = assumed_role['Credentials']
                    self.bedrock_client = boto3.client(
                        'bedrock-runtime',
                        region_name=self.bedrock_region,
                        aws_access_key_id=credentials['AccessKeyId'],
                        aws_secret_access_key=credentials['SecretAccessKey'],
                        aws_session_token=credentials['SessionToken']
                    )
                    
                    self.auth_method = 'role'
                    print(f"DEBUG: Cross-account Bedrock client initialized successfully")
                    return
                    
                except Exception as e:
                    print(f"DEBUG: Cross-account Bedrock access failed: {e}")
            
            # Fallback to same-account access
            try:
                aws_session = get_aws_session()
                if aws_session:
                    self.bedrock_client = aws_session.client(
                        'bedrock-runtime',
                        region_name=self.bedrock_region
                    )
                    self.auth_method = 'same-account'
                    print("DEBUG: Same-account Bedrock client initialized successfully")
            except Exception as e:
                print(f"DEBUG: Same-account Bedrock access also failed: {e}")
                
        except Exception as e:
            print(f"DEBUG: Error initializing Bedrock client: {e}")
    
    def configure_access_keys(self, access_key_id, secret_access_key, region='us-east-1', account_id=None):
        """Configure Bedrock access using AWS access keys."""
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.bedrock_region = region
        self.bedrock_account_id = account_id  # Store the account ID for reference
        
        print(f"DEBUG: Configuring Bedrock access with access keys")
        print(f"  Access Key ID: {access_key_id[:8]}...")
        print(f"  Region: {region}")
        if account_id:
            print(f"  Account ID: {account_id}")
        
        # Reinitialize client with new configuration
        self._initialize_client()
        
        return self.bedrock_client is not None
    
    def configure_cross_account_access(self, account_id, role_name='BedrockAccessRole', region='us-east-1'):
        """Configure cross-account Bedrock access."""
        self.bedrock_account_id = account_id
        self.bedrock_role_name = role_name
        self.bedrock_region = region
        self.access_key_id = None  # Clear access key settings
        self.secret_access_key = None
        
        print(f"DEBUG: Configuring cross-account Bedrock access:")
        print(f"  Account ID: {account_id}")
        print(f"  Role Name: {role_name}")
        print(f"  Region: {region}")
        
        # Reinitialize client with new configuration
        self._initialize_client()
        
        return self.bedrock_client is not None
    
    def test_bedrock_access(self):
        """Test Bedrock access and return status."""
        if not self.bedrock_client:
            return {
                'status': 'failed',
                'error': 'No Bedrock client available',
                'auth_method': 'none'
            }
        
        try:
            # Test with a simple prompt
            test_prompt = "Hello, this is a test. Please respond with 'Bedrock is working'."
            
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 100,
                "messages": [
                    {
                        "role": "user",
                        "content": test_prompt
                    }
                ]
            }
            
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body)
            )
            
            response_body = json.loads(response['body'].read())
            response_text = response_body['content'][0]['text']
            
            return {
                'status': 'success',
                'response': response_text,
                'auth_method': self.auth_method,
                'account_id': self.bedrock_account_id,
                'region': self.bedrock_region,
                'model': self.model_id,
                'access_key_id': self.access_key_id[:8] + '...' if self.access_key_id else None
            }
            
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e),
                'auth_method': self.auth_method or 'unknown'
            }
    
    def generate_actionable_remediation(self, recommendation, affected_resources):
        """Generate AI-powered actionable remediation steps."""
        if not self.bedrock_client:
            return self._fallback_remediation(recommendation)
        
        try:
            # Prepare context for AI
            context = self._prepare_recommendation_context(recommendation, affected_resources)
            
            # Generate AI response
            prompt = self._build_remediation_prompt(context)
            response = self._invoke_bedrock_model(prompt)
            
            if response:
                return self._parse_remediation_response(response)
            else:
                return self._fallback_remediation(recommendation)
                
        except Exception as e:
            print(f"DEBUG: Error generating AI remediation: {e}")
            return self._fallback_remediation(recommendation)
    
    def analyze_recommendation_priority(self, recommendation, affected_resources):
        """AI-powered priority analysis."""
        if not self.bedrock_client:
            return self._fallback_priority_analysis(recommendation)
        
        try:
            context = self._prepare_recommendation_context(recommendation, affected_resources)
            prompt = self._build_priority_analysis_prompt(context)
            response = self._invoke_bedrock_model(prompt)
            
            if response:
                return self._parse_priority_response(response)
            else:
                return self._fallback_priority_analysis(recommendation)
                
        except Exception as e:
            print(f"DEBUG: Error analyzing priority: {e}")
            return self._fallback_priority_analysis(recommendation)
    
    def generate_remediation_code(self, recommendation, affected_resources, code_type="cli"):
        """Generate executable code for remediation."""
        if not self.bedrock_client:
            return self._fallback_code_generation(recommendation, code_type)
        
        try:
            context = self._prepare_recommendation_context(recommendation, affected_resources)
            prompt = self._build_code_generation_prompt(context, code_type)
            response = self._invoke_bedrock_model(prompt)
            
            if response:
                return self._parse_code_response(response, code_type)
            else:
                return self._fallback_code_generation(recommendation, code_type)
                
        except Exception as e:
            print(f"DEBUG: Error generating code: {e}")
            return self._fallback_code_generation(recommendation, code_type)
    
    def chat_about_recommendation(self, recommendation, affected_resources, user_question):
        """Interactive chat about specific recommendation with enhanced context."""
        if not self.bedrock_client:
            # Provide intelligent fallback response based on the question and recommendation
            return self._generate_fallback_chat_response(recommendation, affected_resources, user_question)
        
        try:
            context = self._prepare_recommendation_context(recommendation, affected_resources)
            prompt = self._build_chat_prompt(context, user_question)
            response = self._invoke_bedrock_model(prompt)
            
            return response if response else self._generate_fallback_chat_response(recommendation, affected_resources, user_question)
            
        except Exception as e:
            print(f"DEBUG: Error in chat: {e}")
            return self._generate_fallback_chat_response(recommendation, affected_resources, user_question)
    
    def _generate_fallback_chat_response(self, recommendation, affected_resources, user_question):
        """Generate intelligent fallback response when Bedrock is not available."""
        rec_name = recommendation.get('name', 'Unknown')
        rec_status = recommendation.get('status', 'unknown')
        rec_category = recommendation.get('category', 'unknown')
        resource_count = len(affected_resources)
        
        # Analyze the question to provide relevant response
        question_lower = user_question.lower()
        
        if any(word in question_lower for word in ['urgent', 'priority', 'important', 'critical']):
            if rec_status == 'error':
                return f"This recommendation '{rec_name}' has ERROR status, indicating high priority. With {resource_count} affected resources, you should address this immediately. Error status typically means there are security risks, compliance issues, or service disruptions that need urgent attention."
            elif rec_status == 'warning':
                return f"This recommendation '{rec_name}' has WARNING status, indicating medium priority. With {resource_count} affected resources, you should plan to address this within days or weeks. Warning status suggests potential issues that could become problems if not addressed."
            else:
                return f"This recommendation '{rec_name}' has OK status, indicating low priority. The {resource_count} resources are currently compliant, but you should monitor them regularly."
        
        elif any(word in question_lower for word in ['fix', 'solve', 'remediate', 'address']):
            if rec_category == 'security':
                return f"To address this security recommendation '{rec_name}': 1) Review the {resource_count} affected resources, 2) Identify security gaps or misconfigurations, 3) Apply security best practices, 4) Enable appropriate security controls, 5) Monitor for compliance. Security recommendations should be prioritized to protect your AWS environment."
            elif rec_category == 'cost_optimizing':
                return f"To address this cost optimization recommendation '{rec_name}': 1) Analyze the {resource_count} affected resources for cost inefficiencies, 2) Right-size underutilized resources, 3) Consider reserved instances or savings plans, 4) Remove unused resources, 5) Implement cost monitoring. This can help reduce your AWS bill."
            else:
                return f"To address this {rec_category} recommendation '{rec_name}': 1) Review the {resource_count} affected resources, 2) Understand the specific issues identified, 3) Plan remediation steps, 4) Implement fixes systematically, 5) Monitor for improvements. Follow AWS best practices for the {rec_category} category."
        
        elif any(word in question_lower for word in ['risk', 'impact', 'consequence']):
            if rec_status == 'error':
                return f"The risks of not addressing '{rec_name}' (ERROR status) include: potential security vulnerabilities, compliance violations, service disruptions, or performance issues. With {resource_count} affected resources, the impact could be significant across your AWS environment."
            else:
                return f"Not addressing '{rec_name}' may lead to: reduced efficiency, potential cost increases, security gaps, or operational issues. While the current status is {rec_status}, it's good practice to address recommendations proactively."
        
        elif any(word in question_lower for word in ['cost', 'money', 'expensive', 'bill']):
            if rec_category == 'cost_optimizing':
                return f"This cost optimization recommendation '{rec_name}' affects {resource_count} resources and could help reduce your AWS costs. Common cost-saving actions include: rightsizing instances, using reserved capacity, removing unused resources, and optimizing storage classes."
            else:
                return f"While '{rec_name}' is not primarily a cost recommendation, addressing it properly can prevent future costs from security incidents, performance issues, or operational overhead. The {resource_count} affected resources should be optimized as part of good AWS governance."
        
        else:
            # General response
            return f"Regarding '{rec_name}': This is a {rec_category} recommendation with {rec_status} status affecting {resource_count} resources. It's part of AWS Trusted Advisor's guidance to help optimize your AWS environment. For specific implementation details, consider enabling Bedrock AI for more detailed responses, or consult AWS documentation for this recommendation type."
    
    def _prepare_recommendation_context(self, recommendation, affected_resources):
        """Prepare comprehensive context data for AI prompts."""
        
        # Extract detailed resource information
        resource_details = []
        for resource in affected_resources[:20]:  # Limit to first 20 for context size
            resource_info = {
                'resourceId': resource.get('resourceId', 'N/A'),
                'status': resource.get('status', 'unknown'),
                'regionCode': resource.get('regionCode', 'N/A'),
                'lastUpdatedAt': resource.get('lastUpdatedAt', ''),
                'metadata': resource.get('metadata', [])
            }
            
            # Add ARN if available
            if resource.get('arn'):
                resource_info['arn'] = resource.get('arn')
            if resource.get('awsResourceId'):
                resource_info['awsResourceId'] = resource.get('awsResourceId')
                
            resource_details.append(resource_info)
        
        # Count resources by status
        status_counts = {
            'error': sum(1 for r in affected_resources if r.get('status') == 'error'),
            'warning': sum(1 for r in affected_resources if r.get('status') == 'warning'),
            'ok': sum(1 for r in affected_resources if r.get('status') == 'ok')
        }
        
        # Extract regions
        regions = list(set(r.get('regionCode', 'unknown') for r in affected_resources if r.get('regionCode')))
        
        return {
            'recommendation': {
                'name': recommendation.get('name', 'Unknown'),
                'description': recommendation.get('description', ''),
                'status': recommendation.get('status', 'unknown'),
                'category': recommendation.get('category', 'unknown'),
                'pillar': recommendation.get('pillar', 'unknown'),
                'aws_services': recommendation.get('aws_services', []),
                'error_count': recommendation.get('error_count', 0),
                'warning_count': recommendation.get('warning_count', 0),
                'ok_count': recommendation.get('ok_count', 0),
                'recommendationIdentifier': recommendation.get('recommendationIdentifier', ''),
                'arn': recommendation.get('arn', ''),
                'id': recommendation.get('id', ''),
                'source': recommendation.get('source', 'trusted_advisor')
            },
            'affected_resources': resource_details,
            'total_resources': len(affected_resources),
            'status_counts': status_counts,
            'regions_affected': regions,
            'resource_summary': {
                'total': len(affected_resources),
                'by_status': status_counts,
                'by_region': {region: sum(1 for r in affected_resources if r.get('regionCode') == region) 
                             for region in regions}
            }
        }
    
    def _build_remediation_prompt(self, context):
        """Build prompt for remediation generation."""
        return f"""
You are an AWS Well-Architected expert helping to create actionable remediation plans.

RECOMMENDATION DETAILS:
- Name: {context['recommendation']['name']}
- Description: {context['recommendation']['description']}
- Status: {context['recommendation']['status']}
- Category: {context['recommendation']['category']}
- Well-Architected Pillar: {context['recommendation']['pillar']}
- AWS Services: {', '.join(context['recommendation']['aws_services'])}
- Resources Affected: {context['total_resources']} total
  - Error: {context['recommendation']['error_count']}
  - Warning: {context['recommendation']['warning_count']}
  - OK: {context['recommendation']['ok_count']}

AFFECTED RESOURCES SAMPLE:
{json.dumps(context['affected_resources'], indent=2)}

Please provide a comprehensive, actionable remediation plan with:

1. **Immediate Actions** (0-24 hours)
2. **Short-term Actions** (1-7 days)  
3. **Long-term Actions** (1-4 weeks)
4. **Specific Steps** for each affected resource type
5. **Risk Mitigation** strategies
6. **Validation Steps** to confirm remediation
7. **Prevention Measures** to avoid recurrence

Format your response as structured JSON with clear action items, timelines, and specific AWS commands where applicable.
"""
    
    def _build_priority_analysis_prompt(self, context):
        """Build prompt for priority analysis."""
        return f"""
You are an AWS security and operations expert. Analyze this Trusted Advisor recommendation and provide a priority assessment.

RECOMMENDATION: {context['recommendation']['name']}
STATUS: {context['recommendation']['status']}
CATEGORY: {context['recommendation']['category']}
AFFECTED RESOURCES: {context['total_resources']}

Provide a JSON response with:
1. **priority_score** (1-10, where 10 is most critical)
2. **business_impact** (Low/Medium/High/Critical)
3. **security_risk** (Low/Medium/High/Critical)
4. **cost_impact** (Low/Medium/High)
5. **effort_required** (Low/Medium/High)
6. **recommended_timeline** (Immediate/Days/Weeks/Months)
7. **justification** (detailed explanation)

Consider factors like security implications, cost impact, compliance requirements, and operational risk.
"""
    
    def _build_code_generation_prompt(self, context, code_type):
        """Build prompt for code generation."""
        code_types = {
            'cli': 'AWS CLI commands',
            'cloudformation': 'CloudFormation template',
            'terraform': 'Terraform configuration',
            'python': 'Python boto3 script',
            'powershell': 'PowerShell script'
        }
        
        return f"""
Generate {code_types.get(code_type, 'AWS CLI commands')} to remediate this Trusted Advisor recommendation:

RECOMMENDATION: {context['recommendation']['name']}
DESCRIPTION: {context['recommendation']['description']}
AFFECTED RESOURCES: {json.dumps(context['affected_resources'], indent=2)}

Requirements:
1. Provide working, executable code
2. Include error handling
3. Add comments explaining each step
4. Consider resource dependencies
5. Include validation commands
6. Make it production-ready

Return only the code with appropriate formatting and comments.
"""
    
    def _build_chat_prompt(self, context, user_question):
        """Build comprehensive prompt for chat interaction."""
        
        # Build resource summary
        resource_summary = ""
        if context['affected_resources']:
            resource_summary = f"""
AFFECTED RESOURCES DETAILS:
- Total Resources: {context['total_resources']}
- Status Breakdown: {context['status_counts']['error']} errors, {context['status_counts']['warning']} warnings, {context['status_counts']['ok']} ok
- Regions: {', '.join(context['regions_affected'])}

SAMPLE RESOURCES:
{json.dumps(context['affected_resources'][:5], indent=2)}
"""
        
        return f"""
You are an AWS expert assistant specializing in Trusted Advisor recommendations and AWS best practices.

RECOMMENDATION DETAILS:
- Name: {context['recommendation']['name']}
- Description: {context['recommendation']['description']}
- Status: {context['recommendation']['status']} 
- Category: {context['recommendation']['category']}
- Well-Architected Pillar: {context['recommendation']['pillar']}
- AWS Services: {', '.join(context['recommendation']['aws_services']) if context['recommendation']['aws_services'] else 'Not specified'}
- Recommendation ID: {context['recommendation']['recommendationIdentifier']}

{resource_summary}

RESOURCE DISTRIBUTION BY REGION:
{json.dumps(context['resource_summary']['by_region'], indent=2)}

USER QUESTION: {user_question}

Please provide a detailed, helpful response about this specific Trusted Advisor recommendation. Consider:

1. **Context**: This is a real AWS environment with {context['total_resources']} affected resources
2. **Urgency**: Status is "{context['recommendation']['status']}" with {context['status_counts']['error']} errors and {context['status_counts']['warning']} warnings
3. **Scope**: Resources are distributed across {len(context['regions_affected'])} regions: {', '.join(context['regions_affected'])}
4. **Practical Guidance**: Provide specific AWS CLI commands, console steps, or code examples where relevant
5. **Best Practices**: Include AWS Well-Architected Framework guidance
6. **Risk Assessment**: Explain potential impacts of not addressing this recommendation
7. **Implementation**: Suggest step-by-step remediation approach

Be specific, actionable, and consider the actual resource details provided above.
"""
    
    def _invoke_bedrock_model(self, prompt):
        """Invoke Bedrock model with the given prompt."""
        try:
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body)
            )
            
            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text']
            
        except Exception as e:
            print(f"DEBUG: Error invoking Bedrock model: {e}")
            return None
    
    def _parse_remediation_response(self, response):
        """Parse AI remediation response."""
        try:
            # Try to parse as JSON first
            if response.strip().startswith('{'):
                return json.loads(response)
            else:
                # If not JSON, structure the text response
                return {
                    'type': 'text',
                    'content': response,
                    'generated_at': datetime.now().isoformat(),
                    'source': 'bedrock_ai'
                }
        except:
            return {
                'type': 'text',
                'content': response,
                'generated_at': datetime.now().isoformat(),
                'source': 'bedrock_ai'
            }
    
    def _parse_priority_response(self, response):
        """Parse AI priority analysis response."""
        try:
            if response.strip().startswith('{'):
                return json.loads(response)
            else:
                # Extract priority info from text
                return {
                    'priority_score': 5,
                    'business_impact': 'Medium',
                    'analysis': response,
                    'generated_at': datetime.now().isoformat()
                }
        except:
            return {
                'priority_score': 5,
                'business_impact': 'Medium',
                'analysis': response,
                'generated_at': datetime.now().isoformat()
            }
    
    def _parse_code_response(self, response, code_type):
        """Parse AI code generation response."""
        return {
            'code_type': code_type,
            'code': response,
            'generated_at': datetime.now().isoformat(),
            'language': code_type
        }
    
    def _fallback_remediation(self, recommendation):
        """Fallback remediation when AI is not available."""
        status = recommendation.get('status', 'unknown')
        category = recommendation.get('category', 'unknown')
        
        if status == 'error':
            timeline = {
                'immediate': ['Assess impact on critical systems', 'Identify affected resources', 'Plan emergency fixes'],
                'short_term': ['Implement fixes for high-priority resources', 'Test changes in staging', 'Monitor for issues'],
                'long_term': ['Complete remediation for all resources', 'Implement preventive measures', 'Update documentation']
            }
        else:
            timeline = {
                'planning': ['Review affected resources', 'Plan maintenance windows', 'Prepare remediation steps'],
                'implementation': ['Execute remediation plan', 'Validate changes', 'Update monitoring'],
                'ongoing': ['Monitor compliance', 'Prevent recurrence', 'Regular reviews']
            }
        
        return {
            'type': 'structured',
            'timeline': timeline,
            'category': category,
            'generated_at': datetime.now().isoformat(),
            'source': 'fallback'
        }
    
    def _fallback_priority_analysis(self, recommendation):
        """Fallback priority analysis."""
        status = recommendation.get('status', 'unknown')
        error_count = recommendation.get('error_count', 0)
        
        if status == 'error':
            priority_score = min(8 + (error_count // 10), 10)
            business_impact = 'High' if error_count > 5 else 'Medium'
        elif status == 'warning':
            priority_score = 5
            business_impact = 'Medium'
        else:
            priority_score = 3
            business_impact = 'Low'
        
        return {
            'priority_score': priority_score,
            'business_impact': business_impact,
            'security_risk': 'Medium' if status == 'error' else 'Low',
            'recommended_timeline': 'Immediate' if status == 'error' else 'Days',
            'generated_at': datetime.now().isoformat(),
            'source': 'fallback'
        }
    
    def _fallback_code_generation(self, recommendation, code_type):
        """Fallback code generation."""
        return {
            'code_type': code_type,
            'code': f'# Remediation code for: {recommendation.get("name", "Unknown")}\n# Please implement specific steps based on your environment\necho "Manual remediation required"',
            'generated_at': datetime.now().isoformat(),
            'source': 'fallback'
        }

# Global instance
bedrock_analyzer = BedrockRecommendationAnalyzer()

def get_bedrock_analyzer():
    """Get the global Bedrock analyzer instance."""
    return bedrock_analyzer

def configure_cross_account_bedrock(account_id, role_name='BedrockAccessRole', region='us-east-1'):
    """Configure cross-account Bedrock access globally."""
    global bedrock_analyzer
    return bedrock_analyzer.configure_cross_account_access(account_id, role_name, region)
