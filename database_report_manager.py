#!/usr/bin/env python3
"""
Database-Enabled Report Manager for TorWAR
Author: Mohamed Toraif
"""

from database_service import DatabaseService
from typing import Dict, List, Optional, Any
from datetime import datetime

class DatabaseReportManager:
    """Database-enabled report manager replacing file-based storage."""
    
    def __init__(self):
        self.db_service = DatabaseService
    
    def save_report(self, workload_id: str, workload_name: str, report_data: Dict[str, Any], 
                   user_notes: str = "", custom_name: str = "") -> str:
        """Save a Well-Architected report to database."""
        
        # Ensure workload exists
        workload = self.db_service.get_workload(workload_id)
        if not workload:
            workload = self.db_service.create_workload(
                workload_id=workload_id,
                name=workload_name,
                description="Auto-created from report"
            )
        
        # Generate report name
        report_name = custom_name or f"{workload_name} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # Create report
        report = self.db_service.create_report(
            workload_id=workload_id,
            name=report_name,
            report_data=report_data,
            user_notes=user_notes
        )
        
        return report.id
    
    def load_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Load a report from database."""
        report = self.db_service.get_report(report_id)
        if report:
            return {
                'metadata': {
                    'report_id': report.id,
                    'workload_id': report.workload_id,
                    'workload_name': report.workload.name if report.workload else 'Unknown',
                    'custom_name': report.name,
                    'created_at': report.created_at.isoformat(),
                    'user_notes': report.user_notes,
                    'risk_summary': report.risk_summary
                },
                'report_data': report.report_data
            }
        return None
    
    def list_reports(self, workload_id: str = None) -> List[Dict[str, Any]]:
        """List all reports, optionally filtered by workload."""
        reports = self.db_service.get_reports(workload_id)
        
        return [
            {
                'report_id': report.id,
                'workload_id': report.workload_id,
                'workload_name': report.workload.name if report.workload else 'Unknown',
                'name': report.name,
                'user_notes': report.user_notes,
                'risk_summary': report.risk_summary,
                'created_at': report.created_at.isoformat(),
                'has_data': bool(report.report_data)
            }
            for report in reports
        ]
    
    def delete_report(self, report_id: str) -> bool:
        """Delete a report from database."""
        return self.db_service.delete_report(report_id)
    
    def compare_reports(self, report_id1: str, report_id2: str) -> Optional[Dict[str, Any]]:
        """Compare two reports."""
        report1 = self.load_report(report_id1)
        report2 = self.load_report(report_id2)
        
        if not report1 or not report2:
            return None
        
        comparison = {
            'report1': report1['metadata'],
            'report2': report2['metadata'],
            'risk_comparison': self._compare_risks(
                report1['metadata']['risk_summary'],
                report2['metadata']['risk_summary']
            ),
            'pillar_comparison': self._compare_pillars(
                report1['report_data'],
                report2['report_data']
            )
        }
        
        return comparison
    
    def get_workload_summary(self, workload_id: str) -> Optional[Dict[str, Any]]:
        """Get summary for a workload including all reports."""
        workload = self.db_service.get_workload(workload_id)
        if not workload:
            return None
        
        reports = self.list_reports(workload_id)
        
        # Calculate aggregate risk summary
        total_risks = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'NONE': 0}
        for report in reports:
            if report['risk_summary']:
                for risk_level, count in report['risk_summary'].items():
                    total_risks[risk_level] = total_risks.get(risk_level, 0) + count
        
        return {
            'workload': workload.to_dict(),
            'reports': reports,
            'total_reports': len(reports),
            'aggregate_risks': total_risks,
            'latest_report': reports[0] if reports else None
        }
    
    def _compare_risks(self, risks1: Dict, risks2: Dict) -> Dict[str, Any]:
        """Compare risk summaries between two reports."""
        if not risks1 or not risks2:
            return {}
        
        comparison = {}
        for risk_level in ['HIGH', 'MEDIUM', 'LOW', 'NONE']:
            count1 = risks1.get(risk_level, 0)
            count2 = risks2.get(risk_level, 0)
            comparison[risk_level] = {
                'before': count1,
                'after': count2,
                'change': count2 - count1
            }
        
        return comparison
    
    def _compare_pillars(self, data1: Dict, data2: Dict) -> Dict[str, Any]:
        """Compare pillar data between two reports."""
        if not data1 or not data2:
            return {}
        
        pillar_data1 = data1.get('pillar_data', {})
        pillar_data2 = data2.get('pillar_data', {})
        
        comparison = {}
        for pillar in pillar_data1.keys():
            if pillar in pillar_data2:
                questions1 = pillar_data1[pillar].get('questions', [])
                questions2 = pillar_data2[pillar].get('questions', [])
                
                # Count risk changes
                risks1 = [q.get('Risk', 'NONE') for q in questions1]
                risks2 = [q.get('Risk', 'NONE') for q in questions2]
                
                comparison[pillar] = {
                    'questions_count': len(questions1),
                    'risk_changes': self._count_risk_changes(risks1, risks2)
                }
        
        return comparison
    
    def _count_risk_changes(self, risks1: List[str], risks2: List[str]) -> Dict[str, int]:
        """Count risk level changes between two lists."""
        changes = {'improved': 0, 'worsened': 0, 'unchanged': 0}
        
        risk_values = {'NONE': 0, 'LOW': 1, 'MEDIUM': 2, 'HIGH': 3}
        
        for i in range(min(len(risks1), len(risks2))):
            val1 = risk_values.get(risks1[i], 0)
            val2 = risk_values.get(risks2[i], 0)
            
            if val2 < val1:
                changes['improved'] += 1
            elif val2 > val1:
                changes['worsened'] += 1
            else:
                changes['unchanged'] += 1
        
        return changes
