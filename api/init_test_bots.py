import os
import httpx
from fastapi import HTTPException
from config import SECRET_KEY

"""
Add tokens and the registration password to the environment variables.
MASTER1
MASTER2
SERVANT1
SERVANT2
TEMP_PASS
"""

async def create_test_projects():
    """Create test projects via API endpoint"""
    if not all(os.getenv(var) for var in ['MASTER1', 'MASTER2', 'SERVANT1', 'SERVANT2', 'TEMP_PASS']):
        print("Test bots not configured - skipping initialization")
        return

    test_projects = [
        {
            "master_token": os.getenv("MASTER1"),
            "servant_token": os.getenv("SERVANT1"),
            "master_reg_token": os.getenv("TEMP_PASS"),
            "servant_reg_token": os.getenv("TEMP_PASS")
        },
        {
            "master_token": os.getenv("MASTER2"),
            "servant_token": os.getenv("SERVANT2"),
            "master_reg_token": os.getenv("TEMP_PASS"),
            "servant_reg_token": os.getenv("TEMP_PASS")
        }
    ]

    headers = {
        "X-Secret-Key": SECRET_KEY,
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        for project in test_projects:
            try:
                response = await client.post(
                    "/projects",
                    json=project,
                    headers=headers
                )
                response.raise_for_status()
                print(f"✅ Project created: {response.json()}")
            except httpx.HTTPStatusError as e:
                print(f"⚠️ Failed to create project: {e.response.text}")
            except Exception as e:
                print(f"⚠️ Unexpected error: {str(e)}")

# Пример использования в main.py
if __name__ == "__main__":
    import asyncio
    asyncio.run(create_test_projects())