import os
import sys
import json
import asyncio
import discord
from discord.ext import commands
from discord.ui import Select, View, Button
from bot.game import UNOGame
from bot.player import Player
from bot.card import UNOCard
from typing import Optional
import logging
logging.basicConfig(level=logging.DEBUG)

with open("token.txt", "r") as f:
    token = f.read()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="u!", intents=intents)

games = {}

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        with open("restart_context.json", "r") as f:
            data = json.load(f)
        channel = bot.get_channel(data["channel_id"])
        if channel:
            requester = await bot.fetch_user(data["requester_id"])
            embed = discord.Embed(
                title="✅ Restart Successful",
                description="The bot has successfully restarted!",
                color=0x00ff00
            )
            embed.set_footer(text=f"Requested by {requester.display_name}", 
                             icon_url=requester.display_avatar.url)
            await channel.send(embed=embed)
        os.remove("restart_context.json")
    except FileNotFoundError:
        pass

@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    embed = discord.Embed(
        title="🏓 Pong!",
        description="I'm alive and kicking!",
        color=0x00ff00
    )
    embed.add_field(name="📶 Latency:", value=f"⚡ {latency} ms", inline=False)
    embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command()
@commands.is_owner()
async def restart(ctx):
    data = {"channel_id": ctx.channel.id, "requester_id": ctx.author.id}
    with open("restart_context.json", "w") as f:
        json.dump(data, f)
    embed = discord.Embed(
        title="🔄 Restarting",
        description="Bot is restarting...",
        color=0xffd700
    )
    embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)
    await bot.close()
    os.execv(sys.executable, ['python'] + sys.argv)
    
@bot.command()
async def create(ctx):
    if ctx.channel.id in games:
        await ctx.send("A game is already running in this channel! Only one game per channel is allowed.")
        return
    game = UNOGame()
    games[ctx.channel.id] = game
    game.add_player(0, ctx.author.name)
    game.creator = ctx.author
    await ctx.channel.send(f"🎲 {ctx.author.mention} has started a new UNO game! Join now using `u!join`.")
    embed = discord.Embed (
        title="UNO Game Created!",
        description="Use `u!join` to enter the game.",
        color=0xff4500
    )
    embed.add_field(name="📜 Game Rules:", value=(
        "• Use `u!join` to enter.\n"
        "• Use `u!start` to begin the game.\n"
        "• Play cards using `u!play <card>`."
    ), inline=False)
    embed.add_field(name="👑 Game Creator:", value=game.creator, inline=False)
    embed.add_field(name="🕹️ Current Players:", value="1 Player (Waiting for more...)\nUse `u!join` to enter the game!", inline=False)
    await ctx.channel.send(embed=embed)

