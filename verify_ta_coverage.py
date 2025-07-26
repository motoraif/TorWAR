#!/usr/bin/env python3
"""
Comprehensive verification script to check if we're getting all AWS Trusted Advisor checks
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def verify_ta_coverage():
    """Verify if we're getting all available Trusted Advisor checks"""
    from app import app
    with app.app_context():
        with app.test_request_context():
            from flask import session
            session['aws_profile'] = 'beyon-money-payer'
            session['aws_region'] = 'me-south-1'
            
            from trusted_advisor_helper import get_trusted_advisor_client
            
            print("=== AWS Trusted Advisor Coverage Verification ===\n")
            
            client = get_trusted_advisor_client()
            if not client:
                print("❌ Failed to create Trusted Advisor client")
                return False
            
            # Test 1: Get all recommendations using list_recommendations
            print("1. Testing list_recommendations() API...")
            try:
                all_recommendations = []
                next_token = None
                page_count = 0
                
                while True:
                    page_count += 1
                    params = {}
                    if next_token:
                        params['nextToken'] = next_token
                    
                    response = client.list_recommendations(**params)
                    page_recs = response.get('recommendationSummaries', [])
                    all_recommendations.extend(page_recs)
                    
                    print(f"   Page {page_count}: {len(page_recs)} recommendations")
                    
                    next_token = response.get('nextToken')
                    if not next_token or page_count > 20:  # Safety limit
                        break
                
                print(f"   ✅ Total recommendations via list_recommendations: {len(all_recommendations)}")
                
                # Analyze by pillar
                pillar_counts = {}
                for rec in all_recommendations:
                    pillars = rec.get('pillars', [])
                    for pillar in pillars:
                        pillar_counts[pillar] = pillar_counts.get(pillar, 0) + 1
                
                print(f"   📊 Breakdown by pillar:")
                for pillar, count in sorted(pillar_counts.items()):
                    print(f"      {pillar}: {count}")
                
            except Exception as e:
                print(f"   ❌ Error with list_recommendations: {e}")
                return False
            
            # Test 2: Get recommendations by individual pillars
            print(f"\n2. Testing pillar-specific queries...")
            pillars = ['security', 'cost_optimizing', 'performance', 'fault_tolerance', 'service_limits', 'operational_excellence']
            pillar_totals = {}
            
            for pillar in pillars:
                try:
                    pillar_recs = []
                    next_token = None
                    page_count = 0
                    
                    while True:
                        page_count += 1
                        params = {'pillar': pillar}
                        if next_token:
                            params['nextToken'] = next_token
                        
                        response = client.list_recommendations(**params)
                        page_recs = response.get('recommendationSummaries', [])
                        pillar_recs.extend(page_recs)
                        
                        next_token = response.get('nextToken')
                        if not next_token or page_count > 10:  # Safety limit
                            break
                    
                    pillar_totals[pillar] = len(pillar_recs)
                    print(f"   {pillar}: {len(pillar_recs)} recommendations")
                    
                except Exception as e:
                    print(f"   ❌ Error with {pillar}: {e}")
                    pillar_totals[pillar] = 0
            
            # Test 3: Try the legacy describe_trusted_advisor_checks API
            print(f"\n3. Testing legacy describe_trusted_advisor_checks API...")
            try:
                # Try with support client (legacy API)
                support_client = client._client_config.session.client('support', region_name='us-east-1')
                legacy_response = support_client.describe_trusted_advisor_checks(language='en')
                legacy_checks = legacy_response.get('checks', [])
                print(f"   ✅ Legacy API found {len(legacy_checks)} total checks")
                
                # Analyze legacy checks by category
                legacy_categories = {}
                for check in legacy_checks:
                    category = check.get('category', 'unknown')
                    legacy_categories[category] = legacy_categories.get(category, 0) + 1
                
                print(f"   📊 Legacy API breakdown by category:")
                for category, count in sorted(legacy_categories.items()):
                    print(f"      {category}: {count}")
                
            except Exception as e:
                print(f"   ❌ Legacy API error: {e}")
                legacy_checks = []
            
            # Test 4: Try list_checks API
            print(f"\n4. Testing list_checks API...")
            try:
                checks_response = client.list_checks()
                available_checks = checks_response.get('checks', [])
                print(f"   ✅ list_checks API found {len(available_checks)} checks")
                
                if available_checks:
                    print(f"   📋 Sample checks:")
                    for i, check in enumerate(available_checks[:5]):
                        print(f"      {i+1}. {check.get('name', 'No name')} (ID: {check.get('id', 'No ID')})")
                
            except Exception as e:
                print(f"   ❌ list_checks API error: {e}")
                available_checks = []
            
            # Test 5: Compare CLI output with API results
            print(f"\n5. Comparing with CLI output...")
            cli_file = '/home/toraif/TorWAR/ta-list-all'
            if os.path.exists(cli_file):
                try:
                    with open(cli_file, 'r') as f:
                        cli_content = f.read()
                    
                    # Count recommendations in CLI output
                    cli_rec_count = cli_content.count('- arn:')
                    print(f"   📄 CLI file shows {cli_rec_count} recommendations")
                    
                    # Compare with API results
                    api_count = len(all_recommendations)
                    if cli_rec_count == api_count:
                        print(f"   ✅ Perfect match: CLI ({cli_rec_count}) = API ({api_count})")
                    else:
                        print(f"   ⚠️  Mismatch: CLI ({cli_rec_count}) vs API ({api_count})")
                        print(f"      Difference: {abs(cli_rec_count - api_count)} recommendations")
                
                except Exception as e:
                    print(f"   ❌ Error reading CLI file: {e}")
            else:
                print(f"   ❌ CLI file not found at {cli_file}")
            
            # Summary and recommendations
            print(f"\n=== VERIFICATION SUMMARY ===")
            print(f"📊 API Results:")
            print(f"   • list_recommendations(): {len(all_recommendations)} total")
            print(f"   • Pillar-specific queries: {sum(pillar_totals.values())} total")
            print(f"   • Legacy API checks: {len(legacy_checks)} total")
            print(f"   • list_checks API: {len(available_checks)} checks")
            
            # Check for potential issues
            issues = []
            
            if len(all_recommendations) == 0:
                issues.append("❌ No recommendations found via list_recommendations")
            
            if sum(pillar_totals.values()) != len(all_recommendations):
                issues.append(f"⚠️  Pillar sum ({sum(pillar_totals.values())}) != total ({len(all_recommendations)})")
            
            if len(legacy_checks) > 0 and len(all_recommendations) < len(legacy_checks):
                issues.append(f"⚠️  API recommendations ({len(all_recommendations)}) < Legacy checks ({len(legacy_checks)})")
            
            if issues:
                print(f"\n🚨 POTENTIAL ISSUES:")
                for issue in issues:
                    print(f"   {issue}")
            else:
                print(f"\n✅ ALL CHECKS PASSED - Coverage appears complete!")
            
            return len(issues) == 0

if __name__ == "__main__":
    print("Starting AWS Trusted Advisor Coverage Verification...\n")
    success = verify_ta_coverage()
    print(f"\n{'='*50}")
    print(f"VERIFICATION RESULT: {'✅ COMPLETE COVERAGE' if success else '⚠️  POTENTIAL GAPS'}")
    print(f"{'='*50}")
