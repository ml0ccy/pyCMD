import os
import subprocess
import psutil
from colorama import Fore, Style, init, Back
import sys
import platform
import json
from lang_data import DEFAULT_LANG_DATA
import shlex

init()

default_prompt_color = Fore.BLUE
default_text_color = Fore.WHITE
default_error_color = Fore.RED
default_header_color = Fore.YELLOW
default_background_color = Back.RESET

prompt_color = Fore.BLUE
text_color = Fore.WHITE
error_color = Fore.RED
header_color = Fore.YELLOW
background_color = Back.RESET

CONFIG_FILE = "config.json"

def du(path='.'):
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                # skip if it is symbolic link
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)
        print(Fore.GREEN + f"Размер '{path}': {total_size / (1024 * 1024):.2f} MB" + Style.RESET_ALL)
    except FileNotFoundError:
        print(Fore.RED + f"Директория '{path}' не найдена." + Style.RESET_ALL)
    except OSError as e:
        print(Fore.RED + f"Ошибка: {e}" + Style.RESET_ALL)

def tree(path='.', indent=''):
    try:
        items = os.listdir(path)
    except FileNotFoundError:
        print(Fore.RED + f"Директория '{path}' не найдена." + Style.RESET_ALL)
        return
    except NotADirectoryError:
        print(Fore.RED + f"'{path}' не является директорией." + Style.RESET_ALL)
        return
    except PermissionError: # Обработка ошибки доступа
        print(Fore.RED + f"Отказано в доступе к директории '{path}'." + Style.RESET_ALL)
        return

    for item in items:
        print(indent + Fore.CYAN + item + Style.RESET_ALL)
        item_path = os.path.join(path, item)
        if os.path.isdir(item_path):
            tree(item_path, indent + '  ')

def load_language(lang_code):
    filepath = os.path.join("languages", f"{lang_code}.json") # путь строится корректно
    print(f"Попытка загрузить файл: {filepath}")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print(Fore.RED + f"Ошибка загрузки файла языка '{filepath}'. Используется английский по умолчанию." + Style.RESET_ALL)
        return DEFAULT_LANG_DATA

def load_theme(theme_path):
    try:
        with open(theme_path, 'r', encoding='utf-8') as f:
            theme = json.load(f)
            return theme
    except (FileNotFoundError, json.JSONDecodeError):
        print(Fore.RED + f"Ошибка загрузки файла темы '{theme_path}'. Использованы настройки по умолчанию." + Style.RESET_ALL)
        return None

def apply_theme(theme):
    global prompt_color, text_color, error_color, header_color, background_color
    if theme is None:
        prompt_color = default_prompt_color
        text_color = default_text_color
        error_color = default_error_color
        header_color = default_header_color
        background_color = default_background_color
        os.system('cls' if os.name == 'nt' else 'clear')
        print(background_color, end="")
        return

    prompt_color = getattr(Fore, theme.get("prompt_color", "blue").upper(), default_prompt_color)
    text_color = getattr(Fore, theme.get("text_color", "white").upper(), default_text_color)
    error_color = getattr(Fore, theme.get("error_color", "red").upper(), default_error_color)
    header_color = getattr(Fore, theme.get("header_color", "yellow").upper(), default_header_color)
    background_color = getattr(Back, theme.get("background_color", "BLACK").upper(), default_background_color)
    os.system('cls' if os.name == 'nt' else 'clear')
    print(background_color, end="")

def load_config():
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        print(Fore.RED + f"Ошибка чтения файла конфигурации '{CONFIG_FILE}'. Будут использованы настройки по умолчанию." + Style.RESET_ALL)
        return {}

def save_config(config):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(Fore.RED + f"Ошибка записи в файл конфигурации: {e}" + Style.RESET_ALL)

def is_executable(path):
    return os.path.isfile(path) and os.access(path, os.X_OK)

