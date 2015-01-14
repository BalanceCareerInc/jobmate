from models import User


def authenticate(request):
    try:
        return User.query(id__eq=request['user']).next()
    except StopIteration:
        return None
