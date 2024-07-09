import json

class ConfigManager:
    def __init__(self, filename):
        self.filename = filename
        self.config = self.load_config()

    def load_config(self):
        try:
            with open(self.filename, "r") as f:
                config = json.load(f)
        except FileNotFoundError:
            config = {}
        return config
    def save_config(self):
        with open(self.filename, "w") as f:
            json.dump(self.config, f, indent=4)

    def get_value(self, key):
        return self.config.get(key)

    def get_values(self, key):
        values = []
        if key in self.config:
            values.extend(self.config[key])  # Добавляем все значения из списка
        return values

    def get_all_values(self):
        return self.config # возвращаем весь файл

    def set_value(self, key, value):
        if key in self.config:
            # Проверяем, что значение является списком
            if isinstance(self.config[key], list):
                if value not in self.config[key]:
                    self.config[key].append(value)  # Добавляем значение, если его еще нет в списке
            else:
                # Если значение не является списком, создаем новый список с текущим и новым значением
                if value != self.config[key]:
                    self.config[key] = [self.config[key], value]
        else:
            self.config[key] = value  # Создаем новую запись с одним значением
        self.save_config()

    def delete_value(self, key, value):
        try:
            if key in self.config and isinstance(self.config[key], list):
                if value in self.config[key]:
                    self.config[key].remove(value)
                    self.save_config()
                else:
                    raise ValueError(f"Value '{value}' not found in list for key '{key}'")
            else:
                raise ValueError(f"Key '{key}' not found or value is not a list")
        except ValueError as e:
            print(f"Error deleting value: {e}")
