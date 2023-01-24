"""
This is a Discord bot that allows you to control your hosted qBittorrent client from Discord.
"""

import discord
from discord.ext import commands
from qbittorrent import Client
import requests
import asyncio
from creds import *

qb = Client(CLIENT_URL)
qb.login(CLIENT_USER, CLIENT_PASS)

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
bot.remove_command('help')


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
async def status(ctx, args):
    if ctx.channel.id == CHANNEL_ID:
        message = await ctx.send('Getting Status...')
        torrents = qb.torrents()
        if args == 'all':
            await message.edit(content=f'Are you sure you want to list {len(torrents)} torrents?')
            confirm = await confirm_removal(ctx, message)
            if confirm:
                for torrent in torrents:
                    await ctx.send(f"{torrent['name']} ({round(torrent['uploaded'] / 1000000000, 2)} GB, {round(torrent['downloaded'] / 1000000000, 2)} GB) - {torrent['state']}")
            else:
                await message.edit(content='Aborted, Torrents Not Listed')
            await message.edit(content="Listed All Torrents")
        elif args == 'latest':
            for torrent in torrents[-1:]:
                await message.edit(content=f"{torrent['name']} ({round(torrent['uploaded'] / 1000000000, 2)} GB, {round(torrent['downloaded'] / 1000000000, 2)} GB) - {torrent['state']}")
        elif args == 'oldest':
            for torrent in torrents[:1]:
                await message.edit(content=f"{torrent['name']} ({round(torrent['uploaded'] / 1000000000, 2)} GB, {round(torrent['downloaded'] / 1000000000, 2)} GB) - {torrent['state']}")
        elif args.isdigit():
            if int(args) > len(torrents):
                await message.edit(content='You Only Have ' + str(len(torrents)) + ' Torrents. Try Again.')
                return
            for torrent in torrents[-int(args):]:
                await ctx.send(f"{torrent['name']} ({round(torrent['uploaded'] / 1000000000, 2)} GB, {round(torrent['downloaded'] / 1000000000, 2)} GB) - {torrent['state']}")
            await message.edit(content=f"Listed {args} Torrents")
        else:
            x = 0
            for torrent in torrents:
                if str(args).lower() in torrent['name'].lower():
                    x += 1
                    await message.edit(content=f"Found {x} Matching Torrents")
                    await ctx.send(f"{torrent['name']} ({round(torrent['uploaded'] / 1000000000, 2)} GB, {round(torrent['downloaded'] / 1000000000, 2)} GB) - {torrent['state']}")
            if x == 0:
                await message.edit(content='Torrent Not Found, Try Again')


@bot.command()
async def add(ctx, args):
    if ctx.channel.id == CHANNEL_ID:
        message = await ctx.send('Adding Torrent...')
        try:
            attachment_url = ctx.message.attachments[0].url
            file_request = requests.get(attachment_url)
            try:
                qb.download_from_file(file_request.content)
                await message.edit(content='Added Torrent File')
            except Exception as e:
                await message.edit(content='Error Adding Torrent File: ' + str(e))
        except:
            if 'magnet' in args:
                try:
                    qb.download_from_link(args)
                    await message.edit(content='Added Magnet Link')
                except Exception as e:
                    await message.edit(content='Error Adding Magnet Link: ' + str(e))
            else:
                await message.edit(content='Error Adding Torrent')


@bot.command()
async def space(ctx):
    if ctx.channel.id == CHANNEL_ID:
        message = await ctx.send('Calculating Space...')
        torrents = qb.torrents()
        total_size = 0
        for torrent in torrents:
            total_size += torrent['size']
        reply = f"Count: **{len(torrents)}**\nOccupied: **{round(total_size / 1000000000, 3)} GB**\nBuffer: **{round(990 - (total_size / 1000000000), 3)} GB**"
        await message.edit(content=reply)


@bot.command()
async def remove(ctx, args):
    if ctx.channel.id == CHANNEL_ID:
        message = await ctx.send('Looking for Torrent...')
        torrents = qb.torrents()
        x = 0
        for torrent in torrents:
            if args in torrent['name']:
                x += 1
                message = await ctx.send(f'Are you sure you want to remove {torrent["name"]}?')
                confirm = await confirm_removal(ctx, message)
                if confirm:
                    qb.delete(torrent['hash'])
                    await message.edit(content='Removed Torrent: ' + torrent['name'])
                else:
                    await message.edit(content='Aborted, Torrent Not Removed : ' + torrent['name'])

        if x == 0:
            await message.edit(content='Torrent Not Found, Try Again')


@bot.command()
async def clear(ctx):
    if ctx.channel.id == CHANNEL_ID:
        message = await ctx.send('Are you sure you want to clear this channel?')
        confirm = await confirm_removal(ctx, message)
        if confirm:
            await ctx.channel.purge()
        else:
            await message.edit(content='Aborted, Channel Not Cleared')


@bot.command()
async def help(ctx):
    if ctx.channel.id == CHANNEL_ID:
        message = await ctx.send('Loading...')
        help = "```\n"
        help += "add <magnet link> - Adds a torrent to the download queue\n"
        help += "add <torrent file> - Adds a torrent to the download queue\n"
        help += "remove <name> - Removes a torrent from the download queue\n"
        help += "status all - Lists all torrents in the download queue\n"
        help += "status latest - Lists the latest torrent in the download queue\n"
        help += "status oldest - Lists the oldest torrent in the download queue\n"
        help += "status <number> - Lists the latest <number> of torrents in the download queue\n"
        help += "status <name> - Lists all torrents with <name> in the download queue\n"
        help += "space - Lists the space used by the download queue\n"
        help += "clear - Clears the channel\n"
        help += "help - Lists all commands\n"
        help += "```"
        await message.edit(content=help)


@bot.command()
async def ping(ctx, args):
    if ctx.channel.id == CHANNEL_ID:
        if args == 'qb':
            message = await ctx.send('Pinging...')
            try:
                r = requests.get(CLIENT_URL + '/api/v2/app/webapiVersion')
                ping = r.elapsed.total_seconds() * 1000
                await message.edit(content=f"Pong! {round(ping)}ms")
            except Exception as e:
                await message.edit(content='Error: ' + str(e))
        elif args == 'bot':
            message = await ctx.send('Pinging...')
            try:
                ping = round(bot.latency * 1000)
                await message.edit(content=f"Pong! {ping}ms")
            except Exception as e:
                await message.edit(content='Error: ' + str(e))

@bot.command()
async def upload(ctx):
    if ctx.channel.id == CHANNEL_ID:
        message = await ctx.send('Getting Upload...')
        try:
            upload = qb.transfer_info()['total_upload']
            await message.edit(content=f"Uploaded {round(upload / 1000000000, 3)} GB")
        except Exception as e:
            await message.edit(content='Error: ' + str(e))

if __name__ == '__main__':
    bot.run(DISCORD_TOKEN)
