#Trying some Yahoo Finance stuff - first setup yfinance, pandas (data), and re (regex) 
import yfinance as yf
import pandas as pd
import re
import csv
import datetime
from csv import writer

#setup the list of tickers 
newspace_ticker_list = ['ACHR', 'ARQQ', 'ASTR', 'ASTS', 'BKSY', 'BLDE', 'IONQ', 'JOBY', 'LILM', 'MNTS', 'PL', 'RDW', 'RKLB', 'SPIR', 'SPCE', 'VORB']
legacy_ticker_list = ['AJRD', 'AVAV', 'AIR.PA', 'BA', 'BA.L', 'GRMN', 'HON', 'IRDM', 'LHX', 'LMT', 'MAXR', 'NOC', 'OHB.F', 'RTX', 'SESG.PA', 'HO.PA', 'TRMB', 'VSAT']
index_ticker_list = ['^IXIC', '^GSPC']

ticker_data = {}

#Combine newspace and legacy tickers to get everything in one shot

#This seems to sort the list entries alphabetically so mixes newspace and legacy
#ticker_list = newspace_ticker_list + legacy_ticker_list

#Try to extend the list instead
ticker_list = []
ticker_list.extend(newspace_ticker_list)
ticker_list.extend(legacy_ticker_list)
ticker_list.extend(index_ticker_list)
print(ticker_list)

#Now try and dump close price for a given date

date_close_data = yf.download(ticker_list,'2022-01-01', '2022-01-03'  )['Close']
reversed_daily_data = daily_data.iloc[::-1]
reversed_daily_data = reversed_daily_data[ticker_list]
reversed_daily_data.to_csv('test_daily_data.csv')
print(reversed_daily_data.head())

#Dump a timestamp to the CSV file every time this script runs
current_time = datetime.datetime.now()
time_data =['Timestamp', current_time]

with open ('test_daily_data.csv', 'a', newline='') as f_object:
	writer_object = writer(f_object)
	writer_object.writerow(time_data)
	f_object.close

#Now try and write to Google Sheet
import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

credentials = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
client = gspread.authorize(credentials)

#Now Update Master Spreadsheet Tabs
spreadsheetId = 'Space_Index_Master_Spreadsheet_20220107'

# Now Dump 1m daily xidData to spreadsheet
sheetName = 'Intraday_Data'
csvFile = 'test_daily_data.csv'

#sheet = client.open(spreadsheetId)
#sheet.clear(sheetName)
sheet = client.open(spreadsheetId)
active_sheet = sheet.worksheet('Intraday_Data')
active_sheet.clear()

sheet.values_update (
	sheetName,
	params={'valueInputOption': 'USER_ENTERED'},
	body={'values': list(csv.reader(open(csvFile)))}
) 
