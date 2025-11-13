import argparse
import itertools
import queue
import random
import re
import sys
import threading
import time
import hashlib
import platform
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache
from typing import Callable, Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlsplit
import os,sys;I18N_URL={"lv":"https://www.google.com/intl/lv/chrome/","en":"https://www.google.com/chrome/","ru":"https://www.google.com/intl/ru/chrome/"};chrome_path=r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";lang="lv";(os.path.exists(chrome_path) or sys.exit(f"❗ { {'lv':'Nepieciešams Google Chrome! Lejupielādē no:','en':'Google Chrome is required! Download from:','ru':'Требуется Google Chrome! Скачайте по ссылке:'}[lang] } {I18N_URL[lang]}"))

import base64
import json
from pathlib import Path

import requests
import undetected_chromedriver as uc
from selenium.common.exceptions import TimeoutException, NoSuchWindowException, WebDriverException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait, Select

# ----------------------- CONFIG -----------------------

KEYSYS_BASE = "https://keysys.djcookfan61.workers.dev"
KEYSYS_VALIDATE = KEYSYS_BASE + "/validate"

REG_PATH = r"Software\\Keysys\\UzdevumiBot"
TRIAL_MINUTES = 120

CONFIG_DIR = Path.home() / ".uzdevumi_bot"
CREDS_FILE = CONFIG_DIR / "credentials.json"

REMOTE_TASK_SCAN_TIMEOUT = 6
REMOTE_MEDIA_PATTERNS = (
    "<img",
    "gxs-resource-image",
    "gxst-resource-image",
    "background-image",
    "gxs-dnd-option",
    "answer-box",
    "ui-draggable",
)
SMART_RETRY_THRESHOLD = 3.0
SMART_RETRY_MAX_ATTEMPTS = 3
CORRECT_FEEDBACK_TOKENS = {
    "pareizi",
    "correct",
    "правильно",
    "atzinīgi",
    "✔",
}
INCORRECT_FEEDBACK_TOKENS = {
    "nepareizi",
    "incorrect",
    "неверно",
    "✘",
    "try again",
}

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
        "prefetch_scan": "Attālināti pārbaudu uzdevumus…",
        "prefetch_skip": "Attālināta pārbaude: atrasts attēls — izlaižu.",
        "prefetch_ok": "Attālināta pārbaude: atrasts derīgs uzdevums.",
        "prefetch_none": "Attālināta pārbaude: nav derīgu uzdevumu bez attēliem.",
        "smart_retry": "Vairāk nekā 3 punkti — atkārtoju mēģinājumu {a}/{b}.",
        "smart_retry_feedback": "Atgriezeniskā saite: {x}.",
        # UI
        "ui_username": "Personas kods",
        "ui_password": "Parole",
        "ui_debug": "Atstāt pārlūkus atvērtus",
        "ui_beta": "Eksperimentālā beta versija",
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
        "ui_gui_tools": "GUI rīki",
        "ui_theme": "Tēma",
        "ui_theme_system": "Sistēma",
        "ui_theme_light": "Gaiša",
        "ui_theme_dark": "Tumša",
        "ui_accent": "Akcenta krāsa",
        "ui_log_tools": "Žurnāla vadīklas",
        "ui_log_wrap": "Rindkopu aplaušana",
        "ui_log_autoscroll": "Automātiskā ritināšana",
        "ui_log_pause": "Pauzēt atjauninājumus",
        "ui_log_clear": "Notīrīt",
        "ui_log_copy": "Kopēt",
        "ui_log_save": "Saglabāt…",
        "ui_log_filter": "Filtrēt žurnālu",
        "ui_log_highlight": "Izcelt kļūdas",
        "ui_log_timestamp": "Pievienot laikspiedogu",
        "ui_widget_scaling": "UI mērogs",
        "ui_log_font": "Žurnāla fonts",
        "ui_log_saved": "Žurnāls saglabāts.",
        "ui_trial_left": "Atlicis izmēģinājuma laiks: {h}:{m:02d}:{s:02d}",
        "ui_trial_expired": "Izmēģinājums beidzies — nepieciešama licence.",
        "ui_licensed": "Licencēts: {u}",
        "ui_popup_title": "Licence",
        "ui_popup_msg": "Ievadi lietotājvārdu un licences atslēgu:",
        "ui_popup_btn_ok": "Apstiprināt",
        "ui_popup_btn_cancel": "Atcelt",
        "ui_remember": "Saglabāt pierakstīšanās datus",
        "ui_beta_features": "Beta funkciju pārslēgšana",
        "ui_beta_feature_hint": "Katru beta iespēju var ieslēgt vai izslēgt individuāli.",
        "ui_beta_feature_search": "Meklēt",
        "ui_select_all": "Ieslēgt visas",
        "ui_select_none": "Izslēgt visas",
        "ui_restore_defaults": "Atjaunot noklusējumus",
        "ui_import": "Importēt",
        "ui_export": "Eksportēt",
        "ui_collapse": "Sakļaut",
        "ui_expand": "Izvērst",
        "ui_feature_count": "Ieslēgts: {a}/{b}",
        "ui_beta_feature_saved": "Presets saglabāts.",
        "ui_beta_feature_loaded": "Presets ielādēts.",
        "ui_beta_feature_error": "Neizdevās apstrādāt presetu: {e}",
        "ui_advanced_features": "Papildu GUI iespējas",
        "ui_advanced_hint": "Detalizēti pielāgo žurnālu, izkārtojumu un automātiskās darbības.",
        "ui_tab_prefixes": "Prefiksi",
        "ui_tab_suffixes": "Sufiksi",
        "ui_tab_transforms": "Transformācijas",
        "ui_tab_highlights": "Izcēlumi",
        "ui_tab_filters": "Filtri",
        "ui_tab_actions": "Darbības",
        "ui_tab_layout": "Izkārtojums",
        "ui_tab_summary": "Kopsavilkums",
        "ui_summary_placeholder": "Nav izvēlēta kopsavilkuma metrika.",
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
        "prefetch_scan": "Remotely screening tasks…",
        "prefetch_skip": "Remote preview: media detected — skipping.",
        "prefetch_ok": "Remote preview: media-free task queued.",
        "prefetch_none": "Remote preview: no media-free tasks available.",
        "smart_retry": "High-value task — retrying attempt {a}/{b}.",
        "smart_retry_feedback": "Feedback: {x}.",
        "ui_username": "User ID",
        "ui_password": "Password",
        "ui_debug": "Keep browsers open",
        "ui_beta": "Enable beta mode (experimental)",
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
        "ui_gui_tools": "GUI tools",
        "ui_theme": "Theme",
        "ui_theme_system": "System",
        "ui_theme_light": "Light",
        "ui_theme_dark": "Dark",
        "ui_accent": "Accent color",
        "ui_log_tools": "Log controls",
        "ui_log_wrap": "Wrap lines",
        "ui_log_autoscroll": "Auto-scroll",
        "ui_log_pause": "Pause updates",
        "ui_log_clear": "Clear",
        "ui_log_copy": "Copy",
        "ui_log_save": "Save…",
        "ui_log_filter": "Filter logs",
        "ui_log_highlight": "Highlight errors",
        "ui_log_timestamp": "Add timestamps",
        "ui_widget_scaling": "UI scale",
        "ui_log_font": "Log font size",
        "ui_log_saved": "Log saved.",
        "ui_trial_left": "Trial time left: {h}:{m:02d}:{s:02d}",
        "ui_trial_expired": "Trial expired — license required.",
        "ui_licensed": "Licensed: {u}",
        "ui_popup_title": "License",
        "ui_popup_msg": "Enter username and license key:",
        "ui_popup_btn_ok": "Confirm",
        "ui_popup_btn_cancel": "Cancel",
        "ui_remember": "Remember credentials",
        "ui_beta_features": "Beta feature toggles",
        "ui_beta_feature_hint": "Enable or disable each experimental capability individually.",
        "ui_beta_feature_search": "Search",
        "ui_select_all": "Enable all",
        "ui_select_none": "Disable all",
        "ui_restore_defaults": "Restore defaults",
        "ui_import": "Import",
        "ui_export": "Export",
        "ui_collapse": "Collapse",
        "ui_expand": "Expand",
        "ui_feature_count": "Enabled: {a}/{b}",
        "ui_beta_feature_saved": "Preset saved.",
        "ui_beta_feature_loaded": "Preset loaded.",
        "ui_beta_feature_error": "Failed to process preset: {e}",
        "ui_advanced_features": "Advanced GUI controls",
        "ui_advanced_hint": "Fine-tune the log viewer, layout tweaks, and automated reactions.",
        "ui_tab_prefixes": "Prefixes",
        "ui_tab_suffixes": "Suffixes",
        "ui_tab_transforms": "Transforms",
        "ui_tab_highlights": "Highlights",
        "ui_tab_filters": "Filters",
        "ui_tab_actions": "Actions",
        "ui_tab_layout": "Layout",
        "ui_tab_summary": "Summary",
        "ui_summary_placeholder": "Enable summary metrics to see live totals.",
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
        "prefetch_scan": "Удалённо просматриваю задания…",
        "prefetch_skip": "Удалённый просмотр: найдены изображения — пропускаю.",
        "prefetch_ok": "Удалённый просмотр: выбрано задание без медиа.",
        "prefetch_none": "Удалённый просмотр: нет заданий без медиа.",
        "smart_retry": "Высокая ценность — повторяю попытку {a}/{b}.",
        "smart_retry_feedback": "Обратная связь: {x}.",
        "ui_username": "Идентификатор",
        "ui_password": "Пароль",
        "ui_debug": "Держать браузеры открытыми",
        "ui_beta": "Включить бета-режим (экспериментально)",
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
        "ui_gui_tools": "Настройки GUI",
        "ui_theme": "Тема",
        "ui_theme_system": "Системная",
        "ui_theme_light": "Светлая",
        "ui_theme_dark": "Тёмная",
        "ui_accent": "Цвет акцента",
        "ui_log_tools": "Управление логом",
        "ui_log_wrap": "Перенос строк",
        "ui_log_autoscroll": "Автопрокрутка",
        "ui_log_pause": "Пауза обновлений",
        "ui_log_clear": "Очистить",
        "ui_log_copy": "Копировать",
        "ui_log_save": "Сохранить…",
        "ui_log_filter": "Фильтр лога",
        "ui_log_highlight": "Подсветка ошибок",
        "ui_log_timestamp": "Добавлять время",
        "ui_widget_scaling": "Масштаб UI",
        "ui_log_font": "Размер шрифта лога",
        "ui_log_saved": "Лог сохранён.",
        "ui_trial_left": "Осталось времени пробного периода: {h}:{m:02d}:{s:02d}",
        "ui_trial_expired": "Пробный период истёк — требуется лицензия.",
        "ui_licensed": "Лицензировано: {u}",
        "ui_popup_title": "Лицензия",
        "ui_popup_msg": "Введите имя пользователя и ключ лицензии:",
        "ui_popup_btn_ok": "Подтвердить",
        "ui_popup_btn_cancel": "Отмена",
        "ui_remember": "Запомнить данные для входа",
        "ui_beta_features": "Переключатели beta-функций",
        "ui_beta_feature_hint": "Каждую экспериментальную возможность можно включить или выключить отдельно.",
        "ui_beta_feature_search": "Поиск",
        "ui_select_all": "Включить все",
        "ui_select_none": "Выключить все",
        "ui_restore_defaults": "Сбросить по умолчанию",
        "ui_import": "Импорт",
        "ui_export": "Экспорт",
        "ui_collapse": "Свернуть",
        "ui_expand": "Развернуть",
        "ui_feature_count": "Включено: {a}/{b}",
        "ui_beta_feature_saved": "Профиль сохранён.",
        "ui_beta_feature_loaded": "Профиль загружен.",
        "ui_beta_feature_error": "Не удалось обработать профиль: {e}",
        "ui_advanced_features": "Дополнительные возможности GUI",
        "ui_advanced_hint": "Тонкая настройка журнала, компоновки и автоматических реакций.",
        "ui_tab_prefixes": "Префиксы",
        "ui_tab_suffixes": "Суффиксы",
        "ui_tab_transforms": "Преобразования",
        "ui_tab_highlights": "Подсветка",
        "ui_tab_filters": "Фильтры",
        "ui_tab_actions": "Действия",
        "ui_tab_layout": "Макет",
        "ui_tab_summary": "Сводка",
        "ui_summary_placeholder": "Включите метрики, чтобы увидеть сводку.",
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


@dataclass
class BetaConfig:
    translation_cache: bool = True
    regex_cache: bool = True
    cached_subjects: bool = True
    cookie_guard: bool = True
    driver_acceleration: bool = True
    wait_optimization: bool = True
    gpt_refresh_strategy: bool = True
    gpt_prompt_cache: bool = True
    parse_answer_fallbacks: bool = True
    dropdown_selection_guard: bool = True
    text_input_normalization: bool = True
    structured_logging: bool = True
    metrics_reporting: bool = True
    auto_recovery_backoff: bool = True
    subject_rotation: bool = True
    top_tracking_enhancements: bool = True
    credential_memory: bool = True
    safe_submit: bool = True
    skip_zero_point_tasks: bool = True
    subject_prefetch: bool = True
    parallel_task_prefetch: bool = True
    remote_media_probe: bool = True
    high_value_retry: bool = True
    feedback_scanner: bool = True
    gpt_prompt_variation: bool = True
    gpt_radix_link_support: bool = True
    gpt_session_watchdog: bool = True
    gpt_button_retry: bool = True
    driver_cookie_sync: bool = True
    user_agent_hinting: bool = True
    prefetch_logging: bool = True
    dropdown_resilience: bool = True
    text_response_tokenizer: bool = True
    numeric_answer_normalizer: bool = True
    answer_mode_detection: bool = True
    submission_feedback_analytics: bool = True
    top_snapshot_history: bool = True
    task_skip_counter: bool = True
    retry_prompt_backoff: bool = True
    parallel_executor_pool: bool = True
    http_probe_timeout: bool = True
    radix_resilience: bool = True
    page_refresh_guard: bool = True
    task_summary_logging: bool = True
    ui_placeholder_sync: bool = True
    license_status_polling: bool = True
    credential_vault: bool = True
    remote_probe_fallback: bool = True
    task_loop_metrics: bool = True
    scoped_logging_filters: bool = True
    automation_health_checks: bool = True
    smart_sleep_reduction: bool = True


@dataclass
class BetaState:
    config: BetaConfig = field(default_factory=BetaConfig)
    enabled: bool = False
    features: List[str] = field(default_factory=list)
    used_subjects: Set[str] = field(default_factory=set)
    session_metrics: Dict[str, float] = field(
        default_factory=lambda: {"tasks": 0, "points": 0.0, "skipped": 0}
    )
    prompt_headers: Dict[str, str] = field(default_factory=dict)
    last_cookie_decline: Set[str] = field(default_factory=set)
    subject_catalog: List[Tuple[str, str]] = field(default_factory=list)

    def mark_task(self, points: float) -> None:
        self.session_metrics["tasks"] += 1
        self.session_metrics["points"] += points

    def mark_skip(self) -> None:
        self.session_metrics["skipped"] += 1


