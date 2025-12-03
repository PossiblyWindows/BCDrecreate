from __future__ import annotations

import argparse
import asyncio
import base64
import hashlib
import json
import os
import platform
import queue
import random
import re
import sys
import threading
import time
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple
from urllib.parse import urljoin

import requests
from openai import AsyncOpenAI
from selenium.common.exceptions import (
    NoSuchWindowException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

try:
    import undetected_chromedriver as uc
except ImportError as exc:  # pragma: no cover - imported at runtime
    raise SystemExit("undetected_chromedriver is required: pip install undetected-chromedriver") from exc

# ----------------------- CONFIG -----------------------

KEYSYS_BASE = "https://keysys.djcookfan61.workers.dev"
KEYSYS_VALIDATE = KEYSYS_BASE + "/validate"

REG_PATH = r"Software\\Keysys\\UzdevumiBot"
TRIAL_MINUTES = 120

CONFIG_DIR = Path.home() / ".uzdevumi_bot"
CREDS_FILE = CONFIG_DIR / "credentials.json"
TARGET_FILE = CONFIG_DIR / "target_points.json"

DEFAULT_OPENAI_KEY = os.getenv(
    "UZDEVUMI_OPENAI_KEY",
    "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",
)

# filesystem defaults
SECURE_DIR_MODE = 0o700
SECURE_FILE_MODE = 0o600

# ----------------------- Platform helpers -----------------------


def is_windows() -> bool:
    return platform.system().lower() == "windows"


def get_hwid() -> str:
    base = ""
    if is_windows():
        try:
            import winreg

            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Cryptography",
                0,
                winreg.KEY_READ | 0x0100,
            )
            base, _ = winreg.QueryValueEx(key, "MachineGuid")
            winreg.CloseKey(key)
        except Exception:
            base = ""
    if not base:
        base = f"{platform.node()}|{platform.platform()}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest().upper()[:32]


def find_chrome_binary() -> Optional[str]:
    """Return a Chrome/Chromium binary path if present on the system."""

    env_override = os.getenv("UZDEVUMI_CHROME_BINARY")
    if env_override:
        candidate = Path(env_override)
        if candidate.exists():
            return str(candidate)

    candidates: List[Path] = []
    if is_windows():
        base_dirs = [
            Path(os.environ.get("PROGRAMFILES", "")),
            Path(os.environ.get("PROGRAMFILES(X86)", "")),
            Path(os.environ.get("LOCALAPPDATA", "")),
        ]
        for base in base_dirs:
            if not base:
                continue
            candidates.extend(
                [
                    base / "Google/Chrome/Application/chrome.exe",
                    base / "Google/Chrome Beta/Application/chrome.exe",
                    base / "Microsoft/Edge/Application/msedge.exe",
                ]
            )
    else:
        for binary in (
            "google-chrome",
            "google-chrome-stable",
            "chromium-browser",
            "chromium",
            "chrome",
        ):
            found = shutil.which(binary)
            if found:
                candidates.append(Path(found))

    for candidate in candidates:
        if candidate and candidate.exists():
            return str(candidate)

    try:
        fallback = uc.find_chrome_executable()  # type: ignore[attr-defined]
        return fallback
    except Exception:
        return None


