"""
TorWAR Trusted Advisor Integration
Author: Mohamed Toraif
Description: AWS Trusted Advisor recommendations integration using the new Trusted Advisor API
Updated: 2025-09-28 - Updated to use Trusted Advisor API instead of Support API
"""

import boto3
import json
from datetime import datetime, timezone
from botocore.exceptions import ClientError, NoCredentialsError
from aws_helper import get_aws_session

def get_trusted_advisor_client():
    """Get AWS Trusted Advisor client using the new TrustedAdvisor service."""
    try:
        aws_session = get_aws_session()
        if not aws_session:
            return None
        
        # Use the new trustedadvisor service
        print("DEBUG: Using Trusted Advisor API service...")
        ta_client = aws_session.client('trustedadvisor', region_name='us-east-1')
        return ta_client
        
    except Exception as e:
        print(f"❌ Error creating Trusted Advisor client: {e}")
        return None

def get_all_trusted_advisor_recommendations():
    """Get all Trusted Advisor recommendations using the new API."""
    try:
        client = get_trusted_advisor_client()
        if not client:
            return {'error': 'Could not create Trusted Advisor client'}
        
        print("🔍 Fetching recommendations using Trusted Advisor API...")
        
        # Get all recommendations using the new API
        recommendations = []
        paginator = client.get_paginator('list_recommendations')
        
        for page in paginator.paginate():
            for rec in page.get('recommendationSummaries', []):
                try:
                    # Get detailed recommendation info
                    detail_response = client.get_recommendation(
                        recommendationId=rec['id']
                    )
                    
                    recommendation_detail = detail_response.get('recommendation', {})
                    
                    # Process the recommendation data
                    processed_rec = {
                        'id': rec['id'],
                        'checkId': rec['id'],  # For backward compatibility
                        'name': rec.get('name', 'Unknown Check'),
                        'type': rec.get('type', 'unknown'),
                        'status': rec.get('status', 'unknown').lower(),
                        'pillar': rec.get('pillarOfWellArchitectedFramework', 'operational_excellence'),
                        'category': map_pillar_to_category(rec.get('pillarOfWellArchitectedFramework', 'operational_excellence')),
                        'description': recommendation_detail.get('description', ''),
                        'resource_count': len(recommendation_detail.get('resourcesAggregates', {}).get('resources', [])),
                        'resources': recommendation_detail.get('resourcesAggregates', {}).get('resources', []),
                        'check_metadata': {
                            'source': rec.get('source', 'trusted_advisor'),
                            'arn': rec.get('arn', ''),
                            'created_at': rec.get('createdAt', ''),
                            'last_updated_at': rec.get('lastUpdatedAt', ''),
                            'lifecycle_stage': rec.get('lifecycleStage', ''),
                            'update_reason': rec.get('updateReason', ''),
                            'update_reason_code': rec.get('updateReasonCode', ''),
                            'pillar': rec.get('pillarOfWellArchitectedFramework', '')
                        }
                    }
                    
                    recommendations.append(processed_rec)
                    print(f"DEBUG: Processed {processed_rec['name']}: {processed_rec['status']} ({processed_rec['resource_count']} resources)")
                    
                except Exception as detail_error:
                    print(f"❌ Error getting recommendation details for {rec.get('id', 'unknown')}: {detail_error}")
                    # Add basic info even if details fail
                    basic_rec = {
                        'id': rec['id'],
                        'checkId': rec['id'],
                        'name': rec.get('name', 'Unknown Check'),
                        'type': rec.get('type', 'unknown'),
                        'status': rec.get('status', 'unknown').lower(),
                        'pillar': rec.get('pillarOfWellArchitectedFramework', 'operational_excellence'),
                        'category': map_pillar_to_category(rec.get('pillarOfWellArchitectedFramework', 'operational_excellence')),
                        'description': f"Recommendation: {rec.get('name', 'Unknown')}",
                        'resource_count': 0,
                        'resources': [],
                        'check_metadata': {'source': 'trusted_advisor'}
                    }
                    recommendations.append(basic_rec)
                    continue
        
        print(f"✅ Successfully fetched {len(recommendations)} recommendations from Trusted Advisor API")
        
        return {
            'recommendations': recommendations,
            'total_count': len(recommendations),
            'source': 'trusted_advisor_api'
        }
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']
        
        if error_code == 'SubscriptionRequiredException':
            print("❌ Trusted Advisor requires Business or Enterprise support plan")
            return {'error': 'Trusted Advisor requires Business or Enterprise support plan'}
        elif error_code == 'UnauthorizedOperation':
            print("❌ Insufficient permissions for Trusted Advisor")
            return {'error': 'Insufficient permissions for Trusted Advisor API'}
        else:
            print(f"❌ AWS API Error: {error_code} - {error_msg}")
            return {'error': f'AWS API Error: {error_msg}'}
            
    except NoCredentialsError:
        print("❌ No AWS credentials found")
        return {'error': 'No AWS credentials configured'}
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return {'error': f'Unexpected error: {str(e)}'}

