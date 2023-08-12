import configparser
import json
import logging

configParser = configparser.RawConfigParser()
configFilePath = r'config.ini'
configParser.read(configFilePath)

API_KEY = configParser.get('hypixel', 'api_key')
DISCORD_API_KEY = configParser.get('discord', 'api_key')
MAX_CAKE_YEAR = configParser.getint('hypixel', 'max_cake_year')
SLADA_UUID = "ec8d8033fbd148419817dc29227ed555" # TEST UUID

ALLOWED_CHANNEL_IDS = json.loads(configParser.get("discord", "allowed_channel_ids"))

# Log config values
log_level_mapping = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
}
config_value_log_level = configParser['logs']['log_level'].upper()
LOG_LEVEL = log_level_mapping.get(config_value_log_level)
LOG_MAX_SIZE = configParser.getint('logs', 'max_log_size')
LOG_MAX_FILES = configParser.getint('logs', 'backup_count')
