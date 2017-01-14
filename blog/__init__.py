from pyramid.config import Configurator
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.session import SignedCookieSessionFactory
from blog.model import *
from blog.views import *
from blog.security import groupfinder
from blog.views import BlogViews


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """

    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    my_session_factory = SignedCookieSessionFactory(settings['blog.cookie'])
    config = Configurator(settings=settings, session_factory=my_session_factory, root_factory='.model.Root')

    authn_policy = AuthTktAuthenticationPolicy(settings['blog.secret'], callback=groupfinder, hashalg='sha512')
    authz_policy = ACLAuthorizationPolicy()
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)

    config.add_static_view('static', 'static', cache_max_age=3600)
    config.scan()
    return config.make_wsgi_app()
