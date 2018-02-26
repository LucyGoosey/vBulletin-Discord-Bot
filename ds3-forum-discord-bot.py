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

    def message(self):
        return "`New Post on DS3Club.co.uk`\n" \
               "**{0}** _by_ {1}\n" \
               "**Link:**\n" \
               "{2}\n" \
               "**Preview:**\n" \
               "{3}\n" \
               .format(
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
        return equal


client = discord.Client()
channel = None
config = None
last_post = Post()

BOT_TOKEN = None
CHANNEL_ID = None
UPDATE_FREQUENCY = None


async def check_posts():
    global client
    global channel
    global last_post

    r = requests.get("http://www.ds3club.co.uk/external?type=rss2&nodeid=2")
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

    if last_post != new_post:
        await client.send_message(channel, new_post.message())
        last_post = new_post


@client.event
async def on_ready():
    global channel
    channel = client.get_channel(CHANNEL_ID)

    print("DS3club Update Bot Running!")
    print("On Server: {0}\n"
          "In Channel: {1}\n"
          "Can send messages? {2}"
          .format(channel.server, channel.name, channel.permissions_for(channel.server.me).send_messages))

    while True:
        await check_posts()
        await asyncio.sleep(UPDATE_FREQUENCY)


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

    client.run(BOT_TOKEN)
