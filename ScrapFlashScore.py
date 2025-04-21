from time import sleep

from selenium import webdriver
import time
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
# asynchronous website needs to be awaited
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
#import pymsql
from databricks.connect import DatabricksSession
import psycopg2
from datetime import datetime
from selenium.webdriver.chrome.options import Options
import re

def scrap_rank_data():
    driver = webdriver.Chrome()
    driver.get("https://www.flashscore.com/tennis/rankings/atp/")

    css_selector = ""

    wait = WebDriverWait(driver, 10)
    elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.rankingTable__table")))
    filtered_data = []

    elem = str(elem.text)
    lines = [line.strip() for line in elem.split("\n") if line.strip()]
    lines = list(filter(lambda x: "+" not in x, lines))
    lines = list(filter(lambda x: "-" not in x, lines))

    # Process the data, skipping entries with + or -
    i = 0
    while i < len(lines):
        if lines[i][-1] == ".":  # Detect start of new player entry
            rank = int(lines[i].replace(".", ""))
            name = lines[i + 1]
            change = lines[i + 2]  # Ranking change (+ or -)

            # Skip entry if the ranking change contains '+' or '-'
            if "+" in change or "-" in change:
                i += 6  # Skip this entire player's data
                continue

            nationality = lines[i + 2]
            points = int(lines[i + 3])
            tournaments = int(lines[i + 4].replace(".", ""))
            #plyr_nm, cnty_nm, pnt, trnm
            player = {
                #"Rank": rank,
                "plyr_nm": name,
                "cnty_nm": nationality,
                "pnt": points,
                "trnm": tournaments
            }
            filtered_data.append(player)
            i += 5  # Move to the next player entry
        else:
            i += 1  # Move to next line if not a valid entry start

    # Print the filtered data
    for player in filtered_data:
        print(player)

    driver.quit()
    print("log : filtered data")
    print(filtered_data)

    return filtered_data

def scrap_ao_open_data():
    # to prevent the browser from closing
    options = Options()
    options.add_experimental_option("detach", True)

    driver = webdriver.Chrome(options=options)
    driver.get("https://www.flashscore.com/tennis/atp-singles/australian-open/results/")

    css_selector = ""
    wait = WebDriverWait(driver, 10)
    results = []

    # append the match information on the 'match list'


    # closing the cookie banner
    try:
        # Wait for the cookie banner and accept it
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, 'onetrust-accept-btn-handler'))  # Example ID for cookie banner
        ).click()
        print("Cookie banner accepted.")

    except Exception as e:
        print("No cookie banner found or failed to close it:", e)

    # clickinig "Show more matches" until there is no more butten left on the page
    # 1. collecting data from the results
    '''
    while True:
        # until there is no "Show more matches" button left
        try:
            # scrolling down to
            wait.until(EC.invisibility_of_element_located(
                (By.ID, 'loading-spinner')))  # Replace with your actual spinner selector

            # Then wait for the desired element to be clickable
            element = wait.until(
                EC.element_to_be_clickable((By.XPATH, '//a[contains(@class, "event__more event__more--static")]'))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            driver.execute_script("arguments[0].click();", element)
            print("log: Click action performed after scrolling.")
            time.sleep(1)

        except Exception as e:
            print("No more button on the page")
            break

    elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.sportName.tennis")))
    elem = str(elem.text).split("\n")
    print(elem)
    # filtered_data = []
    idx = next((i for i, s in enumerate(elem) if "Qualification" in s), -1)
    # elem을 메인 경기와 Qualification 두 개로 나눈다
    elem_1 = elem[:idx]
    elem_2 = elem[idx:]

    # filtering the list of the main match and the qualification match
    idx = next((i for i, s in enumerate(elem_1) if "FINAL" in s), -1)
    elem_1 = elem_1[idx:]

    idx = next((i for i, s in enumerate(elem_2) if "FINAL" in s), -1)
    elem_2 = elem_2[idx:]

    print("this is index : " + str(idx))
    print(elem[idx])
    print("elem 1 : ")
    print(elem_1)
    print("elem 2 : ")
    print(elem_2)

    pattern = r"\b\d{2}\.\d{2}\.\s\d{2}:\d{2}\b"

    valid_rounds = {
        'FINAL', 'SEMI-FINALS', 'QUARTER-FINALS', '1/8-FINALS', '1/16-FINALS', '1/32-FINALS', '1/64-FINALS'
    }
    results = []
    i = 0
    current_round = None
    while i < len(elem_1):
        item = elem_1[i].upper()
        if item in valid_rounds:
            current_round = elem_1[i]
            i += 1
        elif re.fullmatch(pattern, elem_1[i]) and i + 4 < len(elem_1):
            # Assume a valid match block: date, player1, player2, score1, score2
            # match_data = elem_1[i:i + 5]
            results.append({
                'match_id': '10001',
                'match_nm': 'Australian Open',
                'trnm_nm': current_round,
                'match_dt': "2025-"+elem_1[i][3:5]+"-"+elem_1[i][0:2],
                'match_tm' : elem_1[i][7:],
                'plyr_id_1' : "",
                'plyr_nm_1' : elem_1[i+1],
                'plyr_id_2' : "",
                'plyr_nm_2' : elem_1[i+2],
                'plyr_pnt_1' : int(elem_1[i+3]),
                'plyr_pnt_2' : int(elem_1[i+4])
            })
            i += 5
        else:
           i += 1  # Skip if not part of match data or no current round

    current_round = None
    i = 0
    while i < len(elem_2):
        item = elem_2[i].upper()
        if item in valid_rounds:
            current_round = elem_2[i]
            i += 1
        elif re.fullmatch(pattern, elem_2[i]) and i + 4 < len(elem_2):
            # Assume a valid match block: date, player1, player2, score1, score2
            # match_data = elem_1[i:i + 5]
            results.append({
                'match_id': '10001',
                'match_nm': 'Australian Open',
                'trnm_nm': current_round,
                'match_dt': "2025-" + elem_2[i][3:5] + "-" + elem_2[i][0:2],
                'match_tm': elem_2[i][7:],
                'plyr_id_1': "",
                'plyr_nm_1': elem_2[i + 1],
                'plyr_id_2': "",
                'plyr_nm_2': elem_2[i + 2],
                'plyr_pnt_1': int(elem_2[i + 3]),
                'plyr_pnt_2': int(elem_2[i + 4])
            })
            i += 5
        else:
            i += 1  # Skip if not part of match data or no current round

    '''

    # 2. clicking each
    # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.rankingTable__table")))
    # wait.until(EC.presence_of_element_located((By.CLASS_NAME), "eventRowLink"))
    matches = driver.find_elements(By.CLASS_NAME, "eventRowLink")
    print("clicking each : ")
    print(matches)
    main_window = driver.current_window_handle

    for idx, i in enumerate(matches):
        try:
            # only testing on the index 1, Sinner case. Later needs to be removed, the following 2 lines
            if idx == 1:
                return results

            # scroll
            driver.execute_script("arguments[0].scrollIntoView(true);",i)
            driver.execute_script("arguments[0].click();",i)
            print("clicking worked")
            matches = driver.find_elements(By.CLASS_NAME, "eventRowLink")
            print("log : enumerating the match index " + str(idx))

            # closing the current tab
            try:
                main_window = driver.current_window_handle
                # Click the link that opens a new tab
                '''link = driver.find_element(By.CLASS_NAME, "eventrowLink")
                link.click()'''

                # Wait for new tab to appear
                WebDriverWait(driver, 10).until(lambda d: len(d.window_handles) > 1)

                # Switch to the new tab
                new_tab = [handle for handle in driver.window_handles if handle != main_window][0]
                driver.switch_to.window(new_tab)

                # You’re now in the new tab — do whatever you want here
                time.sleep(2)  # simulate some interaction

                # Close the current tab
                # driver.close()
                # 3. getting the info of the match
                match_detl_data(driver) # has to pass the driver otherwise, creating the new browser


                # Switch back to original tab
                driver.switch_to.window(main_window)
                print("Closed new tab and returned to main tab.")
                print("Popup closed.")
            except Exception as e:
                print("No popup or couldn't close it:", {e})

        except Exception as e:
            print(f"Could not click element {idx}: {e}")
            # driver.quit()
            time.sleep(2)
            break

    # scroll down

    # driver.quit()

    return results

