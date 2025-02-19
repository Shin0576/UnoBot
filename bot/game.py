from bot.deck import UNODeck
from bot.player import Player
from bot.card import UNOCard

class UNOGame:
    def __init__(self):
        self.deck = UNODeck()
        self.creator = None
        self.players = []
        self.current_player_index = 0
        self.direction = 1
        self.top_card = UNOCard(None, '-1')
        self.game_started = False
        self.pending_draws = 0
        self.decision_maker = None

    def add_player(self, player_id, username):
        if not self.game_started:
            player = Player(player_id, username)
            self.players.append(player)
            return True
        return False

    def next_turn(self):
        self.current_player_index = (self.current_player_index + self.direction) % len(self.players)

    def _is_valid_move(self, card: UNOCard, player: Player):
        flag = True
        message=f"You have successfully played {card}"
        if player.id != self.players[self.current_player_index].id:
            message = "It's not your turn yet! Please wait for your turn."
            flag = False
        elif card.color != self.top_card.color and card.value != self.top_card.value and card.type != "wild":
            message = "Invalid move! Look at the card on board and try again."
            flag = False
        elif card.value in ['+2', 'draw+4'] and self.top_card.value in ['+2', 'draw+4']:
            if card.value != self.top_card.value:
                message = "Invalid move! You can only play the same draw cards consecutively."
                flag = False
        return message, flag

    def _handle_card_effect(self, card, chosen_color):
        message = ""
        headline = ""
        if card.value == self.top_card.value and card.color == self.top_card.color:
            message = f"have played {card.color} {card.value} card!"
            headline = f"🎲 What a coincidence! 🎨"
        if card.value != self.top_card.value and card.color == self.top_card.color:
            message = f"have played a {card.color} {card.value} card!"
            headline = f"🎲 Number changes to {card.value}"
        if card.color != self.top_card.color and card.value == self.top_card.value:
            message = f"have played a {card.color} {card.value} card!"
            headline = f"🎲 Colour changes to {card.color}! 🎨"
        if card.value == "s":
            self.current_player_index += 1
            self.next_turn()
            message = f"has played a {card.color} skip card!"
            headline = f"⏭️ Next player has been skipped!"
        elif card.value == "r":
            if len(self.players) == 2:
                self.current_player_index += 1
                self.next_turn()
            else:
                self.direction *= -1
            message = f"has played a reverse {card} card!"
            headline = f"🔄 The direction of game has been reversed!"
        elif card.value == "+2":
            self.pending_draws += 2
            message = f"has played a {card.color} draw card!!"
            headline = f"💥 Next player draws {self.pending_draws} cards!"
        elif card.type == "wild":
            self.top_card.color = chosen_color
            message = f"has played a wild card!"
            headline = f"🎲 The color has been changed to {chosen_color}! 🎨"
        elif card.value == "draw+4":
            self.pending_draws += 4
            self.top_card.color = chosen_color
            message += f"💥 Next player draws {self.pending_draws} cards!"
            headline = f"Color changed to {chosen_color}!"
        return headline, message

    def check_win(self):
        for player in self.players:
            if len(player.hand) == 0:
                return player
        return None