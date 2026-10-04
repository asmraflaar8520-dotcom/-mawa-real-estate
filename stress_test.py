import sys
import asyncio
import time
import statistics
import httpx
from typing import List, Dict, Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://127.0.0.1:8000"

async def simulate_user_request(client: httpx.AsyncClient, endpoint: str, method: str = "GET", json_data: dict = None) -> Dict[str, Any]:
    start_time = time.perf_counter()
    try:
        if method == "GET":
            response = await client.get(endpoint, timeout=15.0)
        elif method == "POST":
            response = await client.post(endpoint, json=json_data, timeout=15.0)
        else:
            response = await client.request(method, endpoint, timeout=15.0)
        
        latency_ms = (time.perf_counter() - start_time) * 1000
        return {
            "status_code": response.status_code,
            "success": 200 <= response.status_code < 400,
            "latency_ms": latency_ms,
            "error": None
        }
    except Exception as e:
        latency_ms = (time.perf_counter() - start_time) * 1000
        return {
            "status_code": 0,
            "success": False,
            "latency_ms": latency_ms,
            "error": str(type(e).__name__)
        }

async def run_concurrent_stage(concurrency: int, total_requests: int, endpoint: str, method: str = "GET", json_data: dict = None) -> Dict[str, Any]:
    limits = httpx.Limits(max_connections=concurrency + 20, max_keepalive_connections=concurrency)
    async with httpx.AsyncClient(base_url=BASE_URL, limits=limits) as client:
        # Pre-warm
        try:
            await client.get("/api/properties")
        except Exception:
            pass

        semaphore = asyncio.Semaphore(concurrency)
        
        async def bounded_request():
            async with semaphore:
                return await simulate_user_request(client, endpoint, method, json_data)

        wall_start = time.perf_counter()
        tasks = [bounded_request() for _ in range(total_requests)]
        results = await asyncio.gather(*tasks)
        total_duration = time.perf_counter() - wall_start

    latencies = [r["latency_ms"] for r in results]
    successes = [r for r in results if r["success"]]
    failures = [r for r in results if not r["success"]]

    latencies_sorted = sorted(latencies)
    p50 = statistics.median(latencies_sorted) if latencies_sorted else 0
    p95 = latencies_sorted[int(len(latencies_sorted) * 0.95)] if latencies_sorted else 0
    p99 = latencies_sorted[int(len(latencies_sorted) * 0.99)] if latencies_sorted else 0
    avg_latency = statistics.mean(latencies) if latencies else 0
    rps = total_requests / total_duration if total_duration > 0 else 0

    return {
        "concurrency": concurrency,
        "total_requests": total_requests,
        "duration_sec": total_duration,
        "rps": rps,
        "success_count": len(successes),
        "failure_count": len(failures),
        "success_rate": (len(successes) / total_requests) * 100,
        "avg_latency_ms": avg_latency,
        "p50_ms": p50,
        "p95_ms": p95,
        "p99_ms": p99,
        "min_ms": min(latencies) if latencies else 0,
        "max_ms": max(latencies) if latencies else 0,
    }

async def main():
    print("=" * 70)
    print("LOAD & CONCURRENCY STRESS TEST - MA'WA REAL ESTATE PLATFORM")
    print(f"Target: {BASE_URL}")
    print("=" * 70)

    stages = [
        {"concurrency": 25, "requests": 100, "name": "Stage 1: Light (25 concurrent users)"},
        {"concurrency": 50, "requests": 250, "name": "Stage 2: Medium (50 concurrent users)"},
        {"concurrency": 100, "requests": 500, "name": "Stage 3: High (100 concurrent users)"},
        {"concurrency": 250, "requests": 1000, "name": "Stage 4: Stress (250 concurrent users)"},
        {"concurrency": 500, "requests": 1500, "name": "Stage 5: Extreme Peak (500 concurrent users)"},
    ]

    print("\n--- [TEST 1] Public Property Browsing & Search (/api/properties) ---")
    for s in stages:
        res = await run_concurrent_stage(s["concurrency"], s["requests"], "/api/properties")
        print(f"\n[+] {s['name']}:")
        print(f"    - Concurrency: {res['concurrency']} parallel users")
        print(f"    - Requests: {res['total_requests']} in {res['duration_sec']:.2f}s")
        print(f"    - Throughput: {res['rps']:.1f} req/sec (RPS)")
        print(f"    - Success Rate: {res['success_rate']:.1f}% ({res['success_count']} OK / {res['failure_count']} Err)")
        print(f"    - Latency: Avg={res['avg_latency_ms']:.1f}ms | p50={res['p50_ms']:.1f}ms | p95={res['p95_ms']:.1f}ms | Max={res['max_ms']:.1f}ms")

    print("\n\n--- [TEST 2] Static Frontend Landing Page (/) ---")
    frontend_stages = [
        {"concurrency": 50, "requests": 200, "name": "50 concurrent homepage visitors"},
        {"concurrency": 150, "requests": 500, "name": "150 concurrent homepage visitors"},
        {"concurrency": 300, "requests": 1000, "name": "300 concurrent homepage visitors"},
    ]
    for s in frontend_stages:
        res = await run_concurrent_stage(s["concurrency"], s["requests"], "/")
        print(f"\n[+] {s['name']}:")
        print(f"    - Throughput: {res['rps']:.1f} req/sec (RPS)")
        print(f"    - Success Rate: {res['success_rate']:.1f}%")
        print(f"    - Latency: Avg={res['avg_latency_ms']:.1f}ms | p95={res['p95_ms']:.1f}ms")

    print("\n\n--- [TEST 3] User Authentication & Bcrypt Hashing (/api/auth/login) ---")
    auth_stages = [
        {"concurrency": 10, "requests": 20, "name": "10 concurrent logins"},
        {"concurrency": 25, "requests": 50, "name": "25 concurrent logins"},
        {"concurrency": 50, "requests": 100, "name": "50 concurrent logins"},
    ]
    for s in auth_stages:
        login_payload = {"email": "buyer.ahmed@mawa.eg", "password": "BuyerPass123!"}
        res = await run_concurrent_stage(s["concurrency"], s["requests"], "/api/auth/login", method="POST", json_data=login_payload)
        print(f"\n[+] {s['name']}:")
        print(f"    - Throughput: {res['rps']:.1f} req/sec (RPS)")
        print(f"    - Success Rate: {res['success_rate']:.1f}%")
        print(f"    - Latency: Avg={res['avg_latency_ms']:.1f}ms | p95={res['p95_ms']:.1f}ms")

    print("\n" + "=" * 70)
    print("ALL LOAD TESTING STAGES COMPLETED!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
