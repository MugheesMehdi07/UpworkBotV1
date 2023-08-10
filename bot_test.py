import discord
from discord.ext import commands

intents = discord.Intents.default()  # all events by default

token= 'MTEzNzQ3NDgzMzg2OTk3OTcyOQ.GlP2WW.Can-UoT2Aa4X8Z00S7cuaPU7KJ9zi__a68pWOY'

# If you want to disable an event (for example, reactions), you can do:
# intents.reactions = False

# Instantiate a Bot object
import discord
from discord.ext import commands

intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.command()
async def hello(ctx):
    await ctx.send('Hello!')

bot.run(token)
