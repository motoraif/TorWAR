#!/usr/bin/env python3
"""
Enhanced Report Management System for TorWAR
Handles saving, loading, and comparing Well-Architected reports
"""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import hashlib

class ReportManager:
    """Manages Well-Architected reports with versioning and comparison capabilities."""
    
    def __init__(self, data_dir: str = "/app/data/reports"):
        """Initialize the report manager with data directory."""
        self.data_dir = data_dir
        self.ensure_data_directory()
    
    def ensure_data_directory(self):
        """Ensure the reports data directory exists."""
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            # Create subdirectories for organization
            os.makedirs(os.path.join(self.data_dir, "workloads"), exist_ok=True)
            os.makedirs(os.path.join(self.data_dir, "metadata"), exist_ok=True)
        except Exception as e:
            print(f"Warning: Could not create reports directory: {e}")
    
    def save_report(self, workload_id: str, workload_name: str, report_data: Dict[str, Any], 
                   user_notes: str = "", custom_name: str = "") -> str:
        """
        Save a Well-Architected report with metadata.
        
        Args:
            workload_id: AWS workload ID
            workload_name: Human-readable workload name
            report_data: Complete report data including answers, risks, etc.
            user_notes: Optional user notes about this report
            custom_name: Optional custom name for the report
            
        Returns:
            report_id: Unique identifier for the saved report
        """
        # Generate unique report ID
        report_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc)
        
        # Create report metadata
        metadata = {
            "report_id": report_id,
            "workload_id": workload_id,
            "workload_name": workload_name,
            "custom_name": custom_name or f"{workload_name} - {timestamp.strftime('%Y-%m-%d %H:%M')}",
            "created_at": timestamp.isoformat(),
            "user_notes": user_notes,
            "version": self._get_next_version(workload_id),
            "data_hash": self._calculate_data_hash(report_data),
            "summary": self._generate_summary(report_data)
        }
        
        # Save report data
        report_file = os.path.join(self.data_dir, "workloads", f"{report_id}.json")
        metadata_file = os.path.join(self.data_dir, "metadata", f"{report_id}_meta.json")
        
        try:
            # Save main report data
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "metadata": metadata,
                    "report_data": report_data
                }, f, indent=2, default=str)
            
            # Save metadata separately for quick access
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, default=str)
            
            # Update workload index
            self._update_workload_index(workload_id, metadata)
            
            return report_id
            
        except Exception as e:
            raise Exception(f"Failed to save report: {str(e)}")
    
    def get_saved_reports(self, workload_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get list of saved reports, optionally filtered by workload.
        
        Args:
            workload_id: Optional workload ID to filter by
            
        Returns:
            List of report metadata dictionaries
        """
        reports = []
        metadata_dir = os.path.join(self.data_dir, "metadata")
        
        if not os.path.exists(metadata_dir):
            return reports
        
        try:
            for filename in os.listdir(metadata_dir):
                if filename.endswith("_meta.json"):
                    filepath = os.path.join(metadata_dir, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        
                    # Filter by workload if specified
                    if workload_id is None or metadata.get('workload_id') == workload_id:
                        reports.append(metadata)
            
            # Sort by creation date (newest first)
            reports.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
        except Exception as e:
            print(f"Error loading saved reports: {e}")
        
        return reports
    
    def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a specific report by ID.
        
        Args:
            report_id: Unique report identifier
            
        Returns:
            Complete report data or None if not found
        """
        report_file = os.path.join(self.data_dir, "workloads", f"{report_id}.json")
        
        if not os.path.exists(report_file):
            return None
        
        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading report {report_id}: {e}")
            return None
    
    def delete_report(self, report_id: str) -> bool:
        """
        Delete a saved report.
        
        Args:
            report_id: Unique report identifier
            
        Returns:
            True if deleted successfully, False otherwise
        """
        report_file = os.path.join(self.data_dir, "workloads", f"{report_id}.json")
        metadata_file = os.path.join(self.data_dir, "metadata", f"{report_id}_meta.json")
        
        try:
            # Remove files if they exist
            if os.path.exists(report_file):
                os.remove(report_file)
            if os.path.exists(metadata_file):
                os.remove(metadata_file)
            
            return True
            
        except Exception as e:
            print(f"Error deleting report {report_id}: {e}")
            return False
    
    def compare_reports(self, report_id1: str, report_id2: str) -> Dict[str, Any]:
        """
        Compare two reports and return differences.
        
        Args:
            report_id1: First report ID
            report_id2: Second report ID
            
        Returns:
            Comparison results with differences highlighted
        """
        report1 = self.get_report(report_id1)
        report2 = self.get_report(report_id2)
        
        if not report1 or not report2:
            raise ValueError("One or both reports not found")
        
        comparison = {
            "report1": {
                "id": report_id1,
                "name": report1["metadata"]["custom_name"],
                "created_at": report1["metadata"]["created_at"],
                "version": report1["metadata"]["version"]
            },
            "report2": {
                "id": report_id2,
                "name": report2["metadata"]["custom_name"],
                "created_at": report2["metadata"]["created_at"],
                "version": report2["metadata"]["version"]
            },
            "differences": self._compare_report_data(
                report1["report_data"], 
                report2["report_data"]
            ),
            "summary": self._generate_comparison_summary(report1, report2)
        }
        
        return comparison
    
    def get_workload_versions(self, workload_id: str) -> List[Dict[str, Any]]:
        """
        Get all report versions for a specific workload.
        
        Args:
            workload_id: AWS workload ID
            
        Returns:
            List of report versions sorted by version number
        """
        reports = self.get_saved_reports(workload_id)
        
        # Sort by version number
        reports.sort(key=lambda x: x.get('version', 0))
        
        return reports
    
    def _get_next_version(self, workload_id: str) -> int:
        """Get the next version number for a workload."""
        existing_reports = self.get_saved_reports(workload_id)
        if not existing_reports:
            return 1
        
        max_version = max(report.get('version', 0) for report in existing_reports)
        return max_version + 1
    
    def _calculate_data_hash(self, data: Dict[str, Any]) -> str:
        """Calculate hash of report data for change detection."""
        # Create a stable string representation of the data
        data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]
    
    def _generate_summary(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of the report data."""
        summary = {
            "total_questions": 0,
            "answered_questions": 0,
            "high_risks": 0,
            "medium_risks": 0,
            "low_risks": 0,
            "no_risks": 0,
            "pillars": {}
        }
        
        # Count questions and risks by pillar
        for pillar_id, pillar_data in report_data.get('pillars', {}).items():
            pillar_summary = {
                "questions": 0,
                "answered": 0,
                "high_risks": 0,
                "medium_risks": 0,
                "low_risks": 0,
                "no_risks": 0
            }
            
            for question_data in pillar_data.get('questions', []):
                pillar_summary["questions"] += 1
                summary["total_questions"] += 1
                
                # Use correct field name: SelectedChoices instead of selected_choices
                if question_data.get('SelectedChoices'):
                    pillar_summary["answered"] += 1
                    summary["answered_questions"] += 1
                
                # Use correct field name: Risk instead of risk_level
                risk_level = question_data.get('Risk', 'UNANSWERED')
                if risk_level == 'HIGH':
                    pillar_summary["high_risks"] += 1
                    summary["high_risks"] += 1
                elif risk_level == 'MEDIUM':
                    pillar_summary["medium_risks"] += 1
                    summary["medium_risks"] += 1
                elif risk_level == 'LOW':
                    pillar_summary["low_risks"] += 1
                    summary["low_risks"] += 1
                elif risk_level == 'NONE':  # Use NONE instead of NO_RISK
                    pillar_summary["no_risks"] += 1
                    summary["no_risks"] += 1
            
            summary["pillars"][pillar_id] = pillar_summary
        
        return summary
    
    def _compare_report_data(self, data1: Dict[str, Any], data2: Dict[str, Any]) -> Dict[str, Any]:
        """Compare two report data structures and identify differences."""
        differences = {
            "changed_answers": [],
            "risk_changes": [],
            "new_questions": [],
            "removed_questions": [],
            "pillar_changes": {}
        }
        
        # Compare pillar by pillar
        pillars1 = data1.get('pillars', {})
        pillars2 = data2.get('pillars', {})
        
        all_pillars = set(pillars1.keys()) | set(pillars2.keys())
        
        for pillar_id in all_pillars:
            pillar1 = pillars1.get(pillar_id, {})
            pillar2 = pillars2.get(pillar_id, {})
            
            # Use QuestionId instead of question_id
            questions1 = {q.get('QuestionId'): q for q in pillar1.get('questions', [])}
            questions2 = {q.get('QuestionId'): q for q in pillar2.get('questions', [])}
            
            all_questions = set(questions1.keys()) | set(questions2.keys())
            
            pillar_changes = {
                "changed_answers": [],
                "risk_changes": [],
                "new_questions": [],
                "removed_questions": []
            }
            
            for question_id in all_questions:
                q1 = questions1.get(question_id)
                q2 = questions2.get(question_id)
                
                if q1 and not q2:
                    pillar_changes["removed_questions"].append({
                        "question_id": question_id,
                        "title": q1.get('QuestionTitle', 'Unknown Question')
                    })
                elif q2 and not q1:
                    pillar_changes["new_questions"].append({
                        "question_id": question_id,
                        "title": q2.get('QuestionTitle', 'Unknown Question')
                    })
                elif q1 and q2:
                    # Compare answers
                    choices1 = set(q1.get('SelectedChoices', []))
                    choices2 = set(q2.get('SelectedChoices', []))
                    
                    if choices1 != choices2:
                        pillar_changes["changed_answers"].append({
                            "question_id": question_id,
                            "title": q1.get('QuestionTitle', 'Unknown Question'),
                            "old_choices": list(choices1),
                            "new_choices": list(choices2)
                        })
                    
                    # Compare risk levels
                    risk1 = q1.get('Risk')
                    risk2 = q2.get('Risk')
                    
                    if risk1 != risk2:
                        pillar_changes["risk_changes"].append({
                            "question_id": question_id,
                            "title": q1.get('QuestionTitle', 'Unknown Question'),
                            "old_risk": risk1,
                            "new_risk": risk2
                        })
            
            # Only include pillar if there are changes
            if any(pillar_changes.values()):
                differences["pillar_changes"][pillar_id] = pillar_changes
                
                # Add to overall changes
                differences["changed_answers"].extend(pillar_changes["changed_answers"])
                differences["risk_changes"].extend(pillar_changes["risk_changes"])
                differences["new_questions"].extend(pillar_changes["new_questions"])
                differences["removed_questions"].extend(pillar_changes["removed_questions"])
        
        return differences
    
    def _generate_comparison_summary(self, report1: Dict[str, Any], report2: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a high-level summary of the comparison."""
        summary1 = report1["metadata"]["summary"]
        summary2 = report2["metadata"]["summary"]
        
        return {
            "questions_change": summary2["answered_questions"] - summary1["answered_questions"],
            "high_risk_change": summary2["high_risks"] - summary1["high_risks"],
            "medium_risk_change": summary2["medium_risks"] - summary1["medium_risks"],
            "low_risk_change": summary2["low_risks"] - summary1["low_risks"],
            "overall_improvement": (summary1["high_risks"] + summary1["medium_risks"]) - 
                                 (summary2["high_risks"] + summary2["medium_risks"])
        }
    
    def _update_workload_index(self, workload_id: str, metadata: Dict[str, Any]):
        """Update the workload index for quick lookups."""
        index_file = os.path.join(self.data_dir, "workload_index.json")
        
        try:
            # Load existing index
            if os.path.exists(index_file):
                with open(index_file, 'r', encoding='utf-8') as f:
                    index = json.load(f)
            else:
                index = {}
            
            # Update index
            if workload_id not in index:
                index[workload_id] = []
            
            index[workload_id].append({
                "report_id": metadata["report_id"],
                "version": metadata["version"],
                "created_at": metadata["created_at"],
                "custom_name": metadata["custom_name"]
            })
            
            # Sort by version
            index[workload_id].sort(key=lambda x: x["version"])
            
            # Save updated index
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(index, f, indent=2, default=str)
                
        except Exception as e:
            print(f"Warning: Could not update workload index: {e}")
