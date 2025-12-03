# Project Functionality

## Automation and Task Solving
- Navigates Uzdevumi tasks, gathers task text, points, options, and detects drag-and-drop or audio content before solving.【F:main.py†L1258-L1365】
- Sends the parsed task (including multiple choice, dropdowns, drag targets, or text inputs) to the GPT helper and chooses an action based on the model response.【F:main.py†L1505-L1611】【F:main.py†L1784-L1846】
- Fills answers automatically: enters text/number fields, selects checkboxes or radios, picks dropdown options, or places draggable answers with drag/click fallbacks and hidden input updates before submitting.【F:main.py†L1616-L1779】

## Audio Support
- Detects audio sources in tasks, downloads the audio, and requests transcription through the worker helper endpoint so the transcript is added to the prompt sent to the model.【F:main.py†L1303-L1323】
- Worker `/transcribe` endpoint downloads the audio URL and calls the Hugging Face Whisper inference API (with optional HF token) to return text back to the client.【F:index.js†L1106-L1159】

## Licensing and GPT Access
- Manages licensing/trial checks and pulls GPT access tokens from the Keysys helper when solving tasks with the ChatGPT session.【F:main.py†L1370-L1830】

## Browser Control
- Automates Chrome via Selenium/undetected-chromedriver, handling login, navigation, cookie dialogs, and page element utilities used throughout task solving.【F:main.py†L1-L124】【F:main.py†L1200-L1245】
