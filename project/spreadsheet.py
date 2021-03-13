# -*- coding: utf-8 -*-
from googleapiclient.discovery import build
from google.oauth2 import service_account


import sqlite3
import time




SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = 'prepi.json'

creds = None
creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)




# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = '1Zk68h79xns5ezm1rh2vqezfHmVp0fdDroIaLxsoQJec'




service = build('sheets', 'v4', credentials=creds)

# Call the Sheets API
sheet = service.spreadsheets()
result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,range="data!A1:G13").execute()
values = result.get('values', [])
print(values)






cxn = sqlite3.connect('db.sqlite3')
cur = cxn.cursor()
rows = cur.execute('SELECT id, username, date_joined FROM auth_user')

FIELDS = ['id', 'Nome do usuario', 'Data de cadastro', 'Quantidade total de produtos', 'Data do primeiro cadastro de produto']
users = [FIELDS]
user_id_dict = {}
for row in rows:
	user_id_dict[row[0]] = [row[0], row[1], row[2][:10]]
cxn.close()



cxn = sqlite3.connect('db.sqlite3')
cur = cxn.cursor()
rows2 = cur.execute('SELECT auth_user.id, COUNT(*) FROM product_product, auth_user WHERE product_product.owner_id == auth_user.id GROUP BY auth_user.id')
for row in rows2:
	user_id_dict[row[1]].append(row[0])
	print(row,"here")
	#print(user_id_dict[row[1]])


rows3 = cur.execute('SELECT MIN(product_product.created_at),auth_user.id FROM product_product, auth_user WHERE product_product.owner_id == auth_user.id GROUP BY auth_user.id')

for row in rows3:
	user_id_dict[row[1]].append(row[0][:10])
	#print(row[0])


for row in user_id_dict.values():
	print(row)
	users.append(row)



data = {'values': users}

request = sheet.values().update(spreadsheetId=SAMPLE_SPREADSHEET_ID, range='data!A1', body=data, valueInputOption='USER_ENTERED').execute()

print(data)







"""
store = file.Storage('prepi.json')
creds = store.get()
if not creds or creds.invalid:
	flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
	flow = client.flow_from_clientsecrets('prepi.json', SCOPES)

SHEETS = discovery.build('sheets', 'v4', http=creds.authorize(Http()))
data = {'properties': {'title': 'Usuários [%s]' % time.ctime()}}
res = SHEETS.spreadsheets().create(body=data).execute()
SHEET_ID = res['spreadsheetId']
print('Created "%s"' % res[properties]['tittle'])

FIELDS = ('id', 'username', email, date_joined)

cxn = sqlite3.connect('db.sqlite3')
cur = cxn.cursor()
rows = cur.execute('SELECT * FROM auth_user')
cxn.close()
rows.insert(0, FIELDS)
data = {'values': [row[:3] for row in rows]}

SHEETS.spreadsheet().values().update(spreadsheetId=SHEET_ID, range='A1', body=data, valueInputOption='RAW').execute()
print('Wrote data to sheet:')
rows = SHEETS.spreadsheets().values().get(spreadsheetId=SHEET_ID, range='sheet1').execute().get('values', [])
for row in rows:
	print(row)
"""