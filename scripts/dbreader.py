
import dbf
# from dbf import TABLE_DIRECTORY


# Configure Thai character encoding
# dbf.ENCODING = 'tis-620'  # Thai Industrial Standard encoding

# Open the table
table = dbf.Table('/media/bodhirasa/123gb/Tipitaka/Dbf1/wordat.dbf')
table.open()

# Print field names first
print("Fields in the database:", table.field_names)

# Read records
try:
    for record in table:
        # Print each field separately to avoid encoding issues
        for field_name in table.field_names:
            try:
                value = record[field_name]
                print(f"{field_name}: {value}")
            except UnicodeDecodeError as e:
                print(f"Encoding error in field {field_name}: {e}")
        print("-" * 50)  # Separator between records
except Exception as e:
    print(f"Error: {e}")
finally:
    table.close()