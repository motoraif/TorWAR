#!/usr/bin/env python3
"""
Optimized Report Generation for TorWAR
Author: Mohamed Toraif

This module provides an optimized version of the report generation
with minimal logging and better performance.
"""

from logging_config import get_logger, time_operation
import os

# Initialize logger
logger = get_logger("report_generation")

def generate_report_optimized(wa_client, workload_id, selected_pillars, PILLARS):
    """
    Optimized report generation with minimal logging.
    
    Args:
        wa_client: AWS Well-Architected client
        workload_id: ID of the workload to process
        selected_pillars: List of pillar IDs to include
        PILLARS: Dictionary mapping pillar IDs to names
    
    Returns:
        dict: Complete report data
    """
    
    # Only log at INFO level or higher to reduce noise
    logger.info(f"Generating report for workload {workload_id}")
    
    try:
        # Get workload details
        workload_response = wa_client.get_workload(WorkloadId=workload_id)
        workload = workload_response.get('Workload', {})
        
        # Initialize report data structure
        report_data = {
            'workload': {
                'id': workload_id,
                'name': workload.get('WorkloadName', 'Unknown'),
                'description': workload.get('Description', ''),
                'environment': workload.get('Environment', 'PRODUCTION'),
                'owner': workload.get('Owner', ''),
                'review_owner': workload.get('ReviewOwner', ''),
                'industry_type': workload.get('IndustryType', ''),
                'industry': workload.get('Industry', ''),
                'architectural_design': workload.get('ArchitecturalDesign', ''),
                'created_at': workload.get('CreatedAt'),
                'updated_at': workload.get('UpdatedAt')
            },
            'summary': {
                'total_questions': 0,
                'answered_questions': 0,
                'unanswered_questions': 0,
                'completion_percentage': 0,
                'high_risks': 0,
                'medium_risks': 0,
                'low_risks': 0,
                'no_risks': 0
            },
            'pillars': {},
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'version': '1.0'
        }
        
        # Initialize counters
        overall_stats = {'total_questions': 0, 'answered_questions': 0}
        risk_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'NONE': 0}
        
        # Process each pillar
        for pillar_id in selected_pillars:
            if pillar_id not in PILLARS:
                continue
                
            pillar_name = PILLARS[pillar_id]
            
            # Get pillar review
            try:
                pillar_response = wa_client.get_lens_review(
                    WorkloadId=workload_id,
                    LensAlias='wellarchitected',
                    PillarId=pillar_id
                )
                
                pillar_review = pillar_response.get('LensReview', {})
                pillar_summary = pillar_review.get('PillarReviewSummaries', [])
                
                if not pillar_summary:
                    continue
                    
                pillar_data = pillar_summary[0]
                
                # Get detailed answers for this pillar
                detailed_answers = []
                paginator = wa_client.get_paginator('list_answers')
                
                for page in paginator.paginate(
                    WorkloadId=workload_id,
                    LensAlias='wellarchitected',
                    PillarId=pillar_id
                ):
                    for answer in page.get('AnswerSummaries', []):
                        # Get detailed answer
                        answer_response = wa_client.get_answer(
                            WorkloadId=workload_id,
                            LensAlias='wellarchitected',
                            QuestionId=answer['QuestionId']
                        )
                        detailed_answer = answer_response.get('Answer', {})
                        detailed_answers.append(detailed_answer)
                        
                        # Update counters (simplified logic)
                        overall_stats['total_questions'] += 1
                        
                        selected_choices = detailed_answer.get('SelectedChoices', [])
                        if selected_choices and len(selected_choices) > 0:
                            overall_stats['answered_questions'] += 1
                        
                        # Count risks
                        risk = detailed_answer.get('Risk')
                        if risk in risk_counts:
                            risk_counts[risk] += 1
                
                # Calculate pillar statistics
                pillar_stats = {
                    'total_questions': len(detailed_answers),
                    'answered_questions': sum(1 for q in detailed_answers if q.get('SelectedChoices')),
                    'completion_percentage': 0
                }
                
                if pillar_stats['total_questions'] > 0:
                    pillar_stats['completion_percentage'] = round(
                        (pillar_stats['answered_questions'] / pillar_stats['total_questions']) * 100, 1
                    )
                
                # Store pillar data
                report_data['pillars'][pillar_id] = {
                    'name': pillar_name,
                    'risk_counts': pillar_data.get('RiskCounts', {}),
                    'questions': detailed_answers,
                    'statistics': pillar_stats,
                    'notes': pillar_data.get('Notes', ''),
                    'improvement_plan': pillar_data.get('ImprovementPlan', '')
                }
                
            except Exception as e:
                logger.error(f"Error processing pillar {pillar_id}: {str(e)}")
                continue
        
        # Update summary statistics
        report_data['summary'].update({
            'total_questions': overall_stats['total_questions'],
            'answered_questions': overall_stats['answered_questions'],
            'unanswered_questions': overall_stats['total_questions'] - overall_stats['answered_questions'],
            'high_risks': risk_counts['HIGH'],
            'medium_risks': risk_counts['MEDIUM'],
            'low_risks': risk_counts['LOW'],
            'no_risks': risk_counts['NONE']
        })
        
        if overall_stats['total_questions'] > 0:
            report_data['summary']['completion_percentage'] = round(
                (overall_stats['answered_questions'] / overall_stats['total_questions']) * 100, 1
            )
        
        logger.info(f"Report generated successfully: {overall_stats['answered_questions']}/{overall_stats['total_questions']} questions answered")
        return report_data
        
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise

def is_question_answered(question):
    """
    Simplified logic to determine if a question is answered.
    
    Args:
        question: Question data from AWS API
        
    Returns:
        bool: True if question is answered
    """
    selected_choices = question.get('SelectedChoices', [])
    return bool(selected_choices and len(selected_choices) > 0)
