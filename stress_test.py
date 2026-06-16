import asyncio
import time
import httpx


async def get_valid_jwt_token():
    """Logs into the API using Form Data to capture a real authorization token."""
    async with httpx.AsyncClient() as client:
        # Swagger / OAuth2 expects application/x-www-form-urlencoded data
        login_data = {"username": "admin", "password": "password123"}
        response = await client.post("http://127.0.0.1:8000/login", data=login_data)
        
        if response.status_code != 200:
            raise RuntimeError(f"❌ Login failed! Status: {response.status_code}. Verify your credentials.")
        
        token = response.json()["access_token"]
        print("🔑 Successfully authenticated. Received JWT Bearer Token.")
        return token

async def send_single_post_request(client: httpx.AsyncClient, headers: dict, request_id: int):
    try:
        start_time = time.time()
        # Fire a secure POST request containing the JSON payload and security headers
        response = await client.post(TARGET_URL, json=PAYLOAD, headers=headers, timeout=10.0)
        duration = time.time() - start_time
        return response.status_code, duration
    except Exception as e:
        return "ERROR", 0.0


# The containerized target URL 
TARGET_URL = "http://127.0.0.1:8000/logs"

# Adjust these numbers to scale your test
TOTAL_REQUESTS = 200
CONCURRENT_USERS = 20  # How many requests fired simultaneously in waves

# Sample dummy payload
PAYLOAD = {
    "subsystem_name": "stress_test_node",
    "error_code": 500,
    "response_time_ms": 42
}

# Real-world enterprise bypass: We will test a public endpoint or pass a mock payload.
# NOTE: If your /logs endpoint strictly requires authentication, we would pass headers.
# To keep this test focused on raw speed, let's assume your token security is temporarily bypassed 
# or change the TARGET_URL to a public endpoint like your root "/" or "/docs".
# For this run, let's hit a public route first to see absolute hardware speed!
PUBLIC_TARGET = "http://127.0.0.1:8000/logs" 
# PUBLIC_TARGET = "http://127.0.0.1:8000/"

async def send_single_request(client: httpx.AsyncClient, headers: dict, request_id: int):
    try:
        start_time = time.time()
        # Fire a non-blocking GET request to the root server
        response = await client.post(PUBLIC_TARGET, json=PAYLOAD, headers=headers, timeout=10.0)
        duration = time.time() - start_time
        return response.status_code, duration
    except Exception as e:
        return "ERROR", 0.0

async def main():
    # 1. Fetch the token before starting the flood gates
    try:
        token = await get_valid_jwt_token()
        print("TOKEN(demo):",token)
    except Exception as e:
        print(e)
        return
    # 2. Package the token into standard HTTP Authorization header format
    headers = {"Authorization": f"Bearer {token}"}

    print(f"🚀 Starting stress test: Sending {TOTAL_REQUESTS} total requests...")
    print(f"🔥 Concurrency Level: {CONCURRENT_USERS} simultaneous workers pushing the container...")
    
    # Limits control how many concurrent connections are physically open at once
    limits = httpx.Limits(max_connections=CONCURRENT_USERS, max_keepalive_connections=CONCURRENT_USERS)
    
    start_suite = time.time()
    
    async with httpx.AsyncClient(limits=limits) as client:
        # Create a pool of tasks to execute concurrently
        tasks = [send_single_request(client, headers, i) for i in range(TOTAL_REQUESTS)]
        
        # Gather all results as they cross the finish line
        results = await asyncio.gather(*tasks)
    
    total_suite_time = time.time() - start_suite
    
    # Metrics Calculation
    success_count = sum(1 for status, _ in results if status == 200)
    error_count = sum(1 for status, _ in results if status == "ERROR" or status != 200)
    durations = [dur for _, dur in results if dur > 0.0]
    
    avg_response_time = (sum(durations) / len(durations)) * 1000 if durations else 0
    requests_per_second = TOTAL_REQUESTS / total_suite_time
    
    print("\n--- PERFORMANCE TELEMETRY RESULTS ---")
    print(f"⏱️  Total Execution Time:    {total_suite_time:.2f} seconds")
    print(f"📊 Throughput:              {requests_per_second:.2f} Requests/Second (RPS)")
    print(f"✅ Successful Requests (200): {success_count}")
    print(f"❌ Failed/Blocked Requests:   {error_count}")
    print(f"⚡ Avg Latency per Request:  {avg_response_time:.1f} ms")
    print("------------------------------------")

if __name__ == "__main__":
    asyncio.run(main())