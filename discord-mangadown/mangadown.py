import discord
from discord.ext import commands
from creds import TOKEN
from mx import MX
from rn import RN

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
bot.remove_command("help")

@bot.command()
async def raw(ctx, args: str = None, load_speed: str = None):
    if ctx.author.id == 740632983630905445 and ctx.channel.id == 1067638742082400318:
        message = await ctx.send("Checking...")

        if args is None:
            await message.edit(content="Please provide a link")

        elif args.startswith("https://m" + "anga" + "d" + "e" + "x.org"):
            chapter = args.split("chapter/")[1].replace("/", "")
            
            if load_speed == None or load_speed == "normal":
                mx = MX(chapter, message=message)
                
                await mx.download(bot)

            elif load_speed == "fast":
                mx = MX(chapter, message=message)
                
                await mx.download_fast_view(bot)
        
        elif args.startswith("https://read" + "se" + "in" + "en.com"):

            if load_speed == None or load_speed == "normal" and load_speed != "fast":
                rn = RN(args, message=message)
                await rn.download(bot)
                
            elif load_speed == "fast":
                rn = RN(args, message=message)
                await rn.download_fast_view(bot)
        else:
            await message.edit(content="Please provide a valid link")
    else:
        pass

if __name__ == "__main__":
    bot.run(TOKEN)
