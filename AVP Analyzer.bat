@echo off
:: Intenta primero Chrome con la ruta de 64-bit
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" http://127.0.0.1:5000
) else (
    :: Si no existe, intenta con la ruta de 32-bit
    if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
        start "" "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" http://127.0.0.1:5000
    ) else (
        :: Si ninguna ruta funciona, lanza el navegador por default
        start "" http://127.0.0.1:5000
    )
)

python AVP-Analyzer.py

