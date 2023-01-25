import requests
import discord
import io
from bs4 import BeautifulSoup
from html import unescape
from asyncio import sleep
from mimetypes import guess_extension

class RN():
    def __init__(self, url: str, message: discord.Message, channelID: int = 1067638742082400318, initatorID: int = 740632983630905445, download_speed: int = 5, upload_speed: int = 0.5):
        self.url = url
        self.message = message
        self.thread = None
        self.channelID = channelID
        self.initatorID = initatorID
        self.download_speed = download_speed
        self.upload_speed = upload_speed
        self.header = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
            'Referer': 'https://www.google.com',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'TE': 'Trailers',
            'origin': 'https://read' + 'sei' + 'nen.com',
            'referer': 'htt' + 'ps://r' + 'ead' + 'seine' + 'n.com/',
        }

    async def get_json_url(self):
        await self.message.edit(content="Getting Json Url...")
        r = requests.get(self.url, headers=self.header)
        soup = BeautifulSoup(r.text, 'html.parser')
        json_endpoint = soup.find("link", {"rel": "alternate", "type": "application/json"})["href"]
        r = requests.get(json_endpoint, headers=self.header).json()
        return r
    
    async def get_image_links(self, html):
        await self.message.edit(content="Getting Image Links...")
        soup = BeautifulSoup(html, 'html.parser')
        images = soup.find_all("img")
        images = [image["src"] for image in images]
        return images
    
    async def get_data_from_json(self, json):
        await self.message.edit(content="Getting Data From Json...")
        images = await self.get_image_links(json.get('content').get('rendered'))
        title = json.get('title').get('rendered')
        return (images, unescape(title))
    
    async def download(self, bot):
        await self.message.edit(content="Downloading...")
        images, title = await self.get_data_from_json(await self.get_json_url())
        media = []
        i = 0
        
        thread = await self.create_thread(bot, title)

        for image in images:
            with requests.get(image, stream=True, headers=self.header) as response:
                if response.status_code == 200:
                    i+=1
                    file = io.BytesIO(response.content)
                    file.seek(0)
                    file_extension = guess_extension(response.headers['content-type'])
                    media.append(discord.File(file, filename=f"{i}{file_extension}"))
                    await self.message.edit(content=f"Downloading... {len(media)}/{len(images)}")
                else:
                    print(
                        f"WARNING: could not fetch page {image} got {response.status_code}")
                await sleep(self.download_speed)

        for file in media:
            await thread.send(file=file)
            await self.message.edit(content=f"Uploading... {media.index(file)}/{len(media)}")
            await sleep(self.upload_speed)
    
    async def download_fast_view(self, bot):
        await self.message.edit(content="Downloading...")
        images, title = await self.get_data_from_json(await self.get_json_url())
        thread = await self.create_thread(bot, title)

        i = 0
        for image in images:
            with requests.get(image, stream=True, headers=self.header) as response:
                if response.status_code == 200:
                    i+=1
                    file = io.BytesIO(response.content)
                    file.seek(0)
                    file_extension = guess_extension(response.headers['content-type'])
                    await thread.send(file=discord.File(file, filename=f"{i}{file_extension}"))
                    await self.message.edit(content=f"Downloading... {i}/{len(images)}")
                    await sleep(self.download_speed)
                else:
                    print(
                        f"WARNING: could not fetch page {image} got {response.status_code}")
                    
    async def create_thread(self, bot, title):
        channel = bot.get_channel(1067638742082400318)
        self.thread = await channel.create_thread(name=title, type=discord.ChannelType.public_thread)
        await self.thread.send("<@" + str(self.initatorID) + ">")
        return self.thread