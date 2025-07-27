"""
TorWAR Trusted Advisor Integration
Author: Mohamed Toraif
Description: AWS Trusted Advisor recommendations integration for TorWAR
Updated: 2025-07-23 - Updated to use the latest Trusted Advisor APIs
"""

import boto3
import json
from datetime import datetime, timezone
from botocore.exceptions import ClientError, NoCredentialsError
from aws_helper import get_aws_session

def get_trusted_advisor_client():
    """Get AWS Trusted Advisor client."""
    try:
        from flask import session
        
        # Get session or create a new one
        aws_session = get_aws_session()
        if not aws_session:
            return None
        
        # Try different approaches to create the Trusted Advisor client
        # The CLI works without custom endpoint, so try that first
        try:
            # First try: Use standard trustedadvisor service (matches CLI behavior)
            print("DEBUG: Trying standard trustedadvisor service (CLI equivalent)...")
            ta_client = aws_session.client(
                'trustedadvisor', 
                region_name='us-east-1'
            )
            print("DEBUG: Standard trustedadvisor service client created successfully")
            return ta_client
        except Exception as e1:
            print(f"DEBUG: Standard trustedadvisor service failed: {e1}")
        
        try:
            # Second try: Use the newer trustedadvisor service with custom endpoint
            print("DEBUG: Trying trustedadvisor service with custom endpoint...")
            ta_client = aws_session.client(
                'trustedadvisor', 
                region_name='us-east-1',
                endpoint_url='https://trustedadvisor.us-east-1.api.aws'
            )
            print("DEBUG: Custom endpoint trustedadvisor service client created successfully")
            return ta_client
        except Exception as e2:
            print(f"DEBUG: Custom endpoint failed: {e2}")
        
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
    """Get all Trusted Advisor recommendations with their results, handling pagination."""
    try:
        # Get the Trusted Advisor client
        client = get_trusted_advisor_client()
        if not client:
            return {
                'error': 'Unable to create Trusted Advisor client',
                'recommendations': []
            }
        
        try:
            all_recommendations = []
            categories = {
                'security': [],
                'cost_optimizing': [],
                'performance': [],
                'fault_tolerance': [],
                'service_limits': [],
                'operational_excellence': []
            }
            
            # Get all recommendations with pagination
            next_token = None
            page_count = 0
            
            while True:
                page_count += 1
                print(f"Fetching page {page_count} of recommendations...")
                
                # Prepare the request parameters
                params = {}
                if next_token:
                    params['nextToken'] = next_token
                
                try:
                    response = client.list_recommendations(**params)
                    recommendations = response.get('recommendationSummaries', [])
                    print(f"Page {page_count}: Retrieved {len(recommendations)} recommendations")
                    
                    # Process recommendations from this page
                    for rec in recommendations:
                        # Map status - convert to lowercase for consistency
                        status = rec.get('status', '').lower()
                        
                        # Get pillar information - the API shows 'pillars' as a list
                        pillars_list = rec.get('pillars', [])
                        pillar = pillars_list[0] if pillars_list else 'unknown'
                        
                        # Get resources affected from resourcesAggregates
                        resources_aggregates = rec.get('resourcesAggregates', {})
                        error_count = resources_aggregates.get('errorCount', 0)
                        warning_count = resources_aggregates.get('warningCount', 0)
                        ok_count = resources_aggregates.get('okCount', 0)
                        total_resources = error_count + warning_count + ok_count
                        
                        # Create recommendation object
                        # IMPORTANT: Use 'arn' as the recommendationIdentifier for detailed API calls
                        recommendation_identifier = rec.get('arn', '')  # This is the key field for detailed calls
                        
                        recommendation = {
                            'id': rec.get('id', ''),  # Keep original ID for display
                            'recommendationIdentifier': recommendation_identifier,  # Store the correct identifier
                            'name': rec.get('name', ''),
                            'description': rec.get('name', ''),  # Use name as description for now
                            'category': pillar,
                            'status': status,
                            'pillar': pillar,
                            'timestamp': rec.get('lastUpdatedAt', ''),
                            'severity': get_severity_from_status(status),
                            'resource_count': total_resources,
                            'error_count': error_count,
                            'warning_count': warning_count,
                            'ok_count': ok_count,
                            'arn': rec.get('arn', ''),
                            'check_arn': rec.get('checkArn', ''),
                            'aws_services': rec.get('awsServices', []),
                            'source': rec.get('source', ''),
                            'type': rec.get('type', ''),
                            'flagged_resources': []  # We'll need to get details separately
                        }
                        
                        all_recommendations.append(recommendation)
                        
                        # Add to appropriate category
                        if pillar in categories:
                            categories[pillar].append(recommendation)
                        else:
                            # Create category if it doesn't exist
                            categories.setdefault(pillar, []).append(recommendation)
                    
                    # Check if there are more pages
                    next_token = response.get('nextToken')
                    if not next_token:
                        break
                        
                    # Safety check to prevent infinite loops
                    if page_count > 50:  # Reasonable limit
                        print("Warning: Reached maximum page limit (50)")
                        break
                        
                except Exception as page_error:
                    print(f"Error fetching page {page_count}: {page_error}")
                    break
            
            print(f"Successfully processed {len(all_recommendations)} total recommendations across {page_count} pages")
            
            # Sort recommendations by priority: error (high) -> warning (medium) -> ok (low)
            def get_priority_order(status):
                priority_map = {
                    'error': 1,    # High priority first
                    'warning': 2,  # Medium priority second
                    'ok': 3        # Low priority last
                }
                return priority_map.get(status.lower(), 4)  # Unknown status goes last
            
            # Sort all recommendations by priority
            all_recommendations.sort(key=lambda x: get_priority_order(x.get('status', '')))
            
            # Sort recommendations within each category by priority as well
            for category, recs in categories.items():
                recs.sort(key=lambda x: get_priority_order(x.get('status', '')))
            
            # Print category breakdown
            for category, recs in categories.items():
                if recs:
                    status_breakdown = {}
                    for rec in recs:
                        status = rec.get('status', 'unknown')
                        status_breakdown[status] = status_breakdown.get(status, 0) + 1
                    print(f"Category {category}: {len(recs)} recommendations - {status_breakdown}")
            
            return {
                'recommendations': all_recommendations,
                'categories': categories,
                'total_checks': len(all_recommendations),
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            error_message = e.response.get('Error', {}).get('Message', str(e))
            
            if 'SubscriptionRequired' in error_code:
                return {
                    'error': 'Trusted Advisor requires Business or Enterprise support plan',
                    'recommendations': []
                }
            else:
                return {
                    'error': f'Error accessing Trusted Advisor: {error_message}',
                    'recommendations': []
                }
        
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
            return []
        
        print(f"DEBUG: Getting all resources for recommendation ID: {recommendation_id}")
        
        # Check which service we're using
        service_name = 'unknown'
        if hasattr(client, '_service_model'):
            service_model = getattr(client, '_service_model')
            if hasattr(service_model, 'service_name'):
                service_name = service_model.service_name
        
        print(f"DEBUG: Using service: {service_name}")
        
        if service_name == 'support':
            return get_affected_resources_support(client, recommendation_id)
        else:
            return get_affected_resources_trustedadvisor(client, recommendation_id)
        
    except Exception as e:
        print(f"DEBUG: Error getting affected resources: {e}")
        return []

def get_affected_resources_trustedadvisor(client, recommendation_id):
    """Get affected resources using trustedadvisor service."""
    all_resources = []
    next_token = None
    page_count = 0
    
    while True:
        page_count += 1
        print(f"DEBUG: Fetching page {page_count} of resources...")
        
        # Prepare the request parameters
        params = {'recommendationIdentifier': recommendation_id}
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
                
                formatted_resource = {
                    'resourceId': resource.get('resourceId', 'N/A'),
                    'arn': resource.get('arn', ''),
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

def get_affected_resources_support(client, recommendation_id):
    """Get affected resources using support service."""
    try:
        print(f"DEBUG: Getting resources from support API for check: {recommendation_id}")
        
        response = client.describe_trusted_advisor_check_result(
            checkId=recommendation_id,
            language='en'
        )
        
        check_result = response.get('result', {})
        flagged_resources = check_result.get('flaggedResources', [])
        
        all_resources = []
        for resource in flagged_resources:
            formatted_resource = {
                'resourceId': resource.get('resourceId', 'N/A'),
                'arn': 'N/A',  # Support API doesn't provide ARN
                'awsResourceId': resource.get('resourceId', 'N/A'),
                'lastUpdatedAt': check_result.get('timestamp', ''),
                'regionCode': resource.get('region', 'N/A'),
                'status': resource.get('status', 'flagged'),
                'metadata': resource.get('metadata', []),
                'exclusionStatus': '',
                'resourceArn': ''
            }
            all_resources.append(formatted_resource)
        
        print(f"DEBUG: Retrieved {len(all_resources)} flagged resources from support API")
        return all_resources
        
    except Exception as e:
        print(f"DEBUG: Support API error getting resources: {e}")
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
