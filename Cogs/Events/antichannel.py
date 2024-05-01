import discord
from discord.ext import commands, tasks
import os
import random
import aiohttp
import json
import datetime
antinuke = "./Database/antinuke.json"
class antichannel(commands.Cog):
    def __init__(self, client):
        self.bot = client      
        self.processing = []

    @tasks.loop(seconds=15)
    async def clean_processing(self):
        self.processing.clear()

    @commands.Cog.listener()
    async def on_ready(self):
        await self.clean_processing.start()

    async def delete_channel(self, channel: discord.abc.GuildChannel):
        try:
            await channel.delete()
        except:
            pass

    async def punish_member(self, guild, user_id, antinuke_mode):
        member = guild.get_member(user_id)
        if member:
            if antinuke_mode == "beast":
                await member.ban(reason="Beast Mode: Channel Created | Not Whitelisted")
            elif antinuke_mode == "secure":
                
                await member.edit(roles=[], reason="Secure Mode: Channel Created | Not Whitelisted")
                data = self.get_antinuke_config(guild.id)
                blocked_role_id = data.get("quarantine_role_id")

                blocked_role = discord.utils.get(guild.roles, id=blocked_role_id)

                if blocked_role:
                    await member.add_roles(blocked_role, reason="Secure Mode: Channel Created | Not Whitelisted")
                    await self.send_log(guild, f"Added Blocked role to {member.display_name}")

    async def send_log(self, guild, message):
        data = self.get_antinuke_config(guild.id)
        log_channel_id = data.get("arch_logs_channel_id") 
        log_channel = guild.get_channel(log_channel_id)
        if log_channel:
            await log_channel.send(message)

    def get_antinuke_config(self, guild_id):
        with open(antinuke, "r") as file:
            antinuke_data = json.load(file)
        return antinuke_data.get(str(guild_id), {})

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel) -> None:
        try:
            if channel.id in self.processing:
                return
            self.processing.append(channel.id)
            data = self.get_antinuke_config(channel.guild.id)
            antinuke_enabled = data.get("antinuke_enabled", False)
            antinuke_mode = data.get("mode", None)
            whitelist = data.get("whitelist", [])  
            extra_owners = data.get("extra_owners", [])  
            culprit_id = await self.get_audit_log_user(channel.guild, discord.AuditLogAction.channel_create)
            if antinuke_enabled and antinuke_mode and culprit_id:
                if culprit_id not in whitelist and culprit_id not in extra_owners and culprit_id != self.bot.user.id:
                    try:
                        await self.punish_member(channel.guild, culprit_id, antinuke_mode)
                    except:
                        await self.send_log(channel.guild, f"Channel {channel.name} created by a non-whitelisted user and deleted. but i cant take action cause the culprits role is higher then me")
                    await self.delete_channel(channel)
                    await self.send_log(channel.guild, f"Channel {channel.name} created by a non-whitelisted user and deleted.")
        except Exception as error:
            if isinstance(error, discord.Forbidden):
                return
            else:
                raise
        finally:
            self.processing.remove(channel.id)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel) -> None:
        try:
            data = self.get_antinuke_config(channel.guild.id)
            antinuke_enabled = data.get("antinuke_enabled", False)
            antinuke_mode = data.get("mode", None)
            whitelist = data.get("whitelist", [])  
            extra_owners = data.get("extra_owners", [])  
            culprit_id = await self.get_audit_log_user(channel.guild, discord.AuditLogAction.channel_delete)
            if antinuke_enabled and antinuke_mode and culprit_id:
                if culprit_id not in whitelist and culprit_id not in extra_owners and culprit_id != self.bot.user.id:
                  try:
                    await self.punish_member(channel.guild, culprit_id, antinuke_mode)
                  except:
                      await self.send_log(channel.guild, f"Channel {channel.name} created by a non-whitelisted user and deleted. but i cant take action cause the culprits role is higher then me") 
                  await channel.clone(reason="Channel Deleted | Not Whitelisted")
        except Exception as error:
            if isinstance(error, discord.Forbidden):
                return

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after) -> None:
        try:
            data = self.get_antinuke_config(before.guild.id)
            antinuke_enabled = data.get("antinuke_enabled", False)
            antinuke_mode = data.get("mode", None)
            whitelist = data.get("whitelist", [])  
            extra_owners = data.get("extra_owners", [])  
            culprit_id = await self.get_audit_log_user(before.guild, discord.AuditLogAction.channel_update)
            if antinuke_enabled and antinuke_mode and culprit_id:
                if culprit_id not in whitelist and culprit_id not in extra_owners and culprit_id != self.bot.user.id:
                  try:
                    await self.punish_member(before.guild, culprit_id, antinuke_mode)
                  except:
                    await self.send_log(channel.guild, f"Channel {channel.name} created by a non-whitelisted user and deleted. but i cant take action cause the culprits role is higher then me")
                  await after.edit(name=f"{before.name}", topic=before.topic, nsfw=before.nsfw, category=before.category, slowmode_delay=before.slowmode_delay, type=before.type, overwrites=before.overwrites, reason="Channel Updated | Not Whitelisted")
        except Exception as error:
            if isinstance(error, discord.Forbidden):
                return

    async def get_audit_log_user(self, guild, action):
        async for entry in guild.audit_logs(limit=1, action=action):
            return entry.user.id
        return None

async def setup(client):
    await client.add_cog(antichannel(client))
