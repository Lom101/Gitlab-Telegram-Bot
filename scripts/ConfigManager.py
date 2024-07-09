import json

class ConfigManager:
    def __init__(self, filename='config.json'):
        self.filename = filename
        self.data = self.load_config()

    def load_config(self):
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_config(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4)

    def add_value(self, key, value):
        if key in self.data:
            if value not in self.data[key]:
                self.data[key].append(value)
        else:
            self.data[key] = [value]
        self.save_config()

    def remove_value(self, key, value):
        if key in self.data and value in self.data[key]:
            self.data[key].remove(value)
            if not self.data[key]:
                del self.data[key]
            self.save_config()

    def get_values(self, key):
        return self.data.get(key, [])

    def get_all_entries(self):
        return self.data.items()