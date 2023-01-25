import discord, re, requests
from creds import TOKEN

client = discord.Client(intents=discord.Intents.all())

async def push_to_ntfy(title, message, url, icon):
    try:
        requests.post("https://ntfy.1m.cx/manga",
            data=message.encode('utf-8'),
            headers={
                "Title": title,
                "Click": f"{url}",
                "Actions": f"http, Open In Browser, {url}, clear=true",
                "Tags": icon,
            })
    except:
        print("Error sending message to ntfy")

@client.event
async def on_message(message):
    if message.channel.id == 1041159396518015088:
        if message.author.id == 1041159446790950912:
            body = message.content

            try:
                chapter = re.search(r"Chapter (\d+)", body).group(1)
                url = re.search(r"(https?:\/\/[^\s]+)", body).group(1)
                is_break_next_week = re.search(r"(BREAK|NO BREAK) NEXT WEEK", body).group(1) == "BREAK"

                await push_to_ntfy(f"One Piece {chapter} Release!", f"{is_break_next_week == True and 'BREAK NEXT WEEK' or 'NO BREAK NEXT WEEK'}, Click To View", url, "boat")
            except:
                pass
        elif message.author.id == 1046961354222866452:
            try:
                url = re.search(r"(https?:\/\/(?:www\.)?(?:readseinen\.com|mangadex\.org)\/[^\s]+)", message.content).group(1)
                await push_to_ntfy("Berserk Chapter Release!", f"Click To View", url, "dagger")
            except:
                pass

if __name__ == "__main__":
    client.run(TOKEN)