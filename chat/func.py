from models import User


def authenticate(request):
    try:
        return User.query(id__eq=request['token']).next()
    except StopIteration:
        return None


def subscribers(channel):
    return [
        dict(id=user.id, endpoint_arn=user.endpoint_arn)
        for user in User.scan(pair_id__eq=channel)
    ]
