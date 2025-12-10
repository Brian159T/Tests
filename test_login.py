from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

def test_login_correcto():
    
    chrome_options = Options()
    chrome_options.binary_location = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    driver.get("http://localhost:4200/login")

    
    correo_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[formControlName='correo']"))
    )
    correo_input.clear()
    correo_input.send_keys("brayanzegarra321@gmail.com")

  
    password_input = driver.find_element(By.CSS_SELECTOR, "input[formControlName='password']")
    password_input.clear()
    password_input.send_keys("qwerty")

   
    btn_login = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "Boton_inicio"))
    )
    
    driver.execute_script("arguments[0].click();", btn_login)

    
    try:
        
        WebDriverWait(driver, 5).until(
            lambda d: "Dashboard" in d.current_url or "Dashboard_usuario" in d.current_url
        )
        print("✅ Login correcto! Redirigido a:", driver.current_url)
    except:
        
        try:
            snackbar = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "error-snackbar"))
            )
            print("❌ Login fallido! Mensaje de error:", snackbar.text)
        except:
            print("⚠️ Login fallido, no se detectó snackbar ni redirección.")

    
    driver.quit()


if __name__ == "__main__":
    test_login_correcto()
