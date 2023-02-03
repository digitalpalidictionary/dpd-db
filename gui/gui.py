#!/usr/bin/env python3

from pathlib import Path
from typing import Dict
import PySimpleGUI as sg

from sqlalchemy.orm import Session

from dpd.models import PaliWord
from dpd.db_helpers import create_db_if_not_exists, get_db_session


def add_pali_word(db_session: Session, values: Dict[str, str]) -> str:
    word = PaliWord(
        pali_1=values['pali_1'],
        meaning_1=values['meaning_1'],
    )

    try:
        db_session.add(word)
        db_session.commit()
    except Exception as e:
        return str(e)

    return "Ok!"


def main():
    db_path = Path("dpd.sqlite3")
    create_db_if_not_exists(db_path)
    db_session = get_db_session(db_path)

    sg.theme('DarkAmber')

    layout = [
        [sg.Text('DPD Editor')],
        [sg.Text('New Pali Word:')],
        [sg.Text('Pali 1:'), sg.InputText(key='pali_1')],
        [sg.Text('Meaning 1:'), sg.InputText(key='meaning_1')],
        [sg.Text(key='-msg-')],
        [sg.Button('Add'), sg.Button('Exit')] ]

    window = sg.Window("DPD Editor", layout)

    while True:
        event, values = window.read()

        if event == 'Add':
            msg = add_pali_word(db_session, values)
            window['-msg-'].update(msg)

        if event == "Exit" or event == sg.WIN_CLOSED:
            break

    db_session.close()

    window.close()


if __name__ == "__main__":
    main()
