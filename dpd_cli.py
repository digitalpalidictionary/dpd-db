import argparse
from jinja2 import Environment, FileSystemLoader
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import Session
from tools.paths import ProjectPaths
import sys
from typing import Dict, List, Optional
from pathlib import Path

def get_table_columns(engine, table_name: str) -> List[str]:
    """Получаем список всех колонок в таблице"""
    inspector = inspect(engine)
    columns = inspector.get_columns(table_name)
    return [col['name'] for col in columns]

def build_headword_query(engine, table_name: str, word: str) -> str:
    """Строим запрос динамически, используя только существующие колонки"""
    columns = get_table_columns(engine, table_name)
    lemma_columns = [col for col in columns if col.startswith('lemma_')]
    
    if not lemma_columns:
        raise ValueError(f"No lemma columns found in table {table_name}")
    
    conditions = " OR ".join([f"{col} = :word" for col in lemma_columns])
    return f"SELECT * FROM {table_name} WHERE {conditions} LIMIT 1"

def fetch_word_details(db_session: Session, engine, word: str, lang: str = "en") -> Optional[dict]:
    """Получаем детали слова"""
    table_name = "russian" if lang == "ru" else "dpd_headwords"
    
    try:
        query_text = build_headword_query(engine, table_name, word)
        query = text(query_text)
        result = db_session.execute(query, {"word": word}).fetchone()
        
        if result:
            # Преобразуем Row в словарь правильно
            return {column: value for column, value in zip(result._fields, result)}
        return None
    except Exception as e:
        print(f"Error fetching word details from {table_name}: {e}", file=sys.stderr)
        return None

def make_dpd_html(word_details: dict, lang: str = "en") -> str:
    """Генерируем HTML-представление слова"""
    if not word_details:
        return "<div>Word not found</div>"
    
    # Простое представление данных
    html = f"""
    <div class="dpd-word">
        <h2>{word_details.get('lemma_1', '')}</h2>
        <div class="pos">Part of speech: {word_details.get('pos', '')}</div>
        <div class="meaning">Meaning: {word_details.get('meaning_1', '')}</div>
        {f'<div class="meaning-lit">Literal meaning: {word_details["meaning_lit"]}</div>' if word_details.get('meaning_lit') else ''}
        <div class="root">Root: {word_details.get('root_key', '')}</div>
    """
    
    if lang == "ru" and 'ru_meaning' in word_details:
        html += f"""<div class="ru-meaning">Russian: {word_details['ru_meaning']}</div>"""
    
    html += "</div>"
    return html

def main():
    parser = argparse.ArgumentParser(description='DPD Dictionary CLI Search')
    parser.add_argument('query', type=str, help='Search word')
    parser.add_argument('--lang', type=str, default='en', choices=['en', 'ru'],
                      help='Language (en/ru)')
    parser.add_argument('--output', type=str, help='Output HTML file')
    
    args = parser.parse_args()
    pth = ProjectPaths()

    # Подключаемся к базе
    engine = create_engine(f"sqlite:///{pth.dpd_db_path}")
    
    # Для отладки: выводим структуру таблиц
    print("\nStarting search...", file=sys.stderr)
    print(f"Database path: {pth.dpd_db_path}", file=sys.stderr)
    
    with Session(engine) as db_session:
        try:
            print(f"\nSearching for: '{args.query}' in language: '{args.lang}'", file=sys.stderr)
            
            # Получаем детали слова
            word_details = fetch_word_details(db_session, engine, args.query, args.lang)
            print(f"Found word details: {bool(word_details)}", file=sys.stderr)
            
            # Генерируем HTML
            dpd_html = make_dpd_html(word_details, args.lang)
            
            result = f"""
            <div class="dpd-pane" id="dpd-pane">
                <div class="dpd-results">{dpd_html}</div>
            </div>
            """

            if args.output:
                output_path = Path(args.output)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(result)
                print(f"\nResults saved to {args.output}", file=sys.stderr)
            else:
                print(result)

        except Exception as e:
            print(f"\nError: {str(e)}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()



