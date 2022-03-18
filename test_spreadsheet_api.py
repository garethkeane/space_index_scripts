#Trying some Yahoo Finance stuff - first setup yfinance, pandas (data), and re (regex) 
import re
import csv
import datetime
#import Google
#import google
from csv import writer
#Way to erase sheets using Create_Service
#from google import Create_Service

#Now try and write to Google Sheet
import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

credentials = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
client = gspread.authorize(credentials)

#spreadsheet = client.open('Testing_Google_Sheet_API_Calls')

#Dump a timestamp to the CSV file every time this script runs
current_time = datetime.datetime.now()
time_data =['Timestamp', current_time]

with open ('test_dummy_data.csv', 'a', newline='') as f_object:
        writer_object = writer(f_object)
        writer_object.writerow(time_data)
        f_object.close

#Now Update Test Spreadsheet Tabs
spreadsheetId = 'Testing_Google_Sheet_API_Calls'
#First Market Cap Data
sheetName = 'Example_To_Wipe'
csvFile = 'test_dummy_data.csv'

#Google sheet wipe:
#
#Do this with clear() command on a specific sheet in the spreadsheet

sheet = client.open(spreadsheetId)
#active_sheet = sheet.get_worksheet(1)
active_sheet = sheet.worksheet('Example_To_Wipe')
active_sheet.clear()

sheet.values_update (
	sheetName,
	params={'valueInputOption': 'USER_ENTERED'},
	body={'values': list(csv.reader(open(csvFile)))}
)

