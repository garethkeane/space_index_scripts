#Trying some Yahoo Finance stuff - first setup yfinance, pandas (data), and re (regex) 
#Revision tracker
#20220206 Added SATL to New Space list
#20220318 Fork and get last 60 days of 15m data
#20220322 Move back to closing price once daily - change of plan!
#20220326 Update to merge some of the code that is run daily to drive the Google Sheet flow with the graphing flow - want to make sure data matches
#20220404 Update to also spit out some metrics for various indices to include as a table in the website
#20220413 Dump a .csv of the various new and legacy index weights for making sure there are no discrepancies

import yfinance as yf
import pandas as pd
import re
import csv
import datetime
from csv import writer
import shutil
import plotly.express as px

#setup the list of tickers 
newspace_ticker_list = ['ACHR', 'ARQQ', 'ASTR', 'ASTS', 'BKSY', 'BLDE', 'IONQ', 'JOBY', 'LILM', 'MNTS', 'PL', 'RDW', 'RKLB', 'SATL', 'SPIR', 'SPCE', 'VORB']
legacy_ticker_list = ['AJRD', 'AVAV', 'AIR.PA', 'BA', 'BA.L', 'GRMN', 'HON', 'IRDM', 'LHX', 'LMT', 'MAXR', 'NOC', 'OHB.F', 'RTX', 'SESG.PA', 'HO.PA', 'TRMB', 'VSAT']
index_ticker_list = ['^IXIC', '^GSPC']
#For testing - small size lists 
#newspace_ticker_list =['ACHR', 'SATL']
#legacy_ticker_list = ['AJRD', 'AIR.PA', 'BA.L']
ticker_data = {}

#work with new space, legacy space and index components seperately for this script
#But get their data all at once to make sure that there are no gaps
ticker_list = []
ticker_list.extend(newspace_ticker_list)
ticker_list.extend(legacy_ticker_list)
ticker_list.extend(index_ticker_list)
print(ticker_list)

#data = yf.download(ticker_list, '2021-6-1', '2022-3-24')['Close']
data = yf.download(ticker_list, '2021-6-1')['Close']

#look at 7/5/2021 to see what's going on
#july_five = data.iloc[24]
#print(july_five)

#First pad the closing price dataframe so no missing data (eg holidays in the US and not in Europe, etc)
#Had to add 'inplace = True' to get it to replace into the dataframe

data.fillna(method='pad', inplace=True)

#now look again
#print(july_five)

#data[::-1]
reversed_data = data.iloc[::-1]
#reversed_data = data
reversed_data.to_csv('test_not_sorted.csv')
reversed_data = reversed_data[ticker_list]
reversed_data.to_csv('test.csv')

##########
#
#Add some stuff from original script to make sure Google Sheets data and the graphs generated here are synced
#
##########

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

###########
#
# Now back to graphing script
#
##########

#Now try and get market caps for new space companies
#Use a flag to spot bad market cap data
bad_market_cap_data_flag = 'False'

#Define newspace_market_cap dict
newspace_market_cap = {}

with open('newspace_marketcaps.csv', 'w') as output_file:
  output = 'Ticker, Company Name, Market Cap, Currency\n'
  output_file.write(output)
  for ticker in newspace_ticker_list:
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
    if (output_market_cap == 'None'):
      print('In bad market cap loop for', output_name)
      bad_market_cap_data_flag = 'True'
    output = ticker + ',' + output_name + ',' + output_market_cap + ',' + output_currency + '\n'
    output_file.write(output)
    newspace_market_cap[ticker] = output_market_cap 

#Dump a timestamp to the CSV file every time this script runs
current_time = datetime.datetime.now()
time_data =['Timestamp', current_time]

with open ('newspace_marketcaps.csv', 'a', newline='') as f_object:
        writer_object = writer(f_object)
        writer_object.writerow(time_data)
        f_object.close

if (bad_market_cap_data_flag == 'False'):
	print('Copying new space market cap data')
	shutil.copy('newspace_marketcaps.csv', 'last_golden_newspace_market_caps.csv')

#Now time to make sure we have good data for all new space market caps
if (bad_market_cap_data_flag == 'True'):
	marketcap_df = pd.read_csv('last_golden_newspace_market_caps.csv')
	#print(marketcap_df)
	for ticker in newspace_ticker_list:
		if(newspace_market_cap[ticker] == 'None'):
			print('Replacing market cap for', ticker)
			print('Was:', newspace_market_cap[ticker])
			#marketcap_df.set_index('Ticker', inplace=True)
			newspace_market_cap[ticker] = marketcap_df.loc[marketcap_df['Ticker']==ticker][' Market Cap'].values[0]
			print('Now:', newspace_market_cap[ticker])

#Now get FX Data from Yahoo
fx_ticker_list = ['EURUSD=X', 'GBPUSD=X']
bad_exchange_rate_flag = 'False'
exchange_rates = {}

with open('fx_data.csv', 'w') as output_file:
	output = 'Type,Rate\n'
	output_file.write(output)
	for ticker in fx_ticker_list:
		ticker_object = yf.Ticker(ticker)
		exchange_rate = str(ticker_object.history(period='1d')['Close'])
		exchange_rate = exchange_rate.split()
		exchange_rate = exchange_rate[2]
		if (exchange_rate == 'Close,'):
			bad_exchange_rate_flag = 'True'
			exchange_rates[ticker] = 'None'
		else:
			exchange_rates[ticker] = float(exchange_rate) #make sure we can do arithmetic with this - needs to be a number
		output = ticker + ',' + exchange_rate + '\n'
		output_file.write(output)

with open('fx_data.csv', 'a',newline='') as f_object:
	write_object = writer(f_object)
	write_object.writerow(time_data)
	f_object.close

#Now check and get good exchange rate data if needed
if (bad_exchange_rate_flag == 'True'):
	exchangerate_df = pd.read_csv('golden_fx_data.csv')
	for ticker in fx_ticker_list:
		if (exchange_rates[ticker] == 'None'):
			print('Replacing exchange rate for:', ticker)
			exchange_rates[ticker] = exchangerate_df.loc[exchangerate_df['Type']==ticker]['Rate'].values=0
			print('Now:', exchange_rates[ticker])

#Now get total market cap of new space companies and build weights
total_newspace_market_cap = 0

for ticker in newspace_ticker_list:
	newspace_market_cap[ticker] = int(newspace_market_cap[ticker])
	total_newspace_market_cap = total_newspace_market_cap + newspace_market_cap[ticker]

print('Total New Space Market Cap:', total_newspace_market_cap)

#Now get weights
newspace_index_weights = {}
weight_check = 0

for ticker in newspace_ticker_list:
	newspace_index_weights[ticker] = newspace_market_cap[ticker]/total_newspace_market_cap
	print(ticker, ':', newspace_index_weights[ticker])
	weight_check = weight_check + newspace_index_weights[ticker]

print('Weight check:', weight_check)

#Try to dump these weights to a file
with open('newspace_index_weight_data.csv', 'w') as output_file:
	output = 'Ticker, Weight\n'
	output_file.write(output)
	for ticker in newspace_ticker_list:
		weight_text = str(newspace_index_weights[ticker])
		output = ticker + ',' + weight_text + '\n'
		output_file.write(output) 


#Now time to build the new space index

#First pad the closing price dataframe so no missing data (holidays, etc)

#data.fillna(method='pad')
newspace_index = pd.DataFrame(columns = ['Date', 'Value'])

#Now try to add a calculated value for the new space index
data = data.reset_index()
for index, row in data.iterrows():
	newspace_index_value = 0
	for ticker in newspace_ticker_list:
		contribution = row[ticker] * newspace_index_weights[ticker]
		newspace_index_value = newspace_index_value + contribution
	print(row['Date'], ':', newspace_index_value)
	newspace_index = newspace_index.append({'Date':row['Date'], 'Value': newspace_index_value}, ignore_index=True)


#Now try and get market caps for legacy space companies
#Use a flag to spot bad market cap data
bad_legacy_market_cap_data_flag = 'False'

#Define legacy_market_cap dict
legacy_market_cap = {}

with open('legacy_marketcaps.csv', 'w') as output_file:
  output = 'Ticker, Company Name, Market Cap, Currency\n'
  output_file.write(output)
  for ticker in legacy_ticker_list:
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
    if (output_market_cap == 'None'):
      print('In bad market cap loop for', output_name)
      bad_legacy_market_cap_data_flag = 'True'
    output = ticker + ',' + output_name + ',' + output_market_cap + ',' + output_currency + '\n'
    output_file.write(output)
    #Do exchange rate conversion here as have all the data
    if(output_currency == 'EUR'):
      print('updating market cap for ', ticker, ' was ', output_market_cap) 
      output_market_cap = int(output_market_cap)
      output_market_cap = output_market_cap * exchange_rates['EURUSD=X']
      print('Market cap for ', ticker, ' is now ', output_market_cap)
    if(output_currency == 'GBp'):
      output_market_cap = int(output_market_cap)
      output_market_cap = output_market_cap * exchange_rates['GBPUSD=X']
    legacy_market_cap[ticker] = output_market_cap

#Dump a timestamp to the CSV file every time this script runs
current_time = datetime.datetime.now()
time_data =['Timestamp', current_time]

with open ('legacy_marketcaps.csv', 'a', newline='') as f_object:
        writer_object = writer(f_object)
        writer_object.writerow(time_data)
        f_object.close

if (bad_legacy_market_cap_data_flag == 'False'):
        print('Copying legacy space market cap data')
        shutil.copy('legacy_marketcaps.csv', 'last_golden_legacy_market_caps.csv')

#Now time to make sure we have good data for all legacy space market caps
if (bad_legacy_market_cap_data_flag == 'True'):
        marketcap_df = pd.read_csv('last_golden_legacy_market_caps.csv')
        #print(marketcap_df)
        for ticker in legacy_ticker_list:
                if(legacy_market_cap[ticker] == 'None'):
                        print('Replacing market cap for', ticker)
                        print('Was:', legacy_market_cap[ticker])
                        #marketcap_df.set_index('Ticker', inplace=True)
                        legacy_market_cap[ticker] = marketcap_df.loc[marketcap_df['Ticker']==ticker][' Market Cap'].values[0]
                        print('Now:', legacy_market_cap[ticker])


#Now get total market cap of legacy space companies and build weights
total_legacy_market_cap = 0

#Already have made sure everything is in USD - used FX rates before at line 204-209
for ticker in legacy_ticker_list:
	legacy_market_cap[ticker] = int(legacy_market_cap[ticker])
	total_legacy_market_cap = total_legacy_market_cap + legacy_market_cap[ticker]

#Now get legacy weights
legacy_index_weights = {}
weight_check = 0

for ticker in legacy_ticker_list:
        legacy_index_weights[ticker] = legacy_market_cap[ticker]/total_legacy_market_cap
        print(ticker, ':', legacy_index_weights[ticker])
        weight_check = weight_check + legacy_index_weights[ticker]

print('Weight check:', weight_check)

#Now time to build the legacy space index

legacy_index = pd.DataFrame(columns = ['Date', 'Value'])

#Now try to add a calculated value for the space index
data = data.reset_index()
for index, row in data.iterrows():
        legacy_index_value = 0
        for ticker in legacy_ticker_list:
                contribution = row[ticker] * legacy_index_weights[ticker]
                #Quick check for FTSE stocks - currently just BAE - these are listed in pennies so also need to divide the value of the contribution by 100
                if (ticker == 'BA.L'):
                  print ('Fixing size of contribution value for ', ticker, ' from ', contribution)
                  contribution = contribution/100
                  print('To: ', contribution)
                legacy_index_value = legacy_index_value + contribution
        print(row['Date'], ':', legacy_index_value)
        legacy_index = legacy_index.append({'Date':row['Date'], 'Value': legacy_index_value}, ignore_index=True)

