import os
import discord
import requests
import asyncio
import configparser
import datetime
from xml.etree import ElementTree


class Post:
    title = ""
    author = ""
    link = ""
    preview = ""
    date = ""

    def message(self):
        return MESSAGE_FORMAT.format(
                   self.title,
                   self.author,
                   self.link,
                   self.preview
               )

    def date_as_datetime(self):
        return datetime.datetime.strptime(self.date, "%a, %d %b %Y %H:%M:%S %Z")


client = discord.Client()
channel = None
config = None
last_time = None

BOT_TOKEN = None
CHANNEL_ID = None
UPDATE_FREQUENCY = None
RSS_FEED_URL = None
MULTI_POST = True
MESSAGE_FORMAT = "`New Forum Post`\n" \
               "**{0}** _by {1}_\n" \
               "**Link:** {2}\n" \
               "**Preview:**\n" \
               "{3}\n" \
               "--------"

ERROR_COLOUR = "\033[91m"


def safe_print(s):
    try:
        print(s)
    except UnicodeEncodeError:
        for c in s:
            try:
                print(c)
            except UnicodeEncodeError:
                print("?")


def item_to_post(item):
    post = Post()
    for child in item:
        if child.tag == "title":
            post.title = child.text
        elif "creator" in child.tag:
            post.author = child.text
        elif child.tag == "description":
            post.preview = child.text
        elif child.tag == "link":
            post.link = child.text
        elif child.tag == "pubDate":
            post.date = child.text
    return post


@asyncio.coroutine
def make_discord_post(post):
    try:
        yield from client.send_message(channel, post.message())
        print("Sending message:")
        safe_print(post.message())
        print("\n---------------\n")
    except discord.errors.Forbidden:
        print(ERROR_COLOUR)
        print("Your bot doesn't have permission to send messages!")
        print("Please ensure you authorised the bot correctly, and check that it is in a role on your "
              "server/channel that allows it to send messages.")


@asyncio.coroutine
def single_post(items):
    global last_time

    for item in items:
        new_post = item_to_post(item)

        post_time = new_post.date_as_datetime()
        if post_time > last_time:
            yield from make_discord_post(new_post)
            last_time = post_time
            return


@asyncio.coroutine
def multi_post(items):
    global last_time

    to_post = []    # type: list[Post]

    if not last_time:
        to_post.append(item_to_post(items[0]))
    else:
        for item in items:
            new_post = item_to_post(item)
            post_time = new_post.date_as_datetime()

            if post_time > last_time:
                to_post.append(new_post)
            else:
                break

    if to_post:
        to_post.reverse()
        for post in to_post:
            yield from make_discord_post(post)

        last_time = to_post[-1].date_as_datetime()


@asyncio.coroutine
def check_posts():
    global client
    global channel

    try:
        r = requests.get(RSS_FEED_URL)
    except requests.ConnectionError:
        print(ERROR_COLOUR)
        safe_print("Failed to connect to: {0}".format(RSS_FEED_URL))
        print("Please check the the rss_feed_url provided in config.ini to ensure it is correct.")
        return

    items = ElementTree.fromstring(r.content)[0].findall("item")

    if not MULTI_POST:
        yield from single_post(items)
    else:
        yield from multi_post(items)


@client.event
@asyncio.coroutine
def on_ready():
    global channel

    channel = client.get_channel(CHANNEL_ID)

    if not channel:
        print(ERROR_COLOUR)
        safe_print("Cannot find a channel with channel ID: {0}".format(CHANNEL_ID))
        print("Please check the the channel_id provided in config.ini to ensure it is correct.")
        print("Also ensure your bot has been added to the server correctly,"
              " you should be able to see them in the members list.")
        return

    print("vBulletin Update Bot Running!")
    safe_print("On Server: {0}\n" 
               "In Channel: {1}\n" 
               "Querying URL: {2}\n" 
               "Can send messages? {3}"
               .format(channel.server,
                       channel.name,
                       RSS_FEED_URL,
                       channel.permissions_for(channel.server.me).send_messages))

    while True:
        yield from check_posts()
        yield from asyncio.sleep(UPDATE_FREQUENCY)


if __name__ == "__main__":
    config = configparser.ConfigParser()

    try:
        if os.path.isfile("config.override.ini"):
            config.read("config.override.ini")
        elif os.path.isfile("config.ini"):
            config.read("config.ini")
        else:
            print(ERROR_COLOUR)
            print("No config.ini found!")
            exit(-1)
    except configparser.ParsingError:
        print(ERROR_COLOUR)
        print("Error reading config.ini")
        print("If you have a multi-line message make sure there are tabs before each new line!")
        exit(-1)

    options = config.options("Options")

    if "bot_token" in options:
        BOT_TOKEN = config.get("Options", "bot_token")
    else:
        print("No bot_token defined in config.ini")
        exit(-1)

    if "channel_id" in options:
        CHANNEL_ID = config.get("Options", "channel_id")
    else:
        print("No channel_id defined in config.ini")
        exit(-1)

    if "update_frequency" in options:
        UPDATE_FREQUENCY = config.getfloat("Options", "update_frequency")
    else:
        print("No update_frequency defined in config.ini")
        exit(-1)

    if "rss_feed_url" in options:
        RSS_FEED_URL = config.get("Options", "rss_feed_url")
    else:
        print("No rss_feed_url defined in config.ini")
        exit(-1)

    if "message_format" in options:
        MESSAGE_FORMAT = config.get("Options", "message_format")
        MESSAGE_FORMAT = MESSAGE_FORMAT.replace("{post_title}", "{0}")
        MESSAGE_FORMAT = MESSAGE_FORMAT.replace("{post_author}", "{1}")
        MESSAGE_FORMAT = MESSAGE_FORMAT.replace("{post_link}", "{2}")
        MESSAGE_FORMAT = MESSAGE_FORMAT.replace("{post_preview}", "{3}")

    if "multi_post" in options:
        MULTI_POST = config.get("Options", "multi_post").lower() == "true"

    try:
        client.run(BOT_TOKEN)
    except discord.errors.LoginFailure:
        print(ERROR_COLOUR)
        print("Invalid bot token provided!")
        print("Please check the bot_token provided in config.ini to ensure it is correct.")
        exit(-1)
