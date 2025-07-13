"""
TorWAR Trusted Advisor Integration
Author: Mohamed Toraif
Description: AWS Trusted Advisor recommendations integration for TorWAR
"""

import boto3
import json
from datetime import datetime, timezone
from botocore.exceptions import ClientError, NoCredentialsError
from aws_helper import get_aws_session

def get_trusted_advisor_client():
    """Get AWS Support client for Trusted Advisor."""
    try:
        session = get_aws_session()
        if not session:
            return None
        
        # Trusted Advisor requires Support API which is only available in us-east-1
        support_client = session.client('support', region_name='us-east-1')
        return support_client
    except Exception as e:
        print(f"Error creating Trusted Advisor client: {e}")
        return None

def get_trusted_advisor_checks():
    """Get all available Trusted Advisor checks."""
    try:
        client = get_trusted_advisor_client()
        if not client:
            return None
        
        response = client.describe_trusted_advisor_checks(language='en')
        return response.get('checks', [])
    except ClientError as e:
        error_code = e.response['Error']['Code']
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
    """Get result for a specific Trusted Advisor check."""
    try:
        client = get_trusted_advisor_client()
        if not client:
            return None
        
        response = client.describe_trusted_advisor_check_result(
            checkId=check_id,
            language='en'
        )
        return response.get('result')
    except Exception as e:
        print(f"Error getting check result for {check_id}: {e}")
        return None

def get_all_trusted_advisor_recommendations():
    """Get all Trusted Advisor recommendations with their results."""
    try:
        checks = get_trusted_advisor_checks()
        if not checks:
            return {
                'error': 'Unable to retrieve Trusted Advisor checks. This may be due to insufficient support plan or permissions.',
                'recommendations': []
            }
        
        recommendations = []
        categories = {
            'cost_optimizing': [],
            'performance': [],
            'security': [],
            'fault_tolerance': [],
            'service_limits': []
        }
        
        for check in checks:
            check_id = check['id']
            check_name = check['name']
            check_description = check['description']
            check_category = check['category'].lower().replace(' ', '_')
            
            # Get the result for this check
            result = get_trusted_advisor_check_result(check_id)
            
            if result:
                status = result.get('status', 'unknown')
                timestamp = result.get('timestamp', '')
                resources_summary = result.get('resourcesSummary', {})
                flagged_resources = result.get('flaggedResources', [])
                
                recommendation = {
                    'id': check_id,
                    'name': check_name,
                    'description': check_description,
                    'category': check_category,
                    'status': status,
                    'timestamp': timestamp,
                    'resources_summary': resources_summary,
                    'flagged_resources': flagged_resources,
                    'severity': get_severity_from_status(status),
                    'resource_count': len(flagged_resources)
                }
                
                recommendations.append(recommendation)
                
                # Categorize recommendations
                if check_category in categories:
                    categories[check_category].append(recommendation)
                else:
                    categories.setdefault('other', []).append(recommendation)
        
        return {
            'recommendations': recommendations,
            'categories': categories,
            'total_checks': len(recommendations),
            'last_updated': datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        print(f"Error getting Trusted Advisor recommendations: {e}")
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

def get_trusted_advisor_summary():
    """Get a summary of Trusted Advisor recommendations for dashboard."""
    try:
        data = get_all_trusted_advisor_recommendations()
        
        if 'error' in data:
            return {
                'available': False,
                'error': data['error'],
                'summary': {}
            }
        
        recommendations = data.get('recommendations', [])
        
        # Count by status
        status_counts = {
            'error': 0,
            'warning': 0,
            'ok': 0,
            'not_available': 0
        }
        
        # Count by category
        category_counts = {
            'cost_optimizing': 0,
            'performance': 0,
            'security': 0,
            'fault_tolerance': 0,
            'service_limits': 0
        }
        
        total_flagged_resources = 0
        
        for rec in recommendations:
            status = rec.get('status', 'unknown').lower()
            category = rec.get('category', 'other')
            
            if status in status_counts:
                status_counts[status] += 1
            
            if category in category_counts:
                category_counts[category] += 1
            
            total_flagged_resources += rec.get('resource_count', 0)
        
        return {
            'available': True,
            'total_checks': len(recommendations),
            'status_counts': status_counts,
            'category_counts': category_counts,
            'total_flagged_resources': total_flagged_resources,
            'last_updated': data.get('last_updated'),
            'high_priority_count': status_counts['error'],
            'medium_priority_count': status_counts['warning']
        }
        
    except Exception as e:
        print(f"Error getting Trusted Advisor summary: {e}")
        return {
            'available': False,
            'error': f'Error retrieving summary: {str(e)}',
            'summary': {}
        }

def refresh_trusted_advisor_check(check_id):
    """Refresh a specific Trusted Advisor check."""
    try:
        client = get_trusted_advisor_client()
        if not client:
            return False
        
        client.refresh_trusted_advisor_check(checkId=check_id)
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