def detect_chrome_version(binary_path: Optional[str]) -> Optional[int]:
    """Try to detect the Chrome major version to reduce driver guesswork."""

    target = binary_path or find_chrome_binary()
    if not target:
        return None

    try:
        result = subprocess.run(
            [target, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        output = (result.stdout or result.stderr or "").strip()
        match = re.search(r"(\d+)\.", output)
        if match:
            return int(match.group(1))
    except Exception:
        return None
    return None

# ----------------------- i18n -------------------------

I18N = {
    "lv": {
        # Titles / generic
        "title": "Uzdevumi.lv Bots",
        "status": "Statuss",
        "info": "Informācija",
        # Auth / site flow
        "login_start": "Notiek ieiešana…",
        "cookies_declined": "Sīkfaili noraidīti",
        "logged_in": "Ienākts",
        "find_subject": "Meklē priekšmetu…",
        "subject": "Priekšmets: {x}",
        "topic": "Tēma: {x}",
        "task": "Uzdevums: {x}",
        "text": "Teksts: {x}",
        "points": "Punkti: {x}",
        "img_task_skip": "Uzdevums ar bildēm vai vilkšanu – wtf",
        "open_gpt": "Atveru ChatGPT…",
        "sent_gpt": "Sūtīts GPT",
        "gpt_ans": "GPT atbilde: {x}",
        "marked": "Atzīmēti varianti: {x}",
        "submitted": "Iesniegts",
        "no_inputs": "Nav ievades lauku",
        "no_btn": "Nav pogas",
        "no_valid": "GPT neatgrieza derīgas vērtības",
        "done": "Automatizācija pabeigta",
        "debug_keep": "Pārlūki paliek atvērti",
        "cycle": "Cikls #{x}",
        "points_val": "Uzdevuma punktu vērtība (etikete): {x}",
        "top_start": "Sākuma Top punkti: {a}{b}",
        "top_target": "→ mērķis: {t}",
        "top_now": "Pašreizējie Top punkti: {x}",
        "top_reached": "Sasniegts mērķis: {a} ≥ {b}",
        "retry": "Mēģinājums {a}/{b}…",
        # UI
        "ui_username": "Personas kods",
        "ui_password": "Parole",
        "ui_debug": "Atstāt pārlūkus atvērtus",
        "ui_until": "--until-top (piem., 1600)",
        "ui_gain": "--gain (piem., 25)",
        "ui_start": "Sākt",
        "ui_close": "Aizvērt",
        "ui_error_need_creds": "Lūdzu ievadi gan personas kodu, gan paroli.",
        "ui_lang": "Valoda",
        "ui_license": "Licence",
        "ui_license_user": "Licences lietotājvārds",
        "ui_license_key": "Licences atslēga",
        "ui_license_user_ph": "Jūsu lietotājvārds",
        "ui_license_key_ph": "XXXXXX-XXXXXX-XXXXXX-XXXXXX-XXXXXX-XXXXXX",
        "ui_check_license": "Pārbaudīt licenci",
        "ui_end_trial": "Beigt izmēģinājumu un izmantot licenci",
        "ui_trial_left": "Atlicis izmēģinājuma laiks: {h}:{m:02d}:{s:02d}",
        "ui_trial_expired": "Izmēģinājums beidzies — nepieciešama licence.",
        "ui_licensed": "Licencēts: {u}",
        "ui_tier": "Aktīvais līmenis: {t}",
        "ui_tier_trial": "Izmēģinājums",
        "ui_popup_title": "Licence",
        "ui_popup_msg": "Ievadi lietotājvārdu un licences atslēgu:",
        "ui_popup_btn_ok": "Apstiprināt",
        "ui_popup_btn_cancel": "Atcelt",
        "ui_remember": "Saglabāt pierakstīšanās datus",
        # Prompt for ChatGPT
        "p1": "Tu esi asistents, kas risina uzdevumi.lv testus un sniedz tikai galīgo atbildi.",
        "p2": "Tev tiek dota #taskhtml > div teksta satura kopija. Analizē to un sagatavo risinājumu.",
        "p3": "Atbildes formāts:",
        "p4": "- Izvēles varianti: raksti tikai numurus vai burtus (1/A, 2/B, …), katru jaunā rindā.",
        "p5": "- Vairāki ievades lauki: katru rezultātu jaunā rindā tādā pašā secībā.",
        "p6": "- Dropdowniem: katrai rindai izvēlies vienu (burts A/B/C… vai teksts).",
        "p7": "- Bez paskaidrojumiem. Viena īsa atbilde ar tikai gala rezultātu.",
        "p8": "Uzdevuma teksts:",
        "p_radio_hdr": "Varianti (radio/checkbox):",
        "p_drop_hdr": "Varianti (dropdown):",
        # License logs
        "lic_start_trial": "Sākta izmēģinājuma versija (120 min).",
        "lic_trial_left": "Atlikušas izmēģinājuma minūtes: {m}",
        "lic_trial_expired": "Izmēģinājuma laiks beidzies. Nepieciešama licence.",
        "lic_valid": "Licence derīga. Lietotājs: {u}",
        "lic_revoked": "Licence atsaukta: {r}",
        "lic_invalid": "Nederīga licence.",
        "lic_hwid_mismatch": "HWID neatbilst šai ierīcei.",
        "lic_error": "Licence servera kļūda: {e}",
        "lic_burned": "Izmēģinājums ir beigts.",
        "cli_need_key": "Aktīvs licences režīms — norādi --license-user un --license.",
        "creds_saved": "Pierakstīšanās dati saglabāti.",
        "creds_loaded": "Ielādēti saglabātie pierakstīšanās dati.",
        "creds_cleared": "Saglabātie pierakstīšanās dati dzēsti.",
    },
    "en": {
        "title": "Uzdevumi.lv bot",
        "status": "Status",
        "info": "Info",
        "login_start": "Logging in…",
        "cookies_declined": "Cookies declined",
        "logged_in": "Logged in",
        "find_subject": "Picking a subject…",
        "subject": "Subject: {x}",
        "topic": "Topic: {x}",
        "task": "Task: {x}",
        "text": "Text: {x}",
        "points": "Points: {x}",
        "img_task_skip": "Image or drag task — skipping",
        "open_gpt": "Opening ChatGPT…",
        "sent_gpt": "Sent to GPT",
        "gpt_ans": "GPT answer: {x}",
        "marked": "Marked options: {x}",
        "submitted": "Submitted",
        "no_inputs": "No input fields",
        "no_btn": "No submit button",
        "no_valid": "GPT returned no valid values",
        "done": "Automation done",
        "debug_keep": "Keeping browsers open",
        "cycle": "Cycle #{x}",
        "points_val": "Task points (label): {x}",
        "top_start": "Starting Top points: {a}{b}",
        "top_target": "→ target: {t}",
        "top_now": "Current Top points: {x}",
        "top_reached": "Target reached: {a} ≥ {b}",
        "retry": "Retry {a}/{b}…",
        "ui_username": "User ID",
        "ui_password": "Password",
        "ui_debug": "Keep browsers open",
        "ui_until": "--until-top (e.g., 1600)",
        "ui_gain": "--gain (e.g., 25)",
        "ui_start": "Start",
        "ui_close": "Close",
        "ui_error_need_creds": "Please enter both user ID and password.",
        "ui_lang": "Language",
        "ui_license": "License",
        "ui_license_user": "License username",
        "ui_license_key": "License key",
        "ui_license_user_ph": "Your username",
        "ui_license_key_ph": "XXXXXX-XXXXXX-XXXXXX-XXXXXX-XXXXXX-XXXXXX",
        "ui_check_license": "Check license",
        "ui_end_trial": "End trial and use license",
        "ui_trial_left": "Trial time left: {h}:{m:02d}:{s:02d}",
        "ui_trial_expired": "Trial expired — license required.",
        "ui_licensed": "Licensed: {u}",
        "ui_tier": "Active tier: {t}",
        "ui_tier_trial": "Trial",
        "ui_popup_title": "License",
        "ui_popup_msg": "Enter username and license key:",
        "ui_popup_btn_ok": "Confirm",
        "ui_popup_btn_cancel": "Cancel",
        "ui_remember": "Remember credentials",
        "p1": "You are an assistant solving uzdevumi.lv tasks and you must output only the final answer.",
        "p2": "You are given the text content of #taskhtml > div. Analyze and produce the solution.",
        "p3": "Answer format:",
        "p4": "- Multiple choice: write only numbers or letters (1/A, 2/B, …), each on a new line.",
        "p5": "- Several input fields: write each final value on a new line in the same order.",
        "p6": "- Dropdowns: for each line choose one (letter A/B/C… or visible text).",
        "p7": "- No explanations. One short message with only the final result.",
        "p8": "Task text:",
        "p_radio_hdr": "Options (radio/checkbox):",
        "p_drop_hdr": "Options (dropdown):",
        "lic_start_trial": "Trial started (120 min).",
        "lic_trial_left": "Trial minutes left: {m}",
        "lic_trial_expired": "Trial expired. License required.",
        "lic_valid": "License valid. User: {u}",
        "lic_revoked": "License revoked: {r}",
        "lic_invalid": "Invalid license.",
        "lic_hwid_mismatch": "HWID mismatch for this device.",
        "lic_error": "License server error: {e}",
        "lic_burned": "Trial has ended.",
        "cli_need_key": "License mode active — provide --license-user and --license.",
        "creds_saved": "Credentials saved.",
        "creds_loaded": "Loaded saved credentials.",
        "creds_cleared": "Saved credentials cleared.",
    },
    "ru": {
        "title": "Uzdevumi.lv bot",
        "status": "Статус",
        "info": "Информация",
        "login_start": "Вход…",
        "cookies_declined": "Куки отклонены",
        "logged_in": "Вошли",
        "find_subject": "Выбор предмета…",
        "subject": "Предмет: {x}",
        "topic": "Тема: {x}",
        "task": "Задание: {x}",
        "text": "Текст: {x}",
        "points": "Баллы: {x}",
        "img_task_skip": "Задание с картинками или перетаскиванием — херню эту делать не буду.",
        "open_gpt": "Открываю ChatGPT…",
        "sent_gpt": "Отправлено в GPT",
        "gpt_ans": "Ответ GPT: {x}",
        "marked": "Отмеченные варианты: {x}",
        "submitted": "Отправлено",
        "no_inputs": "Нет полей ввода",
        "no_btn": "Нет кнопки отправки",
        "no_valid": "GPT не вернул корректных значений",
        "done": "Готово",
        "debug_keep": "браузеры остаются открыты",
        "cycle": "Цикл #{x}",
        "points_val": "Баллы задания (этикетка): {x}",
        "top_start": "Стартовые Top баллы: {a}{b}",
        "top_target": "→ цель: {t}",
        "top_now": "Текущие Top баллы: {x}",
        "top_reached": "Цель достигнута: {a} ≥ {b}",
        "retry": "Повтор {a}/{b}…",
        "ui_username": "Идентификатор",
        "ui_password": "Пароль",
        "ui_debug": "Держать браузеры открытыми",
        "ui_until": "--until-top (напр., 1600)",
        "ui_gain": "--gain (напр., 25)",
        "ui_start": "Старт",
        "ui_close": "Закрыть",
        "ui_error_need_creds": "Введите идентификатор и пароль.",
        "ui_lang": "Язык",
        "ui_license": "Лицензия",
        "ui_license_user": "Имя пользователя лицензии",
        "ui_license_key": "Ключ лицензии",
        "ui_license_user_ph": "Ваш логин",
        "ui_license_key_ph": "XXXXXX-XXXXXX-XXXXXX-XXXXXX-XXXXXX-XXXXXX",
        "ui_check_license": "Проверить лицензию",
        "ui_end_trial": "Завершить пробный период и использовать лицензию",
        "ui_trial_left": "Осталось времени пробного периода: {h}:{m:02d}:{s:02d}",
        "ui_trial_expired": "Пробный период истёк — требуется лицензия.",
        "ui_licensed": "Лицензировано: {u}",
        "ui_tier": "Активный тариф: {t}",
        "ui_tier_trial": "Пробный период",
        "ui_popup_title": "Лицензия",
        "ui_popup_msg": "Введите имя пользователя и ключ лицензии:",
        "ui_popup_btn_ok": "Подтвердить",
        "ui_popup_btn_cancel": "Отмена",
        "ui_remember": "Запомнить данные для входа",
        "p1": "Вы — ассистент, решающий задания uzdevumi.lv, выводите только окончательный ответ.",
        "p2": "Дан текст содержимого #taskhtml > div. Проанализируйте и дайте решение.",
        "p3": "Формат ответа:",
        "p4": "- Выбор: только номера или буквы (1/A, 2/B, …), по одной строке.",
        "p5": "- Несколько полей ввода: каждое значение с новой строки в том же порядке.",
        "p6": "- Выпадающие списки: для каждой строки выберите одно (буква A/B/C… либо видимый текст).",
        "p7": "- Без пояснений. Одно короткое сообщение только с итогом.",
        "p8": "Текст задания:",
        "p_radio_hdr": "Варианты (radio/checkbox):",
        "p_drop_hdr": "Варианты (dropdown):",
        "lic_start_trial": "Пробный период запущен (120 мин).",
        "lic_trial_left": "Осталось минут пробного периода: {m}",
        "lic_trial_expired": "Пробный период истёк. Нужна лицензия.",
        "lic_valid": "Лицензия валидна. Пользователь: {u}",
        "lic_revoked": "Лицензия отозвана: {r}",
        "lic_invalid": "Неверная лицензия.",
        "lic_hwid_mismatch": "Несовпадение HWID.",
        "lic_error": "Ошибка сервера лицензий: {e}",
        "lic_burned": "Пробный период завершён.",
        "cli_need_key": "Активен режим лицензии — укажите --license-user и --license.",
        "creds_saved": "Данные входа сохранены.",
        "creds_loaded": "Сохранённые данные входа загружены.",
        "creds_cleared": "Сохранённые данные входа удалены.",
    },
}


I18N_URL = {
    "lv": "https://www.google.com/intl/lv/chrome/",
    "en": "https://www.google.com/chrome/",
    "ru": "https://www.google.com/intl/ru/chrome/",
}


def T(lang: str, key: str, **kwargs) -> str:
    pack = I18N.get(lang, I18N["lv"])
    s = pack.get(key, key)
    return s.format(**kwargs) if kwargs else s


# ----------------------- Credential helpers ------------


def _harden_path(path: Path, is_file: bool = False) -> None:
    """Best-effort attempt to restrict permissions for secrets."""

    try:
        if is_file:
            os.chmod(path, SECURE_FILE_MODE)
        else:
            os.chmod(path, SECURE_DIR_MODE)
    except Exception:
        # Non-fatal: we avoid crashing UI if OS blocks chmod (e.g. Windows)
        pass


def _ensure_config_dir() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True, mode=SECURE_DIR_MODE)
    _harden_path(CONFIG_DIR)


def load_saved_credentials() -> Tuple[Optional[str], Optional[str]]:
    try:
        _ensure_config_dir()
        if not CREDS_FILE.exists():
            return None, None
        with CREDS_FILE.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        user = data.get("user")
        pw_blob = data.get("password")
        if not user or not pw_blob:
            return None, None
        password = base64.b64decode(pw_blob.encode("utf-8")).decode("utf-8")
        _harden_path(CREDS_FILE, is_file=True)
        return user, password
    except Exception:
        return None, None


def save_credentials(user: str, password: str) -> None:
    if not user or not password:
        return
    try:
        _ensure_config_dir()
        blob = base64.b64encode(password.encode("utf-8")).decode("utf-8")
        with CREDS_FILE.open("w", encoding="utf-8") as fh:
            json.dump({"user": user, "password": blob}, fh)
        _harden_path(CREDS_FILE, is_file=True)
    except Exception:
        pass


def clear_saved_credentials() -> None:
    try:
        if CREDS_FILE.exists():
            CREDS_FILE.unlink()
    except Exception:
        pass


def save_target_preferences(until_top: Optional[int], gain_points: Optional[float]) -> None:
    try:
        _ensure_config_dir()
        with TARGET_FILE.open("w", encoding="utf-8") as fh:
            json.dump({"until_top": until_top, "gain_points": gain_points}, fh)
        _harden_path(TARGET_FILE, is_file=True)
    except Exception:
        pass


def load_target_preferences() -> Tuple[Optional[int], Optional[float]]:
    try:
        if not TARGET_FILE.exists():
            return None, None
        with TARGET_FILE.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data.get("until_top"), data.get("gain_points")
    except Exception:
        return None, None


# ----------------------- Data classes -------------------


@dataclass
class TaskOption:
    index: int
    text: str
    option_type: str
    input_element: object
    label_element: object


@dataclass
class DragOption:
    text: str
    element: object


@dataclass
class DragTarget:
    index: int
    element: object
    input_element: Optional[object]


@dataclass
class TaskData:
    text: str
    options: List[TaskOption]
    points_label: str
    dropdown_texts: List[List[str]]
    dropdown_ids: List[Optional[str]]
    drag_targets: List[DragTarget]
    drag_options: List[DragOption]


Logger = Optional[Callable[[str], None]]


# ----------------------- Logging & waits -----------------

RESTART_KEYWORDS = (
    "chrome not reachable",
    "no such window",
    "web view not found",
    "disconnected",
    "stale element",
    "tab crashed",
    "session deleted",
    "target window already closed",
    "devtoolsactiveport file doesn't exist",
    "cannot determine loading status",
    "failed to decode response",
)


chrome_path = r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"


def ensure_chrome_available(lang: str) -> None:
    """Abort early with a localized message if Chrome is missing on Windows."""
    if platform.system().lower() == "windows" and not os.path.exists(chrome_path):
        sys.exit(
            f"❗ { {'lv':'Nepieciešams Google Chrome! Lejupielādē no:','en':'Google Chrome is required! Download from:','ru':'Требуется Google Chrome! Скачайте по ссылке:'}[lang] } {I18N_URL[lang]}"
        )


def log_message(message: str, logger: Logger = None) -> None:
    print(message)
    if logger:
        try:
            logger(message)
        except Exception:
            pass


def w(driver, css: str, timeout: int = 7, cond: str = "present"):
    try:
        cond_map = {
            "present": EC.presence_of_element_located,
            "visible": EC.visibility_of_element_located,
            "clickable": EC.element_to_be_clickable,
        }
        return WebDriverWait(driver, timeout).until(cond_map[cond]((By.CSS_SELECTOR, css)))
    except TimeoutException:
        return None


def w_all(driver, css: str, timeout: int = 7, visible_only: bool = False):
    try:
        elements = WebDriverWait(driver, timeout).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, css))
        )
        if visible_only:
            elements = [e for e in elements if e.is_displayed()]
        return elements
    except TimeoutException:
        return []


