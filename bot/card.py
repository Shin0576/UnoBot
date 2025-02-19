import uuid

class UNOCard:
    def __init__(self, color, value):
        self.id = uuid.uuid4()
        self.color = color
        self.value = value
        self.type = self.determine_type()

    def determine_type(self):
        if self.value in ['s', 'r', '+2']:
            return "action"
        elif self.value in ['wild', 'draw+4']:
            return "wild"
        else:
            return "number"

    def __str__(self):
        return f"{self.color} {self.value}" if self.color else f"{self.value}"

    def __repr__(self):
        return str(self)