@bot.command()
async def join(ctx):
    if ctx.channel.id not in games:
        await ctx.channel.send("❌ No active UNO game in this channel! Start one using `u!create`.")
        return
    game = games[ctx.channel.id]
    if game.creator==ctx.author:
        await ctx.channel.send("⚠️ You are the creator of the game! You are already in the game.")
        return
    if game.game_started:
        await ctx.channel.send("❌ The game has already started! Please wait for the next round.")
        return
    if len(game.players) >= 8:
        await ctx.channel.send("❌ Maximum number of players reached! The game is full.")
        return
    if any(player.id == ctx.author.id for player in game.players):
        await ctx.channel.send(f"⚠️ {ctx.author.mention}, you have already joined the game!")
        return
    game.add_player(len(game.players), ctx.author.name)
    await ctx.send(f"✅ {ctx.author.mention} has joined the game!")
    embed = discord.Embed(
        title="UNO Game Updated!",
        description=f"{ctx.author} has joined the game.",
        color=0xff4500
    )
    embed.add_field(name="📜 Game Rules:", value=(
        "• Use `u!join` to enter.\n"
        "• Use `u!start` to begin the game.\n"
        "• Play cards using `u!play <card>`."
    ), inline=False)
    embed.add_field(name="👑 Game Creator:", value=game.creator, inline=False)
    embed.add_field(name="🕹️ Current Players:", value=f"{len(game.players)} Players\n", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def start(ctx):
    if ctx.channel.id not in games:
        await ctx.send("❌ No active UNO game in this channel! Start one using `u!create`.")
        return
    game = games[ctx.channel.id]
    if game.creator.id != ctx.author.id:
        await ctx.send(f"⚠️ Only the game creator - {game.creator.mention} can start the game.")
        return
    if len(game.players) < 2:
        await ctx.send("❌ At least 2 players are required to start the game.")
        return
    game.game_started = True
    for player in game.players:
        game.deck.shuffle_deck()
        player.hand.extend(game.deck.draw_cards(7))
    game.top_card = game.deck.draw_card()
    while game.top_card.type == "wild":
        game.top_card = game.deck.draw_card()
    game.current_player_index = 0
    game.direction = 1
    game.pending_draws = 0
    
    await ctx.send("🎲 The game has started! Let's play UNO!")
    embed = discord.Embed(title="🎲 UNO Game Started!", description=f"🔵 **{ctx.author} has started the game!**", color=0xff4500)
    embed.add_field(
        name="🎮 Top players",
        value=f"🟢 **{game.players[game.current_player_index].username}** is playing now! \n ⏭️ **{game.players[(game.current_player_index+game.direction)%len(game.players)].username}** will play next.",
        inline=True
    )
    embed.add_field(name=f"🃏 Starting Card: **{game.top_card}**", value="", inline=False)
    file_path = f"cards/{game.top_card.color}{game.top_card.value}.png"
    file = discord.File(file_path, filename="top_card.png")
    embed.set_image(url="attachment://top_card.png")
    embed.set_footer(text="Press on **`Show Hand`** button and then on the card to play!", icon_url=bot.user.display_avatar.url)
    
    class ShowHand(View):
        def __init__(self, player, game):
            super().__init__()
            self.player = player
            self.game = game
            self.has_drawn = False

        @discord.ui.button(label="Show Hand", style=discord.ButtonStyle.primary)
        async def show_hand(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.name not in [p.username for p in self.game.players]:
                await interaction.response.send_message("You are not in the game!", ephemeral=True)
                return
            player = next((p for p in self.game.players if p.username == interaction.user.name), None)
            hand_buttons = HandButtons(player)
            await interaction.response.send_message("Your hand:", ephemeral=True, view=hand_buttons)

        @discord.ui.button(label="Draw Card", style=discord.ButtonStyle.secondary)
        async def draw_card(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.name not in [p.username for p in self.game.players]:
                await interaction.response.send_message("You are not in the game!", ephemeral=True)
                return
            if self.has_drawn:
                await interaction.response.send_message("You can only draw one card per turn!", ephemeral=True)
                return
            player = next((p for p in self.game.players if p.username == interaction.user.name), None)
            drawn_card = self.game.deck.draw_card()
            player.hand.append(drawn_card)
            self.has_drawn = True
            hand_buttons = HandButtons(player)
            await interaction.response.send_message(f"You drew: {drawn_card}", ephemeral=True, view=hand_buttons)

        @discord.ui.button(label="Pass Turn", style=discord.ButtonStyle.danger)
        async def pass_turn(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.name not in [p.username for p in self.game.players]:
                await interaction.response.send_message("You are not in the game!", ephemeral=True)
                return
            if not self.has_drawn:
                await interaction.response.send_message("You must draw a card before passing!", ephemeral=True)
                return
            embed = discord.Embed(title="🎲 Turn Passed!", description=f"🔵 **{game.players[game.current_player_index].username}** has passed his turn!", color=0xff4500)
            game.next_turn()
            embed.add_field(
                name="🎮 Top Players",
                value=f"🟢 **{game.players[game.current_player_index].username}** is playing now! \n ⏭️ **{game.players[(game.current_player_index+game.direction)%len(game.players)].username}** will play next.",
                inline=True
            )
            embed.add_field(name=f"🃏 Card on board: **{game.top_card}**", value="", inline=False)
            file_path = f"cards/{game.top_card.color}{game.top_card.value}.png"
            file = discord.File(file_path, filename="top_card.png")
            embed.set_image(url="attachment://top_card.png")
            embed.set_footer(text="Use u!play <card> to play your turn!", icon_url=bot.user.display_avatar.url)
            await ctx.send(embed=embed, file=file, view=ShowHand(game.players[game.current_player_index], game))

    class HandButtons(View):
        def __init__(self, player):
            super().__init__()
            self.player = player
            for card in player.hand:
                self.add_item(CardItem(card))

    class CardItem(Button):
        def __init__(self, card):
            super().__init__(style=discord.ButtonStyle.secondary, label=str(card), custom_id=str(card.id))

        async def callback(self, interaction: discord.Interaction):
            card_id = self.custom_id
            player = next((p for p in game.players if p.username == interaction.user.name), None)
            card_played = next((c for c in player.hand if str(c.id) == card_id), None)
            message, valid_flag = game._is_valid_move(card_played, player)
            await interaction.response.send_message(message, ephemeral=True)
            if valid_flag:
                game.top_card = card_played
                headline_text, play_message = game._handle_card_effect(card_played, None)
                chosen_color = None
                if card_played.type == "wild":
                    view = SelectColor()
                    await interaction.response.send_message("Choose a color for the wild card:", view=view, ephemeral=True)
                    await view.wait()
                    chosen_color = view.values[0]
                    headline_text, play_message = game._handle_card_effect(card_played, chosen_color)
                await ctx.send(f"✅ {interaction.user.mention} has played {card_played}!")
                if card_played.value == "+2":
                    next_player = game.players[(game.current_player_index + game.direction) % len(game.players)]
                    counter_cards = [c for c in next_player.hand if c.value == "+2"]
                    if counter_cards:
                        await ctx.send(f"{next_player.username}, you have {game.pending_draws} cards to draw. You can draw {game.pending_draws} cards or play one of your draw+2 card to counter.")
                    else:
                        await ctx.send(f"{next_player.username}, you have no cards to counter. Pick {game.pending_draws} cards.")
                        next_player.hand.extend(game.deck.draw_cards(game.pending_draws))
                        game.pending_draws = 0
                        play_message += f"has drawn {game.pending_draws} cards! It's {game.players[(game.current_player_index+game.direction)%len(game.players)].username}'s turn now."
                if card_played.value == "+4":
                    next_player = game.players[(game.current_player_index + game.direction) % len(game.players)]
                    counter_cards = [c for c in next_player.hand if c.value == "+4"]
                    if counter_cards:
                        await ctx.send(f"{next_player.username}, you have {game.pending_draws} cards to draw. You can draw {game.pending_draws} cards or play one of your wild+4 card to counter.")
                    else:
                        await ctx.send(f"{next_player.username}, you have no cards to counter. Pick {game.pending_draws} cards.")
                        next_player.hand.extend(game.deck.draw_cards(game.pending_draws))
                        game.pending_draws = 0
                        play_message += f"has drawn {game.pending_draws} cards! It's {game.players[(game.current_player_index+game.direction)%len(game.players)].username}'s turn now."
                embed = discord.Embed(title=f"🎲 {headline_text}!", description=f"**✅ {game.players[game.current_player_index].username}** {play_message}", color=0xff4500)
                game.next_turn()
                embed.add_field(
                    name="🎮 Top Players",
                    value=f"🟢 **{game.players[game.current_player_index].username}** is playing now! \n ⏭️ **{game.players[(game.current_player_index+game.direction)%len(game.players)].username}** will play next.",
                    inline=True
                )
                embed.add_field(name=f"🃏 Card Played: **{game.top_card}**", value="", inline=False)
                file_path = f"cards/{game.top_card.color}{game.top_card.value}.png"
                file = discord.File(file_path, filename="top_card.png")
                embed.set_image(url="attachment://top_card.png")
                embed.set_footer(text=f"It's {game.players[(game.current_player_index+game.direction)%len(game.players)].username} turn to play now", icon_url=bot.user.display_avatar.url)
                player.hand.remove(card_played)
                await ctx.send(embed=embed, file=file, view=ShowHand(game.players[game.current_player_index], game))

    class SelectColor(Select):
        def __init__(self):
            options = [
                discord.SelectOption(label="Red", value="red", emoji="🟥"),
                discord.SelectOption(label="Yellow", value="yellow", emoji="🟨"),
                discord.SelectOption(label="Green", value="green", emoji="🟩"),
                discord.SelectOption(label="Blue", value="blue", emoji="🟦")
            ]
            super().__init__(placeholder="Choose a color", min_values=1, max_values=1, options=options)

        async def callback(self, interaction: discord.Interaction):
            self.stop()

    await ctx.send(embed=embed, file=file, view=ShowHand(game.players[game.current_player_index], game))

@bot.command()
async def game(ctx):
    if ctx.channel.id not in games:
        await ctx.send("❌ No active UNO game in this channel! Start one using `u!create`.")
        return
    game = games[ctx.channel.id]
    embed = discord.Embed(
        title="🎲 UNO Game Status",
        description="Here's the current status of the game.",
        color=0xff4500
    )
    embed.add_field(name="👑 Game Creator", value=game.creator, inline=False)
    embed.add_field(name="🕹️ Current Players", value=f"{len(game.players)} Players", inline=False)
    embed.add_field(name="🧑‍🦰 Players", value="\n".join([player.username for player in game.players]), inline=False)
    embed.add_field(name="🎮 Current Turn", value=game.players[game.current_player_index].username, inline=False)
    embed.add_field(name="🃏 Top Card on board", value=f"**{game.top_card}**", inline=False)
    embed.set_footer(text=f"It's {game.players[game.current_player_index].username}'s turn!", icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)
    
@bot.command(aliases=["info", "status", "game_info"])
async def show(ctx, player: discord.Member):
    if ctx.channel.id not in games:
        await ctx.send("❌ No active UNO game in this channel!")
        return
    game = games[ctx.channel.id]
    game_player = next((p for p in game.players if p.username == player.name), None)
    if not game_player:
        await ctx.send(f"⚠️ {game_player} is not in this game!")
        return
    embed = discord.Embed(
        title=f"🃏 {game_player.username}'s Hand",
        description=f"📥 {len(game_player.hand)} cards in hand",
        color=0xff4500
    )
    embed.set_thumbnail(url=player.display_avatar.url)
    embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command()
async def quit(ctx):
    if ctx.channel.id not in games:
        await ctx.send("❌ No active UNO game in this channel!")
        return
    game = games[ctx.channel.id]
    player_index = None
    for i, player in enumerate(game.players):
        if player.username == ctx.author.name:
            player_index = i
            break
    if player_index is None:
        await ctx.send(f"⚠️ {ctx.author.mention}, you are not in the game!")
        return
    game.players.pop(player_index)
    embed = discord.Embed(
        title="🚪 Player Left",
        description=f"{ctx.author} has quit the game.",
        color=0x3498db
    )
    embed.set_thumbnail(url=ctx.author.display_avatar.url)
    embed.set_footer(text=f"{len(game.players)} players remain in the game. The game continues!", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
    await ctx.send(embed=embed)
    if ctx.author.id==game.creator.id:
        if game.players:
            game.creator = game.players[0]
            embed = discord.Embed(
                title="👑 Game Creator Changed!",
                description=f"🚪 {ctx.author} has left the game.\n"
                            f"🎩 **{game.creator.username}** is now the new game creator!",
                color=0xffd700
            )
            embed.set_footer(text="Let's continue the game!")
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="🚨 Game Ended!",
                description=f"⚠️ {ctx.author.mention}, the game creator has quit.\n"
                            f"The game has been canceled due to no remaining players.",
                color=0xff4500
            )
            embed.set_footer(text="Start a new game with u!create!", icon_url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)
            del games[ctx.channel.id]
            return
    if len(game.players) < 2:
        embed = discord.Embed(
            title="⚠️ Game Canceled",
            description="Not enough players to continue!\nThe game has been automatically canceled.",
            color=0xff4500
        )
        embed.set_footer(text="Start a new game with u!create!", icon_url=bot.user.display_avatar.url)
        await ctx.send(embed=embed)
        del games[ctx.channel.id]
        return

@bot.command()
async def kick(ctx, player: discord.Member):
    if ctx.channel.id not in games:
        await ctx.send("❌ No active UNO game in this channel!")
        return
    game = games[ctx.channel.id]
    if game.creator.id != ctx.author.id:
        await ctx.send(f"⚠️ Only the game creator - {game.creator.mention} can kick players.")
        return
    player_to_kick = next((p for p in game.players if p.username == player.name), None)
    if not player_to_kick:
        await ctx.send(f"⚠️ {player.mention} is not in this game!")
        return
    game.players.remove(player_to_kick)
    embed = discord.Embed(
        title="🚪 Player Kicked",
        description=f"{player.mention} has been kicked from the game due to inactivity.",
        color=0xff4500
    )
    embed.add_field(name="📜 Game Rules:", value=(
        "• Use `u!join` to enter.\n"
        "• Use `u!start` to begin the game.\n"
        "• Play cards using `u!play <card>`."
    ), inline=False)
    embed.add_field(name="👑 Game Creator:", value=game.creator.mention, inline=False)
    embed.add_field(name="🕹️ Current Players:", value=f"{len(game.players)} Players", inline=False)
    embed.set_footer(text=f"Game updated by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)
    if len(game.players) < 2:
        embed = discord.Embed(
            title="⚠️ Game Canceled",
            description="Not enough players to continue!\nThe game has been automatically canceled.",
            color=0xff4500
        )
        embed.set_footer(text="Start a new game with u!create!", icon_url=bot.user.display_avatar.url)
        await ctx.send(embed=embed)
        del games[ctx.channel.id]
        return        

@bot.command(aliases=["end", "abort", "abandon", "stop"])
async def reset(ctx):
    if ctx.channel.id not in games:
        await ctx.send("❌ No active UNO game in this channel!")
        return
    game = games[ctx.channel.id]
    if ctx.author.id != game.creator.id:
        await ctx.send("⚠️ Only the game creator can end the game.")
        return
    del games[ctx.channel.id]  
    embed = discord.Embed(
        title="🚨 Game Ended",
        description=f"The game has been ended by the creator - {game.creator}.",
        color=0xff4500
    )
    embed.set_footer(text="Start a new game with u!create!", icon_url=bot.user.display_avatar.url)
    await ctx.send(embed=embed)

async def main():
    try:
        async with bot:
            await bot.start(token)
    except Exception as e:
        print(f"Error starting bot: {e}")

asyncio.run(main())