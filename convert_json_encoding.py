# convert_json_encoding.py

with open("product_data.json", "r", encoding="iso-8859-1") as source_file:
    content = source_file.read()

with open("product_data_utf8.json", "w", encoding="utf-8") as target_file:
    target_file.write(content)

print("✅ File converted from ISO-8859-1 to UTF-8.")