#Now try and dump out the NASDAQ and S&P500 as individual dataframes
nasdaq_index = data[['Date', '^IXIC']].copy()
sandp_index = data[['Date', '^GSPC']].copy()

print(nasdaq_index)
print(sandp_index)

#quick check to see what the newspace and legacy dataframes look like	
print(newspace_index)
print(legacy_index)

#Now we have all the data, time to try and dump out the various .csv files for charting
#Turns out pd.merge can only manage two dataframes at once! So do this in steps
left_dataframe = pd.merge(newspace_index, legacy_index, on='Date')
right_dataframe = pd.merge(nasdaq_index, sandp_index, on='Date')
master_dataframe = pd.merge(left_dataframe, right_dataframe, on='Date')
master_dataframe.rename(columns={'Value_x':'PV New Space', 'Value_y':'PV Legacy Space', '^IXIC':'NASDAQ', '^GSPC':'S&P500'}, inplace=True)
#print(master_dataframe)
master_dataframe.to_csv('max_data.csv')

###########
#
# Set up timeframe for all graphs here by carving out days from master_dataframe
#
###########


#1 Week of data - update 20220327 to match Google Sheet approach of 6 day window instead of 5
one_week_data = master_dataframe.tail(6)
one_week_data = one_week_data.reset_index()
one_week_data = one_week_data.drop('index', axis=1)
#print(one_week_data)
one_week_data.to_csv('one_week_data.csv')

#1 month of data - estimate 22 trading days - https://www.dummies.com/article/business-careers-money/personal-finance/investing/investment-vehicles/stocks/stock-chart-attributes-starting-time-period-range-spacing-250596/
#Update on 20220327 to be 23 days to match Google Sheet timeframe - ripples through to all the data selection in the graphing as well
#one_month_data = master_dataframe.tail(22)
one_month_data = master_dataframe.tail(23)
one_month_data = one_month_data.reset_index()
one_month_data = one_month_data.drop('index', axis=1)
print(one_month_data)
one_month_data.to_csv('one_month_data.csv')

#3 months of data - estimate 63 trading days
#Update 20220327 to 67 days to match Google Sheet flow
three_month_data = master_dataframe.tail(67)
three_month_data = three_month_data.reset_index()
three_month_data = three_month_data.drop('index', axis=1)
three_month_data.to_csv('three_month_data.csv')

#6 months of data - 129 trading days
six_month_data = master_dataframe.tail(129)
six_month_data = six_month_data.reset_index()
six_month_data = six_month_data.drop('index', axis=1)
six_month_data.to_csv('six_month_data.csv')

#Add more as dataset grows

#######
#
# Now dump out most recent close/previous close for New Space Index, NASDAQ, and S&P 500 to display on wesbite
#
#######

most_recent_data = master_dataframe.tail(2)
most_recent_data = most_recent_data.reset_index()
most_recent_data = most_recent_data.drop('index', axis=1)
most_recent_data.to_csv('most_recent_data.csv')

#Now send this to Google

#Update Master Spreadsheet Tabs
spreadsheetId = 'Space_Index_Master_Spreadsheet_20220107'
#First Market Cap Data
sheetName = 'Data_From_Yahoo_Finance_For_Indices'
csvFile = 'most_recent_data.csv'

sheet = client.open(spreadsheetId)
sheet.values_update (
        sheetName,
        params={'valueInputOption': 'USER_ENTERED'},
        body={'values': list(csv.reader(open(csvFile)))}
)

#######
#
#Start with 1 week chart
#
#######

#Get the value of each starting point
newspace_start = one_week_data.loc[0]['PV New Space']
legacy_start = one_week_data.loc[0]['PV Legacy Space']
nasdaq_start = one_week_data.loc[0]['NASDAQ']
sandp_start = one_week_data.loc[0]['S&P500']

#normalized_one_week = pd.DataFrame(columns = ['Date', 'PV New Space', 'PV Legacy Space', 'NASDAQ', 'S&P500'])
normalized_one_week = one_week_data

def normalize_nasdaq_column(value):
	return(value/nasdaq_start)
def normalize_sandp_column(value):
	return(value/sandp_start)
def normalize_newspace_column(value):
	return(value/newspace_start)
def normalize_legacy_column(value):
	return(value/legacy_start)

normalized_one_week['NASDAQ'] = normalized_one_week['NASDAQ'].apply(normalize_nasdaq_column)
normalized_one_week['S&P500'] = normalized_one_week['S&P500'].apply(normalize_sandp_column)
normalized_one_week['PV New Space'] = normalized_one_week['PV New Space'].apply(normalize_newspace_column)
normalized_one_week['PV Legacy Space'] = normalized_one_week['PV Legacy Space'].apply(normalize_legacy_column)

#for index, row in one_week_data.iterrows():
#	current_pvnewspace_value = one_week_data.iloc[row]['PV New Space'].values[0] / newspace_start
#	current_pvlegacy_value = one_week_data.iloc[row]['PV Legacy Space'].values[0] / legacy_start
#	current_nasdaq_value = one_week_data.iloc[row]['NASDAQ'].values[0] / nasdaq_start
#	current_sandp_value = one_week_data.iloc[row]['S&P500'].values[0] / sandp_start
#	normalized_one_week = normalized_one_week.append({'Date':row['Date'], 'PV New Space':current_pvnewspace_value, 'PV Legacy Space':current_pvlegacy_space_value, 'NASDAQ':current_nasdaq_value, 'S&P500':current_sandp_value}, ignore_index=True)

print(normalized_one_week)
#Now add annotation for the graph - how much delta for the various things being tracked
def return_percentage(value):
	percentage = value - 1
	percentage = percentage * 1000
	percentage = round(percentage)
	percentage = int(percentage) 
	percentage = float(percentage)
	percentage = percentage/10
	return(percentage)

nasdaq_sign = ''
nasdaq_annotation = normalized_one_week.loc[5]['NASDAQ']
nasdaq_annotation = return_percentage(nasdaq_annotation)
if (nasdaq_annotation > 0):
	nasdaq_sign = '+'
nasdaq_annotation = str(nasdaq_annotation)
nasdaq_annotation = 'NASDAQ ' + nasdaq_sign + nasdaq_annotation + '%'
print('NASDAQ Annotation: ', nasdaq_annotation)

sandp_sign = ''
sandp_annotation = normalized_one_week.loc[5]['S&P500']
sandp_annotation = return_percentage(sandp_annotation)
if (sandp_annotation > 0):
	sandp_sign = '+'
sandp_annotation = str(sandp_annotation)
sandp_annotation = 'S&P500 ' + sandp_sign + sandp_annotation + '%' 
print('S&P500 Annotation: ', sandp_annotation)

newspace_sign = ''
newspace_annotation = normalized_one_week.loc[5]['PV New Space']
newspace_annotation = return_percentage(newspace_annotation)
if (newspace_annotation > 0):
	newspace_sign = '+'
newspace_annotation = str(newspace_annotation)
newspace_annotation = 'PV New Space ' + newspace_sign + newspace_annotation + '%' 
print('PV New Space Annotation: ', newspace_annotation)

legacy_sign = ''
legacy_annotation = normalized_one_week.loc[5]['PV Legacy Space']
legacy_annotation = return_percentage(legacy_annotation)
if (legacy_annotation > 0):
	legacy_sign = '+'
legacy_annotation = str(legacy_annotation)
legacy_annotation = 'PV Legacy Space ' + legacy_sign + legacy_annotation + '%' 
print('PV Legacy Space Annotation: ', legacy_annotation)

#Now chart one week data before we do anything more as saves having to figure out how to annotate these things into the dataframe

figure = px.line(normalized_one_week, x='Date', y=['NASDAQ', 'S&P500', 'PV New Space', 'PV Legacy Space'],
  color_discrete_map={
    'NASDAQ': '#68d8ff',
    'S&P500': '#006d97',
    'PV New Space': '#18a1cd',
    'PV Legacy Space': '#2b5d7d'
  },
  title='One Week Performance',
  template='plotly_white',
  width = 800,
  height = 600)

#Build mobile chart at the same time - different form factor
figure_mobile = px.line(normalized_one_week, x='Date', y=['NASDAQ', 'S&P500', 'PV New Space', 'PV Legacy Space'],
  color_discrete_map={
    'NASDAQ': '#68d8ff',
    'S&P500': '#006d97',
    'PV New Space': '#18a1cd',
    'PV Legacy Space': '#2b5d7d'
  },
  title='One Week Performance',
  template='plotly_white',
  width = 320, 
  height = 400) 

#Try to add annotations
figure_annotations = []
mobile_figure_annotations = []


#First define the default y-shifts for the annotations and then try to avoid any overlap
nasdaq_y_shift = 10
sandp_y_shift = 10
newspace_y_shift = 10
legacy_y_shift = 10

sandp_got_shifted = 'False'
newspace_got_shifted = 'False'

#First check NASDAQ vs S&P500 position - use relative % to see if we need to move
if (abs((normalized_one_week['NASDAQ'].values[5]/normalized_one_week['S&P500'].values[5])-1) < 0.02):
  #Brute force approach to the problem - if S&P500 got shifted set a flag, and adjust everything else based on that flag 
  sandp_got_shifted = 'True'
  if(((normalized_one_week['NASDAQ'].values[5]/normalized_one_week['S&P500'].values[5])-1) > 0):
    #NASDAQ Above S&P500, shift S&P500 down
    sandp_y_shift = 0
  else:
    #S&P500 above NASDAQ, shift S&P500 up
    sandp_y_shift = 20

#Next check NASDAQ vs New Space position - use relative % to see if we need to move
if (abs((normalized_one_week['NASDAQ'].values[5]/normalized_one_week['PV New Space'].values[5])-1) < 0.02):
  #Set the newspace_got_shifted flag
  newspace_got_shifted = 'True'
  if(((normalized_one_week['NASDAQ'].values[5]/normalized_one_week['PV New Space'].values[5])-1) > 0):
    #NASDAQ Above PV New Space, shift PV New Space down
    #But need to check NASDAQ vs S&P500 - if these guys overlapped then we need to shift PV New Space by more
    if(sandp_got_shifted == 'True'):
      newspace_y_shift = -10
    else:
      #If no NASDAQ/S&P500 overlap then can just adjust PV New Space by default
      newspace_y_shift = 0
  else:
    #PV New Space above NASDAQ, shift PV New Space up
    #But need to check NASDAQ vs S&P500 - if these ones overlapped then shift PV New Space by more
    if(sandp_got_shifted == 'True'):
      newspace_y_shift = 30
    else:
      newspace_y_shift = 20

#Finally check PV Legacy Space vs NASDAQ
if (abs((normalized_one_week['NASDAQ'].values[5]/normalized_one_week['PV Legacy Space'].values[5])-1) < 0.02):
  if(((normalized_one_week['NASDAQ'].values[5]/normalized_one_week['PV Legacy Space'].values[5])-1) > 0):
    #NASDAQ Above PV Legacy Space, shift PV Legacy Space down
    #But need to check NASDAQ vs others - if any of these guys overlapped then we need to shift PV Legacy Space by more
    if(sandp_got_shifted == 'True'):
      if(newspace_got_shifted == 'True'):
        legacy_y_shift = -20
      else:
        legacy_y_shift = -10
    else:
      #If no NASDAQ/S&P500 overlap then can just adjust PV New Space by default
      legacy_y_shift = 0
  else:
    #PV Legacy Space above NASDAQ, shift PV Legacy Space up
    #But need to check NASDAQ vs others - if these ones overlapped then shift PV Legacy Space by more
    if(sandp_got_shifted == 'True'):
      if(newspace_got_shifted == 'True'):
        legacy_y_shift = 35
      else:
        legacy_y_shift = 25
    else:
      legacy_y_shift = 20


