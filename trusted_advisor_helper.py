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
        
        # Use the newer trustedadvisor service
        # Always use us-east-1 for Trusted Advisor regardless of session region
        ta_client = aws_session.client(
            'trustedadvisor', 
            region_name='us-east-1',
            endpoint_url='https://trustedadvisor.us-east-1.api.aws'
        )
        return ta_client
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
                        recommendation = {
                            'id': rec.get('id', ''),
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
