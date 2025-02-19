from bot.card import UNOCard

class Player:
    def __init__(self, user_id: int, username: str):
        self.id = user_id
        self.username = username
        self.hand = []
        self.uno_call = False

    def draw(self, cards: list[UNOCard]):
        self.hand.extend(cards)

    def play_card(self, card_index: int) -> UNOCard | None:
        if 0 <= card_index < len(self.hand):
            return self.hand.pop(card_index)
        return None

    def has_uno(self) -> bool:
        return len(self.hand) == 1

    def __repr__(self):
        return f"Player({self.username}, cards={len(self.hand)})"