"""
Created by Vizitiu Valentin Iulian
11 Nov 2022

JediGames Master Game Bot for Discord
"""

import discord
import sqlitedict
from dotenv import load_dotenv
import os

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
gem_db = sqlitedict.SqliteDict('databases/gem_db.sqlite', autocommit=True)

# BOT_TOKEN =  os.getenv('JEDI_MASTER_BOT_TOKEN')
BOT_TOKEN = os.getenv('BETA_BOT_TOKEN')  # BETA

EMOJIS = {'amethyst': "<:amethyst:1057313502110425219>",
          'cateye': "<:cateye:1057313504417296405>",
          'diamond': "<:diamond:1057313506829025280>",
          'emerald': "<:emerald:1057313508578033755>",
          'granite': "<:granite:1057313510020890634>",
          'peridot': "<:peridot:1057313513124679741>",
          'ruby': "<:ruby:1057313515112775680>",
          'opal': "<:opal:1057313511413383179>",
          'sapphire': "<:saphhire:1057313516748550224>",
          'quartz': "<:glass_shard:1026197930304082000>"}

GEM_LIST = [i for i in EMOJIS]