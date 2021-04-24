import time

import logging
import struct
import numpy as np
import scipy.stats
from . import db, scenarios, secrets
import typing
import flask
import flask_login
import io
import json

login_manager = flask_login.LoginManager()

logger = logging.getLogger(__name__)


from sqlalchemy import create_engine

engine = create_engine(secrets.db_url, echo=True)
db.Base.metadata.create_all(engine)
del engine


from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask('wakeword', template_folder='templates')
app.config['SQLALCHEMY_DATABASE_URI'] = secrets.db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'VdDmjbDMLhAXfOV1xTRLK2Vm27m2Xci5ftndzLzqHbWghn2m8nXvBxzbeqNCewdB2h2OEjrf14z8'
fdb = SQLAlchemy(model_class=db.Base)
fdb.init_app(app)
login_manager.init_app(app)
import scipy.io.wavfile

# if typing.TYPE_CHECKING:
#     assert isinstance(fdb.session, sqlalchemy.orm.Session)

@app.route('/')
def hello():
    return "Hello, sauce"


@login_manager.user_loader
def user_loader(uid):
    return fdb.session.query(db.User).filter(db.User.id == int(uid)).one_or_none()


@app.route('/login/<login_code>')
def login_with_code(login_code):
    user = fdb.session.query(db.User).filter(db.User.login_link == login_code).one()
    flask_login.login_user(user)
    return flask.redirect('/sessions')


@app.route('/sessions')
@flask_login.login_required
def sessions():
    user = flask_login.current_user
    assert not user.is_anonymous
    return flask.render_template('sessions.html', user=user, scripts=scenarios.scenarios)


@app.route('/sessions/<int:session_id>')
@flask_login.login_required
def session(session_id):
    user = flask_login.current_user
    assert not user.is_anonymous
    session = fdb.session.query(db.RecordingSession).filter(db.RecordingSession.participant == flask_login.current_user, db.RecordingSession.id == session_id).one()
    return flask.render_template('session.html', user=user, session=session)


@app.route('/sessions/new/<stage_name>')
@flask_login.login_required
def record(stage_name):
    user = flask_login.current_user
    session = db.RecordingSession()
    session.participant = user
    session.start_timestamp = int(time.time())
    session.stage_name = stage_name
    fdb.session.add(session)
    fdb.session.commit()
    stage = [i for i in scenarios.scenarios if i.name == stage_name][0]
    return flask.render_template('record.html', session_id=session.id, record_script=stage)


@app.route('/sessions/record/<int:session_id>')
@flask_login.login_required
def record_session(session_id):
    session = fdb.session.query(db.RecordingSession).filter(db.RecordingSession.participant == flask_login.current_user, db.RecordingSession.id == session_id).one()
    if session.chunks:
        for i in session.chunks:
            fdb.session.delete(i)
        fdb.session.commit()
    if session.labels:
        for i in session.labels:
            fdb.session.delete(i)
        fdb.session.commit()
    stage = [i for i in scenarios.scenarios if i.name == session.stage_name][0]

    return flask.render_template('record.html', session_id=session_id, record_script=stage)

@app.route('/session/<int:session_id>/pcm/<int:chunk_id>')
# @flask_login.login_required
def get_pcm(session_id, chunk_id):
    # session = fdb.session.query(db.RecordingSession).filter(db.RecordingSession.participant == flask_login.current_user, db.RecordingSession.id == session_id).one()
    session = fdb.session.query(db.RecordingSession).filter(db.RecordingSession.id == session_id).one()
    chunk = fdb.session.query(db.AudioChunk).filter(db.AudioChunk.session == session, db.AudioChunk.id == chunk_id).one()
    return flask.Response(
        chunk.pcm,
        content_type='audio/wav'
    )

@app.route('/record/pcm/<int:session_id>/<int:start_sample>', methods=['POST'])
@flask_login.login_required
def record_pcm(session_id: int, start_sample: int):
    user = flask_login.current_user
    assert not user.is_anonymous
    session = fdb.session.query(db.RecordingSession).filter(db.RecordingSession.participant == user, db.RecordingSession.id == session_id).one()

    data = flask.request.data
    data = np.array(list(struct.iter_unpack('f', data)))
    logger.warning("POST %d samples (off %d) total chunks: %d, RMS %.5e, avg: %.5e", len(d), start_sample, len(session.chunks), ((d - d.mean()) ** 2).mean(), np.abs(d).mean())
    d = data[len(data) // 2:]
    if len(session.chunks) > 1000:
        logger.warning("Session is waaay too long!")
        return
    buf = io.BytesIO()
    scipy.io.wavfile.write(buf, 44100, data.astype(np.float))
    buf.seek(0)
    chunk = db.AudioChunk()
    chunk.session = session
    chunk.offset = start_sample
    chunk.sample_count = len(data)

    chunk.pcm = buf.read()
    fdb.session.add(chunk)
    fdb.session.commit()
    # logger.error("Saved %s", chunk.id)
    return "ok"


@app.route('/record/label/<int:session_id>', methods=['POST'])
@flask_login.login_required
def record_label(session_id):
    user = flask_login.current_user
    assert not user.is_anonymous
    session = fdb.session.query(db.RecordingSession).filter(db.RecordingSession.participant == user, db.RecordingSession.id == session_id).one()

    data = json.loads(flask.request.data)
    logger.warning("Nes label: %r", data)

    label = db.AudioLabel()
    label.session = session
    label.label = data['label']
    label.offset = data['offset']
    fdb.session.add(label)
    fdb.session.commit()

    return "ok"

# @routes.post('/record/data')
# async def raw_data(request: web.Request):
#     data = await request.read()
#     start_sample = int(request.query.getone('offset'))
#     data = np.array(list(struct.iter_unpack('f', data)))
#     logger.warning("POST %d samples (off %d), RMS %.5f", len(data), start_sample, ((data - data.mean()) ** 2).mean())
#     return web.Response(body='')


# @routes.get('/record')
# async def record(request):
#
#     return web.Response(
#         body=Path('static/collect.html').read_text(),
#         content_type='text/html'
#     )
#
#
# @routes.get('/record/data/stream')
# async def raw_data(request):
#     ws = web.WebSocketResponse()
#     await ws.prepare(request)
#     hello = await ws.receive()
#     logger.warning("ws hello: %r", hello)
#     async for msg in ws:
#         # logger.warning("Got %d bytes", len(msg.data))
#         data = np.array(list(struct.iter_unpack('f', msg.data)))
#         logger.warning("RMS: %.5fr", ((data - data.mean())**2).mean())
#         # logger.warning("Data stats: %s", scipy.stats.describe(data))
#
#
#
#
# @routes.post('/record/data')
# async def raw_data(request: web.Request):
#     data = await request.read()
#     start_sample = int(request.query.getone('offset'))
#     data = np.array(list(struct.iter_unpack('f', data)))
#     logger.warning("POST %d samples (off %d), RMS %.5f", len(data), start_sample, ((data - data.mean()) ** 2).mean())
#     return web.Response(body='')
#
#
# @routes.get('/record/new-session/{user_key}')
# async def new_session(request: web.Request):
#     s = Session()
#     try:
#         participant = s.query(db.User).filter(db.User.login_link == request.match_info['user_key']).one()
#     except sqlalchemy.orm.exc.NoResultFound:
#         return web.Response(body='nope', status = 403)
#     return web.Response(body='hello %s' % participant.codename)

logging.basicConfig(format='[%(asctime)s] - %(message)s')

if __name__ == '__main__':
    app.run(port=8081)