print(normalized_one_week.iloc[5]['Date'])

#annotation_one = dict(x=normalized_one_week.iloc[4]['Date'], y=normalized_one_week['NASDAQ'].values[4], xref='paper', yref='paper', yshift=10, xshift=45, showarrow=False, bgcolor='#000000',font_color='#FFFFFF', text=nasdaq_annotation)
#annotation_one = dict(x=normalized_one_week.iloc[5]['Date'], y=normalized_one_week['NASDAQ'].values[5], xref='x', yref='y', yshift=nasdaq_y_shift, xshift=5, showarrow=False, bgcolor='#68d8ff',font_color='#FFFFFF', text=nasdaq_annotation, clicktoshow='onoff')
annotation_one = dict(x=1.01, y=normalized_one_week['NASDAQ'].values[5], xref='paper', yref='y', yshift=nasdaq_y_shift, xshift=5, showarrow=False, bgcolor='#68d8ff',font_color='#FFFFFF', text=nasdaq_annotation, clicktoshow='onoff')
mobile_annotation_one = dict(x=1.01, y=normalized_one_week['NASDAQ'].values[5], xref='paper', yref='y', yshift=nasdaq_y_shift, xshift=5, showarrow=False, bgcolor='#68d8ff',font_color='#FFFFFF', text=nasdaq_annotation, clicktoshow='onoff', font=dict(size=5))
#annotation_one = dict(x=1, y=normalized_one_week['NASDAQ'].values[4], xref='x', yref='y', yshift=10, xshift=45, showarrow=False, bgcolor='#000000',font_color='#FFFFFF', text=nasdaq_annotation)
figure_annotations.append(annotation_one)
mobile_figure_annotations.append(mobile_annotation_one)

#annotation_two = dict(x=normalized_one_week.iloc[5]['Date'], y=normalized_one_week['S&P500'].values[5], xref='x', yref='y', yshift=sandp_y_shift, xshift=5, showarrow=False, bgcolor='#006d97',font_color='#FFFFFF', text=sandp_annotation)
annotation_two = dict(x=1.01, y=normalized_one_week['S&P500'].values[5], xref='paper', yref='y', yshift=sandp_y_shift, xshift=5, showarrow=False, bgcolor='#006d97',font_color='#FFFFFF', text=sandp_annotation)
mobile_annotation_two = dict(x=1.01, y=normalized_one_week['S&P500'].values[5], xref='paper', yref='y', yshift=sandp_y_shift, xshift=5, showarrow=False, bgcolor='#006d97',font_color='#FFFFFF', text=sandp_annotation, font=dict(size=5))
figure_annotations.append(annotation_two)
mobile_figure_annotations.append(mobile_annotation_two)

#annotation_three = dict(x=normalized_one_week.iloc[5]['Date'], y=normalized_one_week['PV New Space'].values[5], xref='x', yref='y', yshift=newspace_y_shift, xshift=5, showarrow=False, bgcolor='#18a1cd',font_color='#FFFFFF', text=newspace_annotation)
annotation_three = dict(x=1.01, y=normalized_one_week['PV New Space'].values[5], xref='paper', yref='y', yshift=newspace_y_shift, xshift=5, showarrow=False, bgcolor='#18a1cd',font_color='#FFFFFF', text=newspace_annotation)
mobile_annotation_three = dict(x=1.01, y=normalized_one_week['PV New Space'].values[5], xref='paper', yref='y', yshift=newspace_y_shift, xshift=5, showarrow=False, bgcolor='#18a1cd',font_color='#FFFFFF', text=newspace_annotation, font=dict(size=5))
figure_annotations.append(annotation_three)
mobile_figure_annotations.append(mobile_annotation_three)

#annotation_four = dict(x=normalized_one_week.iloc[5]['Date'], y=normalized_one_week['PV Legacy Space'].values[5], xref='x', yref='y', yshift=legacy_y_shift, xshift=5, showarrow=False, bgcolor='#2b5d7d',font_color='#FFFFFF', text=legacy_annotation)
annotation_four = dict(x=1.01, y=normalized_one_week['PV Legacy Space'].values[5], xref='paper', yref='y', yshift=legacy_y_shift, xshift=5, showarrow=False, bgcolor='#2b5d7d',font_color='#FFFFFF', text=legacy_annotation)
mobile_annotation_four = dict(x=1.01, y=normalized_one_week['PV Legacy Space'].values[5], xref='paper', yref='y', yshift=legacy_y_shift, xshift=5, showarrow=False, bgcolor='#2b5d7d',font_color='#FFFFFF', text=legacy_annotation, font=dict(size=5))
figure_annotations.append(annotation_four)
mobile_figure_annotations.append(mobile_annotation_four)

figure.update_layout(annotations=figure_annotations)
figure.update_annotations(clicktoshow='onoff')
figure.update_annotations(xanchor='left')
figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
#figure.update_layout(hovermode='x unified')
#figure.update_layout(hovermode='x')
figure.update_layout(hovermode='closest')
figure.update_layout(yaxis_title='Relative Performance')
figure.update_layout(margin=dict(r=170))
figure.update_yaxes(fixedrange=True)

#Try and set legend on top
figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))

#print the figure
#print(figure)
graph_config = {'displayModeBar':False}
#don't show graphs in cron version in case it hangs the script
#figure.show(config=graph_config)
figure.write_html('test_one_week_graph.html', config=graph_config)

#Do exactly the same for mobile - except for annotations
figure_mobile.update_layout(annotations=mobile_figure_annotations)
figure_mobile.update_annotations(clicktoshow='onoff')
figure_mobile.update_annotations(xanchor='left')
figure_mobile.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
figure_mobile.update_layout(hovermode='closest')
figure_mobile.update_layout(yaxis_title='Relative Performance', font=dict(size=5))
figure_mobile.update_yaxes(fixedrange=True)
figure_mobile.update_xaxes(fixedrange=True)

#Try and set legend on top
figure_mobile.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, font=dict(size=4)))

#print the figure
#print(figure)
graph_config = {'displayModeBar':False}
#figure_mobile.show(config=graph_config)
#figure.show()
figure_mobile.write_html('test_one_week_graph_mobile.html', config=graph_config)



##
#
# Now do 6 month graph without any annotation changes
#
##

#Get the value of each starting point
newspace_start = six_month_data.loc[0]['PV New Space']
legacy_start = six_month_data.loc[0]['PV Legacy Space']
nasdaq_start = six_month_data.loc[0]['NASDAQ']
sandp_start = six_month_data.loc[0]['S&P500']

normalized_six_month = six_month_data

normalized_six_month['NASDAQ'] = normalized_six_month['NASDAQ'].apply(normalize_nasdaq_column)
normalized_six_month['S&P500'] = normalized_six_month['S&P500'].apply(normalize_sandp_column)
normalized_six_month['PV New Space'] = normalized_six_month['PV New Space'].apply(normalize_newspace_column)
normalized_six_month['PV Legacy Space'] = normalized_six_month['PV Legacy Space'].apply(normalize_legacy_column)

#for index, row in one_week_data.iterrows():
#       current_pvnewspace_value = one_week_data.iloc[row]['PV New Space'].values[0] / newspace_start
#       current_pvlegacy_value = one_week_data.iloc[row]['PV Legacy Space'].values[0] / legacy_start
#       current_nasdaq_value = one_week_data.iloc[row]['NASDAQ'].values[0] / nasdaq_start
#       current_sandp_value = one_week_data.iloc[row]['S&P500'].values[0] / sandp_start
#       normalized_one_week = normalized_one_week.append({'Date':row['Date'], 'PV New Space':current_pvnewspace_value, 'PV Legacy Space':current_pvlegacy_space_value, 'NASDAQ':current_nasdaq_value, 'S&P500':current_sandp_value}, ignore_index=True)

print(normalized_six_month)
#Now add annotation for the graph - how much delta for the various things being tracked
#The function return_percentage is defiend above so reuse that

nasdaq_sign = '' 
nasdaq_annotation = normalized_six_month.loc[128]['NASDAQ']
nasdaq_annotation = return_percentage(nasdaq_annotation)
if (nasdaq_annotation > 0):
        nasdaq_sign = '+'
nasdaq_annotation = str(nasdaq_annotation)
nasdaq_annotation = 'NASDAQ ' + nasdaq_sign + nasdaq_annotation + '%'
print('NASDAQ Annotation: ', nasdaq_annotation)

sandp_sign = '' 
sandp_annotation = normalized_six_month.loc[128]['S&P500']
sandp_annotation = return_percentage(sandp_annotation)
if (sandp_annotation > 0):
        sandp_sign = '+'
sandp_annotation = str(sandp_annotation)
sandp_annotation = 'S&P500 ' + sandp_sign + sandp_annotation + '%'
print('S&P500 Annotation: ', sandp_annotation)

newspace_sign = '' 
newspace_annotation = normalized_six_month.loc[128]['PV New Space']
newspace_annotation = return_percentage(newspace_annotation)
if (newspace_annotation > 0):
        newspace_sign = '+'
newspace_annotation = str(newspace_annotation)
newspace_annotation = 'PV New Space ' + newspace_sign + newspace_annotation + '%'
print('PV New Space Annotation: ', newspace_annotation)

legacy_sign = '' 
legacy_annotation = normalized_six_month.loc[128]['PV Legacy Space']
legacy_annotation = return_percentage(legacy_annotation)
if (legacy_annotation > 0):
        legacy_sign = '+'
legacy_annotation = str(legacy_annotation)
legacy_annotation = 'PV Legacy Space ' + legacy_sign + legacy_annotation + '%'
print('PV Legacy Space Annotation: ', legacy_annotation)

#Now chart six month data before we do anything more as saves having to figure out how to annotate these things into the dataframe

figure = px.line(normalized_six_month, x='Date', y=['NASDAQ', 'S&P500', 'PV New Space', 'PV Legacy Space'],
  color_discrete_map={
    'NASDAQ': '#68d8ff',
    'S&P500': '#006d97',
    'PV New Space': '#18a1cd',
    'PV Legacy Space': '#2b5d7d'
  },
  title='Six Month Performance',
  template='plotly_white',
  width = 800,
  height = 600)

#Try to add annotations
figure_annotations = []

annotation_one = dict(x=normalized_six_month.iloc[128]['Date'], y=normalized_six_month['NASDAQ'].values[128], xref='x', yref='y', yshift=10, xshift=5, showarrow=False, bgcolor='#000000',font_color='#FFFFFF', text=nasdaq_annotation)
nasdaq_y_position = normalized_six_month['NASDAQ'].values[128]
figure_annotations.append(annotation_one)

annotation_two = dict(x=normalized_six_month.iloc[128]['Date'], y=normalized_six_month['S&P500'].values[128], xref='x', yref='y', yshift=10, xshift=5, showarrow=False, bgcolor='#000000',font_color='#FFFFFF', text=sandp_annotation)
figure_annotations.append(annotation_two)

annotation_three = dict(x=normalized_six_month.iloc[128]['Date'], y=normalized_six_month['PV New Space'].values[128], xref='x', yref='y', yshift=10, xshift=5, showarrow=False, bgcolor='#000000',font_color='#FFFFFF', text=newspace_annotation)
figure_annotations.append(annotation_three)

annotation_four = dict(x=normalized_six_month.iloc[128]['Date'], y=normalized_six_month['PV Legacy Space'].values[128], xref='x', yref='y', yshift=10, xshift=5, showarrow=False, bgcolor='#000000',font_color='#FFFFFF', text=legacy_annotation)
figure_annotations.append(annotation_four)