def js_click(driver, element) -> None:
    if element is None:
        return
    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
        element.click()
    except Exception:
        try:
            driver.execute_script("arguments[0].click();", element)
        except Exception:
            pass


def clear_cookies(driver) -> None:
    try:
        driver.delete_all_cookies()
    except Exception:
        pass


def build_fast_driver(incognito: bool = True, new_window: bool = False, block_images: bool = True):
    options = uc.ChromeOptions()
    if incognito:
        options.add_argument("--incognito")
    if new_window:
        options.add_argument("--new-window")
    options.page_load_strategy = "eager"
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-features=PrivacySandboxAdsAPIs,HeavyAdIntervention,Translate")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--no-first-run")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-client-side-phishing-detection")
    options.add_argument("--remote-allow-origins=*")
    binary = find_chrome_binary()
    if binary:
        options.binary_location = binary
    if block_images:
        prefs = {"profile.managed_default_content_settings.images": 2}
        options.add_experimental_option("prefs", prefs)

    version_main = detect_chrome_version(binary)
    driver = None
    last_exc: Optional[Exception] = None
    for attempt in range(2):
        try:
            if attempt == 0 and version_main:
                driver = uc.Chrome(options=options, version_main=version_main)
            else:
                driver = uc.Chrome(options=options)
            break
        except Exception as exc:  # pragma: no cover - runtime guard
            last_exc = exc
            version_main = None

    if driver is None:
        if last_exc:
            raise last_exc
        raise RuntimeError("Unable to start Chrome driver")

    try:
        driver.set_page_load_timeout(30)
        driver.set_window_size(1280, 900)
    except Exception:
        pass
    return driver


def with_resilience(
    step_fn: Callable[[], None],
    recreate_fn: Callable[[], None],
    lang: str,
    logger: Logger = None,
    retries: int = 2,
):
    attempt = 0
    while True:
        try:
            return step_fn()
        except Exception as e:  # pragma: no cover - runtime safety guard
            attempt += 1
            msg = str(e).lower()
            restart_needed = isinstance(
                e,
                (NoSuchWindowException, WebDriverException, StaleElementReferenceException),
            )
            if not restart_needed:
                restart_needed = any(keyword in msg for keyword in RESTART_KEYWORDS)
            if restart_needed and attempt <= retries:
                log_message(T(lang, "retry", a=attempt, b=retries), logger)
                try:
                    recreate_fn()
                except Exception:
                    pass
                time.sleep(0.5)
                continue
            raise


# ----------------------- Points helpers ------------------

def parse_points_label(label: str) -> float:
    if not label:
        return 0.0
    m = re.search(r"(\d+[.,]?\d*)", label)
    if not m:
        return 0.0
    return float(m.group(1).replace(",", "."))


def read_top_points(driver) -> Optional[int]:
    try:
        el = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a.top-points"))
        )
        txt = el.text.strip()
        m = re.search(r"\d+", txt.replace(" ", ""))
        if m:
            return int(m.group(0))
    except Exception:
        return None
    return None


# ----------------------- Cosmetic: hide media ------------

HIDE_MEDIA_CSS = """
* { image-rendering: auto !important; }
img, .gxs-resource-image, .gxst-resource-image,
[style*="background-image"], .taskhtmlwrapper .image, .taskhtmlwrapper figure {
  display: none !important;
}
"""


def apply_hide_media_css(driver) -> None:
    try:
        driver.execute_script(
            """
            (function(css){
                const id='__hide_media_style__';
                if(document.getElementById(id)) return;
                const s=document.createElement('style'); s.id=id; s.type='text/css'; s.appendChild(document.createTextNode(css));
                document.head.appendChild(s);
            })(arguments[0]);
        """,
            HIDE_MEDIA_CSS,
        )
    except Exception:
        pass


# ----------------------- Registry / HWID -----------------


def find_chrome_binary() -> Optional[str]:
    """Return a Chrome/Chromium binary path if present on the system."""

    env_override = os.getenv("UZDEVUMI_CHROME_BINARY")
    if env_override:
        candidate = Path(env_override)
        if candidate.exists():
            return str(candidate)

    candidates: List[Path] = []
    if is_windows():
        base_dirs = [
            Path(os.environ.get("PROGRAMFILES", "")),
            Path(os.environ.get("PROGRAMFILES(X86)", "")),
            Path(os.environ.get("LOCALAPPDATA", "")),
        ]
        for base in base_dirs:
            if not base:
                continue
            candidates.extend(
                [
                    base / "Google/Chrome/Application/chrome.exe",
                    base / "Google/Chrome Beta/Application/chrome.exe",
                    base / "Microsoft/Edge/Application/msedge.exe",
                ]
            )
    else:
        for binary in (
            "google-chrome",
            "google-chrome-stable",
            "chromium-browser",
            "chromium",
            "chrome",
        ):
            found = shutil.which(binary)
            if found:
                candidates.append(Path(found))

    for candidate in candidates:
        if candidate and candidate.exists():
            return str(candidate)

    try:
        fallback = uc.find_chrome_executable()  # type: ignore[attr-defined]
        return fallback
    except Exception:
        return None


def detect_chrome_version(binary_path: Optional[str]) -> Optional[int]:
    """Try to detect the Chrome major version to reduce driver guesswork."""

    target = binary_path or find_chrome_binary()
    if not target:
        return None

    try:
        result = subprocess.run(
            [target, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        output = (result.stdout or result.stderr or "").strip()
        match = re.search(r"(\d+)\.", output)
        if match:
            return int(match.group(1))
    except Exception:
        return None
    return None


def reg_read(name: str) -> Optional[str]:
    if not is_windows():
        return None
    try:
        import winreg

        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_READ)
        val, _ = winreg.QueryValueEx(key, name)
        winreg.CloseKey(key)
        return str(val)
    except Exception:
        return None


def reg_write(name: str, value: str) -> None:
    if not is_windows():
        return
    try:
        import winreg

        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_PATH)
        winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)
        winreg.CloseKey(key)
    except Exception:
        pass


def reg_delete(name: str) -> None:
    if not is_windows():
        return
    try:
        import winreg

        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, name)
        winreg.CloseKey(key)
    except Exception:
        pass


# ----------------------- Licensing -----------------------


