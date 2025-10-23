import pymysql
import pandas as pd

# Load CSV
df = pd.read_csv('/home/swiftcsv/mysite/medicine_inventory_200.csv')

# Connect to MySQL
connection = pymysql.connect(
    host='swiftcsv.mysql.pythonanywhere-services.com',
    user='swiftcsv',
    password='pythonanywhereman.com9836APE',
    database='swiftcsv$meddb'
)

cursor = connection.cursor()

# Insert data row by row
for _, row in df.iterrows():
    cursor.execute("""
        INSERT INTO medicine_inventory (
            medicine_id, name, composition, category, supplier_name, supplier_contact,
            batch_no, mfg_date, expiry_date, pack_size, unit_price, stock_quantity,
            reorder_level, location_rack, prescription_required, added_on
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, tuple(row))

connection.commit()
cursor.close()
connection.close()

print("✅ CSV data uploaded successfully!")
