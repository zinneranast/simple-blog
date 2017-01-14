import os
import sys

from sqlalchemy import engine_from_config

from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )

from blog.model import (
    DBSession,
    Base,
    User,
    Group,
    Post
    )


def insert_while_creating(session):
    me = User('Alexander', '1')
    session.add(me)
    he = User('Noname', '2')
    session.add(he)
    my_group = Group(me, 'first group')
    my_group.users.append(me)
    my_group.users.append(he)
    session.add(my_group)
    my_group2 = Group(he, 'cool group')
    my_group2.users.append(me)
    my_group2.users.append(he)
    session.add(my_group2)
    p = Post('Post', 'my post')
    session.add(p)
    p2 = Post('Post2', 'his post in group')
    session.add(p2)
    me.posts.append(p)
    he.posts.append(p2)
    my_group.posts.append(p2)
    p3 = Post('Post3', 'my post in group')
    session.add(p3)
    me.posts.append(p3)
    my_group.posts.append(p3)
    p4 = Post('Post4', 'my post 4')
    session.add(p4)
    me.posts.append(p4)
    session.commit()


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


if __name__ == '__main__':
    argv = sys.argv
    if len(argv) != 2:
        usage(argv)
    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    insert_while_creating(DBSession())
