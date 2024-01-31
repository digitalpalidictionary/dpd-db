#!/usr/bin/env python3

"""Add combined view into db which have PaliWord, Russian, SBS tables and ebt_count together."""

from sqlalchemy import create_engine, text
from tools.paths import ProjectPaths

from rich.console import Console
from tools.tic_toc import tic, toc

pth = ProjectPaths()
engine = create_engine('sqlite:///' + str(pth.dpd_db_path))

console = Console()

def main():
    tic()
    console.print("[bold bright_yellow]making combined view")

    with engine.connect() as connection:
        connection.execute(text("""
            DROP VIEW IF EXISTS _dps;
        """))
        
        connection.execute(text("""
            CREATE VIEW _dps AS
            SELECT 
                COALESCE(pali_words.id, '') AS id,
                COALESCE(derived_data.ebt_count, '') AS count,
                COALESCE(sbs.sbs_class, '') AS class,
                COALESCE(sbs.sbs_class_anki, '') AS anki,
                COALESCE(sbs.sbs_category, '') AS categ,
                COALESCE(sbs.sbs_index, '') AS PER,
                COALESCE(pali_words.pali_1, '') AS pali_1, 
                COALESCE(pali_words.pali_2, '') AS pali_2,  
                COALESCE(pali_words.pos, '') AS pos, 
                COALESCE(pali_words.grammar, '') AS grammar, 
                COALESCE(pali_words.derived_from, '') AS derived, 
                COALESCE(pali_words.neg, '') AS neg, 
                COALESCE(pali_words.verb, '') AS verb, 
                COALESCE(pali_words.trans, '') AS trans, 
                COALESCE(pali_words.plus_case, '') AS plus_case, 
                COALESCE(pali_words.meaning_1, '') AS meaning_1, 
                COALESCE(pali_words.meaning_lit, '') AS meaning_lit, 
                COALESCE(pali_words.meaning_2, '') AS meaning_2,
                COALESCE(sbs.sbs_meaning, '') AS sbs_meaning, 
                COALESCE(russian.ru_meaning, '') AS ru_meaning, 
                COALESCE(russian.ru_meaning_lit, '') AS ru_meaning_lit, 
                COALESCE(pali_words.sanskrit, '') AS sanskrit, 
                COALESCE(pali_words.root_key, '') AS root, 
                COALESCE(pali_words.root_sign, '') AS sign, 
                COALESCE(pali_words.root_base, '') AS root_base, 
                COALESCE(pali_words.family_root, '') AS family_root, 
                COALESCE(pali_words.family_word, '') AS family_word, 
                COALESCE(pali_words.family_compound, '') AS family_compound, 
                COALESCE(pali_words.family_set, '') AS family_set, 
                COALESCE(pali_words.construction, '') AS construction, 
                COALESCE(pali_words.derivative, '') AS derivative, 
                COALESCE(pali_words.suffix, '') AS suffix, 
                COALESCE(pali_words.phonetic, '') AS phonetic, 
                COALESCE(pali_words.compound_type, '') AS compound_type, 
                COALESCE(pali_words.compound_construction, '') AS compound_construction, 
                COALESCE(pali_words.source_1, '') AS source_1, 
                COALESCE(pali_words.sutta_1, '') AS sutta_1, 
                COALESCE(pali_words.example_1, '') AS example_1, 
                COALESCE(pali_words.source_2, '') AS source_2, 
                COALESCE(pali_words.sutta_2, '') AS sutta_2, 
                COALESCE(pali_words.example_2, '') AS example_2,
                COALESCE(sbs.sbs_source_1, '') AS sbs_source_1, 
                COALESCE(sbs.sbs_sutta_1, '') AS sbs_sutta_1, 
                COALESCE(sbs.sbs_example_1, '') AS sbs_example_1, 
                COALESCE(sbs.sbs_chant_pali_1, '') AS sbs_chant_pali_1, 
                COALESCE(sbs.sbs_chant_eng_1, '') AS sbs_chant_eng_1, 
                COALESCE(sbs.sbs_chapter_1, '') AS sbs_chapter_1, 
                COALESCE(sbs.sbs_source_2, '') AS sbs_source_2, 
                COALESCE(sbs.sbs_sutta_2, '') AS sbs_sutta_2, 
                COALESCE(sbs.sbs_example_2, '') AS sbs_example_2, 
                COALESCE(sbs.sbs_chant_pali_2, '') AS sbs_chant_pali_2, 
                COALESCE(sbs.sbs_chant_eng_2, '') AS sbs_chant_eng_2, 
                COALESCE(sbs.sbs_chapter_2, '') AS sbs_chapter_2, 
                COALESCE(sbs.sbs_source_3, '') AS sbs_source_3, 
                COALESCE(sbs.sbs_sutta_3, '') AS sbs_sutta_3, 
                COALESCE(sbs.sbs_example_3, '') AS sbs_example_3, 
                COALESCE(sbs.sbs_chant_pali_3, '') AS sbs_chant_pali_3,
                COALESCE(sbs.sbs_chant_eng_3, '') AS sbs_chant_eng_3, 
                COALESCE(sbs.sbs_chapter_3, '') AS sbs_chapter_3, 
                COALESCE(sbs.sbs_source_4, '') AS sbs_source_4, 
                COALESCE(sbs.sbs_sutta_4, '') AS sbs_sutta_4, 
                COALESCE(sbs.sbs_example_4, '') AS sbs_example_4, 
                COALESCE(sbs.sbs_chant_pali_4, '') AS sbs_chant_pali_4, 
                COALESCE(sbs.sbs_chant_eng_4, '') AS sbs_chant_eng_4, 
                COALESCE(sbs.sbs_chapter_4, '') AS sbs_chapter_4, 
                COALESCE(pali_words.antonym, '') AS antonym, 
                COALESCE(pali_words.synonym, '') AS synonym, 
                COALESCE(pali_words.variant, '') AS variant, 
                COALESCE(pali_words.commentary, '') AS commentary, 
                COALESCE(pali_words.notes, '') AS notes, 
                COALESCE(sbs.sbs_notes, '') AS sbs_notes, 
                COALESCE(russian.ru_notes, '') AS ru_notes,
                COALESCE(pali_words.cognate, '') AS cognate, 
                COALESCE(pali_words.stem, '') AS stem, 
                COALESCE(pali_words.pattern, '') AS pattern 
            FROM pali_words
            LEFT JOIN sbs ON pali_words.id = sbs.id
            LEFT JOIN russian ON pali_words.id = russian.id
            LEFT JOIN derived_data ON pali_words.id = derived_data.id
            """))


    toc()


if __name__ == "__main__":
    main()
