import random
from bot.card import UNOCard

class UNODeck:
    colors = ['red', 'green', 'blue', 'yellow']
    values = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "s", "r", "+2"]
    wilds = ["wild", "draw+4"]
    
    def __init__(self):
        self.cards = []
        self.discard_pile = []
        self.build_deck()
        self.shuffle_deck()
        self._ensure_valid_initial_card()

    def build_deck(self):
        for color in self.colors:
            for value in self.values:
                self.cards.append(UNOCard(color, value))
                if value != '0':
                    self.cards.append(UNOCard(color, value))
        for _ in range(2):
            self.cards.append(UNOCard(None, 'wild'))
            self.cards.append(UNOCard(None, 'draw+4'))

    def shuffle_deck(self):
        random.shuffle(self.cards)
        
    def _ensure_valid_initial_card(self):
        while True:
            if not self.cards:
                self.build_deck()
                self.shuffle_deck()
            top_card = self.cards.pop()
            if top_card.type != "wild":
                self.discard_pile.append(top_card)
                break
            else:
                self.cards.insert(0, top_card)

    def replenish_deck(self):
        if len(self.discard_pile) == 0:
            self.reset_deck()
        elif len(self.discard_pile) == 1:
            top_card = self.discard_pile.pop()
            self.reset_deck()
            self.discard_pile = [top_card]
        else:
            top_card = self.discard_pile.pop()
            self.cards = self.discard_pile
            self.discard_pile = [top_card]
            self.shuffle_deck()
        
    def draw_card(self):
        if not self.cards:
            self.replenish_deck()
        self.shuffle_deck()
        return self.cards.pop()

    def draw_cards(self, number):
        if not self.cards:
            self.replenish_deck()
        if number > len(self.cards):
            self.replenish_deck()
        return [self.draw_card() for _ in range(number)]

    def reset_deck(self):
        self.cards = []
        self.discard_pile = []
        self.build_deck()
        self.shuffle_deck()
        self._ensure_valid_initial_card()
    
    def __repr__(self):
        return f"UNODeck(cards={len(self.cards)}, discard={len(self.discard_pile)})"