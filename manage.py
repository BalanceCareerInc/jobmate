# -*-coding:utf8-*-
import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument('command', choices=['initdb'])
args = parser.parse_args()


def init_db():
    import inspect
    import json
    from boto.dynamodb2.layer1 import DynamoDBConnection
    from bynamodb.model import Model
    from web import models

    def load_fixture(model, fixture):
        with open(os.path.join('fixtures', fixture), 'r') as f:
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


if args.command == 'initdb':
    init_db()