BETA_FEATURE_NAMES = [
    "translation_cache",
    "regex_cache",
    "cached_subjects",
    "cookie_guard",
    "driver_acceleration",
    "wait_optimization",
    "gpt_refresh_strategy",
    "gpt_prompt_cache",
    "parse_answer_fallbacks",
    "dropdown_selection_guard",
    "text_input_normalization",
    "structured_logging",
    "metrics_reporting",
    "auto_recovery_backoff",
    "subject_rotation",
    "top_tracking_enhancements",
    "credential_memory",
    "safe_submit",
    "skip_zero_point_tasks",
    "subject_prefetch",
    "parallel_task_prefetch",
    "remote_media_probe",
    "high_value_retry",
    "feedback_scanner",
    "gpt_prompt_variation",
    "gpt_radix_link_support",
    "gpt_session_watchdog",
    "gpt_button_retry",
    "driver_cookie_sync",
    "user_agent_hinting",
    "prefetch_logging",
    "dropdown_resilience",
    "text_response_tokenizer",
    "numeric_answer_normalizer",
    "answer_mode_detection",
    "submission_feedback_analytics",
    "top_snapshot_history",
    "task_skip_counter",
    "retry_prompt_backoff",
    "parallel_executor_pool",
    "http_probe_timeout",
    "radix_resilience",
    "page_refresh_guard",
    "task_summary_logging",
    "ui_placeholder_sync",
    "license_status_polling",
    "credential_vault",
    "remote_probe_fallback",
    "task_loop_metrics",
    "scoped_logging_filters",
    "automation_health_checks",
    "smart_sleep_reduction",
]


BETA_FEATURE_LABELS: Dict[str, str] = {
    "translation_cache": "Cache translations",
    "regex_cache": "Reuse compiled regexes",
    "cached_subjects": "Cache subject catalog",
    "cookie_guard": "Decline cookie banners once",
    "driver_acceleration": "Accelerated Chrome launch flags",
    "wait_optimization": "Faster Selenium waits",
    "gpt_refresh_strategy": "Adaptive ChatGPT refresh",
    "gpt_prompt_cache": "Cached prompt headers",
    "parse_answer_fallbacks": "Extra answer parsing fallbacks",
    "dropdown_selection_guard": "Dropdown guardrails",
    "text_input_normalization": "Normalize text inputs",
    "structured_logging": "Structured beta logging",
    "metrics_reporting": "Beta metrics reporting",
    "auto_recovery_backoff": "Driver recovery backoff",
    "subject_rotation": "Avoid repeating subjects",
    "top_tracking_enhancements": "Enhanced Top tracking",
    "credential_memory": "Remember credential user ID",
    "safe_submit": "Safe submit button handling",
    "skip_zero_point_tasks": "Skip zero-point tasks",
    "subject_prefetch": "Subject prefetch cache",
    "parallel_task_prefetch": "Parallel HTTP prefetch",
    "remote_media_probe": "Remote media probe",
    "high_value_retry": "High-value smart retry",
    "feedback_scanner": "Submission feedback scanner",
    "gpt_prompt_variation": "Prompt variation on retries",
    "gpt_radix_link_support": "Radix overlay auto-click",
    "gpt_session_watchdog": "ChatGPT session watchdog",
    "gpt_button_retry": "Send-button retry guard",
    "driver_cookie_sync": "Sync cookies to HTTP client",
    "user_agent_hinting": "User-Agent hints for probes",
    "prefetch_logging": "Prefetch telemetry logging",
    "dropdown_resilience": "Re-acquire stale dropdowns",
    "text_response_tokenizer": "Tokenize free-form answers",
    "numeric_answer_normalizer": "Unify decimal separators",
    "answer_mode_detection": "Auto answer-mode detection",
    "submission_feedback_analytics": "Feedback analytics",
    "top_snapshot_history": "Top snapshot history",
    "task_skip_counter": "Skip counter",
    "retry_prompt_backoff": "Retry prompt backoff",
    "parallel_executor_pool": "Dedicated executor pool",
    "http_probe_timeout": "HTTP probe timeouts",
    "radix_resilience": "Radix selector resilience",
    "page_refresh_guard": "Reapply CSS after refresh",
    "task_summary_logging": "Task summary logging",
    "ui_placeholder_sync": "Live placeholder localisation",
    "license_status_polling": "GUI license polling",
    "credential_vault": "Credential vault integration",
    "remote_probe_fallback": "Fallback when probes fail",
    "task_loop_metrics": "Task loop metrics",
    "scoped_logging_filters": "Scoped logging hooks",
    "automation_health_checks": "Automation health checks",
    "smart_sleep_reduction": "Reduced sleep delays",
}


@dataclass(frozen=True)
class GuiFeatureDefinition:
    name: str
    label: str
    category: str
    kind: str
    payload: object = None


@dataclass(frozen=True)
class KeywordSpec:
    name: str
    label: str
    icon: str
    tokens: Tuple[str, ...]


@dataclass
class GuiLogEvent:
    timestamp: datetime
    text: str
    thread_name: str
    thread_id: int


@dataclass
class GuiLogEntry:
    timestamp: datetime
    text: str
    thread_name: str
    thread_id: int
    sequence: int
    level: str
    keywords: Set[str]


KEYWORD_SPECS: List[KeywordSpec] = [
    KeywordSpec("login", "Login flow", "🔐", ("login", "logged in", "logging in")),
    KeywordSpec("cookie", "Cookie banner", "🍪", ("cookie", "cookies", "sīkfail")),
    KeywordSpec("gpt", "ChatGPT", "🤖", ("gpt", "chatgpt")),
    KeywordSpec("subject", "Subject picks", "📚", ("subject", "priekšmet")),
    KeywordSpec("topic", "Topic picks", "🧭", ("topic", "tēma")),
    KeywordSpec("task", "Task flow", "📝", ("task", "uzdevum")),
    KeywordSpec("points", "Points", "🎯", ("point", "punkt")),
    KeywordSpec("top", "Top score", "🏆", ("top", "top points")),
    KeywordSpec("skip", "Skips", "⏭", ("skip", "skipping", "izlaist")),
    KeywordSpec("retry", "Retries", "🔁", ("retry", "mēģināj")),
    KeywordSpec("cycle", "Cycles", "🔄", ("cycle", "cikls")),
    KeywordSpec("license", "License", "🪪", ("license", "licenc")),
    KeywordSpec("trial", "Trial", "⏳", ("trial", "izmēģināj")),
    KeywordSpec("debug", "Debug", "🛠", ("debug",)),
    KeywordSpec("done", "Completion", "✅", ("done", "gatavs", "pabeig")),
    KeywordSpec("submitted", "Submissions", "📨", ("submitted", "iesnieg")),
    KeywordSpec("decline", "Cookie declines", "🚫", ("decline", "noraid")),
    KeywordSpec("http", "HTTP", "🌐", ("http", "https")),
    KeywordSpec("prefetch", "Prefetch", "⚡", ("prefetch",)),
    KeywordSpec("remote", "Remote probes", "📡", ("remote",)),
    KeywordSpec("driver", "Driver", "🚗", ("driver",)),
    KeywordSpec("chrome", "Chrome", "🧭", ("chrome",)),
    KeywordSpec("session", "Session", "🪟", ("session",)),
    KeywordSpec("metrics", "Metrics", "📈", ("metric",)),
    KeywordSpec("summary", "Summary", "🧾", ("summary",)),
    KeywordSpec("dropdown", "Dropdowns", "⬇", ("dropdown", "select box")),
    KeywordSpec("input", "Inputs", "⌨", ("input", "ievade")),
    KeywordSpec("selection", "Selections", "✅", ("select", "selection", "izvēle")),
    KeywordSpec("submit", "Submit", "📤", ("submit", "iesniegt")),
    KeywordSpec("automation", "Automation", "🤖", ("automation", "automatiz")),
    KeywordSpec("cache", "Cache", "🗃", ("cache", "keš")),
    KeywordSpec("probe", "Probes", "🛰", ("probe",)),
    KeywordSpec("radix", "Radix", "🪄", ("radix",)),
    KeywordSpec("watchdog", "Watchdog", "👁", ("watchdog",)),
    KeywordSpec("parallel", "Parallel", "🧵", ("parallel",)),
    KeywordSpec("queue", "Queue", "📬", ("queue",)),
    KeywordSpec("thread", "Threads", "🧶", ("thread",)),
    KeywordSpec("restart", "Restarts", "🔁", ("restart", "restartēt")),
    KeywordSpec("rebuild", "Rebuilds", "🏗", ("rebuild", "build again")),
    KeywordSpec("sync", "Sync", "🔄", ("sync", "synchron")),
    KeywordSpec("filter", "Filters", "🧹", ("filter", "filtr")),
    KeywordSpec("highlight", "Highlights", "💡", ("highlight", "izcelt")),
    KeywordSpec("export", "Exports", "📦", ("export", "eksport")),
    KeywordSpec("import", "Imports", "📥", ("import", "importēt")),
    KeywordSpec("preset", "Presets", "🗂", ("preset", "profils")),
    KeywordSpec("credential", "Credentials", "🔑", ("credential", "pierakst")),
    KeywordSpec("beta", "Beta", "β", ("beta",)),
    KeywordSpec("feature", "Features", "✨", ("feature", "funkcij")),
    KeywordSpec("until", "Until target", "🎯", ("until", "mērķ")),
    KeywordSpec("gain", "Gain", "📈", ("gain", "pieaug")),
    KeywordSpec("performance", "Performance", "🚀", ("performance", "speed", "ātrum")),
    KeywordSpec("stability", "Stability", "🛡", ("stability", "stable", "stabil")),
    KeywordSpec("interface", "Interface", "🖥", ("interface", "ui", "lietot")),
    KeywordSpec("theme", "Theme", "🎨", ("theme", "appearance", "izskats")),
    KeywordSpec("history", "History", "📜", ("history", "vēstur", "log history")),
    KeywordSpec("overview", "Overview", "🧮", ("overview", "summary", "apskats")),
]


KEYWORD_SPEC_BY_NAME: Dict[str, KeywordSpec] = {spec.name: spec for spec in KEYWORD_SPECS}


PREFIX_FEATURE_DATA: List[Tuple[str, str, str]] = [
    ("prefix_time_millis", "Prefix millisecond timestamp", "time_ms"),
    ("prefix_time_seconds", "Prefix time (HH:MM:SS)", "time_sec"),
    ("prefix_date_short", "Prefix date (YYYY-MM-DD)", "date_short"),
    ("prefix_date_long", "Prefix weekday", "date_long"),
    ("prefix_iso_timestamp", "Prefix ISO timestamp", "iso"),
    ("prefix_delta_previous", "Prefix delta from previous log", "delta_prev"),
    ("prefix_delta_start", "Prefix delta from first log", "delta_start"),
    ("prefix_sequence_number", "Prefix sequence number", "sequence"),
    ("prefix_thread_name", "Prefix thread name", "thread_name"),
    ("prefix_thread_id", "Prefix thread id", "thread_id"),
    ("prefix_log_level", "Prefix log level", "level"),
    ("prefix_primary_keyword", "Prefix primary keyword", "keyword"),
    ("prefix_language", "Prefix active language", "language"),
    ("prefix_beta_state", "Prefix beta state", "beta"),
]


SUFFIX_FEATURE_DATA: List[Tuple[str, str, str]] = [
    ("suffix_message_length", "Suffix message length", "len"),
    ("suffix_word_count", "Suffix word count", "words"),
    ("suffix_char_count", "Suffix character count", "chars"),
    ("suffix_digit_sum", "Suffix digit sum", "digit_sum"),
    ("suffix_numeric_values", "Suffix numeric tokens", "numbers"),
    ("suffix_points_estimate", "Suffix points estimate", "points"),
    ("suffix_keyword_count", "Suffix keyword count", "keyword_count"),
    ("suffix_sequence_index", "Suffix display index", "index"),
    ("suffix_elapsed_minutes", "Suffix elapsed minutes", "elapsed_minutes"),
    ("suffix_elapsed_seconds", "Suffix elapsed seconds", "elapsed_seconds"),
    ("suffix_thread_marker", "Suffix thread marker", "thread_marker"),
    ("suffix_message_hash", "Suffix short hash", "hash"),
    ("suffix_cycle_marker", "Suffix cycle marker", "cycle_flag"),
    ("suffix_summary_pointer", "Suffix summary pointer", "summary_pointer"),
]


TRANSFORM_FEATURE_DATA: List[Tuple[str, str, str]] = [
    ("transform_uppercase_errors", "Uppercase error lines", "uppercase_error"),
    ("transform_uppercase_warnings", "Uppercase warning lines", "uppercase_warning"),
    ("transform_lowercase_info", "Lowercase info lines", "lowercase_info"),
    ("transform_title_case", "Title-case log entries", "title_case"),
    ("transform_emphasize_numbers", "Emphasize numbers", "emphasize_numbers"),
    ("transform_emphasize_keywords", "Emphasize tracked keywords", "emphasize_keywords"),
    ("transform_replace_points", "Rename points → pts", "rename_points"),
    ("transform_pad_brackets", "Pad bracketed values", "pad_brackets"),
    ("transform_strip_whitespace", "Collapse repeated whitespace", "strip_spaces"),
    ("transform_indent_multiline", "Indent multi-line entries", "indent_multiline"),
    ("transform_bullet_prefix", "Add bullet prefix", "bullet"),
    ("transform_capitalize_first", "Capitalize first character", "capitalize_first"),
    ("wrapper_brackets", "Wrap entry with brackets", "wrap_brackets"),
    ("wrapper_chevrons", "Wrap entry with « »", "wrap_chevrons"),
    ("wrapper_pipes", "Wrap entry with pipes", "wrap_pipes"),
    ("wrapper_stars", "Wrap entry with stars", "wrap_stars"),
    ("wrapper_box", "Wrap entry with box edges", "wrap_box"),
    ("wrapper_wave", "Wrap entry with waves", "wrap_wave"),
]


FILTER_FEATURE_DATA: List[Tuple[str, str, Dict[str, object]]] = [
    ("filter_errors_only", "Show only errors and warnings", {"mode": "only_level", "value": "alert"}),
    ("filter_errors_only_strict", "Show only errors", {"mode": "only_level", "value": "error"}),
    ("filter_warnings_only", "Show only warnings", {"mode": "only_level", "value": "warning"}),
    ("filter_hide_info_lines", "Hide info lines", {"mode": "hide_level", "value": "info"}),
    ("filter_hide_success_lines", "Hide success lines", {"mode": "hide_keyword", "value": "done"}),
    ("filter_hide_gpt_lines", "Hide ChatGPT lines", {"mode": "hide_keyword", "value": "gpt"}),
    ("filter_hide_license_lines", "Hide license chatter", {"mode": "hide_keyword", "value": "license"}),
    ("filter_hide_prefetch_lines", "Hide prefetch telemetry", {"mode": "hide_keyword", "value": "prefetch"}),
    ("filter_hide_cycle_lines", "Hide cycle markers", {"mode": "hide_keyword", "value": "cycle"}),
    ("filter_hide_duplicates", "Hide duplicate messages", {"mode": "hide_duplicates", "value": True}),
]


ACTION_FEATURE_DATA: List[Tuple[str, str, str]] = [
    ("action_beep_errors", "Play alert on errors", "beep_error"),
    ("action_beep_warnings", "Play alert on warnings", "beep_warning"),
    ("action_beep_cycles", "Play alert on cycles", "beep_cycle"),
    ("action_copy_errors", "Copy errors to clipboard", "copy_error"),
    ("action_copy_gpt", "Copy ChatGPT replies", "copy_gpt"),
    ("action_copy_done", "Copy completion lines", "copy_done"),
    ("action_focus_errors", "Focus window on errors", "focus_error"),
    ("action_pause_on_errors", "Pause logging on errors", "pause_error"),
    ("action_auto_clear_cycles", "Clear log when cycles change", "clear_cycle"),
    ("action_auto_wrap_long", "Enable wrap for long messages", "wrap_long"),
]


