#!/usr/bin/env python3
"""
TorWAR Database Migration Tool
Author: Mohamed Toraif

Migrate existing file-based data to SQLAlchemy database.
"""

import os
import json
from datetime import datetime
from flask import Flask
from models import db, Workload, Report
from database_service import DatabaseService

def migrate_existing_data():
    """Migrate existing file-based data to database."""
    
    # Create Flask app for database context
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///torwar.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    DatabaseService.init_db(app)
    
    with app.app_context():
        print("🔄 Starting data migration...")
        
        # Migrate reports
        reports_dir = 'data/reports'
        if os.path.exists(reports_dir):
            migrated_reports = 0
            
            # Migrate from workloads directory
            workloads_dir = os.path.join(reports_dir, 'workloads')
            if os.path.exists(workloads_dir):
                for filename in os.listdir(workloads_dir):
                    if filename.endswith('.json'):
                        try:
                            filepath = os.path.join(workloads_dir, filename)
                            with open(filepath, 'r') as f:
                                data = json.load(f)
                            
                            metadata = data.get('metadata', {})
                            report_data = data.get('report_data', {})
                            
                            # Create or get workload
                            workload_id = metadata.get('workload_id')
                            workload_name = metadata.get('workload_name', 'Unknown')
                            
                            if workload_id:
                                workload = DatabaseService.get_workload(workload_id)
                                if not workload:
                                    workload = DatabaseService.create_workload(
                                        workload_id=workload_id,
                                        name=workload_name,
                                        description=f"Migrated from file: {filename}"
                                    )
                                
                                # Create report
                                report_name = metadata.get('custom_name', f"Report {filename}")
                                user_notes = metadata.get('user_notes', '')
                                
                                # Check if report already exists
                                existing_report = Report.query.filter_by(
                                    id=metadata.get('report_id', filename.replace('.json', ''))
                                ).first()
                                
                                if not existing_report:
                                    report = DatabaseService.create_report(
                                        workload_id=workload_id,
                                        name=report_name,
                                        report_data=report_data,
                                        user_notes=user_notes
                                    )
                                    
                                    # Set original ID if available
                                    if 'report_id' in metadata:
                                        report.id = metadata['report_id']
                                        db.session.commit()
                                    
                                    migrated_reports += 1
                                    print(f"✅ Migrated report: {report_name}")
                        
                        except Exception as e:
                            print(f"❌ Error migrating {filename}: {e}")
            
            print(f"✅ Migration completed: {migrated_reports} reports migrated")
        else:
            print("ℹ️ No existing reports directory found")
        
        # Show final stats
        stats = DatabaseService.get_database_stats()
        print(f"\n📊 Database Statistics:")
        print(f"  - Workloads: {stats['workloads']}")
        print(f"  - Reports: {stats['reports']}")
        print(f"  - Cache entries: {stats['cache_entries']}")

def backup_existing_data():
    """Create backup of existing file-based data."""
    import shutil
    from datetime import datetime
    
    backup_dir = f"data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    if os.path.exists('data'):
        shutil.copytree('data', backup_dir)
        print(f"✅ Backup created: {backup_dir}")
        return backup_dir
    else:
        print("ℹ️ No existing data directory to backup")
        return None

if __name__ == "__main__":
    print("🗄️ TorWAR Database Migration Tool")
    print("=" * 40)
    
    # Create backup first
    backup_dir = backup_existing_data()
    
    # Run migration
    migrate_existing_data()
    
    print("\n🎯 Migration completed!")
    if backup_dir:
        print(f"📁 Original data backed up to: {backup_dir}")
    print("🚀 You can now use the database-enabled TorWAR!")
