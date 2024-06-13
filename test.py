sql_query="SELECT * FROM film WHERE rental_rate < 5"


import psycopg2, csv
# Define your database connection parameters
db_params = {
    'dbname': 'dvdrental',
    'user': 'postgres',
    'password': 'akashraj',
    'host': 'localhost',  # e.g., 'localhost' or '127.0.0.1'
    'port': '5432'  # e.g., '5432'
}

try:
    # Connect to your postgres DB
    connection = psycopg2.connect(**db_params)

    # Create a cursor object
    cursor = connection.cursor()

    # Execute a query
    cursor.execute(sql_query+";")

    # Fetch all results from the executed query
    rows = cursor.fetchall()
    data=[]
    # Print fetched rows
    for row in rows:
        data.append(row)

    csv_file = 'output.csv'

# Write the data to a CSV file
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        
        # Optional: Write the header
        
        
        # Write the data rows
        writer.writerows(data)

    print(f"Data has been written to {csv_file}")

except Exception as error:
    print(f"Error: {error}")

finally:
    # Close the cursor and connection to the database
    if cursor:
        cursor.close()
    if connection:
        connection.close()