import discord
from discord import app_commands
from discord.ui import Button, View
from discord.ext import commands
from database import Database
import config as config
import random
import asyncio
from time import time

game_board = [
    "-", "-", "-",
    "-", "-", "-",
    "-", "-", "-"
]

tie_words = [
    "It seems both tied. What a pity...",
    "It's a tie! .... Oh well",
    "A tie... Ok."
]

symbols = {
    "X": "<:xx:1007415941140848670>",
    "O": "<:oo:1007415897624936458>"
}

button_colors = {
    "X": discord.ButtonStyle.red,
    "O": discord.ButtonStyle.blurple
}

active_games = {}


def fresh_board(
    username,
    user_id
):
    buttons = []
    button_id = 0
    checked_buttons = 0  # How many buttons we have checked
    button_slot = 1  # Where the button is placed

    embed = discord.Embed(
        title="Tic Tac Toe",
        description=(
            f"It is now **{username}**'s turn! ({symbols['X']})\n"
        ),
        color=config.COLOR_EMPTY
    )

    for slot in game_board:
        checked_buttons += 1

        if checked_buttons > 3:
            button_slot += 1
            checked_buttons = 1

        if slot in ["X", "O"]:
            buttons.append(
                Button(
                    emoji=symbols[slot],
                    style=button_colors[slot],
                    row=button_slot,
                    disabled=True
                )
            )

        else:
            buttons.append(
                Button(
                    custom_id=f"tictactoe_{button_id}_{user_id}",
                    emoji="<:empty:1106191081730756649>",
                    style=discord.ButtonStyle.gray,
                    row=button_slot
                )
            )

        button_id += 1  # Adds buttons to the game with their row id

    view = View()
    for button in buttons:
        view.add_item(button)

    return embed, view


def display_winner(
    board,
    winner,
    game_id
):
    """
    Displays the winner of the TicTacToe game
    """

    end_game = False
    checked_buttons = 0  # How many buttons we have checked
    button_slot = 1  # Where the button is placed

    if winner == "X":
        user = list(active_games[game_id]['players'])[0]
        winner = active_games[game_id]['players'][user]["name"]
        end_game = True

        end_game_description = (
            f"**{winner}** Won the game!\n"
        )

    elif winner == "O":
        user = list(active_games[game_id]['players'])[1]
        winner = active_games[game_id]['players'][user]["name"]
        end_game = True

        end_game_description = (
            f"**{winner}** Won the game!\n"
        )

    else:
        end_game = True
        end_game_description = f"{random.choice(tie_words)}"

    if end_game:
        embed = discord.Embed(
            title="Tic Tac Toe",
            description=(
                f"{end_game_description}"
            ),
            color=config.COLOR_EMPTY
        )
        buttons = []

        for slot in board:
            checked_buttons += 1

            if checked_buttons > 3:
                button_slot += 1
                checked_buttons = 1

            if slot in ["X", "O"]:
                buttons.append(
                    Button(
                        emoji=symbols[slot],
                        style=button_colors[slot],
                        row=button_slot,
                        disabled=True
                    )
                )
            else:
                buttons.append(
                    Button(
                        disabled=True,
                        emoji="<:empty:1106191081730756649>",
                        style=discord.ButtonStyle.gray,
                        row=button_slot
                    )
                )

        view = View()
        for button in buttons:
            view.add_item(button)

        active_games.pop(game_id)
        return embed, view


def display_board(
    board,
    player,
    game_id
):
    """Displays the tic tac toe board"""

    checked_buttons = 0  # How many buttons we have checked
    button_slot = 1  # Where the button is placed

    embed = discord.Embed(
        title="Tic Tac Toe",
        description=(
            f"It is now **{active_games[game_id]['players'][player]['name']}**'s turn! "
            f"({symbols[active_games[game_id]['players'][player]['symbol']]})\n"
        ),
        color=config.COLOR_EMPTY
    )

    buttons = []
    button_id = 0

    for slot in board:
        checked_buttons += 1

        if checked_buttons > 3:
            button_slot += 1
            checked_buttons = 1

        if slot in ["X", "O"]:
            buttons.append(
                Button(
                    emoji=symbols[slot],
                    style=button_colors[slot],
                    row=button_slot,
                    disabled=True
                )
            )

        else:
            buttons.append(
                Button(
                    custom_id=f"tictactoe_{button_id}_{player}",
                    emoji="<:empty:1106191081730756649>",
                    style=discord.ButtonStyle.gray,
                    row=button_slot
                )
            )

        button_id += 1  # Adds buttons to the game with their row id

    view = View()
    for button in buttons:
        view.add_item(button)

    return embed, view


def handle_bot_turn(
    board
):
    available_slots = []

    for slot in range(len(board)):
        if board[slot] not in ["X", "O"]:
            available_slots.append(slot)

    combination_checks = [
        [[0, 2], 1],
        [[0, 8], 4],
        [[0, 6], 3],
        [[2, 8], 5],
        [[6, 8], 7],
        [[1, 7], 4],
    ]

    chosen_slot = None

    if 4 in available_slots:
        chosen_slot = 4

    else:
        for check in combination_checks:
            found = True
            for number in check[0]:
                if number in available_slots:
                    found = False
                    break

            if found and check[1] in available_slots:
                chosen_slot = check[1]
                break

    if not chosen_slot:
        chosen_slot = random.choice(available_slots)

    board[chosen_slot] = "O"
    return


def handle_player_turn(
    chosen_slot,
    symbol,
    board
):
    """Handles a players turn"""
    filled = True
    filled = check_if_empty(int(chosen_slot), board)

    if filled is False:
        board[int(chosen_slot)] = symbol

    return filled


