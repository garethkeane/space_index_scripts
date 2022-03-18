#Trying some Yahoo Finance stuff - first setup yfinance, pandas (data), and re (regex) 
import yfinance as yf
import pandas as pd
import re
import csv
import datetime
from csv import writer

#setup the list of tickers 
fx_ticker_list = ['EURUSD=X', 'GBPUSD=X']

ticker_data = {}

#Use extend to build the list 
ticker_list = []
ticker_list.extend(fx_ticker_list)
print(ticker_list)

#Now try and dump the exchange rate

with open('fx_data.csv', 'w') as output_file:
	output = 'Type, Rate\n'
	output_file.write(output)
	for ticker in ticker_list:
		print ('Working on', ticker)
		ticker_object = yf.Ticker(ticker)
		exchange_rate = str(ticker_object.history(period='1d')['Close'])
		exchange_rate = exchange_rate.split()
		exchange_rate = exchange_rate[2]
		print ('Ticker:', ticker) 
		print ('Exchange Rate:', exchange_rate)
		output = ticker + ',' + exchange_rate + '\n'
		output_file.write(output)

#Dump a timestamp to the CSV file every time this script runs
current_time = datetime.datetime.now()
time_data =['Timestamp', current_time]

with open ('fx_data.csv', 'a', newline='') as f_object:
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
sheetName = 'FX_Data'
csvFile = 'fx_data.csv'

#sheet = client.open(spreadsheetId)
#sheet.clear(sheetName)
sheet = client.open(spreadsheetId)
active_sheet = sheet.worksheet('FX_Data')
active_sheet.clear()

sheet.values_update (
	sheetName,
	params={'valueInputOption': 'USER_ENTERED'},
	body={'values': list(csv.reader(open(csvFile)))}
) 
