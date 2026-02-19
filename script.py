import requests
from bs4 import BeautifulSoup
import sqlite3
from typing import List

class BlogArticle:
    def __init__(self, title: str, text: str):
        self.title = title
        self.text = text

    def to_dict(self) -> dict:
        return {
            'title': self.title,
            'text': self.text
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'BlogArticle':
        return cls(data['title'], data['text'])



class BlogParser:
    def __init__(self, url: str):
        self.url = url

    def fetch_page(self) -> str:
        
        try:
            response = requests.get(self.url)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Ошибка при загрузке страницы: {e}")
            return ""

    def parse_articles(self, html: str) -> List[BlogArticle]:
        soup = BeautifulSoup(html, 'html.parser', from_encoding='utf-8')  # Указываем кодировку парсера
        articles = []

        article_blocks = soup.find_all('div', class_='styles_cardBody__qP0jN')

        for block in article_blocks:
            title_tag = block.find('h1')
            title = title_tag.get_text(strip=True) if title_tag else "Без заголовка"
            paragraphs = block.find_all('p')
            text = ' '.join([p.get_text(strip=True) for p in paragraphs])


            title = title.encode('utf-8', errors='ignore').decode('utf-8')
            text = text.encode('utf-8', errors='ignore').decode('utf-8')

            articles.append(BlogArticle(title, text))

        return articles

    def parse_articles(self, html: str) -> List[BlogArticle]:

        soup = BeautifulSoup(html, 'html.parser')
        articles = []


        article_blocks = soup.find_all('div', class_='styles_cardBody__qP0jN')

        for block in article_blocks:

            title_tag = block.find('h1')
            title = title_tag.get_text(strip=True) if title_tag else "Без заголовка"


            paragraphs = block.find_all('p')
            text = ' '.join([p.get_text(strip=True) for p in paragraphs])

            articles.append(BlogArticle(title, text))

        return articles



class DatabaseManager:
    def __init__(self, db_name: str = 'top_academy_blog.db'):
        self.db_name = db_name
        self.init_db()

    def init_db(self):

        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    text TEXT NOT NULL
                )
            ''')
            conn.commit()

    def save_articles(self, articles: List[BlogArticle]) -> int:

        saved_count = 0
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            for article in articles:
                cursor.execute('''
                    INSERT OR IGNORE INTO articles (title, text)
                    VALUES (?, ?)
                ''', (article.title, article.text))
                if cursor.rowcount > 0:
                    saved_count += 1
            conn.commit()
        return saved_count

    def get_first_n_articles(self, n: int = 5) -> List[tuple]:
        """Возвращает первые n записей из базы данных."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, title, text FROM articles LIMIT ?', (n,))
            return cursor.fetchall()



def main():

    blog_url = 'https://msk.top-academy.ru/blog'


    parser = BlogParser(blog_url)

    html = parser.fetch_page()
    if not html:
        print("Не удалось загрузить страницу. Завершение работы.")
        return

    # Извлекаем данные статей
    articles = parser.parse_articles(html)
    print(f"Найдено статей: {len(articles)}")


    db_manager = DatabaseManager()


    saved_count = db_manager.save_articles(articles)
    print(f"Сохранено новых статей: {saved_count}")


    first_articles = db_manager.get_first_n_articles(5)
    print("\nПервые 5 записей из базы данных:")
    for article in first_articles:
        print(f"ID: {article[0]}, Заголовок: {article[1]}")
        print(f"Текст: {article[2][:200]}...\n")


if __name__ == '__main__':
    main()
