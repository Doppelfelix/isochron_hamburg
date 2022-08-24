import json
from tqdm import tqdm
import pandas as pd
with open('all_stations.json', 'r') as myfile:
    raw_data=myfile.read()

json_data = json.loads(raw_data)

list_of_rows = []
for dur in tqdm(json_data):
    for station in dur["stations"]:
        row = {}
        row["id"]  = station["id"]
        row["name"] = station["name"]
        row["lat"] = station["location"]["latitude"]
        row["lon"] = station["location"]["longitude"]
        row["subway"] = station["products"]["subway"]
        row["suburban"] = station["products"]["suburban"]
        list_of_rows.append(row)    
df = pd.DataFrame(list_of_rows)

df_sub = df.loc[(df["subway"] == True) | (df["suburban"] == True)]
df_ham = df_sub.loc[df_sub["name"].str.contains("Hamburg", regex=False)]
df_ham = df_ham.drop_duplicates(subset=["name"])
df_ham.to_csv('cleaned_station.csv', index=False)

