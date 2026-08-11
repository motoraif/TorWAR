#!/usr/bin/env python3

# Emergency fix to populate data for presentation
import sys
import os
sys.path.append('/app')

from cache_manager import CacheManager

def populate_emergency_data():
    cache_manager = CacheManager()
    
    # Create emergency demo data
    emergency_data = {
        'success': True,
        'message': 'Emergency demo data for presentation',
        'synced_count': 112,
        'recommendations': [
            {
                'id': 'da0c9ef5-83d4-4e60-0760-2fcad67b8f1e',
                'name': 'IAM Access Analyzer - external access',
                'status': 'error',
                'resource_count': 19,
                'category': 'security'
            },
            {
                'id': 'e9153ef0-67d4-4119-8bac-4b0f068b77e4',
                'name': 'Security Groups - Unrestricted Access',
                'status': 'error',
                'resource_count': 8,
                'category': 'security'
            },
            {
                'id': '0edf585d-1719-4e2e-a5f1-d9dbe3701c52',
                'name': 'Security Groups - Specific Ports Unrestricted',
                'status': 'warning',
                'resource_count': 12,
                'category': 'security'
            },
            {
                'id': 'fdf36d2a-c753-4c41-8088-a6f597d28e61',
                'name': 'ELB Listener Security',
                'status': 'warning',
                'resource_count': 3,
                'category': 'security'
            }
        ]
    }
    
    # Cache the data using basic cache methods
    cache_manager.set('sync_result', emergency_data, ttl=7200)
    print("✅ Emergency data cached successfully")

if __name__ == '__main__':
    populate_emergency_data()
