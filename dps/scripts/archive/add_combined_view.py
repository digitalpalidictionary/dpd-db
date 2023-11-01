#!/usr/bin/env python3

"""Add combined view into db which have PaliWord, Russian, SBS tables and ebt_count together."""

from sqlalchemy import create_engine, text
from tools.paths import ProjectPaths

PTH = ProjectPaths()
engine = create_engine('sqlite:///' + str(PTH.dpd_db_path))

with engine.connect() as connection:
    connection.execute(text("""
        DROP VIEW IF EXISTS dps;
    """))
    
    connection.execute(text("""
        CREATE VIEW dps AS
        SELECT 
            pali_words.id,
            derived_data.ebt_count,
            sbs.sbs_class_anki,
            sbs.sbs_category,
            sbs.sbs_chapter_flag,
            pali_words.pali_1, 
            pali_words.pos, 
            pali_words.grammar, 
            pali_words.derived_from, 
            pali_words.neg, 
            pali_words.verb, 
            pali_words.trans, 
            pali_words.plus_case, 
            pali_words.meaning_1, 
            pali_words.meaning_lit, 
            pali_words.meaning_2,
            sbs.sbs_meaning, 
            russian.ru_meaning, 
            russian.ru_meaning_lit, 
            pali_words.sanskrit, 
            pali_words.root_key, 
            pali_words.root_sign, 
            pali_words.root_base, 
            pali_words.family_root, 
            pali_words.family_word, 
            pali_words.family_compound, 
            pali_words.family_set, 
            pali_words.construction, 
            pali_words.derivative, 
            pali_words.suffix, 
            pali_words.phonetic, 
            pali_words.compound_type, 
            pali_words.compound_construction,  
            pali_words.source_1, 
            pali_words.sutta_1, 
            pali_words.example_1, 
            pali_words.source_2, 
            pali_words.sutta_2, 
            pali_words.example_2,
            sbs.sbs_source_1, 
            sbs.sbs_sutta_1, 
            sbs.sbs_example_1, 
            sbs.sbs_chant_pali_1, 
            sbs.sbs_chant_eng_1, 
            sbs.sbs_chapter_1, 
            sbs.sbs_source_2, 
            sbs.sbs_sutta_2, 
            sbs.sbs_example_2, 
            sbs.sbs_chant_pali_2, 
            sbs.sbs_chant_eng_2, 
            sbs.sbs_chapter_2, 
            sbs.sbs_source_3, 
            sbs.sbs_sutta_3, 
            sbs.sbs_example_3, 
            sbs.sbs_chant_pali_3, 
            sbs.sbs_chant_eng_3, 
            sbs.sbs_chapter_3, 
            sbs.sbs_source_4, 
            sbs.sbs_sutta_4, 
            sbs.sbs_example_4, 
            sbs.sbs_chant_pali_4, 
            sbs.sbs_chant_eng_4, 
            sbs.sbs_chapter_4,  
            pali_words.antonym, 
            pali_words.synonym, 
            pali_words.variant, 
            pali_words.commentary, 
            pali_words.notes, 
            sbs.sbs_notes, 
            russian.ru_notes,
            pali_words.cognate, 
            sbs.sbs_class  
        FROM pali_words
        LEFT JOIN sbs ON pali_words.id = sbs.id
        LEFT JOIN russian ON pali_words.id = russian.id
        LEFT JOIN derived_data ON pali_words.id = derived_data.id
    """))
