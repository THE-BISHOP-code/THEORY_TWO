# commands/premium/channel_create_command.py
import discord
async def execute(interaction, bot, args):
  name=args.get('name','new-channel')
  print(f'Simulating channel create: {name}')
  # await interaction.guild.create_text_channel(name=name)
