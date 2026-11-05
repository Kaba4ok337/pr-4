import aiohttp
import asyncio
import json
import random
from datetime import datetime


VIN = "1HGCM82633A004352"
BRAND = "Honda"
MODEL = "Accord"
YEAR = 2003

NHTSA_URL = (
    f"https://vpic.nhtsa.dot.gov/api/vehicles/"
    f"DecodeVinValues/{VIN}?format=json"
)
CARS_URL = "https://api.carsdataset.com/api/v1/preview/search"

MAX_CONCURRENT = 3
TIMEOUT = 5
MAX_RETRIES = 3
RETRY_DELAY = 2
INTERVAL = 600
OUTPUT_FILE = "cars_data.jsonl"


async def fetch_data(session, url, sem, label, params=None):
    for attempt in range(1, MAX_RETRIES + 1):
        async with sem:
            try:
                print(f"[{label}] попытка {attempt}: {url}")

                async with session.get(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json(content_type=None)
                        print(f"[{label}] успех")
                        return data

                    print(f"[{label}] код {resp.status}")

                    if 400 <= resp.status < 500 and resp.status != 429:
                        return None

            except asyncio.TimeoutError:
                print(f"[{label}] таймаут")

            except aiohttp.ClientError as e:
                print(f"[{label}] ошибка сети: {e}")

            except ValueError as e:
                print(f"[{label}] некорректный JSON: {e}")

            except Exception as e:
                print(f"[{label}] неизвестная ошибка: {e}")
                return None

        if attempt < MAX_RETRIES:
            await asyncio.sleep(
                RETRY_DELAY * attempt + random.uniform(0, 1)
            )

    print(f"[{label}] попытки исчерпаны")
    return None


async def get_cars_info():
    sem = asyncio.Semaphore(MAX_CONCURRENT)
    timeout = aiohttp.ClientTimeout(total=TIMEOUT)

    params = {
        "brand": BRAND,
        "model": MODEL,
        "year_min": YEAR,
        "year_max": YEAR,
    }

    async with aiohttp.ClientSession(timeout=timeout) as session:
        nhtsa_task = fetch_data(session, NHTSA_URL, sem, "NHTSA")
        cars_task = fetch_data(session, CARS_URL, sem, "CarsDataset", params)

        nhtsa_result, cars_result = await asyncio.gather(
            nhtsa_task,
            cars_task,
        )

    return {
        "timestamp": datetime.now().isoformat(),
        "VIN": VIN,
        "brand": BRAND,
        "model": MODEL,
        "year": YEAR,
        "NHTSA": nhtsa_result,
        "CarsDataset": cars_result,
    }


def save_data(data, filename=OUTPUT_FILE):
    with open(filename, "a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")

    print(f"Сохранено в {filename}")


async def periodic_collector(interval=INTERVAL):
    while True:
        try:
            data = await get_cars_info()
            if data:
                save_data(data)

        except Exception as e:
            print(f"Ошибка в цикле сбора: {e}")

        await asyncio.sleep(interval)


async def main():
    data = await get_cars_info()
    print(json.dumps(data, indent=2, ensure_ascii=False))
    save_data(data)


if __name__ == "__main__":
    asyncio.run(main())