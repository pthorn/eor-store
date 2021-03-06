# coding: utf-8

class Config(object):
    """
    from eor_rest import config as rest_config
    from eor.models import Session
    rest_config.sqlalchemy_session = Session
    """

    def __init__(self):
        self.sqlalchemy_session = None
        self.sqlalchemy_base = None
        self.subdirs = 3
        self.subdir_chars = 3

        try:
            from eor.models import Session, Base
            self.sqlalchemy_session = Session
            self.sqlalchemy_base = Base
        except ImportError:
            pass

config = Config()
