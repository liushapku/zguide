import zmq.green as zmq
from zmq.green.eventloop.ioloop import IOLoop, PeriodicCallback
# from zmq.green.eventloop.future import Context
from zmq.green.eventloop.zmqstream import ZMQStream
from gevent import monkey
from gevent import pywsgi
import gevent.event
import geventwebsocket
from geventwebsocket.handler import WebSocketHandler
import gevent.pool
import gevent.queue
from flask_socketio import SocketIO
import jsonrpc.backend.flask as jsonrpc
# import socketio
globalpool = gevent.pool.Pool(1000)


import flask
from flask import (
    abort,
    escape,
    flash,
    Flask,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
    Response,
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_required,
    login_user,
    logout_user,
    current_user,
)
from flask_oauthlib.client import OAuth
# from flask_socketio import SocketIO, send, emit
from flask_wtf import FlaskForm
import wtforms
import os
import datetime
import json
import requests
import datetime
import werkzeug.serving
import pdb
import time
from bs4 import BeautifulSoup
from urllib.parse import urlparse
monkey.patch_all()

basedir = os.path.abspath(os.path.dirname(__file__))
staticdir = ''

# static_folder is for server to find the file
# static_url_path is embeded in html, which should begin with '/'
app = Flask(__name__, static_url_path='/static', static_folder=staticdir, template_folder='')
app.config.update(
    # use os.urandom(24) to generate one
    SECRET_KEY = '\xfd{H\xe5<\x95\xf9\xe3\x96.5\xd1\x01O<!\xd5\xa2\xa0\x9fR"\xa1\xa8',
    SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://localhost/flask',
    SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository'),
    SQLALCHEMY_TRACK_MODIFICATIONS = False,
    TEMPLATES_AUTO_RELOAD = True,
)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
sio = SocketIO(app, async_mode='gevent', ping_timeout=10, ping_interval=10)
# sio = socketio.Server(async_mode='gevent')
# app.wsgi_app = socketio.Middleware(sio, app.wsgi_app)

#### template
@app.context_processor
def override_url_for():
    def dated_url_for(endpoint, **values):
        if endpoint == 'static':
            filename = values.get('filename', None)
            if filename:
                file_path = os.path.join(app.root_path, staticdir, filename)
                values['q'] = int(os.stat(file_path).st_mtime)
        return url_for(endpoint, **values)
    return {'url_for': dated_url_for}

@app.template_filter('up')
def upper_filter(msg):
    return msg.upper()
#### end template

#### User
class User(UserMixin):
    def __init__(self, name, password=None):
        self.name = name
        self.password = name
    def __str__(self):
        return self.name
    def get_id(self):
        return str(self.name)

users = { 'Alice': User('Alice'),
         'Bob' : User('Bob')}
posts = { 'Alice': [
            { 'author': {'name': 'Bob'}, 'body': 'Hello Alice' },
            { 'author': {'name': 'Alice'}, 'body': 'Welcome Bob' },
            ],
           'Bob': [
               { 'author': {'name': 'Bob'}, 'body': 'My first post'},
           ],
         }
@app.context_processor
def inject():
    return {'users': users, 'posts': posts}

@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id, None)
#### end User

