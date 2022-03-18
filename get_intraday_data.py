#Trying some Yahoo Finance stuff - first setup yfinance, pandas (data), and re (regex) 
#Revision Tracker
# 20220206 Added SATL to New Space list
# 20220207 Added a check for 'Close' being reported as exchange rate - will not update google doc if that is the case
import yfinance as yf
import pandas as pd
import re
import csv
import datetime
from csv import writer

#setup the list of tickers 
newspace_ticker_list = ['ACHR', 'ARQQ', 'ASTR', 'ASTS', 'BKSY', 'BLDE', 'IONQ', 'JOBY', 'LILM', 'MNTS', 'PL', 'RDW', 'RKLB', 'SATL', 'SPIR', 'SPCE', 'VORB']
legacy_ticker_list = ['AJRD', 'AVAV', 'AIR.PA', 'BA', 'BA.L', 'GRMN', 'HON', 'IRDM', 'LHX', 'LMT', 'MAXR', 'NOC', 'OHB.F', 'RTX', 'SESG.PA', 'HO.PA', 'TRMB', 'VSAT']
index_ticker_list = ['^IXIC', '^GSPC']

#Also do FX data dump 
fx_ticker_list = ['EURUSD=X', 'GBPUSD=X']

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

#Now try and dump 1m daily/real-time data

daily_data = yf.download(ticker_list, period='1d', interval='1m')['Close']
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

# Now do FX stuff
# Default is not to write to google spreadsheet, only do this if exchange rate is valid - keep old data
# Due to issue with getting "Close" instead of a number
write_to_google_doc = 'no'

with open('fx_data.csv', 'w') as output_file:
        output = 'Type, Rate\n'
        output_file.write(output)
        for ticker in fx_ticker_list:
                print ('Working on', ticker)
                ticker_object = yf.Ticker(ticker)
                exchange_rate = str(ticker_object.history(period='1d')['Close'])
                exchange_rate = exchange_rate.split()
                exchange_rate = exchange_rate[2]
                if(exchange_rate == 'Close,'):
                        write_to_google_doc = 'no'
                        exchange_rate_local = str(ticker_object.history(period='1d')['Close'])
                        print('No good exchange rate:', exchange_rate_local)
                else:
                        write_to_google_doc = 'yes'
                print ('Ticker:', ticker)
                print ('Exchange Rate:', exchange_rate)
                output = ticker + ',' + exchange_rate + '\n'
                output_file.write(output)

with open ('fx_data.csv', 'a', newline='') as f_object:
        writer_object = writer(f_object)
        writer_object.writerow(time_data)
        f_object.close

# Now Dump latest FX data to spreadsheet
sheetName = 'FX_Data'
csvFile = 'fx_data.csv'

if (write_to_google_doc == 'yes'):
	#First clear existing sheet data on FX_Data Tab
	sheet = client.open(spreadsheetId)
	active_sheet = sheet.worksheet('FX_Data')
	active_sheet.clear()

	sheet.values_update (
        	sheetName,
        	params={'valueInputOption': 'USER_ENTERED'},
        	body={'values': list(csv.reader(open(csvFile)))}
	)
else:
	print('No good exchange rate!')	
