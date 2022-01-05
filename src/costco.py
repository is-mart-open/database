import datetime
import os
import re
from pprint import pprint
from typing import Tuple

import requests
from bs4 import BeautifulSoup
from dateutil import relativedelta
from dotenv import load_dotenv
from lunardate import LunarDate
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
data_mart_type = 'costco'

# define regex for holiday parsing
# type1: 매월 둘째, 넷째 일요일 의무 휴무
regex_date_type1 = re.compile(r'([첫둘셋넷])째, ([첫둘셋넷])째 ([월화수목금토일])요일')
# type2: 매월 둘째 수요일, 넷째 일요일 의무 휴무
regex_date_type2 = re.compile(r'([첫둘셋넷])째 ([월화수목금토일])요일, ([첫둘셋넷])째 ([월화수목금토일])요일')
date_str_table = {
    '첫': 1,
    '둘': 2,
    '셋': 3,
    '넷': 4,
    '월': relativedelta.MO,
    '화': relativedelta.TU,
    '수': relativedelta.WE,
    '목': relativedelta.TH,
    '금': relativedelta.FR,
    '토': relativedelta.SA,
    '일': relativedelta.SU,
}


def parse_open_time(text_open_time: str, 
                    data_base_date: datetime.datetime) \
                    -> Tuple[datetime.datetime, datetime.datetime]:
    text_start_time, text_end_time = text_open_time.split('-')
    time_start = datetime.datetime.strptime(text_start_time.strip(), '오전 %I:%M')
    time_start = KST.localize(time_start.replace(year=data_base_date.year, month=data_base_date.month, day=data_base_date.day))
    time_end = datetime.datetime.strptime(text_end_time.strip(), '오후 %I:%M') + datetime.timedelta(hours=12)
    time_end = KST.localize(time_end.replace(year=data_base_date.year, month=data_base_date.month, day=data_base_date.day))
    
    return time_start, time_end


def parse_next_holiday(text_holiday: str, 
                       data_base_date: datetime.datetime) \
                       -> Tuple[datetime.datetime, bool]:
    is_holiday = False
    data_base_date = data_base_date.replace(hour=0, minute=0, second=0, microsecond=0)
    date_thismonth = data_base_date.replace(day=1)
    date_nextmonth = date_thismonth + relativedelta.relativedelta(months=1)
    date_thisyear = data_base_date.replace(month=1, day=1)
    date_nextyear = date_thisyear + relativedelta.relativedelta(years=1)
    holiday_list = [
        date_thisyear,                                          # 올해 1월 1일
        date_nextyear,                                          # 내년 1월 1일
        KST.localize(datetime.datetime.combine(
            LunarDate(date_thisyear.year, 1, 1).toSolarDate(),  # 올해 설날
            datetime.time()
        )),
        KST.localize(datetime.datetime.combine(
            LunarDate(date_nextyear.year, 1, 1).toSolarDate(),  # 내년 설날
            datetime.time()
        )),
        KST.localize(datetime.datetime.combine(
            LunarDate(date_thisyear.year, 8, 15).toSolarDate(), # 올해 추석
            datetime.time()
        )),
        KST.localize(datetime.datetime.combine(
            LunarDate(date_nextyear.year, 8, 15).toSolarDate(), # 내년 추석
            datetime.time()
        )),
    ]
    found = regex_date_type1.findall(text_holiday)
    if found: # type1: 매월 _째, _째 _요일 의무 휴무
        found = found[0]
        week_former, week_latter, day = found[0], found[1], found[2]
        holiday_list += [
            date_thismonth + 
            relativedelta.relativedelta(
                weekday = date_str_table[day](date_str_table[week_former])
            ),
            date_thismonth + 
            relativedelta.relativedelta(
                weekday = date_str_table[day](date_str_table[week_latter])
            ),
            date_nextmonth + 
            relativedelta.relativedelta(
                weekday = date_str_table[day](date_str_table[week_former])
            ),
            date_nextmonth + 
            relativedelta.relativedelta(
                weekday = date_str_table[day](date_str_table[week_latter])
            )
        ]
 
    else:     # type2: 매월 _째 _요일, _째 _요일 의무 휴무
        found = regex_date_type2.findall(text_holiday)[0]
        week_former, day_former, week_latter, day_latter = found[0], found[1], found[2], found[3]
        holiday_list += [
            date_thismonth + 
            relativedelta.relativedelta(
                weekday = date_str_table[day_former](date_str_table[week_former])
            ),
            date_thismonth + 
            relativedelta.relativedelta(
                weekday = date_str_table[day_latter](date_str_table[week_latter])
            ),
            date_nextmonth + 
            relativedelta.relativedelta(
                weekday = date_str_table[day_former](date_str_table[week_former])
            ),
            date_nextmonth + 
            relativedelta.relativedelta(
                weekday = date_str_table[day_latter](date_str_table[week_latter])
            )
        ]

    if data_base_date in set(holiday_list):
        is_holiday = True
    
    holiday_list.append(data_base_date)
    holiday_list = list(set(holiday_list))
    holiday_list.sort()
    next_holiday_index = holiday_list.index(data_base_date) + 1 # 다음 휴무일이 존재할 것을 전제
    #pprint(holiday_list) # debug
    return holiday_list[next_holiday_index], is_holiday


def costco() -> None:
    response = requests.get(BASE_URL['costco'], headers=headers_user_agent, data={})
    response_dict = response.json()

    mart_list = []
    for mart_data in response_dict['data']:
        data_mart_name = str(mart_data['displayName'])
        
        html_text = mart_data['storeContent']
        soup = BeautifulSoup(html_text, 'html.parser')
        html_ptag_list = soup.find_all('p')

        text_open_time = str(html_ptag_list[0].font.text)
        data_start_time, data_end_time = parse_open_time(text_open_time, data_base_date)
        
        text_holiday = str(html_ptag_list[-1].span.text)
        data_next_holiday, data_is_holiday = parse_next_holiday(text_holiday, data_base_date)

        data: MartData = {
            'base_date': data_base_date,
            'mart_type': data_mart_type,
            'mart_name': f'코스트코 {data_mart_name}',
            'longitude': float(mart_data['longitude']),
            'latitude': float(mart_data['latitude']),
            'start_time': data_start_time,
            'end_time': data_end_time,
            'next_holiday': data_next_holiday,
            'is_holiday': data_is_holiday
        }
        mart_list.append(data)
    
    #pprint(mart_list) # debug
    database_handler.insert_mart_data(mart_list)



if __name__ == '__main__':
    costco()
