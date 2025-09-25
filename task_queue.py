#!/usr/bin/env python3
"""
TorWAR Background Task Queue - Async task processing
Author: Mohamed Toraif
"""

import threading
import queue
import time
from typing import Callable, Any, Dict
from datetime import datetime
from cache_manager import cache
import uuid

class TaskQueue:
    """Simple background task queue for heavy operations."""
    
    def __init__(self, max_workers=3):
        self.task_queue = queue.Queue()
        self.results = {}
        self.workers = []
        self.running = True
        
        # Start worker threads
        for i in range(max_workers):
            worker = threading.Thread(target=self._worker, daemon=True)
            worker.start()
            self.workers.append(worker)
    
    def _worker(self):
        """Worker thread to process tasks."""
        while self.running:
            try:
                task = self.task_queue.get(timeout=1)
                if task is None:
                    break
                
                task_id, func, args, kwargs = task
                
                try:
                    # Update task status
                    self.results[task_id] = {
                        'status': 'running',
                        'started_at': datetime.now().isoformat()
                    }
                    
                    # Execute task
                    result = func(*args, **kwargs)
                    
                    # Store result
                    self.results[task_id] = {
                        'status': 'completed',
                        'result': result,
                        'completed_at': datetime.now().isoformat()
                    }
                    
                except Exception as e:
                    self.results[task_id] = {
                        'status': 'failed',
                        'error': str(e),
                        'failed_at': datetime.now().isoformat()
                    }
                
                self.task_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Worker error: {e}")
    
    def submit(self, func: Callable, *args, **kwargs) -> str:
        """Submit a task to the queue."""
        task_id = str(uuid.uuid4())
        
        self.results[task_id] = {
            'status': 'queued',
            'queued_at': datetime.now().isoformat()
        }
        
        self.task_queue.put((task_id, func, args, kwargs))
        return task_id
    
    def get_status(self, task_id: str) -> Dict[str, Any]:
        """Get task status and result."""
        return self.results.get(task_id, {'status': 'not_found'})
    
    def cleanup_old_results(self, max_age_hours=24):
        """Clean up old task results."""
        cutoff = datetime.now().timestamp() - (max_age_hours * 3600)
        
        to_remove = []
        for task_id, result in self.results.items():
            if 'completed_at' in result or 'failed_at' in result:
                timestamp_str = result.get('completed_at') or result.get('failed_at')
                if timestamp_str:
                    task_time = datetime.fromisoformat(timestamp_str).timestamp()
                    if task_time < cutoff:
                        to_remove.append(task_id)
        
        for task_id in to_remove:
            del self.results[task_id]
    
    def shutdown(self):
        """Shutdown the task queue."""
        self.running = False
        
        # Signal workers to stop
        for _ in self.workers:
            self.task_queue.put(None)
        
        # Wait for workers to finish
        for worker in self.workers:
            worker.join(timeout=5)

# Background task functions
def refresh_trusted_advisor_cache():
    """Background task to refresh Trusted Advisor cache."""
    try:
        from async_aws_service import async_aws
        recommendations = async_aws.run_async(async_aws.get_recommendations_batch())
        
        # Update cache
        cache_key = f"recommendations:{async_aws.profile}:{async_aws.region}"
        cache.set(cache_key, recommendations, ttl=600)
        
        return {
            'success': True,
            'count': len(recommendations),
            'updated_at': datetime.now().isoformat()
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}

def refresh_workloads_cache():
    """Background task to refresh workloads cache."""
    try:
        from async_aws_service import async_aws
        workloads = async_aws.run_async(async_aws.get_workloads_async())
        
        return {
            'success': True,
            'count': len(workloads),
            'updated_at': datetime.now().isoformat()
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}

# Global task queue
task_queue = TaskQueue()
