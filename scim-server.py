import json
import re

from flask import Flask
from flask import render_template
from flask import request
from flask import url_for
from flask_socketio import SocketIO, emit
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import flask


Base = declarative_base()


class ListResponse():
    def __init__(self, list):
        self.list = list

    def to_scim_resource(self):
        rv = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
            "totalResults": 0,
            "Resources": []
        }
        resources = []
        for item in self.list:
            resources.append(item.to_scim_resource())
        rv['totalResults'] = len(resources)
        rv['Resources'] = resources
        return rv


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    externalId = Column(String(250))
    userName = Column(String(250), unique=True, nullable=False)
    familyName = Column(String(250))
    middleName = Column(String(250))
    givenName = Column(String(250))
    locale = Column(String(250))
    timezone = Column(String(250))
    active = Column(Boolean, default=False)

    def __init__(self, resource):
        for attribute in ['userName', 'locale', 'timezone', 'active']:
            if attribute in resource:
                setattr(self, attribute, resource[attribute])
        for attribute in ['givenName', 'middleName', 'familyName']:
            if attribute in resource['name']:
                setattr(self, attribute, resource['name'][attribute])

    def to_scim_resource(self):
        rv = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "id": self.id,
            "userName": self.userName,
            "name": {
                "familyName": self.familyName,
                "givenName": self.givenName,
                "middleName": self.middleName,
            },
            "active": self.active,
            "locale": self.locale,
            "timezone": self.timezone,
            "meta": {
                "resourceType": "User",
                # "created": "2010-01-23T04:56:22Z",
                # "lastModified": "2011-05-13T04:42:34Z",
                # "location":
                # "https://example.com/v2/Users/2819c223-7f76-453a-413861904646"
            }
        }
        return rv

engine = create_engine('sqlite:///test-users.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

app = Flask(__name__)
socketio = SocketIO(app)


def send_to_browser(obj):
    socketio.emit('user',
                  {'data': obj},
                  broadcast=True,
                  namespace='/test')


@socketio.on('connect', namespace='/test')
def test_connect():
    # emit('my response', {'data': 'Connected'})
    for user in session.query(User).all():
        emit('user', {'data': user.to_scim_resource()})


@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')


@app.route('/')
def hello():
    return render_template('base.html')


@app.route("/scim/v2/Users/<user_id>", methods=['GET'])
def user_get(user_id):
    user = session.query(User).filter(User.id == user_id).one()
    rv = user.to_scim_resource()
    send_to_browser(rv)
    return json.dumps(rv)


@app.route("/scim/v2/Users", methods=['POST'])
def users_post():
    scim_user = request.get_json()
    user = User(scim_user)
    session.add(user)
    session.commit()
    resp = flask.jsonify(user.to_scim_resource())
    send_to_browser(user.to_scim_resource())
    resp.headers['Location'] = url_for('user_get',
                                       user_id=user.userName,
                                       _external=True)
    return resp, 201


@app.route("/scim/v2/Users/<user_id>", methods=['PATCH'])
def users_patch(user_id):
    scim_user = request.get_json()
    if 'schemas' not in scim_user:
        return "Payload must contain 'schemas' attribute.", 400
    schema_other = 'urn:ietf:params:scim:schemas:core:2.0:User'
    if schema_other not in scim_user['schemas']:
        return "The 'schemas' type in this request is not supported.", 501
    del(scim_user['id'])
    del(scim_user['schemas'])
    user = session.query(User).filter(User.id == user_id).one()
    for key in scim_user.keys():
        setattr(user, key, scim_user[key])
    session.add(user)
    session.commit()
    send_to_browser(user.to_scim_resource())
    #FIXME: What goes here?
    return ""


@app.route("/scim/v2/Users", methods=['GET'])
def users_get():
    found = []
    request_filter = request.args.get('filter')
    if request_filter:
        m = re.match('(\w+) eq "([^"]*)"', request_filter)
        (search_key_name, search_value) = m.groups()
        search_key = getattr(User, search_key_name)
        found = session.query(User).filter(search_key == search_value).all()
    else:
        found = session.query(User).all()

    # Is this correct?
    # Should I be returning an empty set? Maybe with 404?
    if len(found) == 0:
        return "Not found", 404

    rv = ListResponse(found)
    return json.dumps(rv.to_scim_resource())

if __name__ == "__main__":
    app.debug = True
    # app.run()
    socketio.run(app)
