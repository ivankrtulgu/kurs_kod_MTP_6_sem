# Common Security Vulnerabilities and Fixes

Руководство по распространенным уязвимостям и способам их исправления.

## SQL Injection

### Уязвимый код

```python
# ❌ НЕБЕЗОПАСНО
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
    return cursor.fetchone()

# ❌ НЕБЕЗОПАСНО
def search_books(title):
    query = f"SELECT * FROM books WHERE title LIKE '%{title}%'"
    cursor.execute(query)
    return cursor.fetchall()
```

### Безопасный код

```python
# ✅ БЕЗОПАСНО
def get_user(user_id):
    query = "SELECT * FROM users WHERE id = %s"
    cursor.execute(query, (user_id,))
    return cursor.fetchone()

# ✅ БЕЗОПАСНО
def search_books(title):
    query = "SELECT * FROM books WHERE title LIKE %s"
    cursor.execute(query, (f"%{title}%",))
    return cursor.fetchall()
```

## Path Traversal

### Уязвимый код

```python
# ❌ НЕБЕЗОПАСНО
def read_file(filename):
    with open(f"uploads/{filename}", 'r') as f:
        return f.read()

# Атака: filename = "../../etc/passwd"
```

### Безопасный код

```python
# ✅ БЕЗОПАСНО
import os
from pathlib import Path

def read_file(filename):
    base_dir = Path("uploads").resolve()
    file_path = (base_dir / filename).resolve()
    
    # Проверка, что файл внутри разрешенной директории
    if not str(file_path).startswith(str(base_dir)):
        raise ValueError("Invalid file path")
    
    with open(file_path, 'r') as f:
        return f.read()
```

## Command Injection

### Уязвимый код

```python
# ❌ НЕБЕЗОПАСНО
import os

def ping_host(host):
    os.system(f"ping -c 1 {host}")

# Атака: host = "google.com; rm -rf /"
```

### Безопасный код

```python
# ✅ БЕЗОПАСНО
import subprocess
import shlex

def ping_host(host):
    # Валидация входных данных
    if not host.replace('.', '').replace('-', '').isalnum():
        raise ValueError("Invalid host")
    
    # Использование списка аргументов вместо shell
    subprocess.run(['ping', '-c', '1', host], check=True)
```

## Insecure Deserialization

### Уязвимый код

```python
# ❌ НЕБЕЗОПАСНО
import pickle

def load_data(data):
    return pickle.loads(data)

# Атака: pickle может выполнить произвольный код
```

### Безопасный код

```python
# ✅ БЕЗОПАСНО
import json

def load_data(data):
    return json.loads(data)

# Или для сложных объектов
from dataclasses import dataclass, asdict
import json

@dataclass
class User:
    id: int
    name: str

def serialize_user(user: User) -> str:
    return json.dumps(asdict(user))

def deserialize_user(data: str) -> User:
    return User(**json.loads(data))
```

## Weak Cryptography

### Уязвимый код

```python
# ❌ НЕБЕЗОПАСНО
import hashlib

def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()

# MD5 легко взламывается
```

### Безопасный код

```python
# ✅ БЕЗОПАСНО
import bcrypt

def hash_password(password: str) -> bytes:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt)

def verify_password(password: str, hashed: bytes) -> bool:
    return bcrypt.checkpw(password.encode(), hashed)
```

## Hardcoded Secrets

### Уязвимый код

```python
# ❌ НЕБЕЗОПАСНО
DATABASE_PASSWORD = "super_secret_password_123"
API_KEY = "sk-1234567890abcdef"

def connect_db():
    return psycopg2.connect(
        host="localhost",
        password=DATABASE_PASSWORD
    )
```

### Безопасный код

```python
# ✅ БЕЗОПАСНО
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
API_KEY = os.getenv("API_KEY")

def connect_db():
    password = os.getenv("DATABASE_PASSWORD")
    if not password:
        raise ValueError("DATABASE_PASSWORD not set")
    
    return psycopg2.connect(
        host="localhost",
        password=password
    )
```

## XML External Entity (XXE)

### Уязвимый код

```python
# ❌ НЕБЕЗОПАСНО
import xml.etree.ElementTree as ET

def parse_xml(xml_string):
    return ET.fromstring(xml_string)

# Атака: XXE может читать локальные файлы
```

### Безопасный код

