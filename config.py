'''
------------------------------------------------------
    .d8888b.                                      888    888      d8b
    d88P  Y88b                                    888    888      Y8P
    Y88b.                                         888    888
    "Y888b.    88888b.d88b.    .d88b.   .d88b.  888888 88888b.   888  .d88b.
       "Y88b.  888 "888 "88b  d88""88b d88""88b  888    888 "88b 888 d8P  Y8b
         "888  888  888   888 888  888 888  888  888    888  888 888 88888888
    Y88b  d88P 888  888   888 Y88..88P Y88..88P  Y88b.  888  888 888 Y8b.
    "Y8888P"   888  888   888  "Y88P"   "Y88P"   "Y888  888  888 888  "Y8888

    Developer: Nattugle 
    2022 / 2023
-------------------------------------------------------
'''

from dotenv import load_dotenv
from os import getenv
load_dotenv()

# BOT DETAILS
BOT_SHARDS = int(getenv("BOT_SHARDS"))
BOT_TOKEN = getenv("BOT_TOKEN")
BOT_PREFIX = "!"

# HEALTH CHECK - USE "True" FOR DIGITAL OCEAN APP PLATFORM ONLY. OTHERWISE "False"
FAKE_HEALTH_CHECK = False
if getenv("FAKE_HEALTH_CHECK") == "true":
    FAKE_HEALTH_CHECK = True

# BOT COLORS
COLOR_SMOOTHIE = 0xF65775
COLOR_BETA = 0x00B3AA
COLOR_ACCEPTED = 0x81A554
COLOR_ERROR = 0xE4192E
COLOR_EMPTY = 0x2F3136
COLOR_RED = 0xff4136
COLOR_ORANGE = 0xff9b00
COLOR_YELLOW = 0xffd800
COLOR_GREEN = 0x32b74d
COLOR_BLUE = 0x00a1ff
COLOR_PURPLE = 0xce50f9

# DATABASE DETAILS
DB_USERNAME = getenv("DB_USERNAME")
DB_PASSWORD = getenv("DB_PASSWORD")
DB_SERVER = getenv("DB_SERVER")
DB_NAME = getenv("DB_NAME")

# TOP.GG DETAILS
WEBHOOK_TOKEN = getenv("WEBHOOK_TOKEN")
WEBHOOK_PASSWORD = getenv("WEBHOOK_PASSWORD")
WEBHOOK_PORT = getenv("WEBHOOK_PORT")

# REDDIT DETAILS
REDDIT_CLIENT_ID = getenv("REDDIT_CLIENT_ID")
REDDIT_SECRET_KEY = getenv("REDDIT_SECRET_KEY")
REDDIT_PASSWORD = getenv("REDDIT_PASSWORD")

# GIVEAWAYS
GIVEAWAY_EXPIRE = 259200
GIVEAWAY_MAX_LENGTH = 3628800
GIVEAWAY_ACTIVE_USER_LIMIT = 50

BOT_INVITE_LINK = "https://discord.com/api/oauth2/authorize?client_id=955120977027690536&permissions=52213883725302&scope=bot%20applications.commands"
SERVER_INVITE_LINK = "https://discord.com/invite/WB7qT8dQJc"
TERMS_OF_SERVICE = "https://docs.google.com/document/d/1-bv3zOdSNI8J-u0qiN0FABYst9lzAb4vE7ADL0MoDPg/edit?usp=sharing"
