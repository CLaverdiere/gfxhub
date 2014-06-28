import os
from flask import Flask, url_for, render_template

app = Flask(__name__)

@app.route("/")
def gfxhub(name=None):
    return render_template('application.html', name=name)

@app.route('/about')
def about():
    return "gfxhub is a place to share graphics."

@app.route('/g/')
def show_graphic_list(pics=[]):
    pics = sorted(filter(lambda f: f.endswith(".png"), os.listdir("static/raytraced_pics/")))
    return render_template('graphics_list.html', pics=pics)

@app.route('/g/<pic>')
def show_graphic(pic=None):
    return render_template('graphics.html', pic=pic)

@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404

if __name__ == "__main__":
    app.run(debug=True)
