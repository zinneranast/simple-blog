from pyramid.httpexceptions import (
    HTTPFound,
    HTTPClientError,
)
from pyramid.security import (
    remember,
    forget,
)
from pyramid.view import (
    view_config,
    forbidden_view_config
)
from .model import (
    DBSession,
    Root,
    User,
    Group,
    Post
)


# from .security import (
#     USERS,
#     hash_password,
#     check_password
# )


class BlogViews:
    def __init__(self, context, request):
        self.request = request
        self.context = context

    def get_resource_from_context(self, context):
        if context.__parent__ is None:
            return context
        s = DBSession()
        r = None
        if type(context) is User:
            r = s.query(User).filter(User.name == context.__name__).one_or_none()
        if type(context) is Group:
            r = s.query(Group).filter(Group.name == context.__name__).one_or_none()
        if type(context) is Post:
            r = s.query(Post).filter(Post.id == context.__name__).one_or_none()
        if r:
            r.__parent__ = context.__parent__
            r.__name__ = context.__name__
        return r

    @property
    def logged_in(self):
        session = self.request.session
        if 'logged_in' in session:
            return session['logged_in']
        else:
            session['logged_in'] = None
            return None

    @view_config(context=Root, renderer='templates/home.jinja2', permission='view')
    def home(self):
        s = DBSession()
        us = s.query(User).all()
        gs = s.query(Group).all()
        return dict(
            name='Home',
            users=us,
            groups=gs,
            back_ref=self.request.application_url
        )

    @view_config(context=User, renderer='templates/user_home.jinja2', permission='view')
    def user_home(self):
        u = self.get_resource_from_context(self.context)
        if not u:
            return HTTPClientError()
        if self.logged_in != u.name:
            return HTTPFound(location=self.request.resource_url(self.context, 'posts_list'))
        else:
            return dict(
                name='My home',
                back_ref=self.request.application_url
            )

    @view_config(context=Group, permission='view')
    def group_home(self):
        g = self.get_resource_from_context(self.context)
        if not g:
            return HTTPClientError()
        return HTTPFound(location=self.request.resource_url(g, 'posts_list'))

    @view_config(context=Post, renderer='templates/view_post.jinja2', permission='view')
    def post_home(self):
        p = self.get_resource_from_context(self.context)
        if not p:
            return HTTPClientError()
        return dict(
            name='Post',
            post=p,
            back_ref=self.request.resource_url(p.__parent__, 'posts_list')
        )

    @view_config(context=Root, name='login', renderer='templates/login.jinja2', permission='view')
    @forbidden_view_config(renderer='templates/login.jinja2')
    def login(self):
        request = self.request
        login_url = request.application_url + '/login'
        referrer = request.url
        if referrer == login_url:
            referrer = '/'
        came_from = request.params.get('came_from', referrer)
        message = ''
        login = ''
        password = ''
        if 'form.submitted' in request.params:
            login = request.params['login']
            password = request.params['password']
            if login != '' and password != '':
                s = DBSession()
                u = s.query(User).filter(User.name == login).one_or_none()
                if u:
                    if u.check_password(password):
                        headers = remember(request, login)
                        request.session['logged_in'] = login
                        u.__parent__ = self.context
                        u.__name__ = login
                        return HTTPFound(location=request.resource_url(self.context, 'user', login),
                                         headers=headers)
            message = 'Failed login'

        return dict(
            name='Login',
            message=message,
            url=login_url,
            came_from=came_from,
            login=login,
            password=password,
        )

    @view_config(context=Root, name='logout', permission='view')
    def logout(self):
        request = self.request
        headers = forget(request)
        url = request.resource_url(self.context, '')
        request.session['logged_in'] = None
        return HTTPFound(location=url, headers=headers)

    @view_config(context=Root, name='registration', renderer='templates/registration.jinja2', permission='view')
    def registration(self):
        request = self.request
        registration_url = request.resource_url(self.context, 'registration')
        referrer = request.url
        if referrer == registration_url:
            referrer = '/'
        came_from = request.params.get('came_from', referrer)
        message = ''
        login = ''
        password = ''
        if 'form.submitted' in request.params:
            login = request.params['login']
            password = request.params['password']
            if login != '' and password != '':
                s = DBSession()
                same_user = s.query(User).filter(User.name == login).one_or_none()
                if not same_user:
                    new_user = User(login, password)
                    s.add(new_user)
                    s.commit()
                    headers = remember(request, login)
                    return HTTPFound(location=request.resource_url(self.context, 'login'),
                                     headers=headers)
                message = 'Login already exist'
            else:
                message = 'Login or password are empty'

        return dict(
            name='Registration',
            message=message,
            url=registration_url,
            came_from=came_from,
            login=login,
            password=password,
        )

    @view_config(context=User, name='add_post', renderer='templates/edit_post.jinja2', permission='add')
    @view_config(context=Group, name='add_post', renderer='templates/edit_post.jinja2', permission='add')
    def add_post(self):
        request = self.request
        context = self.get_resource_from_context(self.context)
        if not context:
            return HTTPClientError()
        add_post_url = request.resource_url(context, 'add_post')
        referrer = request.url
        if referrer == add_post_url:
            referrer = request.resource_url(context, 'posts_list')
        came_from = request.params.get('came_from', referrer)
        message = ''
        title = ''
        text = ''
        if 'form.submitted' in request.params:
            title = request.params['title']
            text = request.params['text']
            if title != '' and text != '':
                s = DBSession()
                if type(context) == User:
                    u = context
                else:
                    u = s.query(User).filter(User.name == self.logged_in).one_or_none()
                if u:
                    p = Post(title, text)
                    s.add(p)
                    u.posts.append(p)
                    if type(context) == Group:
                        context.posts.append(p)
                    s.commit()
                    return HTTPFound(location=request.resource_url(context, 'posts_list'))
            message = 'All fields are required'

        return dict(
            name='Add post',
            message=message,
            title=title,
            text=text,
            came_from=came_from,
            back_ref=request.resource_url(context, 'posts_list')
        )

    @view_config(context=Post, name='edit_post', renderer='templates/edit_post.jinja2', permission='edit')
    def edit_post(self):
        request = self.request
        p = self.get_resource_from_context(self.context)
        if not p:
            return HTTPClientError()
        edit_post_url = request.resource_url(p, 'edit_post')
        referrer = request.url
        if referrer == edit_post_url:
            referrer = request.resource_url(p)
        came_from = request.params.get('came_from', referrer)
        message = ''
        title = p.title
        text = p.text
        if 'form.submitted' in request.params:
            title = request.params['title']
            text = request.params['text']
            if title != '' and text != '':
                s = DBSession()
                p.title = title
                p.text = text
                s.commit()
                return HTTPFound(location=request.resource_url(p))
            message = 'All fields are required'

        return dict(
            name='Add post',
            message=message,
            title=title,
            text=text,
            came_from=came_from,
            back_ref=request.resource_url(p)
        )

    @view_config(context=Post, name='delete_post', permission='edit')
    def delete_post(self):
        request = self.request
        p = self.get_resource_from_context(self.context)
        if not p:
            return HTTPClientError()
        url = request.resource_url(p.__parent__, 'posts_list')
        s = DBSession()
        s.delete(p)
        s.commit()
        return HTTPFound(location=url)

    @view_config(context=User, name='posts_list', renderer='templates/posts_list.jinja2', permission='view')
    @view_config(context=Group, name='posts_list', renderer='templates/posts_list.jinja2', permission='view')
    def posts_list(self):
        request = self.request
        context = self.get_resource_from_context(self.context)
        if not context:
            return HTTPClientError()
        if type(context) is User:
            t = 'User'
            ps = filter(lambda x: x.group_id is None, context.posts)
            u = context
        else:
            t = 'Group'
            ps = context.posts
            u = next((x for x in context.users if x.name == self.logged_in), None)

        if u and self.logged_in == u.name:
            pa = True
            if t == 'Group':
                br = request.application_url + '/user/' + self.logged_in + '/groups_list'
            else:
                br = request.resource_url(context)
        else:
            pa = False
            br = request.application_url

        def inject_meatdata(obj, name, parent):
            obj.__name__ = name
            obj.__parent__ = parent
            return obj

        ps = list(map(lambda x: inject_meatdata(x, str(x.id), context), ps))
        return dict(
            name='Posts',
            type=t,
            context=context,
            posts=ps,
            perm_add=pa,
            back_ref=br
        )

    @view_config(context=User, name='groups_list', renderer='templates/groups_list.jinja2', permission='view')
    def groups_list(self):
        u = self.get_resource_from_context(self.context)
        if not u:
            return HTTPClientError()

        def inject_meatdata(obj, name, parent):
            obj.__name__ = name
            obj.__parent__ = parent
            return obj

        gs = list(map(lambda x: inject_meatdata(x, x.name, u.__parent__.__parent__['group']), u.groups))
        return dict(
            name='Groups',
            groups=gs,
            back_ref=self.request.resource_url(self.context)
        )

    @view_config(context=User, name='add_group', renderer='templates/add_group.jinja2', permission='add')
    def add_group(self):
        request = self.request
        u = self.get_resource_from_context(self.context)
        if not u:
            return HTTPClientError()
        add_group_url = request.resource_url(u, 'add_group')
        referrer = request.url
        if referrer == add_group_url:
            referrer = request.resource_url(u, 'groups_list')
        came_from = request.params.get('came_from', referrer)
        message = ''
        gname = ''
        if 'form.submitted' in request.params:
            gname = request.params['gname']
            if gname != '':
                s = DBSession()
                g = Group(u, gname)
                s.add(g)
                g.users.append(u)
                s.commit()
                return HTTPFound(location=request.resource_url(u, 'groups_list'))
            message = 'All fields are required'

        return dict(
            name='Add group',
            message=message,
            gname=gname,
            came_from=came_from,
            back_ref=request.resource_url(u)
        )

    @view_config(context=Group, name='manage', renderer='templates/group_manage.jinja2', permission='edit')
    def group_manage(self):
        g = self.get_resource_from_context(self.context)
        if not g:
            return HTTPClientError()
        return dict(
            name='Group manage',
            context=g,
            back_ref=self.request.resource_url(g)
        )

    @view_config(context=Group, name='add_member', renderer='templates/add_member.jinja2', permission='add')
    def add_member(self):
        request = self.request
        g = self.get_resource_from_context(self.context)
        if not g:
            return HTTPClientError()
        add_member_url = request.resource_url(g, 'add_member')
        referrer = request.url
        if referrer == add_member_url:
            referrer = request.resource_url(g, 'manage')
        came_from = request.params.get('came_from', referrer)
        message = ''
        member = ''
        if 'form.submitted' in request.params:
            member = request.params['member']
            if member != '':
                in_group = next((x for x in g.users if x.name == member), None)
                if not in_group:
                    s = DBSession()
                    u = s.query(User).filter(User.name == member).one_or_none()
                    if u:
                        g.users.append(u)
                        s.commit()
                        return HTTPFound(location=request.resource_url(g, 'manage'))
                    message = 'Couldn''t add the user ' + member + ' to group'
                else:
                    message = 'User ' + member + ' is a member of the group already'
            else:
                message = 'All fields are required'

        return dict(
            name='Add member',
            group=g,
            message=message,
            member=member,
            came_from=came_from,
            back_ref=self.request.resource_url(g)
        )

    @view_config(context=Group, name='delete_group', permission='edit')
    def delete_group(self):
        request = self.request
        g = self.get_resource_from_context(self.context)
        if not g:
            return HTTPClientError()
        url = request.application_url + '/user/' + self.logged_in + '/groups_list'
        s = DBSession()
        for p in g.posts:
            s.delete(p)
        s.delete(g)
        s.commit()
        return HTTPFound(location=url)