def map_pillar_to_category(pillar):
    """Map Well-Architected pillar to category."""
    pillar_mapping = {
        'cost_optimization': 'cost_optimizing',
        'security': 'security',
        'reliability': 'fault_tolerance',
        'performance_efficiency': 'performance',
        'operational_excellence': 'operational_excellence',
        'sustainability': 'operational_excellence'  # Map sustainability to operational excellence
    }
    
    return pillar_mapping.get(pillar.lower(), 'operational_excellence')

def get_recommendation_details(recommendation_id):
    """Get detailed information for a specific recommendation."""
    try:
        client = get_trusted_advisor_client()
        if not client:
            return {'error': 'Could not create Trusted Advisor client'}
        
        response = client.get_recommendation(recommendationId=recommendation_id)
        return response.get('recommendation', {})
        
    except Exception as e:
        print(f"❌ Error getting recommendation details: {e}")
        return {'error': str(e)}
            )
            print("DEBUG: Support service client created successfully")
            return support_client
        except Exception as e1:
            print(f"DEBUG: Support service failed: {e1}")
        
        try:
            # Second try: Try the newer TrustedAdvisor Public API if available
            print("DEBUG: Trying TrustedAdvisor Public API...")
            import boto3
            ta_client = boto3.client(
                'trustedadvisor',
                region_name='us-east-1'
            )
            print("DEBUG: TrustedAdvisor Public API client created successfully")
            return ta_client
        except Exception as e2:
            print(f"DEBUG: TrustedAdvisor Public API failed: {e2}")
        
        try:
            # Third try: Use support service (traditional Trusted Advisor API) as fallback
            print("DEBUG: Trying support service client as fallback...")
            support_client = aws_session.client(
                'support',
                region_name='us-east-1'
            )
            # Test if it has the methods we need
            if hasattr(support_client, 'describe_trusted_advisor_checks'):
                print("DEBUG: Support service client created successfully")
                return support_client
        except Exception as e3:
            print(f"DEBUG: Support service failed: {e3}")
            return None
                    
    except Exception as e:
        print(f"Error creating Trusted Advisor client: {e}")
        return None

