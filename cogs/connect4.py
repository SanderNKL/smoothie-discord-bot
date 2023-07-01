import discord
from typing import Literal
from discord import app_commands
from discord.ui import Button, View
from discord.ext import commands, tasks
from database import Database
import config as config
import random
import asyncio
from time import time
import emojis as emojis


active_games = {}

symbols = {
    "-": "<:re:1012432372773425203>",
    "x": "<:rg:1012439244284903424>",
    "o": "<:rr:1012439262442033194>"
}

player_symbols = {
    0: "x",
    1: "o"
}

number_symbols = {
    1: "<:row1:1012432420898865222>",
    2: "<:row2:1012432472136491099>",
    3: "<:row3:1012432506684964904>",
    4: "<:row4:1012432565115830282>",
    5: "<:row5:1012432607574769754>",
    6: "<:row6:1012434685466513539>",
    7: "<:row7:1012434700146581585>",
    8: "<:row8:1012434717053833278>",
    9: "<:row9:1012434751027679342>",
    10: "<:row10:1012435113096794182>",
}

button_colors = {
    "x": discord.ButtonStyle.green,
    "o": discord.ButtonStyle.red,
    "disabled": discord.ButtonStyle.gray
}


def create_board(x_rows=7, y_rows=6):
    """Creates the game board"""

    board = {}
    for y_row in range(0, y_rows):
        board[y_row] = list()
        for x_row in range(0, x_rows):
            board[y_row].append("-")

    return board


def check_horizontal(pieces_in_a_row, board):
    """Checks for X in a row, horizontal"""
    horizontal_rows = dict()

    for y_row in board:
        horizontal_rows[y_row] = list()

        for x_row in board[y_row]:
            horizontal_rows[y_row].append(x_row)

    winning_piece = check_rows(horizontal_rows, pieces_in_a_row)
    return winning_piece


def get_vertical_slots(x_row, y_rows, board):
    row_list = list()

    for y_row in range(y_rows):
        row_list.append(list(board[y_row])[x_row])

    return row_list


def is_slot_filled(number, y_rows, board):
    for slot in get_vertical_slots(number, y_rows, board):
        if slot == "-":
            return False

    return True


def check_diagonals(board):
    for symbol in ["x", "o"]:
        boardHeight = len(board[0])
        boardWidth = len(board)

        # check / diagonal spaces
        for x in range(boardWidth - 3):
            for y in range(3, boardHeight):
                if board[x][y] == symbol and board[x+1][y-1] == symbol and board[x+2][y-2] == symbol and board[x+3][y-3] == symbol:  # noqa
                    return symbol

        # check \ diagonal spaces
        for x in range(boardWidth - 3):
            for y in range(boardHeight - 3):
                if board[x][y] == symbol and board[x+1][y+1] == symbol and board[x+2][y+2] == symbol and board[x+3][y+3] == symbol:  # noqa
                    return symbol


def check_vertical(x_rows, y_rows, pieces_in_a_row, board):
    """Checks for X in a row, vertical"""

    vertical_rows = dict()

    for x_row in range(0, x_rows):  # 1-7
        vertical_rows[x_row] = get_vertical_slots(x_row, y_rows, board)

    winning_piece = check_rows(vertical_rows, pieces_in_a_row)
    return winning_piece


def check_rows(rows, pieces_in_a_row):
    for row in rows:
        x = 0
        o = 0

        for piece in rows[row]:
            if piece == "x":
                x += 1
                if x >= pieces_in_a_row:
                    # X won
                    return "x"

                elif o > 0:
                    o = 0

            elif piece == "o":
                o += 1
                if o >= pieces_in_a_row:
                    # O Won
                    return "o"

                elif x > 0:
                    x = 0

            else:
                if o > 0:
                    o = 0

                if x > 0:
                    x = 0


def check_for_tie(board):
    for row in board:
        for slot in board[row]:
            if slot == "-":
                return False

    return True


def check_wins(x_rows, y_rows, pieces_in_a_row, board, game_id):
    """Checks if someone won"""

    winner_symbols = {
        "x": list(active_games[game_id]['players'])[0],
        "o": list(active_games[game_id]['players'])[1]
    }

    winner = check_horizontal(pieces_in_a_row, board)
    if winner:
        return f"{active_games[game_id]['players'][winner_symbols[winner]]['name']} won!"

    winner = check_vertical(x_rows, y_rows, pieces_in_a_row, board)
    if winner:
        return f"{active_games[game_id]['players'][winner_symbols[winner]]['name']} won!"

    winner = check_diagonals(board)
    if winner:
        return f"{active_games[game_id]['players'][winner_symbols[winner]]['name']} won!"

    draw = check_for_tie(board)
    if draw:
        return "No one won, it's a draw!"

    # No one won yet
    return None