def run_script(script_path):
    try:
        if not os.path.isabs(script_path):
            script_path = os.path.join(os.getcwd(), script_path)

        if not os.path.exists(script_path):
            print(Fore.RED + f"Скрипт '{script_path}' не найден." + Style.RESET_ALL)
            return

        # Важное изменение: capture_output=True и text=True
        result = subprocess.run([sys.executable, script_path], capture_output=True, text=True, check=False)

        if result.returncode == 0:  # Проверяем код возврата
            print(Fore.GREEN + "Вывод скрипта:" + Style.RESET_ALL)
            print(result.stdout) #вывод результата выполнения скрипта
        else:
            print(Fore.RED + f"Скрипт '{script_path}' завершился с кодом {result.returncode}." + Style.RESET_ALL)
            if result.stderr:
                print(Fore.RED + "Ошибки скрипта:" + Style.RESET_ALL)
                print(result.stderr)

    except Exception as e:
        print(Fore.RED + f"Произошла ошибка: {e}" + Style.RESET_ALL)

def system_info():
    print(Fore.YELLOW + "=== Системная информация ===" + Style.RESET_ALL)
    print(f"Имя компьютера: {os.environ['COMPUTERNAME']}")
    print(f"Операционная система: {platform.system()} {platform.version()}")
    print(f"Загрузка CPU: {psutil.cpu_percent()}%")
    print(f"Память: {psutil.virtual_memory().total / (1024 * 1024 * 1024):.2f} GB")
    print(f"Свободная память: {psutil.virtual_memory().available / (1024 * 1024 * 1024):.2f} GB")
    print(f"Диск C: ")
    disk_usage = psutil.disk_usage('/')
    print(f"  Общий размер: {disk_usage.total / (1024 * 1024 * 1024):.2f} GB")
    print(f"  Свободно: {disk_usage.free / (1024 * 1024 * 1024):.2f} GB")

def process_list(filter_name=None):
    print(Fore.YELLOW + "PID\tИмя\t\t% ЦП" + Style.RESET_ALL)
    for process in psutil.process_iter():
        try:
            process_info = process.as_dict(attrs=['pid', 'name', 'cpu_percent'])
            name = process_info['name']
            if filter_name is None or filter_name.lower() in name.lower():  # Фильтрация без учета регистра
                print(f"{process_info['pid']}\t{name[:15]}\t\t{process_info['cpu_percent']}")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

