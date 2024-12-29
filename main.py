import discord
from discord import app_commands
from discord.ext import tasks
from discord.ext import commands
from datetime import timedelta
import FileHandling
from siegeapi import Auth
import asyncio
import requests
import os
import math

async def CheckIfAccount(Platform, Username):
    auth = Auth("UBISOFTEMAIL", "UBISOFTPASSWORD")
    try:
        print(Username)
        player = await auth.get_player(name=Username, platform=Platform)
        await auth.close()
        return player.profile_pic_url
    except Exception as e:
        print(e)
        await auth.close()
        return False
    
async def GetAccountStats(Username, Platform):
    auth = Auth("UBISOFTEMAIL", "UBISOFTPASSWORD")
    UserData = {}
    try:
        player = await auth.get_player(name=Username, platform=Platform)
        UserData["Name"] = player.name
        UserData["PFP"] = player.profile_pic_url

        await player.load_ranked_v2()
        UserData["RP"] = player.ranked_profile.rank_points
        UserData["Rank"] = player.ranked_profile.rank
        UserData["Kills"] = player.ranked_profile.kills
        UserData["Deaths"] = player.ranked_profile.deaths
        if not (player.ranked_profile.deaths == 0):
            UserData["KD"] = round(player.ranked_profile.kills/player.ranked_profile.deaths, 2)
        else:
            UserData["KD"] = player.ranked_profile.kills
        if not (player.ranked_profile.wins + player.ranked_profile.losses == 0):
            UserData["WinRate"] = round(player.ranked_profile.wins / (player.ranked_profile.wins + player.ranked_profile.losses), 2) * 100
        else:
            UserData["WinRate"] = 0
        await auth.close()
        return UserData

    except Exception as e:
        print(e)
        print("Not User")
        await auth.close()
        return UserData


intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

token = ""
with open(os.path.join("token.txt"), "r") as tokenFile:
    token = tokenFile.read()

@tasks.loop(minutes=2)
async def CheckStats():
    Servers = FileHandling.GetAllSiegeServers()
    try:
        for server in Servers:
            UserList = []
            for user in server["Users"]:
                UserList.append(await GetAccountStats(user["Username"], user["Platform"]))
        
            UserList.sort(key=lambda x: x["RP"], reverse=True)
            if not(UserList == server["RankedLeaderboard"]):
                server["RankedLeaderboard"] = UserList
                Path = os.path.join("Servers", server["Server"], "siege.json")
                try:
                    with open(Path, "w") as ServerFile:
                        ServerFile.write(str(server))
                except:
                    print("Error Occured")
                MessageChannel = bot.get_channel(int(server["Post"]))
                if(MessageChannel):
                    embed = discord.Embed(title=f"Siege Leaderboard", color=int("7fff7c", 16))
                    for rank, user in enumerate(UserList):
                        embed.add_field(name=f"{rank+1}. {user["Name"]}", value=f"RP: {user["RP"]}\nRank: {user["Rank"]}\nKills: {user["Kills"]}\nDeaths: {user["Deaths"]}\nKD: {user["KD"]}\nWinRate: {user["WinRate"]}", inline=False)
                        if(rank+1 == 1):
                            embed.set_thumbnail(url=str(user["PFP"]))
                    embed.set_footer(text="This data is provided by siegeapi.")
                    await MessageChannel.send(embed=embed)
    except Exception as e:
        print(e)


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    try:
        synced = await bot.tree.sync()  # Sync the commands with Discord
        CheckStats.start()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)

@bot.tree.command(name="setup_siege", description="Set up your channel for posting and registering for Rainbow Six Siege.")
async def setup_siege(interaction: discord.Interaction, post_channel:discord.TextChannel, register_channel:discord.TextChannel):
    if not (interaction.user.guild_permissions.administrator):
        embed = discord.Embed(title="Only administrators can use this command.", color=int("ce0000", 16))
        embed.set_footer(text="Please contact an admin on the server to setup Siege.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    ServerID = interaction.guild.id
    Type = "siege"
    SetupData = {
        "Server":str(interaction.guild.id),
        "Post":str(post_channel.id),
        "Register":str(register_channel.id),
        "RankedLeaderboard":{}
    }
    FileHandling.SaveSetup(ServerID, Type, SetupData)
    embed = discord.Embed(title="Setup Complete!", color=int("7fff7c", 16))
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="register_siege", description="Register to be on the leaderboard for Stat Falcon.")
@app_commands.describe(platform="Select the platform that your Siege account is on.")
@app_commands.choices(
    platform=[
        app_commands.Choice(name="Ubisoft", value="uplay"),
        app_commands.Choice(name="Xbox", value="xbl"),
        app_commands.Choice(name="PlayStation", value="psn")
    ]
)
async def register_siege(interaction: discord.Interaction, platform:str, username:str):
    ServerID = str(interaction.guild.id)
    channeID = str(interaction.channel.id)
    SetUpData = FileHandling.GetSetup(ServerID, "siege")
    if(SetUpData == "NotSetup"):
        embed = discord.Embed(title="Siege is not setup on this server.", color=int("ce0000", 16))
        embed.set_footer(text="Please contact an admin on the server to setup Siege.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    else:
        if (channeID == SetUpData["Register"]):
            CheckAccountData = await CheckIfAccount(platform, username)
            if not (CheckAccountData == False):
                print(platform)
                FileHandling.SaveRegisterSiege(ServerID, platform, username, interaction.user.id)
                embed = discord.Embed(title=f"{username} is now registered!", color=int("7fff7c", 16))
                print(CheckAccountData)
                embed.set_image(url=CheckAccountData)
                await interaction.response.send_message(embed=embed)
            else:
                embed = discord.Embed(title=f"{username} is not a valid user on your selected platform.", color=int("ce0000", 16))
                embed.set_footer(text="Make sure you selected the correct username and platform.")
                await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(title="This is not the regiser channel for siege. Please use your server's register channel.", color=int("ce0000", 16))
            embed.set_footer(text="If you need help, contact a moderator on your server.")
            await interaction.response.send_message(embed=embed, ephemeral=True)


bot.run(token)