import re
import os
from datetime import datetime

from objects import Quest, Status, ChatLog
from dbutil import WowDatabase

class LogReader:
    def __init__(self, file_path, username):
        self.file_path = file_path
        self.username = username

    def _parse_line(self, line):
        """Parse a line into timestamp and text
        Example log: "9/21 19:04:26.594  Sliceyem creates Light Leather"
        Arguments:
            line {string} -- a raw line
        Returns:
            tuple(timestamp, text)
        """
        m = re.search("\d+/\d+ \d+:\d{2}:\d{2}\.\d{3}", line)
        text = line[m.span()[1] + 2 :]

        timestamp = m.group()
        timestamp = datetime.strptime(
            f"{datetime.now().year} {timestamp}", "%Y %m/%d %H:%M:%S.%f"
        )

        return ChatLog(timestamp, text)


    def _reg_search(self, text, regex_str):
        m = re.search(regex_str, text)
        if m:
            return m.group(1)
        else:
            return None


    def _get_quest_accepted(self, text):
        return self._reg_search(text, "Quest accepted: (.+)")


    def _get_quest_completed(self, text):
        return self._reg_search(text, "(.+) completed.$")

    def _get_quest_removed(self, text):
        return self._reg_search(text, "^The quest (.+) has been removed from your quest log$")


    def insert_quests(self):
        db = WowDatabase()
        try:
            changed = datetime.now()
            with open(self.file_path, "r", encoding="UTF-8") as f:
                for line in f:
                    line = line.strip()
                    if line == "":
                        continue
                    ChatLog = self._parse_line(line)
                
                    # Accepted
                    quest_name = self._get_quest_accepted(ChatLog.log)
                    if quest_name:
                        db.insert_quest(self.username, Quest(quest_name, Status.ACCEPTED, ChatLog.timestamp), changed)
                        #continue
                        
                    # Completed
                    quest_name = self._get_quest_completed(ChatLog.log)
                    if quest_name:
                        db.insert_quest(self.username, Quest(quest_name, Status.COMPLETED, ChatLog.timestamp), changed)
                        #continue
                        
                    # Abandoned
                    quest_name = self._get_quest_removed(ChatLog.log)
                    if quest_name:
                        db.insert_quest(self.username, Quest(quest_name, Status.ABANDONED, ChatLog.timestamp), changed)
                        #continue
            
            now = datetime.now()
            now_str = now.strftime("%Y-%m-%d_%H%M%S")
            os.rename(self.file_path, f"{self.file_path}.{self.username}.imported-{now_str}.txt")
        finally:
            db.close()

if __name__ == "__main__":
    file_path = os.path.normpath(
        "E:/games/battle-net-install-location/World of Warcraft/_classic_/Logs/WoWChatLog.txt"
    )
    LogReader = LogReader(file_path, "Lynxlo")
    LogReader.insert_quests()
