import os
from typing import Tuple

import psycopg
from dotenv import load_dotenv
from psycopg.types.shapely import register_shapely

from common_data import MartData


# load enviroment variables (if exist)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if os.path.exists(os.path.join(PROJECT_ROOT, '.env')):
    load_dotenv(os.path.join(PROJECT_ROOT, '.env'))


def __generate_martdata_insert_query_data(mart_data: MartData) -> dict:
    query_data = {
        'base_date': mart_data['base_date'].strftime('%Y-%m-%d %H:%M:%S %Z'),
        'mart_type': mart_data['mart_type'],
        'mart_name': mart_data['mart_name'],
        'loc': f"POINT({mart_data['longitude']} {mart_data['latitude']})",
        'start_time': mart_data['start_time'].strftime('%Y-%m-%d %H:%M:%S %Z'),
        'end_time': mart_data['end_time'].strftime('%Y-%m-%d %H:%M:%S %Z'),
        'next_holiday': mart_data['next_holiday'].strftime('%Y-%m-%d %H:%M:%S %Z') if mart_data['next_holiday'] is not None else None,
        'is_holiday': mart_data['is_holiday']
    }
    # print(query_data) # debug
    return query_data


def insert_mart_data(mart_list: list[MartData], mart_type: str) -> None:
    query_str = '''
        INSERT INTO mart (base_date, mart_type, mart_name, loc, start_time, end_time, next_holiday, is_holiday)
        VALUES (%(base_date)s::timestamptz, %(mart_type)s::varchar, %(mart_name)s::varchar, ST_GeomFromText(%(loc)s, 4326), %(start_time)s::timestamptz, %(end_time)s::timestamptz, %(next_holiday)s::timestamptz, %(is_holiday)s::boolean)
        ON CONFLICT (mart_name) 
        DO 
        UPDATE SET base_date=%(base_date)s::timestamptz, mart_type=%(mart_type)s::varchar, loc=ST_GeomFromText(%(loc)s, 4326), start_time=%(start_time)s::timestamptz, end_time=%(end_time)s::timestamptz, next_holiday=%(next_holiday)s::timestamptz, is_holiday=%(is_holiday)s::boolean;
    '''
    assert all([mart_type == mart['mart_type'] for mart in mart_list])

    assert os.environ.get('DATABASE_URL') is not None
    with psycopg.connect(os.environ.get('DATABASE_URL')) as conn:
        info = psycopg.types.TypeInfo.fetch(conn, 'geometry')
        assert info is not None
        register_shapely(info, conn)
        with conn.cursor() as cur:
            mart_data_list = []
            for mart_data in mart_list:
                mart_data_list.append(__generate_martdata_insert_query_data(mart_data))
            cur.executemany(query_str, mart_data_list)

            conn.commit()