class LicenseManager:
    def __init__(self, lang: str, logger: Logger = None):
        self.lang = lang
        self.logger = logger
        self._tier_cache: Dict[str, Optional[str]] = {"user": None, "key": None, "value": None, "ts": 0.0}

    def _trial_seconds_left(self) -> int:
        if not is_windows():
            return 0
        if reg_read("TrialBurned") == "1":
            return 0
        start_epoch = reg_read("TrialStartEpoch")
        if not start_epoch:
            reg_write("TrialStartEpoch", str(time.time()))
            log_message(T(self.lang, "lic_start_trial"), self.logger)
            return TRIAL_MINUTES * 60
        try:
            used = time.time() - float(start_epoch)
        except Exception:
            used = TRIAL_MINUTES * 60 + 1
        left = int(max(0, TRIAL_MINUTES * 60 - used))
        if left > 0:
            log_message(T(self.lang, "lic_trial_left", m=int(left / 60)), self.logger)
        else:
            log_message(T(self.lang, "lic_trial_expired"), self.logger)
        return left

    def burn_trial(self) -> None:
        if not is_windows():
            return
        reg_write("TrialBurned", "1")
        reg_write("TrialStartEpoch", "0")
        log_message(T(self.lang, "lic_burned"), self.logger)

    def _stored(self) -> Tuple[str, str, str]:
        return (
            reg_read("LicenseUser") or "",
            reg_read("LicenseKey") or "",
            reg_read("LicenseHWID") or "",
        )

    def _get_tier(self, ks_user: str, ks_key: str) -> Optional[str]:
        if not ks_user and not ks_key:
            return None
        now = time.time()
        if (
            self._tier_cache["value"]
            and self._tier_cache["user"] == ks_user
            and self._tier_cache["key"] == ks_key
            and now - (self._tier_cache["ts"] or 0) < 300
        ):
            return self._tier_cache["value"]

        tier = None
        try:
            r = requests.get(
                KEYSYS_BASE + "/tier",
                params={"user": ks_user, "key": ks_key},
                timeout=6,
            )
            js = r.json()
            if js.get("success"):
                tier = js.get("tier")
        except Exception:
            tier = None

        self._tier_cache = {
            "user": ks_user,
            "key": ks_key,
            "value": tier,
            "ts": time.time(),
        }
        return tier

    def validate_and_store(self, ks_user: str, ks_key: str) -> Tuple[bool, str]:
        """Validate via Keysys POST /validate (bind HWID on first success). Requires user+key."""
        if not ks_user or not ks_key:
            msg = T(self.lang, "lic_invalid")
            log_message(msg, self.logger)
            return False, msg
        hwid = reg_read("LicenseHWID") or get_hwid()
        try:
            res = requests.post(
                KEYSYS_VALIDATE,
                json={"user": ks_user, "key": ks_key, "hwid": hwid},
                timeout=12,
            )
            js = res.json()
            if js.get("valid"):
                reg_write("LicenseUser", ks_user)
                reg_write("LicenseKey", ks_key)
                reg_write("LicenseHWID", js.get("hwid") or hwid)
                self.burn_trial()
                log_message(T(self.lang, "lic_valid", u=js.get("user", ks_user)), self.logger)
                return True, js.get("user", ks_user)
            if js.get("revoked"):
                msg = T(self.lang, "lic_revoked", r=js.get("reason", ""))
                log_message(msg, self.logger)
                return False, msg
            message = (js.get("message") or "").lower()
            if "hwid mismatch" in message:
                msg = T(self.lang, "lic_hwid_mismatch")
                log_message(msg, self.logger)
                return False, msg
            if "not bound" in message:
                res2 = requests.post(
                    KEYSYS_VALIDATE,
                    json={"user": ks_user, "key": ks_key, "hwid": hwid},
                    timeout=12,
                )
                js2 = res2.json()
                if js2.get("valid"):
                    reg_write("LicenseUser", ks_user)
                    reg_write("LicenseKey", ks_key)
                    reg_write("LicenseHWID", js2.get("hwid") or hwid)
                    self.burn_trial()
                    log_message(T(self.lang, "lic_valid", u=js2.get("user", ks_user)), self.logger)
                    return True, js2.get("user", ks_user)
            msg = T(self.lang, "lic_invalid")
            log_message(msg, self.logger)
            return False, msg
        except Exception as e:  # pragma: no cover - network safety
            msg = T(self.lang, "lic_error", e=str(e))
            log_message(msg, self.logger)
            return False, msg

    def status(self) -> Dict[str, Optional[str]]:
        ks_user, ks_key, ks_hwid = self._stored()
        if ks_user and ks_key:
            try:
                q = {"user": ks_user, "key": ks_key}
                q["hwid"] = ks_hwid or get_hwid()
                r = requests.get(KEYSYS_VALIDATE, params=q, timeout=8)
                js = r.json()
                if js.get("valid"):
                    if js.get("hwid"):
                        reg_write("LicenseHWID", js["hwid"])
                    tier = self._get_tier(js.get("user") or ks_user, ks_key) or "Basic"
                    return {
                        "state": "licensed",
                        "user": js.get("user") or ks_user,
                        "left_seconds": None,
                        "tier": tier,
                    }
                if js.get("revoked"):
                    reg_delete("LicenseUser")
                    reg_delete("LicenseKey")
                    reg_delete("LicenseHWID")
                else:
                    if (js.get("message") or "").lower().find("mismatch") >= 0:
                        pass
                    reg_delete("LicenseUser")
                    reg_delete("LicenseKey")
            except Exception:
                return {"state": "licensed", "user": ks_user or "unknown", "left_seconds": None}

        left = self._trial_seconds_left()
        if left > 0:
            return {"state": "trial", "user": None, "left_seconds": left}
        return {"state": "expired", "user": None, "left_seconds": 0}

    def ensure_for_cli(
        self,
        use_keysys_flag: bool,
        license_user_arg: Optional[str],
        license_key_arg: Optional[str],
    ) -> None:
        if use_keysys_flag:
            self.burn_trial()
            if not license_user_arg or not license_key_arg:
                raise RuntimeError(T(self.lang, "cli_need_key"))
            ok, msg = self.validate_and_store(license_user_arg, license_key_arg)
            if not ok:
                raise RuntimeError(msg)
            return

        st = self.status()
        if st["state"] == "licensed":
            return
        if st["state"] == "trial":
            return
        if license_user_arg and license_key_arg:
            ok, msg = self.validate_and_store(license_user_arg, license_key_arg)
            if not ok:
                raise RuntimeError(msg)
            return
        raise RuntimeError(T(self.lang, "lic_trial_expired"))


# ----------------------- Site flow ----------------------

EXCLUDE_SUBJECTS = {
    "Vizuālā māksla (Skola2030), 5. klase",
    "Vizuālā māksla, 5. klase",
    "Mūzika (Skola2030), 5. klase",
    "Starpbrīdis, Svētku testi",
    "Starpbrīdis, Izglītojošie testi",
    "Starpbrīdis, Darba lapas",
    "Starpbrīdis, Ralfs mācās ar Uzdevumi.lv",
    "Uzdevumi.lv konkursi, 2025. gads (Matemātika)",
    "Uzdevumi.lv konkursi, 2024. gads (Matemātika)",
    "Uzdevumi.lv konkursi, 2023. gads (Matemātika)",
    "Uzdevumi.lv konkursi, 2023. gads (Ķīmija)",
}


def decline_cookies(driver, lang: str, logger: Logger = None):
    try:
        btn = WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#CybotCookiebotDialogBodyButtonDecline"))
        )
        js_click(driver, btn)
        log_message(T(lang, "cookies_declined"), logger)
    except TimeoutException:
        pass
    apply_hide_media_css(driver)


def login(driver, user: str, password: str, lang: str, logger: Logger = None):
    ensure_chrome_available(lang)
    log_message(T(lang, "login_start"), logger)
    driver.get(
        "https://www.uzdevumi.lv/Sso/AuthRedirect/eklase?authAction=alor&rememberMe=False&isPopup=True"
    )
    decline_cookies(driver, lang, logger)
    u = w(driver, "#UserName", 10, "visible")
    p = w(driver, "div.InputForm_Row:nth-child(2) > input:nth-child(1)", 10, "visible")
    if not u or not p:
        raise RuntimeError("Login fields not found")
    u.send_keys(user)
    p.send_keys(password)
    js_click(driver, w(driver, "#cmdLogonUser", 8, "clickable"))
    try:
        prof = WebDriverWait(driver, 6).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".UserProfileSelector_Button"))
        )
        js_click(driver, prof)
    except TimeoutException:
        pass
    decline_cookies(driver, lang, logger)
    log_message(T(lang, "logged_in"), logger)


def select_task(driver, lang: str, logger: Logger = None) -> bool:
    def open_subjects_page():
        driver.get("https://www.uzdevumi.lv/p")
        apply_hide_media_css(driver)
        decline_cookies(driver, lang, logger)

    def pick_subject() -> Optional[Tuple[object, str]]:
        subjects_list = w(driver, "ul.list-unstyled.thumbnails", 8)
        if not subjects_list:
            return None
        candidates = subjects_list.find_elements(By.CSS_SELECTOR, "li.thumb.wide a[href]")
        subjects = []
        for anchor in candidates:
            if not anchor.is_displayed():
                continue
            title = anchor.text.replace("\n", " ").strip()
            if not title:
                continue
            tnorm = title.lower()
            if title in EXCLUDE_SUBJECTS or "starpbrīdis" in tnorm or "konkurs" in tnorm:
                continue
            subjects.append((anchor, title))
        if not subjects:
            return None
        return random.choice(subjects)

    def pick_topic() -> Optional[object]:
        topics = [e for e in w_all(driver, "ol.list-unstyled a[href]", 6) if e.is_displayed()]
        if not topics:
            return None
        return random.choice(topics)

    def pick_task_link() -> Optional[object]:
        container = None
        for selector in (
            "section.block:nth-child(2) > div:nth-child(2)",
            "section.block:nth-child(1) > div:nth-child(2)",
        ):
            container = w(driver, selector, 6, "visible")
            if container:
                break
        if not container:
            return None
        tasks = [e for e in container.find_elements(By.CSS_SELECTOR, "a[href]") if e.is_displayed()]
        if not tasks:
            return None
        return random.choice(tasks)

    log_message(T(lang, "find_subject"), logger)

    for attempt in range(3):
        try:
            open_subjects_page()
            pair = pick_subject()
            if not pair:
                continue
            anchor, title = pair
            log_message(T(lang, "subject", x=title), logger)
            js_click(driver, anchor)
            apply_hide_media_css(driver)
            decline_cookies(driver, lang, logger)
            try:
                js_click(driver, driver.find_element(By.CSS_SELECTOR, ".ui-button"))
            except Exception:
                pass

            topic_el = pick_topic()
            if not topic_el:
                driver.refresh()
                apply_hide_media_css(driver)
                decline_cookies(driver, lang, logger)
                topic_el = pick_topic()
            if not topic_el:
                continue

            log_message(T(lang, "topic", x=topic_el.text.strip()), logger)
            js_click(driver, topic_el)
            apply_hide_media_css(driver)
            decline_cookies(driver, lang, logger)

            task_el = pick_task_link()
            if not task_el:
                driver.refresh()
                apply_hide_media_css(driver)
                decline_cookies(driver, lang, logger)
                task_el = pick_task_link()
            if not task_el:
                open_subjects_page()
                continue

            log_message(T(lang, "task", x=task_el.text.strip()), logger)
            js_click(driver, task_el)
            apply_hide_media_css(driver)
            decline_cookies(driver, lang, logger)
            return True
        except Exception:
            try:
                driver.refresh()
                apply_hide_media_css(driver)
            except Exception:
                pass
    open_subjects_page()
    return False


