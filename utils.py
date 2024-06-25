import psycopg2, csv
import pandas as pd

def execute_query(query):
    db_params = {
        'dbname': 'postgres',
        'user': 'aura_admin',
        'password': 'England125',
        'host': 'auradata.postgres.database.azure.com',  # e.g., 'localhost' or '127.0.0.1'
        'port': '5432'  # e.g., '5432'
    }
    data=[]
    try:
        # Connect to your postgres DB
        connection = psycopg2.connect(**db_params)

        # Create a cursor object
        cursor = connection.cursor()

        # Execute a query
        cursor.execute(query)
        col_names = [desc[0] for desc in cursor.description]
        # Fetch all results from the executed query
        rows = cursor.fetchall()
        
        # Print fetched rows
        for row in rows:
            data.append(row)

        return col_names,data

    except Exception as error:
        print(f"Error: {error}")
        return "operation failed"

    finally:
        # Close the cursor and connection to the database
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def write_rows_to_csv(csv_file_name,data):
     with open(csv_file_name, mode='a', newline='') as file:
        writer = csv.writer(file)
        
        # Write the data rows
        writer.writerows(data)
        print(f"Data has been written to {csv_file_name}")
        

def write_headings_to_csv(csv_file_name,data):
    with open(csv_file_name, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(data)
    print("Headings created")

def extract_column_names(csv_file_path):
    try:
        # Read the CSV file into a DataFrame
        df = pd.read_csv(csv_file_path)

        # Extract column names
        column_names = df.columns.tolist()

        quoted_list = [f"'{item}'" for item in column_names]
        return ','.join(quoted_list)
    
    except FileNotFoundError:
        print(f"Error: The file at {csv_file_path} was not found.")
        return []
    except pd.errors.EmptyDataError:
        print(f"Error: The file at {csv_file_path} is empty.")
        return []
    except pd.errors.ParserError:
        print(f"Error: The file at {csv_file_path} could not be parsed.")
        return []
    
import requests

def download_csv(url, local_filename):
    # Send a HTTP request to the URL
    with requests.get(url, stream=True) as response:
        response.raise_for_status()  # Check if the request was successful
        # Open a local file in write-binary mode
        with open(local_filename, 'wb') as file:
            # Iterate over the response data in chunks and write to the file
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:  # Filter out keep-alive new chunks
                    file.write(chunk)



def extract_column_names(csv_file_path):
    try:
        # Read the CSV file into a DataFrame
        df = pd.read_csv(csv_file_path,encoding='latin-1')

        # Extract column names
        column_names = df.columns.tolist()

        quoted_list = [f"'{item}'" for item in column_names]
        return ','.join(quoted_list)
    
    except FileNotFoundError:
        print(f"Error: The file at {csv_file_path} was not found.")
        return []
    except pd.errors.EmptyDataError:
        print(f"Error: The file at {csv_file_path} is empty.")
        return []
    except pd.errors.ParserError:
        print(f"Error: The file at {csv_file_path} could not be parsed.")
        return []
    
