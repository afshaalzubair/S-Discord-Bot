import discord
import random
import asyncpraw
import json
import asyncio
from discord.ext import commands, tasks
from itertools import cycle

def get_prefix(client, message):
    with open('prefixes.json', 'r') as f:
        prefixes = json.load(f)
    return prefixes[str(message.guild.id)]


intents = discord.Intents(messages = True, guilds = True, reactions = True, members = True, presences = True)
client = commands.Bot(command_prefix = get_prefix, intents = intents)
status = cycle([])
filtered_words = ['']
reddit = asyncpraw.Reddit(client_id = "",
                     client_secret = "",
                     username = "",
                     password = "",
                     user_agent = "")

### Processes

@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.online)
    change_status.start()
    print("Bot ready.")

@tasks.loop(seconds=4)
async def change_status():
    await client.change_presence(activity=discord.Game(next(status)))

@client.event
async def on_member_join(member):
    print(f'{member} has joined a server.')

@client.event
async def on_member_remove(member):
    print(f'{member} has left a server.')

@client.event
async def on_message(msg):
    for word in filtered_words:
        if word in msg.content:
            await msg.delete()
    await client.process_commands(msg)

### Regular Commands

@client.command()
async def ping(ctx):
    await ctx.send(f'Pong! {round(client.latency * 1000)}ms')

@client.command()
async def flushed(ctx):
    await ctx.send("😳")
    await ctx.message.delete()

@client.command()
@commands.has_permissions(administrator=True)
async def speak(ctx, *, input):
    await ctx.send(input)
    await ctx.message.delete()
@speak.error
async def speak_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('You are not eligible to use this command.')

@client.command(aliases=['8ball'])
async def _8ball(ctx, *, question):
    responses = ["It is certain.",
                "It is decidedly so.",
                "Without a doubt.",
                "Yes - definitely.",
                "You may rely on it.",
                "As I see it, yes.",
                "Most likely.",
                "Outlook good.",
                "Yes.",
                "Signs point to yes.",
                "Reply hazy, try again.",
                "Ask again later.",
                "Better not tell you now.",
                "Cannot predict now.",
                "Concentrate and ask again.",
                "Don't count on it.",
                "My reply is no.",
                "My sources say no.",
                "Outlook not so good.",
                "Very doubtful."]
    await ctx.send(f'Question: {question}\nAnswer: {random.choice(responses)}')

### Prefixes

@client.event
async def on_guild_join(guild):
    with open('prefixes.json', 'r') as f:
        prefixes = json.load(f)

    prefixes[str(guild.id)] = '.'

    with open('prefixes.json', 'w') as f:
        json.dump(prefixes, f, indent=4)

@client.event
async def on_guild_remove(guild):
    with open('prefixes.json', 'r') as f:
        prefixes = json.load(f)

    prefixes.pop(str(guild.id))

    with open('prefixes.json', 'w') as f:
        json.dump(prefixes, f, indent=4)

@client.command()
@commands.has_permissions(administrator=True)
async def changeprefix(ctx, prefix):
    with open('prefixes.json', 'r') as f:
        prefixes = json.load(f)

    prefixes[str(ctx.guild.id)] = prefix

    with open('prefixes.json', 'w') as f:
        json.dump(prefixes, f, indent=4)

    embed = discord.Embed(description=f'Prefix changed to: {prefix}', color=discord.Color.red())
    await ctx.send(embed=embed)

### Error and Moderation

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        embed = discord.Embed(description="Invalid command used.", color=discord.Color.red())
        await ctx.send(embed=embed)

@client.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount : int):
    await ctx.channel.purge(limit=amount)
@clear.error
async def clear_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Please specify an amount of messages to delete.')
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('You are not eligible to use this command.')

@client.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member : commands.MemberConverter, *, reason=None):
    await member.kick(reason=reason)
@kick.error
async def kick_error(ctx, error):
    if isinstance(error, commands.MemberNotFound):
        await ctx.send('Please specify the correct user.')
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('You are not eligible to use this command.')

@client.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member : commands.MemberConverter, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f'Banned {member.mention}')
@ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.MemberNotFound):
        await ctx.send('Please specify the correct user.')
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('You are not eligible to use this command.')

@client.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, *, member):
    banned_users = await ctx.guild.bans()
    member_name, member_discriminator = member.split('#')
    for ban_entry in banned_users:
        user = ban_entry.user
        if (user.name, user.discriminator) == (member_name, member_discriminator):
            await ctx.guild.unban(user)
            await ctx.send(f'Unbanned {user.mention}')
            return