figure.update_layout(annotations=figure_annotations)
figure.update_annotations(clicktoshow='onoff')
figure.update_annotations(xanchor='left')
figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
#figure.update_layout(hovermode='x unified')
#figure.update_layout(hovermode='x')
figure.update_layout(hovermode='closest')
figure.update_layout(yaxis_title='Relative Performance')
figure.update_yaxes(fixedrange=True)

#Try and set legend on top
figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))

#print the figure
#print(figure)
#figure.show()
figure.write_html('test_six_month_graph_no_annotation_changes.html')

##
#
# Now do 6 month graph with annotation changes
#
##

#Get the value of each starting point
newspace_start = six_month_data.loc[0]['PV New Space']
legacy_start = six_month_data.loc[0]['PV Legacy Space']
nasdaq_start = six_month_data.loc[0]['NASDAQ']
sandp_start = six_month_data.loc[0]['S&P500']

normalized_six_month = six_month_data

normalized_six_month['NASDAQ'] = normalized_six_month['NASDAQ'].apply(normalize_nasdaq_column)
normalized_six_month['S&P500'] = normalized_six_month['S&P500'].apply(normalize_sandp_column)
normalized_six_month['PV New Space'] = normalized_six_month['PV New Space'].apply(normalize_newspace_column)
normalized_six_month['PV Legacy Space'] = normalized_six_month['PV Legacy Space'].apply(normalize_legacy_column)

#for index, row in one_week_data.iterrows():
#       current_pvnewspace_value = one_week_data.iloc[row]['PV New Space'].values[0] / newspace_start
#       current_pvlegacy_value = one_week_data.iloc[row]['PV Legacy Space'].values[0] / legacy_start
#       current_nasdaq_value = one_week_data.iloc[row]['NASDAQ'].values[0] / nasdaq_start
#       current_sandp_value = one_week_data.iloc[row]['S&P500'].values[0] / sandp_start
#       normalized_one_week = normalized_one_week.append({'Date':row['Date'], 'PV New Space':current_pvnewspace_value, 'PV Legacy Space':current_pvlegacy_space_value, 'NASDAQ':current_nasdaq_value, 'S&P500':current_sandp_value}, ignore_index=True)

print(normalized_six_month)
#Now add annotation for the graph - how much delta for the various things being tracked
#The function return_percentage is defiend above so reuse that

nasdaq_sign = ''
nasdaq_annotation = normalized_six_month.loc[128]['NASDAQ']
nasdaq_annotation = return_percentage(nasdaq_annotation)
if (nasdaq_annotation > 0):
        nasdaq_sign = '+'
nasdaq_annotation = str(nasdaq_annotation)
nasdaq_annotation = 'NASDAQ ' + nasdaq_sign + nasdaq_annotation + '%'
print('NASDAQ Annotation: ', nasdaq_annotation)

sandp_sign = ''
sandp_annotation = normalized_six_month.loc[128]['S&P500']
sandp_annotation = return_percentage(sandp_annotation)
if (sandp_annotation > 0):
        sandp_sign = '+'
sandp_annotation = str(sandp_annotation)
sandp_annotation = 'S&P500 ' + sandp_sign + sandp_annotation + '%'
print('S&P500 Annotation: ', sandp_annotation)

newspace_sign = ''
newspace_annotation = normalized_six_month.loc[128]['PV New Space']
newspace_annotation = return_percentage(newspace_annotation)
if (newspace_annotation > 0):
        newspace_sign = '+'
newspace_annotation = str(newspace_annotation)
newspace_annotation = 'PV New Space ' + newspace_sign + newspace_annotation + '%'
print('PV New Space Annotation: ', newspace_annotation)

legacy_sign = ''
legacy_annotation = normalized_six_month.loc[128]['PV Legacy Space']
legacy_annotation = return_percentage(legacy_annotation)
if (legacy_annotation > 0):
        legacy_sign = '+'
legacy_annotation = str(legacy_annotation)
legacy_annotation = 'PV Legacy Space ' + legacy_sign + legacy_annotation + '%'
print('PV Legacy Space Annotation: ', legacy_annotation)

#Now chart six month data before we do anything more as saves having to figure out how to annotate these things into the dataframe

figure = px.line(normalized_six_month, x='Date', y=['NASDAQ', 'S&P500', 'PV New Space', 'PV Legacy Space'],
  color_discrete_map={
    'NASDAQ': '#68d8ff',
    'S&P500': '#006d97',
    'PV New Space': '#18a1cd',
    'PV Legacy Space': '#2b5d7d'
  },
  title='Six Month Performance',
  template='plotly_white',
  width = 800,
  height = 600)

figure_mobile = px.line(normalized_six_month, x='Date', y=['NASDAQ', 'S&P500', 'PV New Space', 'PV Legacy Space'],
  color_discrete_map={
    'NASDAQ': '#68d8ff',
    'S&P500': '#006d97',
    'PV New Space': '#18a1cd',
    'PV Legacy Space': '#2b5d7d'
  },
  title='Six Month Performance',
  template='plotly_white',
  width = 320, 
  height = 400) 

#Try to add annotations
figure_annotations = []
mobile_figure_annotations = []

#First define the default y-shifts for the annotations and then try to avoid any overlap
nasdaq_y_shift = 10
sandp_y_shift = 10
newspace_y_shift = 10
legacy_y_shift = 10

sandp_got_shifted = 'False'
newspace_got_shifted = 'False'

#First check NASDAQ vs S&P500 position - use relative % to see if we need to move
if (abs((normalized_six_month['NASDAQ'].values[128]/normalized_six_month['S&P500'].values[128])-1) < 0.02):
  #Brute force approach to the problem - if S&P500 got shifted set a flag, and adjust everything else based on that flag 
  sandp_got_shifted = 'True'
  if(((normalized_six_month['NASDAQ'].values[128]/normalized_six_month['S&P500'].values[128])-1) > 0):
    #NASDAQ Above S&P500, shift S&P500 down
    sandp_y_shift = 0
  else:
    #S&P500 above NASDAQ, shift S&P500 up
    sandp_y_shift = 20 

#Next check NASDAQ vs New Space position - use relative % to see if we need to move
if (abs((normalized_six_month['NASDAQ'].values[128]/normalized_six_month['PV New Space'].values[128])-1) < 0.02):
  #Set the newspace_got_shifted flag
  newspace_got_shifted = 'True'  
  if(((normalized_six_month['NASDAQ'].values[128]/normalized_six_month['PV New Space'].values[128])-1) > 0):
    #NASDAQ Above PV New Space, shift PV New Space down
    #But need to check NASDAQ vs S&P500 - if these guys overlapped then we need to shift PV New Space by more
    #if (abs((normalized_six_month['NASDAQ'].values[128]/normalized_six_month['S&P500'].values[128])-1) < 0.02):
    if(sandp_got_shifted == 'True'):
      newspace_y_shift = -10
    else:
      #If no NASDAQ/S&P500 overlap then can just adjust PV New Space by default
      newspace_y_shift = 0 
  else:
    #PV New Space above NASDAQ, shift PV New Space up
    #But need to check NASDAQ vs S&P500 - if these ones overlapped then shift PV New Space by more
    #if (abs((normalized_six_month['S&P500'].values[128]/normalized_six_month['PV New Space'].values[128])-1) < 0.02):
    #  if(((normalized_six_month['S&P500'].values[128]/normalized_six_month['PV New Space'].values[128])-1) > 0):
    #    #S&P500 above PV New Space, shift both upwards
    #    newspace_y_shift = newspace_y_shift + 5
    #    sandp_y_shift = sandp_y_shift + 5
    #  else:
    #    #S&P500 below PV New Space, shift S&P500 up
    #sandp_y_shift = 15a
    if(sandp_got_shifted == 'True'):
      newspace_y_shift = 30
    else:
      newspace_y_shift = 20

#Finally check PV Legacy Space vs NASDAQ
if (abs((normalized_six_month['NASDAQ'].values[128]/normalized_six_month['PV Legacy Space'].values[128])-1) < 0.02):
  if(((normalized_six_month['NASDAQ'].values[128]/normalized_six_month['PV Legacy Space'].values[128])-1) > 0):
    #NASDAQ Above PV Legacy Space, shift PV Legacy Space down
    #But need to check NASDAQ vs others - if any of these guys overlapped then we need to shift PV Legacy Space by more
    #if (abs((normalized_six_month['NASDAQ'].values[128]/normalized_six_month['S&P500'].values[128])-1) < 0.02):
    if(sandp_got_shifted == 'True'):
      if(newspace_got_shifted == 'True'):
        legacy_y_shift = -20
      else:
        legacy_y_shift = -10
    else:
      #If no NASDAQ/S&P500 overlap then can just adjust PV New Space by default
      legacy_y_shift = 0
  else:
    #PV Legacy Space above NASDAQ, shift PV Legacy Space up
    #But need to check NASDAQ vs others - if these ones overlapped then shift PV Legacy Space by more
    if(sandp_got_shifted == 'True'):
      if(newspace_got_shifted == 'True'):
        legacy_y_shift = 35
      else:
        legacy_y_shift = 25
    else:
      legacy_y_shift = 20


#annotation_one = dict(x=normalized_six_month.iloc[128]['Date'], y=normalized_six_month['NASDAQ'].values[128], xref='x', yref='y', yshift=nasdaq_y_shift, xshift=5, showarrow=False, bgcolor='#68d8ff',font_color='#FFFFFF', text=nasdaq_annotation)
annotation_one = dict(x=1.01, y=normalized_six_month['NASDAQ'].values[128], xref='paper', yref='y', yshift=nasdaq_y_shift, xshift=5, showarrow=False, bgcolor='#68d8ff',font_color='#FFFFFF', text=nasdaq_annotation)
mobile_annotation_one = dict(x=1.01, y=normalized_six_month['NASDAQ'].values[128], xref='paper', yref='y', yshift=nasdaq_y_shift, xshift=5, showarrow=False, bgcolor='#68d8ff',font_color='#FFFFFF', text=nasdaq_annotation, font=dict(size=5))
nasdaq_y_position = normalized_six_month['NASDAQ'].values[128]
figure_annotations.append(annotation_one)
mobile_figure_annotations.append(mobile_annotation_one)

#annotation_two = dict(x=normalized_six_month.iloc[128]['Date'], y=normalized_six_month['S&P500'].values[128], xref='x', yref='y', yshift=sandp_y_shift, xshift=5, showarrow=False, bgcolor='#006d97',font_color='#FFFFFF', text=sandp_annotation)
annotation_two = dict(x=1.01, y=normalized_six_month['S&P500'].values[128], xref='paper', yref='y', yshift=sandp_y_shift, xshift=5, showarrow=False, bgcolor='#006d97',font_color='#FFFFFF', text=sandp_annotation)
mobile_annotation_two = dict(x=1.01, y=normalized_six_month['S&P500'].values[128], xref='paper', yref='y', yshift=sandp_y_shift, xshift=5, showarrow=False, bgcolor='#006d97',font_color='#FFFFFF', text=sandp_annotation, font=dict(size=5))
figure_annotations.append(annotation_two)
mobile_figure_annotations.append(mobile_annotation_two)

#annotation_three = dict(x=normalized_six_month.iloc[128]['Date'], y=normalized_six_month['PV New Space'].values[128], xref='x', yref='y', yshift=newspace_y_shift, xshift=5, showarrow=False, bgcolor='#18a1cd',font_color='#FFFFFF', text=newspace_annotation)
annotation_three = dict(x=1.01, y=normalized_six_month['PV New Space'].values[128], xref='paper', yref='y', yshift=newspace_y_shift, xshift=5, showarrow=False, bgcolor='#18a1cd',font_color='#FFFFFF', text=newspace_annotation)
mobile_annotation_three = dict(x=1.01, y=normalized_six_month['PV New Space'].values[128], xref='paper', yref='y', yshift=newspace_y_shift, xshift=5, showarrow=False, bgcolor='#18a1cd',font_color='#FFFFFF', text=newspace_annotation, font=dict(size=5))
figure_annotations.append(annotation_three)
mobile_figure_annotations.append(mobile_annotation_three)

