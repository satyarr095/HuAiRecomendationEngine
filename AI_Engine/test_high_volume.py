#!/usr/bin/env python3
"""
High-Volume Performance Test for AI Recommendation Engine
Tests the system's ability to handle 10,000+ requests
"""

import asyncio
import time
import json
import statistics
from concurrent.futures import ThreadPoolExecutor
import aiohttp
import random
from typing import List, Dict

# Test data samples
TEST_DATA_SAMPLES = [
    {
        "user_id": "test_001",
        "interests": ["python programming", "web development"],
        "skills": ["basic coding", "html"],
        "experience_level": "beginner",
        "goals": ["become full stack developer"]
    },
    {
        "user_id": "test_002", 
        "interests": ["data science", "machine learning"],
        "skills": ["python", "statistics"],
        "experience_level": "intermediate",
        "goals": ["data scientist role"]
    },
    {
        "user_id": "test_003",
        "interests": ["javascript", "react"],
        "skills": ["frontend development"],
        "experience_level": "advanced",
        "goals": ["senior developer"]
    },
    {
        "user_id": "test_004",
        "interests": ["cybersecurity", "networking"],
        "skills": ["linux", "networking"],
        "experience_level": "beginner",
        "goals": ["security analyst"]
    },
    {
        "user_id": "test_005",
        "interests": ["mobile development", "android"],
        "skills": ["java", "kotlin"],
        "experience_level": "intermediate",
        "goals": ["mobile app developer"]
    }
]

class PerformanceTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = []
        
    async def single_request_test(self, session: aiohttp.ClientSession, test_data: Dict) -> Dict:
        """Test a single API request"""
        start_time = time.time()
        
        try:
            async with session.post(
                f"{self.base_url}/api/recommendations",
                json={"jsonData": test_data},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    processing_time = time.time() - start_time
                    
                    return {
                        "success": True,
                        "response_time": processing_time,
                        "status_code": response.status,
                        "recommendations_count": len(result.get("recommendations", [])),
                        "has_skill_gaps": len(result.get("skillGaps", [])) > 0,
                        "has_learning_paths": len(result.get("learningPaths", [])) > 0
                    }
                else:
                    return {
                        "success": False,
                        "response_time": time.time() - start_time,
                        "status_code": response.status,
                        "error": f"HTTP {response.status}"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "response_time": time.time() - start_time,
                "error": str(e)
            }

    async def concurrent_test(self, num_requests: int = 100, concurrent_limit: int = 20) -> Dict:
        """Test concurrent requests with specified limits"""
        print(f"\n🚀 Testing {num_requests} concurrent requests (max {concurrent_limit} at once)...")
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(concurrent_limit)
        
        async def limited_request(session, test_data):
            async with semaphore:
                return await self.single_request_test(session, test_data)
        
        # Create test data for all requests
        test_requests = []
        for i in range(num_requests):
            test_data = random.choice(TEST_DATA_SAMPLES).copy()
            test_data["user_id"] = f"load_test_{i:04d}"
            test_requests.append(test_data)
        
        # Execute all requests concurrently
        start_time = time.time()
        
        connector = aiohttp.TCPConnector(limit=concurrent_limit)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [limited_request(session, data) for data in test_requests]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = time.time() - start_time
        
        # Process results
        successful_results = [r for r in results if isinstance(r, dict) and r.get("success")]
        failed_results = [r for r in results if not isinstance(r, dict) or not r.get("success")]
        
        if successful_results:
            response_times = [r["response_time"] for r in successful_results]
            
            stats = {
                "total_requests": num_requests,
                "successful_requests": len(successful_results),
                "failed_requests": len(failed_results),
                "success_rate": len(successful_results) / num_requests * 100,
                "total_time": total_time,
                "requests_per_second": num_requests / total_time,
                "avg_response_time": statistics.mean(response_times),
                "median_response_time": statistics.median(response_times),
                "min_response_time": min(response_times),
                "max_response_time": max(response_times),
                "p95_response_time": self._percentile(response_times, 95),
                "p99_response_time": self._percentile(response_times, 99)
            }
        else:
            stats = {
                "total_requests": num_requests,
                "successful_requests": 0,
                "failed_requests": len(failed_results),
                "success_rate": 0,
                "total_time": total_time,
                "error": "No successful requests"
            }
        
        return stats

    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of response times"""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]

    async def health_check(self) -> bool:
        """Check if the API is responsive"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                    return response.status == 200
        except:
            return False

    async def stress_test_sequence(self):
        """Run a sequence of stress tests with increasing load"""
        print("🔥 AI Recommendation Engine - High Volume Stress Test")
        print("=" * 60)
        
        # Health check first
        print("🏥 Checking API health...")
        if not await self.health_check():
            print("❌ API is not responding. Please start the server first.")
            return
        print("✅ API is healthy")
        
        # Test scenarios
        test_scenarios = [
            {"requests": 10, "concurrent": 5, "name": "Warm-up Test"},
            {"requests": 50, "concurrent": 10, "name": "Light Load"},
            {"requests": 100, "concurrent": 20, "name": "Medium Load"},
            {"requests": 500, "concurrent": 50, "name": "Heavy Load"},
            {"requests": 1000, "concurrent": 100, "name": "Stress Test"},
            {"requests": 5000, "concurrent": 200, "name": "High Volume Test"},
            {"requests": 10000, "concurrent": 300, "name": "Maximum Capacity Test"}
        ]
        
        all_results = []
        
        for scenario in test_scenarios:
            print(f"\n📊 Running: {scenario['name']}")
            print("-" * 40)
            
            try:
                stats = await self.concurrent_test(
                    num_requests=scenario["requests"],
                    concurrent_limit=scenario["concurrent"]
                )
                
                # Display results
                if stats.get("success_rate", 0) > 0:
                    print(f"✅ Success Rate: {stats['success_rate']:.1f}%")
                    print(f"⚡ Requests/sec: {stats['requests_per_second']:.1f}")
                    print(f"⏱️  Avg Response: {stats['avg_response_time']:.3f}s")
                    print(f"📈 P95 Response: {stats['p95_response_time']:.3f}s")
                    print(f"📊 P99 Response: {stats['p99_response_time']:.3f}s")
                    
                    # Stop if performance degrades significantly
                    if stats['success_rate'] < 95 or stats['avg_response_time'] > 10:
                        print("⚠️  Performance degradation detected!")
                        if stats['success_rate'] < 50:
                            print("❌ Stopping tests due to high failure rate")
                            break
                else:
                    print(f"❌ Test failed: {stats.get('error', 'Unknown error')}")
                    break
                    
                all_results.append({"scenario": scenario["name"], **stats})
                
                # Brief pause between tests
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"❌ Test failed with exception: {e}")
                break
        
        # Summary
        print("\n📋 PERFORMANCE SUMMARY")
        print("=" * 60)
        
        if all_results:
            max_rps = max(r['requests_per_second'] for r in all_results if 'requests_per_second' in r)
            best_scenario = max(all_results, key=lambda x: x.get('total_requests', 0) if x.get('success_rate', 0) > 95 else 0)
            
            print(f"🚀 Maximum throughput: {max_rps:.1f} requests/second")
            print(f"📊 Best performing scenario: {best_scenario['scenario']}")
            print(f"✅ Maximum successful requests: {best_scenario.get('total_requests', 0)}")
            print(f"⚡ System can handle high volume: {'YES' if max_rps > 50 else 'NEEDS OPTIMIZATION'}")
        
        return all_results

async def main():
    """Main test runner"""
    tester = PerformanceTester()
    results = await tester.stress_test_sequence()
    
    # Save results to file
    with open("performance_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: performance_test_results.json")

if __name__ == "__main__":
    asyncio.run(main()) 