```python
# ✅ БЕЗОПАСНО
import defusedxml.ElementTree as ET

def parse_xml(xml_string):
    return ET.fromstring(xml_string)

# defusedxml защищает от XXE, billion laughs и других атак
```

## Insecure Random

### Уязвимый код

```python
# ❌ НЕБЕЗОПАСНО
import random

def generate_token():
    return ''.join(random.choices('0123456789abcdef', k=32))

# random не криптографически безопасен
```

### Безопасный код

```python
# ✅ БЕЗОПАСНО
import secrets

def generate_token():
    return secrets.token_hex(32)

def generate_password():
    return secrets.token_urlsafe(32)
```

## Unvalidated Redirects

### Уязвимый код

```python
# ❌ НЕБЕЗОПАСНО
from flask import redirect, request

@app.route('/redirect')
def redirect_user():
    url = request.args.get('url')
    return redirect(url)

# Атака: /redirect?url=http://evil.com
```

### Безопасный код

```python
# ✅ БЕЗОПАСНО
from flask import redirect, request, abort
from urllib.parse import urlparse

ALLOWED_HOSTS = ['example.com', 'www.example.com']

@app.route('/redirect')
def redirect_user():
    url = request.args.get('url')
    
    # Проверка, что URL относительный или на разрешенном домене
    parsed = urlparse(url)
    if parsed.netloc and parsed.netloc not in ALLOWED_HOSTS:
        abort(400, "Invalid redirect URL")
    
    return redirect(url)
```

## Information Disclosure

### Уязвимый код

```python
# ❌ НЕБЕЗОПАСНО
from flask import Flask

app = Flask(__name__)
app.config['DEBUG'] = True  # В production!

@app.errorhandler(Exception)
def handle_error(e):
    return str(e), 500  # Раскрывает внутренние детали
```

### Безопасный код

```python
# ✅ БЕЗОПАСНО
from flask import Flask
import logging

app = Flask(__name__)
app.config['DEBUG'] = False

logger = logging.getLogger(__name__)

@app.errorhandler(Exception)
def handle_error(e):
    # Логируем детали для разработчиков
    logger.error(f"Error: {e}", exc_info=True)
    
    # Возвращаем общее сообщение пользователю
    return "An error occurred. Please try again later.", 500
```

## Insecure File Upload

### Уязвимый код

```python
# ❌ НЕБЕЗОПАСНО
from flask import request

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    file.save(f"uploads/{file.filename}")
    return "File uploaded"

# Атака: загрузка shell.php
```

### Безопасный код

```python
# ✅ БЕЗОПАСНО
from flask import request
from werkzeug.utils import secure_filename
import os

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file", 400
    
    file = request.files['file']
    
    # Проверка расширения
    if not allowed_file(file.filename):
        return "Invalid file type", 400
    
    # Проверка размера
    file.seek(0, os.SEEK_END)
    size = file.tell()
    if size > MAX_FILE_SIZE:
        return "File too large", 400
    file.seek(0)
    
    # Безопасное имя файла
    filename = secure_filename(file.filename)
    
    # Сохранение
    file.save(os.path.join('uploads', filename))
    return "File uploaded"
```

## Race Conditions

### Уязвимый код

```python
# ❌ НЕБЕЗОПАСНО
import os

def create_temp_file():
    filename = "/tmp/myapp_temp"
    if not os.path.exists(filename):
        with open(filename, 'w') as f:
            f.write("data")
    return filename

# Атака: TOCTOU (Time-of-check to time-of-use)
```

### Безопасный код

```python
# ✅ БЕЗОПАСНО
import tempfile

def create_temp_file():
    # Атомарное создание временного файла
    fd, filename = tempfile.mkstemp(prefix="myapp_")
    with os.fdopen(fd, 'w') as f:
        f.write("data")
    return filename
```

## Дополнительные рекомендации

1. **Всегда валидируйте ввод** на стороне сервера
2. **Используйте whitelist**, а не blacklist для валидации
3. **Применяйте принцип наименьших привилегий**
4. **Регулярно обновляйте зависимости**
5. **Используйте HTTPS** для всех соединений
6. **Включите CSP** (Content Security Policy)
7. **Настройте rate limiting** для API
8. **Логируйте security events**
9. **Проводите code review** с фокусом на безопасность
10. **Используйте automated security testing**