#annotation_four = dict(x=normalized_six_month.iloc[128]['Date'], y=normalized_six_month['PV Legacy Space'].values[128], xref='x', yref='y', yshift=legacy_y_shift, xshift=5, showarrow=False, bgcolor='#2b5d7d',font_color='#FFFFFF', text=legacy_annotation)
annotation_four = dict(x=1.01, y=normalized_six_month['PV Legacy Space'].values[128], xref='paper', yref='y', yshift=legacy_y_shift, xshift=5, showarrow=False, bgcolor='#2b5d7d',font_color='#FFFFFF', text=legacy_annotation)
mobile_annotation_four = dict(x=1.01, y=normalized_six_month['PV Legacy Space'].values[128], xref='paper', yref='y', yshift=legacy_y_shift, xshift=5, showarrow=False, bgcolor='#2b5d7d',font_color='#FFFFFF', text=legacy_annotation, font=dict(size=5))
figure_annotations.append(annotation_four)
mobile_figure_annotations.append(mobile_annotation_four)

#graph_current_time = str(current_time)
#date_graph_was_generated = 'Graph Generated: ' + graph_current_time
#date_annotation = dict(x=0, y=0, xref='paper', yref='paper', showarrow=False, text=date_graph_was_generated)
#figure_annotations.append(date_annotation)

figure.update_layout(annotations=figure_annotations)
figure.update_annotations(clicktoshow='onoff')
figure.update_annotations(xanchor='left')
figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
#figure.update_layout(hovermode='x unified')
#figure.update_layout(hovermode='x')
figure.update_layout(hovermode='closest')
figure.update_layout(yaxis_title='Relative Performance')
figure.update_layout(margin=dict(r=170))
figure.update_yaxes(fixedrange=True)

#Try and set legend on top
figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))

#print the figure
#print(figure)
graph_config = {'displayModeBar':False}
#figure.show(config=graph_config)
figure.write_html('test_six_month_graph.html', config = graph_config)

#Now do all of this for mobile
#Do exactly the same for mobile - except using mobile annotations
figure_mobile.update_layout(annotations=mobile_figure_annotations)
figure_mobile.update_annotations(clicktoshow='onoff')
figure_mobile.update_annotations(xanchor='left')
figure_mobile.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
figure_mobile.update_layout(hovermode='closest')
figure_mobile.update_layout(yaxis_title='Relative Performance', font=dict(size=5))
figure_mobile.update_layout(margin=dict(l=20))
figure_mobile.update_yaxes(fixedrange=True)
figure_mobile.update_xaxes(fixedrange=True)

#Try and set legend on top
figure_mobile.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, font=dict(size=4)))

#print the figure
#print(figure)
graph_config = {'displayModeBar':False}
#figure_mobile.show(config=graph_config)
#figure.show()
figure_mobile.write_html('test_six_month_graph_mobile.html', config=graph_config)


##
#
# Now do 1 month graph
#
##

#Get the value of each starting point
newspace_start = one_month_data.loc[0]['PV New Space']
legacy_start = one_month_data.loc[0]['PV Legacy Space']
nasdaq_start = one_month_data.loc[0]['NASDAQ']
sandp_start = one_month_data.loc[0]['S&P500']

normalized_one_month = one_month_data

normalized_one_month['NASDAQ'] = normalized_one_month['NASDAQ'].apply(normalize_nasdaq_column)
normalized_one_month['S&P500'] = normalized_one_month['S&P500'].apply(normalize_sandp_column)
normalized_one_month['PV New Space'] = normalized_one_month['PV New Space'].apply(normalize_newspace_column)
normalized_one_month['PV Legacy Space'] = normalized_one_month['PV Legacy Space'].apply(normalize_legacy_column)

print(normalized_one_month)
#Now add annotation for the graph - how much delta for the various things being tracked
#The function return_percentage is defined above so reuse that

nasdaq_sign = ''
nasdaq_annotation = normalized_one_month.loc[22]['NASDAQ']
nasdaq_annotation = return_percentage(nasdaq_annotation)
if (nasdaq_annotation > 0):
        nasdaq_sign = '+'
nasdaq_annotation = str(nasdaq_annotation)
nasdaq_annotation = 'NASDAQ ' + nasdaq_sign + nasdaq_annotation + '%'
print('NASDAQ Annotation: ', nasdaq_annotation)

sandp_sign = ''
sandp_annotation = normalized_one_month.loc[22]['S&P500']
sandp_annotation = return_percentage(sandp_annotation)
if (sandp_annotation > 0):
        sandp_sign = '+'
sandp_annotation = str(sandp_annotation)
sandp_annotation = 'S&P500 ' + sandp_sign + sandp_annotation + '%'
print('S&P500 Annotation: ', sandp_annotation)

newspace_sign = ''
newspace_annotation = normalized_one_month.loc[22]['PV New Space']
newspace_annotation = return_percentage(newspace_annotation)
if (newspace_annotation > 0):
        newspace_sign = '+'
newspace_annotation = str(newspace_annotation)
newspace_annotation = 'PV New Space ' + newspace_sign + newspace_annotation + '%'
print('PV New Space Annotation: ', newspace_annotation)

legacy_sign = ''
legacy_annotation = normalized_one_month.loc[22]['PV Legacy Space']
legacy_annotation = return_percentage(legacy_annotation)
if (legacy_annotation > 0):
        legacy_sign = '+'
legacy_annotation = str(legacy_annotation)
legacy_annotation = 'PV Legacy Space ' + legacy_sign + legacy_annotation + '%'
print('PV Legacy Space Annotation: ', legacy_annotation)

#Now chart one month data before we do anything more as saves having to figure out how to annotate these things into the dataframe

figure = px.line(normalized_one_month, x='Date', y=['NASDAQ', 'S&P500', 'PV New Space', 'PV Legacy Space'],
  color_discrete_map={
    'NASDAQ': '#68d8ff',
    'S&P500': '#006d97',
    'PV New Space': '#18a1cd',
    'PV Legacy Space': '#2b5d7d'
  },
  title='One Month Performance',
  template='plotly_white',
  width = 800,
  height = 600)

#Build mobile chart at the same time - different form factor
figure_mobile = px.line(normalized_one_month, x='Date', y=['NASDAQ', 'S&P500', 'PV New Space', 'PV Legacy Space'],
  color_discrete_map={
    'NASDAQ': '#68d8ff',
    'S&P500': '#006d97',
    'PV New Space': '#18a1cd',
    'PV Legacy Space': '#2b5d7d'
  },
  title='One Month Performance',
  template='plotly_white',
  width = 320,
  height = 400)

#Try to add annotations
figure_annotations = []
mobile_figure_annotations = []

#First define the default y-shifts for the annotations and then try to avoid any overlap
nasdaq_y_shift = 10
sandp_y_shift = 10
newspace_y_shift = 10
legacy_y_shift = 10

sandp_got_shifted = 'False'
newspace_got_shifted = 'False'

#First check NASDAQ vs S&P500 position - use relative % to see if we need to move
if (abs((normalized_one_month['NASDAQ'].values[22]/normalized_one_month['S&P500'].values[22])-1) < 0.02):
  #Brute force approach to the problem - if S&P500 got shifted set a flag, and adjust everything else based on that flag 
  sandp_got_shifted = 'True'
  if(((normalized_one_month['NASDAQ'].values[22]/normalized_one_month['S&P500'].values[22])-1) > 0):
    #NASDAQ Above S&P500, shift S&P500 down
    sandp_y_shift = 0
  else:
    #S&P500 above NASDAQ, shift S&P500 up
    sandp_y_shift = 20

#Next check NASDAQ vs New Space position - use relative % to see if we need to move
if (abs((normalized_one_month['NASDAQ'].values[22]/normalized_one_month['PV New Space'].values[22])-1) < 0.02):
  #Set the newspace_got_shifted flag
  newspace_got_shifted = 'True'
  if(((normalized_one_month['NASDAQ'].values[22]/normalized_one_month['PV New Space'].values[22])-1) > 0):
    #NASDAQ Above PV New Space, shift PV New Space down
    #But need to check NASDAQ vs S&P500 - if these guys overlapped then we need to shift PV New Space by more
    if(sandp_got_shifted == 'True'):
      newspace_y_shift = -10
    else:
      #If no NASDAQ/S&P500 overlap then can just adjust PV New Space by default
      newspace_y_shift = 0
  else:
    #PV New Space above NASDAQ, shift PV New Space up
    #But need to check NASDAQ vs S&P500 - if these ones overlapped then shift PV New Space by more
    if(sandp_got_shifted == 'True'):
      newspace_y_shift = 30
    else:
      newspace_y_shift = 20

#Finally check PV Legacy Space vs NASDAQ
if (abs((normalized_one_month['NASDAQ'].values[22]/normalized_one_month['PV Legacy Space'].values[22])-1) < 0.02):
  if(((normalized_one_month['NASDAQ'].values[22]/normalized_one_month['PV Legacy Space'].values[22])-1) > 0):
    #NASDAQ Above PV Legacy Space, shift PV Legacy Space down
    #But need to check NASDAQ vs others - if any of these guys overlapped then we need to shift PV Legacy Space by more
    if(sandp_got_shifted == 'True'):
      if(newspace_got_shifted == 'True'):
        legacy_y_shift = -20
      else:
        legacy_y_shift = -10
    else:
      #If no NASDAQ/S&P500 overlap then can just adjust PV New Space by default
      legacy_y_shift = 0
  else:
    #PV Legacy Space above NASDAQ, shift PV Legacy Space up
    #But need to check NASDAQ vs others - if these ones overlapped then shift PV Legacy Space by more
    if(sandp_got_shifted == 'True'):
      if(newspace_got_shifted == 'True'):
        legacy_y_shift = 35
      else:
        legacy_y_shift = 25
    else:
      legacy_y_shift = 20

#annotation_one = dict(x=normalized_one_month.iloc[22]['Date'], y=normalized_one_month['NASDAQ'].values[22], xref='x', yref='y', yshift=nasdaq_y_shift, xshift=5, showarrow=False, bgcolor='#68d8ff',font_color='#FFFFFF', text=nasdaq_annotation)
annotation_one = dict(x=1.01, y=normalized_one_month['NASDAQ'].values[22], xref='paper', yref='y', yshift=nasdaq_y_shift, xshift=5, showarrow=False, bgcolor='#68d8ff',font_color='#FFFFFF', text=nasdaq_annotation)
mobile_annotation_one = dict(x=1.01, y=normalized_one_month['NASDAQ'].values[22], xref='paper', yref='y', yshift=nasdaq_y_shift, xshift=5, showarrow=False, bgcolor='#68d8ff',font_color='#FFFFFF', text=nasdaq_annotation, font=dict(size=5))
figure_annotations.append(annotation_one)
mobile_figure_annotations.append(mobile_annotation_one)

