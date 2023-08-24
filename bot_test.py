# import discord
# from discord.ext import commands
# import multiprocessing
#
# intents = discord.Intents.default()  # all events by default
# # shared_variable = Value('b', False)
#
# discord_token = 'MTEzNzQ3NDgzMzg2OTk3OTcyOQ.GBfeTV.JlkqAuuMmYY1YXKL7lUnlu8Y7_GMvnL-wx4Hjo'
# flag = multiprocessing.Queue()
# # UpworkBot token
# # If you want to disable an event (for example, reactions), you can do:
# # intents.reactions = False
# # manager = Manager()
# # shared_variable = manager.Value('b', False)
#
# # Instantiate a Bot object
# intents = discord.Intents.all()
# bot = commands.Bot(command_prefix='!', intents=intents)
#
# @bot.event
# async def on_ready():
#     print(f'We have logged in as {bot.user}')
#
# # @bot.command()
# # async def hello(ctx):
# #     global command
# #     print('ctx', ctx)
# #     if ctx == "!start":
# #         command = True
# #         print('ctx', ctx)
# #         await ctx.channel.send('Hello!')
# #     elif ctx == "!stop":
# #         command = False
# #         await ctx.chnnel.send("server stopped.")
#
# @bot.event
# async def on_message(message):
#     print(f'Message content: {message.content}')
#     global flag
#
#
#     # Perform any additional checks or actions based on the message content
#     if message.content.lower() == '!start':
#         flag.put('start')
#         await message.channel.send('Hello!')
#     elif message.content.lower() == '!stop':
#         flag.put('stop')
#         await message.channel.send("server stopped.")
# # def bot_run(token):
# if __name__ == "__main__":
#     bot.run(discord_token)

