import datetime
from typing import TypedDict, Union


# define data structure for mart data
class MartData(TypedDict):
    base_date: datetime.datetime
    mart_type: str
    mart_name: str
    longitude: float
    latitude: float
    start_time: datetime.datetime
    end_time: datetime.datetime
    next_holiday: Union[datetime.datetime, None]
    is_holiday: bool

BASE_URL = {
    'emart': 'https://store.emart.com/branch/searchList.do',
    'homeplus': 'https://corporate.homeplus.co.kr/STORE/HyperMarket.aspx',
    'costco': 'https://www.costco.co.kr/store-finder/search?q=',
    'emart_everyday_list': 'http://www.emarteveryday.co.kr/branch/searchBranch.jsp',
    'emart_everyday_info': 'http://www.emarteveryday.co.kr/branch/branchView.jsp'
}

headers_user_agent = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15'
}