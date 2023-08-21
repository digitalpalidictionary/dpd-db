import sqlite3
from typing import Dict, List

DataType = List[Dict[str, str]]

class DataKeeper:
    def __init__(self, db_name: str) -> None:
        self.db_name = db_name

    def create_db(self) -> None:
        with sqlite3.connect(self.db_name) as connector:
            connector.execute(
                '''
                CREATE TABLE IF NOT EXISTS entries(
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    word TEXT NOT NULL,
                    definition_html TEXT NOT_NULL,
                    definition_plain TEXT);
                ''')
            connector.execute(
                '''
                CREATE TABLE IF NOT EXISTS synonyms(
                    entry_id INTEGER NOT NULL,
                    word TEXT NOT NULL,
                    FOREIGN KEY (entry_id) REFERENCES entries(id));
                ''')
            connector.commit()

    def save_data(self, data: DataType) -> None:
        with sqlite3.connect(self.db_name) as connector:
            i = 0
            cursor = connector.cursor()

            for entry in data:
                cursor.execute(
                    'INSERT INTO entries(word, definition_html) VALUES (?, ?)',
                    (entry['word'], entry['definition_html']))
                entry_id = cursor.lastrowid
                cursor.executemany(
                    'INSERT INTO synonyms(entry_id, word) VALUES (?, ?)',
                    ((entry_id, word) for word in entry['synonyms']))
                i += 1
                if i % 1000 == 0:
                    connector.commit()

            connector.commit()

    def load_data(self) -> DataType:
        result = []
        with sqlite3.connect(self.db_name) as connector:
            entry_cur = connector.cursor()
            syn_cur = connector.cursor()
            data = entry_cur.execute('SELECT id, word, definition_html FROM entries;')
            for row in data:
                entry_id, word, def_html = row
                synonyms = syn_cur.execute('SELECT word FROM synonyms WHERE entry_id = ?;', (entry_id,))
                result.append({
                    'word': word,
                    'definition_html': def_html,
                    'synonyms': [i[0] for i in synonyms]
                })

        return result
