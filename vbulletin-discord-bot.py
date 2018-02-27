import discord
import requests
import asyncio
import json
from xml.etree import ElementTree


class Post:
    title = ""
    author = ""
    link = ""
    preview = ""
    date = ""

    def message(self):
        return "`New Post on {0}`\n" \
               "**{1}** _by {2}_\n" \
               "**Link:**\n" \
               "{3}\n" \
               "**Preview:**\n" \
               "{4}\n" \
               .format(
                   FORUM_NAME,
                   self.title,
                   self.author,
                   self.link,
                   self.preview
               )

    def __eq__(self, other):
        equal = self.title == other.title
        equal &= self.author == other.author
        equal &= self.link == other.link
        equal &= self.preview == other.preview
        equal &= self.date == other.date
        return equal


client = discord.Client()
channel = None
config = None
last_post = Post()

BOT_TOKEN = None
CHANNEL_ID = None
UPDATE_FREQUENCY = None
RSS_FEED_URL = None
FORUM_NAME = ""

ERROR_COLOUR = "\033[91m"


@asyncio.coroutine
def check_posts():
    global client
    global channel
    global last_post

    try:
        r = requests.get(RSS_FEED_URL)
    except requests.ConnectionError:
        print(ERROR_COLOUR)
        print("Failed to connect to: {0}".format(RSS_FEED_URL))
        print("Please check the the rss_feed_url provided in config.json to ensure it is correct.")
        return

    newest_item = ElementTree.fromstring(r.content)[0].find("item")

    new_post = Post()
    for child in newest_item:
        if child.tag == "title":
            new_post.title = child.text
        elif "creator" in child.tag:
            new_post.author = child.text
        elif child.tag == "description":
            new_post.preview = child.text
        elif child.tag == "link":
            new_post.link = child.text
        elif child.tag == "pubDate":
            new_post.date = child.text

    if last_post != new_post:
        try:
            yield from client.send_message(channel, new_post.message())
            print("Sending message:")
            print(new_post.message())
            print("---------------")
        except discord.errors.Forbidden:
            print(ERROR_COLOUR)
            print("Your bot doesn't have permission to send messages!")
            print("Please ensure you authorised the bot correctly, and check that it is in a role on your "
                  "server/channel that allows it to send messages.")
            return

        last_post = new_post


@client.event
@asyncio.coroutine
def on_ready():
    global channel

    channel = client.get_channel(CHANNEL_ID)

    if not channel:
        print(ERROR_COLOUR)
        print("Cannot find a channel with channel ID: {0}".format(CHANNEL_ID))
        print("Please check the the channel_id provided in config.json to ensure it is correct.")
        print("Also ensure your bot has been added to the server correctly,"
              " you should be able to see them in the members list.")
        return

    print("vBulletin Update Bot Running!")
    print("On Server: {0}\n" 
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
    with open('config.json') as cfg:
        config = json.load(cfg)

    if "bot_token" in config.keys():
        BOT_TOKEN = config["bot_token"]
    else:
        print("No bot_token defined in config.json")
        exit(-1)

    if "channel_id" in config.keys():
        CHANNEL_ID = config["channel_id"]
    else:
        print("No channel_id defined in config.json")
        exit(-1)

    if "update_frequency" in config.keys():
        UPDATE_FREQUENCY = float(config["update_frequency"])
    else:
        print("No update_frequency defined in config.json")
        exit(-1)

    if "rss_feed_url" in config.keys():
        RSS_FEED_URL = config["rss_feed_url"]
    else:
        print("No rss_feed_url defined in config.json")
        exit(-1)

    if "forum_name" in config.keys():
        FORUM_NAME = config["forum_name"]
    else:
        print("No forum_name defined in config.json")
        exit(-1)

    try:
        client.run(BOT_TOKEN)
    except discord.errors.LoginFailure:
        print(ERROR_COLOUR)
        print("Invalid bot token provided!")
        print("Please check the bot_token provided in config.json to ensure it is correct.")
        exit(-1)
