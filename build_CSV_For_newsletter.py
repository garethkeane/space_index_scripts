#Building CSV file that gets loaded into Google Sheets for generating tables for newsletter - hopefully helps to remove data issues from Google Finance

#First setup all the modules needed: yfinance, pandas (data), csv, datetime, and re (regex) 
import yfinance as yf
import pandas as pd
import re
import csv
import datetime
from csv import writer
from datetime import date, timedelta
#import yfinance.stock_info as si

#setup the list of tickers - using all stock tickers from other data runs
#Also want to order these alphabetically this time around
#For testing - short list
#newspace_ticker_list = ['ACHR', 'VORB']
#legacy_ticker_list = ['BA', 'VSAT']

newspace_ticker_list = ['ACHR', 'ARQQ', 'ASTR', 'ASTS', 'BKSY', 'BLDE', 'IONQ', 'JOBY', 'LILM', 'MNTS', 'PL', 'RDW', 'RKLB', 'SATL', 'SPIR', 'SPCE', 'VORB']
legacy_ticker_list = ['AJRD', 'AVAV', 'AIR.PA', 'BA', 'BA.L', 'GRMN', 'HON', 'IRDM', 'LHX', 'LMT', 'MAXR', 'NOC', 'OHB.F', 'RTX', 'SESG.PA', 'HO.PA', 'TRMB', 'VSAT']

#For testing
#newspace_ticker_list = ['ACHR']
#legacy_ticker_list = ['AJRD']

#Setup New/Legacy flag for each ticker symbol
sector = {}
for ticker in newspace_ticker_list:
	sector[ticker] = 'New Space'

for ticker in legacy_ticker_list:
	sector[ticker] = 'Legacy Space'

#ticker_list = newspace_ticker_list + legacy_ticker_list
ticker_list = newspace_ticker_list
print(ticker_list)
#ticker_list.sort()
#print(ticker_list)

#First try to get today as a date
today = date.today()
this_year = today.strftime("%Y")
this_year = this_year +"-01-01"
two_weeks_ago = today - timedelta(days=14)
thirty_days_ago = today - timedelta(days=30)

print("Today: ", today)
print ("Start of year: ", this_year)
print ("Two weeks ago: ", two_weeks_ago)
print ("Thiry days ago: ", thirty_days_ago)


ticker_data = {}

#Now try and dump the company data

with open('newsletter_table_data.csv', 'w') as output_file:
	output = 'Company Name, Ticker, Price at Start of Year, Price 30 Days Ago, Price Two Weeks Ago, Price Now\n'
	output_file.write(output)
	for ticker in ticker_list:
		print ('Working on', ticker)
		today_close = yf.download(ticker, today)['Close']
		today_close = today_close.iloc[0]
		print ("Close: ", today_close)
		today_close = str(today_close)
		start_of_year_close = yf.download(ticker, this_year)['Close']
		start_of_year_close = start_of_year_close.iloc[0]
		print ("Start of year: ", start_of_year_close)
		start_of_year_close = str(start_of_year_close)
		two_week_close = yf.download(ticker, two_weeks_ago)['Close']
		two_week_close = two_week_close.iloc[0]
		print ("Two week: ", two_week_close)
		two_week_close = str(two_week_close)
		thirty_day_close = yf.download(ticker, thirty_days_ago)['Close']
		thirty_day_close = thirty_day_close.iloc[0]
		print ("Thirty day close: ", thirty_day_close)
		thirty_day_close = str(thirty_day_close)
		ticker_object = yf.Ticker(ticker)
		#print(ticker_object.info)
		company_name = str(ticker_object.info['longName'])
		company_name = re.sub(',', '', company_name) # remove any commas that mess up csv file
		output = company_name + ',' + ticker + ',' + start_of_year_close + ',' + thirty_day_close + ',' + two_week_close + ',' + today_close + '\n'
		output_file.write(output)
	ticker_list = legacy_ticker_list
	for ticker in ticker_list:
                print ('Working on', ticker)
                today_close = yf.download(ticker, today)['Close']
                today_close = today_close.iloc[0]
                print ("Close: ", today_close)
                today_close = str(today_close)
                start_of_year_close = yf.download(ticker, this_year)['Close']
                start_of_year_close = start_of_year_close.iloc[0]
                print ("Start of year: ", start_of_year_close)
                start_of_year_close = str(start_of_year_close)
                two_week_close = yf.download(ticker, two_weeks_ago)['Close']
                two_week_close = two_week_close.iloc[0]
                print ("Two week: ", two_week_close)
                two_week_close = str(two_week_close)
                thirty_day_close = yf.download(ticker, thirty_days_ago)['Close']
                thirty_day_close = thirty_day_close.iloc[0]
                print ("Thirty day close: ", thirty_day_close)
                thirty_day_close = str(thirty_day_close)
                ticker_object = yf.Ticker(ticker)
                #print(ticker_object.info)
                company_name = str(ticker_object.info['longName'])
                company_name = re.sub(',', '', company_name) # remove any commas that mess up csv file
                output = company_name + ',' + ticker + ',' + start_of_year_close + ',' + thirty_day_close + ',' + two_week_close + ',' + today_close + '\n'
                output_file.write(output)

#Dump a timestamp to the CSV file every time this script runs
current_time = datetime.datetime.now()
time_data =['Timestamp', current_time]

with open ('newsletter_table_data.csv', 'a', newline='') as f_object:
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
sheetName = 'Data_For_Newsletter_Tables'
csvFile = 'newsletter_table_data.csv'

#sheet = client.open(spreadsheetId)
#sheet.clear(sheetName)
sheet = client.open(spreadsheetId)
active_sheet = sheet.worksheet('Data_For_Newsletter_Tables')
active_sheet.clear()

sheet.values_update (
	sheetName,
	params={'valueInputOption': 'USER_ENTERED'},
	body={'values': list(csv.reader(open(csvFile)))}
) 