#annotation_two = dict(x=normalized_one_month.iloc[22]['Date'], y=normalized_one_month['S&P500'].values[22], xref='x', yref='y', yshift=sandp_y_shift, xshift=5, showarrow=False, bgcolor='#006d97',font_color='#FFFFFF', text=sandp_annotation)
annotation_two = dict(x=1.01, y=normalized_one_month['S&P500'].values[22], xref='paper', yref='y', yshift=sandp_y_shift, xshift=5, showarrow=False, bgcolor='#006d97',font_color='#FFFFFF', text=sandp_annotation)
mobile_annotation_two = dict(x=1.01, y=normalized_one_month['S&P500'].values[22], xref='paper', yref='y', yshift=sandp_y_shift, xshift=5, showarrow=False, bgcolor='#006d97',font_color='#FFFFFF', text=sandp_annotation, font=dict(size=5))
figure_annotations.append(annotation_two)
mobile_figure_annotations.append(mobile_annotation_two)

#annotation_three = dict(x=normalized_one_month.iloc[22]['Date'], y=normalized_one_month['PV New Space'].values[22], xref='x', yref='y', yshift=newspace_y_shift, xshift=5, showarrow=False, bgcolor='#18a1cd',font_color='#FFFFFF', text=newspace_annotation)
annotation_three = dict(x=1.01, y=normalized_one_month['PV New Space'].values[22], xref='paper', yref='y', yshift=newspace_y_shift, xshift=5, showarrow=False, bgcolor='#18a1cd',font_color='#FFFFFF', text=newspace_annotation)
mobile_annotation_three = dict(x=1.01, y=normalized_one_month['PV New Space'].values[22], xref='paper', yref='y', yshift=newspace_y_shift, xshift=5, showarrow=False, bgcolor='#18a1cd',font_color='#FFFFFF', text=newspace_annotation, font=dict(size=5))
figure_annotations.append(annotation_three)
mobile_figure_annotations.append(mobile_annotation_three)

#annotation_four = dict(x=normalized_one_month.iloc[22]['Date'], y=normalized_one_month['PV Legacy Space'].values[22], xref='x', yref='y', yshift=legacy_y_shift, xshift=5, showarrow=False, bgcolor='#2b5d7d',font_color='#FFFFFF', text=legacy_annotation)
annotation_four = dict(x=1.01, y=normalized_one_month['PV Legacy Space'].values[22], xref='paper', yref='y', yshift=legacy_y_shift, xshift=5, showarrow=False, bgcolor='#2b5d7d',font_color='#FFFFFF', text=legacy_annotation)
mobile_annotation_four = dict(x=1.01, y=normalized_one_month['PV Legacy Space'].values[22], xref='paper', yref='y', yshift=legacy_y_shift, xshift=5, showarrow=False, bgcolor='#2b5d7d',font_color='#FFFFFF', text=legacy_annotation, font=dict(size=5))
figure_annotations.append(annotation_four)
mobile_figure_annotations.append(mobile_annotation_four)

figure.update_layout(annotations=figure_annotations)
figure.update_annotations(clicktoshow='onoff')
figure.update_annotations(xanchor='left')
figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
#figure.update_layout(hovermode='x unified')
#figure.update_layout(hovermode='x')
figure.update_layout(hovermode='closest')
figure.update_layout(yaxis_title='Relative Performance')
figure.update_layout(margin=dict(r=170))
figure.update_yaxes(fixedrange=True)

#Try and set legend on top
figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))

#print the figure
#print(figure)
graph_config = {'displayModeBar':False}
#figure.show(config=graph_config)
#figure.show()
figure.write_html('test_one_month_graph.html', config=graph_config)

#Do exactly the same for mobile - except use mobile annotations
figure_mobile.update_layout(annotations=mobile_figure_annotations)
figure_mobile.update_annotations(clicktoshow='onoff')
figure_mobile.update_annotations(xanchor='left')
figure_mobile.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
figure_mobile.update_layout(hovermode='closest')
figure_mobile.update_layout(yaxis_title='Relative Performance', font=dict(size=5))
figure_mobile.update_layout(margin=dict(l=20))
figure_mobile.update_yaxes(fixedrange=True)
figure_mobile.update_xaxes(fixedrange=True)

#Try and set legend on top
figure_mobile.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, font=dict(size=4)))

#print the figure
#print(figure)
graph_config = {'displayModeBar':False}
#figure_mobile.show(config=graph_config)
#figure.show()
figure_mobile.write_html('test_one_month_graph_mobile.html', config=graph_config)


##
#
# Now do 3 month graph
#
##

#Get the value of each starting point
newspace_start = three_month_data.loc[0]['PV New Space']
legacy_start = three_month_data.loc[0]['PV Legacy Space']
nasdaq_start = three_month_data.loc[0]['NASDAQ']
sandp_start = three_month_data.loc[0]['S&P500']

normalized_three_month = three_month_data

normalized_three_month['NASDAQ'] = normalized_three_month['NASDAQ'].apply(normalize_nasdaq_column)
normalized_three_month['S&P500'] = normalized_three_month['S&P500'].apply(normalize_sandp_column)
normalized_three_month['PV New Space'] = normalized_three_month['PV New Space'].apply(normalize_newspace_column)
normalized_three_month['PV Legacy Space'] = normalized_three_month['PV Legacy Space'].apply(normalize_legacy_column)

#for index, row in one_week_data.iterrows():
#       current_pvnewspace_value = one_week_data.iloc[row]['PV New Space'].values[0] / newspace_start
#       current_pvlegacy_value = one_week_data.iloc[row]['PV Legacy Space'].values[0] / legacy_start
#       current_nasdaq_value = one_week_data.iloc[row]['NASDAQ'].values[0] / nasdaq_start
#       current_sandp_value = one_week_data.iloc[row]['S&P500'].values[0] / sandp_start
#       normalized_one_week = normalized_one_week.append({'Date':row['Date'], 'PV New Space':current_pvnewspace_value, 'PV Legacy Space':current_pvlegacy_space_value, 'NASDAQ':current_nasdaq_value, 'S&P500':current_sandp_value}, ignore_index=True)

print(normalized_three_month)
#Now add annotation for the graph - how much delta for the various things being tracked
#The function return_percentage is defiend above so reuse that

nasdaq_sign = ''
nasdaq_annotation = normalized_three_month.loc[66]['NASDAQ']
nasdaq_annotation = return_percentage(nasdaq_annotation)
if (nasdaq_annotation > 0):
        nasdaq_sign = '+'
nasdaq_annotation = str(nasdaq_annotation)
nasdaq_annotation = 'NASDAQ ' + nasdaq_sign + nasdaq_annotation + '%'
print('NASDAQ Annotation: ', nasdaq_annotation)

sandp_sign = ''
sandp_annotation = normalized_three_month.loc[66]['S&P500']
sandp_annotation = return_percentage(sandp_annotation)
if (sandp_annotation > 0):
        sandp_sign = '+'
sandp_annotation = str(sandp_annotation)
sandp_annotation = 'S&P500 ' + sandp_sign + sandp_annotation + '%'
print('S&P500 Annotation: ', sandp_annotation)

newspace_sign = ''
newspace_annotation = normalized_three_month.loc[66]['PV New Space']
newspace_annotation = return_percentage(newspace_annotation)
if (newspace_annotation > 0):
        newspace_sign = '+'
newspace_annotation = str(newspace_annotation)
newspace_annotation = 'PV New Space ' + newspace_sign + newspace_annotation + '%'
print('PV New Space Annotation: ', newspace_annotation)

legacy_sign = ''
legacy_annotation = normalized_three_month.loc[66]['PV Legacy Space']
legacy_annotation = return_percentage(legacy_annotation)
if (legacy_annotation > 0):
        legacy_sign = '+'
legacy_annotation = str(legacy_annotation)
legacy_annotation = 'PV Legacy Space ' + legacy_sign + legacy_annotation + '%'
print('PV Legacy Space Annotation: ', legacy_annotation)

#Now chart three month data before we do anything more as saves having to figure out how to annotate these things into the dataframe

figure = px.line(normalized_three_month, x='Date', y=['NASDAQ', 'S&P500', 'PV New Space', 'PV Legacy Space'],
  color_discrete_map={
    'NASDAQ': '#68d8ff',
    'S&P500': '#006d97',
    'PV New Space': '#18a1cd',
    'PV Legacy Space': '#2b5d7d'
  },
  title='Three Month Performance',
  template='plotly_white',
  width = 800,
  height = 600)

figure_mobile = px.line(normalized_three_month, x='Date', y=['NASDAQ', 'S&P500', 'PV New Space', 'PV Legacy Space'],
  color_discrete_map={
    'NASDAQ': '#68d8ff',
    'S&P500': '#006d97',
    'PV New Space': '#18a1cd',
    'PV Legacy Space': '#2b5d7d'
  },
  title='Three Month Performance',
  template='plotly_white',
  width = 320,
  height = 400)

#Try to add annotations
figure_annotations = []
mobile_figure_annotations = []

#First define the default y-shifts for the annotations and then try to avoid any overlap
nasdaq_y_shift = 10
sandp_y_shift = 10
newspace_y_shift = 10
legacy_y_shift = 10

sandp_got_shifted = 'False'
newspace_got_shifted = 'False'

#First check NASDAQ vs S&P500 position - use relative % to see if we need to move
if (abs((normalized_three_month['NASDAQ'].values[66]/normalized_three_month['S&P500'].values[66])-1) < 0.02):
  #Brute force approach to the problem - if S&P500 got shifted set a flag, and adjust everything else based on that flag 
  sandp_got_shifted = 'True'
  if(((normalized_three_month['NASDAQ'].values[66]/normalized_three_month['S&P500'].values[66])-1) > 0):
    #NASDAQ Above S&P500, shift S&P500 down
    sandp_y_shift = 0
  else:
    #S&P500 above NASDAQ, shift S&P500 up
    sandp_y_shift = 20

#Next check NASDAQ vs New Space position - use relative % to see if we need to move
if (abs((normalized_three_month['NASDAQ'].values[66]/normalized_three_month['PV New Space'].values[66])-1) < 0.02):
  #Set the newspace_got_shifted flag
  newspace_got_shifted = 'True'
  if(((normalized_three_month['NASDAQ'].values[66]/normalized_three_month['PV New Space'].values[66])-1) > 0):
    #NASDAQ Above PV New Space, shift PV New Space down
    #But need to check NASDAQ vs S&P500 - if these guys overlapped then we need to shift PV New Space by more
    if(sandp_got_shifted == 'True'):
      newspace_y_shift = -10
    else:
      #If no NASDAQ/S&P500 overlap then can just adjust PV New Space by default
      newspace_y_shift = 0
  else:
    #PV New Space above NASDAQ, shift PV New Space up
    #But need to check NASDAQ vs S&P500 - if these ones overlapped then shift PV New Space by more
    if(sandp_got_shifted == 'True'):
      newspace_y_shift = 30
    else:
      newspace_y_shift = 20

#Finally check PV Legacy Space vs NASDAQ
if (abs((normalized_three_month['NASDAQ'].values[66]/normalized_three_month['PV Legacy Space'].values[66])-1) < 0.02):
  if(((normalized_three_month['NASDAQ'].values[66]/normalized_three_month['PV Legacy Space'].values[66])-1) > 0):
    #NASDAQ Above PV Legacy Space, shift PV Legacy Space down
    #But need to check NASDAQ vs others - if any of these guys overlapped then we need to shift PV Legacy Space by more
    if(sandp_got_shifted == 'True'):
      if(newspace_got_shifted == 'True'):
        legacy_y_shift = -20
      else:
        legacy_y_shift = -10
    else:
      #If no NASDAQ/S&P500 overlap then can just adjust PV New Space by default
      legacy_y_shift = 0
  else:
    #PV Legacy Space above NASDAQ, shift PV Legacy Space up
    #But need to check NASDAQ vs others - if these ones overlapped then shift PV Legacy Space by more
    if(sandp_got_shifted == 'True'):
      if(newspace_got_shifted == 'True'):
        legacy_y_shift = 35
      else:
        legacy_y_shift = 25
    else:
      legacy_y_shift = 20

