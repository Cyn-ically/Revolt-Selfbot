import websocket
import json
import time
import threading
import logging
import aiohttp, asyncio
import uuid
import os, requests
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(level=logging.CRITICAL) # Switch to logging.INFO for more verbose output
logger = logging.getLogger('revolt_bot')

def load_config():
    try:
        if os.path.exists('config.json'):
            with open('config.json', 'r') as f:
                return json.load(f)
        else:
            default_config = {
                "token": "YOUR_TOKEN_HERE",
                "prefix": "!",
                "custom_status": True,
                "custom_status_text": "Ramona-Flower",
                "custom_status_type": "Busy", 
                "commands": {
                    "help": "Show this help message",
                    "hello": "Get a greeting from the bot",
                    "userinfo": "Fetch user info",
                    "username": "Change your username (usage: !username <new_name>)",
                    "reloadnames": "Reload usernames from config/usernames.txt",
                    "customstatus": "Set a custom status for the bot (usage: !customstatus <status_message>)"

                },
                "auto_switch_username": {
                    "enabled": False,
                    "delay": 30
                }
            }
            with open('config.json', 'w') as f:
                json.dump(default_config, f, indent=4)
            logger.warning("Created default config.json - please edit with your token")
            return default_config
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {"token": "", "prefix": "!", "commands": {}}

def load_usernames():
    os.makedirs('config', exist_ok=True)

    try:
        if os.path.exists('./config/usernames.txt'):
            with open('./config/usernames.txt', 'r') as f:
                return [line.strip() for line in f.readlines() if line.strip()]
        else:
            default_names = ["Example1", "Example2", "Example3"]
            with open('./config/usernames.txt', 'w') as f:
                f.write('\n'.join(default_names))
            logger.warning("Created default config/usernames.txt - please edit with your desired usernames")
            return default_names
    except Exception as e:
        logger.error(f"Error loading usernames: {e}")
        return []

async def change_status(client, custom_status, custom_type):
    try:
        if not client.config.get("custom_status", False):
            logger.info("Custom status is disabled.")
            return False, "Custom status is disabled."
        if not client.config.get("custom_status_text", ""):
            logger.info("Custom status text is not set.")
            return False, "Custom status text is not set."
        
        if not client.config.get("custom_status_type", ""):
            logger.info("Custom status type is not set.")
            return False, "Custom status type is not set."
        
        custom_type = custom_type.capitalize()
        if custom_type not in ["Online", "Idle", "Focus", "Invisible", "Busy"]:
            logger.info("Invalid status type. Please choose from: Online, Idle, Do Not Disturb, Invisible, Busy")
            return False, "Invalid status type. Please choose from: Online, Idle, Do Not Disturb, Invisible, Busy"
        
        update_payload = {
            "type": "UserUpdate",
            "id": client.user_id,
            "data": {
                "online": True,
                "status": {
                    "text": custom_status,
                    "presence": custom_type
                }
            },
            "clear": [],
            "event_id": None
        }
        client.ws.send(json.dumps(update_payload))
        
        return True, f"Successfully updated your status to: {custom_status}"
    except Exception as e:
        logger.error(f"Exception during status update: {e}")
        return False, f"Error updating status: {str(e)}"

async def update_status_periodically(client):
    custom_status = client.config.get("custom_status_text", "Ramona-Flower")
    custom_type = client.config.get("custom_status_type", "Busy")

    while True:
        success, message = await change_status(client, custom_status, custom_type)
        if not success:
            logger.error(f"Failed to update status: {message}")
        await asyncio.sleep(10)
        
        
async def change_username(client, new_name):
    try:
        update_payload = {
            "type": "UserUpdate",
            "id": client.user_id,
            "data": {
                "display_name": new_name
            },
            "clear": [],
            "event_id": None
        }
        client.ws.send(json.dumps(update_payload))
        logger.info(f"Successfully changed username to: {new_name}")
        return True, f"Successfully changed username to: {new_name}"
    except Exception as e:
        logger.error(f"Exception during username change: {e}")
        return False, f"Error changing username: {str(e)}"

