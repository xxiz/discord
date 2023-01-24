"""
This is a Discord bot that allows you to control your hosted qBittorrent client from Discord.
"""

import discord
from discord.ext import commands
from qbittorrent import Client
import requests
import asyncio
from creds import *
import re
import requests
from datetime import datetime

qb = Client(CLIENT_URL)
qb.login(CLIENT_USER, CLIENT_PASS)

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
bot.remove_command('help')


async def get_sorted_by_date(t):
    t.sort(key=lambda x: x['added_on'])
    return t


async def get_all_categories():
    categories = []
    for torrent in qb.torrents():
        if torrent['category'] not in categories:
            categories.append(torrent['category'])
    return categories


@bot.event
async def confirm_removal(ctx, message):
    await message.add_reaction('✅')
    await message.add_reaction('❌')

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ['✅', '❌']

    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)
    except asyncio.TimeoutError:
        await message.edit(content='Timeout, Aborted')
        await message.clear_reactions()
        return False

    if str(reaction.emoji) == '✅':
        await message.clear_reactions()
        return True
    else:
        await message.clear_reactions()
        return False


@bot.command()
async def status(ctx, args: str = None):
    if ctx.channel.id == CHANNEL_ID and ctx.author.id == OWNER_ID and ctx.author.id == OWNER_ID:
        message = await ctx.send('Getting Status...')

        try:
            if args == None:
                torrents = qb.torrents()

                for torrent in torrents:
                    if torrent['state'] == 'stalledUP':
                        torrent['state'] = 'Seeding'
                    elif torrent['state'] == 'stalledDL':
                        torrent['state'] = 'Downloading'
                    elif torrent['state'] == 'pausedUP' or torrent['state'] == 'pausedDL':
                        torrent['state'] = 'Paused'
                    
                await message.edit(content=f"```Torrents: {len(torrents)} \nSeeding: {len([torrent for torrent in torrents if torrent['state'] == 'Seeding'])} \nDownloading: {len([torrent for torrent in torrents if torrent['state'] == 'Downloading'])} \nPaused: {len([torrent for torrent in torrents if torrent['state'] == 'Paused'])}```")
                return

            if args == 'all':
                await message.edit(content=f'Are you sure you want to list all torrents? (NOTE: This may take a while)')
                confirm = await confirm_removal(ctx, message)
                if confirm:
                    torrents = qb.torrents()
                    await message.edit(content=f"Listing {len(torrents)} torrents...")

                    for torrent in torrents:
                        await ctx.send(f"```{torrent['name']} ({round(torrent['uploaded'] / 1000000000, 2)} GB, {round(torrent['downloaded'] / 1000000000, 2)} GB) - {torrent['state']}```")

                    await message.edit(content=f"Listed {len(torrents)} torrents")
                else:
                    await message.edit(content='User aborted, torrents not listed')

            elif args == 'latest':
                torrents = qb.torrents()
                torrents = await get_sorted_by_date(torrents)
                await message.edit(content=f"```Added on: {datetime.fromtimestamp(torrents[-1]['added_on']).strftime('%Y-%m-%d %H:%M:%S')} \n{torrents[-1]['name']} ({round(torrents[-1]['uploaded'] / 1000000000, 2)} GB, {round(torrents[-1]['downloaded'] / 1000000000, 2)} GB) - {torrents[-1]['state']}```")
            elif args == 'oldest':
                torrents = qb.torrents()
                torrents = await get_sorted_by_date(torrents)
                await message.edit(content=f"```Added on: {datetime.fromtimestamp(torrents[0]['added_on']).strftime('%Y-%m-%d %H:%M:%S')} \n{torrents[0]['name']} ({round(torrents[0]['uploaded'] / 1000000000, 2)} GB, {round(torrents[0]['downloaded'] / 1000000000, 2)} GB) - {torrents[0]['state']}```")

            elif args.isdigit():
                torrents = qb.torrents()
                if int(args) > len(torrents) or int(args) < 1:
                    await message.edit(content='Abort: You only have ' + str(len(torrents)) + ' torrents.')
                    return
                await message.edit(content=f"Listing {args} torrents...")
                for torrent in torrents[-int(args):]:
                    await ctx.send(f"`{torrent['name']} ({round(torrent['uploaded'] / 1000000000, 2)} GB, {round(torrent['downloaded'] / 1000000000, 2)} GB) - {torrent['state']}`")
                await message.edit(content=f"Listed {args} torrents")

            else:
                x = 0
                for torrent in qb.torrents():
                    if str(args).lower() in torrent['name'].lower():
                        x += 1
                        await message.edit(content=f"Found {x} matching torrents")
                        await ctx.send(f"```{torrent['name']} ({round(torrent['uploaded'] / 1000000000, 2)} GB, {round(torrent['downloaded'] / 1000000000, 2)} GB) - {torrent['state']}```")
                if x == 0:
                    await message.edit(content='```No matching torrents found```')
        except Exception as e:
            await message.edit(content='```Error: ' + str(e) + '```')