def add_piece_to_board(move, y_rows, board, player, game_id):
    slots = get_vertical_slots(move, y_rows, board)
    check_slots = y_rows-1

    for slot in range(y_rows):
        if slots[check_slots] == "-":
            break

        check_slots -= 1

    active_games[game_id]['board'][check_slots][move] = player

    return board


def display_board(board, x_rows):
    board_rows = []

    for y_row in range(len(board)):
        rows = ""
        for row in board[y_row]:
            rows += f"{symbols[row]}"

        board_rows.append(rows)

    rows = ""
    row_numbers = ""

    for number in range(0, x_rows):
        row_numbers += number_symbols[(number)+1]

    for row in board_rows:
        rows += f"\n{row}"

    embed = discord.Embed(
        title="Connect 4",
        description=(
            f"{row_numbers}{rows}"
        ),
        color=config.COLOR_SMOOTHIE
    )

    return embed


def swap_player(player, game_id):
    if player == list(active_games[game_id]['players'])[1]:
        player = list(active_games[game_id]['players'])[0]

    else:
        player = list(active_games[game_id]['players'])[1]

    active_games[game_id]['players_turn'] = player
    return player


def play_game():
    # x_rows = 7  # Rows to the right/left  <->
    # y_rows = 6  # Rows upwards ^v
    # pieces_in_a_row = 4  # How many they must get in a row to win

    x_rows = 10
    y_rows = 20
    pieces_in_a_row = 5

    # Create a board with the values from above
    board = create_board(x_rows, y_rows)

    active = True
    player = 0  # Starting player

    display_board(board)
    while active:
        move = input(f"{player}'s turn!. Select between 1-7: ")
        move = int(move) - 1
        board = add_piece_to_board(move, y_rows, board, player)

        winner = check_wins(x_rows, y_rows, pieces_in_a_row, board)
        if winner:
            active = False
            print(
                f"""
                ---------

                {player} won!

                ---------
                """
            )
            break

        player = swap_player(player)