async def auto_username_changer(client):
    config = load_config()
    auto_switch = config.get("auto_switch_username", {})

    if not auto_switch.get("enabled", False):
        logger.info("Auto username switching is disabled")
        return

    names = load_usernames()
    if not names:
        logger.warning("Auto username switching is enabled but no names were found in config/usernames.txt")
        return

    interval_seconds = auto_switch.get("delay", 30)

    logger.info(f"Starting auto username changer - rotating through names every {interval_seconds} seconds")

    name_index = 0
    while True:
        names = load_usernames()
        if not names:
            logger.warning("Username list is empty - pausing auto username changer")
            await asyncio.sleep(interval_seconds)
            continue

        new_name = names[name_index % len(names)]
        success, message = await change_username(client, new_name)

        if success:
            logger.info(f"Auto-switched username to: {new_name}")
        else:
            logger.error(f"Auto-switch failed: {message}")

        name_index = (name_index + 1) % len(names)
        await asyncio.sleep(interval_seconds)

async def send_revolt_message_with_session(channel_id, message_content, embed=None):
    config = load_config()
    token = config.get("token")
    if not token:
        logger.error("Token not found in config")
        return None

    SESSION_TOKEN = token
    NONCE = str(uuid.uuid4()).replace("-", "").upper()[:24]
    API_URL = "https://app.revolt.chat/api"

    headers = {
        "Content-Type": "application/json",
        "x-session-token": SESSION_TOKEN
    }

    data = {
        "content": message_content,
        "nonce": NONCE,
        "replies": []
    }

    if embed:
        data["embeds"] = [embed]

    async with aiohttp.ClientSession() as session:
        try:
            endpoint = f"{API_URL}/channels/{channel_id}/messages"
            async with session.post(endpoint, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    text = await response.text()
                    logger.error(f"Failed to send message. Status {response.status}: {text}")
                    return None
        except Exception as e:
            logger.error(f"Exception occurred during API request: {e}")
            return None

async def fetch_user_bio(user_id):
    config = load_config()
    token = config.get("token")
    if not token:
        logger.error("Token not found in config")
        return None

    API_URL = f"https://app.revolt.chat/api/users/{user_id}/profile"
    HEADERS = {
        "Content-Type": "application/json",
        "x-session-token": token,
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
    }

    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(ThreadPoolExecutor(), lambda: requests.get(API_URL, headers=HEADERS))

    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Failed to fetch user info: {response.status_code}\nResponse: {response.text}")
        return None

class RevoltClient:
    def __init__(self, token):
        self.token = token
        self.ws = None
        self.user_id = None
        self.connected = False
        self.message_handlers = {}
        self.config = load_config()
        self.prefix = self.config["prefix"]
        self.commands = self.config["commands"]
        self.username_task = None
        self.loop = asyncio.get_event_loop()

    def connect(self):
        self.ws = websocket.WebSocketApp(
            "wss://app.revolt.chat/events",
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )

        wst = threading.Thread(target=self.ws.run_forever)
        wst.daemon = True
        wst.start()

        timeout = 15
        while not self.connected and timeout > 0:
            time.sleep(1)
            timeout -= 1

        if not self.connected:
            raise ConnectionError("Failed to connect to Revolt WebSocket API")

        return self.connected

    def on_open(self, ws):
        print("Connection established. Authenticating...")
        auth_payload = {
            "type": "Authenticate",
            "token": self.token
        }
        ws.send(json.dumps(auth_payload))

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            msg_type = data.get("type")

            if msg_type == "Authenticated":
                print("Authentication successful!")

            elif msg_type == "Ready":
                self.connected = True
                if "users" in data and len(data["users"]) > 0:
                    for user in data["users"]:
                        if user.get("relationship") == "User":
                            self.user_id = user.get("_id")
                            print(f"Connected as: {user.get('username')}#{user.get('discriminator')}")
                print("Client is ready!")

                if "servers" in data:
                    print(f"Server loaded: {len(data['servers'])} servers")
                    for server in data['servers']:
                        print(f"- {server.get('name')}")

                if self.config.get("auto_switch_username", {}).get("enabled", False):
                    self.username_task = self.loop.create_task(auto_username_changer(self))

                self.loop.create_task(update_status_periodically(self))

            elif msg_type == "Ping":
                pong_payload = {
                    "type": "Pong",
                    "data": data.get("data"),
                    "token": self.token
                }
                ws.send(json.dumps(pong_payload))

            elif msg_type == "Message":
                author = data.get("author")
                content = data.get("content")
                channel = data.get("channel")

                print(f"Received message in channel {channel} from {author}: {content}")

                if author == self.user_id:
                    if "message" in self.message_handlers:
                        for handler in self.message_handlers["message"]:
                            handler(data)

            else:
                pass

        except json.JSONDecodeError:
            print(f"Error decoding message: {message}")
        except Exception as e:
            print(f"Error processing message: {e}")

    def on_error(self, ws, error):
        print(f"WebSocket error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        self.connected = False
        print(f"WebSocket connection closed: {close_status_code} - {close_msg}")

    def send_message(self, channel_id, content):
        if not self.connected:
            print("Not connected. Cannot send message.")
            return False

        message_payload = {
            "type": "SendMessage",
            "channel": channel_id,
            "content": content,
            "nonce": f"nonce-{int(time.time() * 1000)}",
            "token": self.token
        }

        self.ws.send(json.dumps(message_payload))
        return True

    def on_message_received(self, handler):
        if "message" not in self.message_handlers:
            self.message_handlers["message"] = []
        self.message_handlers["message"].append(handler)

    def start_typing(self, channel_id):
        if not self.connected:
            return False

        typing_payload = {
            "type": "BeginTyping",
            "channel": channel_id,
            "x-session-token": self.token
        }

        self.ws.send(json.dumps(typing_payload))
        return True

    def stop_typing(self, channel_id):
        if not self.connected:
            return False

        typing_payload = {
            "type": "EndTyping",
            "channel": channel_id,
            "x-session-token": self.token
        }

        self.ws.send(json.dumps(typing_payload))
        return True

    def close(self):
        if self.ws:
            self.ws.close()

async def main():
    TOKEN = "2WvDRW6hKB1WRNXz9U8JBoVwxEE1Srg_zW7PTlJBE5Exmo__5Zb88I6u4Onsbd-f"

    client = RevoltClient(TOKEN)

    try:
        client.connect()

        def message_handler(message_data):
            content = message_data.get("content").strip()
            if content.startswith(client.prefix):
                parts = content[len(client.prefix):].strip().split(maxsplit=1)
                command = parts[0]
                args = parts[1] if len(parts) > 1 else ""

                if command == "userinfo" and args:
                    user_id = args.strip('<@>')

                    user_data = asyncio.run(fetch_user_bio(user_id))
                    background_id = user_data.get("background", {}).get("_id", None)
                    background_url = f"https://autumn.revolt.chat/backgrounds/{background_id}?width=1000" if background_id else None

                    description = f"""User: <@{user_id}>\n\nUser description:\n\n`{user_data.get("content", "No bio available")}`"""

                    if background_url:
                        description += f"\n\nBanner URL: {background_url}"

                    if user_data:
                        embed = {
                            "type": "Website",
                            "title": f"Revolt.chat Selfbot - User Info",
                            "description": description,
                            "colour": "#3498db",
                            "image": None
                        }

                        asyncio.run(send_revolt_message_with_session(message_data.get("channel"), "", embed))
                    else:
                        client.send_message(message_data.get("channel"), "Failed to fetch user info.")

                elif command == "help":
                    commands_text = "\n".join([f"**{cmd}**: {desc}" for cmd, desc in client.commands.items()])
                    embed = {
                        "type": "Website",
                        "title": "Revolt.chat Selfbot - Bot Help",
                        "description": f"Here are the available commands:\n\n{commands_text}",
                        "colour": "#ff5733"
                    }

                    result = asyncio.run(send_revolt_message_with_session(
                        message_data.get("channel"),
                        "Here's the help information:",
                        embed
                    ))

                    if not result:
                        client.send_message(message_data.get("channel"), "Failed to display help. Check logs for details.")
                elif command == "customstatus":
                    if not args:
                        client.send_message(message_data.get("channel"), f"Please provide a custom status. Usage: `{client.prefix}customstatus <status_message>`")
                        return

                    custom_status = args.strip()

                    custom_status_type = client.config.get("custom_status_type", "Busy")
                    success, response_msg = asyncio.run(change_status(client, custom_status, custom_status_type))
                    client.send_message(message_data.get("channel"), response_msg)

                elif command == "hello":
                    client.send_message(message_data.get("channel"), "Hello there! 👋")

                elif command == "username":
                    if not args:
                        client.send_message(message_data.get("channel"), f"Please provide a new username. Usage: `{client.prefix}username <new_name>`")
                        return

                    success, response_msg = asyncio.run(change_username(client, args))
                    client.send_message(message_data.get("channel"), response_msg)

                elif command == "reloadnames":
                    names = load_usernames()
                    if names:
                        client.send_message(message_data.get("channel"), f"Reloaded {len(names)} usernames from config/usernames.txt")
                    else:
                        client.send_message(message_data.get("channel"), "No usernames found in config/usernames.txt")

                else:
                    client.send_message(message_data.get("channel"), f"Unknown command: {command}")

        client.on_message_received(message_handler)

        while client.connected:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        client.close()
        print("Client closed.")
        
        
asyncio.run(main())
