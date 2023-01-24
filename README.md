# discord-qBit
A discord bot that allows you to control your hosted qBittorrent client from Discord.

## Features
- Get the status of your qBittorrent client including the list of torrents, their names, uploaded, downloaded and their state.
- Search for specific torrents by name, or list the latest/oldest torrents.
- Add new torrents to your qBittorrent client by providing the torrent magnet link or .torrent file.
- Remove specific torrents from your qBittorrent client.

## Requirements
- A hosted qBittorrent client with the WebUI enabled.
- Python 3.6+
- Discord Bot Token (https://discordpy.readthedocs.io/en/stable/discord.html#discord-intro)
### Libraries
- qBittorrent-api (https://pypi.org/project/qbittorrent-api/)
- Discord.py (https://pypi.org/project/discord.py/)

## Usage
- Fill in respective credentials in `creds.example.py` file and rename to `creds.py`
- Start the bot using `python seedbox.py`

## Commands
- !status all - Lists all torrents along with their names, uploaded, downloaded and state.
- !status latest - Lists the latest added torrent along with its name, uploaded, downloaded and state.
- !status oldest - Lists the oldest added torrent along with its name, uploaded, downloaded and state.
- !status <number> - Lists the latest <number> added torrents along with their names, uploaded, downloaded and state.
- !status <name> - Lists all torrents with the name <name> along with their names, uploaded, downloaded and state.
- !add <magnet_link/torrent_file> - Adds a new torrent to the qBittorrent client using the provided magnet_link or torrent_file.
- !remove <name> - Removes the torrent with the name <name> from the qBittorrent client.
- !clear - Clears the channel
- !ping <qb|bot> - Check the latency of your qBit server & bot

## Note
- Be sure to keep your qBittorrent WebUI URL, username and password secure.
- Make sure the bot has permissions to send messages, read message history and add reactions in the channel where you want to use the bot.
- The bot uses the confirm_removal() function to confirm the removal of the torrents which is explained in the code, you can modify it to your liking.
