#!/usr/bin/env python3
"""
TorWAR Database Integration Enabler
Author: Mohamed Toraif
"""

def enable_database_integration():
    """Enable database integration in TorWAR."""
    
    try:
        from flask import Flask, jsonify, request
        from database_config import configure_database
        from database_service import DatabaseService
        from database_report_manager import DatabaseReportManager
        
        print("🗄️ Enabling TorWAR database integration...")
        
        # Import main app
        from app import app
        
        # Configure database
        configure_database(app)
        
        # Initialize database
        DatabaseService.init_db(app)
        
        # Create database-enabled report manager
        db_report_manager = DatabaseReportManager()
        
        # Add database API endpoints
        @app.route('/api/database/stats')
        def database_stats():
            """Get database statistics."""
            return jsonify(DatabaseService.get_database_stats())
        
        @app.route('/api/workloads')
        def api_workloads():
            """Get all workloads."""
            workloads = DatabaseService.get_workloads()
            return jsonify([w.to_dict() for w in workloads])
        
        @app.route('/api/workloads/<workload_id>')
        def api_workload_detail(workload_id):
            """Get workload details with reports."""
            summary = db_report_manager.get_workload_summary(workload_id)
            if summary:
                return jsonify(summary)
            return jsonify({'error': 'Workload not found'}), 404
        
        @app.route('/api/reports')
        def api_reports():
            """Get all reports."""
            workload_id = request.args.get('workload_id')
            reports = db_report_manager.list_reports(workload_id)
            return jsonify(reports)
        
        @app.route('/api/reports/<report_id>')
        def api_report_detail(report_id):
            """Get report details."""
            report = db_report_manager.load_report(report_id)
            if report:
                return jsonify(report)
            return jsonify({'error': 'Report not found'}), 404
        
        @app.route('/api/reports/<report_id>', methods=['DELETE'])
        def api_delete_report(report_id):
            """Delete a report."""
            success = db_report_manager.delete_report(report_id)
            if success:
                return jsonify({'success': True})
            return jsonify({'error': 'Report not found'}), 404
        
        @app.route('/api/reports/compare/<report_id1>/<report_id2>')
        def api_compare_reports(report_id1, report_id2):
            """Compare two reports."""
            comparison = db_report_manager.compare_reports(report_id1, report_id2)
            if comparison:
                return jsonify(comparison)
            return jsonify({'error': 'One or both reports not found'}), 404
        
        print("✅ Database integration enabled!")
        print("\n📊 New database endpoints:")
        print("  - GET  /api/database/stats")
        print("  - GET  /api/workloads")
        print("  - GET  /api/workloads/<id>")
        print("  - GET  /api/reports")
        print("  - GET  /api/reports/<id>")
        print("  - DELETE /api/reports/<id>")
        print("  - GET  /api/reports/compare/<id1>/<id2>")
        
        print("\n🔧 Database features:")
        print("  ✅ SQLAlchemy models")
        print("  ✅ Automatic migrations")
        print("  ✅ Report management")
        print("  ✅ Workload tracking")
        print("  ✅ Database caching")
        
        return app
        
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("Install with: pip install flask-sqlalchemy")
        return None
    except Exception as e:
        print(f"❌ Error enabling database: {e}")
        return None

if __name__ == "__main__":
    app = enable_database_integration()
    if app:
        print("\n🎯 Database-enabled TorWAR ready!")
        print("🔄 Run migration: python migrate_to_database.py")
        print("🚀 Start app: python enable_database.py")
        
        # Start the app
        app.run(host='0.0.0.0', port=5000, debug=False)