def kill_process(pid):
    try:
        process = psutil.Process(int(pid))  # Преобразуем PID в целое число
        process.kill()
        print(Fore.GREEN + f"Процесс с PID {pid} успешно завершен." + Style.RESET_ALL)
    except psutil.NoSuchProcess:
        print(Fore.RED + f"Процесс с PID {pid} не найден." + Style.RESET_ALL)
    except psutil.AccessDenied:
        print(Fore.RED + f"Отказано в доступе к завершению процесса с PID {pid}." + Style.RESET_ALL)
    except ValueError:
        print(Fore.RED + "Некорректный PID. Введите целое число." + Style.RESET_ALL)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def shell_loop():
    current_lang = "en_US"
    lang_data = load_language(current_lang)
    config = load_config()
    theme = None
    theme_path = config.get("last_theme")
    if theme_path:
        theme = load_theme(theme_path)
        if theme:
            apply_theme(theme)

    while True:
        current_path = os.getcwd()
        command_line = input(background_color + prompt_color + current_path + lang_data["prompt"] + Style.RESET_ALL)
        if command_line == "exit":
            break

        try:
            command_parts = shlex.split(command_line)
            if not command_parts:
                continue

            command = command_parts[0]
            arguments = command_parts[1:]

            if command == "theme":
                if arguments:
                    if arguments[0].lower() == "none":  # проверка на аргумент none
                        apply_theme(None)
                        config.pop("last_theme", None)  # удаляем тему из конфига
                        save_config(config)
                        print(Fore.GREEN + "Тема сброшена на стандартную." + Style.RESET_ALL)
                    else:
                        theme_path = arguments[0]
                        theme = load_theme(theme_path)
                        if theme:
                            apply_theme(theme)
                            config["last_theme"] = theme_path
                            save_config(config)
                elif theme:
                    print(Fore.GREEN + f"Текущая тема: {theme_path}" + Style.RESET_ALL)
                else:
                    print(Fore.YELLOW + "Тема не установлена, используются стандартные настройки." + Style.RESET_ALL)
            elif command == "process_list":
                if arguments:  # Если есть аргументы, используем их как фильтр
                    filter_name = arguments[0]
                    process_list(filter_name)
                else:
                    process_list()
            elif command == "du":
                path = "." if not arguments else arguments[0]
                du(path)
            elif command == "kill":
                if arguments:
                    kill_process(arguments[0])
                else:
                    print(Fore.RED + "Укажите PID процесса для завершения." + Style.RESET_ALL)
            elif command == "lang":
                if arguments:
                    lang_code = arguments[0]  # получаем только "ru_RU" или "en_US"
                    lang_data = load_language(lang_code)  # load_language сам добавит languages/ и .json
                    current_lang = lang_code
                else:
                    print(Fore.GREEN + f"Текущий язык: {current_lang}" + Style.RESET_ALL)
            elif command == "tree":
                path = "." if not arguments else arguments[0]
                tree(path)
            elif command == "system_info":
                system_info()
            elif command == "run":
                if arguments:
                    script_path = arguments[0]
                    run_script(script_path)
                else:
                    print(Fore.RED + "Укажите путь к скрипту." + Style.RESET_ALL)
            elif command == "cd":
                if arguments:
                    try:
                        os.chdir(arguments[0])
                        print(Fore.GREEN + f"Текущая директория изменена на: {os.getcwd()}" + Style.RESET_ALL)
                    except FileNotFoundError:
                        print(Fore.RED + f"Директория '{arguments[0]}' не найдена." + Style.RESET_ALL)
                    except NotADirectoryError:
                        print(Fore.RED + f"'{arguments[0]}' не является директорией." + Style.RESET_ALL)
                    except OSError as e: # Обработка других ошибок файловой системы
                        print(Fore.RED + f"Ошибка при смене директории: {e}" + Style.RESET_ALL)
                else:
                    print(Fore.YELLOW + f"Текущая директория: {os.getcwd()}" + Style.RESET_ALL) # Вывод текущей директории, если аргумент не указан
            elif command == "clear" or command == "cls":
                clear_screen()
            elif command == "help":
                print(Fore.YELLOW + lang_data["available_commands"] + Style.RESET_ALL)
                print("process_list - " + lang_data["process_list"])
                print("kill <PID> - " + lang_data["kill"])
                print("system_info - " + lang_data["system_info"])
                print("run <path_for_script> - " + lang_data["run"])
                print("cd <path> - " + lang_data["cd"])
                print("clear/cls - " + lang_data["clear/cls"])
                print("theme <path_for_file> - " + lang_data["theme"])
                print("theme none - " + lang_data["theme_reset"])
                print("exit - " + lang_data["exit"])
            else:  # Обработка внешних команд
                if sys.platform == "win32":  # для windows
                    if not (is_executable(command) or is_executable(command + ".exe") or is_executable(
                            os.path.join(os.getcwd(), command)) or is_executable(
                            os.path.join(os.getcwd(), command + ".exe"))):
                        print(Fore.RED + lang_data["command_not_found"] + Style.RESET_ALL)
                        continue  # переходим к следующей итерации цикла, не вызывая subprocess.run
                else:  # для linux/macOS
                    if not (is_executable(command) or is_executable(os.path.join(os.getcwd(), command))):
                        print(Fore.RED + lang_data["command_not_found"] + Style.RESET_ALL)
                        continue  # переходим к следующей итерации цикла, не вызывая subprocess.run
                subprocess.run(command_parts, check=True, capture_output=True, text=True)

        except subprocess.CalledProcessError as e:
            print(Fore.RED + f"Ошибка выполнения команды: {e}" + Style.RESET_ALL)
            if e.stderr:
                print(Fore.RED + e.stderr + Style.RESET_ALL)
        except OSError as e:
            print(Fore.RED + f"Ошибка ОС: {e}" + Style.RESET_ALL)
        except ValueError as e:
            print(Fore.RED + f"Ошибка ввода: {e}" + Style.RESET_ALL)
        except IndexError:
            print(Fore.RED + lang_data["invalid_input"] + Style.RESET_ALL)

shell_loop()
