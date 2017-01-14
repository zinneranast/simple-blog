import datetime
import hashlib

from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, engine_from_config, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref, sessionmaker
from sqlalchemy.orm.scoping import scoped_session

from pyramid.security import Allow, Deny, Everyone


Base = declarative_base()
DBSession = scoped_session(sessionmaker())


class Root(object):
    __acl__ = [
        (Allow, Everyone, 'view'),
        (Allow, 'group:editors', ('add', 'edit')),
    ]

    __name__ = None
    __parent__ = None

    def __init__(self, request):
        self.request = request

    @staticmethod
    def get_root():
        return {
            'user': Users(),
            'group': Groups()
        }

    def __getitem__(self, item):
        item = Root.get_root()[item]
        item.__parent__ = self
        return item


class Users(object):
    def __init__(self):
        self.__name__ = 'user'

    def __getitem__(self, item):
        s = DBSession()
        u = s.query(User).filter(User.name == item).one_or_none()
        if u:
            u.__name__ = item
            u.__parent__ = self
            return u
        raise KeyError(item)


class Groups(object):
    def __init__(self):
        self.__name__ = 'group'

    def __getitem__(self, item):
        s = DBSession()
        g = s.query(Group).filter(Group.name == item).one_or_none()
        if g:
            g.__name__ = item
            g.__parent__ = self
            return g
        raise KeyError(item)


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(40), nullable=False)
    password = Column(Text, nullable=False)
    groups = relationship('Group', secondary='user_group')

    def __init__(self, name, password):
        self.name = name
        self.password = User.encrypt_password(password)

    def check_password(self, password):
        return True if User.encrypt_password(password) == self.password else False

    def __getitem__(self, item):
        try:
            item_id = int(item)
        except:
            raise KeyError(item)
        post = next((p for p in self.posts if p.id == item_id), None)
        if post:
            post.__name__ = item
            post.__parent__ = self
            return post
        else:
            raise KeyError(item)

    @staticmethod
    def encrypt_password(password):
        return hashlib.sha1(password.encode('utf-8')).hexdigest()


class Group(Base):
    __tablename__ = 'groups'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    admin_id = Column(Integer, ForeignKey('users.id'))
    admin = relationship(User)
    users = relationship('User', secondary='user_group')

    def __init__(self, admin=None, name=None):
        self.name = name
        self.admin = admin

    def __getitem__(self, item):
        try:
            item_id = int(item)
        except:
            raise KeyError(item)
        post = next((p for p in self.posts if p.id == item_id), None)
        if post:
            post.__name__ = item
            post.__parent__ = self
            return post
        else:
            raise KeyError(item)


class UserGroup(Base):
    __tablename__ = 'user_group'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    group_id = Column(Integer, ForeignKey('groups.id'), primary_key=True)


class Post(Base):
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    text = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=func.now())
    author_id = Column(Integer, ForeignKey('users.id'))
    author = relationship(User, backref = backref('posts', uselist=True))
    group_id = Column(Integer, ForeignKey('groups.id'))
    group = relationship(Group, backref = backref('posts', uselist=True))

    def __init__(self, title, text):
        self.title = title
        self.text = text
        self.timestamp = datetime.datetime.now()
