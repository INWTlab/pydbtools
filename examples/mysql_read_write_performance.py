"""
In this file you find some of the test scenarios we used to develop and
understand how to retrieve/send medium sized data sets from/to a mysql
database.
"""
import string
import time
import random as rnd
from contextlib import contextmanager
from datatable import Frame
from docker import from_env

import dbrequests.mysql as mysql
import dbrequests

# Globals
DOCKER_CONFIG = {
    'image': 'mariadb:10.3',
    'name': 'test-mariadb-database',
    'ports': {3306: 3307},
    'environment': {'MYSQL_ROOT_PASSWORD': 'root', 'MYSQL_DATABASE': 'test'},
    'detach': True
}
CLIENT = from_env()
CONTAINER = CLIENT.containers.run(**DOCKER_CONFIG)
URL_PYMYSQL = 'mysql+pymysql://root:root@0.0.0.0:3307/test'
URL_MYSQLDB = 'mysql+mysqldb://root:root@0.0.0.0:3307/test'
NROW = 20000000


# Helper
@contextmanager
def stopwatch(name):
    "Time the execution of a long running function call / code block."
    start_time = time.time()
    yield
    elapsed_time = time.time() - start_time
    print('[{}] finished in {} s'.format(name, int(elapsed_time)))


def numbers(nrow):
    "Generate 'nrow' random integers."
    return [rnd.randint(0, 100000) for _ in range(nrow)]


def chars(nrow):
    "Generate 'nrow' random strings."
    return [''.join(rnd.choices(string.ascii_letters, k=8))
            for _ in range(nrow)]


DT = Frame(
    id=range(NROW),
    char1=chars(NROW),
    char2=chars(NROW),
    num1=numbers(NROW),
    num2=numbers(NROW)
)

with mysql.Database(URL_PYMYSQL) as db:
    db.send_bulk_query("""
    CREATE TABLE test.some_table
    (
        id INTEGER NOT NULL,
        char1 VARCHAR(8) NOT NULL,
        char2 VARCHAR(8) NOT NULL,
        num1 INTEGER NOT NULL,
        num2 INTEGER NOT NULL
    )
    ENGINE=InnoDB
    DEFAULT CHARSET=utf8mb4;
    """)

# The complete 20 million rows will not work on a local machine with 16GB RAM.
# This approach uses the pandas.DataFrame.to_sql method internally, the
# overhead generated by dbrequests is neglectable. We do this with 5 million
# rows and still the memory consumption is high. An additional ~4GB of RAM
# will be used for sending that data.
DF = DT[range(5000000), :].to_pandas()
with stopwatch('send data with mysqldb/DF.to_sql'):
    with dbrequests.Database(URL_PYMYSQL) as db:
        db.send_bulk_query('truncate table some_table;')
        db.send_data(DF, 'some_table')
del DF

# The following approach is not only twice as fast for 4 times the rows, it
# will also not consume any additional memory at all. Thanks to datatable and
# MySQLs LOAD DATA LOCAL INFILE.
with stopwatch('send data with pymysql/infile'):
    with mysql.Database(URL_PYMYSQL) as db:
        db.send_data(DT, 'some_table', 'truncate')


# Now we read data with pymysql and pandas.read_query method. To be fair, we
# have not tried to optimize this approach. Like with sending the data, it
# will eat up all available memory (apperently it requires >8GB). With 5
# million rows, we need ~1.6GB RAM to hold the data and an additional 800MB
# for downloading it.
with stopwatch('fetch data with pymysql/pd.read_query'):
    with dbrequests.Database(URL_PYMYSQL) as db:
        DUMP = db.send_query('select * from some_table limit 5000000;')
del DUMP


# With the new approach we reduce the memory consumption dramatically. Now for
# 20 million rows, we need ~800MB to keep the data in memory as
# datatable.Frame. And no more for fetching it. But the time it takes is
# uncceptable: ~200s.
with stopwatch('fetch data with pymysql/new approach/no pandas'):
    with mysql.Database(URL_PYMYSQL) as db:
        DUMP = db.send_query('select * from some_table;', to_pandas=False)
del DUMP


# Now repeat, but fast, please! Instead of pymysql we use mysqldb
# (mysqlclient). Now the same query takes 20s.
with stopwatch('fetch data with mysqldb/new approach/no pandas'):
    with mysql.Database(URL_MYSQLDB) as db:
        DUMP = db.send_query('select * from some_table;', to_pandas=False)
del DUMP

CONTAINER.kill()
CONTAINER.remove()
CLIENT.close()