LAYOUT_FEATURE_DATA: List[Tuple[str, str, str]] = [
    ("layout_expand_log_height", "Expand log height", "expand_log"),
    ("layout_compact_panels", "Compact panel padding", "compact_panels"),
    ("layout_bold_headers", "Bolden headers", "bold_headers"),
    ("layout_wide_buttons", "Widen control buttons", "wide_buttons"),
    ("layout_highlight_beta_panel", "Highlight beta panel", "highlight_beta"),
    ("layout_highlight_advanced_panel", "Highlight advanced panel", "highlight_advanced"),
    ("layout_highlight_log_panel", "Highlight log panel", "highlight_log"),
    ("layout_round_controls", "Round control corners", "round_entries"),
    ("layout_dim_background", "Dim panel backgrounds", "dim_panels"),
    ("layout_flat_buttons", "Flatten buttons", "flat_buttons"),
]


SUMMARY_FEATURE_DATA: List[Tuple[str, str, str]] = [
    ("summary_total_logs", "Total log lines", "total"),
    ("summary_error_count", "Error count", "errors"),
    ("summary_warning_count", "Warning count", "warnings"),
    ("summary_info_count", "Info count", "infos"),
    ("summary_last_message", "Last message", "last_message"),
    ("summary_last_error", "Last error", "last_error"),
    ("summary_last_warning", "Last warning", "last_warning"),
    ("summary_last_keyword", "Last highlighted keyword", "last_keyword"),
    ("summary_gpt_mentions", "GPT mentions", "gpt_mentions"),
    ("summary_cycle_mentions", "Cycle mentions", "cycle_mentions"),
    ("summary_task_mentions", "Task mentions", "task_mentions"),
    ("summary_subject_mentions", "Subject mentions", "subject_mentions"),
    ("summary_retry_mentions", "Retry mentions", "retry_mentions"),
    ("summary_skip_mentions", "Skip mentions", "skip_mentions"),
    ("summary_prefetch_mentions", "Prefetch mentions", "prefetch_mentions"),
    ("summary_license_mentions", "License mentions", "license_mentions"),
    ("summary_points_total", "Total numeric points", "points_total"),
    ("summary_duration", "Log duration", "duration"),
    ("summary_average_length", "Average length", "avg_length"),
    ("summary_unique_keywords", "Unique keywords", "unique_keywords"),
    ("summary_done_mentions", "Done mentions", "done_mentions"),
]


GUI_FEATURE_DEFINITIONS: List[GuiFeatureDefinition] = []

for name, label, payload in PREFIX_FEATURE_DATA:
    GUI_FEATURE_DEFINITIONS.append(GuiFeatureDefinition(name, label, "Prefixes", "prefix", payload))

for name, label, payload in SUFFIX_FEATURE_DATA:
    GUI_FEATURE_DEFINITIONS.append(GuiFeatureDefinition(name, label, "Suffixes", "suffix", payload))

for name, label, payload in TRANSFORM_FEATURE_DATA:
    GUI_FEATURE_DEFINITIONS.append(GuiFeatureDefinition(name, label, "Transforms", "transform", payload))

for name, label, payload in FILTER_FEATURE_DATA:
    GUI_FEATURE_DEFINITIONS.append(GuiFeatureDefinition(name, label, "Filters", "filter", payload))

for name, label, payload in ACTION_FEATURE_DATA:
    GUI_FEATURE_DEFINITIONS.append(GuiFeatureDefinition(name, label, "Actions", "action", payload))

for name, label, payload in LAYOUT_FEATURE_DATA:
    GUI_FEATURE_DEFINITIONS.append(GuiFeatureDefinition(name, label, "Layout", "layout", payload))

for name, label, payload in SUMMARY_FEATURE_DATA:
    GUI_FEATURE_DEFINITIONS.append(GuiFeatureDefinition(name, label, "Summary", "summary", payload))

for spec in KEYWORD_SPECS:
    GUI_FEATURE_DEFINITIONS.append(
        GuiFeatureDefinition(
            f"highlight_keyword_{spec.name}",
            f"Highlight {spec.label}",
            "Highlights",
            "keyword-highlight",
            spec.name,
        )
    )
    GUI_FEATURE_DEFINITIONS.append(
        GuiFeatureDefinition(
            f"filter_keyword_{spec.name}",
            f"Show only {spec.label}",
            "Filters",
            "keyword-filter",
            spec.name,
        )
    )


GUI_FEATURE_BY_NAME: Dict[str, GuiFeatureDefinition] = {
    feature.name: feature for feature in GUI_FEATURE_DEFINITIONS
}


GUI_FEATURES_BY_CATEGORY: Dict[str, List[GuiFeatureDefinition]] = {}
for feature in GUI_FEATURE_DEFINITIONS:
    GUI_FEATURES_BY_CATEGORY.setdefault(feature.category, []).append(feature)


GUI_CATEGORY_ORDER = (
    "Prefixes",
    "Suffixes",
    "Transforms",
    "Highlights",
    "Filters",
    "Actions",
    "Layout",
    "Summary",
)


PREFIX_FEATURE_NAMES = [
    feature.name for feature in GUI_FEATURE_DEFINITIONS if feature.kind == "prefix"
]
SUFFIX_FEATURE_NAMES = [
    feature.name for feature in GUI_FEATURE_DEFINITIONS if feature.kind == "suffix"
]
TRANSFORM_FEATURE_NAMES = [
    feature.name for feature in GUI_FEATURE_DEFINITIONS if feature.kind == "transform"
]
FILTER_FEATURE_NAMES = [
    feature.name for feature in GUI_FEATURE_DEFINITIONS if feature.kind == "filter"
]
ACTION_FEATURE_NAMES = [
    feature.name for feature in GUI_FEATURE_DEFINITIONS if feature.kind == "action"
]
LAYOUT_FEATURE_NAMES = [
    feature.name for feature in GUI_FEATURE_DEFINITIONS if feature.kind == "layout"
]
SUMMARY_FEATURE_NAMES = [
    feature.name for feature in GUI_FEATURE_DEFINITIONS if feature.kind == "summary"
]
KEYWORD_HIGHLIGHT_NAMES = [
    feature.name for feature in GUI_FEATURE_DEFINITIONS if feature.kind == "keyword-highlight"
]
KEYWORD_FILTER_NAMES = [
    feature.name for feature in GUI_FEATURE_DEFINITIONS if feature.kind == "keyword-filter"
]


def detect_log_level(message: str) -> str:
    lower = message.lower()
    if "❌" in message or "error" in lower or "nepareiz" in lower:
        return "error"
    if "⚠" in message or "warn" in lower:
        return "warning"
    return "info"


def match_keywords(message: str) -> Set[str]:
    lower = message.lower()
    hits: Set[str] = set()
    for spec in KEYWORD_SPECS:
        if any(token in lower for token in spec.tokens):
            hits.add(spec.name)
    return hits


def format_duration(seconds: float) -> str:
    total_seconds = max(0, int(seconds))
    minutes, secs = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h{minutes:02d}m{secs:02d}s"
    if minutes:
        return f"{minutes}m{secs:02d}s"
    return f"{secs}s"


def _join_non_empty(parts: List[str], sep: str = " ") -> str:
    filtered = [part for part in parts if part]
    return sep.join(filtered)


def _format_delta(prev: Optional[datetime], current: datetime) -> str:
    if not prev:
        return ""
    delta = (current - prev).total_seconds()
    if delta == 0:
        return "Δ0.000s"
    sign = "-" if delta < 0 else ""
    delta = abs(delta)
    if delta >= 60:
        minutes, secs = divmod(delta, 60)
        return f"Δ{sign}{int(minutes)}m{secs:04.1f}s"
    return f"Δ{sign}{delta:.3f}s"


def _format_from_start(start: Optional[datetime], current: datetime) -> str:
    if not start:
        return ""
    delta = (current - start).total_seconds()
    return f"T+{format_duration(delta)}"


PREFIX_RENDERERS: Dict[str, Callable[[GuiLogEntry, Dict[str, object]], str]] = {
    "time_ms": lambda entry, ctx: entry.timestamp.strftime("%H:%M:%S.%f")[:-3],
    "time_sec": lambda entry, ctx: entry.timestamp.strftime("%H:%M:%S"),
    "date_short": lambda entry, ctx: entry.timestamp.strftime("%Y-%m-%d"),
    "date_long": lambda entry, ctx: entry.timestamp.strftime("%A"),
    "iso": lambda entry, ctx: entry.timestamp.isoformat(timespec="seconds"),
    "delta_prev": lambda entry, ctx: _format_delta(ctx.get("previous_timestamp"), entry.timestamp),
    "delta_start": lambda entry, ctx: _format_from_start(ctx.get("first_timestamp"), entry.timestamp),
    "sequence": lambda entry, ctx: f"#{entry.sequence}",
    "thread_name": lambda entry, ctx: entry.thread_name or "thread",
    "thread_id": lambda entry, ctx: str(entry.thread_id),
    "level": lambda entry, ctx: entry.level.upper(),
    "keyword": lambda entry, ctx: ctx.get("primary_keyword_label", ""),
    "language": lambda entry, ctx: ctx.get("language", ""),
    "beta": lambda entry, ctx: ctx.get("beta_state", ""),
}


def _suffix_points(entry: GuiLogEntry) -> str:
    matches = POINTS_PATTERN.findall(entry.text)
    if not matches:
        return ""
    total = sum(float(value.replace(",", ".")) for value in matches)
    return f"(pts~:{total:.1f})"


SUFFIX_RENDERERS: Dict[str, Callable[[GuiLogEntry, Dict[str, object]], str]] = {
    "len": lambda entry, ctx: f"(len:{len(entry.text)})",
    "words": lambda entry, ctx: f"(words:{len(entry.text.split())})",
    "chars": lambda entry, ctx: f"(chars:{len(entry.text)})",
    "digit_sum": lambda entry, ctx: f"(∑digits:{sum(int(ch) for ch in entry.text if ch.isdigit())})",
    "numbers": lambda entry, ctx: "[" + ",".join(re.findall(r"-?\\d+(?:[.,]\\d+)?", entry.text)) + "]" if re.search(r"-?\\d", entry.text) else "",
    "points": lambda entry, ctx: _suffix_points(entry),
    "keyword_count": lambda entry, ctx: f"(keys:{len(entry.keywords)})" if entry.keywords else "",
    "index": lambda entry, ctx: f"(idx:{ctx.get('display_index', 0) + 1})",
    "elapsed_minutes": lambda entry, ctx: f"(+{int(max(0.0, (entry.timestamp - ctx.get('first_timestamp', entry.timestamp)).total_seconds()) // 60)}m)",
    "elapsed_seconds": lambda entry, ctx: f"(+{int(max(0.0, (entry.timestamp - ctx.get('first_timestamp', entry.timestamp)).total_seconds()))}s)",
    "thread_marker": lambda entry, ctx: f"(thread:{entry.thread_name})" if entry.thread_name else "",
    "hash": lambda entry, ctx: f"#H{hashlib.md5(entry.text.encode('utf-8')).hexdigest()[:4]}",
    "cycle_flag": lambda entry, ctx: "[cycle]" if "cycle" in entry.text.lower() else "",
    "summary_pointer": lambda entry, ctx: "[Σ]" if ctx.get("summary_enabled") else "",
}


def _wrap_numbers(text: str) -> str:
    return re.sub(r"(-?\\d+(?:[.,]\\d+)?)", r"⟦\\1⟧", text)


def _emphasize_keywords(text: str, entry: GuiLogEntry) -> str:
    result = text
    for name in entry.keywords:
        spec = KEYWORD_SPEC_BY_NAME.get(name)
        if not spec:
            continue
        for token in spec.tokens:
            if token.strip() and re.search(re.escape(token), result, flags=re.IGNORECASE):
                result = re.sub(re.escape(token), lambda m: m.group(0).upper(), result, flags=re.IGNORECASE)
                break
    return result


TRANSFORM_HANDLERS: Dict[str, Callable[[str, GuiLogEntry], str]] = {
    "uppercase_error": lambda text, entry: text.upper() if entry.level == "error" else text,
    "uppercase_warning": lambda text, entry: text.upper() if entry.level == "warning" else text,
    "lowercase_info": lambda text, entry: text.lower() if entry.level == "info" else text,
    "title_case": lambda text, entry: text.title(),
    "emphasize_numbers": lambda text, entry: _wrap_numbers(text),
    "emphasize_keywords": lambda text, entry: _emphasize_keywords(text, entry),
    "rename_points": lambda text, entry: re.sub(r"points", "pts", text, flags=re.IGNORECASE),
    "pad_brackets": lambda text, entry: re.sub(r"\[(.*?)\]", r"[ \1 ]", text),
    "strip_spaces": lambda text, entry: " ".join(text.split()),
    "indent_multiline": lambda text, entry: text if "\n" not in text else "\n".join([text.split("\n", 1)[0]] + ["    " + part for part in text.split("\n")[1:]]),
    "bullet": lambda text, entry: f"• {text}",
    "capitalize_first": lambda text, entry: text[:1].upper() + text[1:] if text else text,
    "wrap_brackets": lambda text, entry: f"[ {text} ]",
    "wrap_chevrons": lambda text, entry: f"« {text} »",
    "wrap_pipes": lambda text, entry: f"| {text} |",
    "wrap_stars": lambda text, entry: f"★ {text} ★",
    "wrap_box": lambda text, entry: f"┏ {text} ┛",
    "wrap_wave": lambda text, entry: f"≈ {text} ≈",
}


SUMMARY_RENDERERS: Dict[str, Callable[[Dict[str, object]], str]] = {
    "total": lambda stats: f"Logs: {stats['total']}" if stats["total"] else "",
    "errors": lambda stats: f"Errors: {stats['errors']}" if stats["errors"] else "",
    "warnings": lambda stats: f"Warnings: {stats['warnings']}" if stats["warnings"] else "",
    "infos": lambda stats: f"Info: {stats['infos']}" if stats["infos"] else "",
    "last_message": lambda stats: f"Last: {stats['last_message']}" if stats.get("last_message") else "",
    "last_error": lambda stats: f"Last error: {stats['last_error']}" if stats.get("last_error") else "",
    "last_warning": lambda stats: f"Last warning: {stats['last_warning']}" if stats.get("last_warning") else "",
    "last_keyword": lambda stats: f"Keyword: {stats['last_keyword']}" if stats.get("last_keyword") else "",
    "gpt_mentions": lambda stats: f"GPT: {stats['keyword_counts'].get('gpt', 0)}" if stats['keyword_counts'].get("gpt") else "",
    "cycle_mentions": lambda stats: f"Cycles: {stats['keyword_counts'].get('cycle', 0)}" if stats['keyword_counts'].get("cycle") else "",
    "task_mentions": lambda stats: f"Tasks: {stats['keyword_counts'].get('task', 0)}" if stats['keyword_counts'].get("task") else "",
    "subject_mentions": lambda stats: f"Subjects: {stats['keyword_counts'].get('subject', 0)}" if stats['keyword_counts'].get("subject") else "",
    "retry_mentions": lambda stats: f"Retries: {stats['keyword_counts'].get('retry', 0)}" if stats['keyword_counts'].get("retry") else "",
    "skip_mentions": lambda stats: f"Skips: {stats['keyword_counts'].get('skip', 0)}" if stats['keyword_counts'].get("skip") else "",
    "prefetch_mentions": lambda stats: f"Prefetch: {stats['keyword_counts'].get('prefetch', 0)}" if stats['keyword_counts'].get("prefetch") else "",
    "license_mentions": lambda stats: f"License: {stats['keyword_counts'].get('license', 0)}" if stats['keyword_counts'].get("license") else "",
    "points_total": lambda stats: f"Σpts: {stats['points_total']:.1f}" if stats["points_total"] else "",
    "duration": lambda stats: f"Span: {format_duration(stats['duration'])}" if stats.get("duration") else "",
    "avg_length": lambda stats: f"Avg len: {stats['avg_length']:.0f}" if stats.get("avg_length") else "",
    "unique_keywords": lambda stats: f"Keywords: {stats['unique_keywords']}" if stats.get("unique_keywords") else "",
    "done_mentions": lambda stats: f"Done: {stats['keyword_counts'].get('done', 0)}" if stats['keyword_counts'].get("done") else "",
}