def get_trusted_advisor_summary():
    """Get a summary of Trusted Advisor recommendations for dashboard, handling pagination."""
    try:
        # Get the Trusted Advisor client
        client = get_trusted_advisor_client()
        if not client:
            return {
                'available': False,
                'error': 'Unable to create Trusted Advisor client',
                'summary': {}
            }
        
        try:
            # Get all recommendations with pagination to get accurate counts
            all_recommendations = []
            next_token = None
            page_count = 0
            
            while True:
                page_count += 1
                
                # Prepare the request parameters
                params = {}
                if next_token:
                    params['nextToken'] = next_token
                
                try:
                    response = client.list_recommendations(**params)
                    recommendations = response.get('recommendationSummaries', [])
                    all_recommendations.extend(recommendations)
                    
                    # Check if there are more pages
                    next_token = response.get('nextToken')
                    if not next_token:
                        break
                        
                    # Safety check to prevent infinite loops
                    if page_count > 50:  # Reasonable limit
                        break
                        
                except Exception as page_error:
                    print(f"Error fetching page {page_count}: {page_error}")
                    break
            
            print(f"Summary: Retrieved {len(all_recommendations)} total recommendations across {page_count} pages")
            
            # Count by status and category
            status_counts = {
                'error': 0,
                'warning': 0,
                'ok': 0
            }
            
            category_counts = {
                'security': 0,
                'cost_optimizing': 0,
                'performance': 0,
                'fault_tolerance': 0,
                'service_limits': 0,
                'operational_excellence': 0
            }
            
            # Process all recommendations
            for rec in all_recommendations:
                status = rec.get('status', '').lower()
                if status == 'error':
                    status_counts['error'] += 1
                elif status == 'warning':
                    status_counts['warning'] += 1
                elif status == 'ok':
                    status_counts['ok'] += 1
                
                # Get pillar information
                pillars_list = rec.get('pillars', [])
                pillar = pillars_list[0] if pillars_list else 'unknown'
                
                if pillar in category_counts:
                    category_counts[pillar] += 1
                else:
                    category_counts.setdefault(pillar, 0)
                    category_counts[pillar] += 1
            
            return {
                'available': True,
                'total_checks': len(all_recommendations),
                'status_counts': status_counts,
                'category_counts': category_counts,
                'total_flagged_resources': status_counts['error'] + status_counts['warning'],
                'last_updated': datetime.now(timezone.utc).isoformat(),
                'high_priority_count': status_counts['error'],
                'medium_priority_count': status_counts['warning'],
                'message': f"Found {status_counts['error']} high impact and {status_counts['warning']} medium impact recommendations"
            }
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            error_message = e.response.get('Error', {}).get('Message', str(e))
            
            if 'SubscriptionRequired' in error_code:
                return {
                    'available': False,
                    'error': 'Trusted Advisor requires Business or Enterprise support plan',
                    'summary': {}
                }
            elif '403' in str(e) or 'AccessDenied' in error_code:
                return {
                    'available': False,
                    'error': f'Insufficient permissions to access Trusted Advisor',
                    'summary': {}
                }
            else:
                return {
                    'available': False,
                    'error': f'Error accessing Trusted Advisor: {error_message}',
                    'summary': {}
                }
        
    except Exception as e:
        return {
            'available': False,
            'error': f'Error retrieving summary: {str(e)}',
            'summary': {}
        }

