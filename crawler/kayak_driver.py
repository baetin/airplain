from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
from datetime import date
import time

def run_single_flight_check(start_area: str, end_area: str, d: date):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    options.page_load_strategy = 'eager'  # 빠르게 로딩

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(20)

    try:
        date_str = d.strftime('%Y-%m-%d')
        url = f"https://www.kayak.com/flights/{start_area}-{end_area}/{date_str}?sort=bestflight_a"
        print(f"🔗 접속 URL: {url}")
        driver.get(url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "e2GB-price-text"))
        )
        print("✅ 가격 요소 로딩 완료")

        containers = driver.find_elements(By.CLASS_NAME, "nrc6-inner")
        result_list = []  # ✅ 반복문 밖으로 이동

        for idx in range(len(containers)):
            try:
                # 반복마다 최신 요소로 재조회 (stale 방지)
                containers = driver.find_elements(By.CLASS_NAME, "nrc6-inner")
                container = containers[idx]

                for attempt in range(3):
                    try:
                        price_el = container.find_element(By.CLASS_NAME, "e2GB-price-text")
                        airline_el = container.find_element(By.CLASS_NAME, "c_cgF.c_cgF-mod-variant-default")
                        break
                    except StaleElementReferenceException:
                        if attempt < 2:
                            time.sleep(0.5)
                        else:
                            print("⚠️ 요소 재시도 실패 (stale)")
                            price_el = None
                            airline_el = None

                if not price_el or not airline_el:
                    continue

                price_text = price_el.text.replace("$", "").replace(",", "").strip()
                airline_text = (
                    airline_el.get_attribute("aria-label") or
                    airline_el.get_attribute("title") or
                    airline_el.text.strip()
                )

                if price_text.isdigit():
                    price = int(price_text)
                    print(f"💲 감지된 가격: {price} / 🛫 항공사: {airline_text}")
                    result_list.append({"price": price, "airline": airline_text})

            except Exception as e:
                print(f"⚠️ 일부 항목 파싱 실패 (외부): {e}")
                continue

        if result_list:
            return min(result_list, key=lambda x: x["price"])
        else:
            return {"price": 0, "airline": ""}

    except Exception as e:
        print("❌ 예외 발생:", e)
        return {"price": 0, "airline": ""}

    finally:
        driver.quit()
