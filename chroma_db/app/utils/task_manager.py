import asyncio

active_tasks = {}

def get_client_ip(request):
    return request.client.host

async def cancel_existing_task(ip):
    if ip in active_tasks:
        task = active_tasks[ip]
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                print(f"❌ Previous task for {ip} cancelled.")
        del active_tasks[ip]
