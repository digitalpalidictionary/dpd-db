from spellchecker import SpellChecker

def check_spelling(field, values, window):
    

    meaning_1 = values["meaning_1"]
    sentence = meaning_1.split(" ")
    spell = SpellChecker()
    unknown = spell.unknown(sentence)
    window[field].update(unknown)
