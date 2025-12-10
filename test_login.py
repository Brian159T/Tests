from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

import base64
import datetime
import os
import time
import traceback

# --- CONFIG ---
BRAVE_BINARY = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
TARGET_URL = "http://localhost:4200/login"
REPORTS_DIR = "reports"  # se creará si no existe

def ensure_reports_dir():
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)

def now_str():
    return datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def build_html_report(filename, title, summary, steps, screenshot_b64):
    css = """
    body{font-family: Inter, Roboto, Arial, sans-serif; background:#0f1724; color:#e6eef8; margin:0; padding:0;}
    .container{max-width:1000px;margin:28px auto;padding:20px;background:linear-gradient(180deg,#0b1220 0%, #0e1a2a 100%);border-radius:12px;box-shadow:0 6px 24px rgba(2,6,23,.7);}
    h1{margin:0 0 8px 0;font-size:22px}
    .meta{color:#9fb2d6;font-size:13px;margin-bottom:18px}
    .result-badge{display:inline-block;padding:6px 10px;border-radius:999px;font-weight:700;}
    .pass{background:#0f5132;color:#bff2d3}
    .fail{background:#5b1016;color:#ffd7dd}
    .steps{background:#071022;border-radius:8px;padding:12px;margin-top:14px;font-family:monospace;color:#cde7ff}
    .step{margin-bottom:8px}
    .screenshot{margin-top:14px;border-radius:8px;overflow:hidden; border:1px solid rgba(255,255,255,0.06)}
    .footer{margin-top:18px;color:#8ea9cf;font-size:13px}
    .key{color:#a7c1ff}
    a.report-link{color:#cff0ff}
    """
    # simple HTML layout
    html = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>{css}</style>
</head>
<body>
  <div class="container">
    <h1>{title}</h1>
    <div class="meta">
      <span class="key">Timestamp:</span> {summary['timestamp']} &nbsp; | &nbsp;
      <span class="key">Navegador:</span> Brave (ruta: {summary['browser_path']}) &nbsp; | &nbsp;
      <span class="key">URL probada:</span> <a class="report-link" href="{summary['url']}">{summary['url']}</a>
    </div>

    <div>
      <span class="result-badge {'pass' if summary['status']=='PASSED' else 'fail'}">{summary['status']}</span>
      &nbsp;&nbsp;<strong>{summary['title']}</strong>
    </div>

    <div class="steps">
      {"".join([f"<div class='step'>• {s}</div>" for s in steps])}
    </div>

    <div class="screenshot">
      <img alt="screenshot" src="data:image/png;base64,{screenshot_b64}" style="width:100%; display:block;">
    </div>

    <div class="footer">
      Reporte generado: {summary['timestamp']} • Archivo: {filename}
    </div>
  </div>
</body>
</html>"""
    return html

def test_login_and_report():
    ensure_reports_dir()
    timestamp = now_str()
    report_filename = f"report_login_{timestamp}.html"
    report_path = os.path.join(REPORTS_DIR, report_filename)

    steps_log = []
    summary = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "browser_path": BRAVE_BINARY,
        "url": TARGET_URL,
        "status": "FAILED",
        "title": "Test login correcto"
    }
    screenshot_b64 = ""  # fallback blank

    chrome_options = Options()
    # usar Brave como navegador (ruta custom)
    chrome_options.binary_location = BRAVE_BINARY
    # opciones headless si quieres (descomentar): chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    driver = None

    try:
        steps_log.append("Iniciando WebDriver...")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        steps_log.append("Abriendo URL objetivo: " + TARGET_URL)
        driver.get(TARGET_URL)

        # esperar el input correo
        steps_log.append("Esperando input correo...")
        correo_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[formControlName='correo']"))
        )
        correo_input.clear()
        correo_input.send_keys("brayanzegarra321@gmail.com")
        steps_log.append("Correo ingresado")

        password_input = driver.find_element(By.CSS_SELECTOR, "input[formControlName='password']")
        password_input.clear()
        password_input.send_keys("qwerty")
        steps_log.append("Password ingresado")

        btn_login = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "Boton_inicio"))
        )
        # click via JS para evitar overlay issues
        driver.execute_script("arguments[0].click();", btn_login)
        steps_log.append("Botón de login clickeado")

        # esperar redirección a dashboard o aparición de snackbar
        try:
            WebDriverWait(driver, 7).until(
                lambda d: "Dashboard" in d.current_url or "Dashboard_usuario" in d.current_url
            )
            summary['status'] = "PASSED"
            steps_log.append("Redirección detectada: " + driver.current_url)
        except Exception:
            # intentar obtener snackbar
            try:
                snackbar = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "error-snackbar"))
                )
                steps_log.append("Snackbar de error detectado: " + snackbar.text)
                summary['status'] = "FAILED"
            except Exception:
                steps_log.append("No se detectó redirección ni snackbar. Estado indeterminado.")
                summary['status'] = "FAILED"

        # esperar un instante para que la UI se estabilice y luego screenshot
        time.sleep(0.8)
        steps_log.append("Tomando screenshot...")
        screenshot_b64 = driver.get_screenshot_as_base64()
        steps_log.append("Screenshot tomado (embebido en el reporte).")

    except Exception as e:
        steps_log.append("ERROR EXCEPCIÓN: " + str(e))
        steps_log.append(traceback.format_exc())
        # si driver existe, también tomar screenshot del error
        if driver:
            try:
                screenshot_b64 = driver.get_screenshot_as_base64()
                steps_log.append("Screenshot tomado tras excepción.")
            except Exception:
                steps_log.append("No se pudo tomar screenshot tras excepción.")
    finally:
        if driver:
            driver.quit()
            steps_log.append("WebDriver cerrado.")

        # construir y guardar HTML
        html = build_html_report(report_filename, "Reporte de Test - Login", summary, steps_log, screenshot_b64 or "")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html)

        print(f"Reporte guardado en: {report_path}")
        print("Resumen:", summary['status'])
        return report_path, summary, steps_log

if __name__ == "__main__":
    test_login_and_report()