#annotation_one = dict(x=normalized_three_month.iloc[65]['Date'], y=normalized_three_month['NASDAQ'].values[65], xref='x', yref='y', yshift=nasdaq_y_shift, xshift=5, showarrow=False, bgcolor='#68d8ff',font_color='#FFFFFF', text=nasdaq_annotation)
annotation_one = dict(x=1.01, y=normalized_three_month['NASDAQ'].values[66], xref='paper', yref='y', yshift=nasdaq_y_shift, xshift=5, showarrow=False, bgcolor='#68d8ff',font_color='#FFFFFF', text=nasdaq_annotation)
mobile_annotation_one = dict(x=1.01, y=normalized_three_month['NASDAQ'].values[66], xref='paper', yref='y', yshift=nasdaq_y_shift, xshift=5, showarrow=False, bgcolor='#68d8ff',font_color='#FFFFFF', text=nasdaq_annotation, font=dict(size=5))
figure_annotations.append(annotation_one)
mobile_figure_annotations.append(mobile_annotation_one)

#annotation_two = dict(x=normalized_three_month.iloc[65]['Date'], y=normalized_three_month['S&P500'].values[65], xref='x', yref='y', yshift=sandp_y_shift, xshift=5, showarrow=False, bgcolor='#006d97',font_color='#FFFFFF', text=sandp_annotation)
annotation_two = dict(x=1.01, y=normalized_three_month['S&P500'].values[66], xref='paper', yref='y', yshift=sandp_y_shift, xshift=5, showarrow=False, bgcolor='#006d97',font_color='#FFFFFF', text=sandp_annotation)
mobile_annotation_two = dict(x=1.01, y=normalized_three_month['S&P500'].values[66], xref='paper', yref='y', yshift=sandp_y_shift, xshift=5, showarrow=False, bgcolor='#006d97',font_color='#FFFFFF', text=sandp_annotation, font=dict(size=5))
figure_annotations.append(annotation_two)
mobile_figure_annotations.append(mobile_annotation_two)

#annotation_three = dict(x=normalized_three_month.iloc[65]['Date'], y=normalized_three_month['PV New Space'].values[65], xref='x', yref='y', yshift=newspace_y_shift, xshift=5, showarrow=False, bgcolor='#18a1cd',font_color='#FFFFFF', text=newspace_annotation)
annotation_three = dict(x=1.01, y=normalized_three_month['PV New Space'].values[66], xref='paper', yref='y', yshift=newspace_y_shift, xshift=5, showarrow=False, bgcolor='#18a1cd',font_color='#FFFFFF', text=newspace_annotation)
mobile_annotation_three = dict(x=1.01, y=normalized_three_month['PV New Space'].values[66], xref='paper', yref='y', yshift=newspace_y_shift, xshift=5, showarrow=False, bgcolor='#18a1cd',font_color='#FFFFFF', text=newspace_annotation, font=dict(size=5))
figure_annotations.append(annotation_three)
mobile_figure_annotations.append(mobile_annotation_three)

#annotation_four = dict(x=normalized_three_month.iloc[65]['Date'], y=normalized_three_month['PV Legacy Space'].values[65], xref='x', yref='y', yshift=legacy_y_shift, xshift=5, showarrow=False, bgcolor='#2b5d7d',font_color='#FFFFFF', text=legacy_annotation)
annotation_four = dict(x=1.01, y=normalized_three_month['PV Legacy Space'].values[66], xref='paper', yref='y', yshift=legacy_y_shift, xshift=5, showarrow=False, bgcolor='#2b5d7d',font_color='#FFFFFF', text=legacy_annotation)
mobile_annotation_four = dict(x=1.01, y=normalized_three_month['PV Legacy Space'].values[66], xref='paper', yref='y', yshift=legacy_y_shift, xshift=5, showarrow=False, bgcolor='#2b5d7d',font_color='#FFFFFF', text=legacy_annotation, font=dict(size=5))
figure_annotations.append(annotation_four)
mobile_figure_annotations.append(mobile_annotation_four)

figure.update_layout(annotations=figure_annotations)
figure.update_annotations(clicktoshow='onoff')
figure.update_annotations(xanchor='left')
figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
#figure.update_layout(hovermode='x unified')
#figure.update_layout(hovermode='x')
figure.update_layout(hovermode='closest')
figure.update_layout(yaxis_title='Relative Performance')
figure.update_layout(margin=dict(r=170))
figure.update_yaxes(fixedrange=True)

#Try and set legend on top
figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))

#print the figure
#print(figure)
graph_config = {'displayModeBar':False}
#figure.show(config=graph_config)
#figure.show()
figure.write_html('test_three_month_graph.html', config=graph_config)
figure.write_html('test_three_month_graph_allow_zoom.html')

#Do exactly the same for mobile - except for annotations
figure_mobile.update_layout(annotations=mobile_figure_annotations)
figure_mobile.update_annotations(clicktoshow='onoff')
figure_mobile.update_annotations(xanchor='left')
figure_mobile.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
figure_mobile.update_layout(hovermode='closest')
figure_mobile.update_layout(yaxis_title='Relative Performance', font=dict(size=5))
figure_mobile.update_layout(margin=dict(l=20))
figure_mobile.update_yaxes(fixedrange=True)
figure_mobile.update_xaxes(fixedrange=True)

#Try and set legend on top
figure_mobile.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, font=dict(size=4)))

#print the figure
#print(figure)
graph_config = {'displayModeBar':False}
#figure_mobile.show(config=graph_config)
#figure.show()
figure_mobile.write_html('test_three_month_graph_mobile.html', config=graph_config)

##
#
# Now do max graph
#
##

max_data = master_dataframe

#Get the value of each starting point
newspace_start = max_data.loc[0]['PV New Space']
legacy_start = max_data.loc[0]['PV Legacy Space']
nasdaq_start = max_data.loc[0]['NASDAQ']
sandp_start = max_data.loc[0]['S&P500']

normalized_max_data = max_data

normalized_max_data['NASDAQ'] = normalized_max_data['NASDAQ'].apply(normalize_nasdaq_column)
normalized_max_data['S&P500'] = normalized_max_data['S&P500'].apply(normalize_sandp_column)
normalized_max_data['PV New Space'] = normalized_max_data['PV New Space'].apply(normalize_newspace_column)
normalized_max_data['PV Legacy Space'] = normalized_max_data['PV Legacy Space'].apply(normalize_legacy_column)

#for index, row in one_week_data.iterrows():
#       current_pvnewspace_value = one_week_data.iloc[row]['PV New Space'].values[0] / newspace_start
#       current_pvlegacy_value = one_week_data.iloc[row]['PV Legacy Space'].values[0] / legacy_start
#       current_nasdaq_value = one_week_data.iloc[row]['NASDAQ'].values[0] / nasdaq_start
#       current_sandp_value = one_week_data.iloc[row]['S&P500'].values[0] / sandp_start
#       normalized_one_week = normalized_one_week.append({'Date':row['Date'], 'PV New Space':current_pvnewspace_value, 'PV Legacy Space':current_pvlegacy_space_value, 'NASDAQ':current_nasdaq_value, 'S&P500':current_sandp_value}, ignore_index=True)

print(normalized_max_data)
#Now add annotation for the graph - how much delta for the various things being tracked
#The function return_percentage is defiend above so reuse that

nasdaq_sign = ''
nasdaq_annotation = normalized_max_data.iloc[-1]['NASDAQ']
nasdaq_annotation = return_percentage(nasdaq_annotation)
if (nasdaq_annotation > 0):
        nasdaq_sign = '+'
nasdaq_annotation = str(nasdaq_annotation)
nasdaq_annotation = 'NASDAQ ' + nasdaq_sign + nasdaq_annotation + '%'
print('NASDAQ Annotation: ', nasdaq_annotation)

sandp_sign = ''
sandp_annotation = normalized_max_data.iloc[-1]['S&P500']
sandp_annotation = return_percentage(sandp_annotation)
if (sandp_annotation > 0):
        sandp_sign = '+'
sandp_annotation = str(sandp_annotation)
sandp_annotation = 'S&P500 ' + sandp_sign + sandp_annotation + '%'
print('S&P500 Annotation: ', sandp_annotation)

newspace_sign = ''
newspace_annotation = normalized_max_data.iloc[-1]['PV New Space']
newspace_annotation = return_percentage(newspace_annotation)
if (newspace_annotation > 0):
        newspace_sign = '+'
newspace_annotation = str(newspace_annotation)
newspace_annotation = 'PV New Space ' + newspace_sign + newspace_annotation + '%'
print('PV New Space Annotation: ', newspace_annotation)

legacy_sign = ''
legacy_annotation = normalized_max_data.iloc[-1]['PV Legacy Space']
legacy_annotation = return_percentage(legacy_annotation)
if (legacy_annotation > 0):
        legacy_sign = '+'
legacy_annotation = str(legacy_annotation)
legacy_annotation = 'PV Legacy Space ' + legacy_sign + legacy_annotation + '%'
print('PV Legacy Space Annotation: ', legacy_annotation)

#Now chart max/all data before we do anything more as saves having to figure out how to annotate these things into the dataframe

figure = px.line(normalized_max_data, x='Date', y=['NASDAQ', 'S&P500', 'PV New Space', 'PV Legacy Space'],
  color_discrete_map={
    'NASDAQ': '#68d8ff',
    'S&P500': '#006d97',
    'PV New Space': '#18a1cd',
    'PV Legacy Space': '#2b5d7d'
  },
  title='Max Historical Performance',
  template='plotly_white',
  width = 800,
  height = 600)

figure_mobile = px.line(normalized_max_data, x='Date', y=['NASDAQ', 'S&P500', 'PV New Space', 'PV Legacy Space'],
  color_discrete_map={
    'NASDAQ': '#68d8ff',
    'S&P500': '#006d97',
    'PV New Space': '#18a1cd',
    'PV Legacy Space': '#2b5d7d'
  },
  title='Max Historical Performance',
  template='plotly_white',
  width = 320,
  height = 400)

#Try to add annotations
figure_annotations = []
mobile_figure_annotations = []

#First define the default y-shifts for the annotations and then try to avoid any overlap
nasdaq_y_shift = 10
sandp_y_shift = 10
newspace_y_shift = 10
legacy_y_shift = 10

sandp_got_shifted = 'False'
newspace_got_shifted = 'False'

#First check NASDAQ vs S&P500 position - use relative % to see if we need to move
if (abs((normalized_max_data['NASDAQ'].values[-1]/normalized_max_data['S&P500'].values[-1])-1) < 0.02):
  #Brute force approach to the problem - if S&P500 got shifted set a flag, and adjust everything else based on that flag 
  sandp_got_shifted = 'True'
  if(((normalized_max_data['NASDAQ'].values[-1]/normalized_max_data['S&P500'].values[-1])-1) > 0):
    #NASDAQ Above S&P500, shift S&P500 down
    sandp_y_shift = 0
  else:
    #S&P500 above NASDAQ, shift S&P500 up
    sandp_y_shift = 20

#Next check NASDAQ vs New Space position - use relative % to see if we need to move
if (abs((normalized_max_data['NASDAQ'].values[-1]/normalized_max_data['PV New Space'].values[-1])-1) < 0.02):
  #Set the newspace_got_shifted flag
  newspace_got_shifted = 'True'
  if(((normalized_max_data['NASDAQ'].values[-1]/normalized_max_data['PV New Space'].values[-1])-1) > 0):
    #NASDAQ Above PV New Space, shift PV New Space down
    #But need to check NASDAQ vs S&P500 - if these guys overlapped then we need to shift PV New Space by more
    if(sandp_got_shifted == 'True'):
      newspace_y_shift = -10
    else:
      #If no NASDAQ/S&P500 overlap then can just adjust PV New Space by default
      newspace_y_shift = 0
  else:
    #PV New Space above NASDAQ, shift PV New Space up
    #But need to check NASDAQ vs S&P500 - if these ones overlapped then shift PV New Space by more
    if(sandp_got_shifted == 'True'):
      newspace_y_shift = 30
    else:
      newspace_y_shift = 20

