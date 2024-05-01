import discord
from discord.ext import commands
import typing 
from typing import Union, Optional
import aiohttp
import re
import requests
import io
from io import BytesIO

error = "<a:error:1227648997389504664>"
tick = "<:1209:1227285187717627904>"


class emojisticker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0x38024a
    
    @commands.command(aliases=['as', 'stealsticker'], description="Adds the sticker to the server")
    @commands.has_permissions(manage_emojis=True)
    async def addsticker(self, ctx: commands.Context, *, name=None):
        embed = discord.Embed(color=self.color)

        # Check if the command was replied to a message containing stickers
        if ctx.message.reference is None:
            embed.description = "No replied message found"
            return await ctx.reply(embed=embed)

        # Fetch the referenced message and check if it contains stickers
        msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        if len(msg.stickers) == 0:
            embed.description = "No sticker found"
            return await ctx.reply(embed=embed)

        # Extract the sticker name and URL from the referenced message
        sticker_name, sticker_url = msg.stickers[0].name, msg.stickers[0].url

        # Set the sticker name if not provided
        if name is None:
            name = sticker_name

        try:
            response = requests.get(sticker_url)
            if response.status_code != 200:
                embed.description = "Failed to fetch the sticker image"
                return await ctx.reply(embed=embed)

            # Determine the file extension based on the sticker URL
            is_animated = sticker_url.endswith(".gif")

            # Create a discord.File object from the sticker image data
            filename = "Sticker.gif" if is_animated else "Sticker.png"
            file = discord.File(BytesIO(response.content), filename)

            # Truncate the description to fit within the 200 character limit
            description = f"Sticker created by {str(self.bot.user)}"
            if len(description) > 200:
                description = description[:197] + "..."

            # Create the sticker in the server
            created_sticker = await ctx.guild.create_sticker(
                name=name,
                description=description,
                emoji="",  # emoji parameter is required but can be left empty
                file=file
            )

            # Update the embed description to indicate successful creation
            embed.description = f"Sticker created with name `{name}`"
            return await ctx.reply(embed=embed, stickers=[created_sticker])
        except Exception as e:
            # Handle any exceptions that occur during sticker creation
            embed.description = f"Failed to create the sticker\n{e}"
            return await ctx.reply(embed=embed)

    @commands.command(aliases=["deletesticker", "removesticker"], description="Delete the sticker from the server")
    @commands.has_permissions(manage_emojis=True)
    async def delsticker(self, ctx: commands.Context, *, name=None):
        embed = discord.Embed(color=self.color)
        
        if ctx.message.reference is None:
            embed.description = f"{error} |No replied message found"
            return await ctx.reply(embed=embed)
        
        msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        if len(msg.stickers) == 0:
            embed.description = f"{error} |No sticker found"
            return await ctx.reply(embed=embed)

        try:
            sticker_names = []
            for sticker in msg.stickers:
                sticker_names.append(sticker.name)
                await ctx.guild.delete_sticker(sticker)
            
            names_string = ", ".join([f"`{name}`" for name in sticker_names])
            embed.description = f"{tick} |Deleted Stickers: {names_string}"
            return await ctx.reply(embed=embed)
        except Exception as e:
            embed.description = f"{error} |Failed to delete the sticker\n{e}"
            return await ctx.reply(embed=embed)

    @commands.command(aliases=["delemoji", "removeemoji"], description="Deletes the emoji from the server")
    @commands.has_permissions(manage_emojis=True)
    async def deleteemoji(self, ctx, emoji=None):
        embed = discord.Embed(color=self.color)
        
        if ctx.message.reference is not None:
            message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            con = str(message.content)
        else:
            con = str(ctx.message.content)
        
        print("Content:", con)
        
        if con is not None:
            x = r"<a?:(?:[a-zA-Z0-9_]+:)?([0-9]+)>"
            xxx = re.findall(x, con)
            print("Emoji IDs:", xxx)
            
            count = 0
            if len(xxx) != 0:
                if len(xxx) >= 20:
                    embed.description = f"{error} |Maximum 20 emojis can be deleted by the bot."
                    return await ctx.reply(embed=embed)
                for i in xxx:
                    emoji_id = int(i)
                    print("Emoji ID:", emoji_id)
                    if emoji_id in [emoji.id for emoji in ctx.guild.emojis]:
                        emoo = await ctx.guild.fetch_emoji(emoji_id)
                        await emoo.delete()
                        count += 1
                embed.description = f"{tick} |Successfully deleted {count}/{len(xxx)} Emoji(s)"
                return await ctx.reply(embed=embed)
        else:
            embed.description = f"{error} |No Emoji found"
    
    
   

    @commands.command(aliases=["steal", "ae"], description="Adds the emoji to the server")
    @commands.has_permissions(manage_emojis=True)
    async def addemoji(self, ctx: commands.Context, emoji: Union[discord.Emoji, discord.PartialEmoji, str] = None, *, name: str = None):
        embed = discord.Embed(color=self.color, title="Emoji Addition")
        init = await ctx.reply(embed=embed)

        try:
            if not emoji:
                content = ctx.message.reference.resolved.content if ctx.message.reference else ctx.message.content
                emoji_ids = re.findall(r"<a?:[a-zA-Z0-9\_]+:([0-9]+)>", content)

                if emoji_ids:
                    count = 0
                    for emoji_id in emoji_ids:
                        emoji = discord.PartialEmoji(name="emoji", id=int(emoji_id))
                        url = f"https://cdn.discordapp.com/emojis/{emoji.id}.{'gif' if emoji.animated else 'png'}"

                        async with aiohttp.request("GET", url) as r:
                            if r.status == 200:
                                img = await r.read()
                                created_emoji = await ctx.guild.create_custom_emoji(name=emoji.name, image=img)
                                count += 1
                            else:
                                raise ValueError(f"Failed to fetch emoji with ID: {emoji.id}")

                    embed.description = f"Successfully created {count}/{len(emoji_ids)} emojis"
                    await init.edit(embed=embed)
                    return
                else:
                    raise ValueError("Please provide an emoji URL or reply to a message containing emojis.")

            if isinstance(emoji, str):
                if not emoji.startswith("https://"):
                    raise ValueError("Please provide a valid emoji URL")

                url = emoji
            else:
                url = f"https://cdn.discordapp.com/emojis/{emoji.id}.{'gif' if emoji.animated else 'png'}"

            if not name:
                raise ValueError("Please provide a name for the emoji")

            async with aiohttp.request("GET", url) as r:
                if r.status == 200:
                    img = await r.read()
                    created_emoji = await ctx.guild.create_custom_emoji(name=name, image=img, animated=".gif" in url)
                    embed.description = f"Successfully created {created_emoji}"
                    await init.edit(embed=embed)
                    return
                else:
                    raise ValueError("Failed to fetch the emoji from the URL")

        except discord.Forbidden:
            embed.description = "I don't have permissions to add emojis."
            await init.edit(embed=embed)
        except Exception as e:
            embed.description = f"An error occurred: {e}"
            await init.edit(embed=embed)

async def setup(bot):
    await bot.add_cog(emojisticker(bot))