@unban.error
async def unban_error(ctx, error):
    if isinstance(error, commands.MemberNotFound):
        await ctx.send('Please specify the correct user.')
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('You are not eligible to use this command.')

### Embeds

@client.command(aliases=['user', 'info'])
@commands.has_permissions(kick_members=True)
async def whois(ctx, member : discord.Member):
    embed = discord.Embed(title = member.name, description = member.mention, color = discord.Color.red())
    embed.add_field(name = 'ID', value = member.id, inline = True)
    embed.set_thumbnail(url = member.avatar_url)
    embed.set_footer(icon_url = ctx.author.avatar_url, text = f"Requested by {ctx.author.name}")
    await ctx.send(embed=embed)

@client.command()
async def poll(ctx, *, msg):
    channel = ctx.channel
    try:
        op1, op2 = msg.split("or")
        txt = f"React with the preferred option below.\n\n ✅ for {op1}\n\n or \n\n❌ for {op2}"
    except:
        await channel.send("Correct Syntax: [Choice 1] or [Choice 2]")
        return
    embed = discord.Embed(title = "Poll", description = txt, color = discord.Color.red())
    embed.set_footer(icon_url=ctx.author.avatar_url, text=f"Requested by {ctx.author.name}")
    message_ = await channel.send(embed=embed)
    await message_.add_reaction("✅")
    await message_.add_reaction("❌")
    await ctx.message.delete()

@client.command()
async def keywordtest(ctx, keyword):
    if keyword == "iron":
        embed = discord.Embed(title="Iron",color=discord.Color.teal())
        embed.set_image(url="https://cdn.discordapp.com/attachments/872658858017951837/875600985714737203/iron.PNG")
        await ctx.send(embed=embed)
    elif keyword == "silver":
        embed = discord.Embed(title="Silver",color=discord.Color.teal())
        embed.set_image(url="https://cdn.discordapp.com/attachments/872658858017951837/875601010444369950/silver.PNG")
        await ctx.send(embed=embed)
    elif keyword == "wolfram":
        embed = discord.Embed(title="Wolfram",color=discord.Color.teal())
        embed.set_image(url="https://cdn.discordapp.com/attachments/872658858017951837/875601035333345330/wolfram.PNG")
        await ctx.send(embed=embed)
    elif keyword == "gold":
        embed = discord.Embed(title="Gold",color=discord.Color.teal())
        embed.set_image(url="https://cdn.discordapp.com/attachments/872658858017951837/875601055642177556/gold.PNG")
        await ctx.send(embed=embed)
    elif keyword == "rosegold":
        embed = discord.Embed(title="Rosegold",color=discord.Color.teal())
        embed.set_image(url="https://cdn.discordapp.com/attachments/872658858017951837/875601095500627978/rosegold.PNG")
        await ctx.send(embed=embed)
    elif keyword == "cobalt":
        embed = discord.Embed(title="Cobalt",color=discord.Color.teal())
        embed.set_image(url="https://cdn.discordapp.com/attachments/872658858017951837/875601111107657808/cobalt.PNG")
        await ctx.send(embed=embed)
    elif keyword == "platinum":
        embed = discord.Embed(title="Platinum",color=discord.Color.teal())
        embed.set_image(url="https://cdn.discordapp.com/attachments/872658858017951837/875601147967189032/platinum.PNG")
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="Keyword Error", description="Please make sure you have input a valid keyword.\n Please click [here](https://www.youtube.com/watch?v=dQw4w9WgXcQ) if you believe there is an issue.", color=discord.Color.red())
        await ctx.send(embed=embed)

### Reddit

@client.command()
async def meme(ctx, subred = "memes"):
    msg = await ctx.send("Loading meme...")
    subreddit = await reddit.subreddit(subred)
    all_subs = []

    top = subreddit.top(limit=350)

    async for submission in top:
        all_subs.append(submission)

    random_sub = random.choice(all_subs)

    name = random_sub.title
    url = random_sub.url

    embed = discord.Embed(title=f'__{name}__', color=discord.Color.random(), timestamp=ctx.message.created_at, url=url)
    embed.set_image(url=url)
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
    embed.set_footer(text='Here is your meme!', icon_url=ctx.guild.icon_url)
    await ctx.send(embed=embed)
    await msg.edit(content=f'<https://reddit.com/r/{subred}/> :white_check_mark:')
    return

### React Roles

