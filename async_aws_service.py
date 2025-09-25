#!/usr/bin/env python3
"""
TorWAR Async AWS Service - High-performance async AWS operations
Author: Mohamed Toraif
"""

import asyncio
import aioboto3
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any
from cache_manager import cache
import json

class AsyncAWSService:
    """Async AWS service for high-performance operations."""
    
    def __init__(self, region='us-east-1', profile=None):
        self.region = region
        self.profile = profile or 'tau-dev'
        self.executor = ThreadPoolExecutor(max_workers=10)
    
    async def get_workloads_async(self) -> List[Dict]:
        """Get workloads asynchronously with caching."""
        cache_key = f"workloads:{self.profile}:{self.region}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        session = aioboto3.Session(profile_name=self.profile)
        async with session.client('wellarchitected', region_name=self.region) as client:
            try:
                response = await client.list_workloads(MaxResults=50)
                workloads = response.get('WorkloadSummaries', [])
                cache.set(cache_key, workloads, ttl=300)  # 5 min cache
                return workloads
            except Exception as e:
                print(f"Error fetching workloads: {e}")
                return []
    
    async def get_recommendations_batch(self, batch_size=10) -> List[Dict]:
        """Get Trusted Advisor recommendations in batches."""
        cache_key = f"recommendations:{self.profile}:{self.region}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        session = aioboto3.Session(profile_name=self.profile)
        async with session.client('trustedadvisor', region_name='us-east-1') as client:
            try:
                all_recommendations = []
                next_token = None
                
                while len(all_recommendations) < 100:  # Limit for performance
                    params = {'maxResults': batch_size}
                    if next_token:
                        params['nextToken'] = next_token
                    
                    response = await client.list_recommendations(**params)
                    recommendations = response.get('recommendationSummaries', [])
                    all_recommendations.extend(recommendations)
                    
                    next_token = response.get('nextToken')
                    if not next_token:
                        break
                
                cache.set(cache_key, all_recommendations, ttl=600)  # 10 min cache
                return all_recommendations
            except Exception as e:
                print(f"Error fetching recommendations: {e}")
                return []
    
    def run_async(self, coro):
        """Run async function in thread pool."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

# Global async service
async_aws = AsyncAWSService()
