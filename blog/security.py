from .model import (
    User,
    Group,
    Post
)


def groupfinder(userid, request):
    context = request.context
    if type(context) is User:
        if context.name == userid:
            return ['group:editors']
    elif type(context) is Group:
        in_group = next((x for x in context.users if x.name == userid), None)
        if in_group:
            return ['group:editors']
    elif type(context) is Post:
        if context.author.name == userid:
            return ['group:editors']
        elif context.group_id:
            in_group = next((x for x in context.group.users if x.name == userid), None)
            if in_group:
                return ['group:editors']
    return []