def transcribe_audio_via_worker(audio_url: str, lang: str, logger: Logger = None) -> Optional[str]:
    payload = {"audio_url": audio_url, "language": lang}
    try:
        response = requests.post(f"{KEYSYS_BASE}/transcribe", json=payload, timeout=25)
    except Exception as exc:  # pragma: no cover - network
        log_message(f"⚠️ Audio transcription request failed: {exc}", logger)
        return None

    try:
        data = response.json()
    except Exception:
        log_message(
            f"⚠️ Audio transcription failed with status {response.status_code}", logger
        )
        return None

    if response.ok and data.get("success") and data.get("text"):
        return str(data.get("text"))

    log_message(f"⚠️ Audio transcription failed: {data.get('message')}", logger)
    return None


def fetch_task(driver, lang: str, logger: Logger = None) -> Optional[TaskData]:
    wrapper = w(driver, "#taskhtml > div", 10, "visible")
    if wrapper is None:
        return None
    text_content = wrapper.text.strip()
    summary = (
        text_content.replace("\n", " ")[:120] + "…"
        if len(text_content) > 120
        else text_content.replace("\n", " ")
    )
    points_label = "0 p."
    pts_el = driver.find_elements(By.CSS_SELECTOR, ".obj-points")
    if pts_el:
        points_label = pts_el[0].text.strip()
    drag_fields = wrapper.find_elements(By.CSS_SELECTOR, ".gxs-dnd-field")
    drag_options_raw = wrapper.find_elements(By.CSS_SELECTOR, ".gxs-dnd-option")
    drag_targets: List[DragTarget] = []
    drag_options: List[DragOption] = []

    for idx, field in enumerate(drag_fields, start=1):
        hidden = None
        try:
            hid_id = field.get_attribute("id") or ""
            if hid_id:
                hidden = wrapper.find_element(By.CSS_SELECTOR, f"input[id='dnd{hid_id}']")
        except Exception:
            hidden = None
        drag_targets.append(DragTarget(index=idx, element=field, input_element=hidden))

    for opt in drag_options_raw:
        txt = (opt.text or "").strip()
        if not txt:
            txt = (opt.get_attribute("innerText") or "").strip()
        drag_options.append(DragOption(text=txt, element=opt))

    has_drag = bool(drag_targets and drag_options)

    media = wrapper.find_elements(
        By.CSS_SELECTOR,
        "img,[style*='background-image'],.gxs-resource-image,.gxst-resource-image",
    )
    if media and not has_drag:
        log_message(T(lang, "img_task_skip"), logger)
        return "SKIP"

    audio_sources = wrapper.find_elements(By.CSS_SELECTOR, "audio, audio source")
    audio_url = None
    for aud in audio_sources:
        src = (aud.get_attribute("src") or "").strip()
        if src:
            audio_url = src
            break
    if drag_options:
        option_texts = [o.text for o in drag_options if o.text]
        if option_texts:
            text_content = f"{text_content}\nAtbilžu varianti: " + ", ".join(option_texts)
    if audio_url:
        full_audio_url = urljoin(driver.current_url, audio_url)
        log_message("🎵 Audio task detected – transcribing…", logger)
        transcription = transcribe_audio_via_worker(full_audio_url, lang, logger)
        if transcription:
            log_message(f"🎵 Audio text: {transcription}", logger)
            text_content = f"{text_content}\n\nAudio transcription: {transcription}"
        else:
            log_message("⚠️ Audio transcription failed", logger)
    options: List[TaskOption] = []
    for idx, item in enumerate(
        wrapper.find_elements(By.CSS_SELECTOR, "ul.gxs-answer-select > li"), start=1
    ):
        try:
            input_el = item.find_element(By.CSS_SELECTOR, "input")
        except Exception:
            continue
        try:
            label_el = item.find_element(By.CSS_SELECTOR, "label")
            option_text = label_el.text.strip()
        except Exception:
            label_el, option_text = None, item.text.strip()
        input_type = (input_el.get_attribute("type") or "").lower()
        options.append(TaskOption(idx, option_text, input_type, input_el, label_el))
    dropdown_texts: List[List[str]] = []
    dropdown_ids: List[Optional[str]] = []
    selects = wrapper.find_elements(By.CSS_SELECTOR, "select.gxs-answer-dropdown")
    for sel in selects:
        try:
            sid = sel.get_attribute("id") or None
            select_obj = Select(sel)
            texts = []
            for opt in select_obj.options:
                txt = (opt.text or "").strip()
                if txt == "":
                    continue
                texts.append(txt)
            dropdown_texts.append(texts)
            dropdown_ids.append(sid)
        except Exception:
            continue
    log_message(T(lang, "text", x=summary), logger)
    log_message(T(lang, "points", x=points_label), logger)
    return TaskData(
        text=text_content,
        options=options,
        points_label=points_label,
        dropdown_texts=dropdown_texts,
        dropdown_ids=dropdown_ids,
        drag_targets=drag_targets,
        drag_options=drag_options,
    )


# ----------------------- GPT session --------------------

def fetch_chatgpt5free_token(max_wait: float = 8.0) -> Optional[str]:
    """
    Pull a fresh API key from the Keysys helper endpoint.

    The endpoint returns JSON shaped as::

        {"success": true, "results": [{"key": "sk-proj-…"}]}

    Only the ``key`` field is returned. ``max_wait`` caps the HTTP timeout
    so the caller can fail over quickly if the service is down.
    """

    try:
        res = requests.get(
            f"{KEYSYS_BASE}/gettoken", timeout=max_wait
        )
        js = res.json()
        if not js or not js.get("success"):
            return None
        results = js.get("results") or []
        for item in results:
            key = (item.get("key") or "").strip()
            if key:
                return key
            full = item.get("full") or ""
            match = re.search(r"API_KEY=['\"]([^'\"]+)", full)
            if match and match.group(1):
                return match.group(1).strip()
    except Exception:
        return None
    return None


class ChatGPTSession:
    """Async OpenAI wrapper with background loop and graceful teardown."""

    def __init__(self, lang: str, logger: Logger = None):
        self.lang = lang
        self.logger = logger
        self._client_lock = threading.Lock()
        self.model = "gpt-5.1-latest-chat"
        self.api_key = os.getenv("UZDEVUMI_OPENAI_KEY") or DEFAULT_OPENAI_KEY
        self.client = AsyncOpenAI(api_key=self.api_key, timeout=15)
        self._loop = asyncio.new_event_loop()
        self._loop_thread = threading.Thread(
            target=self._run_loop, name="gpt-loop", daemon=True
        )
        self._loop_thread.start()

        if not os.getenv("UZDEVUMI_OPENAI_KEY"):
            threading.Thread(
                target=self._try_upgrade_token,
                name="gpt-token-upgrade",
                daemon=True,
            ).start()

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    async def _ask_task_async(self, task: TaskData) -> str:
        prompt = build_prompt(task, self.lang)
        log_message(T(self.lang, "open_gpt"), self.logger)
        resp = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": T(self.lang, "p1")},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=1024,
        )
        answer = resp.choices[0].message.content.strip()
        log_message(T(self.lang, "gpt_ans", x=answer), self.logger)
        return answer

    def ask_task(self, task: TaskData) -> str:
        future = asyncio.run_coroutine_threadsafe(
            self._ask_task_async(task), self._loop
        )
        return future.result(timeout=30)

    async def _close_async(self) -> None:
        try:
            await self.client.close()
        except Exception:
            pass

    def close(self) -> None:
        try:
            asyncio.run_coroutine_threadsafe(self._close_async(), self._loop).result(10)
        except Exception:
            pass
        self._loop.call_soon_threadsafe(self._loop.stop)
        if self._loop_thread.is_alive():
            self._loop_thread.join(timeout=5)

    def _try_upgrade_token(self) -> None:
        token = fetch_chatgpt5free_token(max_wait=10.0)
        if not token:
            return
        if token.startswith("Bearer "):
            token = token[len("Bearer ") :]
        self._swap_client(token)
        log_message("↺ GPT token refreshed", self.logger)

    def _swap_client(self, new_key: str) -> None:
        with self._client_lock:
            if not new_key or new_key == self.api_key:
                return
            old_client = self.client
            self.api_key = new_key
            self.client = AsyncOpenAI(api_key=self.api_key, timeout=15)
        try:
            asyncio.run_coroutine_threadsafe(old_client.close(), self._loop).result(8)
        except Exception:
            pass


# ----------------------- Prompt / parser -----------------


def build_prompt(task: TaskData, lang: str) -> str:
    parts = [
        T(lang, "p1"),
        T(lang, "p2"),
        T(lang, "p3"),
        T(lang, "p4"),
        T(lang, "p5"),
        T(lang, "p6"),
        T(lang, "p7"),
        "",
        T(lang, "p8"),
        task.text,
    ]
    if task.options:
        opt_lines = []
        for o in task.options:
            letter = chr(ord("A") + (o.index - 1))
            opt_lines.append(f"{o.index}/{letter}. {o.text}")
        parts.extend(["", T(lang, "p_radio_hdr"), "\n".join(opt_lines)])
    if task.dropdown_texts:
        lines = []
        for i, opts in enumerate(task.dropdown_texts, start=1):
            lettered = [f"{chr(ord('A')+j)}. {txt}" for j, txt in enumerate(opts)]
            lines.append(f"{i}) " + " | ".join(lettered))
        parts.extend(["", T(lang, "p_drop_hdr"), "\n".join(lines)])
    return "\n".join(parts)