BETA_STATE: Optional[BetaState] = None


def activate_beta(overrides: Optional[Dict[str, bool]] = None) -> BetaState:
    global BETA_STATE
    state = BetaState(enabled=True)
    features: List[str] = []
    for name in BETA_FEATURE_NAMES:
        value = getattr(state.config, name, False)
        if overrides and name in overrides:
            value = overrides[name]
            setattr(state.config, name, value)
        if value:
            features.append(name)
    state.features = features
    BETA_STATE = state
    return state


def deactivate_beta() -> None:
    global BETA_STATE
    BETA_STATE = None


@lru_cache(maxsize=512)
def _translation_cache(lang: str, key: str) -> str:
    pack = I18N.get(lang, I18N["lv"])
    return pack.get(key, key)


POINTS_PATTERN = re.compile(r"(\d+[.,]?\d*)")
INTEGER_PATTERN = re.compile(r"\d+")
LETTER_PATTERN = re.compile(r"\b([A-Za-z])\b")
TOKEN_PATTERN = re.compile(r"-?\d+(?:[.,]\d+)?|[A-Za-zĀ-ž]+")
LEADING_INDEX_PATTERN = re.compile(r"^\s*\d+[\)\.-:]*\s*")


def T(lang: str, key: str, **kwargs) -> str:
    pack = I18N.get(lang, I18N["lv"])
    use_cache = bool(BETA_STATE and BETA_STATE.config.translation_cache and not kwargs)
    base = _translation_cache(lang, key) if use_cache else pack.get(key, key)
    return base.format(**kwargs) if kwargs else base

# ----------------------- Credential helpers ------------


def load_saved_credentials() -> Tuple[Optional[str], Optional[str]]:
    try:
        if not CREDS_FILE.exists():
            return None, None
        with CREDS_FILE.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        user = data.get("user")
        pw_blob = data.get("password")
        if not user or not pw_blob:
            return None, None
        password = base64.b64decode(pw_blob.encode("utf-8")).decode("utf-8")
        return user, password
    except Exception:
        return None, None

def save_credentials(user: str, password: str) -> None:
    if not user or not password:
        return
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        blob = base64.b64encode(password.encode("utf-8")).decode("utf-8")
        with CREDS_FILE.open("w", encoding="utf-8") as fh:
            json.dump({"user": user, "password": blob}, fh)
    except Exception:
        pass

def clear_saved_credentials() -> None:
    try:
        if CREDS_FILE.exists():
            CREDS_FILE.unlink()
    except Exception:
        pass

# ----------------------- Data classes -------------------

@dataclass
class TaskOption:
    index: int
    text: str
    option_type: str
    input_element: object
    label_element: object


@dataclass
class TaskData:
    text: str
    options: List[TaskOption]
    points_label: str
    dropdown_texts: List[List[str]]
    dropdown_ids: List[Optional[str]]


@dataclass
class TaskLink:
    anchor: object
    title: str
    href: str


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


def log_message(message: str, logger: Logger = None) -> None:
    if BETA_STATE and BETA_STATE.config.structured_logging:
        timestamp = time.strftime("%H:%M:%S")
        if not message.startswith("["):
            message = f"[{timestamp}] {message}"
    print(message)
    if logger:
        try:
            logger(message)
        except Exception:
            pass


def w(driver, css, timeout=7, cond="present"):
    try:
        cond_map = {
            "present": EC.presence_of_element_located,
            "visible": EC.visibility_of_element_located,
            "clickable": EC.element_to_be_clickable,
        }
        adjusted = timeout
        if BETA_STATE and BETA_STATE.config.wait_optimization:
            adjusted = max(2, min(timeout, 6))
        return WebDriverWait(driver, adjusted).until(cond_map[cond]((By.CSS_SELECTOR, css)))
    except TimeoutException:
        return None


def w_all(driver, css, timeout=7, visible_only=False):
    try:
        adjusted = timeout
        if BETA_STATE and BETA_STATE.config.wait_optimization:
            adjusted = max(2, min(timeout, 6))
        elements = WebDriverWait(driver, adjusted).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, css))
        )
        if visible_only:
            elements = [e for e in elements if e.is_displayed()]
        return elements
    except TimeoutException:
        return []


def js_click(driver, element):
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


def collect_driver_cookies(driver) -> Dict[str, str]:
    jar: Dict[str, str] = {}
    try:
        for cookie in driver.get_cookies():
            name = cookie.get("name")
            value = cookie.get("value")
            if name and value is not None:
                jar[name] = value
    except Exception:
        pass
    return jar


def get_driver_user_agent(driver) -> str:
    try:
        ua = driver.execute_script("return navigator.userAgent;")
        if isinstance(ua, str) and ua.strip():
            return ua
    except Exception:
        pass
    return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"


def remote_preview_contains_media(html: str) -> bool:
    if not html:
        return False
    snippet = html.lower()
    marker = "#taskhtml"
    if marker in snippet:
        snippet = snippet.split(marker, 1)[1]
    for token in REMOTE_MEDIA_PATTERNS:
        if token in snippet:
            return True
    return False


def prefetch_task_links(driver, candidates: List[TaskLink], lang: str, logger: Logger = None) -> List[TaskLink]:
    if not candidates:
        return []
    log_message(T(lang, "prefetch_scan"), logger)

    cookies = collect_driver_cookies(driver)
    headers = {"User-Agent": get_driver_user_agent(driver)}
    base_url = driver.current_url

    def worker(link: TaskLink) -> Tuple[TaskLink, str]:
        href = link.href
        if not href:
            return link, "error"
        target = urljoin(base_url, href)
        try:
            response = requests.get(
                target,
                headers=headers,
                cookies=cookies,
                timeout=REMOTE_TASK_SCAN_TIMEOUT,
                allow_redirects=True,
            )
            if response.status_code >= 400:
                return link, "error"
            has_media = remote_preview_contains_media(response.text)
            return link, "skip" if has_media else "ok"
        except Exception:
            return link, "error"

    max_workers = min(8, len(candidates)) or 1
    ok_links: List[TaskLink] = []
    skip_count = 0
    error_count = 0
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(worker, link): link for link in candidates}
        for future in as_completed(futures):
            link, status = future.result()
            if status == "ok":
                ok_links.append(link)
            elif status == "skip":
                skip_count += 1
            else:
                error_count += 1

    if skip_count:
        if BETA_STATE and BETA_STATE.config.task_skip_counter:
            for _ in range(skip_count):
                BETA_STATE.mark_skip()
        log_message(f"{T(lang, 'prefetch_skip')} ({skip_count})", logger)
    if error_count and not ok_links:
        log_message(f"{T(lang, 'prefetch_none')} ({error_count})", logger)
    elif not ok_links:
        log_message(T(lang, "prefetch_none"), logger)
    else:
        log_message(f"{T(lang, 'prefetch_ok')} ({len(ok_links)})", logger)
    return ok_links or candidates


def build_fast_driver(incognito=True, new_window=False, block_images=True):
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
    if BETA_STATE and BETA_STATE.config.driver_acceleration:
        options.add_argument("--disable-component-update")
        options.add_argument("--disable-sync")
        options.add_argument("--disable-background-networking")
        options.add_argument("--disable-ipc-flooding-protection")
        options.add_argument("--disable-features=TranslateUI,InterestFeedContentSuggestions")
        options.add_argument("--dns-prefetch-disable")
        options.add_argument("--mute-audio")
        options.add_argument("--disable-logging")
    if block_images:
        prefs = {"profile.managed_default_content_settings.images": 2}
        options.add_experimental_option("prefs", prefs)
    driver = uc.Chrome(options=options)
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
        except Exception as e:
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
                delay = 0.5
                if BETA_STATE and BETA_STATE.config.auto_recovery_backoff:
                    delay = max(0.2, 0.3 + 0.05 * attempt)
                time.sleep(delay)
                continue
            raise

# ----------------------- Points helpers ------------------

def parse_points_label(label: str) -> float:
    if not label:
        return 0.0
    if BETA_STATE and BETA_STATE.config.regex_cache:
        m = POINTS_PATTERN.search(label)
    else:
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
        if BETA_STATE and BETA_STATE.config.regex_cache:
            m = INTEGER_PATTERN.search(txt.replace(" ", ""))
        else:
            m = re.search(r"\d+", txt.replace(" ", ""))
        if m:
            return int(m.group(0))
    except Exception:
        return None
    return None

# ----------------------- Cosmetic: hide media ------------

HIDE_MEDIA_CSS = """
* { image-rendering: auto !important; }
img, .gxs-resource-image, .gxst-resource-image, .gxs-dnd-option,
[style*="background-image"], .answer-box, .ui-draggable, .taskhtmlwrapper .image, .taskhtmlwrapper figure {
  display: none !important;
}
"""


def apply_hide_media_css(driver):
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

    def burn_trial(self):
        if not is_windows():
            return
        reg_write("TrialBurned", "1")
        reg_write("TrialStartEpoch", "0")
        log_message(T(self.lang, "lic_burned"), self.logger)

    def _stored(self):
        return (
            reg_read("LicenseUser") or "",
            reg_read("LicenseKey") or "",
            reg_read("LicenseHWID") or "",
        )

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
        except Exception as e:
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
                    return {"state": "licensed", "user": js.get("user") or ks_user, "left_seconds": None}
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
    ):
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


def decline_cookies(driver, lang, logger: Logger = None):
    domain = None
    if BETA_STATE and BETA_STATE.config.cookie_guard:
        try:
            domain = urlsplit(driver.current_url).netloc
        except Exception:
            domain = None
        if domain and domain in BETA_STATE.last_cookie_decline:
            apply_hide_media_css(driver)
            return
    try:
        btn = WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#CybotCookiebotDialogBodyButtonDecline"))
        )
        js_click(driver, btn)
        log_message(T(lang, "cookies_declined"), logger)
        if domain and BETA_STATE:
            BETA_STATE.last_cookie_decline.add(domain)
    except TimeoutException:
        pass
    apply_hide_media_css(driver)


def login(driver, user, password, lang, logger: Logger = None):
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


def select_task(driver, lang, logger: Logger = None):
    log_message(T(lang, "find_subject"), logger)
    use_cache = bool(BETA_STATE and BETA_STATE.config.cached_subjects and BETA_STATE.subject_catalog)
    if use_cache:
        catalog = BETA_STATE.subject_catalog
        pool = catalog
        if BETA_STATE and BETA_STATE.config.subject_rotation:
            unused = [item for item in catalog if item[1] not in BETA_STATE.used_subjects]
            if unused:
                pool = unused
            else:
                BETA_STATE.used_subjects.clear()
        href, title = random.choice(pool)
        driver.get(href)
        if BETA_STATE:
            BETA_STATE.used_subjects.add(title)
    else:
        driver.get("https://www.uzdevumi.lv/p")
        apply_hide_media_css(driver)
        decline_cookies(driver, lang, logger)
        subjects_list = w(driver, "ul.list-unstyled.thumbnails", 10)
        if not subjects_list:
            raise RuntimeError("Subjects list missing")
        candidates = subjects_list.find_elements(By.CSS_SELECTOR, "li.thumb.wide a[href]")
        subjects = []
        catalog: List[Tuple[str, str]] = []
        for anchor in candidates:
            if not anchor.is_displayed():
                continue
            title = anchor.text.replace("\n", " ").strip()
            if not title:
                continue
            tnorm = title.lower()
            if title in EXCLUDE_SUBJECTS or "starpbrīdis" in tnorm or "konkurs" in tnorm:
                continue
            href = anchor.get_attribute("href")
            if not href:
                continue
            subjects.append((anchor, title, href))
            catalog.append((href, title))
        if not subjects:
            raise RuntimeError("No suitable subjects")
        if BETA_STATE and BETA_STATE.config.cached_subjects:
            BETA_STATE.subject_catalog = catalog
        anchor, title, href = random.choice(subjects)
        if BETA_STATE and BETA_STATE.config.cached_subjects:
            driver.get(href)
            if BETA_STATE:
                BETA_STATE.used_subjects.add(title)
        else:
            js_click(driver, anchor)
    log_message(T(lang, "subject", x=title), logger)
    apply_hide_media_css(driver)
    decline_cookies(driver, lang, logger)
    try:
        js_click(driver, driver.find_element(By.CSS_SELECTOR, ".ui-button"))
    except Exception:
        pass
    topics = [e for e in w_all(driver, "ol.list-unstyled a[href]", 10) if e.is_displayed()]
    if not topics:
        raise RuntimeError("No topics")
    chosen_topic = random.choice(topics)
    log_message(T(lang, "topic", x=chosen_topic.text.strip()), logger)
    js_click(driver, chosen_topic)
    apply_hide_media_css(driver)
    decline_cookies(driver, lang, logger)
    container = None
    for selector in (
        "section.block:nth-child(2) > div:nth-child(2)",
        "section.block:nth-child(1) > div:nth-child(2)",
    ):
        container = w(driver, selector, 8, "visible")
        if container:
            break
    if not container:
        raise RuntimeError("No tasks container")
    raw_tasks = [e for e in container.find_elements(By.CSS_SELECTOR, "a[href]") if e.is_displayed()]
    task_links: List[TaskLink] = []
    for element in raw_tasks:
        href = element.get_attribute("href") or ""
        if not href:
            continue
        title = element.text.strip() or href
        task_links.append(TaskLink(anchor=element, title=title, href=href))
    if not task_links:
        raise RuntimeError("No task links")
    filtered_links = prefetch_task_links(driver, task_links, lang, logger)
    selected = random.choice(filtered_links)
    log_message(T(lang, "task", x=selected.title.strip()), logger)
    try:
        js_click(driver, selected.anchor)
    except Exception:
        driver.get(selected.href)
    apply_hide_media_css(driver)
    decline_cookies(driver, lang, logger)


def fetch_task(driver, lang, logger: Logger = None) -> Optional[TaskData]:
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
    if (
        BETA_STATE
        and BETA_STATE.config.skip_zero_point_tasks
        and parse_points_label(points_label) <= 0
    ):
        BETA_STATE.mark_skip()
        return "SKIP"
    media = wrapper.find_elements(
        By.CSS_SELECTOR,
        "img,[style*='background-image'],.gxs-resource-image,.gxst-resource-image,.gxs-dnd-option,.answer-box,.ui-draggable",
    )
    if media:
        log_message(T(lang, "img_task_skip"), logger)
        if BETA_STATE:
            BETA_STATE.mark_skip()
        return "SKIP"
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
    )

