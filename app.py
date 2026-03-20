from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
import os
import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'super-secret-key-12345-change-me-please-2026'  # ← поменяй на свой

# Настройки
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 МБ

# Создаём папку uploads если нет
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Пароль для админа (лучше потом перенести в .env)
ADMIN_PASSWORD = 'admin123'  # ← ИЗМЕНИ ОБЯЗАТЕЛЬНО!

# Какие файлы можно загружать
ALLOWED_EXTENSIONS = {
    'pdf', 'jpg', 'jpeg', 'png', 'gif', 'zip', 'rar', '7z',
    'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'csv',
    'mp4', 'mp3', 'wav'
}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# =============================================================================
# Главная страница — доступна всем
# =============================================================================
@app.route('/')
def index():
    files = []
    upload_dir = app.config['UPLOAD_FOLDER']

    for filename in os.listdir(upload_dir):
        filepath = os.path.join(upload_dir, filename)
        if os.path.isfile(filepath):
            size_bytes = os.path.getsize(filepath)
            if size_bytes >= 1024 * 1024:
                size_str = f"{size_bytes / (1024 * 1024):.1f} МБ"
            elif size_bytes >= 1024:
                size_str = f"{size_bytes / 1024:.1f} КБ"
            else:
                size_str = f"{size_bytes} Б"

            mtime = os.path.getmtime(filepath)
            date_str = datetime.datetime.fromtimestamp(mtime).strftime('%d.%m.%Y %H:%M')

            files.append({
                'name': filename,
                'size': size_str,
                'date': date_str,
                'timestamp': mtime
            })

    files.sort(key=lambda x: x['timestamp'], reverse=True)

    is_admin = 'admin' in session

    return render_template('index.html', files=files, is_admin=is_admin)

# =============================================================================
# Скачивание файла
# =============================================================================
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

# =============================================================================
# Страница входа для админа
# =============================================================================
@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['admin'] = True
            flash('Успешный вход как администратор', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Неверный пароль', 'error')

    return render_template('admin_login.html')

# =============================================================================
# Выход из админки
# =============================================================================
@app.route('/admin-logout')
def admin_logout():
    session.pop('admin', None)
    flash('Вы вышли из админ-панели', 'info')
    return redirect(url_for('index'))

# =============================================================================
# Админ-панель
# =============================================================================
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'admin' not in session:
        flash('Доступ только для администратора', 'error')
        return redirect(url_for('admin_login'))

    if request.method == 'POST' and 'file' in request.files:
        file = request.files['file']
        if file.filename == '':
            flash('Файл не выбран', 'error')
        elif file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash(f'Файл "{filename}" успешно загружен', 'success')
        else:
            flash('Недопустимый тип файла', 'error')
        return redirect(url_for('admin'))

    files = [f for f in os.listdir(app.config['UPLOAD_FOLDER'])
             if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], f))]

    return render_template('admin.html', files=files)

# =============================================================================
# Запуск
# =============================================================================
if __name__ == '__main__':
    print("Сервер запущен")
    print("http://127.0.0.1:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
