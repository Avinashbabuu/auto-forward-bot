import json

def load_data():
    with open("database.json", "r") as file:
        return json.load(file)

def save_data(data):
    with open("database.json", "w") as file:
        json.dump(data, file, indent=4)

def apply_filters(text):
    data = load_data()
    for word in data["filters"]:
        text = text.replace(word, "****")  # Replace filtered word with ****
    return text