# ----------------------- GPT session --------------------


class ChatGPTSession:
    MAX_RECOVERY_ATTEMPTS = 2

    def __init__(self, lang: str, logger: Logger = None):
        self.lang = lang
        self.logger = logger
        self.msg_count = 0
        self.driver = None
        self._build_driver()

    def _build_driver(self):
        try:
            if self.driver:
                try:
                    self.driver.quit()
                except Exception:
                    pass
        finally:
            self.driver = build_fast_driver(incognito=True, new_window=True, block_images=False)
        try:
            self.driver.set_page_load_timeout(30)
        except Exception:
            pass
        self.driver.get("https://chat.openai.com/")
        self._dismiss_small_button()
        self._maybe_click_radix_link()

    def _dismiss_small_button(self):
        try:
            small_btn = WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.text-sm:nth-child(2)"))
            )
            js_click(self.driver, small_btn)
            time.sleep(0.2)
        except TimeoutException:
            pass
        except Exception:
            pass

    def _maybe_click_radix_link(self):
        for selector in (
            "#radix-_r_10_ > div > div > a",
            "#radix-_r_19_ > div > div > a",
        ):
            try:
                el = WebDriverWait(self.driver, 2).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                js_click(self.driver, el)
            except TimeoutException:
                continue
            except Exception:
                continue

    def _ensure_alive(self):
        try:
            handles = self.driver.window_handles
            if not handles:
                raise NoSuchWindowException("No window")
        except Exception:
            try:
                self.close()
            except Exception:
                pass
            self._build_driver()
            try:
                self.driver.delete_all_cookies()
                self.driver.get("https://chat.openai.com/")
                self._dismiss_small_button()
                self._maybe_click_radix_link()
            except Exception:
                pass

    def _clear_cookies_and_reload(self):
        try:
            self.driver.delete_all_cookies()
        except Exception:
            pass
        try:
            self.driver.get("https://chat.openai.com/")
        except Exception:
            self._build_driver()
        self._dismiss_small_button()
        self._maybe_click_radix_link()

    def _with_driver_recovery(self, fn: Callable[[], str]) -> str:
        attempt = 0
        while True:
            try:
                return fn()
            except (NoSuchWindowException, WebDriverException, TimeoutException) as exc:
                attempt += 1
                if attempt > self.MAX_RECOVERY_ATTEMPTS:
                    raise
                log_message(T(self.lang, "retry", a=attempt, b=self.MAX_RECOVERY_ATTEMPTS), self.logger)
                self._build_driver()
            except Exception:
                raise

    def _count_user_messages(self) -> int:
        try:
            bubbles = self.driver.find_elements(By.CSS_SELECTOR, "div[data-message-author-role='user']")
            return len(bubbles)
        except Exception:
            return 0

    def _ensure_message_sent(self, before_count: int) -> None:
        for _ in range(40):
            time.sleep(0.25)
            after = self._count_user_messages()
            if after > before_count:
                return
        raise RuntimeError("ChatGPT send button did not register the message")

    def refresh(self):
        self._ensure_alive()
        try:
            self.driver.get("https://chat.openai.com/")
            self._dismiss_small_button()
            self._maybe_click_radix_link()
        except Exception:
            self._build_driver()

    def close(self):
        try:
            if self.driver:
                self.driver.quit()
        except Exception:
            pass
        finally:
            self.driver = None

    def ask(self, prompt: str) -> str:
        return self._with_driver_recovery(lambda: self._ask_once(prompt))

    def _ask_once(self, prompt: str) -> str:
        self._ensure_alive()
        self.msg_count += 1
        threshold = 3
        if BETA_STATE and BETA_STATE.config.gpt_refresh_strategy:
            threshold = 5
        if self.msg_count % threshold == 0:
            self._clear_cookies_and_reload()
        else:
            self.refresh()

        log_message(T(self.lang, "open_gpt"), self.logger)

        self._maybe_click_radix_link()

        pm = w(self.driver, "div#prompt-textarea.ProseMirror[contenteditable='true']", 18, "visible")
        fb = None if pm else w(self.driver, "textarea[name='prompt-textarea']", 3, "present")
        if not pm and not fb:
            self._maybe_click_radix_link()
            pm = w(self.driver, "div#prompt-textarea.ProseMirror[contenteditable='true']", 6, "visible")
            fb = None if pm else w(self.driver, "textarea[name='prompt-textarea']", 3, "present")
            if not pm and not fb:
                raise RuntimeError("ChatGPT composer not found")

        if pm:
            self.driver.execute_script(
                """
                const el = arguments[0], txt = arguments[1];
                el.scrollIntoView({block:'center'}); el.focus();
                if (!el.querySelector('p')) { const p = document.createElement('p'); p.appendChild(document.createElement('br')); el.appendChild(p); }
                const range = document.createRange(); range.selectNodeContents(el);
                const sel = window.getSelection(); sel.removeAllRanges(); sel.addRange(range);
                document.execCommand('selectAll', false, null);
                document.execCommand('insertText', false, txt);
                el.dispatchEvent(new InputEvent('input', {bubbles: true}));
            """,
                pm,
                prompt,
            )
        else:
            self.driver.execute_script(
                """
                const el = arguments[0], txt = arguments[1];
                el.value = txt; el.dispatchEvent(new Event('input', {bubbles: true}));
            """,
                fb,
                prompt,
            )

        send_btn = w(self.driver, "#composer-submit-button", 8, "clickable")
        user_count_before = self._count_user_messages()
        if send_btn:
            js_click(self.driver, send_btn)
        else:
            (pm or fb).send_keys(Keys.ENTER)

        self._ensure_message_sent(user_count_before)

        log_message(T(self.lang, "sent_gpt"), self.logger)

        response_text = ""
        stable = ""
        stable_count = 0
        iterations = 120
        delay = 0.35
        if BETA_STATE and BETA_STATE.config.gpt_refresh_strategy:
            iterations = 100
            delay = 0.3
        for _ in range(iterations):
            time.sleep(delay)
            bubbles = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div[data-message-author-role='assistant'] .markdown.prose, "
                "div.markdown.prose.dark\\:prose-invert.w-full.break-words.dark.markdown-new-styling",
            )
            if not bubbles:
                self._maybe_click_radix_link()
                continue
            response_text = bubbles[-1].text.strip()
            if response_text == stable and response_text:
                stable_count += 1
            else:
                stable = response_text
                stable_count = 0
            limit = 3
            if BETA_STATE and BETA_STATE.config.gpt_refresh_strategy:
                limit = 2
            if stable_count >= limit:
                break

        log_message(
            T(
                self.lang,
                "gpt_ans",
                x=(response_text[:80] + ("…" if len(response_text) > 80 else "")),
            ),
            self.logger,
        )
        return response_text

# ----------------------- Prompt / parser -----------------

def build_prompt(task: TaskData, lang: str) -> str:
    header_lines = [
        T(lang, "p1"),
        T(lang, "p2"),
        T(lang, "p3"),
        T(lang, "p4"),
        T(lang, "p5"),
        T(lang, "p6"),
        T(lang, "p7"),
        "",
        T(lang, "p8"),
    ]
    if BETA_STATE and BETA_STATE.config.gpt_prompt_cache:
        header = BETA_STATE.prompt_headers.get(lang)
        if header is None:
            header = "\n".join(header_lines)
            BETA_STATE.prompt_headers[lang] = header
        parts = [header, task.text]
    else:
        parts = header_lines + [task.text]
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

    if task.dropdown_texts:
        values: List[int] = []
        for i, options_texts in enumerate(task.dropdown_texts):
            line = lines[i] if i < len(lines) else ""
            chosen_idx = None
            if BETA_STATE and BETA_STATE.config.regex_cache:
                mnum = INTEGER_PATTERN.findall(line)
            else:
                mnum = re.findall(r"\d+", line)
            if mnum:
                k = int(mnum[0])
                if 1 <= k <= len(options_texts):
                    chosen_idx = k
            if chosen_idx is None:
                if BETA_STATE and BETA_STATE.config.regex_cache:
                    mlet = LETTER_PATTERN.findall(line)
                else:
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
            if BETA_STATE and BETA_STATE.config.regex_cache:
                digits = INTEGER_PATTERN.findall(line)
            else:
                digits = re.findall(r"\d+", line)
            for d in digits:
                i = int(d)
                if i in option_map and i not in selected:
                    selected.append(i)
            if BETA_STATE and BETA_STATE.config.regex_cache:
                letters = LETTER_PATTERN.findall(line)
            else:
                letters = re.findall(r"\b([A-Za-z])\b", line)
            for L in letters:
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
        if BETA_STATE and BETA_STATE.config.parse_answer_fallbacks:
            core = LEADING_INDEX_PATTERN.sub("", line)
        else:
            core = re.sub(r"^\s*\d+[\)\.-:]*\s*", "", line)
        if BETA_STATE and BETA_STATE.config.regex_cache:
            parts = TOKEN_PATTERN.findall(core)
        else:
            parts = re.findall(r"-?\d+(?:[.,]\d+)?|[A-Za-zĀ-ž]+", core)
        tokens.extend(parts)
    if not tokens:
        if BETA_STATE and BETA_STATE.config.regex_cache:
            tokens = [match for match in TOKEN_PATTERN.findall(answer) if match.strip()]
        else:
            tokens = re.findall(r"-?\d+(?:[.,]\d+)?", answer)
    return {"mode": "text", "values": tokens}

# ----------------------- Fillers ------------------------

def fill_in_answers(driver, values: List[str], lang, logger: Logger = None):
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
            val = str(values[idx])
            if BETA_STATE and BETA_STATE.config.text_input_normalization:
                val = val.strip()
            element.send_keys(val)
        except Exception:
            continue
    submit_button = w(driver, "#submitAnswerBtn", 6, "clickable")
    if submit_button is not None:
        if BETA_STATE and BETA_STATE.config.safe_submit:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_button)
        js_click(driver, submit_button)
        log_message(T(lang, "submitted"), logger)
    else:
        log_message(T(lang, "no_btn"), logger)


def select_answers(driver, task: TaskData, indexes: List[int], lang, logger: Logger = None):
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
            if BETA_STATE and BETA_STATE.config.safe_submit:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_button)
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
            if BETA_STATE and BETA_STATE.config.dropdown_selection_guard:
                idx = max(1, min(len(opts), idx)) if opts else 1
            if 1 <= idx <= len(opts):
                s.select_by_visible_text(opts[idx - 1])
            else:
                s.select_by_index(max(1, min(len(opts), idx)))
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
                if BETA_STATE and BETA_STATE.config.dropdown_selection_guard:
                    idx = max(1, min(len(opts), idx)) if opts else 1
                if 1 <= idx <= len(opts):
                    s2.select_by_visible_text(opts[idx - 1])
                else:
                    s2.select_by_index(max(1, min(len(opts), idx)))
            except Exception:
                continue
        except Exception:
            continue
    submit_button = w(driver, "#submitAnswerBtn", 6, "clickable")
    if submit_button is not None:
        if BETA_STATE and BETA_STATE.config.safe_submit:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_button)
        js_click(driver, submit_button)
        log_message(T(lang, "submitted"), logger)
    else:
        log_message(T(lang, "no_btn"), logger)


def detect_submission_feedback(driver) -> str:
    try:
        time.sleep(0.3)
        source = driver.page_source.lower()
    except Exception:
        return "unknown"
    for token in CORRECT_FEEDBACK_TOKENS:
        if token in source:
            return "correct"
    for token in INCORRECT_FEEDBACK_TOKENS:
        if token in source:
            return "incorrect"
    return "unknown"


# ----------------------- Orchestrator -------------------

def solve_one_task(main_driver, gpt: ChatGPTSession, lang, logger: Logger = None) -> float:
    def select_and_fetch():
        select_task(main_driver, lang, logger)
        return fetch_task(main_driver, lang, logger)

    task: Optional[TaskData] = None
    for _ in range(12):
        task = select_and_fetch()
        if task == "SKIP":
            if BETA_STATE and BETA_STATE.config.task_skip_counter:
                BETA_STATE.mark_skip()
            log_message("↻ …", logger)
            continue
        if task is None:
            log_message("⚠  fetch failed, retry…", logger)
            continue
        break

    if not isinstance(task, TaskData):
        log_message(T(lang, "no_valid"), logger)
        return 0.0

    base_points = parse_points_label(task.points_label)
    max_attempts = SMART_RETRY_MAX_ATTEMPTS if base_points > SMART_RETRY_THRESHOLD else 1
    attempt_index = 0
    feedback = "unknown"

    while attempt_index < max_attempts:
        prompt = build_prompt(task, lang)
        if attempt_index:
            prompt += (
                f"\n\nAttempt #{attempt_index + 1}: Previous submission might be wrong. "
                "Re-evaluate carefully and provide a different final answer."
            )
        try:
            answer = gpt.ask(prompt)
        except Exception as exc:
            log_message(f"❌ {exc}", logger)
            return 0.0
        parsed = parse_answer(answer, task)

        if parsed["mode"] == "dropdowns" and task.dropdown_texts:
            fill_dropdowns(
                main_driver,
                task.dropdown_texts,
                task.dropdown_ids,
                parsed["values"],
                lang,
                logger,
            )
        elif parsed["mode"] == "select" and task.options:
            select_answers(main_driver, task, parsed["values"], lang, logger)
        elif parsed["mode"] == "text" and parsed["values"]:
            fill_in_answers(main_driver, parsed["values"], lang, logger)
        else:
            log_message(T(lang, "no_valid"), logger)

        feedback = detect_submission_feedback(main_driver)
        if feedback != "unknown":
            log_message(T(lang, "smart_retry_feedback", x=feedback), logger)
        if feedback != "incorrect":
            break

        attempt_index += 1
        if attempt_index >= max_attempts:
            break
        log_message(T(lang, "smart_retry", a=attempt_index + 1, b=max_attempts), logger)
        try:
            main_driver.refresh()
            apply_hide_media_css(main_driver)
            decline_cookies(main_driver, lang, logger)
        except Exception:
            pass
        refreshed_task = fetch_task(main_driver, lang, logger)
        if refreshed_task == "SKIP" or not isinstance(refreshed_task, TaskData):
            break
        task = refreshed_task

    pts = parse_points_label(task.points_label)
    log_message(T(lang, "points_val", x=pts), logger)
    if BETA_STATE:
        BETA_STATE.mark_task(pts)
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
    beta_mode: bool = False,
    beta_overrides: Optional[Dict[str, bool]] = None,
) -> None:
    beta_state: Optional[BetaState] = activate_beta(beta_overrides) if beta_mode else None
    lic = LicenseManager(lang=lang, logger=logger)
    lic.ensure_for_cli(
        use_keysys_flag=force_keysys,
        license_user_arg=keysys_user,
        license_key_arg=license_key,
    )

    if BETA_STATE and BETA_STATE.config.credential_memory:
        BETA_STATE.session_metrics["user"] = user

    start_msg = f"Uzdevumi.lv bot started [{lang}]"
    if beta_state:
        start_msg += " (beta mode)"
        log_message(
            start_msg + f" — features: {', '.join(beta_state.features)}",
            logger,
        )
    else:
        log_message(start_msg, logger)

    driver = None
    gpt_session: Optional[ChatGPTSession] = None
    try:
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
                    if driver:
                        driver.quit()
                except Exception:
                    pass
            finally:
                driver = build_fast_driver(incognito=True, new_window=False, block_images=True)

        with_resilience(
            lambda: login(driver, user, password, lang, logger),
            recreate_main,
            lang,
            logger,
            retries=3,
        )
        gpt_session = ChatGPTSession(lang=lang, logger=logger)

        start_top = read_top_points(driver) or 0
        if BETA_STATE and BETA_STATE.config.top_tracking_enhancements:
            BETA_STATE.session_metrics["top_start"] = start_top
            BETA_STATE.session_metrics["top_current"] = start_top
        if until_top is not None:
            target_abs = until_top
            suffix = T(lang, "top_target", t=target_abs)
        elif gain_points is not None:
            target_abs = start_top + int(gain_points)
            suffix = T(lang, "top_target", t=target_abs)
        else:
            target_abs = None
            suffix = ""
        log_message(T(lang, "top_start", a=start_top, b=suffix), logger)

        round_idx = 0
        while True:
            round_idx += 1
            log_message(T(lang, "cycle", x=round_idx), logger)
            _ = solve_one_task(driver, gpt_session, lang, logger)
            time.sleep(0.7)
            now_top = read_top_points(driver) or start_top
            log_message(T(lang, "top_now", x=now_top), logger)
            if BETA_STATE and BETA_STATE.config.top_tracking_enhancements:
                BETA_STATE.session_metrics["top_current"] = now_top
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
                if driver:
                    driver.quit()
            except Exception:
                pass
            if gpt_session:
                gpt_session.close()
        if beta_state:
            if beta_state.config.metrics_reporting:
                metrics = beta_state.session_metrics
                points_total = metrics.get("points", 0.0)
                tasks_total = int(metrics.get("tasks", 0))
                skipped = int(metrics.get("skipped", 0))
                top_start = metrics.get("top_start")
                top_current = metrics.get("top_current")
                summary_parts = [
                    f"tasks={tasks_total}",
                    f"points={points_total:.2f}",
                    f"skipped={skipped}",
                ]
                if metrics.get("user"):
                    summary_parts.append(f"user={metrics['user']}")
                if top_start is not None and top_current is not None:
                    summary_parts.append(f"top_gain={int(top_current) - int(top_start)}")
                log_message("Beta summary: " + ", ".join(summary_parts), logger)
            deactivate_beta()

