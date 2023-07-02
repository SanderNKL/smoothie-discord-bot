import config as config
from database import Database
import re
import requests
from requests.auth import HTTPBasicAuth
import random
import discord
from os import getenv

db = Database()

def button_color(
    input_color
):
    """
    Returns the button color for (green, red, blue, gray)
    """

    color = discord.ButtonStyle.gray

    if input_color.lower() == "green":
        color = discord.ButtonStyle.green

    elif input_color.lower() == "red":
        color = discord.ButtonStyle.red

    elif input_color.lower() == "blue":
        color = discord.ButtonStyle.blurple

    return color

def user_avatar(user: discord.User):
    if user.avatar:
        return user.avatar.url

    else:
        return "https://i.imgur.com/GGcIgAS.png"


async def user_invites(user: discord.User, guild: discord.Guild):
    search = db.invites.find({
        "guild_id": str(guild.id),
        "user_id": str(user.id)
    })

    logged_invites = await search.to_list(length=100)

    joins = 0
    leaves = 0
    fakes = 0

    for invite in logged_invites:
        for user in invite["joins"]:
            if invite["joins"][user]["fake"]:
                fakes += 1

        joins += len(invite["joins"])
        leaves += len(invite["leaves"])

    return {"joins": joins, "leaves": leaves, "fake": fakes}


async def user_messages(user: discord.User, guild: discord.Guild):
    user_id = str(user.id)
    guild_id = str(guild.id)
    user_data = await db.user_messages.find_one({"user_id": user_id})

    if user_data is None or guild_id not in user_data['guilds']:
        return 0

    else:
        return user_data['guilds'][guild_id]


def reddit_connection():
    """
    Connects to reddit and returns a header with token
    """

    headers = {
        'User-Agent': 'Smoothiebot'
    }

    data = {
        'grant_type': 'password',
        'username': 'UltimateRPG',
        'password': getenv("REDDIT_PASSWORD")
    }

    res = requests.post(
        'https://www.reddit.com/api/v1/access_token',
        auth=HTTPBasicAuth(getenv("REDDIT_CLIENT_ID"), getenv("REDDIT_SECRET_KEY")),
        data=data,
        headers=headers
    )

    headers = {**headers, **{'Authorization': f'bearer {res.json()["access_token"]}'}}
    return headers


def reddit_posts(subreddits: list, headers=None):
    if not headers:
        headers = reddit_connection()

    fit_posts = []
    categories = ['hot', 'top']
    for category in categories:
        for subreddit in subreddits:
            response = requests.get(f'https://oauth.reddit.com/r/{subreddit}/{category}', headers=headers)
            for post in response.json()['data']['children']:
                if not post['data']['is_video'] and not post['data']['over_18'] and post['data']['url']:
                    if "jpg" not in post['data']['url'] and "png" not in post['data']['url']:
                        continue

                    fit_posts.append(
                        {
                            'title': post['data']['title'],
                            'text':  post['data']['selftext'],
                            'image_url': post['data']['url'],
                            # 'author': post['data']['author'],
                            # 'upvotes': post['data']['ups'],
                            'permalink': post['data']['permalink']
                        }
                    )

    return fit_posts


def random_reddit_post(fit_posts):
    if len(fit_posts) < 1:
        post = {
            'data': {
                'title': 'Only doggo was found!',
                'selftext':  'It may just be no posts fit my criteria today... Have a dog instead!',
                'image_url': "https://i.kym-cdn.com/entries/icons/original/000/014/959/Screenshot_116.png",
                'author': 'Smoothie',
                'upvotes': 0,
                'permalink': 'none...'
            }
        }

    else:
        post = random.choice(fit_posts)

    return post


async def embed_color(user_id):
    user_id = str(user_id)

    player_color = await db.color_data.find_one({"_user_id": user_id})
    COLORS = {
        "smoothie": config.COLOR_SMOOTHIE,
        "beta": config.COLOR_BETA,
        "empty": config.COLOR_EMPTY,
        "red": config.COLOR_RED,
        "orange": config.COLOR_ORANGE,
        "yellow": config.COLOR_YELLOW,
        "blue": config.COLOR_BLUE,
        "purple": config.COLOR_PURPLE
    }

    if player_color is None:
        return config.COLOR_SMOOTHIE

    elif player_color['color'] is None:
        return config.COLOR_SMOOTHIE

    elif player_color['color'] in COLORS:
        color = COLORS[player_color['color']]

    else:
        color = player_color['color']

    return color


def determined_time(input):
    time = 0  # Seconds

    # Seconds
    placeholders = {
        "year": {
            "seconds": 31556926,
            "search": re.search(r"(\d+)(y|year|years)", input)
        },
        "month": {
            "seconds": 604800,
            "search": re.search(r"(\d+)(month|months)", input)
        },
        "weeks": {
            "seconds": 604800,
            "search": re.search(r"(\d+)(w|week|weeks)", input)
        },
        "days": {
            "seconds": 86400,
            "search": re.search(r"(\d+)(d|day|days)", input)
        },
        "hours": {
            "seconds": 3600,
            "search": re.search(r"(\d+)(h|hour|hours)", input)
        },
        "minutes": {
            "seconds": 60,
            "search": re.search(r"(\d+)(m|minute|minutes)", input)
        },
        "seconds": {
            "seconds": 1,
            "search": re.search(r"(\d+)(s|second|seconds)", input)
        }
    }

    for placeholder in placeholders:
        if placeholders[placeholder]["search"] is not None:
            number = placeholders[placeholder]["search"].group(1)

            # Check if day
            if number.isdigit():
                time += int(number) * placeholders[placeholder]["seconds"]

            else:
                print("Failed to aquire number from determine_time:", placeholder.group(1))

    return time
