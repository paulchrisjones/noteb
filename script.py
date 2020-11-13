import json
import time
import requests
import mysql.connector
from mysql.connector import Error

seconds_to_wait_between_requests = 15 #to avoid hammering noteb and your own database	
number_of_requests_to_make = 1000 #noteb gives you 1000 requests per day
using_public_api_key = False

def main():

	for _ in " " * number_of_requests_to_make:

		model_id = Get_model_id_from_save_file()

		if using_public_api_key:
			noteb_api_key = '112233aabbcc'
		else:
			from variables import noteb_api_key

		api_data = Get_api_data(model_id, noteb_api_key)
		print(api_data['daily_hits_left'] + ' hits left');
		#print(json.dumps(api_data, indent=4))

		if api_data['code'] == 10 and not using_public_api_key:
			print("Out of daily hits, switching to public api key.")
			using_public_api_key = True;
			continue

		if api_data['code'] == 10 and using_public_api_key:
			print("Out of daily hits, closing script. Try again tomorrrow.")
			exit()

		if api_data['code'] == 30:
			print("No laptop for thet ID. :(")
			Increment_model_id_in_save_file(model_id)
			Wait()
			continue

		elif not api_data['result']:
			print("No laptop data for that ID. :(") #The ID exists in the noteb database but there is no data associated with it 
			Increment_model_id_in_save_file(model_id)
			Wait()
			continue

		else:
			print("LAPTOP FOUND")
			laptop = Make_data_into_a_dictionary(api_data['result']['0'], model_id)
			Write_to_database(laptop)
			Increment_model_id_in_save_file(model_id)
			Wait()
			continue

def Get_model_id_from_save_file():
	file = open("current_model_id.txt","r")
	model_id = file.read()
	file.close()
	return model_id

def Increment_model_id_in_save_file(model_id):
	file = open("current_model_id.txt","w")
	new_model_id = str(int(model_id)+1)
	file.write(new_model_id)
	file.close()

def Get_api_data(model_id, noteb_api_key):
	print('Querying noteb database for laptop with ID ' + model_id + '...')
	response = requests.post('https://noteb.com/api/webservice.php', data={'apikey': noteb_api_key, 'method': "get_model_info", 'param[model_id]': int(model_id)})
	api_data = json.loads(response.text)
	return api_data 

def Make_data_into_a_dictionary(api_data, model_id):
	laptop_data = {
		'noteb_id': model_id,
		'name': api_data['model_info'][0]['name'],
		'noteb_name': api_data['model_info'][0]['noteb_name'],
		'image': api_data['model_resources']['thumbnail'],
		'primary_storage_model': api_data['primary_storage']['model'],
		'primary_storage_capacity': api_data['primary_storage']['cap'],
		'secondary_storage_model': api_data['secondary_storage']['model'],
		'secondary_storage_capacity': api_data['secondary_storage']['cap'],
		'motherboard_storage_slots': api_data['motherboard']['storage_slots'],
		'operating_system': api_data['operating_system']
	}
	return laptop_data


def Wait():
	print('Next request will be in ' + str(seconds_to_wait_between_requests) + ' seconds')
	print('')
	time.sleep(seconds_to_wait_between_requests)

def Write_to_database(laptop_data):

	from variables import host
	from variables import user
	from variables import password 
	from variables import database 

	conn = None
	print("Will save the result in the user's database.")
	print("Connecting to the user's database...")

	try:
		conn = mysql.connector.connect(
			host = host,
			user = user,
			password = password,
			database = database
		)

		if conn.is_connected():
			print('Connected. Saving data to database...')
			query = "INSERT INTO Laptops (Noteb_ID, Name, Noteb_name, Primary_storage_model, Primary_storage_capacity, Secondary_storage_model, Secondary_storage_capacity, Motherboard_storage_slots, Operating_system, Image) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
			args = (laptop_data['noteb_id'],laptop_data['name'],laptop_data['noteb_name'],laptop_data['primary_storage_model'],laptop_data['primary_storage_capacity'],laptop_data['secondary_storage_model'],laptop_data['secondary_storage_capacity'],laptop_data['motherboard_storage_slots'],laptop_data['operating_system'],laptop_data['image'])
			cursor = conn.cursor()
			cursor.execute(query, args)
			conn.commit()


	except Error as e:
		print(e)

	finally:
		if conn is not None and conn.is_connected():
			print('Done. Closing connection...')
			conn.close()
			print('Connection closed.')

if __name__ == '__main__':
    main()
