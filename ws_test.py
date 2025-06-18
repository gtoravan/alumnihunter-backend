import asyncio
import websockets

async def test_websocket():
    uri = "ws://3.tcp.ngrok.io:29365"
    try:
        async with websockets.connect(uri) as websocket:
            print("Connection successful")
            await websocket.send("Test message")
            response = await websocket.recv()
            print(f"Received response: {response}")
    except Exception as e:
        print(f"Failed to connect: {e}")

asyncio.run(test_websocket())
