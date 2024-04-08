import os
import asyncio
import websockets
import json
import aiohttp
from urllib.parse import unquote
from services import directory_tree_to_json

import re


id = ""


def ensure_data_directory():
    if not os.path.exists("./data"):
        os.makedirs("./data")


async def saveFile(save_path, data):
    with open(save_path, "wb") as buffer:
        buffer.write(data)


async def get_tree_structure():
    return directory_tree_to_json("./data")


async def read_file_content(file_path):
    try:
        with open(file_path, "rb") as file:
            file_content = file.read()
            return file_content
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


async def download_file(download_code):
    download_url = f"http://localhost:8000/drive/download-file/{download_code}"
    async with aiohttp.ClientSession() as session:
        async with session.get(download_url) as response:
            print(f"Response status: {response.status}")
            if response.status == 200:
                content_disp = response.headers.get("Content-Disposition")
                print(content_disp)
                if content_disp and "filename=" in content_disp:

                    filename = (
                        content_disp.split("filename=")[1].split(";")[0].strip('"')
                    )

                    filename = unquote(filename)
                else:
                    filename = f"{download_code}.bin"

                save_path = os.path.join("./data", filename)
                print(f"Downloading file to: {save_path}")
                file_data = await response.read()
                await saveFile(save_path, file_data)
                print(f"File downloaded and saved as: {save_path}")
            else:
                print("Failed to download file.")


async def handle_file(websocket):
    try:
        message = await websocket.recv()
        print(f"Raw message received: {message}")
        if message:
            try:
                data = json.loads(message)
                if "download_code" in data:
                    await download_file(data["download_code"])
                else:
                    print(f"Received message: {data}")
                    await handle_request(websocket, data["action"])
            except json.JSONDecodeError as e:
                print(
                    f"JSONDecodeError occurred while decoding message: {message}, error: {e}"
                )
        else:
            print("Received an empty message or non-JSON message.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


async def handle_request(websocket, action):
    if action == "get_tree_structure":
        print("Sending directory structure")
        tree_structure = directory_tree_to_json("./data")
        try:
            response = {
                "DEVICE_ID": id,
                "action": "send_tree_structure",
                "data": tree_structure,
            }
            response = json.dumps(response)
            await websocket.send(response)
        except Exception as e:
            print(f"An error occurred: {e}")
        print("Directory structure sent")


async def connect_and_listen():
    ensure_data_directory()
    id_file_path = "./id.txt"

    if not os.path.exists(id_file_path):
        device_id = input("Enter your device_id: ").strip()
        with open(id_file_path, "w") as f:
            f.write(device_id)
    else:
        with open(id_file_path, "r") as f:
            device_id = f.read().strip()

    id = device_id

    headers = {"DEVICE_ID": device_id}
    uri = "ws://localhost:8000/drive/ws"

    async with websockets.connect(uri, extra_headers=headers) as websocket:
        while True:
            await handle_file(websocket)


asyncio.get_event_loop().run_until_complete(connect_and_listen())
