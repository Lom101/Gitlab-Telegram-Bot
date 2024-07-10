import json

class ConfigManager:
    def __init__(self, filename='config.json'):
        """
                Конструктор класса ConfigManager.

                Args:
                - filename (str): Имя файла конфигурации. По умолчанию 'config.json'.
                """
        self.filename = filename
        self.data = self.load_config()

    def load_config(self):
        """
                Загружает данные из файла конфигурации.

                Returns:
                - dict: Загруженные данные конфигурации в формате словаря.
                """
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_config(self):
        """
                Сохраняет текущие данные конфигурации в файл.
                """
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4)

    def add_value(self, key, value):
        """
                Добавляет значение к списку, связанному с указанным ключом в данных конфигурации.

                Args:
                - key (str): Ключ, к которому добавляется значение.
                - value (any): Значение, которое нужно добавить.
                """
        if key in self.data:
            if value not in self.data[key]:
                self.data[key].append(value)
        else:
            self.data[key] = [value]
        self.save_config()

    def remove_value(self, key, value):
        """
                Удаляет значение из списка, связанного с указанным ключом в данных конфигурации.
                Если после удаления список становится пустым, удаляет ключ целиком.

                Args:
                - key (str): Ключ, из которого удаляется значение.
                - value (any): Значение, которое нужно удалить.
                """
        if key in self.data and value in self.data[key]:
            self.data[key].remove(value)
            if not self.data[key]:
                del self.data[key]
            self.save_config()

    def get_values(self, key):
        """
                Возвращает список значений, связанных с указанным ключом в данных конфигурации.

                Args:
                - key (str): Ключ, для которого нужно получить список значений.

                Returns:
                - list: Список значений, связанных с указанным ключом. Если ключ отсутствует, возвращает пустой список.
                """
        return self.data.get(key, [])

    def get_all_entries(self):
        """
               Возвращает все записи (ключ-значение) из данных конфигурации.

               Returns:
               - dict_items: Все записи данных конфигурации в формате dict_items.
               """
        return self.data.items()