def check_if_empty(
    slot,
    board
):
    """We check if the board slot is empty"""

    # If the slot is filled, return True
    if board[int(slot)] not in ["X", "O"]:
        return False

    # Otherwise, we want them to be able to place a piece here
    else:
        return True


# Board Display
# Play game
# Handle turn


def swap_player(
    game_id,
    player
):
    if list(active_games[game_id]["players"])[0] == player:
        active_games[game_id]["players_turn"] = list(active_games[game_id]["players"])[1]

    else:
        active_games[game_id]["players_turn"] = list(active_games[game_id]["players"])[0]

    return active_games[game_id]["players_turn"]


def check_if_filled(
    board
):
    for slot in range(0, len(board)):
        if board[slot] not in ["X", "O"]:
            return False

    return True


def check_for_winner(
    board
):
    # Check rows. If there is a winner, return the winner
    if board[0] == board[1] == board[2] in ["X", "O"]:
        return board[0]

    if board[3] == board[4] == board[5] in ["X", "O"]:
        return board[3]

    if board[6] == board[7] == board[8] in ["X", "O"]:
        return board[6]

    # Check collums
    if board[0] == board[3] == board[6] in ["X", "O"]:
        return board[0]

    if board[1] == board[4] == board[7] in ["X", "O"]:
        return board[1]

    if board[2] == board[5] == board[8] in ["X", "O"]:
        return board[2]

    # Check diagonal [\]
    if board[0] == board[4] == board[8] in ["X", "O"]:
        return board[0]

    # Check diagonal [/]
    if board[2] == board[4] == board[6] in ["X", "O"]:
        return board[2]

    return None


class TicTacToe(
    commands.Cog
):
    """
    AFK COG

    This cog allows users to go AFK on discord.
    The user types /afk and the bot will let anyone who pings them
    know that they are busy, as well as providing the user a link
    to all of these messages when they return.
    """

    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    @commands.Cog.listener()
    async def on_interaction(
        self,
        interaction: discord.Interaction
    ):
        """Detects when a user clicks a button or uses a slash command"""

        try:
            # Ensures that the interaction is a button, and not a slash commabd
            if interaction.type.name != "component":
                return

            user_id = str(interaction.user.id)
            button = interaction.data["custom_id"]

            if interaction.message.id not in active_games:
                return

            if button[0:9] != "tictactoe":
                return

            else:
                await interaction.response.defer()  # Let's discord know we're handling the interaction
                game_id = interaction.message.id

                # Check if it is the users turn
                if active_games[game_id]["players_turn"] != user_id:
                    return

                board = active_games[game_id]["board"]
                button_id = button[10].replace(f"_{user_id}", "")
                await self.process_round(interaction, button_id, game_id, user_id, board)

        except Exception as e:
            print("Issue with on_interaction tictactoe", e)

    async def process_round(self, interaction: discord.Interaction, button_id, game_id, player, board):
        if handle_player_turn(button_id, active_games[game_id]["players"][player]["symbol"], board) is True:
            return

        # Check for a winner, if we have a winner, we end the game
        winner = check_for_winner(board)
        tie = check_if_filled(board)
        active_games[game_id]["last_played"] = time()

        if winner or tie:
            embed, view = display_winner(board, winner, game_id)
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=view)
            return

        player = swap_player(game_id, player)
        embed, view = display_board(board, player, game_id)

        await interaction.followup.edit_message(interaction.message.id, embed=embed, view=view)

        opponent_id = list(active_games[game_id]["players"])[1]
        if active_games[game_id]["players"][opponent_id]["bot"] is True:
            await asyncio.sleep(1)
            handle_bot_turn(board)

            # Check for a winner, if we have a winner, we end the game
            winner = check_for_winner(board)
            tie = check_if_filled(board)
            if winner:
                embed, view = display_winner(board, winner, game_id)
                await interaction.followup.edit_message(interaction.message.id, embed=embed, view=view)
                return

            player = swap_player(game_id, player)
            embed, view = display_board(board, player, game_id)
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=view)

    async def play_game(
        self,
        interaction: discord.Interaction,
        user_id,
        opponent
    ):
        # Display the game board
        await interaction.response.defer()

        if interaction.user.id == opponent.id:
            await interaction.response.send_message("You're really trying to duel yourself. Wow.")

        if opponent.id == self.bot.user.id:
            versus_message = (
                f"**{interaction.user.mention}** vs **Me, {self.bot.user.mention}!**\n\n"
            )

        else:
            versus_message = f"**{interaction.user.mention}** vs **{opponent.mention}**"

        embed, view = fresh_board(interaction.user.name, user_id)
        msg = await interaction.followup.send(
            versus_message,
            embed=embed,
            view=view
        )

        active_games[msg.id] = {
            "players": {
                user_id: {
                    "bot": False,
                    "symbol": "X",
                    "name": interaction.user
                },
                str(opponent.id): {
                    "bot": opponent.bot,
                    "symbol": "O",
                    "name": opponent
                }
            },
            "players_turn": user_id,
            "board": game_board.copy(),
            "last_played": time()
        }

    @app_commands.command(
        name="tictactoe",
        description="Play a fun game of TIC TAC TOE!"
    )
    async def tictactoe(
        self,
        interaction: discord.Interaction,
        opponent: discord.User
    ):
        await self.play_game(interaction, str(interaction.user.id), opponent)


async def setup(bot):
    await bot.add_cog(TicTacToe(bot))
