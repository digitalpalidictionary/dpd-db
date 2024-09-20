#!/usr/bin/env python3

"""Add combined view into db which have DpdHeadword, Russian, SBS tables and ebt_count together."""

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
                COALESCE(dpd_headwords.id, '') AS id,
                COALESCE(dpd_headwords.ebt_count, '') AS count,
                COALESCE(sbs.sbs_class, '') AS class,
                COALESCE(sbs.sbs_class_anki, '') AS anki,
                COALESCE(sbs.sbs_category, '') AS categ,
                COALESCE(sbs.sbs_patimokkha, '') AS pat,
                COALESCE(sbs.sbs_index, '') AS PER,
                COALESCE(dpd_headwords.lemma_1, '') AS lemma_1, 
                COALESCE(dpd_headwords.lemma_2, '') AS lemma_2,  
                COALESCE(dpd_headwords.pos, '') AS pos, 
                COALESCE(dpd_headwords.grammar, '') AS grammar, 
                COALESCE(dpd_headwords.derived_from, '') AS derived, 
                COALESCE(dpd_headwords.neg, '') AS neg, 
                COALESCE(dpd_headwords.verb, '') AS verb, 
                COALESCE(dpd_headwords.trans, '') AS trans, 
                COALESCE(dpd_headwords.plus_case, '') AS plus_case, 
                COALESCE(dpd_headwords.meaning_1, '') AS meaning_1, 
                COALESCE(dpd_headwords.meaning_lit, '') AS meaning_lit, 
                COALESCE(dpd_headwords.meaning_2, '') AS meaning_2,
                COALESCE(sbs.sbs_meaning, '') AS sbs_meaning, 
                COALESCE(russian.ru_meaning, '') AS ru_meaning, 
                COALESCE(russian.ru_meaning_lit, '') AS ru_meaning_lit,
                COALESCE(russian.ru_meaning_raw, '') AS ru_meaning_raw, 
                COALESCE(dpd_headwords.sanskrit, '') AS sanskrit, 
                COALESCE(dpd_headwords.root_key, '') AS root, 
                COALESCE(dpd_headwords.root_sign, '') AS sign, 
                COALESCE(dpd_headwords.root_base, '') AS root_base, 
                COALESCE(dpd_headwords.family_root, '') AS family_root, 
                COALESCE(dpd_headwords.family_word, '') AS family_word, 
                COALESCE(dpd_headwords.family_compound, '') AS family_compound, 
                COALESCE(dpd_headwords.family_set, '') AS family_set, 
                COALESCE(dpd_headwords.construction, '') AS construction, 
                COALESCE(dpd_headwords.derivative, '') AS derivative, 
                COALESCE(dpd_headwords.suffix, '') AS suffix, 
                COALESCE(dpd_headwords.phonetic, '') AS phonetic, 
                COALESCE(dpd_headwords.compound_type, '') AS compound_type, 
                COALESCE(dpd_headwords.compound_construction, '') AS compound_construction, 
                COALESCE(dpd_headwords.source_1, '') AS source_1, 
                COALESCE(dpd_headwords.sutta_1, '') AS sutta_1, 
                COALESCE(dpd_headwords.example_1, '') AS example_1, 
                COALESCE(dpd_headwords.source_2, '') AS source_2, 
                COALESCE(dpd_headwords.sutta_2, '') AS sutta_2, 
                COALESCE(dpd_headwords.example_2, '') AS example_2,
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
                COALESCE(dpd_headwords.antonym, '') AS antonym, 
                COALESCE(dpd_headwords.synonym, '') AS synonym, 
                COALESCE(dpd_headwords.variant, '') AS variant, 
                COALESCE(dpd_headwords.commentary, '') AS commentary, 
                COALESCE(dpd_headwords.notes, '') AS notes, 
                COALESCE(sbs.sbs_notes, '') AS sbs_notes, 
                COALESCE(russian.ru_notes, '') AS ru_notes,
                COALESCE(dpd_headwords.cognate, '') AS cognate, 
                COALESCE(dpd_headwords.stem, '') AS stem, 
                COALESCE(dpd_headwords.pattern, '') AS pattern 
            FROM dpd_headwords
            LEFT JOIN sbs ON dpd_headwords.id = sbs.id
            LEFT JOIN russian ON dpd_headwords.id = russian.id
            """))


    toc()


if __name__ == "__main__":
    main()
