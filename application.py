import os, sqlite3
from flask import Flask, url_for, render_template, request, redirect, session, abort, flash, g
from werkzeug.utils import secure_filename

# Globals
G_DIR = "static/g_pics/"
ALLOWED_EXT = set(['png', 'jpg', 'jpeg', 'gif'])


# App settings
app = Flask(__name__)
app.config.from_object(__name__)
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'graphics.db'),
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default',
    UPLOAD_FOLDER = G_DIR
))
app.config.from_envvar('GRAPHICS_SETTINGS', silent=True)


# Routes
@app.route("/")
def gfxhub(name=None):
    return render_template('application.html', name=name)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contribute', methods=['GET', 'POST'])
def contribute(categories=None):
    categories = os.listdir("static/g_pics/")
    if request.method == 'POST':
        category = request.form['category-picker']
        if not category:
            category = 'misc'
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], category, filename))
            return redirect('/g/' + category + '/' + filename)
    return render_template('contribute.html', categories=categories)

@app.route('/dbshow')
def dbshow():
    db = get_db()
    cur = db.execute('select title, category from graphics order by id desc')
    graphics = cur.fetchall()
    return render_template('dbshow.html', graphics=graphics)

@app.route('/dbadd', methods=['POST'])
def dbadd():
    db = get_db()
    db.execute('insert into graphics (title, category) values (?, ?)',
                [request.form['title'], request.form['category']])
    db.commit()
    flash("New graphic posted.")
    return redirect(url_for('dbshow'))

@app.route('/g/')
def show_graphic_list(pics=None):
    categories = os.listdir("static/g_pics/")
    pics = zip(categories, map(os.listdir, [G_DIR + fi for fi in categories]))
    return render_template('graphics_list.html', pics=pics)

@app.route('/g/<category>/')
def show_graphic_list_one_category(category=None):
    pics = zip([category], map(os.listdir, [G_DIR + category]))
    return render_template('graphics_list.html', pics=pics)

@app.route('/g/<category>/<pic>')
def show_graphic(category=None, pic=None, adjacent_pics=None):
    pics = sorted(os.listdir(G_DIR + category))
    pic_index = pics.index(pic)
    adjacent_pics = {'prev' : None, 'next': None}
    if pic_index > 0:
        adjacent_pics['prev'] = pics[pic_index-1]
    if pic_index < len(pics)-1:
        adjacent_pics['next'] = pics[pic_index+1]
    return render_template('graphics.html', category=category, pic=pic, adjacent_pics=adjacent_pics)

@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404


# Helper functions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXT

def connect_db():
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


if __name__ == "__main__":
    app.run()
