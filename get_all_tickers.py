#Trying some Yahoo Finance stuff - first setup yfinance, pandas (data), and re (regex) 
#Revision tracker
#20220206 Dump Yahoo Finance yTicker info for a single ticker symbol - testing due to issues with SATL
#		- Needed more than one ticker for the historical price stuff to work so added RKLB
import yfinance as yf
import pandas as pd
import re
import csv
import datetime
from csv import writer

#setup the list of tickers 
newspace_ticker_list = ['ACHR', 'ARQQ', 'ASTR', 'ASTS', 'BKSY', 'BLDE', 'IONQ', 'JOBY', 'LILM', 'MNTS', 'PL', 'RDW', 'RKLB', 'SATL', 'SPIR', 'SPCE', 'VORB']
#newspace_ticker_list = ['RKLB', 'SATL']
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


with open('test_all_tickers.csv', 'w') as output_file:
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
		else:
			output_name = str(ticker_object.info['longName'])
		print ('Old Name: ', output_name)
		output_name = re.sub(',', '', output_name)
		print ('New Name: ', output_name)
		output = ticker + ',' + output_name + ',' + output_market_cap + ',' + output_currency + '\n'
		output_file.write(output)
		#print(ticker_object.info)
		
#Dump a timestamp to the CSV file every time this script runs
current_time = datetime.datetime.now()
time_data =['Timestamp', current_time]
 
with open ('test_all_tickers.csv', 'a', newline='') as f_object:
	writer_object = writer(f_object)
	writer_object.writerow(time_data)
	f_object.close

