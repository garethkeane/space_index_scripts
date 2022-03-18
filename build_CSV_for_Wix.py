#Building CSV file that gets loaded into Google Sheets and then drives a Wix table
#Revision Tracker
# 20220206 Added SATL to New Space list

#First setup all the modules needed: yfinance, pandas (data), csv, datetime, and re (regex) 
import yfinance as yf
import pandas as pd
import re
import csv
import datetime
from csv import writer
#import yfinance.stock_info as si

#setup the list of tickers - using all stock tickers from other data runs
#Also want to order these alphabetically this time around
#For testing - short list
#newspace_ticker_list = ['ACHR', 'VORB']
#legacy_ticker_list = ['BA', 'VSAT']

newspace_ticker_list = ['ACHR', 'ARQQ', 'ASTR', 'ASTS', 'BKSY', 'BLDE', 'IONQ', 'JOBY', 'LILM', 'MNTS', 'PL', 'RDW', 'RKLB', 'SATL', 'SPIR', 'SPCE', 'VORB']
#newspace_ticker_list = ['ACHR', 'ARQQ', 'ASTR', 'ASTS', 'BKSY', 'BLDE', 'IONQ', 'JOBY', 'LILM', 'MNTS', 'PL', 'RDW', 'RKLB', 'SPIR', 'SPCE', 'VORB']
legacy_ticker_list = ['AJRD', 'AVAV', 'AIR.PA', 'BA', 'BA.L', 'GRMN', 'HON', 'IRDM', 'LHX', 'LMT', 'MAXR', 'NOC', 'OHB.F', 'RTX', 'SESG.PA', 'HO.PA', 'TRMB', 'VSAT']

#Setup New/Legacy flag for each ticker symbol
sector = {}
for ticker in newspace_ticker_list:
	sector[ticker] = 'New Space'

for ticker in legacy_ticker_list:
	sector[ticker] = 'Legacy Space'

ticker_list = newspace_ticker_list + legacy_ticker_list
print(ticker_list)
ticker_list.sort()
print(ticker_list)

ticker_data = {}

#Use extend to build the list 

#Now try and dump the company data

with open('wix_table_data.csv', 'w') as output_file:
	with open('wix_bad_table_data.csv', 'w') as output_file_no_data:
		output = 'Company Name, Ticker, Yahoo Finance URL, Market Cap, LTM Revenue Multiple, Quarterly Revenue Growth (YoY), Category, EV to EBITDA\n'
		output_file.write(output)
		output_file_no_data.write(output)
		for ticker in ticker_list:
			print ('Working on', ticker)
			ticker_object = yf.Ticker(ticker)
			#print(ticker_object.info)
			market_cap = str(ticker_object.info['marketCap'])
			company_name = str(ticker_object.info['longName'])
			company_name = re.sub(',', '', company_name) # remove any commas that mess up csv file
			company_sector = sector[ticker]
			company_TTM = str(ticker_object.info['priceToSalesTrailing12Months'])
			company_ev2ebitda = str(ticker_object.info['enterpriseToEbitda'])
			#company_growth = str(ticker_object.info['revenueGrowth'])
			try:
				ticker_object.info['revenueGrowth']
			except KeyError:
				company_growth = 'None'
			else:
				company_growth = str(ticker_object.info['revenueGrowth'])
			company_url = "https://finance.yahoo.com/quote/" + ticker
			output = company_name + ',' + ticker + ',' + company_url + ',' + market_cap + ',' + company_TTM + ',' + company_growth + ',' + company_sector + ',' + company_ev2ebitda + '\n'
			if (company_TTM == "None"):
				#do nothing
				company_TTM = company_TTM
			else:
				company_TTM = float(company_TTM) #convert back to integer to check value in if statement below
			if (company_TTM == "None") or (company_growth == "None") or (company_TTM > 300):
				output_file_no_data.write(output)
				print('Here: ', ticker)
				print('company_TTM: ', company_TTM)
				print('company_growth: ', company_growth)
			else:
				output_file.write(output)

#Dump a timestamp to the CSV file every time this script runs
current_time = datetime.datetime.now()
time_data =['Timestamp', current_time]

with open ('wix_table_data.csv', 'a', newline='') as f_object:
	writer_object = writer(f_object)
	writer_object.writerow(time_data)
	f_object.close

with open('wix_bad_table_data.csv', 'a') as f_object:
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

#Updatig two different tabs of this spreadsheet 
sheetName = 'Test_Updating_Wix'
csvFile = 'wix_table_data.csv'

sheetName_bad_data = 'Test_Updating_Wix_No_Metrics'
csvFile_bad_data = 'wix_bad_table_data.csv'

#sheet = client.open(spreadsheetId)
#sheet.clear(sheetName)
sheet = client.open(spreadsheetId)
active_sheet = sheet.worksheet('Test_Updating_Wix')
active_sheet.clear()

active_sheet = sheet.worksheet('Test_Updating_Wix_No_Metrics')
active_sheet.clear()

sheet.values_update (
	sheetName,
	params={'valueInputOption': 'USER_ENTERED'},
	body={'values': list(csv.reader(open(csvFile)))}
) 

sheet.values_update (
	sheetName_bad_data,
	params={'valueInputOption': 'USER_ENTERED'},
	body={'values': list(csv.reader(open(csvFile_bad_data)))}
)
