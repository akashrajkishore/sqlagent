import psycopg2, csv

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


def write_rows_to_csv(csv_file,data):
     with open(csv_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        
        # Write the data rows
        writer.writerows(data)
        print(f"Data has been written to {csv_file}")
        

def write_headings_to_csv(csv_file,data):
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(data)
    print("Headings created")