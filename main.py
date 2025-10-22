import concurrent.futures
from os import system, path, mkdir, getcwd, rename
from bs4 import BeautifulSoup
import requests
from datetime import datetime
from fake_useragent import UserAgent
import threading
import time
import sys

class cs:
    INFO = '\033[93m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    END = '\033[0m'

_ = system("cls")

name = input(f"{cs.INFO}Имя: ")
offset = input("Оффсет: ")
threads_input = input("Количество потоков: ")

try:
    offset = int(offset)
    if offset < 1:
        print(f"{cs.RED}Ошибка: Оффсет должен быть положительным целым числом!{cs.END}")
        exit()
except ValueError:
    print(f"{cs.RED}Ошибка: Оффсет должен быть целым числом!{cs.END}")
    exit()

try:
    threads = int(threads_input)
    if threads < 1:
        threads = 1
    if threads > 50:
        threads = 50
except ValueError:
    threads = 5
print(f"{cs.INFO}Используем {threads} потоков.{cs.END}")

def is_valid_date(year, month, day):
    try:
        datetime(year, month, day)
        return True
    except ValueError:
        return False

def get_file_extension(video_url, response):
    content_type = response.headers.get('Content-Type', '').lower()
    if '.mp4' in video_url or 'video/mp4' in content_type:
        return '.mp4'
    elif '.webm' in video_url or 'video/webm' in content_type:
        return '.webm'
    elif '.mov' in video_url or 'video/quicktime' in content_type:
        return '.mov'
    elif '.avi' in video_url or 'video/x-msvideo' in content_type:
        return '.avi'
    elif '.mkv' in video_url or 'video/x-matroska' in content_type:
        return '.mkv'
    elif '.ogv' in video_url or 'video/ogg' in content_type:
        return '.ogv'
    return '.mp4'

def search_animation(stop_event):
    animation = ['|', '/', '-', '\\']
    idx = 0
    while not stop_event.is_set():
        sys.stdout.write(f'\rПоиск... {animation[idx % 4]}')
        sys.stdout.flush()
        idx += 1
        time.sleep(0.2)
    sys.stdout.write('\rПоиск завершен!     \n')
    sys.stdout.flush()

total_downloaded = 0
error_log_file = f"{getcwd()}\\error_log.txt"

def log_error(message):
    with open(error_log_file, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()}: {message}\n")

def parse(name, day, month, offset_str, year):
    global total_downloaded
    try:
        ua = UserAgent()
        HEADERS = {'User-Agent': ua.random}
        url = f"https://telegra.ph/{name}-{month}-{day}{offset_str}"
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            log_error(f"Не удалось открыть {url}: Статус {response.status_code}")
            return
        soup = BeautifulSoup(response.content, 'html.parser')
        items = soup.findAll('video')
        videos = []
        for item in items:
            src = item.get('src')
            if src and not src.startswith("http"):
                videos.append(f"https://telegra.ph{src}")
        if videos:
            print(f"{cs.GREEN}ЗАГРУЗКА | Начало | {day}.{month}{offset_str}{cs.END}")
            base_dir = f"{getcwd()}\\videos"
            name_dir = f"{base_dir}\\{name}"
            date_dir = f"{name_dir}\\{month}_{day}_{offset_str[1:]}" if offset_str else f"{name_dir}\\{month}_{day}"
            for directory in [base_dir, name_dir, date_dir]:
                if not path.isdir(directory):
                    mkdir(directory)
            downloaded_count = 0
            for i, video_url in enumerate(videos):
                try:
                    response = requests.get(video_url, headers={'User-Agent': ua.random}, timeout=10)
                    ext = get_file_extension(video_url, response)
                    file_name = f"{date_dir}/{month}_{day}_{offset_str[1:]}_{i}{ext}" if offset_str else f"{date_dir}/{month}_{day}_{i}{ext}"
                    with open(file_name, "wb") as file:
                        file.write(response.content)
                    downloaded_count += 1
                    total_downloaded += 1
                except Exception as e:
                    log_error(f"Не удалось скачать {video_url}: {str(e)}")
            if downloaded_count > 0:
                new_date_dir = f"{date_dir} - {downloaded_count} video"
                try:
                    rename(date_dir, new_date_dir)
                except Exception as e:
                    log_error(f"Не удалось переименовать папку {date_dir}: {str(e)}")
            print(f"{cs.GREEN}ЗАГРУЗКА | Конец | {day}.{month}{offset_str} | Скачано {downloaded_count} видео | Всего скачано: {total_downloaded}{cs.END}")
    except Exception as e:
        log_error(f"Ошибка доступа к {url}: {str(e)}")

def main():
    print("")
    year = datetime.now().year
    tasks = []
    for _month in range(1, 13):
        for _day in range(31, 0, -1):
            if is_valid_date(year, _month, _day):
                for _offset in range(1, offset + 1):
                    offset_str = "" if _offset == 1 else f"-{_offset}"
                    tasks.append((name, f"{_day:02}", f"{_month:02}", offset_str, year))
    
    stop_event = threading.Event()
    animation_thread = threading.Thread(target=search_animation, args=(stop_event,))
    animation_thread.start()
    
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
            list(executor.map(lambda args: parse(*args), tasks))
    except Exception as e:
        log_error(f"Критическая ошибка в ThreadPoolExecutor: {str(e)}")
    finally:
        stop_event.set()
        animation_thread.join()

if __name__ == "__main__":
    main()