#Finally check PV Legacy Space vs NASDAQ
if (abs((normalized_max_data['NASDAQ'].values[-1]/normalized_max_data['PV Legacy Space'].values[-1])-1) < 0.02):
  if(((normalized_max_data['NASDAQ'].values[-1]/normalized_max_data['PV Legacy Space'].values[-1])-1) > 0):
    #NASDAQ Above PV Legacy Space, shift PV Legacy Space down
    #But need to check NASDAQ vs others - if any of these guys overlapped then we need to shift PV Legacy Space by more
    if(sandp_got_shifted == 'True'):
      if(newspace_got_shifted == 'True'):
        legacy_y_shift = -20
      else:
        legacy_y_shift = -10
    else:
      #If no NASDAQ/S&P500 overlap then can just adjust PV New Space by default
      legacy_y_shift = 0
  else:
    #PV Legacy Space above NASDAQ, shift PV Legacy Space up
    #But need to check NASDAQ vs others - if these ones overlapped then shift PV Legacy Space by more
    if(sandp_got_shifted == 'True'):
      if(newspace_got_shifted == 'True'):
        legacy_y_shift = 35
      else:
        legacy_y_shift = 25
    else:
      legacy_y_shift = 20

#annotation_one = dict(x=normalized_max_data.iloc[-1]['Date'], y=normalized_max_data['NASDAQ'].values[-1], xref='x', yref='y', yshift=nasdaq_y_shift, xshift=5, showarrow=False, bgcolor='#68d8ff',font_color='#FFFFFF', text=nasdaq_annotation)
annotation_one = dict(x=1.01, y=normalized_max_data['NASDAQ'].values[-1], xref='paper', yref='y', yshift=nasdaq_y_shift, xshift=5, showarrow=False, bgcolor='#68d8ff',font_color='#FFFFFF', text=nasdaq_annotation)
mobile_annotation_one = dict(x=1.01, y=normalized_max_data['NASDAQ'].values[-1], xref='paper', yref='y', yshift=nasdaq_y_shift, xshift=5, showarrow=False, bgcolor='#68d8ff',font_color='#FFFFFF', text=nasdaq_annotation, font=dict(size=5))
figure_annotations.append(annotation_one)
mobile_figure_annotations.append(mobile_annotation_one)

#annotation_two = dict(x=normalized_max_data.iloc[-1]['Date], y=normalized_max_data['S&P500'].values[-1], xref='paper', yref='y', yshift=sandp_y_shift, xshift=5, showarrow=False, bgcolor='#006d97',font_color='#FFFFFF', text=sandp_annotation)
annotation_two = dict(x=1.01, y=normalized_max_data['S&P500'].values[-1], xref='paper', yref='y', yshift=sandp_y_shift, xshift=5, showarrow=False, bgcolor='#006d97',font_color='#FFFFFF', text=sandp_annotation)
mobile_annotation_two = dict(x=1.01, y=normalized_max_data['S&P500'].values[-1], xref='paper', yref='y', yshift=sandp_y_shift, xshift=5, showarrow=False, bgcolor='#006d97',font_color='#FFFFFF', text=sandp_annotation, font=dict(size=5))
figure_annotations.append(annotation_two)
mobile_figure_annotations.append(mobile_annotation_two)

#annotation_three = dict(x=normalized_max_data.iloc[-1]['Date'], y=normalized_max_data['PV New Space'].values[-1], xref='x', yref='y', yshift=newspace_y_shift, xshift=5, showarrow=False, bgcolor='#18a1cd',font_color='#FFFFFF', text=newspace_annotation)
annotation_three = dict(x=1.01, y=normalized_max_data['PV New Space'].values[-1], xref='paper', yref='y', yshift=newspace_y_shift, xshift=5, showarrow=False, bgcolor='#18a1cd',font_color='#FFFFFF', text=newspace_annotation)
mobile_annotation_three = dict(x=1.01, y=normalized_max_data['PV New Space'].values[-1], xref='paper', yref='y', yshift=newspace_y_shift, xshift=5, showarrow=False, bgcolor='#18a1cd',font_color='#FFFFFF', text=newspace_annotation, font=dict(size=5))
figure_annotations.append(annotation_three)
mobile_figure_annotations.append(mobile_annotation_three)

#annotation_four = dict(x=normalized_max_data.iloc[-1]['Date'], y=normalized_max_data['PV Legacy Space'].values[-1], xref='x', yref='y', yshift=legacy_y_shift, xshift=5, showarrow=False, bgcolor='#2b5d7d',font_color='#FFFFFF', text=legacy_annotation)
annotation_four = dict(x=1.01, y=normalized_max_data['PV Legacy Space'].values[-1], xref='paper', yref='y', yshift=legacy_y_shift, xshift=5, showarrow=False, bgcolor='#2b5d7d',font_color='#FFFFFF', text=legacy_annotation)
mobile_annotation_four = dict(x=1.01, y=normalized_max_data['PV Legacy Space'].values[-1], xref='paper', yref='y', yshift=legacy_y_shift, xshift=5, showarrow=False, bgcolor='#2b5d7d',font_color='#FFFFFF', text=legacy_annotation, font=dict(size=5))
figure_annotations.append(annotation_four)
mobile_figure_annotations.append(mobile_annotation_four)

figure.update_layout(annotations=figure_annotations)
figure.update_annotations(clicktoshow='onoff')
figure.update_annotations(xanchor='left')
figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
#figure.update_layout(hovermode='x unified')
#figure.update_layout(hovermode='x')
figure.update_layout(hovermode='closest')
figure.update_layout(yaxis_title='Relative Performance')
figure.update_layout(margin=dict(r=170))
figure.update_yaxes(fixedrange=True)

#Try and set legend on top
figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))

#print the figure
#print(figure)
graph_config = {'displayModeBar':False}
#figure.show(config=graph_config)
#figure.show()
figure.write_html('test_max_graph.html', config=graph_config)

#Do exactly the same for mobile - except using mobile annotations
figure_mobile.update_layout(annotations=mobile_figure_annotations)
figure_mobile.update_annotations(clicktoshow='onoff')
figure_mobile.update_annotations(xanchor='left')
figure_mobile.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
figure_mobile.update_layout(hovermode='closest')
figure_mobile.update_layout(yaxis_title='Relative Performance', font=dict(size=5))
figure_mobile.update_layout(margin=dict(l=20))
figure_mobile.update_yaxes(fixedrange=True)
figure_mobile.update_xaxes(fixedrange=True)

#Try and set legend on top
figure_mobile.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, font=dict(size=4)))

#print the figure
#print(figure)
graph_config = {'displayModeBar':False}
#figure_mobile.show(config=graph_config)
#figure.show()
figure_mobile.write_html('test_max_graph_mobile.html', config=graph_config)



##
#
#All graphs generated, time to commit new graph .html files to GitHub
#Commit done in shell script as easier
#
##

# First copy the various .html graph files to the stuff that gets committed to GitHub

shutil.copy('test_one_week_graph.html', './graphing_scripts/graph_repository/latest_one_week_graph.html')
shutil.copy('test_one_month_graph.html', './graphing_scripts/graph_repository/latest_one_month_graph.html')
shutil.copy('test_three_month_graph.html', './graphing_scripts/graph_repository/latest_three_month_graph.html')
shutil.copy('test_six_month_graph.html', './graphing_scripts/graph_repository/latest_six_month_graph.html')
shutil.copy('test_max_graph.html', './graphing_scripts/graph_repository/latest_max_graph.html')
shutil.copy('test_three_month_graph_allow_zoom.html', './graphing_scripts/graph_repository/latest_three_month_graph_allow_zoom.html')


#############
#
# Now try and do a smaller mobile graph - work on three month for starters
#
#############

#Actually do this up with the 3 month graph as all the setup is already there

shutil.copy('test_one_week_graph_mobile.html', './graphing_scripts/graph_repository/latest_one_week_graph_mobile.html')
shutil.copy('test_one_month_graph_mobile.html', './graphing_scripts/graph_repository/latest_one_month_graph_mobile.html')
shutil.copy('test_three_month_graph_mobile.html', './graphing_scripts/graph_repository/latest_three_month_graph_mobile.html')
shutil.copy('test_six_month_graph_mobile.html', './graphing_scripts/graph_repository/latest_six_month_graph_mobile.html')
shutil.copy('test_max_graph_mobile.html', './graphing_scripts/graph_repository/latest_max_graph_mobile.html')

#Import some more modules
#import os
#import subprocess

#def execute_shell_command(cmd, work_dir):
#    """Executes a shell command in a subprocess, waiting until it has completed.
# 
#    :param cmd: Command to execute.
#    :param work_dir: Working directory path.
#    """
#    pipe = subprocess.Popen(cmd, shell=True, cwd=work_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#    (out, error) = pipe.communicate()
#    print out, error
#    pipe.wait()
# 
# 
#def git_add(file_path, repo_dir):
#    """Adds the file at supplied path to the Git index.
#    File will not be copied to the repository directory.
#    No control is performed to ensure that the file is located in the repository directory.
# 
#    :param file_path: Path to file to add to Git index.
#    :param repo_dir: Repository directory.
#    """
#    cmd = 'git add ' + file_path
#    execute_shell_command(cmd, repo_dir)
# 
# 
#def git_commit(commit_message, repo_dir):
#    """Commits the Git repository located in supplied repository directory with the supplied commit message.
# 
#    :param commit_message: Commit message.
#    :param repo_dir: Directory containing Git repository to commit.
#    """
#    cmd = 'git commit -am "%s"' % commit_message
#    execute_shell_command(cmd, repo_dir)
# 
# 
#def git_push(repo_dir):
#    """Pushes any changes in the Git repository located in supplied repository directory to remote git repository.
# 
#    :param repo_dir: Directory containing git repository to push.
#    """
#    cmd = 'git push '
#    execute_shell_command(cmd, repo_dir)
# 
# 
#def git_clone(repo_url, repo_dir):
#    """Clones the remote Git repository at supplied URL into the local directory at supplied path.
#    The local directory to which the repository is to be clone is assumed to be empty.
# 
#    :param repo_url: URL of remote git repository.
#    :param repo_dir: Directory which to clone the remote repository into.
#    """
#    cmd = 'git clone ' + repo_url + ' ' + repo_dir
#    execute_shell_command(cmd, repo_dir)
#
#def update_date_file_in_remote_git_repository(in_repo_url):
#    """Clones the remote Git repository at supplied URL and adds/updates a .date file
#    containing the current date and time. The changes are then pushed back to the remote Git repository.
#    """
#    # Create temporary directory to clone the Git project into.
#    repo_path = tempfile.mkdtemp()
#    print("Repository path: " + repo_path)
#    date_file_path = repo_path + '/.date'
# 
#    try:
#        # Clone the remote GitHub repository.
#        git_clone(in_repo_url, repo_path)
# 
#        # Create/update file with current date and time.
#        if os.path.exists(date_file_path):
#            os.remove(date_file_path)
#        execute_shell_command('date > ' + date_file_path, repo_path)
# 
#        # Add new .date file to repository, commit and push the changes.
#        git_add(date_file_path, repo_path)
#        git_commit('Updated .date file', repo_path)
#        git_push(repo_path)
#    finally:
#        # Delete the temporary directory holding the cloned project.
#        shutil.rmtree(repo_path)
