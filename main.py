import discord
from discord.ext import commands, tasks
import asyncio
import colorama
from colorama import Fore
from itertools import cycle
import json
import datetime
import os
from discord.ui import View, Button 
from Extra.np import get_prefix
colorama.init(autoreset=True)

status = cycle(['The SkyGem | $help ','play.skygem.fun'])

with open('Database/info.json', 'r') as f:
    Data = json.load(f)

ray = Data['OWNER_IDS']
print(f"{ray}\n")
class Context(commands.Context):
    async def send(self, content: str = None, *args, **kwargs) -> discord.Message:
        return await super().send(content, *args, **kwargs)

intents = discord.Intents.all()

class Bot(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(
            command_prefix=get_prefix,
            intents=intents,
            shards=2,
            shard_count=2,
            help_command=None,
            case_insensitive=True,
            strip_after_prefix=True,
            status=discord.Status.dnd,
            activity=discord.Activity(type=discord.ActivityType.playing, name=next(status)),
        )

    async def setup_hook(self):
        self.launch_time = datetime.datetime.now(datetime.timezone.utc)

        extensions = [
            "jishaku",
            "Cogs.afk",
            "Cogs.leaderboard",
            "Cogs.role",
            "Cogs.extra",
            "Cogs.owner",
            "Cogs.giveaway",
            "Cogs.help",
            "Cogs.moderation",
            "Cogs.auto",
            "Cogs.mention",
            "Cogs.autorole",
            "Extra.event",
            "Extra.error_handler",
            "Cogs.emojisticker",
            "Cogs.antinuke",
            "Cogs.Events.antichannel"
        ]
        for extension in extensions:
          try:
            await self.load_extension(extension)
            print(f"Loaded extension: {extension}")
          except Exception as e:
            print(f"Failed to load extension {extension}. Reason: {e}")

    @tasks.loop(seconds=2)
    async def status_task(self):
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name=next(status)))

    async def get_context(self, message, *, cls=None):
        return await super().get_context(message, cls=cls or Context)

    async def on_ready(self):
        self.status_task.start()
        ray = Fore.RED
        os.system("cls")
        print(Fore.RED + r"""
-----------------------------------------------------
| ░▒▓██████▓▒░░▒▓███████▓▒░ ░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░ |
|░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░ |
|░▒▓████████▓▒░▒▓███████▓▒░░▒▓█▓▒░      ░▒▓████████▓▒░ |
|░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░ |
|░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ |
|░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░ |
 ------------------------------------------------------  """)
        print(f"{ray}Logged In As {self.user}\nID - {self.user.id}")
        print(f"{ray} Made by ray <3")
        print(f"{ray}logged In as {self.user.name}")
        print(f"{ray}Total servers ~ {len(self.guilds)}")
        print(f"{ray}Total Users ~ {len(self.users)}")

    async def on_message_edit(self, before, after):
        ctx: Context = await self.get_context(after, cls=Context)
        if before.content != after.content:
            if after.guild is None or after.author.bot:
                return
            if ctx.command is None:
                return
            if str(ctx.channel.type) == "public_thread":
                return
            await self.invoke(ctx)
        else:
            return

os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"
os.environ["JISHAKU_HIDE"] = "True"
os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_FORCE_PAGINATOR"] = "True"
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

client.run(os.getenv("token"))

client=Bot()

client.owner_ids=ray
ray = ""

async def main(AA):
    await client.start(ray, reconnect=True)

asyncio.run(main())
