# Revolt Selfbot POC

A proof-of-concept (POC) selfbot for [Revolt](https://revolt.chat), demonstrating how to interact with the API using Python.

## Features
- Basic command handling with a configurable prefix
- Fetch user information using `userinfo` command
- Send messages and embeds
- Configurable settings via `config.json`
- Logging for debugging

## Requirements
- Python 3.8+
- `aiohttp`, `requests`, and `revolt` Python modules

## Installation
1. Clone the repository:
   ```sh
   git clone https://github.com/Ramona-Flower/Revolt-Selfbot/Revolt-Selfbot.git
   cd revolt-selfbot-poc
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

## Example
Send the `!userinfo` command:
```sh
!userinfo @theuser
```
The bot will respond with user details if available.

## Disclaimer
This selfbot is for educational purposes only. Usage of selfbots may violate Revolt's Terms of Service. Use at your own risk.

## License
Apache 2.0 License
