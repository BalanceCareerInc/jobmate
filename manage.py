# -*-coding:utf8-*-
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('command', choices=['initdb'])
args = parser.parse_args()


def init_db():
    import inspect
    from boto.dynamodb2.layer1 import DynamoDBConnection
    from bynamodb.model import Model
    from web import models

    conn = DynamoDBConnection()
    table_names = conn.list_tables()['TableNames']
    models_ = [getattr(models, name) for name in dir(models)]
    models_ = [model for model in models_
               if inspect.isclass(model) and issubclass(model, Model) and not model == Model]
    for model in models_:
        if model.get_table_name() not in table_names:
            model.create_table(2, 2)


if args.command == 'initdb':
    init_db()
