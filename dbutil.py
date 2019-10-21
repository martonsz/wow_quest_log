import os
import psycopg2
from datetime import datetime
from operator import attrgetter

from objects import Quest, Status, ChatLog, UsersQuest


class WowDatabase:
    def __init__(self):
        self._db_password = os.getenv("WOW_DB_PASSWORD")
        self._db_host = os.getenv("WOW_DB_HOST")
        self._db_port = os.getenv("WOW_DB_PORT", "5432")
        self._connect()

    def _connect(self):
        """Connects to databse. Remember to call close() in a finally!
        
        Returns:
            Connection -- return from psycopg2.connect()
        """
        try:
            self._connection = psycopg2.connect(
                user="tempus",
                password=self._db_password,
                host=self._db_host,
                port=self._db_port,
                database="wow",
            )

            # self._connection.autocommit=False
            return self._connection
        except (Exception, psycopg2.Error) as error:
            print("Error while connecting to PostgreSQL", error)

    def _rollback(self):
        self._connection.rollback()

    def close(self):
        # closing database connection.
        if self._connection:
            self._connection.close()
            self._connection = None
            # print("PostgreSQL connection is closed")

    def _cursor(self):
        return self._connection.cursor()

    def get_quests(self, include_ignored=False):
        cursor = self._cursor()

        users_quests = {}
        try:
            where_sql = ""
            if not include_ignored:
                where_sql = "WHERE quest_ignore is not true"
            sql = f""" SELECT username, quest_name, quest_status, quest_timestamp, quest_ignore
                      FROM tbl_quest
                      {where_sql}
                      ORDER BY quest_timestamp ASC;"""
            cursor.execute(sql, (include_ignored,))
            row = cursor.fetchone()
            while row is not None:
                # print(row)
                username = row[0]
                quest = Quest(row[1], Status[row[2]], row[3], row[4])
                # print(f"{username} {quest}")
                user_list = users_quests.get(username)
                if not user_list:
                    user_list = []
                    users_quests[username] = user_list

                # Insert accepted quest. Check if it is a serie
                if quest.status is Status.ACCEPTED:
                    for q in reversed(user_list):
                        if q.name == quest.name:
                            if q.status is not Status.COMPLETED:
                                print(
                                    f"WARN: ACCEPTED, Invalid quest order {username} {quest} VS {q}. Ignoring quest"
                                )
                                continue
                            quest.serie = q.serie + 1
                            # print(f"Found a serie. Increasing serie number {username} {quest} VS {q}")
                            break
                    # print(f"Appending quest {username} {quest}")
                    user_list.append(quest)
                # Complete a quest
                elif quest.status is Status.COMPLETED:
                    found = False
                    for q in reversed(user_list):
                        if q.name == quest.name:
                            if q.status is not Status.ACCEPTED:
                                print(
                                    f"WARN: COMPLETED, Invalid quest order {username} {quest} VS {q}"
                                )
                            q.status = Status.COMPLETED
                            q.timestamp = quest.timestamp
                            # print(f"Completing existing quest {username} {q}")
                            found = True
                            break
                    if not found:
                        # print(f"Appending completed quest {username} {quest}")
                        user_list.append(quest)
                # Delete accepted quest if abandoned
                elif quest.status is Status.ABANDONED:
                    for q in reversed(user_list):
                        if q.name == quest.name:
                            if q.status is not Status.ACCEPTED:
                                print(
                                    f"WARN: ABANDONED, Invalid quest order {username} {quest} VS {q}"
                                )
                            # print(f"Removing abandoned {username} {q}")
                            user_list.remove(q)
                            break

                # print("")
                row = cursor.fetchone()

            usernames = list(users_quests.keys())
            user_quests_result = {}
            for username, quests in users_quests.items():
                for quest in reversed(quests):
                    user_quest = user_quests_result.get(quest.key())
                    if not user_quest:
                        user_quest = UsersQuest(quest.key(), usernames, quest.ignored)
                        user_quests_result[quest.key()] = user_quest
                    user_quest.addUserQuest(username, quest)

            # sorted(user_quests_result.items(), key=lambda kv: kv[1])
            # return user_quests_result
            return sorted(
                user_quests_result.values(),
                key=attrgetter("compare_status", "quest_name"),
                reverse=False,
            )
        finally:
            cursor.close()

    def insert_quest(self, username, quest: Quest, changed=None):
        cursor = self._cursor()
        if not changed:
            changed = datetime.now()
        try:
            # self._connection.autocommit=False
            sql = """ INSERT INTO tbl_quest
                      (username, quest_name, quest_status, quest_timestamp, changed) VALUES (%s,%s,%s,%s,%s)"""
            record = (
                username,
                quest.name,
                quest.status.value,
                quest.timestamp,
                changed,
            )
            cursor.execute(sql, record)
            self._connection.commit()
            print(f"{quest}")
        except psycopg2.errors.UniqueViolation as e:
            print(f"Already exists {quest} - {e}")
            self._rollback()
        finally:
            cursor.close()

    def set_ignore_quest(self, quest_name: str, ignore: bool):
        cursor = self._cursor()
        print(f"Setting ignore = {ignore} for {quest_name}")
        try:
            sql = """ UPDATE tbl_quest
                      SET quest_ignore = %s
                      WHERE quest_name = %s"""
            record = (ignore, quest_name)
            cursor.execute(sql, record)
            self._connection.commit()
        finally:
            cursor.close()


if __name__ == "__main__":
    wow_db = WowDatabase()

    try:
        result = wow_db.get_quests(include_ignored=True)
        for r in result:
            print(r)

        # connection = wow_db._connect()
        # cursor = wow_db._cursor()
        # Print PostgreSQL Connection properties
        # print(connection.get_dsn_parameters(), "\n")

        # Print PostgreSQL version
        # cursor.execute("SELECT version();")
        # record = cursor.fetchone()
        # print("You are connected to - ", record, "\n")
    finally:
        wow_db.close()
