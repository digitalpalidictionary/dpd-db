import argparse
from jinja2 import Environment, FileSystemLoader
from sqlalchemy.orm import Session
from db.db_helpers import get_db_session
from exporter.webapp.tools import make_dpd_html
from exporter.webapp.preloads import (
    make_roots_count_dict,
    make_headwords_clean_set,
    make_ascii_to_unicode_dict
)
from tools.paths import ProjectPaths
import sys
from typing import Dict, Set

def load_data_on_demand(db_session: Session, lang: str, query: str) -> tuple:
    """Загружаем только необходимые данные для конкретного запроса"""
    # 1. Загружаем только нужные headwords
    print(f"Loading headwords for query: {query}", file=sys.stderr)
    headwords_clean_set = make_headwords_clean_set(db_session, lang)
    
    # 2. Проверяем, есть ли запрос в headwords
    if query not in headwords_clean_set:
        print(f"Query '{query}' not found in headwords, loading additional data...", file=sys.stderr)
        # Если запроса нет в headwords, загружаем roots и ascii mapping
        roots_count_dict = make_roots_count_dict(db_session)
        ascii_to_unicode_dict = make_ascii_to_unicode_dict(db_session)
        return roots_count_dict, headwords_clean_set, ascii_to_unicode_dict
    
    # Если запрос найден в headwords, другие данные могут не понадобиться
    return {}, headwords_clean_set, {}

def main():
    # 1. Парсинг аргументов
    parser = argparse.ArgumentParser(description='DPD Dictionary CLI Search')
    parser.add_argument('query', type=str, help='Search word')
    parser.add_argument('--lang', type=str, default='en', choices=['en', 'ru'],
                      help='Language (en/ru)')
    parser.add_argument('--output', type=str, help='Output HTML file')
    
    args = parser.parse_args()

    # 2. Инициализация
    pth = ProjectPaths()
    
    # 3. Подключение к базе данных
    db_session: Session = get_db_session(pth.dpd_db_path)
    try:
        # 4. Настройка шаблонов (делаем это до загрузки данных)
        templates_dir = "exporter/webapp/ru_templates" if args.lang == "ru" else "exporter/webapp/templates"
        env = Environment(loader=FileSystemLoader(templates_dir))
        
        # 5. Загрузка данных по требованию
        roots_count_dict, headwords_clean_set, ascii_to_unicode_dict = load_data_on_demand(
            db_session, args.lang, args.query)
    
        # 6. Поиск и генерация HTML
        print(f"Searching for: {args.query}", file=sys.stderr)
        dpd_html, summary_html = make_dpd_html(
            q=args.query,
            pth=pth,
            templates=env,
            roots_count_dict=roots_count_dict,
            headwords_clean_set=headwords_clean_set,
            ascii_to_unicode_dict=ascii_to_unicode_dict,
            lang=args.lang
        )

        result = f"""<div class="dpd-pane" id="dpd-pane">
            <div class="summary-results">{summary_html}</div>
            <div class="dpd-results">{dpd_html}</div>
        </div>"""

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(result)
            print(f"Results saved to {args.output}", file=sys.stderr)
        else:
            print(result)

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
    finally:
        db_session.close()
        print("Database connection closed", file=sys.stderr)

if __name__ == "__main__":
    main()

