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

# About This Project
## What is Smoothie?
Smoothie is a Discord moderation, utility and game bot created to
make discord servers more fun and easier to manage.
This repository hosts only it's moderation and utility features.

## Why is Smoothie's utilities open source?
We believe that server management should be free and easily available.
Discord has not made these features themselves so we have sought out to
help users do all of this for free!

## How does Smoothie make money?
Smoothie makes money from game subscriptions that are only available in the
main bot. These features have therefore not been included into this repository.

## Contributing to the project
We allow people to contribute to the project.
Contributions made in here will be added to the official Smoothie bot.
If you don't want to host your own bot, this is a great way to get the
features/improvements/fixes you need into the bot.

# Getting Started
## Setting up the bot
1. Create a .env file
2. Put the following in to the .env file:
    ```
    # BOT DETAILS
    BOT_SHARDS = "1"
    BOT_TOKEN = "YOUR-BOT-TOKEN"

    # DATABASE DETAILS
    DB_USERNAME = "YOUR-DATABASE-USERNAMe"
    DB_PASSWORD = "YOUR-DATABASE-PASSWORD"
    DB_SERVER = "YOUR-DATABASE-SERVER"
    DB_NAME = "YOUR-DATABASE-NAME"

    # DIGITAL OCEAN - Leave this to false if you do not use it's app platform.
    FAKE_HEALTH_CHECK = "false"

    # REDDIT DETAILS
    REDDIT_CLIENT_ID = "YOUR-REDDIT-CLIENT-ID"
    REDDIT_SECRET_KEY = "YOUR-REDDIT-SECRET-KEY"
    REDDIT_PASSWORD = "YOUR-REDDIT-PASSWORD"
    ```

## Creating a database
1. Create a MongoDB Database: https://www.mongodb.com/basics/create-database
2. Enter the database details into the .env file

## Creating a reddit bot
1. Create a reddit API account and add them to the .env

## Boot up the bot!
It's time to add your discord bot token to the .env file, and select how many shards you want.
If your bot is not in over 1.000 servers, you don't need to worry about this. Leave it at 1.