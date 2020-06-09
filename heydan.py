import requests
import csv
from collections import OrderedDict
import datetime
import os

hosturl = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv"
weeklychangesweekswanted = 19
todaytimestamp = datetime.datetime.today().strftime("%Y-%m-%d")
reportdir = "/var/www/html/misc/20200417-covid-county-analysis/"   # Blank or ending in a slash
if not os.path.exists(reportdir):
    reportdir = ""

r = requests.get(hosturl)
reader = list(csv.DictReader(r.text.splitlines()))
placeitems = [
    'UID', 'iso2', 'iso3', 'code3', 'FIPS', 'Admin2', 'Province_State', 'Country_Region', 'Lat', 'Long_', 'Combined_Key'
]
dateswanted = OrderedDict()
firstdateraw = "1/22/20"
lastdateraw = list(reader[0].keys())[-1]
firstdate = datetime.datetime.strptime(firstdateraw, "%m/%d/%y")
lastdate = datetime.datetime.strptime(lastdateraw, "%m/%d/%y")
datespread = (lastdate-firstdate).days

# Here's a problem: Windows will only give us padded dates. So we have to work around that:
for i in range(0, datespread + 1):
    actualdate = firstdate + datetime.timedelta(days=i)
    jhudate = f"{actualdate.month}/{actualdate.day}/{actualdate.strftime('%y')}"
    mydate = actualdate.strftime("%Y%m%d")
    dateswanted[mydate] = jhudate

masterdict = {}
placedict = {}
for row in reader:
    row['FIPS'] = row['FIPS'].replace(".0", "")
    fips = row['FIPS']
    placedict[fips] = OrderedDict()
    for item in placeitems:
        placedict[fips][item] = row[item]
    masterdict[fips] = OrderedDict()
    for mydate in dateswanted:
        masterdict[fips][mydate] = int(row[dateswanted[mydate]])

latestdate = lastdate
weeklylu = {}
for count in range(1, weeklychangesweekswanted + 1):
    mydate = (latestdate + datetime.timedelta(days= -7 * count)).strftime("%Y%m%d")
    weeklylu[count] = mydate
weeklylu[0] = latestdate.strftime("%Y%m%d")

weeklyreport = []
for fips in masterdict:
    line = OrderedDict()
    line['fips'] = fips
    line['county'] = placedict[fips]["Admin2"]
    line['state'] = placedict[fips]['Province_State']
    latestvalue = masterdict[fips][weeklylu[0]]
    for count in reversed(list(range(1, weeklychangesweekswanted + 1))):
        if count == 1:
            tag = "pct 1 week"
        else:
            tag = f"pct {count} weeks"
        oldvalue = masterdict[fips][weeklylu[count]]
        if oldvalue == 0:
            line[tag] = ""
        else:
            line[tag] = 100*((latestvalue - oldvalue)/oldvalue)
    for count in reversed(list(range(0, weeklychangesweekswanted + 1))):
        if count == 1:
            tag = "raw 1 week"
        else:
            tag = f"raw {count} weeks"
        line[tag] = masterdict[fips][weeklylu[count]]
#    line['latestvalue2'] = latestvalue
    weeklyreport.append(line)
        
with open(f"{reportdir}JHU-weeklychanges-{todaytimestamp}.csv", "w", newline="", encoding="utf-8") as outfile:
    writer = csv.writer(outfile)
    writer.writerow(list(line.keys()))
    for row in weeklyreport:
        writer.writerow(list(row.values()))
