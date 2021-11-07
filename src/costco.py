import datetime
import re
from pprint import pprint
from typing import Tuple, TypedDict, Union

import requests
from bs4 import BeautifulSoup
from dateutil import relativedelta
from pytz import timezone

from config import BASE_URL


# define data structure for mart data
class MartData(TypedDict):
    base_date: datetime.datetime
    mart_type: str
    mart_name: str
    loc: Tuple[float, float]
    start_time: datetime.datetime
    end_time: datetime.datetime
    next_holiday: datetime.datetime

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
                       -> datetime.datetime:
    date_thismonth = data_base_date.replace(day=1)
    holiday_list = []
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
            )
        ]

    holiday_list.append(data_base_date)
    holiday_list.sort()
    next_holiday_index = min(holiday_list.index(data_base_date) + 1, len(holiday_list) - 1)
    return holiday_list[next_holiday_index]


def main() -> None:
    response = requests.get(BASE_URL['costco'], data={})
    response_dict = response.json()

    mart_list = []
    for mart_data in response_dict['data']:
        data_mart_name = str(mart_data['displayName'])
        data_loc = (float(mart_data['latitude']), float(mart_data['longitude']))
        
        html_text = mart_data['storeContent']
        soup = BeautifulSoup(html_text, 'html.parser')
        html_ptag_list = soup.find_all('p')

        text_open_time = str(html_ptag_list[0].font.text)
        data_start_time, data_end_time = parse_open_time(text_open_time, data_base_date)
        
        text_holiday = str(html_ptag_list[-1].span.text)
        data_next_holiday = parse_next_holiday(text_holiday, data_base_date)

        data: MartData = {
            'base_date': data_base_date,
            'mart_type': data_mart_type,
            'mart_name': data_mart_name,
            'loc': data_loc,
            'start_time': data_start_time,
            'end_time': data_end_time,
            'next_holiday': data_next_holiday
        }
        mart_list.append(data)
    
    pprint(mart_list)


# data: MartData = {
#     'base_date': datetime.datetime.now(KST),
#     'mart_type': '',
#     'mart_name': 'None',
#     'loc': (0, 0),
#     'start_time': temp,
#     'end_time': temp,
#     'next_holiday': temp
# }


if __name__ == '__main__':
    main()