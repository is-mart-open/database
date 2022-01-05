import datetime
import os
from pprint import pprint
from typing import Tuple, Union

import requests
from dotenv import load_dotenv
from pytz import timezone

import database_handler
from common_data import MartData, BASE_URL, headers_user_agent


# load enviroment variables (if exist)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if os.path.exists(os.path.join(PROJECT_ROOT, '.env')):
    load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

# define common info across all mart data
KST = timezone('Asia/Seoul')
data_base_date = datetime.datetime.now(KST)
data_mart_type = 'emart'


def parse_open_time(text_start_time: str,
                    text_end_time: str,
                    data_base_date: datetime.datetime) \
                    -> Tuple[datetime.datetime, datetime.datetime]:
    time_start = datetime.datetime.strptime(text_start_time.strip(), '%H:%M')
    time_start = KST.localize(time_start.replace(year=data_base_date.year, month=data_base_date.month, day=data_base_date.day))
    time_end = datetime.datetime.strptime(text_end_time.strip(), '%H:%M')
    time_end = KST.localize(time_end.replace(year=data_base_date.year, month=data_base_date.month, day=data_base_date.day))
    
    return time_start, time_end


def parse_next_holiday(text_holiday_list: list[str], 
                       data_base_date: datetime.datetime) \
                       -> Tuple[Union[datetime.datetime, None], bool]:
    is_holiday = False
    data_base_date = data_base_date.replace(hour=0, minute=0, second=0, microsecond=0)
    holiday_list = []
    for text_holiday in filter(lambda x: len(x) > 0, text_holiday_list):
        time_holiday = datetime.datetime.strptime(text_holiday.strip(), '%Y%m%d')
        time_holiday = KST.localize(time_holiday)
        holiday_list.append(time_holiday)

    if data_base_date in set(holiday_list):
        is_holiday = True
    holiday_list.append(data_base_date)
    holiday_list = list(set(holiday_list))
    holiday_list.sort()
    if len(holiday_list) > 1:
        next_holiday_index = holiday_list.index(data_base_date) + 1
        if next_holiday_index < len(holiday_list):
            return holiday_list[next_holiday_index], is_holiday
        else:
            return None, False
    else:
        return None, False


def emart() -> None:
    payload = {
        'srchMode': 'jijum',
        'year': data_base_date.strftime('%Y'),
        'month': data_base_date.strftime('%m'),
        'jMode': 'true',
        'strConfirmYN': 'N',
        'searchType': 'EM',
        'keyword': '',
    }
    response = requests.post(BASE_URL['emart'], headers=headers_user_agent, data=payload)
    response_dict = response.json()

    mart_list = []
    for mart_data in response_dict['dataList']:
        data_mart_name = str(mart_data['NAME'])
        data_longitude = float(mart_data['MAP_Y'])
        data_latitude = float(mart_data['MAP_X'])
        data_start_time, data_end_time = parse_open_time(
            str(mart_data['OPEN_SHOPPING_TIME']), 
            str(mart_data['CLOSE_SHOPPING_TIME']), 
            data_base_date
        )
        data_next_holiday, data_is_holiday = parse_next_holiday(
            [
                str(mart_data['HOLIDAY_DAY1_YYYYMMDD']),
                str(mart_data['HOLIDAY_DAY2_YYYYMMDD']),
                str(mart_data['HOLIDAY_DAY3_YYYYMMDD'])
            ], 
            data_base_date
        )

        data: MartData = {
            'base_date': data_base_date,
            'mart_type': data_mart_type,
            'mart_name': data_mart_name,
            'longitude': data_longitude,
            'latitude': data_latitude,
            'start_time': data_start_time,
            'end_time': data_end_time,
            'next_holiday': data_next_holiday,
            'is_holiday': data_is_holiday
        }

        mart_list.append(data)
    
    #pprint(mart_list) # debug
    database_handler.insert_mart_data(mart_list)



if __name__ == '__main__':
    emart()
