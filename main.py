import revolt
import asyncio
import logging
import aiohttp
import uuid
import json
import os
from concurrent.futures import ThreadPoolExecutor
import requests

logging.basicConfig(level=logging.CRITICAL)
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
                "commands": {
                    "help": "Show this help message",
                    "hello": "Get a greeting from the bot",
                    "userinfo": "Fetch user info"

                }
            }
            with open('config.json', 'w') as f:
                json.dump(default_config, f, indent=4)
            logger.warning("Created default config.json - please edit with your token")
            return default_config
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {"token": "", "prefix": "!", "commands": {}}

async def send_revolt_message_with_session(channel_id, message_content, embed=None):
    config = load_config()
    SESSION_TOKEN = config["token"]
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
    API_URL = f"https://app.revolt.chat/api/users/{user_id}/profile"
    HEADERS = {
        "Content-Type": "application/json",
        "x-session-token": config["token"],
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
    }

    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(ThreadPoolExecutor(), lambda: requests.get(API_URL, headers=HEADERS))

    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Failed to fetch user info: {response.status_code}\nResponse: {response.text}")
        return None

class Client(revolt.Client):
    def __init__(self, session, token):
        super().__init__(session, token)
        self.config = load_config()
        self.prefix = self.config["prefix"]
        self.commands = self.config["commands"]

    async def on_ready(self):
        logger.info(f"Logged in as {self.user.name}, ID: {self.user.id}")
        logger.info(f"Using command prefix: {self.prefix}")
        
        # SKID FONT ART BUT DONT HAVE SOMETHING BETTER
        
        print("""
              

██████╗░███████╗██╗░░░██╗░█████╗░██╗░░░░░████████╗
██╔══██╗██╔════╝██║░░░██║██╔══██╗██║░░░░░╚══██╔══╝
██████╔╝█████╗░░╚██╗░██╔╝██║░░██║██║░░░░░░░░██║░░░
██╔══██╗██╔══╝░░░╚████╔╝░██║░░██║██║░░░░░░░░██║░░░
██║░░██║███████╗░░╚██╔╝░░╚█████╔╝███████╗░░░██║░░░
╚═╝░░╚═╝╚══════╝░░░╚═╝░░░░╚════╝░╚══════╝░░░╚═╝░░░

░██████╗███████╗██╗░░░░░███████╗██████╗░░█████╗░████████╗
██╔════╝██╔════╝██║░░░░░██╔════╝██╔══██╗██╔══██╗╚══██╔══╝
╚█████╗░█████╗░░██║░░░░░█████╗░░██████╦╝██║░░██║░░░██║░░░
░╚═══██╗██╔══╝░░██║░░░░░██╔══╝░░██╔══██╗██║░░██║░░░██║░░░
██████╔╝███████╗███████╗██║░░░░░██████╦╝╚█████╔╝░░░██║░░░
╚═════╝░╚══════╝╚══════╝╚═╝░░░░░╚═════╝░░╚════╝░░░░╚═╝░░░
""")
        print(f"Prefix used for commands: '{self.prefix}' for example '{self.prefix}help'\nLogged in as user: {self.user.name} ({self.user.id})")

    async def on_message(self, message: revolt.Message):
        if message.author.id != self.user.id:
            return

        content = message.content.strip()
        if content.startswith(self.prefix):
            parts = content[len(self.prefix):].strip().split()
            command = parts[0]

            if command == "userinfo" and len(parts) > 1:
                user_id = parts[1].strip('<@>')
                user_data = await fetch_user_bio(user_id)
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
                    


                    await send_revolt_message_with_session(message.channel.id, "", embed)
                else:
                    await message.channel.send("Failed to fetch user info.")

            elif command == "help":
                commands_text = "\n".join([f"**{cmd}**: {desc}" for cmd, desc in self.commands.items()])
                embed = {
                    "type": "Website",
                    "title": "Revolt.chat Selfbot - Bot Help",
                    "description": f"Here are the available commands:\n\n{commands_text}",
                    "colour": "#ff5733"
                }

                result = await send_revolt_message_with_session(
                    message.channel.id,
                    "Here's the help information:",
                    embed
                )

                if not result:
                    await message.channel.send("Failed to display help. Check logs for details.")

            elif command == "hello":
                await message.channel.send("Hello there! 👋")
            else:
                await message.channel.send(f"Unknown command: {command}")

async def main():
    config = load_config()
    TOKEN = config["token"]

    if TOKEN == "YOUR_TOKEN_HERE":
        logger.error("Please edit config.json and set your token")
        return

    try:
        async with revolt.utils.client_session() as session:
            client = Client(session, TOKEN)
            await client.start()
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