class ConnectFour(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.timeout_games.start()

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Detects when a user clicks a button or uses a slash command"""

        try:
            # Ensures that the interaction is a button, and not a slash commabd
            if interaction.type.name != "component":
                return

            user_id = str(interaction.user.id)
            button = interaction.data["custom_id"]

            if button[0:8] != "connect4":
                return

            else:
                await interaction.response.defer()  # Let's discord know we're handling the interaction
                game_id = interaction.message.id

                if game_id not in active_games:
                    return

                # Check if it is the users turn
                if active_games[game_id]["players_turn"] != user_id:
                    return

                button_id = button[9].replace(f"_{user_id}", "")
                await self.process_round(interaction, button_id, user_id, game_id)

        except Exception as e:
            print("Issue with on_interaction tictactoe", e)

    @tasks.loop(seconds=100)
    async def timeout_games(self):
        """Ends inactive games"""

        games = active_games.copy()
        for game in games:
            if games[game]['time'] < time():
                active_games.pop(game)

                try:
                    await games[game]['message'].edit(view=None)

                except discord.Forbidden:
                    continue

                except Exception as e:
                    print("Failed to end connect4 game:", e)

    async def bot_turn(self, interaction, player, game_id, x_rows, y_rows, board):
        available_slots = []
        for x_row in range(0, x_rows):
            if is_slot_filled(x_row, y_rows, board) is False:
                available_slots.append(x_row)

        move = random.choice(available_slots)
        await self.process_round(interaction, move, player, game_id)

    async def process_round(self, interaction: discord.Interaction, move, player, game_id):
        move = int(move)

        x_rows = active_games[game_id]['x_rows']
        y_rows = active_games[game_id]['y_rows']
        pieces_in_a_row = active_games[game_id]['pieces_in_a_row']
        board = active_games[game_id]['board']

        player_one = list(active_games[game_id]['players'])[0]
        player_two = list(active_games[game_id]['players'])[1]

        board = add_piece_to_board(
            move, y_rows, board, active_games[game_id]['players'][player]['symbol'], game_id
        )

        embed = display_board(board, x_rows)

        winner = check_wins(x_rows, y_rows, pieces_in_a_row, board, game_id)
        if winner:
            embed.add_field(
                name="{} VS {}".format(
                    active_games[game_id]['players'][player_one]['name'],
                    active_games[game_id]['players'][player_two]['name']
                ),
                value=f"{winner}",
            )

            await interaction.followup.edit_message(game_id, embed=embed, view=None)
            active_games.pop(game_id)
            return

        player = swap_player(player, game_id)
        active_games[game_id]['time'] = time() + 300

        embed.add_field(
                name="{} VS {}".format(
                    active_games[game_id]['players'][player_one]['name'],
                    active_games[game_id]['players'][player_two]['name']
                ),
                value=f"<@{player}>'s turn!",
            )

        embed.add_field(
            name="Countdown",
            value=f"Time: <t:{int(active_games[game_id]['time'])}:R> {emojis.TIMER}",
            inline=False
        )

        buttons = []
        for number in range(0, x_rows):
            if is_slot_filled(number, y_rows, board):
                buttons.append(
                    Button(
                        label=f"{number+1}",
                        style=(
                            button_colors["disabled"]
                        ),
                        disabled=True
                    )
                )

            else:
                buttons.append(
                    Button(
                        label=f"{number+1}",
                        style=(
                            button_colors[active_games[game_id]['players'][player]['symbol']]
                        ),
                        custom_id=f"connect4_{number}_{player}"
                    )
                )

        view = View()
        for button in buttons:
            view.add_item(button)

        await interaction.followup.edit_message(game_id, embed=embed, view=view)

        if active_games[game_id]['players'][player_two]['bot'] and player == player_two:
            await asyncio.sleep(1.5)
            player = await self.bot_turn(interaction, player_two, game_id, x_rows, y_rows, board)

    def select_gamemode(self, mode):
        if mode == "original":
            x_rows = 7
            y_rows = 6

        elif mode == "mini":
            x_rows = 5
            y_rows = 4

        elif mode == "2x2":
            x_rows = 2
            y_rows = 2

        elif mode == "large":
            x_rows = 10
            y_rows = 8

        pieces_in_a_row = 4

        return x_rows, y_rows, pieces_in_a_row

    def is_in_game(self, user_id):
        for game in active_games:
            for player in active_games[game]['players']:
                if user_id == player:
                    return True

        return False

    @app_commands.command(
        name="connect4",
        description="Play a fun game of CONNECT FOUR!"
    )
    async def connect_four(
        self,
        interaction: discord.Interaction,
        opponent: discord.User,
        mode: Literal[
            "mini", "original", "large"
        ] = "original"
    ):
        await interaction.response.defer()
        if opponent == interaction.user:
            await interaction.followup.send("You cannot play against yourself!")
            return

        user_id = str(interaction.user.id)
        if self.is_in_game(user_id):
            await interaction.followup.send("You are already in a game!")
            return

        if self.is_in_game(str(opponent.id)):
            await interaction.followup.send(f"{opponent} is already in a game...")
            return

        x_rows, y_rows, pieces_in_a_row = self.select_gamemode(mode)
        player = 0

        game_board = create_board(x_rows, y_rows)
        embed = display_board(game_board, x_rows)

        buttons = []
        for number in range(0, x_rows):
            buttons.append(
                Button(
                    label=f"{number+1}",
                    style=button_colors[player_symbols[player]],
                    custom_id=f"connect4_{number}_{user_id}"
                )
            )

        view = View()
        for button in buttons:
            view.add_item(button)

        embed.add_field(
            name="{} VS {}".format(
                interaction.user.name,
                opponent.name
            ),
            value=f"{interaction.user.mention}'s turn!",
        )

        embed.add_field(
            name="Countdown",
            value=f"Game times out: <t:{int(time() + 300)}:R> {emojis.TIMER}",
            inline=False
        )

        message = await interaction.followup.send(f"<@{user_id}> VS <@{opponent.id}>!", embed=embed, view=view)

        active_games[message.id] = {
            "message": message,
            "time": time() + 300,
            "board": game_board,
            "players": {
                user_id: {
                    "name": interaction.user.name,
                    "symbol": "x",
                    "bot": interaction.user.bot
                },
                str(opponent.id): {
                    "name": opponent.name,
                    "symbol": "o",
                    "bot": opponent.bot
                }
            },
            "players_turn": user_id,
            "x_rows": x_rows,
            "y_rows": y_rows,
            "pieces_in_a_row": pieces_in_a_row
        }


async def setup(bot):
    await bot.add_cog(ConnectFour(bot))
