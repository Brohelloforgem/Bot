import discord
from discord.ext import commands
import json
import asyncio

antinuke = "./Database/antinuke.json"

async def check_permissions(guild, position):
    if len(guild.roles) < position:
        return True
    bot_role_position = guild.me.top_role.position
    return bot_role_position >= position

class SetupButton(discord.ui.Button):
    def __init__(self, bot, label, custom_id):
        super().__init__(label=label, custom_id=custom_id)
        self.bot = bot
        self.used = False  
        

    async def callback(self, interaction: discord.Interaction):
        ctx = interaction.channel
        try:
            guild = ctx.guild
            if self.custom_id == "secure_setup":
                if await check_permissions(guild, 10):
                    await self.secure_setup(ctx)
                    await interaction.response.send_message("You are using the secure mode", ephemeral=True)
                else:
                    await ctx.send("Cannot set up Secure mode. Bot's role is not in top 10.")
            elif self.custom_id == "beast_setup":
                if await check_permissions(guild, 5):
                    await self.beast_setup(ctx)
                    await interaction.response.send_message("You are using the beast mode", ephemeral=True)
                else:
                    await ctx.send("Cannot set up Beast mode. Bot's role is not in top 5.")
            elif self.custom_id == "no_setup":
                await self.no_setup(ctx)
                await interaction.response.send_message("Antinuke is disabled", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)

    


    async def check_permissions(self, guild, required_position):
        roles = sorted(guild.roles, reverse=True) 
        bot_top_role_position = roles[-1].position  
        return bot_top_role_position <= required_position

    async def secure_setup(self, ctx):
        guild = ctx.guild
        if await self.check_permissions(guild, 10):
            bot_role = guild.me.top_role
            quarantine_role = discord.utils.get(guild.roles, name="Blocked")
            if not quarantine_role:
                quarantine_role = await guild.create_role(name="Blocked")
                position = bot_role.position - 1 if bot_role.position != len(guild.roles) - 1 else bot_role.position
                await quarantine_role.edit(position=position)
            arch_goat_role = discord.utils.get(guild.roles, name="Arch Goat")
            if not arch_goat_role:
                arch_goat_role = await guild.create_role(name="Arch Goat")
                position = quarantine_role.position - 1 if quarantine_role.position != len(guild.roles) - 1 else quarantine_role.position
                await arch_goat_role.edit(position=position)
            
            await self.save_data_to_json(ctx, True, "secure", arch_goat_role_id=arch_goat_role.id, quarantine_role_id=quarantine_role.id)
            await ctx.send("Secure mode setup completed.")
            for channel in guild.channels:
                await channel.set_permissions(quarantine_role, read_messages=False)
        else:
            await ctx.send("Cannot set up Secure mode. Bot's role is not in top 10.")

    async def beast_setup(self, ctx):
        guild = ctx.guild
        bot_role = guild.me.top_role
        if await self.check_permissions(guild, 5): 
            if not arch_goat_role:
                arch_goat_role = await guild.create_role(name="Arch Goat")
                position = bot_role.position - 1 if bot_role.position != len(guild.roles) - 1 else bot_role.position
                await arch_goat_role.edit(position=position)
            
            await self.save_data_to_json(ctx, True, "beast", arch_goat_role_id=arch_goat_role.id)
            await ctx.send("Beast mode setup completed.")
        else:
            await ctx.send("Cannot set up Beast mode. Bot's role is not in top 5.")

    async def no_setup(self, ctx):
        await self.save_data_to_json(ctx, False, "none")
        await ctx.send("Antinuke is disabled")

    async def get_or_create_role_id(self, guild, role_name):
        role_id = None
        role = discord.utils.get(guild.roles, name=role_name)
        if not role:
            new_role = await guild.create_role(name=role_name)
            role_id = new_role.id
        else:
            role_id = role.id
        return role_id

    async def save_data_to_json(self, ctx, enabled, mode, arch_goat_role_id=None, quarantine_role_id=None):
        data = {"antinuke_enabled": enabled, "mode": mode, "whitelist": []}
        if arch_goat_role_id:
            data["arch_goat_role_id"] = arch_goat_role_id
        if quarantine_role_id:
            data["quarantine_role_id"] = quarantine_role_id

        with open(antinuke, "r") as file:
            antinuke_data = json.load(file)

        guild_id = str(ctx.guild.id)
        antinuke_data[guild_id] = data

        with open(antinuke, "w") as file:
            json.dump(antinuke_data, file, indent=4)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        antinuke_data = self.load_antinuke_data(channel.guild.id)
        if antinuke_data.get("antinuke_enabled") and antinuke_data.get("mode") == "secure":
            quarantine_role_id = antinuke_data.get("quarantine_role_id")
            if quarantine_role_id:
                quarantine_role = channel.guild.get_role(quarantine_role_id)
                if quarantine_role:
                    await channel.set_permissions(quarantine_role, read_messages=False)

    def load_antinuke_data(self, guild_id):
        with open(antinuke, "r") as file:
            antinuke_data = json.load(file)
        
        
        antinuke_entry = antinuke_data.get(str(guild_id), {})
        antinuke_entry['antinuke_enabled'] = antinuke_entry.get('antinuke_enabled', '').lower() == 'true'

        return antinuke_entry
    
