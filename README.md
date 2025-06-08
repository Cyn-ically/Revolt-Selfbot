# Revolt Selfbot

full recode without using idiotic revolt.py library

A proof-of-concept (POC) selfbot for [Revolt](https://revolt.chat) Revolt.chat, demonstrating how to interact with the API using Python.

## Features
- Basic command handling with a configurable prefix
- Fetch user information using `userinfo` command
- Send messages and embeds
- Configurable settings via `config.json`
- Logging for debugging
- Auto name changer (Change name by modifying usernames.txt)

## Requirements
- Python 3.8+
- `aiohttp`, `requests`, and `revolt` Python modules

## Installation
1. Clone the repository:
   ```sh
   git clone https://github.com/cyn-ically/Revolt-Selfbot/Revolt-Selfbot.git
   cd Revolt-Selfbot
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Create a `config.json` file (it will be generated automatically on first run if missing):
   ```json
   {
       "token": "YOUR_TOKEN_HERE",
       "prefix": "!",
       "commands": {
           "help": "Show this help message",
           "hello": "Get a greeting from the bot"
           "userinfo": "Fetch user info"
       }
   }
   ```
4. Edit `config.json` and replace `YOUR_TOKEN_HERE` with your Revolt session token.

## Usage
Run the bot using:
```sh
python main.py
```

### Commands
| Command    | Description |
|------------|------------|
| `!help`    | Displays available commands |
| `!hello`   | Responds with a greeting |
| `!userinfo <user_id>` | Fetches user info |
| `!username <new_name>` | Change your username |

## Example
Send the `!userinfo` command any chat:
```sh
!userinfo @theuser
```
The bot will respond with user details if available.
# How to Get Your Revolt Session Token 

<details>
<summary><strong>Click to view the steps for obtaining your Revolt session token</strong></summary>
   
# Tutorial
- To run the Revolt Selfbot, you'll need your x-session-token, which can be obtained from the network requests in your browser. Follow these steps carefully:


## Step 1: Open Revolt in Your Browser
1. Go to Revolt and log in to your account.
2. Open Developer Tools:
- Google Chrome / Edge: Press F12 or Ctrl + Shift + I
- Firefox: Press F12 or Ctrl + Shift + I
## Step 2: Start a New Application Session

1. Click on the "Network" tab in Developer Tools.
2. Make sure the filter is set to "Fetch/XHR" (in Chrome) or "XHR" in Firefox.
3. If the network log is empty, refresh the page (F5) to populate it with requests.
   
## Step 3: Send a Message
1. Open any DM or server channel.
2. Type a message and send it.
- Look for a request named "messages" in the Network tab.
3. Step 4: Find Your Token
- Click on the "messages" request.
- Navigate to the "Headers" tab.
- Scroll down to the Request Headers section.
- Locate the x-session-token field.
- Copy the token value (a long alphanumeric string).

</details>

## Disclaimer
This selfbot is for educational purposes only. Usage of selfbots may violate Revolt's Terms of Service. Use at your own risk.

## License
Apache 2.0 License
