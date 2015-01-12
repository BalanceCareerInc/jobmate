from models import User


def authenticate(request):
    try:
        return User.query(username__eq=request['user']).next()
    except StopIteration:
        return None