def get_all_trusted_advisor_recommendations():
    """Get all Trusted Advisor recommendations using Support API."""
    try:
        client = get_trusted_advisor_client()
        if not client:
            return {'error': 'Unable to create Trusted Advisor client'}
        
        print("DEBUG: Getting Trusted Advisor checks from Support API...")
        
        # Get all available checks first
        try:
            checks_response = client.describe_trusted_advisor_checks(language='en')
            checks = checks_response.get('checks', [])
            print(f"DEBUG: Found {len(checks)} available checks")
        except Exception as e:
            print(f"DEBUG: Error getting checks: {e}")
            return {'error': f'Error getting Trusted Advisor checks: {str(e)}'}
        
        recommendations = []
        categories = {}
        
        # Get results for each check
        for check in checks:
            check_id = check.get('id')
            check_name = check.get('name', 'Unknown')
            check_category = check.get('category', 'General')
            
            try:
                # Get check result
                result_response = client.describe_trusted_advisor_check_result(
                    checkId=check_id,
                    language='en'
                )
                
                result = result_response.get('result', {})
                status = result.get('status', 'unknown')
                
                # Map Support API status to our status
                if status == 'error':
                    mapped_status = 'error'
                elif status == 'warning':
                    mapped_status = 'warning'
                elif status == 'ok':
                    mapped_status = 'ok'
                else:
                    mapped_status = 'unknown'
                
                # Count resources
                flagged_resources = result.get('flaggedResources', [])
                resource_count = len(flagged_resources)
                
                recommendation = {
                    'id': check_id,
                    'name': check_name,
                    'category': check_category,
                    'pillar': check_category,  # Use category as pillar
                    'status': mapped_status,
                    'description': check.get('description', ''),
                    'resource_count': resource_count,
                    'resources': flagged_resources[:10],  # Store first 10 resources
                    'timestamp': result.get('timestamp', ''),
                    'check_metadata': check
                }
                
                recommendations.append(recommendation)
                
                # Group by category
                if check_category not in categories:
                    categories[check_category] = []
                categories[check_category].append(recommendation)
                
                print(f"DEBUG: Processed {check_name}: {mapped_status} ({resource_count} resources)")
                
            except Exception as e:
                print(f"DEBUG: Error getting result for check {check_name}: {e}")
                continue
        
        print(f"DEBUG: Successfully processed {len(recommendations)} recommendations")
        
        return {
            'recommendations': recommendations,
            'categories': categories,
            'total_recommendations': len(recommendations),
            'last_updated': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"DEBUG: Error in get_all_trusted_advisor_recommendations: {e}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}

def get_trusted_advisor_summary():
    """Get a summary of Trusted Advisor recommendations for dashboard."""
    try:
        # Get the Trusted Advisor client
        client = get_trusted_advisor_client()
        if not client:
            return {
                'available': False,
                'error': 'Unable to create Trusted Advisor client',
                'summary': {}
            }
        
        # Get all checks and their results
        try:
            checks_response = client.describe_trusted_advisor_checks(language='en')
            checks = checks_response.get('checks', [])
            
            status_counts = {'error': 0, 'warning': 0, 'ok': 0}
            category_counts = {}
            
            for check in checks:
                try:
                    result_response = client.describe_trusted_advisor_check_result(
                        checkId=check.get('id'),
                        language='en'
                    )
                    
                    result = result_response.get('result', {})
                    status = result.get('status', 'unknown')
                    category = check.get('category', 'General')
                    
                    # Count by status
                    if status in status_counts:
                        status_counts[status] += 1
                    
                    # Count by category
                    if category not in category_counts:
                        category_counts[category] = {'error': 0, 'warning': 0, 'ok': 0}
                    if status in category_counts[category]:
                        category_counts[category][status] += 1
                        
                except Exception as e:
                    print(f"DEBUG: Error getting result for check {check.get('name')}: {e}")
                    continue
            
            return {
                'available': True,
                'summary': {
                    'total_checks': len(checks),
                    'status_counts': status_counts,
                    'category_counts': category_counts
                }
            }
            
        except Exception as e:
            print(f"DEBUG: Error getting summary: {e}")
            return {
                'available': False,
                'error': str(e),
                'summary': {}
            }
            
    except Exception as e:
        print(f"DEBUG: Error in get_trusted_advisor_summary: {e}")
        return {
            'available': False,
            'error': str(e),
            'summary': {}
        }

def get_trusted_advisor_check_categories():
    """Get available Trusted Advisor check categories."""
    try:
        client = get_trusted_advisor_client()
        if not client:
            return {}
        
        checks_response = client.describe_trusted_advisor_checks(language='en')
        checks = checks_response.get('checks', [])
        
        categories = {}
        for check in checks:
            category = check.get('category', 'General')
            if category not in categories:
                categories[category] = []
            categories[category].append(check)
        
        return categories
        
    except Exception as e:
        print(f"DEBUG: Error getting check categories: {e}")
        return {}
    except Exception as e:
        print(f"Exception in get_all_trusted_advisor_recommendations: {e}")
        return {
            'error': f'Error retrieving recommendations: {str(e)}',
            'recommendations': []
        }

def get_severity_from_status(status):
    """Convert Trusted Advisor status to severity level."""
    status_map = {
        'error': 'high',
        'warning': 'medium',
        'ok': 'low',
        'not_available': 'info'
    }
    return status_map.get(status.lower(), 'info')

def get_trusted_advisor_checks():
    """Get all available Trusted Advisor checks using the newer list_checks API."""
    try:
        client = get_trusted_advisor_client()
        if not client:
            return None
        
        # Use the newer list_checks API
        response = client.list_checks(language='en')
        return response.get('checks', [])
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'SubscriptionRequiredError':
            print("Trusted Advisor requires Business or Enterprise support plan")
            return None
        else:
            print(f"Error getting Trusted Advisor checks: {e}")
            return None
    except Exception as e:
        print(f"Unexpected error getting Trusted Advisor checks: {e}")
        return None

def get_trusted_advisor_check_result(check_id):
    """Get result for a specific Trusted Advisor check using the newer API."""
    try:
        client = get_trusted_advisor_client()
        if not client:
            return None
        
        # Use the newer get_check_result API
        response = client.get_check_result(checkId=check_id)
        return response.get('result')
    except Exception as e:
        print(f"Error getting check result for {check_id}: {e}")
        return None

def refresh_trusted_advisor_check(check_id):
    """Refresh a specific Trusted Advisor check."""
    try:
        client = get_trusted_advisor_client()
        if not client:
            return False
        
        # Use the newer refresh_check API
        client.refresh_check(checkId=check_id)
        return True
    except Exception as e:
        print(f"Error refreshing check {check_id}: {e}")
        return False

def get_trusted_advisor_check_categories():
    """Get available Trusted Advisor categories."""
    return {
        'cost_optimizing': {
            'name': 'Cost Optimization',
            'description': 'Recommendations to reduce costs',
            'icon': 'fas fa-dollar-sign',
            'color': 'success'
        },
        'performance': {
            'name': 'Performance',
            'description': 'Recommendations to improve performance',
            'icon': 'fas fa-tachometer-alt',
            'color': 'info'
        },
        'security': {
            'name': 'Security',
            'description': 'Security-related recommendations',
            'icon': 'fas fa-shield-alt',
            'color': 'danger'
        },
        'fault_tolerance': {
            'name': 'Fault Tolerance',
            'description': 'Recommendations for better resilience',
            'icon': 'fas fa-heartbeat',
            'color': 'warning'
        },
        'service_limits': {
            'name': 'Service Limits',
            'description': 'Service usage and limits monitoring',
            'icon': 'fas fa-chart-line',
            'color': 'secondary'
        },
        'operational_excellence': {
            'name': 'Operational Excellence',
            'description': 'Recommendations for operational best practices',
            'icon': 'fas fa-cogs',
            'color': 'primary'
        }
    }

def get_recommendation_details(recommendation_id):
    """Get detailed information for a specific recommendation including affected resources."""
    try:
        client = get_trusted_advisor_client()
        if not client:
            return {
                'error': 'Unable to create Trusted Advisor client',
                'recommendation': None,
                'affected_resources': []
            }
        
        print(f"DEBUG: Getting details for recommendation ID: {recommendation_id}")
        print(f"DEBUG: Client type: {type(client)}")
        
        # Check which service we're using and call appropriate methods
        service_name = 'unknown'
        if hasattr(client, '_service_model'):
            service_model = getattr(client, '_service_model')
            if hasattr(service_model, 'service_name'):
                service_name = service_model.service_name
        
        print(f"DEBUG: Client service: {service_name}")
        
        if service_name == 'support':
            return get_recommendation_details_support(client, recommendation_id)
        else:
            return get_recommendation_details_trustedadvisor(client, recommendation_id)
            
    except Exception as e:
        print(f"DEBUG: Outer exception: {str(e)}")
        return {
            'error': f'Error in get_recommendation_details: {str(e)}',
            'recommendation': None,
            'affected_resources': [],
            'remediation': None
        }

def get_recommendation_details_trustedadvisor(client, recommendation_id):
    """Get recommendation details using the trustedadvisor service."""
    try:
        print("DEBUG: Using trustedadvisor service API")
        
        # Get recommendation details - use only recommendationIdentifier
        print("DEBUG: Calling get_recommendation with recommendationIdentifier...")
        response = client.get_recommendation(recommendationIdentifier=recommendation_id)
        recommendation_data = response.get('recommendation', {})
        print("DEBUG: Successfully got recommendation details")
        
        # Get affected resources - use only recommendationIdentifier
        print("DEBUG: Calling list_recommendation_resources with recommendationIdentifier...")
        resources_response = client.list_recommendation_resources(
            recommendationIdentifier=recommendation_id
        )
        print("DEBUG: Successfully got recommendation resources")
        
        affected_resources = []
        resources = resources_response.get('recommendationResourceSummaries', [])
        
        for resource in resources:
            # Format datetime fields to strings
            last_updated = resource.get('lastUpdatedAt', '')
            if hasattr(last_updated, 'isoformat'):  # It's a datetime object
                last_updated = last_updated.isoformat()
            elif last_updated and not isinstance(last_updated, str):
                last_updated = str(last_updated)
            
            # Ensure metadata is always a list
            metadata = resource.get('metadata', [])
            if not isinstance(metadata, list):
                metadata = [str(metadata)] if metadata else []
            
            formatted_resource = {
                'resourceId': resource.get('resourceId', 'N/A'),
                'arn': resource.get('arn', ''),
                'awsResourceId': resource.get('awsResourceId', ''),
                'lastUpdatedAt': last_updated,
                'regionCode': resource.get('regionCode', 'N/A'),
                'status': resource.get('status', 'unknown'),
                'metadata': metadata
            }
            affected_resources.append(formatted_resource)
        
        print(f"DEBUG: Processed {len(affected_resources)} resources")
        
        # Get remediation information if available
        remediation_info = get_recommendation_remediation(recommendation_id)
        
        return {
            'recommendation': recommendation_data,
            'affected_resources': affected_resources,
            'remediation': remediation_info,
            'total_resources': len(affected_resources),
            'error': None
        }
        
    except Exception as e:
        print(f"DEBUG: trustedadvisor service error: {str(e)}")
        return {
            'error': f'Trustedadvisor API Error: {str(e)}',
            'recommendation': None,
            'affected_resources': [],
            'remediation': None
        }

def get_recommendation_details_support(client, recommendation_id):
    """Get recommendation details using the support service (traditional API)."""
    try:
        print("DEBUG: Using support service API")
        
        # The support service uses different methods
        # We need to get the check result using describe_trusted_advisor_check_result
        print(f"DEBUG: Calling describe_trusted_advisor_check_result with checkId: {recommendation_id}")
        
        try:
            response = client.describe_trusted_advisor_check_result(
                checkId=recommendation_id,
                language='en'
            )
            
            check_result = response.get('result', {})
            print("DEBUG: Successfully got check result from support service")
            
            # Format the response to match the expected structure
            recommendation_data = {
                'id': recommendation_id,
                'name': check_result.get('checkId', recommendation_id),
                'description': 'Detailed information from Support API',
                'status': check_result.get('status', 'unknown').lower()
            }
            
            # Get flagged resources
            affected_resources = []
            flagged_resources = check_result.get('flaggedResources', [])
            
            for resource in flagged_resources:
                formatted_resource = {
                    'resourceId': resource.get('resourceId', 'N/A'),
                    'arn': 'N/A',  # Support API doesn't provide ARN
                    'awsResourceId': resource.get('resourceId', 'N/A'),
                    'lastUpdatedAt': check_result.get('timestamp', ''),
                    'regionCode': resource.get('region', 'N/A'),
                    'status': resource.get('status', 'flagged'),
                    'metadata': resource.get('metadata', [])
                }
                affected_resources.append(formatted_resource)
            
            print(f"DEBUG: Processed {len(affected_resources)} flagged resources from support API")
            
            return {
                'recommendation': recommendation_data,
                'affected_resources': affected_resources,
                'remediation': None,  # Support API doesn't provide detailed remediation
                'total_resources': len(affected_resources),
                'error': None
            }
            
        except Exception as e:
            print(f"DEBUG: Support API call failed: {str(e)}")
            # If the specific check call fails, return empty but valid response
            return {
                'recommendation': {'id': recommendation_id, 'name': 'Unknown Check'},
                'affected_resources': [],
                'remediation': None,
                'total_resources': 0,
                'error': f'Support API Error: {str(e)}'
            }
        
    except Exception as e:
        print(f"DEBUG: Support service error: {str(e)}")
        return {
            'error': f'Support API Error: {str(e)}',
            'recommendation': None,
            'affected_resources': [],
            'remediation': None
        }

def get_recommendation_remediation(recommendation_id):
    """Get remediation information for a specific recommendation."""
    try:
        client = get_trusted_advisor_client()
        if not client:
            return None
        
        print(f"DEBUG: Getting remediation for recommendation ID: {recommendation_id}")
        
        # Check which service we're using
        service_name = 'unknown'
        if hasattr(client, '_service_model'):
            service_model = getattr(client, '_service_model')
            if hasattr(service_model, 'service_name'):
                service_name = service_model.service_name
        
        if service_name == 'support':
            return get_remediation_support(client, recommendation_id)
        else:
            return get_remediation_trustedadvisor(client, recommendation_id)
            
    except Exception as e:
        print(f"DEBUG: Error getting remediation info: {e}")
        return None

def get_remediation_trustedadvisor(client, recommendation_id):
    """Get remediation using trustedadvisor service."""
    try:
        # Use only recommendationIdentifier
        response = client.get_recommendation(recommendationIdentifier=recommendation_id)
        recommendation = response.get('recommendation', {})
        
        # Extract remediation information from the recommendation
        # Helper function to format datetime fields
        def format_datetime_field(field_value):
            if hasattr(field_value, 'isoformat'):  # It's a datetime object
                return field_value.isoformat()
            elif field_value and not isinstance(field_value, str):
                return str(field_value)
            return field_value or ''
        
        remediation_info = {
            'description': recommendation.get('description', ''),
            'resolvedAt': format_datetime_field(recommendation.get('resolvedAt')),
            'createdAt': format_datetime_field(recommendation.get('createdAt')),
            'lastUpdatedAt': format_datetime_field(recommendation.get('lastUpdatedAt')),
            'lifecycleStage': recommendation.get('lifecycleStage', ''),
            'updateReason': recommendation.get('updateReason', ''),
            'updateReasonCode': recommendation.get('updateReasonCode', ''),
            'pillarSpecificAggregates': recommendation.get('pillarSpecificAggregates', {}),
            'source': recommendation.get('source', ''),
            'type': recommendation.get('type', '')
        }
        
        print("DEBUG: Successfully got remediation info from trustedadvisor service")
        return remediation_info
        
    except Exception as e:
        print(f"DEBUG: Could not get remediation info from trustedadvisor service: {e}")
        return None

def get_remediation_support(client, recommendation_id):
    """Get remediation using support service."""
    try:
        # Support service doesn't have detailed remediation info
        # We can get basic check information
        response = client.describe_trusted_advisor_check_result(
            checkId=recommendation_id,
            language='en'
        )
        
        check_result = response.get('result', {})
        
        # Create basic remediation info from what's available
        remediation_info = {
            'description': f"Check status: {check_result.get('status', 'unknown')}",
            'resolvedAt': None,
            'createdAt': None,
            'lastUpdatedAt': check_result.get('timestamp', ''),
            'lifecycleStage': check_result.get('status', ''),
            'updateReason': '',
            'updateReasonCode': '',
            'pillarSpecificAggregates': {},
            'source': 'support',
            'type': 'trusted_advisor_check'
        }
        
        print("DEBUG: Successfully got basic remediation info from support service")
        return remediation_info
        
    except Exception as e:
        print(f"DEBUG: Could not get remediation info from support service: {e}")
        return None

def get_all_affected_resources_for_check(recommendation_id):
    """Get all affected resources for a specific check with pagination."""
    try:
        client = get_trusted_advisor_client()
        if not client:
            print("DEBUG: No Trusted Advisor client available")
            return []
        
        print(f"DEBUG: Getting all resources for recommendation ID: {recommendation_id}")
        
        # Check which service we're using
        service_name = 'unknown'
        if hasattr(client, '_service_model'):
            service_model = getattr(client, '_service_model')
            if hasattr(service_model, 'service_name'):
                service_name = service_model.service_name
        
        print(f"DEBUG: Using service: {service_name}")
        
        # Use the appropriate API based on the service
        if service_name == 'trustedadvisor':
            return get_affected_resources_trustedadvisor(client, recommendation_id)
        elif service_name == 'support':
            return get_affected_resources_support_legacy(client, recommendation_id)
        else:
            # Default to trustedadvisor API
            return get_affected_resources_trustedadvisor(client, recommendation_id)
        
    except Exception as e:
        print(f"DEBUG: Error getting affected resources: {e}")
        import traceback
        traceback.print_exc()
        return []

def get_affected_resources_trustedadvisor(client, recommendation_id):
    """Get affected resources using trustedadvisor service."""
    from flask import session
    
    all_resources = []
    next_token = None
    page_count = 0
    
    # Convert UUID to ARN format if needed
    if not recommendation_id.startswith('arn:'):
        # Get account ID from Flask session
        account_id = session.get('aws_account_id')
        if not account_id:
            print("DEBUG: No AWS account ID in session")
            return []
        
        recommendation_arn = f"arn:aws:trustedadvisor::{account_id}:recommendation/{recommendation_id}"
        print(f"DEBUG: Converted UUID to ARN: {recommendation_arn}")
    else:
        recommendation_arn = recommendation_id
    
    while True:
        page_count += 1
        print(f"DEBUG: Fetching page {page_count} of resources...")
        
        # Prepare the request parameters
        params = {'recommendationIdentifier': recommendation_arn}
        if next_token:
            params['nextToken'] = next_token
        
        try:
            response = client.list_recommendation_resources(**params)
            resources = response.get('recommendationResourceSummaries', [])
            print(f"DEBUG: Got {len(resources)} resources on page {page_count}")
            
            for resource in resources:
                # Format datetime fields to strings
                last_updated = resource.get('lastUpdatedAt', '')
                if hasattr(last_updated, 'isoformat'):  # It's a datetime object
                    last_updated = last_updated.isoformat()
                elif last_updated and not isinstance(last_updated, str):
                    last_updated = str(last_updated)
                
                # Ensure metadata is always a list
                metadata = resource.get('metadata', [])
                if not isinstance(metadata, list):
                    metadata = [str(metadata)] if metadata else []
                
                # Try to construct ARN from metadata if not provided
                resource_arn = resource.get('arn', '') or resource.get('resourceArn', '')
                if not resource_arn and metadata:
                    # For S3 buckets, the bucket name is often in metadata[0]
                    if len(metadata) > 0 and metadata[0]:
                        bucket_name = metadata[0]
                        if 'cf-templates' in bucket_name or bucket_name.startswith('cf-'):
                            resource_arn = f"arn:aws:s3:::{bucket_name}"
                        # Add other resource type ARN construction as needed
                
                formatted_resource = {
                    'resourceId': resource.get('resourceId', 'N/A'),
                    'arn': resource_arn,
                    'awsResourceId': resource.get('awsResourceId', ''),
                    'lastUpdatedAt': last_updated,
                    'regionCode': resource.get('regionCode', 'N/A'),
                    'status': resource.get('status', 'unknown'),
                    'metadata': metadata,
                    'exclusionStatus': resource.get('exclusionStatus', ''),
                    'resourceArn': resource.get('resourceArn', '')
                }
                all_resources.append(formatted_resource)
            
            # Check if there are more pages
            next_token = response.get('nextToken')
            if not next_token:
                break
                
            # Safety check to prevent infinite loops
            if page_count > 20:  # Reasonable limit for resources
                print("DEBUG: Reached maximum page limit (20)")
                break
                
        except Exception as page_error:
            print(f"DEBUG: Error fetching resources page {page_count}: {page_error}")
            break
    
    print(f"DEBUG: Retrieved {len(all_resources)} total resources for recommendation {recommendation_id}")
    return all_resources
    return all_resources

def get_affected_resources_support_legacy(client, recommendation_id):
    """Get affected resources using legacy support service."""
    try:
        print(f"DEBUG: Getting resources from support API for check: {recommendation_id}")
        
        # Create a separate support client for legacy API
        import boto3
        support_client = boto3.client('support', region_name='us-east-1')
        
        # The support API might need a different identifier format
        check_id = recommendation_id
        
        # If it's an ARN, extract the check ID part
        if recommendation_id.startswith('arn:aws:trustedadvisor:'):
            parts = recommendation_id.split('/')
            if len(parts) > 1:
                check_id = parts[-1]
                print(f"DEBUG: Extracted check ID from ARN: {check_id}")
        
        try:
            response = support_client.describe_trusted_advisor_check_result(
                checkId=check_id,
                language='en'
            )
        except Exception as e:
            print(f"DEBUG: Support API failed with check_id '{check_id}': {e}")
            if check_id != recommendation_id:
                print(f"DEBUG: Retrying with original recommendation_id: {recommendation_id}")
                response = support_client.describe_trusted_advisor_check_result(
                    checkId=recommendation_id,
                    language='en'
                )
            else:
                raise e
        
        check_result = response.get('result', {})
        flagged_resources = check_result.get('flaggedResources', [])
        
        all_resources = []
        for resource in flagged_resources:
            metadata = resource.get('metadata', [])
            if isinstance(metadata, dict):
                metadata = [f"{k}: {v}" for k, v in metadata.items()]
            elif not isinstance(metadata, list):
                metadata = [str(metadata)] if metadata else []
            
            formatted_resource = {
                'resourceId': resource.get('resourceId', 'N/A'),
                'arn': 'N/A',
                'awsResourceId': resource.get('resourceId', 'N/A'),
                'lastUpdatedAt': check_result.get('timestamp', ''),
                'regionCode': resource.get('region', 'N/A'),
                'status': resource.get('status', 'flagged'),
                'metadata': metadata,
                'exclusionStatus': '',
                'resourceArn': ''
            }
            all_resources.append(formatted_resource)
        
        print(f"DEBUG: Retrieved {len(all_resources)} flagged resources from support API")
        return all_resources
        
    except Exception as e:
        print(f"DEBUG: Support API error getting resources: {e}")
        import traceback
        traceback.print_exc()
        return []

def format_trusted_advisor_resource(resource, metadata):
    """Format a flagged resource for display."""
    try:
        formatted = {
            'id': resource.get('resourceId', 'N/A'),
            'status': resource.get('status', 'unknown'),
            'region': resource.get('region', 'N/A'),
            'metadata': {}
        }
        
        # Map metadata to readable format
        if metadata and len(resource.get('metadata', [])) >= len(metadata):
            for i, field in enumerate(metadata):
                if i < len(resource['metadata']):
                    formatted['metadata'][field['name']] = resource['metadata'][i]
        
        return formatted
    except Exception as e:
        print(f"Error formatting resource: {e}")
        return resource