#### login
class LoginForm(FlaskForm):
    name = wtforms.StringField('name', validators=[wtforms.validators.DataRequired()])
    password = wtforms.PasswordField('password', validators=[wtforms.validators.DataRequired()])
    remember_me = wtforms.BooleanField('remember_me', default=False)
    submit = wtforms.SubmitField('Login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash('you are already logged in', 'warn')
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        name = request.form['name']
        password = request.form['password']
        next = request.args.get('next', request.referrer)
        found = False
        if name in users:
            if password == users[name].password:
                login_user(users[name])
                flash('{} logged in'.format(name))
                print('----', urlparse(next).path, next, request.referrer, url_for('login'), sep=' | ')
                if next is None or urlparse(next).path == '/login':
                    next = url_for('index')
                return redirect(next)
            form.password.errors.append('invalid password')
        else:
            form.name.errors.append('invalid user name')
    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
def logout():
    if current_user.is_authenticated:
        logout_user()
    resp = make_response(redirect('index'))
    resp.set_cookie('lastvisited', '', expires=0, path='/profile')
    return resp

#### end login
@app.route('/profile/<username>')
@login_required
def profile(username):
    last_visited = request.cookies.get('lastvisited')
    current_time = str(datetime.datetime.now())
    body = render_template('profile.html',
                           username=username,
                           last_visited=last_visited,
                           current_time=current_time)
    resp = make_response(body)
    resp.set_cookie('lastvisited',
                    current_time,
                    path='/profile')
    return resp


@app.route('/index')
@app.route('/')
def index():
    print(request)
    print(session)
    user = {'name': 'Alice'}
    body = render_template('index.html',
                           title='Home',
                           user=user,
                           posts=posts,
                           request_arg=request.args)
    return body

# entry for raw websocket
@app.route('/echo')
def handle_echo():
    return render_template('echo.html', title='Echo')

# handle raw websocket
@app.route('/echo/channel')
def handle_echo_message():
    # print()
    print(request.environ)
    ws = request.environ.get('wsgi.websocket')
    if ws is not None:
        try:
            while True:  # need to put in a inf loop otherwise, the connection will be closed
                message = ws.receive()
                print(message) # message is unicode
                if message is not None:
                    ws.send(message)
                else:  # when client closed, message is None
                    break
        except geventwebsocket.WebSocketError as ex:
            print('exception ', type(ex), ex)
        finally:
            ws.close()
        return ''
    else:
        flask.abort(404)

@app.route('/zmqsub')
def handle_zmqsub():
    return render_template('zmqsub.html', title='Zmqsub')

@app.route('/zmqsub/channel')
def handle_zmqsub_message():
    # NOTE: remember to run `python zmqpub.py` to start publisher
    # print()
    print(request.environ)
    ws = request.environ.get('wsgi.websocket')
    # raw socket: ws.stream.handler.socket._sock : type stdlib socket
    rawsock = ws.stream.handler.socket._sock
    if ws is None:
        flask.abort(404)
    try:
        def ws_receive():
            if ws.receive() is None:
                pass
        wsthread = globalpool.spawn(ws_receive)
        context    = zmq.Context.instance()
        subscriber = context.socket(zmq.SUB)
        subscriber.connect("tcp://localhost:5563")
        subscriber.setsockopt(zmq.SUBSCRIBE, b"B")
        # need to put in a inf loop otherwise, the connection will be closed
        while True:
            # Read envelope with address
            [address, contents] = subscriber.recv_multipart()
            message = "{} ".format(time.asctime()) + (b"[%s] %s" % (address, contents)).decode()
            # pdb.set_trace()

            print('zmqsub:', message)
            if wsthread.ready():
                break
            else:
                ws.send(message)
    except geventwebsocket.WebSocketError as ex:
        print('exception ', type(ex), ex)
    finally:
        print('zmqsub closed')
        subscriber.close()
        ws.close()
    return ''

@app.route('/zmqsub/stream')
def handle_zmqsub_stream():
    # print()
    ws = request.environ.get('wsgi.websocket')
    # raw socket: ws.stream.handler.socket._sock : type stdlib socket
    rawsock = ws.stream.handler.socket._sock
    if ws is None:
        flask.abort(404)
    context    = zmq.Context.instance()
    subscriber = context.socket(zmq.SUB)
    subscriber.connect("tcp://localhost:5563")
    subscriber.setsockopt(zmq.SUBSCRIBE, b"B")
    ioloop = IOLoop()
    stream = ZMQStream(subscriber, ioloop)
    def on_recv(msg):
        address, contents = msg
        message = "{} ".format(time.asctime()) + (b"[%s] %s" % (address, contents)).decode()
        print('===zmqsub:', message)
        ws.send(message)
    stream.on_recv(on_recv)

    def ws_receive():
        ws.receive()
        ioloop.stop()

    try:
        globalpool.spawn(ws_receive)
        ioloop.start()

    except geventwebsocket.WebSocketError as ex:
        print('exception ', type(ex), ex)
    except Exception as ex:
        print('Exception ', ex)
    finally:
        print('zmqsub closed')
        subscriber.close()
        ws.close()
    return ''

from urllib.parse import urljoin, urldefrag
def remove_fragment(url):
    pure_url, frag = urldefrag(url)
    return pure_url

@app.errorhandler(404)
def page_not_found(error):
    return "This page does not exist", 404

clients = {}
@sio.on('connect')
def on_connected():
    if 'user_id' not in session:
        print('--- recieved a connection without a session', request.sid)
        session['user_id'] = 'Anonymous'
    else:
        print(session)
        print(type(request.namespace))
    clients[session['user_id']] = request.sid
    print('--- received a connection from', session['user_id'])

@sio.on('disconnect')
def on_disconnected():
    del clients[session['user_id']]
    print('--- disconnected from', session['user_id'])

@sio.on('message')
def on_message(data):
    print(data)
    print('transfer message from {} to {}: {}'.format(session['user_id'], data['to'], data['message']))
    to = clients.get(data['to'])
    if to:
        todata = {
            'event': 'receive',
            'from': session['user_id'],
            'message': data['message']
        }
        sio.send(json.dumps(todata), room=to)
    else:
        print('{} is not connected'.format(data['to']))
        feedback = {
            'event': 'friend disconnected',
            'name': data['to']
        }
        sio.send(json.dumps(feedback))


@app.route('/gevent')
def handle_gevent():
    session = requests.Session()
    queue = gevent.queue.Queue(1000)
    t1 = datetime.datetime.now()
    def response_generator():
        ii = 0
        while npending or not queue.empty():
            ii += 1
            result = queue.get()
            msg = '{} {}\n'.format(ii, result)
            print(msg, end='')
            yield msg
        t2 = datetime.datetime.now()
        print('====', t2 - t1)

    generator = response_generator()
    # generator.send(None)
    def finished(greenlet):
        nonlocal npending
        npending -= 1
        queue.put(greenlet.value)

    # no need to lock
    # lock = gevent.lock.RLock()
    def get_links_from_url(url):
        nonlocal npending
        try:
            resp = session.get(url)
            soup = BeautifulSoup(resp.text, 'lxml')
            for tag in soup.find_all('a'):
                newurl = tag.get('href')
                newurl = urljoin(baseurl, remove_fragment(newurl))
                if newurl.startswith(baseurl) and newurl not in results:
                    results.add(newurl)
                    npending += 1
                    gevent.spawn(get_links_from_url, newurl).link(finished)
            return url
        except Exception as e:
            print('==============================', url, e)

    baseurl = 'http://www.tornadoweb.org/en/stable/'
    results = {baseurl}
    npending = 1
    gevent.spawn(get_links_from_url, baseurl).link(finished) #.link(finished)
    return Response(generator,  mimetype='text/html')


# jsonrpc
# invoke as: webapi#jsonrpc#call('http://localhost:port/jsonrpc/', 'jsonrpc_test_method', {'a':1, 'b': 2}, 3)
app.register_blueprint(jsonrpc.api.as_blueprint(), url_prefix='/jsonrpc')
@jsonrpc.api.dispatcher.add_method
def jsonrpc_test_method(*args, **kwargs):
    return args, kwargs
# invoke as: webapi#jsonrpc#call('http://localhost:port/jsonrpc/', 'my_add', [1,2], 3)
# or webapi#jsonrpc#call('http://localhost:port/jsonrpc/', 'my_add', {'x': 1, 'y': 2}, 3)
@jsonrpc.api.dispatcher.add_method
def my_add(x, y):
    return x+y


@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    # print('====================add_header==========')
    # print(r.headers)
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r

# auto reload
@werkzeug.serving.run_with_reloader
def run():
    # no need to add extra_files if TEMPLATES_AUTO_RELOAD is set
    sio.run(app, debug=True, host='localhost', port=5000, spawn=globalpool, extra_files=[])

    # app.debug = True
    # server = pywsgi.WSGIServer(('192.168.1.185', 5000), app,
    #                            handler_class=WebSocketHandler,
    #                            spawn=globalpool)
    # server.serve_forever()

run()

# app.run(host='192.168.1.185', port=5000)
# socketio.run(app, debug=True, host='192.168.1.185', port=5000)

# another example  to run the app: in geventwebsocket examples/chat/chat.py
# WebSocketServer(
#     ('0.0.0.0', 8000),

#     Resource([
#         ('^/chat', ChatApplication),
#         ('^/.*', DebuggedApplication(flask_app))
#     ]),

#     debug=False
# ).serve_forever()
