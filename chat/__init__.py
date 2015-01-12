# -*-coding:utf8-*-


def get_config(config_file):
    with open(config_file, 'r') as f:
        data = f.read()
    config = dict()
    default = dict()
    exec '' in default
    exec data in config
    return dict((k, v) for k, v in config.iteritems() if k not in default)
