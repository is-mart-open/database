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
