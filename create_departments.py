#Скрипт для автоматического создания fixtures - departments.json из загруженной структуры в таблице Structure.xlsx 

import pandas as pd
import json

df = pd.read_excel("./Structure.xlsx")
df.columns = ["код", "управление", "отдел"]

fixtures = [{
    "model": "users.department",
    "pk": 1,
    "fields": {
        "department_id": "666",
        "department_name": "Superuser"
    }
}]

for idx, row in df.iterrows():
    fixture = {
        "model": "users.department",
        "pk": idx + 2,
        "fields": {
            "department_id": row["код"],
            "department_name": row["код"]
        }
    }
    fixtures.append(fixture)

with open("fixtures/departments.json", "w", encoding="utf-8") as f:
    json.dump(fixtures, f, ensure_ascii=False, indent=4)

print("Фикстуры успешно сохранены в fixtures/departments.json")