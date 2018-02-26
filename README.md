# DS3Club-Discord-Bot

Gets updates from ds3club.com and posts them in a discord channel

## Getting Started

This project is Python 3.6, and uses pipenv.

Python 3: http://bfy.tw/GojO
Pipenv: http://bfy.tw/GojW

Make sure you have both installed and then run:

`pipenv install --three
pipenv shell
python ds3-forum-discord-bot.py`

Off you go!

## Setup

Get a bot token and a channel ID by following the instructions found at: https://github.com/Chikachi/DiscordIntegration/wiki/How-to-get-a-token-and-channel-ID-for-Discord

Alter the [config.json](config.json) file to include this bot token and channel id.

eg.

```buildoutcfg
{
  "bot_token": "some.token.fromDiscord",
  "channel_id": "1234567890",
  "update_frequency": "60"
}
```

You can change `update_frequency` to change how often the forum is polled, this value is in seconds.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.