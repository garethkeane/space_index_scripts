#Trying some Yahoo Finance stuff - first setup yfinance, pandas (data), and re (regex) 
#Revision tracker
#20220206 Added SATL to New Space list
import yfinance as yf
import pandas as pd
import re
import csv
import datetime
from csv import writer

#setup the list of tickers 
newspace_ticker_list = ['ACHR', 'ARQQ', 'ASTR', 'ASTS', 'BKSY', 'BLDE', 'IONQ', 'JOBY', 'LILM', 'MNTS', 'PL', 'RDW', 'RKLB', 'SATL', 'SPIR', 'SPCE', 'VORB']
#newspace_ticker_list = ['ACHR', 'ARQQ', 'ASTR', 'ASTS', 'BKSY', 'BLDE', 'IONQ', 'JOBY', 'LILM', 'MNTS', 'PL', 'RDW', 'RKLB', 'SPIR', 'SPCE', 'VORB']
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

data = yf.download(ticker_list, '2021-6-1')['Close']
#data[::-1]
reversed_data = data.iloc[::-1]
reversed_data.to_csv('test_not_sorted.csv')
reversed_data = reversed_data[ticker_list]
reversed_data.to_csv('test.csv')

#Now try and dump 1m daily/real-time data

daily_data = yf.download(ticker_list, period='1d', interval='1m')['Close']
reversed_daily_data = daily_data.iloc[::-1]
reversed_daily_data = reversed_daily_data[ticker_list]
reversed_daily_data.to_csv('test_daily_data.csv')
print(reversed_daily_data.head())

#print frst 5 rows of data
print(reversed_data.head())

rocket_lab = yf.Ticker("RKLB")
print(rocket_lab.info['marketCap'])

#Now try and download all company information
#for ticker in legacy_ticker_list:
#for ticker in ticker_list:
#Define short_ticker_list while testing
short_ticker_list = ['RKLB', 'LHX']
for ticker in short_ticker_list:
	ticker_object = yf.Ticker(ticker)
	print("Market Cap for ", ticker, ":", ticker_object.info['marketCap'])
	
	#convert info() output from dictionary to dataframe
	temp = pd.DataFrame.from_dict(ticker_object.info, orient="index")
	temp.reset_index(inplace=True)
	temp.columns = ["Attribute", "Recent"]
	
	#add (ticker dataframe) to main dictionary
	ticker_data[ticker] = temp

ticker_data

#Now try and write to Google Sheet
import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

credentials = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
client = gspread.authorize(credentials)

spreadsheet = client.open('Space_Index_Historical_Data__AutoUpdated')

with open('test.csv', 'r') as file_obj:
    content = file_obj.read()
    client.import_csv(spreadsheet.id, data=content)

#Now try to write out the MarketCap data to another spreadsheet
#First dump Market Caps out to a CSV file

#spreadsheet = client.open('Space_Index_Market_Cap_Data__AutoUpdated')
with open('marketcaps.csv', 'w') as output_file:
	output = 'Ticker, Company Name, Market Cap, Currency\n'
	output_file.write(output)
	for ticker in ticker_list:
		print ('Working on', ticker)
		ticker_object = yf.Ticker(ticker)
		output_market_cap = str(ticker_object.info['marketCap'])
		output_currency = ticker_object.info['currency']
		try: 
			ticker_object.info['longName']
		except KeyError:
			output_name = 'None'
			print('KeyError for: ', ticker)
		else:
			output_name = str(ticker_object.info['longName'])
		print ('Old Name: ', output_name)
		output_name = re.sub(',', '', output_name)
		print ('New Name: ', output_name)
		output = ticker + ',' + output_name + ',' + output_market_cap + ',' + output_currency + '\n'
		output_file.write(output)
		
#Dump a timestamp to the CSV file every time this script runs
current_time = datetime.datetime.now()
time_data =['Timestamp', current_time]
 
with open ('marketcaps.csv', 'a', newline='') as f_object:
	writer_object = writer(f_object)
	writer_object.writerow(time_data)
	f_object.close

with open ('test.csv', 'a', newline='') as f_object:
        writer_object = writer(f_object)
        writer_object.writerow(time_data)
        f_object.close

#with open('marketcaps.csv', 'r') as file_obj:
#	content = file_obj.read()
#	client.import_csv(spreadsheet.id, data=content)

#Try something a little different - update a specific sheet
spreadsheetId = 'Space_Index_Market_Cap_Data__AutoUpdated'
#spreadsheetId = 'https://docs.google.com/spreadsheets/d/1NjRwaeHfOVO0aXcLv0h4y2WYeCZx0KXfkyhFVDIdWlI'
sheetName = 'Test_This_Sheet'
csvFile = 'marketcaps.csv'

#sheet = client.open_by_key(spreadsheetId)
sheet = client.open(spreadsheetId)
sheet.values_update(
	sheetName,
	params={'valueInputOption': 'USER_ENTERED'},
	body={'values': list(csv.reader(open(csvFile)))}
)

#Now Update Master Spreadsheet Tabs
spreadsheetId = 'Space_Index_Master_Spreadsheet_20220107'
#First Market Cap Data
sheetName = 'Market_Cap_Data'
csvFile = 'marketcaps.csv'

sheet = client.open(spreadsheetId)
sheet.values_update (
	sheetName,
	params={'valueInputOption': 'USER_ENTERED'},
	body={'values': list(csv.reader(open(csvFile)))}
)

# Now Historical Data
sheetName = 'Historical_Data'
csvFile = 'test.csv'

sheet.values_update (
	sheetName,
	params={'valueInputOption': 'USER_ENTERED'},
	body={'values': list(csv.reader(open(csvFile)))}
)
