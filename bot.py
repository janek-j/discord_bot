import os
import discord
from discord.ext import commands
from datetime import datetime, timedelta
import json
import matplotlib.pyplot as plt
import numpy as np

class UserOnGame:
    def __init__(self, user: str):
        self.account_holder = user
        self.start_time = datetime.now()

    def end_session(self):
        time_spent = datetime.now() - self.start_time
        return time_spent

class AfkManager:
    def __init__(self):
        self.afk_accounts = {}

    def set_afk(self, nick, user):
        if nick not in self.afk_accounts:
            self.afk_accounts[nick] = [user, datetime.now()]
            return True
        return False

    def get_afk(self, nick):
        if nick in self.afk_accounts:
            user, start_time = self.afk_accounts[nick]
            time_spent = datetime.now() - start_time
            return user, time_spent
        return None, None

    def remove_afk(self, nick, user):
        if nick in self.afk_accounts and self.afk_accounts[nick][0] == user:
            start_time = self.afk_accounts.pop(nick)[1]
            time_spent = datetime.now() - start_time
            return time_spent
        return None

class GameSession:
    def __init__(self):
        self.current_user = None
        self.start_time = None
        self.time_spent_file = "time_spent.txt"
        self.check_and_reset_time_file()

    def check_and_reset_time_file(self):
        """Resets the time_spent file if it's a new month."""
        if os.path.exists(self.time_spent_file):
            last_reset = datetime.fromtimestamp(os.path.getmtime(self.time_spent_file))
            if last_reset.month != datetime.now().month:
                with open(self.time_spent_file, 'w') as file:
                    file.write("")  # Clear the file at the start of a new month
        else:
            open(self.time_spent_file, 'w').close()  # Create the file if it doesn't exist

    def record_time_spent(self, user, time_spent):
        if os.path.exists(self.time_spent_file):
            with open(self.time_spent_file, 'r') as file:
                lines = file.readlines()
        else:
            lines = []

        user_found = False
        with open(self.time_spent_file, 'w') as file:
            for line in lines:
                parts = line.strip().split()
                name = parts[0]
                if name == user:
                    user_found = True
                    # Initialize hours, minutes, and seconds to 0
                    hours, minutes, seconds = 0, 0, 0

                    # Iterate over the remaining parts to extract time information
                    for part in parts[1:]:
                        if 'h' in part:
                            hours = int(part.replace('h', ''))
                        elif 'm' in part:
                            minutes = int(part.replace('m', ''))
                        elif 's' in part:
                            seconds = int(part.replace('s', ''))

                    # Add the newly spent time
                    total_seconds = time_spent.total_seconds()
                    seconds += int(total_seconds)
                    minutes += seconds // 60
                    hours += minutes // 60
                    seconds %= 60
                    minutes %= 60

                    # Update the user's time
                    file.write(f"{user} {hours}h {minutes}m {seconds}s\n")
                else:
                    file.write(line)

            if not user_found:
                # If the user is not in the file, add them
                total_seconds = time_spent.total_seconds()
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                file.write(f"{user} {int(hours)}h {int(minutes)}m {int(seconds)}s\n")

    def get_time_series(self, user):
        time_series = []
        if os.path.exists(self.time_spent_file):
            with open(self.time_spent_file, 'r') as file:
                lines = file.readlines()
                for line in lines:
                    parts = line.strip().split()
                    name = parts[0]
                    if name == user:
                        hours, minutes, seconds = 0, 0, 0
                        for part in parts[1:]:
                            if 'h' in part:
                                hours = int(part.replace('h', ''))
                            elif 'm' in part:
                                minutes = int(part.replace('m', ''))
                            elif 's' in part:
                                seconds = int(part.replace('s', ''))
                        total_seconds = hours * 3600 + minutes * 60 + seconds
                        time_series.append(total_seconds)
        return time_series

    def plot_time_series(self, user):
        time_series = self.get_time_series(user)  # Pobranie danych dla danego użytkownika
        if time_series:
            plt.figure(figsize=(10, 5))

            # Przekształcenie czasu na godziny
            times_in_hours = [t / 3600 for t in time_series]

            plt.plot(times_in_hours, marker='o', linestyle='-', color='b', label='Czas spędzony')

            # Ustawienie tytułu i etykiet
            plt.title(f'Czas spędzony na koncie przez {user}')
            plt.xlabel(f'Uzytkownik {user}')
            plt.ylabel('Czas spędzony (godziny)')

            # Ustawienie interwałów co 30 minut (0.5 godziny) na osi y
            max_time = max(times_in_hours) if times_in_hours else 0
            y_ticks = np.arange(0, max_time + 0.5, 0.5)
            plt.yticks(y_ticks)

            plt.grid(True, which='both', linestyle='--', linewidth=0.5)
            plt.tight_layout()  # Dopasowanie układu

            image_path = "time_series.png"
            plt.savefig(image_path)
            plt.close()
            return image_path
        return None

    def start_session(self, user):
        if not self.current_user:
            self.current_user = user
            self.start_time = datetime.now()
            return True
        return False

    def end_session(self, user):
        if self.current_user == user:
            time_spent = datetime.now() - self.start_time
            self.record_time_spent(user, time_spent)
            self.current_user = None
            self.start_time = None
            return time_spent
        return None

    def get_current_session(self):
        if self.current_user:
            time_spent = datetime.now() - self.start_time
            return self.current_user, time_spent
        return None, None