def parse_answer(answer: str, task: TaskData):
    if not answer:
        return {"mode": "empty", "values": []}
    lines = [line.strip() for line in answer.splitlines() if line.strip()]
    if not lines:
        return {"mode": "empty", "values": []}

    if task.drag_targets and task.drag_options:
        option_texts = [o.text.lower() for o in task.drag_options]
        values: List[int] = []
        for i in range(len(task.drag_targets)):
            line = lines[i] if i < len(lines) else (lines[-1] if lines else "")
            chosen_idx = None
            if line:
                mnum = re.findall(r"\d+", line)
                if mnum:
                    k = int(mnum[0])
                    if 1 <= k <= len(option_texts):
                        chosen_idx = k
                if chosen_idx is None:
                    normalized = line.lower()
                    for j, txt in enumerate(option_texts, start=1):
                        if normalized == txt or (normalized and normalized in txt):
                            chosen_idx = j
                            break
            values.append(chosen_idx or 1)
        return {"mode": "drag", "values": values}

    if task.dropdown_texts:
        values: List[int] = []
        for i, options_texts in enumerate(task.dropdown_texts):
            line = lines[i] if i < len(lines) else ""
            chosen_idx = None
            mnum = re.findall(r"\d+", line)
            if mnum:
                k = int(mnum[0])
                if 1 <= k <= len(options_texts):
                    chosen_idx = k
            if chosen_idx is None:
                mlet = re.findall(r"\b([A-Za-z])\b", line)
                if mlet:
                    L = mlet[0].lower()
                    k = ord(L) - ord("a") + 1
                    if 1 <= k <= len(options_texts):
                        chosen_idx = k
            if chosen_idx is None:
                normalized = line.lower()
                for j, txt in enumerate(options_texts, start=1):
                    if normalized == txt.lower():
                        chosen_idx = j
                        break
            if chosen_idx is None:
                normalized = line.lower()
                for j, txt in enumerate(options_texts, start=1):
                    if normalized and normalized in txt.lower():
                        chosen_idx = j
                        break
            values.append(chosen_idx or 1)
        return {"mode": "dropdowns", "values": values}

    if task.options:
        option_map = {o.index: o for o in task.options}
        letter_to_idx = {
            chr(ord("A") + (o.index - 1)).lower(): o.index for o in task.options
        }
        selected: List[int] = []
        for line in lines:
            for d in re.findall(r"\d+", line):
                i = int(d)
                if i in option_map and i not in selected:
                    selected.append(i)
            for L in re.findall(r"\b([A-Za-z])\b", line):
                idx = letter_to_idx.get(L.lower())
                if idx and idx not in selected:
                    selected.append(idx)
            if selected:
                continue
            normalized = line.lower()
            for o in task.options:
                if o.text.lower() == normalized and o.index not in selected:
                    selected.append(o.index)
                    break
        return {"mode": "select", "values": selected}

    tokens: List[str] = []
    for line in lines:
        core = re.sub(r"^\s*\d+[\)\.-:]*\s*", "", line)
        parts = re.findall(r"-?\d+(?:[.,]\d+)?|[A-Za-zĀ-ž]+", core)
        tokens.extend(parts)
    if not tokens:
        tokens = re.findall(r"-?\d+(?:[.,]\d+)?", answer)
    return {"mode": "text", "values": tokens}


# ----------------------- Fillers ------------------------

def fill_in_answers(driver, values: List[str], lang: str, logger: Logger = None):
    inputs = driver.find_elements(
        By.CSS_SELECTOR,
        "input[type='text'],input[type='number'],textarea,input.gxs-answer-number",
    )
    if not inputs:
        log_message(T(lang, "no_inputs"), logger)
        return
    for idx, element in enumerate(inputs):
        if idx >= len(values):
            break
        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
            driver.execute_script("arguments[0].value='';", element)
            element.send_keys(str(values[idx]))
        except Exception:
            continue
    submit_button = w(driver, "#submitAnswerBtn", 6, "clickable")
    if submit_button is not None:
        js_click(driver, submit_button)
        log_message(T(lang, "submitted"), logger)
    else:
        log_message(T(lang, "no_btn"), logger)


def select_answers(driver, task: TaskData, indexes: List[int], lang: str, logger: Logger = None):
    if not indexes:
        log_message(T(lang, "no_valid"), logger)
        return
    options = {o.index: o for o in task.options}
    chosen = []
    for idx in indexes:
        opt = options.get(idx)
        if not opt:
            continue
        target = opt.label_element if opt.label_element else opt.input_element
        try:
            js_click(driver, target)
            chosen.append(idx)
        except Exception:
            continue
    if chosen:
        submit_button = w(driver, "#submitAnswerBtn", 6, "clickable")
        if submit_button is not None:
            js_click(driver, submit_button)
            log_message(T(lang, "submitted"), logger)
        else:
            log_message(T(lang, "no_btn"), logger)
    else:
        log_message(T(lang, "no_valid"), logger)


def fill_dropdowns(
    driver,
    dropdown_texts: List[List[str]],
    dropdown_ids: List[Optional[str]],
    values: List[int],
    lang,
    logger: Logger = None,
):
    wrapper = w(driver, "#taskhtml > div", 6, "visible")
    if not wrapper:
        log_message(T(lang, "no_inputs"), logger)
        return
    fresh_selects: List[object] = []
    for sid in dropdown_ids:
        sel_el = None
        if sid:
            try:
                sel_el = driver.find_element(By.ID, sid)
            except Exception:
                sel_el = None
        if sel_el is None:
            try:
                all_sel = wrapper.find_elements(By.CSS_SELECTOR, "select.gxs-answer-dropdown")
                used = set(map(id, fresh_selects))
                sel_el = next((e for e in all_sel if id(e) not in used), None)
            except Exception:
                sel_el = None
        fresh_selects.append(sel_el)
    valid = [e for e in fresh_selects if e is not None]
    if len(valid) != len(dropdown_texts):
        try:
            fresh_selects = wrapper.find_elements(By.CSS_SELECTOR, "select.gxs-answer-dropdown")
        except Exception:
            fresh_selects = []
    for i, sel_el in enumerate(fresh_selects):
        if i >= len(values):
            break
        if sel_el is None:
            continue
        idx = values[i]
        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", sel_el)
            s = Select(sel_el)
            opts = dropdown_texts[i]
            if 1 <= idx <= len(opts):
                s.select_by_visible_text(opts[idx - 1])
            else:
                s.select_by_index(max(0, idx - 1))
        except StaleElementReferenceException:
            try:
                sid = dropdown_ids[i]
                sel2 = (
                    driver.find_element(By.ID, sid)
                    if sid
                    else wrapper.find_elements(By.CSS_SELECTOR, "select.gxs-answer-dropdown")[i]
                )
                s2 = Select(sel2)
                opts = dropdown_texts[i]
                if 1 <= idx <= len(opts):
                    s2.select_by_visible_text(opts[idx - 1])
                else:
                    s2.select_by_index(max(0, idx - 1))
            except Exception:
                continue
        except Exception:
            continue
    submit_button = w(driver, "#submitAnswerBtn", 6, "clickable")
    if submit_button is not None:
        js_click(driver, submit_button)
        log_message(T(lang, "submitted"), logger)
    else:
        log_message(T(lang, "no_btn"), logger)


def fill_drag_targets(driver, task: TaskData, values: List[int], lang, logger: Logger = None):
    if not task.drag_targets or not task.drag_options:
        log_message(T(lang, "no_inputs"), logger)
        return

    for i, target in enumerate(task.drag_targets):
        if i >= len(values):
            break
        choice_idx = values[i]
        if not (1 <= choice_idx <= len(task.drag_options)):
            continue
        option = task.drag_options[choice_idx - 1]
        try:
            ActionChains(driver).move_to_element(option.element).click_and_hold().pause(0.1).move_to_element(target.element).pause(0.1).release().perform()
        except Exception:
            try:
                js_click(driver, target.element)
                js_click(driver, option.element)
            except Exception:
                continue

        try:
            data_id = option.element.get_attribute("data-id") or option.text
            if target.input_element and data_id:
                driver.execute_script(
                    "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change', {bubbles:true}));",
                    target.input_element,
                    data_id,
                )
        except Exception:
            pass

    submit_button = w(driver, "#submitAnswerBtn", 6, "clickable")
    if submit_button is not None:
        js_click(driver, submit_button)
        log_message(T(lang, "submitted"), logger)
    else:
        log_message(T(lang, "no_btn"), logger)


# ----------------------- Orchestrator -------------------

def solve_one_task(main_driver, gpt: ChatGPTSession, lang: str, logger: Logger = None) -> float:
    def select_and_fetch():
        ok = select_task(main_driver, lang, logger)
        if not ok:
            return None
        return fetch_task(main_driver, lang, logger)

    task: Optional[TaskData] = None
    for _ in range(12):
        task = select_and_fetch()
        if task == "SKIP":
            log_message("↻ …", logger)
            continue
        if task is None:
            log_message("↻ …", logger)
            continue
        break

    if not isinstance(task, TaskData):
        log_message(T(lang, "no_valid"), logger)
        return 0.0

    answer = ""
    try:
        answer = gpt.ask_task(task)
        if (
            "Priekšmets:" in task.text
            and ("⚠" in answer or "skipping task" in answer.lower() or "Atveru ChatGPT" in answer)
        ):
            raise RuntimeError("GPT fallback skipped or failed — retrying with new token")
    except Exception:
        log_message("⚠  fetching new token…", logger)
        new_token = fetch_chatgpt5free_token(max_wait=8.0)
        if new_token and new_token.startswith("Bearer "):
            new_token = new_token[len("Bearer ") :]
        if new_token:
            gpt._swap_client(new_token)
            log_message("↻ Retrying GPT task with new token", logger)
            try:
                answer = gpt.ask_task(task)
            except Exception:
                log_message("⚠  skipping task (again)", logger)
                return 0.0
        else:
            log_message("⚠  token not found — skipping task", logger)
            return 0.0

    parsed = parse_answer(answer, task)

    if parsed["mode"] == "dropdowns" and task.dropdown_texts:
        fill_dropdowns(main_driver, task.dropdown_texts, task.dropdown_ids, parsed["values"], lang, logger)
    elif parsed["mode"] == "drag" and task.drag_targets and task.drag_options:
        fill_drag_targets(main_driver, task, parsed["values"], lang, logger)
    elif parsed["mode"] == "select" and task.options:
        select_answers(main_driver, task, parsed["values"], lang, logger)
    elif parsed["mode"] == "text" and parsed["values"]:
        fill_in_answers(main_driver, parsed["values"], lang, logger)
    else:
        log_message(T(lang, "no_valid"), logger)

    pts = parse_points_label(task.points_label)
    log_message(T(lang, "points_val", x=pts), logger)
    return pts


