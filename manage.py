# -*-coding:utf8-*-
import argparse
import os

from boto.dynamodb2.layer1 import DynamoDBConnection
from boto.dynamodb2.table import Table

from web.app import create_app


def init_db():
    import inspect
    import json
    from bynamodb.model import Model
    import models

    def load_fixture(model, fixture):
        with open(os.path.join('fixtures', '%s.json' % fixture), 'r') as f:
            for row in json.loads(f.read()):
                model.put_item(**row)

    conn = DynamoDBConnection()
    table_names = conn.list_tables()['TableNames']
    models_ = [getattr(models, name) for name in dir(models)]
    models_ = [model for model in models_
               if inspect.isclass(model) and issubclass(model, Model) and not model == Model]
    for model in models_:
        if model.get_table_name() not in table_names:
            model.create_table(2, 2)
            [load_fixture(model, fixture) for fixture in getattr(model, '__fixtures__', [])]


def reset_db():
    conn = DynamoDBConnection()
    table_names = conn.list_tables()['TableNames']
    for table in table_names:
        Table(table).delete()
    init_db()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['initdb', 'resetdb', 'runserver', 'runchatserver', 'pairing'])
    args = parser.parse_args()

    if args.command == 'initdb':
        app = create_app('localconfig.py')
        init_db()
    elif args.command == 'resetdb':
        app = create_app('localconfig.py')
        reset_db()
    elif args.command == 'runserver':
        app = create_app('localconfig.py')
        app.run(host='0', port=9338, debug=True)
    elif args.command == 'runchatserver':
        from dnachat.runner import run_dnachat
        run_dnachat('chat/config.py')
    elif args.command == 'pairing':
        from web.tasks import pairing
        app = create_app('localconfig.py')
        pairing()
