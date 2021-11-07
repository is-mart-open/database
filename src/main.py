import requests


# col
# id, base_date, mart_type, mart_name, loc, start_time, end_time, next_holiday

# mart_type
# emart, traders, homeplus, costco, emart_everyday

BASE_URL = {
    'emart': 'https://store.emart.com/branch/searchList.do',
    'homeplus': 'https://corporate.homeplus.co.kr/STORE/HyperMarket.aspx',
    'costco': 'https://www.costco.co.kr/store-finder/search?q=',
    'emart_everyday_list': 'http://www.emarteveryday.co.kr/branch/searchBranch.jsp',
    'emart_everyday_info': 'http://www.emarteveryday.co.kr/branch/branchView.jsp'
}


response = requests.get(BASE_URL['costco'], data={})

print(len(response.json()['data']))

