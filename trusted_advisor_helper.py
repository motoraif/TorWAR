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
    """Get all Trusted Advisor recommendations with their results using CLI command."""
    try:
        import subprocess
        import json
        from flask import session
        
        # Get profile from session or use default
        profile = session.get('aws_profile', 'default')
        
        # Run the CLI command for security recommendations
        cmd = ["aws", "trustedadvisor", "list-recommendations", "--pillar", "security"]
        
        # Add profile if specified
        if profile:
            cmd.extend(["--profile", profile])
        
        # Add region (use us-east-1 for Trusted Advisor regardless of session region)
        cmd.extend(["--region", "us-east-1"])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return {
                'error': f'Error executing AWS CLI command: {result.stderr}',
                'recommendations': []
            }
        
        # Parse the JSON output
        try:
            cli_data = json.loads(result.stdout)
            security_recommendations = cli_data.get('recommendations', [])
            
            # Process recommendations
            recommendations = []
            categories = {
                'cost_optimizing': [],
                'performance': [],
                'security': [],
                'fault_tolerance': [],
                'service_limits': []
            }
            
            # Process CLI recommendations
            for rec in security_recommendations:
                # Map status - convert to lowercase for consistency
                status = rec.get('status', '').lower()
                
                # Get resources affected
                resources_affected = rec.get('resourcesAffected', [])
                
                # Create recommendation object
                recommendation = {
                    'id': rec.get('id', ''),
                    'name': rec.get('name', ''),
                    'description': rec.get('description', ''),
                    'category': 'security',
                    'status': status,
                    'pillar': 'security',
                    'timestamp': rec.get('lastUpdatedAt', ''),
                    'severity': get_severity_from_status(status),
                    'resource_count': len(resources_affected),
                    'flagged_resources': resources_affected
                }
                
                recommendations.append(recommendation)
                categories['security'].append(recommendation)
            
            # Get recommendations for other pillars if needed
            other_pillars = ['cost_optimizing', 'performance', 'fault_tolerance', 'service_limits']
            for pillar in other_pillars:
                try:
                    pillar_cmd = ["aws", "trustedadvisor", "list-recommendations", "--pillar", pillar]
                    
                    # Add profile if specified
                    if profile:
                        pillar_cmd.extend(["--profile", profile])
                    
                    # Add region (use us-east-1 for Trusted Advisor regardless of session region)
                    pillar_cmd.extend(["--region", "us-east-1"])
                    
                    pillar_result = subprocess.run(pillar_cmd, capture_output=True, text=True)
                    
                    if pillar_result.returncode == 0:
                        pillar_data = json.loads(pillar_result.stdout)
                        pillar_recommendations = pillar_data.get('recommendations', [])
                        
                        for rec in pillar_recommendations:
                            status = rec.get('status', '').lower()
                            resources_affected = rec.get('resourcesAffected', [])
                            
                            recommendation = {
                                'id': rec.get('id', ''),
                                'name': rec.get('name', ''),
                                'description': rec.get('description', ''),
                                'category': pillar,
                                'status': status,
                                'pillar': pillar,
                                'timestamp': rec.get('lastUpdatedAt', ''),
                                'severity': get_severity_from_status(status),
                                'resource_count': len(resources_affected),
                                'flagged_resources': resources_affected
                            }
                            
                            recommendations.append(recommendation)
                            categories[pillar].append(recommendation)
                except Exception:
                    pass
            
            return {
                'recommendations': recommendations,
                'categories': categories,
                'total_checks': len(recommendations),
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
            
        except json.JSONDecodeError:
            return {
                'error': 'Error parsing CLI output',
                'recommendations': []
            }
            
    except Exception as e:
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
    """Get a summary of Trusted Advisor recommendations for dashboard using CLI command."""
    try:
        import subprocess
        import json
        from flask import session
        import os
        from datetime import datetime, timedelta
        
        # Check if we have a cached summary that's less than 5 minutes old
        cache_file = os.path.join('/tmp', 'torwar_ta_summary.json')
        if os.path.exists(cache_file):
            file_mtime = datetime.fromtimestamp(os.path.getmtime(cache_file))
            if datetime.now() - file_mtime < timedelta(minutes=5):
                try:
                    with open(cache_file, 'r') as f:
                        cached_data = json.load(f)
                        return cached_data
                except:
                    # If there's any error reading the cache, continue with the normal flow
                    pass
        
        # Get profile from session or use default
        profile = session.get('aws_profile', 'default')
        
        # Run the CLI command for security recommendations - only get count
        cmd = ["aws", "trustedadvisor", "list-recommendations", "--pillar", "security", "--query", "length(recommendations)"]
        
        # Add profile if specified
        if profile:
            cmd.extend(["--profile", profile])
        
        # Add region (use us-east-1 for Trusted Advisor regardless of session region)
        cmd.extend(["--region", "us-east-1"])
        
        # Run the command with a timeout to prevent hanging
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        
        if result.returncode != 0:
            return {
                'available': False,
                'error': f'Error executing AWS CLI command',
                'summary': {}
            }
        
        # Parse the output - should be just a number
        try:
            security_count = int(result.stdout.strip())
            
            # Get counts by status - simplified approach
            cmd_high = ["aws", "trustedadvisor", "list-recommendations", "--pillar", "security", "--status", "error", "--query", "length(recommendations)"]
            cmd_medium = ["aws", "trustedadvisor", "list-recommendations", "--pillar", "security", "--status", "warning", "--query", "length(recommendations)"]
            
            if profile:
                cmd_high.extend(["--profile", profile])
                cmd_medium.extend(["--profile", profile])
            
            cmd_high.extend(["--region", "us-east-1"])
            cmd_medium.extend(["--region", "us-east-1"])
            
            # Run commands with timeout
            result_high = subprocess.run(cmd_high, capture_output=True, text=True, timeout=3)
            result_medium = subprocess.run(cmd_medium, capture_output=True, text=True, timeout=3)
            
            high_count = int(result_high.stdout.strip()) if result_high.returncode == 0 else 0
            medium_count = int(result_medium.stdout.strip()) if result_medium.returncode == 0 else 0
            
            # Create summary
            summary = {
                'available': True,
                'total_checks': security_count,
                'status_counts': {
                    'error': high_count,
                    'warning': medium_count,
                    'ok': security_count - high_count - medium_count
                },
                'category_counts': {
                    'security': security_count,
                    'cost_optimizing': 0,
                    'performance': 0,
                    'fault_tolerance': 0,
                    'service_limits': 0
                },
                'total_flagged_resources': high_count + medium_count,
                'last_updated': datetime.now(timezone.utc).isoformat(),
                'high_priority_count': high_count,
                'medium_priority_count': medium_count,
                'message': f"Found {high_count} high impact and {medium_count} medium impact security recommendations"
            }
            
            # Cache the summary
            try:
                with open(cache_file, 'w') as f:
                    json.dump(summary, f)
            except:
                # If caching fails, just continue
                pass
                
            return summary
            
        except Exception as e:
            return {
                'available': True,
                'error': None,
                'total_checks': 0,
                'status_counts': {'error': 0, 'warning': 0, 'ok': 0},
                'category_counts': {'security': 0, 'cost_optimizing': 0, 'performance': 0, 'fault_tolerance': 0, 'service_limits': 0},
                'total_flagged_resources': 0,
                'last_updated': datetime.now(timezone.utc).isoformat(),
                'high_priority_count': 0,
                'medium_priority_count': 0,
                'message': "No recommendations found"
            }
            
    except Exception as e:
        return {
            'available': False,
            'error': f'Error retrieving summary',
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
