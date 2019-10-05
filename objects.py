from enum import Enum


class Status(Enum):
    ABANDONED = "ABANDONED"
    ACCEPTED = "ACCEPTED"
    COMPLETED = "COMPLETED"
    MISSING = "MISSING"


class Quest:
    def __init__(self, name=None, status=None, timestamp=None, serie=1):
        self.name = name
        self.status = status
        self.timestamp = timestamp
        self.serie = serie

    def key(self):
        if self.serie > 1:
            return f"{self.name} ({self.serie})"
        return f"{self.name}"

    def compare_status(self):
        if self.status is Status.COMPLETED:
            return 2
        else:
            return 1

    def __str__(self):
        if self.serie > 1:
            return f"{self.name} ({self.serie}) {self.status.value} {self.timestamp}"
        return f"{self.name} {self.status.value} {self.timestamp}"

    def __repr__(self):
        return self.__str__

    def __eq__(self, other):
        return (
            self.name == other.name
            and self.status is other.status
            and self.serie == other.serie
        )

    def __ne__(self, other):
        return not self.__eq__(other)


class ChatLog:
    def __init__(self, timestamp, log):
        self.timestamp = timestamp
        self.log = log

    def __str__(self):
        return f"{self.timestamp} {self.log}"

    def __repr__(self):
        return self.__str__()


class UsersQuest:
    def __init__(self, quest_name: str, usernames: list):
        self.quest_name = quest_name
        self.user_quests = {}
        for username in usernames:
            self.user_quests[username] = None
        self.compare_status = None
        self.compare_timestamp = None

    def addUserQuest(self, username: str, quest: Quest):
        self.user_quests[username] = quest

        self.compare_status = quest.compare_status()
        for username, q in self.user_quests.items():
            compare_status = 1  # Missing status
            if q:
                compare_status = q.compare_status()
            if compare_status < self.compare_status:
                self.compare_status = compare_status

        if not self.compare_timestamp or self.compare_timestamp < quest.timestamp:
            self.compare_timestamp = quest.timestamp

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        sb = ""
        for username, quest in self.user_quests.items():
            if quest:
                sb = f"{sb} {username:5} {quest.status.name:10}"
            else:
                sb = f"{sb} {username:5} {Status.MISSING.name:10}"
        # return f"{self.quest_name} {self.compare_status} {self.compare_timestamp}"
        return (
            f"{self.quest_name:35} {sb} {self.compare_timestamp} {self.compare_status}"
        )
