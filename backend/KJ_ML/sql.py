import pandas as pd
from sqlalchemy import create_engine

# Define your MySQL database connection parameters
username = 'root'
password = ''
host = 'localhost'
port = '3306'  # Default MySQL port
database = 'kj'  # Your database name
table_name = 'rating_matrix'  # Your target table name
csv_file_path = "D:\\KJ_ML\\datasets\\ratings_matrix.csv"  # Path to your CSV file

# Create a connection string
connection_string = f'mysql+pymysql://{username}:{password}@{host}:{port}/{database}'

# Create a SQLAlchemy engine
engine = create_engine(connection_string)

# Read the CSV file into a DataFrame
df = pd.read_csv(csv_file_path)

# Import DataFrame into MySQL table
df.to_sql(table_name, con=engine, if_exists='replace', index=False)

print(f"Data from {csv_file_path} has been imported into the '{table_name}' table in the '{database}' database.")
