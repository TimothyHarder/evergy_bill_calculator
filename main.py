"""
This code was written to compare my bills against what my power company advertises the rates to be,
and to give more detail on the charges than their bills do.

I in no way guarantee the accuracy of this information, nor is this code meant for anything but personal use.
"""
import copy
import re
import datetime

import tabulate
from selenium import webdriver
from selenium.webdriver.firefox.options import  Options
# from selenium.webdriver.common.keys import Keys

'''
1. Retail Energy Cost Adjustment
    RECA Factor / Fuel Adjustment
    Set Quarterly
    0.016149/kWh

2. Property Tax Surcharge
    PTS Factor
    0.00123/kWh

3. Transmission Delivery Charge
    Set Every July 1.
    0.018810/kWh

4. Environmental Cost Recovery Rider
    NOT APPLICABLE :D

5. Renewable Energy Program Rider
    NOT APPLICABLE :D

6. Energy Efficiency Rider
    Set Every November.
    $0.000199/kWh

7. Tax Adjustment
    Collected through TDC

City Tax
1.625%

County Tax
1.475%

Basic Service Fee
14.50/bill

City Franchise Fee
7.27/bill

Rate information:
https://www.evergy.com/manage-account/rate-information/plan-options/standard-plan?hasTerritory=true
MUST set region

Fee information:
https://www.evergy.com/manage-account/rate-information/how-rates-are-set/rate-overviews/rate-riders-and-adjustments
MUST set region

'''

rates = {
    "500": 0,
    "900": 0,
    "900+": 0,
    "BS": 0,
    "FA": 0,
    "TDC": 0,
    "PTS": 0,
    "EE": 0,
    "CF": 7.27,
    "CI_TAX": 0.01625,
    "CO_TAX": 0.01475,
}

friendly_rate_names = {
    "500": "Per kWh up to 500kW",
    "900": "Per kWh up to 900kW",
    "900+": "Per kWh after 900kW",
    "BS": "Basic Service Fee",
    "FA": "Retail Energy Cost / Fuel Adjustment (Per kWh)",
    "TDC": "Transmission Delivery Charge (Per kWh)",
    "PTS": "Property Tax Surcharge (Per kWh)",
    "EE": "Energy Efficiency Rider (Per kWh)",
    "CF": "City Franchise Fee",
    "CI_TAX": "City Tax",
    "CO_TAX": "County Tax",
    "subtotal": "Subtotal",
    "total": "Total",
}


def get_season(month=None):
    print(month)
    if not month:
        month = datetime.datetime.now().strftime('%B')

    summer_months = ['june', 'july', 'august', 'september']
    if month.lower() in summer_months:
        return 'summer'
    else:
        return 'winter'


def get_info_from_kcpl(month=None):
    options = Options()
    options.headless = False

    driver = webdriver.Firefox(options=options, executable_path="/Users/Harder/bin/geckodriver")

    driver.get(f"https://www.evergy.com/manage-account/rate-information/plan-options/standard-plan?hasTerritory=true")

    # driver.find_element_by_name("Select Your Location").click()
    driver.find_element_by_xpath('//button[normalize-space()="Select Your Location"]').click()
    driver.find_element_by_xpath('//label[normalize-space()="Kansas Central"]').click()

    table_rows = driver.find_elements_by_tag_name("tr")

    i_rate_map = {
        1: "BS",
        3: "500",
        4: "900",
        5: "900+",
    }

    season_dependent = [3, 4, 5]

    dollar_re = r"\$(\d+\.\d+)"
    season = get_season(month)
    print(f"Getting rates for the {season.title()} season. ")

    for i in range(0, len(table_rows)):
        matches = re.findall(dollar_re, table_rows[i].text)
        price_index = 0
        if i in season_dependent:
            if season == 'winter':
                price_index = 1

        if i in i_rate_map.keys():
            rates[i_rate_map[i]] = matches[price_index]

    driver.get("https://www.evergy.com/manage-account/rate-information/how-rates-are-set/rate-overviews/rate-riders-and-adjustments")

    tables = driver.find_elements_by_tag_name("table")

    i = 0
    i_table_map = {
        0: "FA",
        1: "TDC",
        3: "PTS",
        4: "EE",
    }

    matches = None
    for i in range(0, len(tables)):
        rows = tables[i].find_elements_by_tag_name("tr")
        matches = re.findall(dollar_re, rows[1].text)
        if i in i_table_map.keys():
            rates[i_table_map[i]] = matches[0]

    driver.quit()


def calculate_bill(kWh):
    headers = ["Charge", "Cost", "Amount"]
    data = []

    pkwh_charges = ["FA", "TDC", "PTS", "EE"]
    pb_charges = ["BS", "CF"]
    taxes = ["CI_TAX", "CO_TAX"]

    kWh = int(kWh)

    rate_costs = copy.deepcopy(rates)
    for rate in rate_costs:
        rate_costs[rate] = 0

    if kWh <= 500:
        rate_costs['500'] = kWh * float(rates['500'])
    else:
        rate_costs['500'] = 500 * float(rates['500'])
        if kWh <= 900:
            rate_costs['900'] = (kWh - 500) * float(rates['900'])
        else:
            rate_costs['900'] = 400 * float(rates['900'])
            rate_costs['900+'] = (kWh - 900) * float(rates['900+'])

    for pkwh_charge in pkwh_charges:
        rate_costs[pkwh_charge] = kWh * float(rates[pkwh_charge])

    for rate in pb_charges:
        rate_costs[rate] = float(rates[rate])

    rate_costs['subtotal'] = 0
    for charge in (pkwh_charges + pb_charges + ["500", "900", "900+"]):
        rate_costs['subtotal'] += float(rate_costs[charge])

    rate_costs['total'] = rate_costs['subtotal']
    for tax in taxes:
        rate_costs[tax] = rate_costs['subtotal'] * float(rates[tax])
        rate_costs['total'] += rate_costs['subtotal'] * float(rates[tax])

    for cost in rate_costs:
        if cost == "subtotal" or cost == "total":
            rate = ""
        elif 'tax' in cost.lower():
            rate = f"{str(rates[cost] * 100)[:5]}%"
        else:
            rate = f"${rates[cost]}"

        data.append([friendly_rate_names[cost], f"{rate}", rate_costs[cost]])

    print('\n')
    print(f"Bill for {kwh_charged}kWh")
    print(tabulate.tabulate(data, headers=headers))


get_info_from_kcpl(month="October")

kwh_charged = "1177"

print(rates)
calculate_bill(kwh_charged)
