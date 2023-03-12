import configparser
import json

configParser = configparser.RawConfigParser()
configFilePath = r'config.ini'
configParser.read(configFilePath)

API_KEY = configParser.get('hypixel', 'api_key')
DISCORD_API_KEY = configParser.get('discord', 'api_key')
MAX_CAKE_YEAR = configParser.getint('hypixel', 'max_cake_year')
SLADA_UUID = "ec8d8033fbd148419817dc29227ed555" # TEST UUID

ALLOWED_CHANNEL_IDS = json.loads(configParser.get("discord","allowed_channel_ids"))
COMMAND_PREFIX = configParser.get('discord', 'command_prefix')