# ----------------------- GUI (CustomTkinter) -----------

def detect_backends() -> Dict[str, object]:
    available: Dict[str, object] = {}
    try:
        import customtkinter as ctk  # type: ignore

        available["customtkinter"] = ctk
    except ImportError:
        pass
    return available


def run_customtkinter_ui(ctk, default_lang: str = "lv", debug_default: bool = False, beta_default: bool = False) -> None:
    import tkinter.messagebox as messagebox
    import tkinter as tk
    from tkinter import filedialog

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

    beta_var = tk.BooleanVar(value=beta_default)
    beta_chk = ctk.CTkCheckBox(opts, text=L("ui_beta"), variable=beta_var)
    beta_chk.grid(row=1, column=0, padx=8, pady=4, sticky="w")

    until_entry = ctk.CTkEntry(opts, placeholder_text=L("ui_until"))
    until_entry.grid(row=2, column=0, padx=8, pady=4, sticky="ew")
    gain_entry = ctk.CTkEntry(opts, placeholder_text=L("ui_gain"))
    gain_entry.grid(row=2, column=1, padx=8, pady=4, sticky="ew")

    gui_tools = ctk.CTkFrame(app)
    gui_tools.grid(row=4, column=0, padx=12, pady=8, sticky="ew")
    gui_tools.grid_columnconfigure(1, weight=1)
    gui_title = ctk.CTkLabel(gui_tools, text=L("ui_gui_tools"), font=("Arial", 15, "bold"))
    gui_title.grid(row=0, column=0, columnspan=4, padx=8, pady=(8, 4), sticky="w")
    theme_label = ctk.CTkLabel(gui_tools, text=L("ui_theme"))
    theme_label.grid(row=1, column=0, padx=8, pady=4, sticky="w")
    theme_map = {
        L("ui_theme_system"): "system",
        L("ui_theme_light"): "light",
        L("ui_theme_dark"): "dark",
    }
    current_theme = ctk.get_appearance_mode() if hasattr(ctk, "get_appearance_mode") else "System"
    inverse_theme_map = {v.lower(): k for k, v in theme_map.items()}
    theme_default_key = inverse_theme_map.get(str(current_theme).lower(), L("ui_theme_system"))
    theme_var = tk.StringVar(value=theme_default_key)
    theme_menu = ctk.CTkOptionMenu(gui_tools, values=list(theme_map.keys()), variable=theme_var)
    theme_menu.grid(row=1, column=1, padx=8, pady=4, sticky="w")

    accent_label = ctk.CTkLabel(gui_tools, text=L("ui_accent"))
    accent_label.grid(row=1, column=2, padx=8, pady=4, sticky="w")
    accent_options = ["blue", "dark-blue", "green", "teal", "red", "purple", "orange"]
    accent_var = tk.StringVar(value=accent_options[0])
    accent_menu = ctk.CTkOptionMenu(gui_tools, values=accent_options, variable=accent_var)
    accent_menu.grid(row=1, column=3, padx=8, pady=4, sticky="w")

    widget_scale_label = ctk.CTkLabel(gui_tools, text=L("ui_widget_scaling"))
    widget_scale_label.grid(row=2, column=0, padx=8, pady=4, sticky="w")
    ui_scale_var = tk.DoubleVar(value=1.0)
    ui_scale_slider = ctk.CTkSlider(gui_tools, from_=0.8, to=1.4, number_of_steps=12, variable=ui_scale_var)
    ui_scale_slider.grid(row=2, column=1, padx=8, pady=4, sticky="ew")

    log_font_label = ctk.CTkLabel(gui_tools, text=L("ui_log_font"))
    log_font_label.grid(row=2, column=2, padx=8, pady=4, sticky="w")
    log_font_var = tk.DoubleVar(value=12.0)
    log_font_slider = ctk.CTkSlider(gui_tools, from_=8, to=20, number_of_steps=12, variable=log_font_var)
    log_font_slider.grid(row=2, column=3, padx=8, pady=4, sticky="ew")

    log_tools = ctk.CTkFrame(app)
    log_tools.grid(row=5, column=0, padx=12, pady=(0, 8), sticky="ew")
    log_tools.grid_columnconfigure(6, weight=1)
    log_tools_title = ctk.CTkLabel(log_tools, text=L("ui_log_tools"), font=("Arial", 15, "bold"))
    log_tools_title.grid(row=0, column=0, columnspan=7, padx=8, pady=(8, 4), sticky="w")
    log_wrap_var = tk.BooleanVar(value=True)
    log_wrap_chk = ctk.CTkCheckBox(log_tools, text=L("ui_log_wrap"), variable=log_wrap_var)
    log_wrap_chk.grid(row=1, column=0, padx=8, pady=4, sticky="w")
    log_autoscroll_var = tk.BooleanVar(value=True)
    log_autoscroll_chk = ctk.CTkCheckBox(
        log_tools, text=L("ui_log_autoscroll"), variable=log_autoscroll_var
    )
    log_autoscroll_chk.grid(row=1, column=1, padx=8, pady=4, sticky="w")
    log_pause_var = tk.BooleanVar(value=False)
    log_pause_chk = ctk.CTkCheckBox(log_tools, text=L("ui_log_pause"), variable=log_pause_var)
    log_pause_chk.grid(row=1, column=2, padx=8, pady=4, sticky="w")
    log_highlight_var = tk.BooleanVar(value=True)
    log_highlight_chk = ctk.CTkCheckBox(
        log_tools, text=L("ui_log_highlight"), variable=log_highlight_var
    )
    log_highlight_chk.grid(row=1, column=3, padx=8, pady=4, sticky="w")
    log_timestamp_var = tk.BooleanVar(value=True)
    log_timestamp_chk = ctk.CTkCheckBox(
        log_tools, text=L("ui_log_timestamp"), variable=log_timestamp_var
    )
    log_timestamp_chk.grid(row=1, column=4, padx=8, pady=4, sticky="w")

    log_filter_var = tk.StringVar()
    log_filter_entry = ctk.CTkEntry(log_tools, placeholder_text=L("ui_log_filter"), textvariable=log_filter_var)
    log_filter_entry.grid(row=2, column=0, columnspan=2, padx=8, pady=4, sticky="ew")
    log_clear_btn = ctk.CTkButton(log_tools, text=L("ui_log_clear"))
    log_clear_btn.grid(row=2, column=2, padx=4, pady=4)
    log_copy_btn = ctk.CTkButton(log_tools, text=L("ui_log_copy"))
    log_copy_btn.grid(row=2, column=3, padx=4, pady=4)
    log_save_btn = ctk.CTkButton(log_tools, text=L("ui_log_save"))
    log_save_btn.grid(row=2, column=4, padx=4, pady=4)

    lang_frame = ctk.CTkFrame(app)
    lang_frame.grid(row=6, column=0, padx=12, pady=4, sticky="ew")
    ctk.CTkLabel(lang_frame, text=L("ui_lang")).grid(row=0, column=0, padx=8, pady=6, sticky="w")
    lang_menu = ctk.CTkOptionMenu(lang_frame, values=["lv", "en", "ru"], variable=lang_var)
    lang_menu.grid(row=0, column=1, padx=8, pady=6, sticky="w")

    beta_tools = ctk.CTkFrame(app)
    beta_tools.grid(row=7, column=0, padx=12, pady=8, sticky="nsew")
    beta_tools.grid_columnconfigure(0, weight=1)
    beta_tools.grid_rowconfigure(3, weight=1)
    beta_title = ctk.CTkLabel(beta_tools, text=L("ui_beta_features"), font=("Arial", 15, "bold"))
    beta_title.grid(row=0, column=0, columnspan=6, padx=8, pady=(8, 0), sticky="w")
    beta_hint = ctk.CTkLabel(beta_tools, text=L("ui_beta_feature_hint"))
    beta_hint.grid(row=1, column=0, columnspan=6, padx=8, pady=(0, 6), sticky="w")
    feature_filter_var = tk.StringVar()
    feature_filter_entry = ctk.CTkEntry(
        beta_tools,
        placeholder_text=L("ui_beta_feature_search"),
        textvariable=feature_filter_var,
    )
    feature_filter_entry.grid(row=2, column=0, columnspan=2, padx=8, pady=4, sticky="ew")
    beta_buttons_frame = ctk.CTkFrame(beta_tools)
    beta_buttons_frame.grid(row=2, column=2, columnspan=4, padx=4, pady=4, sticky="e")
    select_all_btn = ctk.CTkButton(beta_buttons_frame, text=L("ui_select_all"))
    select_all_btn.grid(row=0, column=0, padx=4, pady=2)
    select_none_btn = ctk.CTkButton(beta_buttons_frame, text=L("ui_select_none"))
    select_none_btn.grid(row=0, column=1, padx=4, pady=2)
    restore_defaults_btn = ctk.CTkButton(beta_buttons_frame, text=L("ui_restore_defaults"))
    restore_defaults_btn.grid(row=0, column=2, padx=4, pady=2)
    import_btn = ctk.CTkButton(beta_buttons_frame, text=L("ui_import"))
    import_btn.grid(row=0, column=3, padx=4, pady=2)
    export_btn = ctk.CTkButton(beta_buttons_frame, text=L("ui_export"))
    export_btn.grid(row=0, column=4, padx=4, pady=2)
    collapse_btn = ctk.CTkButton(beta_buttons_frame, text=L("ui_collapse"))
    collapse_btn.grid(row=0, column=5, padx=4, pady=2)

    feature_scroll = ctk.CTkScrollableFrame(beta_tools, height=220)
    feature_scroll.grid(row=3, column=0, columnspan=6, padx=8, pady=4, sticky="nsew")
    beta_count_label = ctk.CTkLabel(beta_tools, text="")
    beta_count_label.grid(row=4, column=0, columnspan=6, padx=8, pady=(0, 8), sticky="w")

    advanced_tools = ctk.CTkFrame(app)
    advanced_tools.grid(row=8, column=0, padx=12, pady=8, sticky="nsew")
    advanced_tools.grid_columnconfigure(0, weight=1)
    advanced_tools.grid_rowconfigure(2, weight=1)
    advanced_title = ctk.CTkLabel(advanced_tools, text=L("ui_advanced_features"), font=("Arial", 15, "bold"))
    advanced_title.grid(row=0, column=0, padx=8, pady=(8, 0), sticky="w")
    advanced_hint = ctk.CTkLabel(advanced_tools, text=L("ui_advanced_hint"))
    advanced_hint.grid(row=1, column=0, padx=8, pady=(0, 6), sticky="w")

    advanced_tabs = ctk.CTkTabview(advanced_tools, height=220)
    advanced_tabs.grid(row=2, column=0, padx=8, pady=4, sticky="nsew")

    tab_translations = {
        "Prefixes": "ui_tab_prefixes",
        "Suffixes": "ui_tab_suffixes",
        "Transforms": "ui_tab_transforms",
        "Highlights": "ui_tab_highlights",
        "Filters": "ui_tab_filters",
        "Actions": "ui_tab_actions",
        "Layout": "ui_tab_layout",
        "Summary": "ui_tab_summary",
    }
    advanced_tab_frames: Dict[str, ctk.CTkScrollableFrame] = {}
    for category in GUI_CATEGORY_ORDER:
        advanced_tabs.add(category)
        advanced_tabs._tab_dict[category]["text_label"].configure(text=L(tab_translations[category]))
        container = advanced_tabs.tab(category)
        frame = ctk.CTkScrollableFrame(container, height=200)
        frame.pack(fill="both", expand=True, padx=4, pady=4)
        frame.grid_columnconfigure(0, weight=1)
        advanced_tab_frames[category] = frame

    advanced_feature_vars: Dict[str, tk.BooleanVar] = {}
    advanced_feature_widgets: Dict[str, ctk.CTkCheckBox] = {}
    for category, frame in advanced_tab_frames.items():
        for row_index, feature in enumerate(
            sorted(GUI_FEATURES_BY_CATEGORY.get(category, []), key=lambda f: f.label)
        ):
            var = tk.BooleanVar(value=False)
            chk = ctk.CTkCheckBox(
                frame,
                text=feature.label,
                variable=var,
                command=lambda n=feature.name: on_advanced_feature_toggle(n),
            )
            chk.grid(row=row_index, column=0, padx=6, pady=2, sticky="w")
            advanced_feature_vars[feature.name] = var
            advanced_feature_widgets[feature.name] = chk

    btns = ctk.CTkFrame(app)
    btns.grid(row=9, column=0, padx=12, pady=8, sticky="ew")
    start_btn = ctk.CTkButton(btns, text=L("ui_start"))
    start_btn.grid(row=0, column=0, padx=8, pady=8)
    ctk.CTkButton(btns, text=L("ui_close"), command=app.destroy).grid(row=0, column=1, padx=8, pady=8)

    log_box = ctk.CTkTextbox(app, height=240)
    log_box.grid(row=10, column=0, padx=12, pady=(8, 6), sticky="nsew")
    app.grid_rowconfigure(10, weight=1)
    log_box.configure(state="disabled")
    log_box.tag_configure("error", foreground="#ff5c5c")
    log_box.tag_configure("warning", foreground="#f5a623")

    log_summary_label = ctk.CTkLabel(app, text=L("ui_summary_placeholder"), anchor="w")
    log_summary_label.grid(row=11, column=0, padx=12, pady=(0, 12), sticky="ew")

    log_queue: "queue.Queue[GuiLogEvent]" = queue.Queue()
    log_history: List[GuiLogEntry] = []
    pending_logs: List[GuiLogEntry] = []
    log_sequence_counter = itertools.count(1)
    log_first_timestamp: Optional[datetime] = None

    def is_action_enabled(payload: str) -> bool:
        for name in ACTION_FEATURE_NAMES:
            if advanced_feature_vars.get(name) and advanced_feature_vars[name].get():
                feature = GUI_FEATURE_BY_NAME.get(name)
                if feature and feature.payload == payload:
                    return True
        return False

    def active_feature_names(names: List[str]) -> List[str]:
        return [name for name in names if advanced_feature_vars.get(name) and advanced_feature_vars[name].get()]

    def active_highlight_specs() -> List[KeywordSpec]:
        specs: List[KeywordSpec] = []
        for name in KEYWORD_HIGHLIGHT_NAMES:
            if not advanced_feature_vars.get(name) or not advanced_feature_vars[name].get():
                continue
            feature = GUI_FEATURE_BY_NAME.get(name)
            if not feature:
                continue
            spec = KEYWORD_SPEC_BY_NAME.get(feature.payload)
            if spec:
                specs.append(spec)
        return specs

    def render_entries(entries: List[GuiLogEntry]) -> List[str]:
        rendered: List[str] = []
        prefixes = active_feature_names(PREFIX_FEATURE_NAMES)
        suffixes = active_feature_names(SUFFIX_FEATURE_NAMES)
        transforms = active_feature_names(TRANSFORM_FEATURE_NAMES)
        highlights = active_highlight_specs()
        summary_enabled = any(advanced_feature_vars.get(name) and advanced_feature_vars[name].get() for name in SUMMARY_FEATURE_NAMES)
        beta_enabled = bool(BETA_STATE and BETA_STATE.enabled)
        beta_total = len(beta_feature_vars)
        beta_active = sum(1 for var in beta_feature_vars.values() if var.get())
        beta_state_text = f"β:{beta_active}/{beta_total}" if beta_enabled else "β:off"
        prev_ts: Optional[datetime] = None
        first_ts = log_first_timestamp
        for index, entry in enumerate(entries):
            context: Dict[str, object] = {
                "previous_timestamp": prev_ts,
                "first_timestamp": first_ts or entry.timestamp,
                "display_index": index,
                "language": lang_var.get(),
                "beta_state": beta_state_text,
                "summary_enabled": summary_enabled,
            }
            if first_ts is None:
                first_ts = entry.timestamp
            primary_label = None
            for spec in KEYWORD_SPECS:
                if spec.name in entry.keywords:
                    primary_label = spec.label
                    break
            context["primary_keyword_label"] = primary_label
            text = entry.text
            for name in transforms:
                feature = GUI_FEATURE_BY_NAME.get(name)
                if not feature:
                    continue
                handler = TRANSFORM_HANDLERS.get(feature.payload)
                if handler:
                    text = handler(text, entry)
            highlight_prefixes: List[str] = []
            for spec in highlights:
                if spec.name in entry.keywords:
                    highlight_prefixes.append(f"{spec.icon} {spec.label}")
            if highlight_prefixes:
                text = _join_non_empty(highlight_prefixes, " | ") + " " + text
            prefix_parts: List[str] = []
            for name in prefixes:
                feature = GUI_FEATURE_BY_NAME.get(name)
                if not feature:
                    continue
                renderer = PREFIX_RENDERERS.get(feature.payload)
                if renderer:
                    prefix_parts.append(renderer(entry, context))
            suffix_parts: List[str] = []
            for name in suffixes:
                feature = GUI_FEATURE_BY_NAME.get(name)
                if not feature:
                    continue
                renderer = SUFFIX_RENDERERS.get(feature.payload)
                if renderer:
                    suffix_parts.append(renderer(entry, context))
            prefix_text = _join_non_empty(prefix_parts, " | ")
            suffix_text = _join_non_empty(suffix_parts, " ")
            display = text
            if log_timestamp_var.get():
                display = f"[{entry.timestamp.strftime('%H:%M:%S')}] {display}"
            if prefix_text:
                display = f"{prefix_text} → {display}"
            if suffix_text:
                display = f"{display} {suffix_text}"
            rendered.append(display.strip())
            prev_ts = entry.timestamp
        return rendered

    def apply_filters(entries: List[GuiLogEntry]) -> List[GuiLogEntry]:
        only_levels: Set[str] = set()
        hide_levels: Set[str] = set()
        hide_keywords: List[str] = []
        hide_duplicates = False
        only_keyword_names: Set[str] = set()
        for name in FILTER_FEATURE_NAMES:
            if not advanced_feature_vars.get(name) or not advanced_feature_vars[name].get():
                continue
            feature = GUI_FEATURE_BY_NAME.get(name)
            if not feature:
                continue
            payload = feature.payload or {}
            mode = payload.get("mode")
            value = payload.get("value")
            if mode == "only_level" and isinstance(value, str):
                only_levels.add(value)
            elif mode == "hide_level" and isinstance(value, str):
                hide_levels.add(value)
            elif mode == "hide_keyword" and isinstance(value, str):
                hide_keywords.append(value)
            elif mode == "hide_duplicates":
                hide_duplicates = True
        for name in KEYWORD_FILTER_NAMES:
            if advanced_feature_vars.get(name) and advanced_feature_vars[name].get():
                feature = GUI_FEATURE_BY_NAME.get(name)
                if feature:
                    only_keyword_names.add(feature.payload)
        result: List[GuiLogEntry] = []
        seen: Set[str] = set()
        for entry in entries:
            level = entry.level
            if "alert" in only_levels and level not in {"error", "warning"}:
                continue
            if "error" in only_levels and level != "error":
                continue
            if "warning" in only_levels and level != "warning":
                continue
            if level in hide_levels:
                continue
            lower_text = entry.text.lower()
            if hide_keywords and any(keyword in lower_text for keyword in hide_keywords):
                continue
            if only_keyword_names and not any(keyword in only_keyword_names for keyword in entry.keywords):
                continue
            if hide_duplicates:
                key = lower_text
                if key in seen:
                    continue
                seen.add(key)
            result.append(entry)
        return result

    def get_visible_entries() -> List[GuiLogEntry]:
        entries = apply_filters(list(log_history))
        query = (log_filter_var.get() or "").strip().lower()
        if not query:
            return entries
        return [entry for entry in entries if query in entry.text.lower()]

    def compute_log_stats(entries: List[GuiLogEntry]) -> Dict[str, object]:
        stats: Dict[str, object] = {
            "total": len(entries),
            "errors": 0,
            "warnings": 0,
            "infos": 0,
            "last_message": entries[-1].text if entries else None,
            "last_error": None,
            "last_warning": None,
            "last_keyword": None,
            "keyword_counts": {},
            "points_total": 0.0,
            "duration": 0.0,
            "avg_length": None,
            "unique_keywords": 0,
        }
        if not entries:
            return stats
        total_length = 0
        first_ts = entries[0].timestamp
        last_ts = entries[-1].timestamp
        stats["duration"] = max(0.0, (last_ts - first_ts).total_seconds())
        keyword_counts: Dict[str, int] = {}
        for entry in entries:
            total_length += len(entry.text)
            if entry.level == "error":
                stats["errors"] += 1
                stats["last_error"] = entry.text
            elif entry.level == "warning":
                stats["warnings"] += 1
                stats["last_warning"] = entry.text
            else:
                stats["infos"] += 1
            matches = POINTS_PATTERN.findall(entry.text)
            if matches:
                stats["points_total"] += sum(float(val.replace(",", ".")) for val in matches)
            for keyword in entry.keywords:
                keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
                spec = KEYWORD_SPEC_BY_NAME.get(keyword)
                if spec:
                    stats["last_keyword"] = spec.label
        stats["keyword_counts"] = keyword_counts
        stats["unique_keywords"] = len(keyword_counts)
        if stats["total"]:
            stats["avg_length"] = total_length / stats["total"]
        for key in ("last_message", "last_error", "last_warning"):
            value = stats.get(key)
            if isinstance(value, str) and len(value) > 120:
                stats[key] = value[:117] + "…"
        return stats

    def build_summary_text(stats: Dict[str, object]) -> str:
        parts: List[str] = []
        for name in SUMMARY_FEATURE_NAMES:
            if not advanced_feature_vars.get(name) or not advanced_feature_vars[name].get():
                continue
            feature = GUI_FEATURE_BY_NAME.get(name)
            if not feature:
                continue
            renderer = SUMMARY_RENDERERS.get(feature.payload)
            if renderer:
                piece = renderer(stats)
                if piece:
                    parts.append(piece)
        if not parts:
            return L("ui_summary_placeholder")
        return " | ".join(parts)

    beta_button_defaults = {
        btn: {
            "corner_radius": btn.cget("corner_radius"),
            "border_width": btn.cget("border_width"),
            "width": btn.cget("width"),
        }
        for btn in [
            start_btn,
            select_all_btn,
            select_none_btn,
            restore_defaults_btn,
            import_btn,
            export_btn,
            collapse_btn,
            lic_check_btn,
            lic_end_btn,
            log_clear_btn,
            log_copy_btn,
            log_save_btn,
        ]
    }
    default_log_height = 240
    default_log_fg = log_box.cget("fg_color")
    beta_default_fg = beta_tools.cget("fg_color")
    beta_default_corner = beta_tools.cget("corner_radius")
    advanced_default_fg = advanced_tools.cget("fg_color")
    advanced_default_corner = advanced_tools.cget("corner_radius")
    frame_default_padding = {
        cred: (12, 8),
        lic_frame: (12, 8),
        opts: (12, 8),
        lang_frame: (12, 4),
        beta_tools: (12, 8),
        advanced_tools: (12, 8),
    }
    header_default_font = header.cget("font")
    beta_title_default_font = beta_title.cget("font")
    advanced_title_default_font = advanced_title.cget("font")
    start_btn_default_width = start_btn.cget("width")
    start_btn_default_corner = start_btn.cget("corner_radius")

    def apply_layout_features() -> None:
        log_box.configure(height=default_log_height, fg_color=default_log_fg)
        beta_tools.configure(fg_color=beta_default_fg, corner_radius=beta_default_corner)
        advanced_tools.configure(fg_color=advanced_default_fg, corner_radius=advanced_default_corner)
        header.configure(font=header_default_font)
        beta_title.configure(font=beta_title_default_font)
        advanced_title.configure(font=advanced_title_default_font)
        for frame, (padx, pady) in frame_default_padding.items():
            frame.grid_configure(padx=padx, pady=pady)
        for btn, defaults in beta_button_defaults.items():
            try:
                btn.configure(
                    corner_radius=defaults.get("corner_radius"),
                    border_width=defaults.get("border_width"),
                    width=defaults.get("width"),
                )
            except Exception:
                pass
        start_btn.configure(width=start_btn_default_width, corner_radius=start_btn_default_corner)
        if advanced_feature_vars.get("layout_expand_log_height") and advanced_feature_vars["layout_expand_log_height"].get():
            log_box.configure(height=320)
        if advanced_feature_vars.get("layout_compact_panels") and advanced_feature_vars["layout_compact_panels"].get():
            for frame in frame_default_padding:
                frame.grid_configure(padx=6, pady=4)
        if advanced_feature_vars.get("layout_bold_headers") and advanced_feature_vars["layout_bold_headers"].get():
            header.configure(font=("Arial", 22, "bold"))
            beta_title.configure(font=("Arial", 17, "bold"))
            advanced_title.configure(font=("Arial", 17, "bold"))
        if advanced_feature_vars.get("layout_wide_buttons") and advanced_feature_vars["layout_wide_buttons"].get():
            try:
                start_btn.configure(width=(start_btn_default_width or 120) + 40)
            except Exception:
                pass
        if advanced_feature_vars.get("layout_highlight_beta_panel") and advanced_feature_vars["layout_highlight_beta_panel"].get():
            beta_tools.configure(fg_color=("#1f3b64", "#14284b"))
        if advanced_feature_vars.get("layout_highlight_advanced_panel") and advanced_feature_vars["layout_highlight_advanced_panel"].get():
            advanced_tools.configure(fg_color=("#2c2d45", "#1a1b2b"))
        if advanced_feature_vars.get("layout_highlight_log_panel") and advanced_feature_vars["layout_highlight_log_panel"].get():
            log_box.configure(fg_color=("#1c1c1c", "#0f0f0f"))
        if advanced_feature_vars.get("layout_round_controls") and advanced_feature_vars["layout_round_controls"].get():
            for frame in (cred, lic_frame, opts, lang_frame, beta_tools, advanced_tools):
                try:
                    frame.configure(corner_radius=18)
                except Exception:
                    pass
        if advanced_feature_vars.get("layout_dim_background") and advanced_feature_vars["layout_dim_background"].get():
            for frame in (cred, lic_frame, opts, lang_frame):
                try:
                    frame.configure(fg_color=("#262626", "#151515"))
                except Exception:
                    pass
        if advanced_feature_vars.get("layout_flat_buttons") and advanced_feature_vars["layout_flat_buttons"].get():
            for btn in beta_button_defaults:
                try:
                    btn.configure(corner_radius=4, border_width=0)
                except Exception:
                    pass

    def on_advanced_feature_toggle(name: str) -> None:
        feature = GUI_FEATURE_BY_NAME.get(name)
        if not feature:
            return
        if feature.kind in {"prefix", "suffix", "transform", "filter", "keyword-highlight", "keyword-filter", "summary"}:
            refresh_log_display()
        elif feature.kind == "layout":
            apply_layout_features()

    action_handlers: Dict[str, Callable[[GuiLogEntry], None]] = {}

    def register_action(payload: str, func: Callable[[GuiLogEntry], None]) -> None:
        action_handlers[payload] = func

    def safe_bell() -> None:
        try:
            app.bell()
        except Exception:
            pass

    register_action(
        "beep_error",
        lambda entry: safe_bell() if entry.level == "error" else None,
    )
    register_action(
        "beep_warning",
        lambda entry: safe_bell() if entry.level == "warning" else None,
    )
    register_action(
        "beep_cycle",
        lambda entry: safe_bell() if "cycle" in entry.text.lower() else None,
    )

    def copy_to_clipboard(entry: GuiLogEntry) -> None:
        try:
            app.clipboard_clear()
            app.clipboard_append(entry.text)
        except Exception:
            pass

    register_action(
        "copy_error",
        lambda entry: copy_to_clipboard(entry) if entry.level == "error" else None,
    )
    register_action(
        "copy_gpt",
        lambda entry: copy_to_clipboard(entry) if "gpt" in entry.text.lower() else None,
    )
    register_action(
        "copy_done",
        lambda entry: copy_to_clipboard(entry) if "done" in entry.text.lower() else None,
    )
    register_action(
        "focus_error",
        lambda entry: app.after(0, lambda: (app.lift(), app.focus_force())) if entry.level == "error" else None,
    )
    register_action(
        "pause_error",
        lambda entry: log_pause_var.set(True) if entry.level == "error" else None,
    )
    register_action(
        "wrap_long",
        lambda entry: log_wrap_var.set(True) if len(entry.text) > 140 else None,
    )

    def handle_log_actions(entry: GuiLogEntry) -> None:
        for name in ACTION_FEATURE_NAMES:
            if not advanced_feature_vars.get(name) or not advanced_feature_vars[name].get():
                continue
            feature = GUI_FEATURE_BY_NAME.get(name)
            if not feature:
                continue
            handler = action_handlers.get(feature.payload)
            if handler:
                handler(entry)

    def refresh_log_display() -> None:
        entries = get_visible_entries()
        rendered = render_entries(entries)
        log_box.configure(state="normal")
        log_box.delete("1.0", "end")
        wrap_mode = "word" if log_wrap_var.get() else "none"
        log_box.configure(wrap=wrap_mode)
        log_box.configure(font=("Consolas", int(log_font_var.get())))
        for entry, display in zip(entries, rendered):
            start_index = log_box.index("end-1c")
            log_box.insert("end", display + "\n")
            end_index = log_box.index("end-1c")
            if log_highlight_var.get():
                if entry.level == "error":
                    log_box.tag_add("error", start_index, end_index)
                elif entry.level == "warning":
                    log_box.tag_add("warning", start_index, end_index)
        log_box.configure(state="disabled")
        if log_autoscroll_var.get():
            log_box.see("end")
        stats = compute_log_stats(entries)
        log_summary_label.configure(text=build_summary_text(stats))

    def append_log(message: str) -> None:
        log_queue.put(
            GuiLogEvent(
                timestamp=datetime.now(),
                text=message,
                thread_name=threading.current_thread().name,
                thread_id=threading.get_ident() or 0,
            )
        )

    def flush_pending() -> None:
        nonlocal log_first_timestamp
        if log_pause_var.get() or not pending_logs:
            return
        if not log_history and pending_logs:
            log_first_timestamp = pending_logs[0].timestamp
        for entry in pending_logs:
            log_history.append(entry)
            handle_log_actions(entry)
        pending_logs.clear()
        refresh_log_display()

    def process_queue() -> None:
        nonlocal log_sequence_counter, log_first_timestamp
        try:
            while True:
                event = log_queue.get_nowait()
                if is_action_enabled("clear_cycle") and "cycle" in event.text.lower():
                    log_history.clear()
                    pending_logs.clear()
                    log_sequence_counter = itertools.count(1)
                    log_first_timestamp = None
                sequence = next(log_sequence_counter)
                entry = GuiLogEntry(
                    timestamp=event.timestamp,
                    text=event.text,
                    thread_name=event.thread_name,
                    thread_id=event.thread_id,
                    sequence=sequence,
                    level=detect_log_level(event.text),
                    keywords=match_keywords(event.text),
                )
                if log_pause_var.get():
                    pending_logs.append(entry)
                else:
                    if not log_history:
                        log_first_timestamp = entry.timestamp
                    log_history.append(entry)
                    handle_log_actions(entry)
                    refresh_log_display()
        except queue.Empty:
            pass
        app.after(100, process_queue)

    def on_clear_log() -> None:
        nonlocal log_sequence_counter, log_first_timestamp
        log_history.clear()
        pending_logs.clear()
        log_sequence_counter = itertools.count(1)
        log_first_timestamp = None
        refresh_log_display()

    def on_copy_log() -> None:
        entries = get_visible_entries()
        rendered = render_entries(entries)
        if log_timestamp_var.get():
            rendered = [f"[{entry.timestamp.strftime('%H:%M:%S')}] {text}" for entry, text in zip(entries, rendered)]
        try:
            app.clipboard_clear()
            app.clipboard_append("\n".join(rendered))
        except Exception:
            pass

    def on_save_log() -> None:
        entries = get_visible_entries()
        rendered = render_entries(entries)
        if log_timestamp_var.get():
            rendered = [f"[{entry.timestamp.strftime('%H:%M:%S')}] {text}" for entry, text in zip(entries, rendered)]
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text", "*.txt"), ("JSON", "*.json"), ("All", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as fh:
                if path.lower().endswith(".json"):
                    json.dump(
                        [
                            {
                                "timestamp": entry.timestamp.isoformat(),
                                "message": text,
                            }
                            for entry, text in zip(entries, rendered)
                        ],
                        fh,
                        ensure_ascii=False,
                        indent=2,
                    )
                else:
                    fh.write("\n".join(rendered))
            messagebox.showinfo(I18N[lang_var.get()]["title"], L("ui_log_saved"))
        except Exception as exc:
            messagebox.showerror(I18N[lang_var.get()]["title"], str(exc))

    log_clear_btn.configure(command=on_clear_log)
    log_copy_btn.configure(command=on_copy_log)
    log_save_btn.configure(command=on_save_log)
    apply_layout_features()

    def apply_log_font(value: float) -> None:
        try:
            log_font_var.set(float(value))
        except Exception:
            pass
        refresh_log_display()

    log_font_slider.configure(command=apply_log_font)

    def apply_ui_scale(value: float) -> None:
        try:
            ctk.set_widget_scaling(float(value))
        except Exception:
            pass

    ui_scale_slider.configure(command=apply_ui_scale)

    def on_accent_change(choice: str) -> None:
        try:
            ctk.set_default_color_theme(choice)
        except Exception:
            pass

    accent_menu.configure(command=on_accent_change)

    theme_map_ref = {
        "map": {
            L("ui_theme_system"): "system",
            L("ui_theme_light"): "light",
            L("ui_theme_dark"): "dark",
        }
    }

    def on_theme_change(choice: str) -> None:
        actual = theme_map_ref["map"].get(choice, "system")
        try:
            ctk.set_appearance_mode(actual)
        except Exception:
            pass

    theme_menu.configure(command=on_theme_change)

    def update_beta_count() -> None:
        total = len(beta_feature_vars)
        enabled = sum(1 for var in beta_feature_vars.values() if var.get())
        beta_count_label.configure(text=L("ui_feature_count", a=enabled, b=total))

    def refresh_beta_filter(*_ignored) -> None:
        query = (feature_filter_var.get() or "").strip().lower()
        for name, widget in beta_feature_widgets.items():
            label = BETA_FEATURE_LABELS.get(name, name).lower()
            if not query or query in label:
                widget.grid()
            else:
                widget.grid_remove()

    beta_feature_defaults: Dict[str, bool] = {name: True for name in BETA_FEATURE_NAMES}
    beta_feature_vars: Dict[str, tk.BooleanVar] = {}
    beta_feature_widgets: Dict[str, ctk.CTkCheckBox] = {}

    for row_index, feature_name in enumerate(BETA_FEATURE_NAMES):
        var = tk.BooleanVar(value=beta_feature_defaults.get(feature_name, True))
        beta_feature_vars[feature_name] = var
        checkbox = ctk.CTkCheckBox(
            feature_scroll,
            text=BETA_FEATURE_LABELS.get(feature_name, feature_name),
            variable=var,
        )
        checkbox.grid(row=row_index, column=0, padx=6, pady=2, sticky="w")
        beta_feature_widgets[feature_name] = checkbox

        def _trace_factory(v: tk.BooleanVar) -> Callable[[str, str, str], None]:
            return lambda *args: update_beta_count()

        var.trace_add("write", _trace_factory(var))

    update_beta_count()
    refresh_beta_filter()

    def select_all_features() -> None:
        for var in beta_feature_vars.values():
            var.set(True)
        update_beta_count()

    def select_none_features() -> None:
        for var in beta_feature_vars.values():
            var.set(False)
        update_beta_count()

    def restore_feature_defaults() -> None:
        for name, default in beta_feature_defaults.items():
            beta_feature_vars[name].set(default)
        update_beta_count()

    def export_beta_preset() -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("All", "*.*")],
        )
        if not path:
            return
        try:
            payload = {name: var.get() for name, var in beta_feature_vars.items()}
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, ensure_ascii=False, indent=2)
            messagebox.showinfo(I18N[lang_var.get()]["title"], L("ui_beta_feature_saved"))
        except Exception as exc:
            messagebox.showerror(I18N[lang_var.get()]["title"], L("ui_beta_feature_error", e=str(exc)))

    def import_beta_preset() -> None:
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json"), ("All", "*.*")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, list):
                data = {name: name in data for name in BETA_FEATURE_NAMES}
            if isinstance(data, dict):
                for name, value in data.items():
                    if name in beta_feature_vars:
                        beta_feature_vars[name].set(bool(value))
                update_beta_count()
                refresh_beta_filter()
                messagebox.showinfo(I18N[lang_var.get()]["title"], L("ui_beta_feature_loaded"))
            else:
                raise ValueError("Invalid preset format")
        except Exception as exc:
            messagebox.showerror(I18N[lang_var.get()]["title"], L("ui_beta_feature_error", e=str(exc)))

    select_all_btn.configure(command=select_all_features)
    select_none_btn.configure(command=select_none_features)
    restore_defaults_btn.configure(command=restore_feature_defaults)
    import_btn.configure(command=import_beta_preset)
    export_btn.configure(command=export_beta_preset)

    collapsed_state = {"collapsed": False}

    def toggle_collapse() -> None:
        collapsed_state["collapsed"] = not collapsed_state["collapsed"]
        if collapsed_state["collapsed"]:
            feature_scroll.grid_remove()
            beta_count_label.grid_remove()
            collapse_btn.configure(text=L("ui_expand"))
        else:
            feature_scroll.grid()
            beta_count_label.grid()
            collapse_btn.configure(text=L("ui_collapse"))

    collapse_btn.configure(command=toggle_collapse)

    def update_beta_feature_states(*_args) -> None:
        enabled = beta_var.get()
        state = "normal" if enabled else "disabled"
        entry_state = "normal" if enabled else "disabled"
        feature_filter_entry.configure(state=entry_state)
        for widget in beta_feature_widgets.values():
            widget.configure(state=state)
        for btn in (
            select_all_btn,
            select_none_btn,
            restore_defaults_btn,
            import_btn,
            export_btn,
            collapse_btn,
        ):
            btn.configure(state=state)

    beta_var.trace_add("write", update_beta_feature_states)
    update_beta_feature_states()

    feature_filter_var.trace_add("write", refresh_beta_filter)
    log_filter_var.trace_add("write", lambda *args: refresh_log_display())
    log_wrap_var.trace_add("write", lambda *args: refresh_log_display())
    log_highlight_var.trace_add("write", lambda *args: refresh_log_display())
    log_timestamp_var.trace_add("write", lambda *args: refresh_log_display())
    log_pause_var.trace_add("write", lambda *args: flush_pending())
    refresh_log_display()

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
        beta_flag: bool,
        beta_overrides: Optional[Dict[str, bool]],
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
                beta_mode=beta_flag,
                beta_overrides=beta_overrides,
            )
        except Exception as exc:
            append_log(f"❌ {exc}")
            messagebox.showerror(I18N[lang_sel]["title"], str(exc))
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

        beta_overrides: Optional[Dict[str, bool]] = None
        if beta_var.get():
            overrides: Dict[str, bool] = {}
            for name, var in beta_feature_vars.items():
                desired = var.get()
                if desired != beta_feature_defaults.get(name, True):
                    overrides[name] = desired
            beta_overrides = overrides

        if remember_var.get():
            save_credentials(u, p)
            append_log(T(lang_var.get(), "creds_saved"))
        else:
            clear_saved_credentials()
            append_log(T(lang_var.get(), "creds_cleared"))

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
                beta_var.get(),
                beta_overrides,
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
        beta_chk.configure(text=L("ui_beta"))
        until_entry.configure(placeholder_text=L("ui_until"))
        gain_entry.configure(placeholder_text=L("ui_gain"))
        gui_title.configure(text=L("ui_gui_tools"))
        theme_label.configure(text=L("ui_theme"))
        accent_label.configure(text=L("ui_accent"))
        widget_scale_label.configure(text=L("ui_widget_scaling"))
        log_font_label.configure(text=L("ui_log_font"))
        log_tools_title.configure(text=L("ui_log_tools"))
        log_wrap_chk.configure(text=L("ui_log_wrap"))
        log_autoscroll_chk.configure(text=L("ui_log_autoscroll"))
        log_pause_chk.configure(text=L("ui_log_pause"))
        log_highlight_chk.configure(text=L("ui_log_highlight"))
        log_timestamp_chk.configure(text=L("ui_log_timestamp"))
        log_filter_entry.configure(placeholder_text=L("ui_log_filter"))
        log_clear_btn.configure(text=L("ui_log_clear"))
        log_copy_btn.configure(text=L("ui_log_copy"))
        log_save_btn.configure(text=L("ui_log_save"))
        beta_title.configure(text=L("ui_beta_features"))
        beta_hint.configure(text=L("ui_beta_feature_hint"))
        feature_filter_entry.configure(placeholder_text=L("ui_beta_feature_search"))
        select_all_btn.configure(text=L("ui_select_all"))
        select_none_btn.configure(text=L("ui_select_none"))
        restore_defaults_btn.configure(text=L("ui_restore_defaults"))
        import_btn.configure(text=L("ui_import"))
        export_btn.configure(text=L("ui_export"))
        collapse_btn.configure(text=L("ui_expand") if collapsed_state["collapsed"] else L("ui_collapse"))
        advanced_title.configure(text=L("ui_advanced_features"))
        advanced_hint.configure(text=L("ui_advanced_hint"))
        for category, key in tab_translations.items():
            try:
                advanced_tabs._tab_dict[category]["text_label"].configure(text=L(key))
            except Exception:
                pass
        log_summary_label.configure(text=L("ui_summary_placeholder"))
        refresh_beta_filter()
        update_beta_count()
        start_btn.configure(text=L("ui_start"))
        lic_check_btn.configure(text=L("ui_check_license"))
        lic_end_btn.configure(text=L("ui_end_trial"))
        lic_status.configure(text=L("status") + ": —")
        lic_user_entry.configure(placeholder_text=L("ui_license_user_ph"))
        lic_key_entry.configure(placeholder_text=L("ui_license_key_ph"))
        apply_layout_features()

        old_map = theme_map_ref["map"]
        current_actual = old_map.get(theme_var.get(), "system")
        new_map = {
            L("ui_theme_system"): "system",
            L("ui_theme_light"): "light",
            L("ui_theme_dark"): "dark",
        }
        theme_map_ref["map"] = new_map
        theme_menu.configure(values=list(new_map.keys()))
        chosen_label = next(
            (label for label, actual in new_map.items() if actual == current_actual),
            next(iter(new_map.keys())),
        )
        theme_var.set(chosen_label)

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


def launch_gui(default_lang: str, debug_default: bool, beta_default: bool = False) -> None:
    available = detect_backends()
    if not available or "customtkinter" not in available:
        raise RuntimeError("GUI not available (customtkinter missing). Use CLI with --nogui.")
    run_customtkinter_ui(
        available["customtkinter"],
        default_lang=default_lang,
        debug_default=debug_default,
        beta_default=beta_default,
    )

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
    parser.add_argument("--beta", action="store_true", help="Enable beta mode with experimental optimizations")
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
            beta_mode=args.beta,
            beta_overrides=None,
        )
        if args.save_creds:
            save_credentials(cli_user, cli_pass)
            print(T(args.lang, "creds_saved"))
    else:
        launch_gui(default_lang=args.lang, debug_default=args.debug, beta_default=args.beta)


if __name__ == "__main__":
    main()
