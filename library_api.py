from flask import Flask, request, jsonify, json
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
import os

# === Настройка базы данных ===

DATABASE_URL = 'sqlite:///library.db'

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


# === Модели базы данных ===

class Author(Base):
    __tablename__ = 'authors'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    bio = Column(Text)

    books = relationship('Book', back_populates='author', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'bio': self.bio,
            'books': [book.id for book in self.books]
        }


class Book(Base):
    __tablename__ = 'books'

    id = Column(Integer, primary_key=True)
    title = Column(String(200), unique=True, nullable=False)
    description = Column(Text)
    author_id = Column(Integer, ForeignKey('authors.id'), nullable=False)

    author = relationship('Author', back_populates='books')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'author_id': self.author_id,
            'author_name': self.author.name
        }


# === Инициализация базы данных с предустановленными данными ===

def init_db():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Проверяем, есть ли данные в таблице авторов
        author_count = db.query(Author).count()
        if author_count == 0:
            # Добавляем авторов
            author1 = Author(
                name='Лев Толстой',
                bio='Русский писатель, один из величайших авторов в истории литературы.'
            )
            author2 = Author(
                name='Фёдор Достоевский',
                bio='Русский писатель, мыслитель, философ и публицист.'
            )
            author3 = Author(
                name='Джейн Остин',
                bio='Английская писательница, одна из величайших романисток в истории.'
            )
            author4 = Author(
                name='Марк Твен',
                bio='Американский писатель, журналист и общественный деятель.'
            )

            db.add_all([author1, author2, author3, author4])
            db.commit()

            # Добавляем книги
            book1 = Book(
                title='Война и мир',
                description='Эпический роман об истории России во время наполеоновских войн.',
                author_id=author1.id
            )
            book2 = Book(
                title='Анна Каренина',
                description='Роман о трагической любви и судьбе женщины в российском обществе.',
                author_id=author1.id
            )
            book3 = Book(
                title='Преступление и наказание',
                description='Роман о внутренней борьбе молодого человека после совершения преступления.',
                author_id=author2.id
            )
            book4 = Book(
                title='Идиот',
                description='Роман о намерении человека быть полностью искренним в обществе лицемеров.',
                author_id=author2.id
            )
            book5 = Book(
                title='Гордость и предубеждение',
                description='Роман о любви и социальных предрассудках в английском обществе XVIII века.',
                author_id=author3.id
            )
            book6 = Book(
                title='Том Сойер',
                description='Приключения юного Тома Сойера на берегах реки Миссисипи.',
                author_id=author4.id
            )

            db.add_all([book1, book2, book3, book4, book5, book6])
            db.commit()
    finally:
        db.close()


# === Создание приложения Flask ===

app = Flask(__name__)

# Инициализация базы данных при запуске приложения
init_db()


# === Пользовательская функция для сериализации JSON с кириллическими символами ===

def custom_jsonify(data, status=200):
    return app.response_class(
        response=json.dumps(data, ensure_ascii=False, indent=2),
        status=status,
        mimetype='application/json'
    )


# === Маршрут для корневого URL ===

@app.route('/', methods=['GET'])
def home():
    return '''
    <h1>Добро пожаловать в библиотечный API</h1>
    <p>Используйте следующие маршруты для взаимодействия с API:</p>
    <ul>
        <li>GET /api/books — получить список всех книг</li>
        <li>GET /api/books/&lt;book_id&gt; — получить информацию о книге по ID</li>
        <li>GET /api/authors — получить список всех авторов</li>
        <li>GET /api/authors/&lt;author_id&gt; — получить информацию об авторе по ID</li>
    </ul>
    '''


# === Маршруты для управления книгами ===

# Получить список всех книг
@app.route('/api/books', methods=['GET'])
def get_books():
    db = SessionLocal()
    books = db.query(Book).all()
    result = [book.to_dict() for book in books]
    db.close()
    return custom_jsonify(result)


# Создать новую книгу
@app.route('/api/books', methods=['POST'])
def create_book():
    data = request.get_json()
    required_fields = ['title', 'author_id']
    if not data or not all(field in data for field in required_fields):
        return custom_jsonify({'error': 'Missing required fields'}, status=400)

    db = SessionLocal()
    try:
        book = Book(
            title=data['title'],
            description=data.get('description'),
            author_id=data['author_id']
        )
        db.add(book)
        db.commit()
        result = book.to_dict()
        db.close()
        return custom_jsonify(result, status=201)
    except IntegrityError:
        db.rollback()
        db.close()
        return custom_jsonify({'error': 'Author not found or duplicate book title'}, status=400)


