import datetime
from typing import TypedDict


# define data structure for mart data
class MartData(TypedDict):
    base_date: datetime.datetime
    mart_type: str
    mart_name: str
    longitude: float
    latitude: float
    start_time: datetime.datetime
    end_time: datetime.datetime
    next_holiday: datetime.datetime

BASE_URL = {
    'emart': 'https://store.emart.com/branch/searchList.do',
    'homeplus': 'https://corporate.homeplus.co.kr/STORE/HyperMarket.aspx',
    'costco': 'https://www.costco.co.kr/store-finder/search?q=',
    'emart_everyday_list': 'http://www.emarteveryday.co.kr/branch/searchBranch.jsp',
    'emart_everyday_info': 'http://www.emarteveryday.co.kr/branch/branchView.jsp'
}
