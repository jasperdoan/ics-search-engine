import json

with open("full_analytics/index.json", "r") as file:
    index_data = json.load(file)

with open("index_new.txt", "w") as txt_file:
    for key, value in index_data.items():
        txt_file.write(f"{key}: {value}\n")

seek_position_dict = {}

with open("index_new.txt", "r") as txt_file:
    while True:
        seek_pos = txt_file.tell()
        line = txt_file.readline()
        
        if not line:
            break 
        
        key = line.split(":")[0].strip()  
        seek_position_dict[key] = seek_pos

with open("secondary_index.json", "w") as json_file:
    json.dump(seek_position_dict, json_file, indent=4)

print("Process completed successfully!")