# Получить информацию о книге по ID
@app.route('/api/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    db = SessionLocal()
    book = db.query(Book).get(book_id)
    if not book:
        db.close()
        return custom_jsonify({'error': 'Book not found'}, status=404)
    result = book.to_dict()
    db.close()
    return custom_jsonify(result)


# Обновить информацию о книге
@app.route('/api/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    data = request.get_json()
    db = SessionLocal()
    book = db.query(Book).get(book_id)
    if not book:
        db.close()
        return custom_jsonify({'error': 'Book not found'}, status=404)
    if 'title' in data:
        book.title = data['title']
    if 'description' in data:
        book.description = data['description']
    if 'author_id' in data:
        book.author_id = data['author_id']
    db.commit()
    result = book.to_dict()
    db.close()
    return custom_jsonify(result)


# Удалить книгу
@app.route('/api/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    db = SessionLocal()
    book = db.query(Book).get(book_id)
    if not book:
        db.close()
        return custom_jsonify({'error': 'Book not found'}, status=404)
    db.delete(book)
    db.commit()
    db.close()
    return custom_jsonify({'message': 'Book deleted'})


# === Маршруты для управления авторами ===

# Получить список всех авторов
@app.route('/api/authors', methods=['GET'])
def get_authors():
    db = SessionLocal()
    authors = db.query(Author).all()
    result = [author.to_dict() for author in authors]
    db.close()
    return custom_jsonify(result)


# Создать нового автора
@app.route('/api/authors', methods=['POST'])
def create_author():
    data = request.get_json()
    required_fields = ['name']
    if not data or not all(field in data for field in required_fields):
        return custom_jsonify({'error': 'Missing required fields'}, status=400)

    db = SessionLocal()
    try:
        author = Author(
            name=data['name'],
            bio=data.get('bio')
        )
        db.add(author)
        db.commit()
        result = author.to_dict()
        db.close()
        return custom_jsonify(result, status=201)
    except IntegrityError:
        db.rollback()
        db.close()
        return custom_jsonify({'error': 'Duplicate author name'}, status=400)


# Получить информацию об авторе по ID
@app.route('/api/authors/<int:author_id>', methods=['GET'])
def get_author(author_id):
    db = SessionLocal()
    author = db.query(Author).get(author_id)
    if not author:
        db.close()
        return custom_jsonify({'error': 'Author not found'}, status=404)
    result = author.to_dict()
    db.close()
    return custom_jsonify(result)


# Обновить информацию об авторе
@app.route('/api/authors/<int:author_id>', methods=['PUT'])
def update_author(author_id):
    data = request.get_json()
    db = SessionLocal()
    author = db.query(Author).get(author_id)
    if not author:
        db.close()
        return custom_jsonify({'error': 'Author not found'}, status=404)
    if 'name' in data:
        author.name = data['name']
    if 'bio' in data:
        author.bio = data['bio']
    db.commit()
    result = author.to_dict()
    db.close()
    return custom_jsonify(result)


# Удалить автора
@app.route('/api/authors/<int:author_id>', methods=['DELETE'])
def delete_author(author_id):
    db = SessionLocal()
    author = db.query(Author).get(author_id)
    if not author:
        db.close()
        return custom_jsonify({'error': 'Author not found'}, status=404)
    # Проверяем, есть ли у автора связанные книги
    books = db.query(Book).filter_by(author_id=author_id).all()
    if books:
        db.close()
        return custom_jsonify({'error': 'Cannot delete author with books'}, status=400)
    db.delete(author)
    db.commit()
    db.close()
    return custom_jsonify({'message': 'Author deleted'})


# === Обработка ошибок ===

@app.errorhandler(404)
def not_found(error):
    return custom_jsonify({'error': 'Resource not found'}, status=404)


@app.errorhandler(400)
def bad_request(error):
    return custom_jsonify({'error': 'Bad request'}, status=400)


# === Запуск приложения ===

if __name__ == '__main__':
    app.run(debug=True)