def run_automation(
    user: str,
    password: str,
    lang: str = "lv",
    logger: Logger = None,
    debug: bool = False,
    until_top: Optional[int] = None,
    gain_points: Optional[float] = None,
    keysys_user: Optional[str] = None,
    license_key: Optional[str] = None,
    force_keysys: bool = False,
) -> None:
    lic = LicenseManager(lang=lang, logger=logger)
    lic.ensure_for_cli(
        use_keysys_flag=force_keysys,
        license_user_arg=keysys_user,
        license_key_arg=license_key,
    )

    driver = build_fast_driver(incognito=True, new_window=False, block_images=True)
    clear_cookies(driver)

    def recreate_main():
        nonlocal driver
        try:
            try:
                clear_cookies(driver)
            except Exception:
                pass
            try:
                driver.quit()
            except Exception:
                pass
        finally:
            driver = build_fast_driver(incognito=True, new_window=False, block_images=True)

    gpt_session: Optional[ChatGPTSession] = None
    try:
        with_resilience(
            lambda: login(driver, user, password, lang, logger),
            recreate_main,
            lang,
            logger,
            retries=3,
        )
        gpt_session = ChatGPTSession(lang=lang, logger=logger)

        start_top = read_top_points(driver) or 0
        if until_top is not None:
            target_abs = until_top
            suffix = T(lang, "top_target", t=target_abs)
        elif gain_points is not None:
            target_abs = start_top + int(gain_points)
            suffix = T(lang, "top_target", t=target_abs)
        else:
            target_abs = None
            suffix = ""
        save_target_preferences(until_top, gain_points)
        log_message(T(lang, "top_start", a=start_top, b=suffix), logger)

        round_idx = 0
        while True:
            round_idx += 1
            log_message(T(lang, "cycle", x=round_idx), logger)
            try:
                _ = solve_one_task(driver, gpt_session, lang, logger)
            except Exception:
                log_message("↻ Restarting browsers…", logger)
                recreate_main()
                with_resilience(
                    lambda: login(driver, user, password, lang, logger),
                    recreate_main,
                    lang,
                    logger,
                    retries=2,
                )
                continue
            time.sleep(0.7)
            now_top = read_top_points(driver) or start_top
            log_message(T(lang, "top_now", x=now_top), logger)
            if target_abs is not None and now_top >= target_abs:
                log_message(T(lang, "top_reached", a=now_top, b=target_abs), logger)
                break
            if target_abs is None:
                break
            try:
                driver.get("https://www.uzdevumi.lv/p")
                apply_hide_media_css(driver)
            except Exception:
                recreate_main()

        log_message(T(lang, "done"), logger)
        if debug:
            log_message(T(lang, "debug_keep"), logger)
            return
    finally:
        if not debug:
            try:
                driver.quit()
            except Exception:
                pass
            if gpt_session:
                gpt_session.close()


# ----------------------- GUI (CustomTkinter) -----------

def detect_backends() -> Dict[str, object]:
    available: Dict[str, object] = {}
    try:
        import customtkinter as ctk  # type: ignore

        available["customtkinter"] = ctk
    except ImportError:
        pass
    return available