class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    @commands.group(name='Whitelist', aliases=['wl'])
    async def _whitelist(self, ctx: commands.Context):
        if ctx.subcommand_passed is None:
            embed = discord.Embed(
                title="Whitelist Command Help",
                description="Here are the available subcommands for the whitelist command:",
                color=discord.Color.blue()
            )
            embed.add_field(name="Whitelist add [user]", value="Adds a member to the whitelist", inline=False)
            embed.add_field(name="Whitelist remove [user]", value="Removes a member from the whitelist", inline=False)
            embed.add_field(name="Whitelist show", value="Shows members in the whitelist", inline=False)
            embed.set_thumbnail(url=self.bot.user.avatar.url)
            embed.set_footer(
                text=f"Requested By {ctx.author}",
                icon_url=ctx.author.avatar.url)
            await ctx.send(embed=embed)

    
    @commands.group(name='antinuke', aliases=['security'])
    async def _antinuke(self, ctx: commands.Context):
        if ctx.subcommand_passed is None:
            await ctx.send("Command usage: `$antinuke setup`")
    
    def load_antinuke_data(self, guild_id):
        with open(antinuke, "r") as file:
            antinuke_data = json.load(file)
        antinuke_entry = antinuke_data.get(str(guild_id), {})
        return antinuke_entry


    @_antinuke.command(name="antinuke disable",aliases=['off'])
    async def disable(self, ctx):
        antinuke_file_path = "./Database/antinuke.json"
        guild_id = ctx.guild.id

      
        with open(antinuke_file_path, "r") as file:
            antinuke_data = json.load(file)

       
        antinuke_enabled = antinuke_data.get(str(guild_id), {}).get("antinuke_enabled", False)

        embed = discord.Embed(
            title="Antinuke Disable",
            color=discord.Color.blurple()
        )

        if not antinuke_enabled:
            embed.add_field(name="Status", value="Antinuke is already disabled", inline=False)
        else:
            # Set antinuke_enabled to False for the guild
            antinuke_data[str(guild_id)]["antinuke_enabled"] = False
            antinuke_data[str(guild_id)]["mode"] = "none"  # Set mode to "none"

            # Write the updated data back to the JSON file
            with open(antinuke_file_path, "w") as file:
                json.dump(antinuke_data, file, indent=4)

            embed.add_field(name="Status", value="Antinuke has been disabled", inline=False)

        await ctx.send(embed=embed)

        await ctx.send(embed=embed)
    @_antinuke.command(name="check_antinuke_status")
    async def status(self, ctx):
        antinuke_data = self.load_antinuke_data(ctx.guild.id)
        antinuke_enabled = antinuke_data.get("antinuke_enabled", False)

        embed = discord.Embed(
            title="Antinuke Status",
            color=discord.Color.blurple()
        )

        if antinuke_enabled:
            embed.add_field(name="Status", value="Antinuke is currently enabled", inline=False)
        else:
            embed.add_field(name="Status", value="Antinuke is currently disabled", inline=False)

        await ctx.send(embed=embed)


    @_antinuke.command(name='setup', aliases=['enable'])
    async def _setup(self, ctx):
        antinuke_data = self.load_antinuke_data(ctx.guild.id)
        antinuke_enabled = antinuke_data.get("antinuke_enabled", False)

        embed = discord.Embed(color=discord.Color.blurple(), title="Arch Antinuke Setup")

        if antinuke_enabled:
            embed.title = "Antinuke Already Enabled"
            embed.description = "Antinuke is already enabled."
        else:
            embed.description = ":wrench: Initializing Arch Antinuke Setup!"
            message = await ctx.send(embed=embed)

            await asyncio.sleep(2)

            tasks = [
                "Checking for bot permissions.",
                "Checking bot role position.",
                "Setting up Jail role across all channels.",
                "Ensuring the Jail role is placed correctly.",
                "Creating The Arch role.",
                "Setting up Antinuke logging."
            ]

            for index, task in enumerate(tasks):
                embed.description += f"\n:white_check_mark: {task}"
                await message.edit(embed=embed)
                await asyncio.sleep(2)

            embed.description += "\n:white_check_mark: All tasks completed!"  # Add a final completion message
            view = discord.ui.View()
            view.add_item(SetupButton(self.bot, label="Secure", custom_id="secure_setup"))
            view.add_item(SetupButton(self.bot, label="Beast", custom_id="beast_setup"))
            view.add_item(SetupButton(self.bot, label="Disable", custom_id="no_setup"))
            await message.edit(embed=embed, view=view)

            await asyncio.sleep(2)
            embed.description = "Ready to start the setup process! :thumbsup:"

            # Set antinuke_enabled flag to True in the antinuke data
            antinuke_data["antinuke_enabled"] = True
            file_path = "./Database/antinuke.json"  # File path for antinuke data
            try:
                with open(file_path, "w") as file:
                    json.dump(antinuke_data, file, indent=4)
            except Exception as e:
                print(f"Error saving antinuke data: {e}")
                embed.description = "Error enabling Antinuke: Failed to save data."
            
        await ctx.send(embed=embed)





    @commands.command()
    async def add_extra_owner(self, ctx, user: discord.Member):
        if ctx.author.guild_permissions.administrator or ctx.author == ctx.guild.owner or ctx.author.id == self.bot.user.id:
            guild_id = str(ctx.guild.id)
            with open(antinuke, "r") as file:
                antinuke_data = json.load(file)
            if guild_id in antinuke_data:
                extra_owners = antinuke_data[guild_id].get("extra_owners", [])
                if len(extra_owners) < 2:
                    if user.id not in extra_owners:
                        extra_owners.append(user.id)
                        antinuke_data[guild_id]["extra_owners"] = extra_owners
                        with open(antinuke, "w") as file:
                            json.dump(antinuke_data, file, indent=4)
                        await ctx.send(f"{user.name}#{user.discriminator} has been added as an extra owner.")
                    else:
                        await ctx.send(f"{user.name}#{user.discriminator} is already an extra owner.")
                else:
                    await ctx.send("Only two members can be added as extra owners.")
            else:
                await ctx.send("Antinuke is not enabled for this server.")
        else:
            await ctx.send("You don't have permission to use this command.")

    @commands.command()
    async def remove_extra_owner(self, ctx, user: discord.Member):
        if ctx.author.guild_permissions.administrator or ctx.author == ctx.guild.owner or ctx.author.id == self.bot.user.id:
            guild_id = str(ctx.guild.id)
            with open(antinuke, "r") as file:
                antinuke_data = json.load(file)
            if guild_id in antinuke_data:
                extra_owners = antinuke_data[guild_id].get("extra_owners", [])
                if user.id in extra_owners:
                    extra_owners.remove(user.id)
                    antinuke_data[guild_id]["extra_owners"] = extra_owners
                    with open(antinuke, "w") as file:
                        json.dump(antinuke_data, file, indent=4)
                    await ctx.send(f"{user.name}#{user.discriminator} has been removed from extra owners.")
                else:
                    await ctx.send(f"{user.name}#{user.discriminator} is not an extra owner.")
            else:
                await ctx.send("Antinuke is not enabled for this server.")
        else:
            await ctx.send("You don't have permission to use this command.")

    @_whitelist.command(name="add", aliases=['wl_add'])
    async def add_to_whitelist(self, ctx, user: discord.User):
        if ctx.author.guild_permissions.administrator or ctx.author == ctx.guild.owner or ctx.author.id == self.bot.user.id:
            guild_id = str(ctx.guild.id)
            with open(antinuke, "r") as file:
                antinuke_data = json.load(file)
            if guild_id in antinuke_data:
                whitelist = antinuke_data[guild_id].get("whitelist", [])
                if user.id not in whitelist:
                    whitelist.append(user.id)
                    antinuke_data[guild_id]["whitelist"] = whitelist
                    with open(antinuke, "w") as file:
                        json.dump(antinuke_data, file, indent=4)
                    await ctx.send(f"{user.name}#{user.discriminator} has been added to the whitelist.")
                else:
                    await ctx.send(f"{user.name}#{user.discriminator} is already in the whitelist.")
            else:
                await ctx.send("Antinuke is not enabled for this server.")
        else:
            await ctx.send("You don't have permission to use this command.")

    @_whitelist.command(name="remove", aliases=['wl_remove'])
    async def remove_from_whitelist(self, ctx, user: discord.User):
        if ctx.author.guild_permissions.administrator or ctx.author == ctx.guild.owner or ctx.author.id == self.bot.user.id:
            guild_id = str(ctx.guild.id)
            with open(antinuke, "r") as file:
                antinuke_data = json.load(file)
            if guild_id in antinuke_data:
                whitelist = antinuke_data[guild_id].get("whitelist", [])
                if user.id in whitelist:
                    whitelist.remove(user.id)
                    antinuke_data[guild_id]["whitelist"] = whitelist
                    with open(antinuke, "w") as file:
                        json.dump(antinuke_data, file, indent=4)
                    await ctx.send(f"{user.name}#{user.discriminator} has been removed from the whitelist.")
                else:
                    await ctx.send(f"{user.name}#{user.discriminator} is not in the whitelist.")
            else:
                await ctx.send("Antinuke is not enabled for this server.")
        else:
            await ctx.send("You don't have permission to use this command.")

    @_whitelist.command(name="show", aliases=['wl_show'])
    async def show_whitelist(self, ctx):
        if ctx.author.guild_permissions.administrator or ctx.author == ctx.guild.owner or ctx.author.id == self.bot.user.id:
            guild_id = str(ctx.guild.id)
            with open(antinuke, "r") as file:
                antinuke_data = json.load(file)
            if guild_id in antinuke_data:
                whitelist = antinuke_data[guild_id].get("whitelist", [])
                if whitelist:
                    member_mentions = [f"<@{uid}>" for uid in whitelist]
                    await ctx.send(f"Whitelisted members: {', '.join(member_mentions)}")
                else:
                    await ctx.send("The whitelist is empty.")
            else:
                await ctx.send("Antinuke is not enabled for this server.")
        else:
            await ctx.send("You don't have permission to use this command.")

async def setup(bot):
    await bot.add_cog(Setup(bot))