@client.command()
async def reactrole(ctx, emoji, role: discord.Role, *, message):
    embed = discord.Embed(description=message)
    msg = await ctx.channel.send(embed=embed)
    await msg.add_reaction(emoji)

    with open('reactrole.json') as json_file:
        data = json.load(json_file)

        new_react_role = {
            'role_name':role.name,
            'role_id':role.id,
            'emoji':emoji,
            'message_id':msg.id
        }

        data.append(new_react_role)

    with open('reactrole.json', 'w') as j:
        json.dump(data,j,indent=4)

@client.event
async def on_raw_reaction_add(payload):
    if payload.member.bot:
        pass
    else:
        with open('reactrole.json') as react_file:
            data = json.load(react_file)
            for x in data:
                if x['emoji'] == payload.emoji.name and x['message_id'] == payload.message_id:
                    role = discord.utils.get(client.get_guild(payload.guild_id).roles, id=x['role_id'])
                    await payload.member.add_roles(role)

@client.event
async def on_raw_reaction_remove(payload):
    with open('reactrole.json') as react_file:
        data = json.load(react_file)
        for x in data:
            if x['emoji'] == payload.emoji.name and x['message_id'] == payload.message_id:
                role = discord.utils.get(client.get_guild(payload.guild_id).roles, id=x['role_id'])
                await client.get_guild(payload.guild_id).get_member(payload.user_id).remove_roles(role)

### Giveaway

def convert(time):
    pos = ["s", "m", "h", "d"]
    time_dict = {"s" : 1, "m" : 60, "h" : 3600, "d" : 3600*24}
    unit = time[-1]
    if unit not in pos:
        return -1
    try:
        val = int(time[:-1])
    except:
        return -2
    return val * time_dict[unit]

@client.command()
@commands.has_permissions(administrator=True)
async def giveaway(ctx):
    embed = discord.Embed(title = "Giveaway!", description = "Let's start with this giveaway! Answer these questions within 15 seconds!", color = discord.Color.green())
    await ctx.send(embed=embed)
    questions = ["Which channel should it be hosted in?",
                 "What should be the duration of the giveaway? (s|m|h|d)",
                 "What is the prize of the giveaway?"]
    answers = []

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    for i in questions:
        embed = discord.Embed(description = i, color = discord.Color.blue())
        await ctx.send(embed=embed)

        try:
            msg = await client.wait_for("message", timeout=15.0, check=check)
        except asyncio.TimeoutError:
            embed = discord.Embed(description = "You didn't answer in time, please be quicker next time!", color = discord.Color.red())
            await ctx.send(embed=embed)
            return
        else:
            answers.append(msg.content)

    try:
        c_id = int(answers[0][2:-1])
    except:
        embed = discord.Embed(description = f"You didn't mention a channel properly. Do it like this {ctx.channel.mention} next time.",color = discord.Color.red())
        await ctx.send(embed=embed)
        return

    channel = client.get_channel(c_id)

    time = convert(answers[1])
    if time == -1:
        embed = discord.Embed(description = "You didn't answer the time with a proper unit. Use (s|m|h|d) next time.", color = discord.Color.red())
        await ctx.send(embed=embed)
        return
    elif time == -2:
        embed = discord.Embed(description = "The time must be an integer. Please enter an integer next time", color = discord.Color.red())
        await ctx.send(embed=embed)
        return

    prize = answers[2]
    embed = discord.Embed(description = f"The Giveaway will be in {channel.mention} and will last {answers[1]}!", color = discord.Color.blue())
    await ctx.send(embed=embed)

    embed = discord.Embed(title = "Giveaway!", description = f"{prize}", color = discord.Color.green())
    embed.add_field(name = "Hosted by:", value = ctx.author.mention)
    embed.set_footer(text = f"Ends {answers[1]} from now!")
    my_msg = await channel.send(embed=embed)
    await my_msg.add_reaction("🎉")
    await asyncio.sleep(time)

    new_msg = await channel.fetch_message(my_msg.id)

    users = await new_msg.reactions[0].users().flatten()
    users.pop(users.index(client.user))

    winner = random.choice(users)
    await channel.send(f"Congratulations! {winner.mention} won {prize}!")

@client.command()
@commands.has_permissions(administrator=True)
async def reroll(ctx, channel : discord.TextChannel, id_ : int):
    try:
        new_msg = await channel.fetch_message(id_)
    except:
        embed = discord.Embed(description = "The ID was entered incorrectly.", color = discord.Color.red())
        await ctx.send(embed=embed)
        return

    users = await new_msg.reactions[0].users().flatten()
    users.pop(users.index(client.user))

    winner = random.choice(users)
    await channel.send(f"Congratulations! {winner.mention} won!")

### Run

client.run()
