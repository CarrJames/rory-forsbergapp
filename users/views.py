from flask import Blueprint, render_template, request
from users.forms import StartForm

users_blueprint = Blueprint('users', __name__, template_folder='templates')


@users_blueprint.route('/index', methods=['GET', 'POST'])
def index():
    form = StartForm()

    if form.validate_on_submit():
        print(request.form.get('username'))
        print(request.form.get('email'))
        print(request.form.get('csv'))
        return login()

    return render_template('index.html', form=form)


@users_blueprint.route('/login')
def login():
    return render_template('login.html')