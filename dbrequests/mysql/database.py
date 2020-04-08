from dbrequests.database import Database as SuperDatabase
from .connection import Connection as MysqlConnection
from sqlalchemy import exc
from MySQLdb.cursors import SSCursor


class Database(SuperDatabase):
    """This class is derived from `dbrequests.Database`.

    It uses the dbrequests.mysql.Connection which implements a different
    strategy for writing data into databases (load data local infile).
    Encapsulates a url and an SQLAlchemy engine with a pool of connections.

    The url to the database can be provided directly or via a credentials-
    dictionary `creds` with keys: - host - db - user - password - dialect
    (defaults to mysql) - driver (defaults to pymysql)
    """

    def __init__(self, db_url=None, creds=None, sql_dir=None,
                 escape_percentage=False, remove_comments=False, **kwargs):
        connect_args = kwargs.pop('connect_args', {})
        connect_args["local_infile"] = 1
        connect_args["cursorclass"] = SSCursor
        if creds:
            creds['driver'] = 'mysqldb'
            creds['dialect'] = 'mysql'
        super().__init__(db_url=db_url, creds=creds, sql_dir=sql_dir,
                         connection_class=MysqlConnection,
                         escape_percentage=escape_percentage,
                         remove_comments=remove_comments,
                         connect_args=connect_args, **kwargs)