@bot.command()
async def add(ctx, args: str = None):
    if ctx.channel.id == CHANNEL_ID and ctx.author.id == OWNER_ID:
        message = await ctx.send('Adding Torrent...')
        type = ''

        if args == None:
            await message.edit(content='```Error: no torrent provided```')
            return

        if 'magnet:' in args:
            type = 'magnet'
        elif 'http' in args:
            type = 'url'
        elif ctx.message.attachments:
            if ctx.message.attachments[0].filename[-8:] == '.torrent':
                type = 'attachment'
            else:
                await message.edit(content='```Error: attachment must be a .torrent file```')
                return
        else:
            await message.edit(content='```Error: no torrent provided```')
            return

        try:
            if type == 'attachment':
                await message.edit(content='Detected attachment, adding torrent...')
                attachment_url = ctx.message.attachments[0].url
                file_request = requests.get(attachment_url)
                qb.download_from_file(file_request.content, category='Public')
                torrents = await get_sorted_by_date(qb.torrents())
                torrent_name = torrents[-1]['name']
                await message.edit(content=f"Added torrent: `{torrent_name}`")

            elif type == 'magnet':
                await message.edit(content='Detected magnet, adding torrent...')
                qb.download_from_link(args, category='Public')
                torrents = await get_sorted_by_date(qb.torrents())
                torrent_name = torrents[-1]['name']
                await message.edit(content=f"Added torrent: `{torrent_name}`")
            elif type == 'url':
                url = re.search(
                    r'(https?://[^\s]+)', ctx.message.content).group(1)
                if url[-8:] == '.torrent':
                    await message.edit(content='Detected url, adding torrent...')
                    file_request = requests.get(url)
                    qb.download_from_file(
                        file_request.content, category='Public')
                    torrents = await get_sorted_by_date(qb.torrents())
                    torrent_name = torrents[-1]['name']
                    await message.edit(content=f"Added torrent: `{torrent_name}`")
                else:
                    await message.edit(content='Abort: url provided is not a torrent file')
            else:
                await message.edit(content='Abort: No torrent found')

            return
        except Exception as e:
            await message.edit(content='```Error: ' + str(e) + '```')


@bot.command()
async def space(ctx):
    if ctx.channel.id == CHANNEL_ID and ctx.author.id == OWNER_ID:
        message = await ctx.send('Calculating Space...')

        try:
            torrents = qb.torrents()
            total_size = 0
            for torrent in torrents:
                total_size += torrent['size']
            reply = f"Torrent(s): {len(torrents)}\nOccupied: {round(total_size / 1000000000, 2)} GB\nBuffer: {round(990 - (total_size / 1000000000), 2)} GB"
            await message.edit(content='```' + reply + '```')
        except Exception as e:
            await message.edit(content='```Error: ' + str(e) + '```')
            return


@bot.command()
async def remove(ctx, args: str = None, perm: int = 0):
    if ctx.channel.id == CHANNEL_ID and ctx.author.id == OWNER_ID:
        message = await ctx.send('Looking for Torrent...')

        if perm == 1:
            perm = True
        else:
            perm = False

        if args == None:
            await message.edit(content='```Error: No torrent name provided```')
            return
        if perm:
            await message.edit(content='WARNING: This will delete all data including the files. Continue?')
            confirm = await confirm_removal(ctx, message)
            if not confirm:
                await message.edit(content='User aborted, no torrents deleted')
                return
        try:
            torrents = qb.torrents()
            hits = []
            for torrent in torrents:
                if args.lower() in torrent['name'].lower():
                    hits.append(torrent)
            if len(hits) == 0:
                await message.edit(content=f'```No torrents found matching "{args}"```')
                return
            elif len(hits) > 0:
                await message.edit(content=f'Found {len(hits)} matching torrents. Are you sure you want to delete them?\n```{", ".join([torrent["name"] for torrent in hits])}```')
                confirm = await confirm_removal(ctx, message)
                if confirm:
                    if perm:
                        await message.edit(content=f'This command is destructive. Are you sure you want to delete {len(hits)} torrents? ')
                        confirm = await confirm_removal(ctx, message)
                        if not confirm:
                            await message.edit(content='User aborted, torrents not deleted')
                            return
                    for torrent in hits:
                        if perm:
                            qb.delete_permanently(torrent['hash'])
                        else:
                            qb.delete(torrent['hash'])

                    await message.edit(content=f'```Deleted {len(hits)} matching torrents```')
                else:
                    await message.edit(content='User aborted, torrents not deleted')
        except Exception as e:
            await message.edit(content='```Error: ' + str(e) + '```')


@bot.command()
async def clear(ctx):
    if ctx.channel.id == CHANNEL_ID and ctx.author.id == OWNER_ID:
        message = await ctx.send('Are you sure you want to clear this channel?')
        confirm = await confirm_removal(ctx, message)
        if confirm:
            await ctx.channel.purge()
        else:
            await message.edit(content='User aborted, channel not cleared')
    else:
        return


