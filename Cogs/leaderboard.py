import discord
from discord.ext import commands
import datetime
import json
import asyncio
import traceback

with open('./Database/info.json', 'r') as f:
    Data = json.load(f)

def is_higher_admin(ctx):
    if ctx.guild is None:
        return False
    return ctx.author == ctx.guild.owner or ctx.author.id in Data['OWNER_IDS'] or ctx.author.guild_permissions.administrator

class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.file_path = "./Database/leaderboard_data.json"
        self.initialize_data()
        self.update_task = self.bot.loop.create_task(self.update_leaderboard_loop())
        self.color = 0x38024a
    def initialize_data(self):
        try:
            with open(self.file_path, "r") as file:
                pass
        except FileNotFoundError:
            data = {
                "leaderboard": {},
                "channels": {}
            }
            with open(self.file_path, "w") as file:
                json.dump(data, file, indent=4)

    def load_data(self):
        with open(self.file_path, "r") as file:
            return json.load(file)

    def save_data(self, data):
        with open(self.file_path, "w") as file:
            json.dump(data, file, indent=4)

    async def exponential_backoff(self, coro):
        retries = 0
        while True:
            try:
                return await coro
            except discord.HTTPException as e:
                if e.status in {502, 503} and retries < 3:  # Retrying for Bad Gateway and Service Unavailable
                    retries += 1
                    await asyncio.sleep(2 ** retries)
                else:
                    raise

    async def update_leaderboard_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                #print("Updating leaderboard...")
                await self.update_leaderboard()
            except Exception:
                traceback.print_exc()
            await asyncio.sleep(30)  # Update leaderboard every 30 seconds

    async def update_leaderboard(self):
        data = self.load_data()
        for guild_id, guild_data in data["leaderboard"].items():
            try:
                print(f"Processing guild ID: {guild_id}")  # Debug statement
                guild = self.bot.get_guild(int(guild_id))
                if guild:
                    for channel_id in data["channels"].get(guild_id, []):
                        channel = guild.get_channel(int(channel_id))
                        if channel:
                            weekly_message_id = guild_data.get("weekly_leaderboard_message_id")
                            if weekly_message_id:
                                weekly_message = await self.exponential_backoff(
                                    channel.fetch_message(weekly_message_id)
                                )
                                if weekly_message:
                                    monthly_message_id = guild_data.get("monthly_leaderboard_message_id")
                                    monthly_message = await self.exponential_backoff(
                                        channel.fetch_message(monthly_message_id)
                                    )
                                    if monthly_message:
                                        lifetime_message_id = guild_data.get("lifetime_leaderboard_message_id")
                                        lifetime_message = await self.exponential_backoff(
                                            channel.fetch_message(lifetime_message_id)
                                        )
                                        await asyncio.sleep(2)
                                        await self.update_leaderboard_embed(guild, guild_id, weekly_message, monthly_message, lifetime_message)

            except discord.errors.NotFound as e:
                print(f"Message not found: {e}")

            except Exception as e:
                print(f"Error updating leaderboard: {e}")

    async def update_leaderboard_embed(self, guild, guild_id, weekly_message, monthly_message, lifetime_message):
        print(f"Updating leaderboard embed for guild: {guild_id}")
        data = self.load_data()
        leaderboard_data = data["leaderboard"][guild_id].get("users", {})

        if weekly_message:
            embed_weekly = await self.generate_embed(guild_id, leaderboard_data, '**<:stats:1224393794104066110> | Weekly Leaderboard**')
            # Update embed
            await weekly_message.edit(embed=embed_weekly)

        if monthly_message:
            embed_monthly = await self.generate_embed(guild_id, leaderboard_data, '**<:stats:1224393794104066110> | Monthly Leaderboard**')
            # Update embed
            await monthly_message.edit(embed=embed_monthly)

        if lifetime_message:
            embed_lifetime = await self.generate_embed(guild_id, leaderboard_data, '**<:stats:1224393794104066110> | Lifetime Leaderboard**')
            # Update embed
            await lifetime_message.edit(embed=embed_lifetime)

    async def generate_embed(self, guild_id, leaderboard_data, title):
        print(f"Generating embed for {title}")
        embed = discord.Embed(title=title, description="This is the leaderboard for chat stats.", color=self.color
        )
        embed.set_footer(text="Leaderboard updated every 30 seconds")
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1210268753036705882/1224400757739229245/stats.png?ex=661d5b10&is=660ae610&hm=d95c1f4c4ba8971ecc51e4e1&")
        embed.set_image(url='https://cdn.discordapp.com/attachments/1210268753036705882/1221852115304185969/divider.png?ex=66141575&is=6601a075&hm=687a4ad79a80d8508fa6bca7&')

        try:
            leaderboard_text = ""
            sorted_leaderboard = sorted(leaderboard_data.items(), key=lambda x: x[1], reverse=True)[:15]

            for idx, (user_id, chat_count) in enumerate(sorted_leaderboard, 1):
                try:
                    guild = self.bot.get_guild(int(guild_id))
                    if guild:
                        member = guild.get_member(int(user_id))
                        if member:
                            leaderboard_text += f"<:curvedline_B:1224397348667527274>`#{idx}` <a:dot:1218087533141819413> **|** {member.mention} : **messages** - `{chat_count}`\n"
                except Exception as e:
                    print(f"Error processing user data: {e}")

            embed.description = leaderboard_text
        except Exception as e:
            print(f"Error generating embed for {title}: {e}")

        return embed

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        print(f"Guild removed: {guild.name}")
        await self.delete_guild_data(guild.id)

    async def delete_guild_data(self, guild_id):
        print(f"Deleting data for guild ID: {guild_id}")
        data = self.load_data()
        if guild_id in data["leaderboard"]:
            del data["leaderboard"][guild_id]
        self.save_data(data)

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot and not message.content.startswith('owo'):
            guild_id = str(message.guild.id)
            user_id = str(message.author.id)

            data = self.load_data()
            data["leaderboard"].setdefault(guild_id, {})
            data["leaderboard"][guild_id].setdefault("users", {})
            data["leaderboard"][guild_id]["users"].setdefault(user_id, 0)
            data["leaderboard"][guild_id]["users"][user_id] += 1

            await self.check_weekly_reset(guild_id)
            await self.check_monthly_reset(guild_id)
            self.save_data(data)

    async def check_weekly_reset(self, guild_id):
        #print("Checking weekly reset...")  # Debug statement
        data = self.load_data()
        weekly_reset = datetime.datetime.fromisoformat(data["leaderboard"][guild_id]["weekly_reset"])

        if datetime.datetime.utcnow() > weekly_reset + datetime.timedelta(days=7):
            data["leaderboard"][guild_id]["weekly_reset"] = str(datetime.datetime.utcnow())
            self.save_data(data)
            await self.reset_leaderboard(guild_id, 'weekly_reset')

    async def check_monthly_reset(self, guild_id):
        #print("Checking monthly reset...")  # Debug statement
        data = self.load_data()
        monthly_reset = datetime.datetime.fromisoformat(data["leaderboard"][guild_id]["monthly_reset"])

        if datetime.datetime.utcnow() > monthly_reset + datetime.timedelta(days=30):
            data["leaderboard"][guild_id]["monthly_reset"] = str(datetime.datetime.utcnow())
            self.save_data(data)
            await self.reset_leaderboard(guild_id, 'monthly_reset')

    async def reset_leaderboard(self, guild_id, reset_type):
        #print(f"Resetting {reset_type} leaderboard for guild ID: {guild_id}")
        data = self.load_data()
        leaderboard_data = data["leaderboard"][guild_id].get("users", {})
        for user_id in leaderboard_data:
            leaderboard_data[user_id] = 0
        self.save_data(data)

    @commands.Cog.listener()
    async def command_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            embed = discord.Embed(title='Error occurred', description=f"<:crosss:1212440602659262505> | You don't have enough permissions to use this command.")
            embed.set_image(url='https://cdn.discordapp.com/attachments/1210268753036705882/1221852115304185969/divider.png?ex=66141575&is=6601a075&hm=cf2b18e95b792252568ae8d899ae4a5e605e7a5b687a4ad79a80d8508fa6bca7&')
            await ctx.send(embed=embed)
        elif isinstance(error, commands.CommandInvokeError):
            embed = discord.Embed(title='Error occurred', description=f'<:crosss:1212440602659262505> | Please run the command `$leaderboard setup <channel>` to setup the leaderboard')
            embed.set_image(url='https://cdn.discordapp.com/attachments/1210268753036705882/1221852115304185969/divider.png?ex=66141575&is=6601a075&hm=cf2b18e95b792252568ae8d899ae4a5e605e7a5b687a4ad79a80d8508fa6bca7&')
            await ctx.send(embed=embed)

    @commands.group(name='leaderboard', aliases=['lb', 'ranking'], invoke_without_command=True)
    async def _leaderboard(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="Leaderboard Command Help",
                description="Here are the available subcommands for the leaderboard command:\n```- [] = optional argument\n- <> = required argument\n- Do NOT Type These When Using Commands !```",
                color=self.color
                
            )
            embed.add_field(name="`$leaderboard setup <channel>`", value="Setup the leaderboard for your server.", inline=False)
            embed.add_field(name="`$leaderboard delete`", value="Delete the leaderboard.", inline=False)
            embed.add_field(name="`$leaderboard reset`", value="Reset the leaderboard stats.", inline=False)
            embed.add_field(name="`$leaderboard resend`", value="Resend the leaderboard to the same channel if it got deleted.", inline=False)
            embed.add_field(name="`$leaderboard stats <member>`", value="Shows the stats of mentioned user", inline=False)
            embed.add_field(name="`$leaderboard resetuser <member>`", value="Delete the stats of mentioned user", inline=False)
            embed.set_image(url='https://cdn.discordapp.com/attachments/1210268753036705882/1221852115304185969/divider.png?ex=66141575&is=6601a075&hm=cf2b18e95b792252568ae8d899ae4a5e605e7a5b687a4ad79a80d8508fa6bca7&')
            await ctx.send(embed=embed)

    @_leaderboard.command()
    @commands.check(is_higher_admin)
    async def setup(self, ctx, channel: discord.TextChannel):
        data = self.load_data()
        guild_id = str(ctx.guild.id)
        data["leaderboard"].setdefault(guild_id, {})
        data["leaderboard"][guild_id].setdefault("weekly_reset", str(datetime.datetime.utcnow()))
        data["leaderboard"][guild_id].setdefault("monthly_reset", str(datetime.datetime.utcnow()))
        data["channels"].setdefault(guild_id, [])
        data["channels"][guild_id].append(str(channel.id))
        self.save_data(data)

        embed = discord.Embed(
            title="Leaderboard",
            description="This is the leaderboard for chat stats.",
            color=self.color
            
        )
        embed.set_image(url='https://cdn.discordapp.com/attachments/1210268753036705882/1221852115304185969/divider.png?ex=66141575&is=6601a075&hm=cf2b18e95b792252568ae8d899ae4a5e605e7a5b687a4ad79a80d8508fa6bca7&')
        embed.set_footer(text="Leaderboard updated every 30 seconds")
        weekly_message = await channel.send(embed=embed)
        monthly_message = await channel.send(embed=embed)
        lifetime_message = await channel.send(embed=embed)

        data["leaderboard"][guild_id]["weekly_leaderboard_message_id"] = weekly_message.id
        data["leaderboard"][guild_id]["monthly_leaderboard_message_id"] = monthly_message.id
        data["leaderboard"][guild_id]["lifetime_leaderboard_message_id"] = lifetime_message.id

        self.save_data(data)

        await self.update_leaderboard_embed(ctx.guild, guild_id, weekly_message, monthly_message, lifetime_message)
        embed = discord.Embed(
            title='Success',
            description=f"<:IconTick:1213170250267492383> | Successfully created leaderboard in {channel.mention}",
            color=self.color
            
        )
        embed.set_image(url='https://cdn.discordapp.com/attachments/1210268753036705882/1221852115304185969/divider.png?ex=66141575&is=6601a075&hm=cf2b18e95b792252568ae8d899ae4a5e605e7a5b687a4ad79a80d8508fa6bca7&')
        await ctx.send(embed=embed)

    @_leaderboard.command()
    @commands.check(is_higher_admin)
    async def delete(self, ctx):
        data = self.load_data()
        guild_id = str(ctx.guild.id)
        if guild_id in data["leaderboard"]:
            del data["leaderboard"][guild_id]
        if guild_id in data["channels"]:
            del data["channels"][guild_id]
        self.save_data(data)

        embed = discord.Embed(
            title="Success",
            description=f"<:IconTick:1213170250267492383> | Successfully deleted leaderboard from this server.",
            color=self.color
            
        )
        await ctx.send(embed=embed)

    @_leaderboard.command()
    @commands.check(is_higher_admin)
    async def reset(self, ctx):
        data = self.load_data()
        guild_id = str(ctx.guild.id)
        if guild_id in data["leaderboard"]:
            data["leaderboard"][guild_id]["weekly_reset"] = str(datetime.datetime.utcnow())
            data["leaderboard"][guild_id]["monthly_reset"] = str(datetime.datetime.utcnow())
            for user_id in data["leaderboard"][guild_id].get("users", {}):
                data["leaderboard"][guild_id]["users"][user_id] = 0
            self.save_data(data)

            embed = discord.Embed(
                title="Success",
                description=f"<:IconTick:1213170250267492383> | Successfully reset the leaderboard stats for this server.",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Error",
                description=f"<:crosss:1212440602659262505> | Leaderboard not set up for this server.",
                color=self.color
                
            )
            await ctx.send(embed=embed)

    @_leaderboard.command()
    async def resend(self, ctx):
        data = self.load_data()
        guild_id = str(ctx.guild.id)
        channels = data["channels"].get(guild_id, [])
        if channels:
            for channel_id in channels:
                channel = ctx.guild.get_channel(int(channel_id))
                if channel:
                    weekly_message_id = data["leaderboard"][guild_id].get("weekly_leaderboard_message_id")
                    if weekly_message_id:
                        weekly_message = await channel.fetch_message(weekly_message_id)
                        if weekly_message:
                            monthly_message_id = data["leaderboard"][guild_id].get("monthly_leaderboard_message_id")
                            if monthly_message_id:
                                monthly_message = await channel.fetch_message(monthly_message_id)
                                if monthly_message:
                                    lifetime_message_id = data["leaderboard"][guild_id].get("lifetime_leaderboard_message_id")
                                    if lifetime_message_id:
                                        lifetime_message = await channel.fetch_message(lifetime_message_id)
                                        if lifetime_message:
                                            await self.update_leaderboard_embed(ctx.guild, guild_id, weekly_message, monthly_message, lifetime_message)
                                            embed = discord.Embed(
                                                title="Success",
                                                description=f"<:IconTick:1213170250267492383> | Successfully resent the leaderboard to {channel.mention}",
                                                color=discord.Color.green()
                                            )
                                            await ctx.send(embed=embed)
                                            return
        embed = discord.Embed(
            title="Error",
            description=f"<:crosss:1212440602659262505> | Leaderboard not found in any channel.",
            color=self.color
            
        )
        await ctx.send(embed=embed)

    @_leaderboard.command(name="stats")
    async def _stats(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author

        data = self.load_data()
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)

        user_stats = data["leaderboard"].get(guild_id, {}).get("users", {}).get(user_id, 0)

        embed = discord.Embed(
            title=f"Stats for {member.display_name}",
            description=f"Total Messages: {user_stats}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @_leaderboard.command(name="resetuser")
    @commands.check(is_higher_admin)
    async def _resetuser(self, ctx, member: discord.Member):
        data = self.load_data()
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)

        if guild_id in data["leaderboard"]["users"] and user_id in data["leaderboard"]["users"][guild_id]:
            data["leaderboard"]["users"][guild_id][user_id] = 0
            self.save_data(data)
            embed = discord.Embed(
                title="Success",
                description=f"<:IconTick:1213170250267492383> | Successfully reset the stats for {member.display_name}",
                color=self.color
                
            )
        else:
            embed = discord.Embed(
                title="Error",
                description=f"<:crosss:1212440602659262505> | No stats found for {member.mention}",color=self.color
                
            )

        await ctx.send(embed=embed)

async def setup(bot):
   await bot.add_cog(Leaderboard(bot))
