import os
import subprocess
import time

import psutil
import sys
import platform
import json
from lang_data import DEFAULT_LANG_DATA
import shlex
from utils.command_list import commands
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.lexers import PygmentsLexer
from pygments.lexers.shell import BashLexer
import operator
import ast

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
        print(f"Размер '{path}': {total_size / (1024 * 1024):.2f} MB")
    except FileNotFoundError:
        print(f"Директория '{path}' не найдена.")
    except OSError as e:
        print(f"Ошибка: {e}")

def tree(path='.', indent=''):
    try:
        items = os.listdir(path)
    except FileNotFoundError:
        print(f"Директория '{path}' не найдена.")
        return
    except NotADirectoryError:
        print(f"'{path}' не является директорией.")
        return
    except PermissionError: # Обработка ошибки доступа
        print(f"Отказано в доступе к директории '{path}'.")
        return

    for item in items:
        print(indent + item)
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
        print(f"Ошибка загрузки файла языка '{filepath}'. Используется английский по умолчанию.")
        return DEFAULT_LANG_DATA

def load_config():
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        print(f"Ошибка чтения файла конфигурации '{CONFIG_FILE}'. Будут использованы настройки по умолчанию.")
        return {}

def save_config(config):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Ошибка записи в файл конфигурации: {e}")

def is_executable(path):
    return os.path.isfile(path) and os.access(path, os.X_OK)

def run_script(script_path):
    try:
        if not os.path.isabs(script_path):
            script_path = os.path.join(os.getcwd(), script_path)

        if not os.path.exists(script_path):
            print(f"Скрипт '{script_path}' не найден.")
            return

        # Важное изменение: capture_output=True и text=True
        result = subprocess.run([sys.executable, script_path], capture_output=True, text=True, check=False)

        if result.returncode == 0:  # Проверяем код возврата
            print("Вывод скрипта:")
            print(result.stdout) #вывод результата выполнения скрипта
        else:
            print(f"Скрипт '{script_path}' завершился с кодом {result.returncode}.")
            if result.stderr:
                print("Ошибки скрипта:")
                print(result.stderr)

    except Exception as e:
        print(f"Произошла ошибка: {e}")

def system_info():
    print("=== Системная информация ===")
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
    print("PID\tИмя\t\t% ЦП")
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
        print(f"Процесс с PID {pid} успешно завершен.")
    except psutil.NoSuchProcess:
        print(f"Процесс с PID {pid} не найден.")
    except psutil.AccessDenied:
        print(f"Отказано в доступе к завершению процесса с PID {pid}.")
    except ValueError:
        print("Некорректный PID. Введите целое число.")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

operators = {
    ast.Add: operator.add, # +
    ast.Sub: operator.sub, # -
    ast.Mult: operator.mul, # *
    ast.Div: operator.truediv, # /
    ast.Pow: operator.pow  # ^
}

def calculate(expression):
    try:
        node = ast.parse(expression, mode='eval')

        def _eval(node):
            if isinstance(node, ast.Constant):
                return node.value
            elif isinstance(node, ast.BinOp):
                left = _eval(node.left)
                right = _eval(node.right)
                op = operators.get(type(node.op))
                if op is None:
                    raise TypeError(f"Неподдерживаемый оператор: {type(node.op)}")
                return op(left, right)
            elif isinstance(node, ast.UnaryOp): # Обработка унарных операторов (например, -5)
                operand = _eval(node.operand)
                if isinstance(node.op, ast.USub):
                    return -operand
                elif isinstance(node.op, ast.UAdd):
                    return +operand
                else:
                    raise TypeError(f"Неподдерживаемый унарный оператор: {type(node.op)}")
            else:
                raise TypeError(f"Неподдерживаемый тип узла: {type(node)}")

        return _eval(node.body)
    except (SyntaxError, NameError, TypeError, ZeroDivisionError) as e:
        print(f"Ошибка ввода: {e}")
        return None
    except Exception as e:
        print(f"Непредвиденная ошибка: {e}")
        return None

def calculator():
    while True:
        expression = input(": ")
        if expression.lower() == "exit":
            break
        result = calculate(expression)
        if result is not None:
            print("Результат:", result)

def shell_loop():
    current_lang = "en_US"
    lang_data = load_language(current_lang)
    config = load_config()

    command_completer = WordCompleter(commands, ignore_case=True)

    while True:
        current_path = os.getcwd()

        try:
            command_line = prompt(
                current_path + lang_data["prompt"],
                completer=command_completer,
                lexer=PygmentsLexer(BashLexer)  # подсветка синтаксиса
            )
        except (EOFError, KeyboardInterrupt):  # Обработка Ctrl+D и Ctrl+C
            print()  # Перевод строки после Ctrl+C или Ctrl+D
            break  # Выход из цикла

        if not command_line.strip():  # обработка пустой строки
            continue

        if command_line == "exit":
            break

        try:
            command_parts = shlex.split(command_line)
            command = command_parts[0]
            arguments = command_parts[1:]

            if command == "process_list":
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
                    print("Укажите PID процесса для завершения.")
            elif command == "calc":
                calculator()
            elif command == "lang":
                if arguments:
                    lang_code = arguments[0]  # получаем только "ru_RU" или "en_US"
                    lang_data = load_language(lang_code)  # load_language сам добавит languages/ и .json
                    current_lang = lang_code
                else:
                    print(f"Текущий язык: {current_lang}")
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
                    print("Укажите путь к скрипту.")
            elif command == "cd":
                if arguments:
                    try:
                        os.chdir(arguments[0])
                        print(f"Текущая директория изменена на: {os.getcwd()}")
                    except FileNotFoundError:
                        print(f"Директория '{arguments[0]}' не найдена.")
                    except NotADirectoryError:
                        print(f"'{arguments[0]}' не является директорией.")
                    except OSError as e: # Обработка других ошибок файловой системы
                        print(f"Ошибка при смене директории: {e}")
                else:
                    print(f"Текущая директория: {os.getcwd()}") # Вывод текущей директории, если аргумент не указан
            elif command == "clear" or command == "cls":
                clear_screen()
            elif command == "help":
                print(lang_data["available_commands"])
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
                        print(lang_data["command_not_found"])
                        continue  # переходим к следующей итерации цикла, не вызывая subprocess.run
                else:  # для linux/macOS
                    if not (is_executable(command) or is_executable(os.path.join(os.getcwd(), command))):
                        print(lang_data["command_not_found"])
                        continue  # переходим к следующей итерации цикла, не вызывая subprocess.run
                subprocess.run(command_parts, check=True, capture_output=True, text=True)

        except subprocess.CalledProcessError as e:
            print(f"Ошибка выполнения команды: {e}")
            if e.stderr:
                print(e.stderr)
        except OSError as e:
            print(f"Ошибка ОС: {e}")
        except ValueError as e:
            print(f"Ошибка ввода: {e}")
        except IndexError:
            print(lang_data["invalid_input"])

shell_loop()
