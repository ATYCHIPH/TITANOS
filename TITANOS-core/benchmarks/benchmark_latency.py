import asyncio
import time
from httpx import AsyncClient
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from titanos.server.app import app

async def benchmark_endpoint(url: str, concurrency: int, total_requests: int):
    print(f"Benchmarking {url} with {concurrency} concurrent connections, total {total_requests} requests...")
    
    async def make_request(ac: AsyncClient):
        start = time.perf_counter()
        response = await ac.get(url)
        end = time.perf_counter()
        return end - start, response.status_code

    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Warmup
        await ac.get(url)
        
        times = []
        statuses = []
        
        tasks = []
        for _ in range(total_requests):
            tasks.append(asyncio.create_task(make_request(ac)))
            
        results = await asyncio.gather(*tasks)
        
        for t, status in results:
            times.append(t)
            statuses.append(status)
            
    if not times:
        print("No requests completed.")
        return
        
    times.sort()
    mean_latency = sum(times) / len(times) * 1000
    p95 = times[int(len(times) * 0.95)] * 1000
    p99 = times[int(len(times) * 0.99)] * 1000
    
    print("\nResults:")
    print(f"Mean Latency: {mean_latency:.2f} ms")
    print(f"p95 Latency:  {p95:.2f} ms")
    print(f"p99 Latency:  {p99:.2f} ms")
    
    successes = sum(1 for s in statuses if s == 200)
    print(f"Success Rate: {successes / total_requests * 100:.1f}%")

if __name__ == "__main__":
    asyncio.run(benchmark_endpoint("/healthz", concurrency=20, total_requests=100))
