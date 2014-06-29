import os
from flask import Flask, url_for, render_template, request, redirect
from werkzeug.utils import secure_filename

# Globals
G_DIR = "static/g_pics/"
ALLOWED_EXT = set(['png', 'jpg', 'jpeg', 'gif'])


# App settings
app = Flask(__name__)
app.debug = True
app.config['UPLOAD_FOLDER'] = G_DIR


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


if __name__ == "__main__":
    app.run()