def run_customtkinter_ui(ctk, default_lang: str = "lv", debug_default: bool = False) -> None:
    import tkinter.messagebox as messagebox
    import tkinter as tk

    app = ctk.CTk()
    app.title(I18N[default_lang]["title"])
    app.geometry("700x720")
    lang_var = tk.StringVar(value=default_lang)

    def L(key, **kw):
        return T(lang_var.get(), key, **kw)

    app.grid_columnconfigure(0, weight=1)
    header = ctk.CTkLabel(app, text=L("title"), font=("Arial", 20, "bold"))
    header.grid(row=0, column=0, pady=(12, 4))

    cred = ctk.CTkFrame(app)
    cred.grid(row=1, column=0, padx=12, pady=8, sticky="ew")
    cred.grid_columnconfigure(1, weight=1)
    user_label = ctk.CTkLabel(cred, text=L("ui_username"))
    user_label.grid(row=0, column=0, padx=8, pady=6, sticky="w")
    user_entry = ctk.CTkEntry(cred)
    user_entry.grid(row=0, column=1, padx=8, pady=6, sticky="ew")
    pass_label = ctk.CTkLabel(cred, text=L("ui_password"))
    pass_label.grid(row=1, column=0, padx=8, pady=6, sticky="w")
    pass_entry = ctk.CTkEntry(cred, show="*")
    pass_entry.grid(row=1, column=1, padx=8, pady=6, sticky="ew")

    lic_frame = ctk.CTkFrame(app)
    lic_frame.grid(row=2, column=0, padx=12, pady=8, sticky="ew")
    lic_frame.grid_columnconfigure(1, weight=1)
    ctk.CTkLabel(lic_frame, text=L("ui_license")).grid(row=0, column=0, padx=8, pady=(8, 4), sticky="w")
    ctk.CTkLabel(lic_frame, text=L("ui_license_user")).grid(row=1, column=0, padx=8, pady=4, sticky="w")
    lic_user_entry = ctk.CTkEntry(lic_frame, placeholder_text=L("ui_license_user_ph"))
    lic_user_entry.grid(row=1, column=1, padx=8, pady=4, sticky="ew")
    ctk.CTkLabel(lic_frame, text=L("ui_license_key")).grid(row=2, column=0, padx=8, pady=4, sticky="w")
    lic_key_entry = ctk.CTkEntry(lic_frame, placeholder_text=L("ui_license_key_ph"))
    lic_key_entry.grid(row=2, column=1, padx=8, pady=4, sticky="ew")

    lic_status = ctk.CTkLabel(lic_frame, text=L("status") + ": —")
    lic_status.grid(row=3, column=0, columnspan=2, padx=8, pady=6, sticky="w")

    btn_row = ctk.CTkFrame(lic_frame)
    btn_row.grid(row=4, column=0, columnspan=2, padx=0, pady=4, sticky="w")
    lic_check_btn = ctk.CTkButton(btn_row, text=L("ui_check_license"))
    lic_check_btn.grid(row=0, column=0, padx=6, pady=4)
    lic_end_btn = ctk.CTkButton(btn_row, text=L("ui_end_trial"))
    lic_end_btn.grid(row=0, column=1, padx=6, pady=4)

    opts = ctk.CTkFrame(app)
    opts.grid(row=3, column=0, padx=12, pady=8, sticky="ew")
    opts.grid_columnconfigure(1, weight=1)
    dbg_var = tk.BooleanVar(value=debug_default)
    dbg_chk = ctk.CTkCheckBox(opts, text=L("ui_debug"), variable=dbg_var)
    dbg_chk.grid(row=0, column=0, padx=8, pady=4, sticky="w")

    remember_var = tk.BooleanVar(value=False)
    remember_chk = ctk.CTkCheckBox(opts, text=L("ui_remember"), variable=remember_var)
    remember_chk.grid(row=0, column=1, padx=8, pady=4, sticky="w")

    until_entry = ctk.CTkEntry(opts, placeholder_text=L("ui_until"))
    until_entry.grid(row=1, column=0, padx=8, pady=4, sticky="ew")
    gain_entry = ctk.CTkEntry(opts, placeholder_text=L("ui_gain"))
    gain_entry.grid(row=1, column=1, padx=8, pady=4, sticky="ew")

    saved_until, saved_gain = load_target_preferences()
    if saved_until is not None:
        until_entry.insert(0, str(saved_until))
    if saved_gain is not None:
        gain_entry.insert(0, str(saved_gain))

    lang_frame = ctk.CTkFrame(app)
    lang_frame.grid(row=4, column=0, padx=12, pady=4, sticky="ew")
    ctk.CTkLabel(lang_frame, text=L("ui_lang")).grid(row=0, column=0, padx=8, pady=6, sticky="w")
    lang_menu = ctk.CTkOptionMenu(lang_frame, values=["lv", "en", "ru"], variable=lang_var)
    lang_menu.grid(row=0, column=1, padx=8, pady=6, sticky="w")

    btns = ctk.CTkFrame(app)
    btns.grid(row=5, column=0, padx=12, pady=8, sticky="ew")
    start_btn = ctk.CTkButton(btns, text=L("ui_start"))
    start_btn.grid(row=0, column=0, padx=8, pady=8)
    ctk.CTkButton(btns, text=L("ui_close"), command=app.destroy).grid(row=0, column=1, padx=8, pady=8)

    log_box = ctk.CTkTextbox(app, height=240)
    log_box.grid(row=6, column=0, padx=12, pady=(8, 12), sticky="nsew")
    app.grid_rowconfigure(6, weight=1)
    log_box.configure(state="disabled")
    log_queue: "queue.Queue[str]" = queue.Queue()

    tier_label = ctk.CTkLabel(app, text=L("ui_tier", t="—"))
    tier_label.grid(row=7, column=0, padx=12, pady=(0, 12), sticky="w")

    def append_log(m: str):
        log_queue.put(m)

    def process_queue():
        try:
            while True:
                m = log_queue.get_nowait()
                log_box.configure(state="normal")
                log_box.insert("end", m + "\n")
                log_box.see("end")
                log_box.configure(state="disabled")
        except queue.Empty:
            pass
        app.after(100, process_queue)

    lic_mgr = LicenseManager(lang=lang_var.get(), logger=append_log)
    popup_open_flag = {"open": False}

    saved_user, saved_pass = load_saved_credentials()
    if saved_user and saved_pass:
        user_entry.insert(0, saved_user)
        pass_entry.insert(0, saved_pass)
        remember_var.set(True)
        append_log(T(lang_var.get(), "creds_loaded"))

    def update_license_status():
        lic_mgr.lang = lang_var.get()
        st = lic_mgr.status()
        if st["state"] == "licensed":
            lic_status.configure(text=L("ui_licensed", u=st.get("user") or ""))
            start_btn.configure(state="normal")
        elif st["state"] == "trial":
            left = int(st.get("left_seconds") or 0)
            h = left // 3600
            m = (left % 3600) // 60
            s = left % 60
            lic_status.configure(text=L("ui_trial_left", h=h, m=m, s=s))
            start_btn.configure(state="normal")
        else:
            lic_status.configure(text=L("ui_trial_expired"))
            start_btn.configure(state="disabled")
            if not popup_open_flag["open"]:
                popup_open_flag["open"] = True
                open_license_popup()

        tier_text = st.get("tier") or (L("ui_tier_trial") if st["state"] == "trial" else "—")
        tier_label.configure(text=L("ui_tier", t=tier_text))

        app.after(1000, update_license_status)

    def open_license_popup():
        win = ctk.CTkToplevel(app)
        win.title(L("ui_popup_title"))
        win.grab_set()
        win.geometry("420x220")
        win.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(win, text=L("ui_popup_msg")).grid(
            row=0, column=0, columnspan=2, padx=12, pady=(12, 6), sticky="w"
        )
        ctk.CTkLabel(win, text=L("ui_license_user")).grid(row=1, column=0, padx=12, pady=6, sticky="w")
        e_user = ctk.CTkEntry(win, placeholder_text=L("ui_license_user_ph"))
        e_user.grid(row=1, column=1, padx=12, pady=6, sticky="ew")
        ctk.CTkLabel(win, text=L("ui_license_key")).grid(row=2, column=0, padx=12, pady=6, sticky="w")
        e_key = ctk.CTkEntry(win, placeholder_text=L("ui_license_key_ph"))
        e_key.grid(row=2, column=1, padx=12, pady=6, sticky="ew")

        def on_ok():
            u = e_user.get().strip()
            k = e_key.get().strip()
            ok, msg = lic_mgr.validate_and_store(u, k)
            if ok:
                lic_user_entry.delete(0, tk.END)
                lic_user_entry.insert(0, u)
                lic_key_entry.delete(0, tk.END)
                lic_key_entry.insert(0, k)
                win.destroy()
                popup_open_flag["open"] = False
            else:
                messagebox.showerror(L("ui_popup_title"), msg)

        def on_cancel():
            win.destroy()
            popup_open_flag["open"] = False

        btns = ctk.CTkFrame(win)
        btns.grid(row=3, column=0, columnspan=2, pady=12)
        ctk.CTkButton(btns, text=L("ui_popup_btn_ok"), command=on_ok).grid(row=0, column=0, padx=6)
        ctk.CTkButton(btns, text=L("ui_popup_btn_cancel"), command=on_cancel).grid(row=0, column=1, padx=6)

    def on_check_license():
        u = lic_user_entry.get().strip()
        k = lic_key_entry.get().strip()
        ok, msg = lic_mgr.validate_and_store(u, k)
        if ok:
            messagebox.showinfo(L("ui_license"), T(lang_var.get(), "lic_valid", u=u))
        else:
            messagebox.showerror(L("ui_license"), msg)

    def on_end_trial():
        lic_mgr.burn_trial()
        append_log(T(lang_var.get(), "lic_burned"))

    lic_check_btn.configure(command=on_check_license)
    lic_end_btn.configure(command=on_end_trial)

    def finish_run():
        start_btn.configure(state="normal")

    def worker(
        u: str,
        p: str,
        dbg: bool,
        until_val: Optional[int],
        gain_val: Optional[float],
        lang_sel: str,
        ks_user: Optional[str],
        ks_key: Optional[str],
        force_keysys: bool,
    ):
        try:
            run_automation(
                u,
                p,
                lang=lang_sel,
                logger=append_log,
                debug=dbg,
                until_top=until_val,
                gain_points=gain_val,
                keysys_user=ks_user,
                license_key=ks_key,
                force_keysys=force_keysys,
            )
        except Exception:
            append_log("⚠  automatizācija apstādināta")
        finally:
            app.after(0, finish_run)

    def on_start():
        u = user_entry.get().strip()
        p = pass_entry.get().strip()
        if not u or not p:
            messagebox.showerror(I18N[lang_var.get()]["title"], T(lang_var.get(), "ui_error_need_creds"))
            return
        until_val = None
        gain_val = None
        try:
            if until_entry.get().strip():
                until_val = int(re.sub(r"\D", "", until_entry.get().strip()))
        except Exception:
            until_val = None
        try:
            if gain_entry.get().strip():
                gain_val = float(
                    re.sub(r"[^0-9.,]", "", gain_entry.get().strip()).replace(",", ".")
                )
        except Exception:
            gain_val = None

        st = lic_mgr.status()
        force = st["state"] == "expired"

        ks_user = lic_user_entry.get().strip() or None
        ks_key = lic_key_entry.get().strip() or None

        if remember_var.get():
            save_credentials(u, p)
            append_log(T(lang_var.get(), "creds_saved"))
        else:
            clear_saved_credentials()
            append_log(T(lang_var.get(), "creds_cleared"))

        save_target_preferences(until_val, gain_val)

        start_btn.configure(state="disabled")
        threading.Thread(
            target=worker,
            args=(
                u,
                p,
                dbg_var.get(),
                until_val,
                gain_val,
                lang_var.get(),
                ks_user,
                ks_key,
                force,
            ),
            daemon=True,
        ).start()

    def refresh_ui(*_):
        app.title(L("title"))
        header.configure(text=L("title"))
        user_label.configure(text=L("ui_username"))
        pass_label.configure(text=L("ui_password"))
        dbg_chk.configure(text=L("ui_debug"))
        remember_chk.configure(text=L("ui_remember"))
        until_entry.configure(placeholder_text=L("ui_until"))
        gain_entry.configure(placeholder_text=L("ui_gain"))
        start_btn.configure(text=L("ui_start"))
        lic_check_btn.configure(text=L("ui_check_license"))
        lic_end_btn.configure(text=L("ui_end_trial"))
        lic_status.configure(text=L("status") + ": —")
        lic_user_entry.configure(placeholder_text=L("ui_license_user_ph"))
        lic_key_entry.configure(placeholder_text=L("ui_license_key_ph"))

    lang_var.trace_add(
        "write",
        lambda *a: (
            setattr(lic_mgr, "lang", lang_var.get()),
            refresh_ui(),
        ),
    )
    start_btn.configure(command=on_start)

    app.after(100, process_queue)
    app.after(200, update_license_status)
    app.mainloop()


def launch_gui(default_lang: str, debug_default: bool) -> None:
    available = detect_backends()
    if not available or "customtkinter" not in available:
        raise RuntimeError("GUI not available (customtkinter missing). Use CLI with --nogui.")
    run_customtkinter_ui(available["customtkinter"], default_lang=default_lang, debug_default=debug_default)


# ----------------------- CLI ---------------------------

def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        description="Uzdevumi.lv bot (FAST + dropdowns + loop + i18n + Keysys licensing)"
    )
    parser.add_argument("--lang", choices=["lv", "en", "ru"], default="lv", help="UI/log/prompt language")
    parser.add_argument("--debug", action="store_true", help="Keep browsers open at the end")
    parser.add_argument("--until-top", type=int, help="Stop when Top points reach this absolute value")
    parser.add_argument("--gain", type=float, help="Stop after gaining this many Top points relative to start")
    parser.add_argument("--nogui", action="store_true", help="Run without GUI (pure CLI)")
    parser.add_argument("--user", help="uzdevumi.lv user ID (CLI)")
    parser.add_argument("--passw", help="uzdevumi.lv password (CLI)")
    parser.add_argument("--keysys", action="store_true", help="Force Keysys mode (burns trial immediately; requires --license-user and --license)")
    parser.add_argument("--license-user", help="Keysys username")
    parser.add_argument("--license", help="Keysys license key")
    parser.add_argument("--use-saved-creds", action="store_true", help="Load saved credentials if present")
    parser.add_argument("--save-creds", action="store_true", help="Save provided credentials after a successful run")
    parser.add_argument("--forget-creds", action="store_true", help="Clear saved credentials and exit")
    args = parser.parse_args(argv)

    if args.forget_creds:
        clear_saved_credentials()
        print(T(args.lang, "creds_cleared"))
        return

    if args.nogui:
        cli_user = args.user
        cli_pass = args.passw
        if args.use_saved_creds and (not cli_user or not cli_pass):
            saved_user, saved_pass = load_saved_credentials()
            if saved_user and saved_pass:
                cli_user = cli_user or saved_user
                cli_pass = cli_pass or saved_pass
                print(T(args.lang, "creds_loaded"))
        if not cli_user or not cli_pass:
            print("CLI mode requires --user and --passw")
            sys.exit(2)
        save_target_preferences(args.until_top, args.gain)
        run_automation(
            cli_user,
            cli_pass,
            lang=args.lang,
            logger=None,
            debug=args.debug,
            until_top=args.until_top,
            gain_points=args.gain,
            keysys_user=args.license_user,
            license_key=args.license,
            force_keysys=args.keysys,
        )
        if args.save_creds:
            save_credentials(cli_user, cli_pass)
            print(T(args.lang, "creds_saved"))
    else:
        launch_gui(default_lang=args.lang, debug_default=args.debug)


if __name__ == "__main__":
    main()
