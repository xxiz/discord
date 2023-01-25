import requests
import discord
import io, os
from asyncio import sleep
from mimetypes import guess_extension

class MX():
    def __init__(self, id: str, message: discord.Message, channelID: int = 1067638742082400318, initatorID: int = 740632983630905445, download_speed: int = 1, upload_speed: int = 0.5, is_cbz: bool = False):
        self.id = id
        self.message = message
        self.channelID = channelID
        self.initatorID = initatorID
        self.download_speed = download_speed
        self.upload_speed = upload_speed
        self.thread = None
        self.is_cbz = is_cbz
        self.header = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
            'Referer': 'https://www.google.com',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'TE': 'Trailers',
            'origin': 'https://m' + 'anga' + 'dex.org',
            'referer': 'htt' + 'ps://m' + 'ang' + 'adex.org/',
        }

    async def get_metadata(self):
        r = requests.get(f"https://api.ma" + "ng" + "a" + f"dex.org/chapter/{self.id}?includes[]=scanlation_group&includes[]=manga&includes[]=user", headers=self.header).json()
        try:
            return r.get('data').get('attributes')
        except AttributeError:
            print("WARNING: could not fetch metadata")
            return None

    async def get_api(self):
        r = requests.get(f"https://api.m" + "an" + "gad" + "ex.org/a" + "t-home/ser" + f"ver/{self.id}?forcePo" + "rt443=false", headers=self.header).json()
        r = r.get('chapter')
        return (r.get('hash'), r.get('data'), r.get('dataSaver'))

    async def get_pages(self, maxQuality=True):
        await self.message.edit(content="Waiting for API...")
        hash, pages_maxres, pages_lowres = await self.get_api()
        await self.message.edit(content="Found Pages...")
        if maxQuality:
            return [f"https://u" + "plo" + "ads.m" + "ang" + "ade" + f"x.org/data/{hash}/{page}" for page in pages_maxres]
        else:
            return [f"https://u" + "plo" + "ads.m" + "ang" + "ade" + f"x.org/data/{hash}/{page}" for page in pages_lowres]

    async def download(self, maxQuality=True):
        pages = await self.get_pages(maxQuality)
        metadata = await self.get_metadata()
        media = []

        i = 0
        for page in pages:
            with requests.get(page, stream=True, headers=self.header) as response:
                if response.status_code == 200:
                    i+=1
                    file = io.BytesIO(response.content)
                    file.seek(0)
                    file_extension = guess_extension(response.headers['content-type'])
                    media.append(discord.File(file, filename=f"{i}{file_extension}"))
                    await self.message.edit(content=f"Downloading... {len(media)}/{len(pages)}")
                else:
                    print(
                        f"WARNING: could not fetch page {page} got {response.status_code}")
                await sleep(self.download_speed)
        
        if self.is_cbz:
            await self.to_cbz(media, f"{metadata.get('chapter')} - {metadata.get('title')}")
            return

        thread = await self.create_thread(thread, f"{metadata.get('chapter')} - {metadata.get('title')}")

        for file in media:
            await thread.send(file=file)
            await self.message.edit(content=f"Uploading... {media.index(file)}/{len(media)}")
            await sleep(self.upload_speed)

        await self.message.edit(content="Done!")
        
    async def download_fast_view(self, thread, maxQuality=True):
        pages = await self.get_pages(maxQuality)
        metadata = await self.get_metadata()

        thread = await self.create_thread(thread, f"{metadata.get('chapter')} - {metadata.get('title')}")

        for page in pages:
            with requests.get(page, stream=True, headers=self.header) as response:
                if response.status_code == 200:
                    file = io.BytesIO(response.content)
                    file.seek(0)
                    await thread.send(file=discord.File(file, filename=page))
                    await sleep(self.download_speed)
                else:
                    print(f"WARNING: could not fetch page {page} got {response.status_code}")
                await sleep(self.download_speed)
                    
    async def create_thread(self, bot, title):
        channel = bot.get_channel(1067638742082400318)
        self.thread = await channel.create_thread(name=title, type=discord.ChannelType.public_thread)
        await self.thread.send("<@" + str(self.initatorID) + ">")
        return self.thread
    
    async def to_cbz(self, media_files, title):
        import zipfile

        await self.message.edit(content="Creating CBZ...")
        with zipfile.ZipFile(f"{title}.cbz", "w") as cbz:
            for file in media_files:
                await self.message.edit(content=f"Adding... {media_files.index(file)}/{len(media_files)}")
                cbz.writestr(file.filename, file.fp.read())
        
        await self.message.edit(content="Uploading CBZ...")
        await self.message.channel.send(file=discord.File(f"{title}.cbz"))
        await self.message.edit(content="Done!")
        os.remove(f"{title}.cbz")