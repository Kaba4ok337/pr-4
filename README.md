# Сбор данных об автомобиле

Программа `cars.py` запрашивает данные в NHTSA и CarsDataset и сохраняет результат в `cars_data.jsonl`.

Для запуска нужен Python и библиотека `aiohttp`:

```bash
pip install aiohttp
python cars.py
```

VIN, марку, модель и год можно изменить в начале `cars.py`. Поиск CarsDataset выполняется по марке, модели и году и может вернуть несколько вариантов.
