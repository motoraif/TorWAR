#!/usr/bin/env python3

import sys
sys.path.append('/app')

from database_models import db, User, AWSAccount, TrustedAdvisorRecommendation
from flask import Flask
import json

def populate_database():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@db:5432/torwar_db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        # Get first user
        user = User.query.first()
        if not user:
            print("No user found")
            return
        
        # Get or create AWS account
        aws_account = AWSAccount.query.filter_by(
            user_id=user.id,
            account_id='466171249965',
            region='us-east-1'
        ).first()
        
        if not aws_account:
            aws_account = AWSAccount(
                user_id=user.id,
                account_id='466171249965',
                region='us-east-1',
                profile_name='default'
            )
            db.session.add(aws_account)
            db.session.commit()
        
        # Sample recommendations
        recommendations = [
            {
                'check_id': 'da0c9ef5-83d4-4e60-0760-2fcad67b8f1e',
                'name': 'IAM Access Analyzer - external access',
                'category': 'security',
                'pillar': 'security',
                'status': 'error',
                'description': 'IAM Access Analyzer detected external access to your resources',
                'resource_count': 19
            },
            {
                'check_id': 'e9153ef0-67d4-4119-8bac-4b0f068b77e4',
                'name': 'Security Groups - Unrestricted Access',
                'category': 'security',
                'pillar': 'security',
                'status': 'error',
                'description': 'Security groups with unrestricted access detected',
                'resource_count': 8
            },
            {
                'check_id': '0edf585d-1719-4e2e-a5f1-d9dbe3701c52',
                'name': 'Security Groups - Specific Ports Unrestricted',
                'category': 'security',
                'pillar': 'security',
                'status': 'warning',
                'description': 'Security groups with specific ports unrestricted',
                'resource_count': 12
            },
            {
                'check_id': 'fdf36d2a-c753-4c41-8088-a6f597d28e61',
                'name': 'ELB Listener Security',
                'category': 'security',
                'pillar': 'security',
                'status': 'warning',
                'description': 'ELB listeners with security issues',
                'resource_count': 3
            },
            {
                'check_id': 'df160a32-d80d-487f-9a69-f4403afe83b4',
                'name': 'Amazon S3 Server Access Logs Enabled',
                'category': 'operational_excellence',
                'pillar': 'operational_excellence',
                'status': 'warning',
                'description': 'S3 buckets without server access logging',
                'resource_count': 4
            }
        ]
        
        # Clear existing recommendations
        TrustedAdvisorRecommendation.query.filter_by(aws_account_id=aws_account.id).delete()
        
        # Add new recommendations
        for rec_data in recommendations:
            rec = TrustedAdvisorRecommendation(
                aws_account_id=aws_account.id,
                **rec_data
            )
            db.session.add(rec)
        
        db.session.commit()
        print(f"✅ Added {len(recommendations)} recommendations to database")

if __name__ == '__main__':
    populate_database()