@bot.command()
async def ping(ctx, args: str = None):
    if ctx.channel.id == CHANNEL_ID and ctx.author.id == OWNER_ID:
        if args == None:
            args = 'bot'

        message = await ctx.send('Pinging...')
        if args == 'qbit':
            try:
                r = requests.get(CLIENT_URL + '/api/v2/app/webapiVersion')
                ping = r.elapsed.total_seconds() * 1000
                await message.edit(content=f"qBit: Pong! {round(ping)}ms")
            except Exception as e:
                await message.edit(content='```Error: ' + str(e) + '```')
        elif args == 'bot':
            try:
                ping = round(bot.latency * 1000)
                await message.edit(content=f"Bot: Pong! {ping}ms")
            except Exception as e:
                await message.edit(content='```Error: ' + str(e) + '```')
    else:
        return


@bot.command()
async def upload(ctx, args: str = None):
    if ctx.channel.id == CHANNEL_ID and ctx.author.id == OWNER_ID:
        message = await ctx.send('Getting Upload Data...')

        try:
            if args == None:
                await message.edit(content=f'No timepsan provided, getting upload for last 24h...')
                args = '24h'
            if args[-1] == 'h':
                seconds = int(args[:-1]) * 3600
            elif args[-1] == 'd':
                seconds = int(args[:-1]) * 86400
            elif args[-1] == 'm':
                seconds = int(args[:-1]) * 2592000
            else:
                await message.edit(content=f'Aborting, invalid timespan "{args}". ex: 24h, 7d, 1m')

            now = datetime.now()
            categories = {}

            for torrent in qb.torrents():
                upload_data = qb.get_torrent(torrent['hash'])['total_uploaded']
                added_time = datetime.fromtimestamp(torrent['added_on'])
                if (now - added_time).total_seconds() < seconds:
                    category = torrent['category']
                    if category not in categories:
                        categories[category] = 0
                    categories[category] += upload_data

            content = f"Uploads over {args}\n```"
            for category, upload in categories.items():
                if upload > 0:
                    content += f"{category}: {round(upload / 1000000000, 2)} GB\n"
            if content == f"Uploads over {args}\n```":
                content == "No uploads in the last {args}"
                await message.edit(content=content)
                return

            await message.edit(content=content + '```')
        except Exception as e:
            await message.edit(content='```Error: ' + str(e) + '```')
    else:
        return


@bot.command()
async def list(ctx, args: str = None):
    if ctx.channel.id == CHANNEL_ID and ctx.author.id == OWNER_ID:
        message = await ctx.send('Getting Torrents...')
        try:
            if args == None:
                content = f"Categories:\n\n"
                for category in await get_all_categories():
                    content += f"{category}\n"
                await message.edit(content='```' + content + '```')
                return
            torrents = qb.torrents()
            hits = []
            for torrent in torrents:
                if args.lower() in torrent['category'].lower():
                    hits.append(torrent)
            if len(hits) == 0:
                await message.edit(content=f'```No torrents found in category "{args}"```')
                return
            elif len(hits) > 0:
                for torrent in hits:
                    content += f"{torrent['name']}\n"
                await message.edit(content='```' + content + '```')
        except Exception as e:
            await message.edit(content='```Error: ' + str(e) + '```')


@bot.command()
async def help(ctx):
    if ctx.channel.id == CHANNEL_ID:
        message = await ctx.send('Getting Help...')
        try:
            content = f"```Commands:\n"
            content += f"- !status - Get number status of all torrents\n"
            content += f"- !status all - Get individual stats of each torrent\n"
            content += f"- !status [query] - Get status of specific torrent(s)\n"
            content += f"- !status [latest/oldest] - Get status of the lastest/oldest torrents \n"
            content += f"- !list - List categories\n"
            content += f"- !list [category] - List torrents\n"
            content += f"- !add [name] [url] - Add a torrent\n"
            content += f"- !remove [name] [perm] - Remove a torrent\n"
            content += f"- !clear - Clear this channel\n"
            content += f"- !ping [bot/qbit] - Ping the bot or qbit\n"
            content += f"- !upload [timespan] - Get upload data\n"
            content += f"- !help - Get this message\n```"
            await message.edit(content=content)
        except Exception as e:
            await message.edit(content='```Error: ' + str(e) + '```')
    else:
        return
    
@bot.command()
async def renew(ctx):
    if ctx.channel.id == CHANNEL_ID and ctx.author.id == OWNER_ID:
        global qb
        message = await ctx.send('Requesting qBit Client Renewal')
        try:
            qb = Client(CLIENT_URL)
            qb.login(CLIENT_USER, CLIENT_PASS)
            await message.edit(content='qBit Client Renewed')
        except Exception as e:
            await message.edit(content='```Error: ' + str(e) + '```')

if __name__ == '__main__':
    bot.run(DISCORD_TOKEN)