with open("config.json") as config_file:
    config = json.load(config_file)
    TOKEN = config["DISCORD_TOKEN"]

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

afk_manager = AfkManager()
game_session = GameSession()

@bot.event
async def on_ready():
    print(f'Bot zalogowany jako {bot.user}')

@bot.command()
async def stawiam_afk(ctx, nick: str):
    if afk_manager.set_afk(nick, ctx.author.name):
        await ctx.send(f'Konto {nick} zostało postawione AFK przez {ctx.author.name}.')
    else:
        afk_user, _ = afk_manager.get_afk(nick)
        await ctx.send(f'Konto {nick} już jest AFK, postawione przez {afk_user}.')

@bot.command()
async def kto_afk(ctx, nick: str):
    afk_user, time_spent = afk_manager.get_afk(nick)
    if afk_user:
        minutes, seconds = divmod(time_spent.total_seconds(), 60)
        await ctx.send(f'Konto {nick} jest AFK od {afk_user} przez {int(minutes)} minut i {int(seconds)} sekund.')
    else:
        await ctx.send(f'Konto {nick} nie jest postawione AFK.')

@bot.command()
async def zdejmij_afk(ctx, nick: str):
    time_spent = afk_manager.remove_afk(nick, ctx.author.name)
    if time_spent:
        minutes, seconds = divmod(time_spent.total_seconds(), 60)
        await ctx.send(f'{ctx.author.name} zdjął AFK z konta {nick}. Konto było AFK przez {int(minutes)} minut i {int(seconds)} sekund.')
    else:
        afk_user, _ = afk_manager.get_afk(nick)
        if afk_user:
            await ctx.send(f'Nie możesz zdjąć AFK z konta {nick}, ponieważ nie jesteś osobą, która je postawiła AFK.')
        else:
            await ctx.send(f'Konto {nick} nie jest postawione AFK.')

@bot.command()
async def wbijam(ctx):
    if game_session.start_session(ctx.author.name):
        await ctx.send(f'{ctx.author.name} jest teraz na koncie w grze.')
    else:
        current_user, _ = game_session.get_current_session()
        await ctx.send(f'{current_user} już jest na koncie. Musisz poczekać, aż opuści.')

@bot.command()
async def kto(ctx):
    current_user, time_spent = game_session.get_current_session()
    if current_user:
        minutes, seconds = divmod(time_spent.total_seconds(), 60)
        await ctx.send(f'{current_user} jest teraz na koncie w grze od {int(minutes)} minut i {int(seconds)} sekund.')
    else:
        await ctx.send('Nikt nie jest na koncie w grze.')

@bot.command()
async def wychodze(ctx):
    time_spent = game_session.end_session(ctx.author.name)
    if time_spent:
        minutes, seconds = divmod(time_spent.total_seconds(), 60)
        await ctx.send(f'{ctx.author.name} wychodzi z konta w grze. Był(a) na koncie przez {int(minutes)} minut i {int(seconds)} sekund.')
    else:
        await ctx.send(f'Nie możesz wyjść, ponieważ nie jesteś osobą na koncie.')

@bot.command()
async def wykres(ctx, user: str):
    image_path = game_session.plot_time_series(user)
    if image_path:
        await ctx.send(file=discord.File(image_path))
        os.remove(image_path)  # Usuwanie pliku po wysłaniu
    else:
        await ctx.send(f'Brak danych dla użytkownika {user}.')


bot.run(TOKEN)
