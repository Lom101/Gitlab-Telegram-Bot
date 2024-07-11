import json

class ConfigManager:
    def __init__(self, filename='config.json'):
        # Инициализация класса ConfigManager
        self.filename = filename
        self.data = self.load_config()

    def load_config(self):
        # Загружает конфигурацию из JSON-файла
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_config(self):
        # Сохраняет текущую конфигурацию в JSON-файл
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4)

    def add_value(self, key, value):
        # Добавляет значение в конфигурацию
        if key in self.data:
            if value not in self.data[key]:
                self.data[key].append(value)
        else:
            self.data[key] = [value]
        self.save_config()

    def remove_value(self, key, value):
        # Удаляет значение из конфигурации
        if key in self.data and value in self.data[key]:
            self.data[key].remove(value)
            if not self.data[key]:
                del self.data[key]
            self.save_config()

    def get_values(self, key):
        # Возвращает значения для заданного ключа
        return self.data.get(key, [])

    def get_all_entries(self):
        # Возвращает все записи конфигурации
        return self.data.items()
