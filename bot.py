""" Autor: janek """

import os
import discord
from discord.ext import commands
from datetime import datetime, timedelta
import json

with open("config.json") as config_file:
    config = json.load(config_file)
    TOKEN = config["DISCORD_TOKEN"]

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

account_holder = ""
start_time = None
afk_accounts = {
}

@bot.event
async def on_ready():
    print(f'Bot zalogowany jako {bot.user}')

@bot.command()
async def stawiam_afk(ctx, nick: str):
    if nick in afk_accounts:
        await ctx.send(f'Konto {nick} już jest AFK, postawione przez {afk_accounts[nick][0]}.')
    else:
        afk_accounts[nick] = [ctx.author.name, datetime.now()]
        await ctx.send(f'Konto {nick} zostało postawione AFK przez {ctx.author.name}.')

@bot.command()
async def kto_afk(ctx, nick: str):
    if nick in afk_accounts:
        user, start_time = afk_accounts[nick]
        time_spent = datetime.now() - start_time
        minutes, seconds = divmod(time_spent.total_seconds(), 60)
        await ctx.send(f'Konto {nick} jest AFK od {user} przez {int(minutes)} minut i {int(seconds)} sekund.')
    else:
        await ctx.send(f'Konto {nick} nie jest postawione AFK.')

@bot.command()
async def zdejmij_afk(ctx, nick: str):
    if nick in afk_accounts and afk_accounts[nick][0] == ctx.author.name:
        user, start_time = afk_accounts.pop(nick)
        time_spent = datetime.now() - start_time
        minutes, seconds = divmod(time_spent.total_seconds(), 60)
        await ctx.send(f'{user} zdjął AFK z konta {nick}. Konto było AFK przez {int(minutes)} minut i {int(seconds)} sekund.')
    elif nick in afk_accounts:
        await ctx.send(f'Nie możesz zdjąć AFK z konta {nick}, ponieważ nie jesteś osobą, która je postawiła AFK.')
    else:
        await ctx.send(f'Konto {nick} nie jest postawione AFK.')

@bot.command()
async def wbijam(ctx):
    global account_holder, start_time
    if account_holder:
        await ctx.send(f'{account_holder} już jest na koncie. Musisz poczekać, aż opuści.')
    else:
        account_holder = ctx.author.name
        start_time = datetime.now()  # Zapisuje czas, kiedy osoba dołączyła
        await ctx.send(f'{account_holder} jest teraz na koncie w grze.')

@bot.command()
async def kto(ctx):
    if account_holder:
        time_spent = datetime.now() - start_time
        minutes, seconds = divmod(time_spent.total_seconds(), 60)
        await ctx.send(f'{account_holder} jest teraz na koncie w grze od {int(minutes)} minut i {int(seconds)} sekund.')
    else:
        await ctx.send('Nikt nie jest na koncie w grze.')

@bot.command()
async def wychodze(ctx):
    global account_holder, start_time
    if account_holder == ctx.author.name:
        time_spent = datetime.now() - start_time
        minutes, seconds = divmod(time_spent.total_seconds(), 60)
        await ctx.send(f'{account_holder} wychodzi z konta w grze. Był(a) na koncie przez {int(minutes)} minut i {int(seconds)} sekund.')
        account_holder = ""
        start_time = None
    else:
        await ctx.send(f'Nie możesz wyjść, ponieważ nie jesteś osobą na koncie.')


bot.run(TOKEN)