def match_detl_data(driver):
    print("log : match_detl_data")
    # 여기에서 webdriver이 없다 오류 뜨는데.. 졸리다! 내일도 파이팅
    css_selector = ""
    wait = WebDriverWait(driver, 10) # defining wait object first
    print("log : 3")
    try:
        stats_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Stats')]"))
        )
        stats_button.click()

        # wait
        wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "div.stats-container")  # Replace with a real selector for new content
        ))
        time.sleep(5)
        print(driver.page_source)
        print("one day closer")

        print("log : 4")

        time.sleep(10)
    except Exception as e:
        print({e})

    #elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.selected")))
    print("log : 4")
    # 니코 잘생겼어 나 졸려 one day closer

# from here connection to postgresql
# PostgreSQL 데이터베이스에 연결
def connect_db():
    conn = psycopg2.connect(
        dbname='postgres',
        user='postgres',
        password='sw100400^^',
        host='localhost',
        port='5432'
    )
    return conn


# insert data
def insert_data(conn, data, flag):
    cursor = conn.cursor()

    if flag == "":
        insert_query = "INSERT INTO tennis_rank_bs (app_dt, plyr_nm, cnty_nm, pnt, trnm) VALUES (%s ,%s, %s, %s, %s)"
        cursor.executemany(insert_query, data)  # Execute multiple rows of data
    elif flag == "data_au_open":
        insert_query = "INSERT INTO match_dc (match_id, match_nm, trnm_nm, match_dt, match_tm, plyr_id_1, plyr_nm_1, plyr_id_2, plyr_nm_2, plyr_pnt_1, plyr_pnt_2) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)" #\
                       #"ON CONFLICT (match_id, match_nm, trnm_nm, match_dt) DO UPDATE SET match_id = EXCLUDED.match_id, match_nm = EXCLUDED.match_nm, trnm_nm = EXCLUDED.trnm_nm, match_dt = EXCLUDED.match_dt"
        cursor.executemany(insert_query, data)


    conn.commit()
    cursor.close()



def main():
    # 1. scrap data for the rank
    flag = ""
    '''data_dict = scrap_rank_data()
    app_dt = datetime.now()
    app_dt = app_dt.strftime('%Y-%m-%d')
    print("app_dt : "+app_dt)
    data = [(app_dt, player['plyr_nm'], player['cnty_nm'], player['pnt'], player['trnm']) for player in data_dict]
    print("in the main function")
    print(data)

    conn = connect_db()
    insert_data(conn, data)
    conn.close()'''


    # 2. scrap data for the match score
    # starting from the AUS open
    data_au_open = scrap_ao_open_data()
    data_filtered = [(match['match_id'], match['match_nm'], match['trnm_nm'], match['match_dt'], match['match_tm'], match['plyr_id_1'], match['plyr_nm_1'], match['plyr_id_2'], match['plyr_nm_2'], match['plyr_pnt_1'], match['plyr_pnt_2']) for match in data_au_open]
    flag = "data_au_open"
    #conn = connect_db()
    #insert_data(conn, data_filtered, flag)

    print("end of the main function")


if __name__ == '__main__':
    main()
