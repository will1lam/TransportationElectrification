#Used with credentials.py to consolidate truck flow data of given stations (truck_flow_results.py) into one excel sheet.
#Refer to trafficData.py to gather truck flow availability for given stations.

from playwright.sync_api import sync_playwright
import pandas as pd
import credentials

# Config
DEBUG = True
MAX_STATIONS = None  # Set to None to process all
BASE_URL = "https://pems.dot.ca.gov/?dnode=VDS&content=loops&tab=det_timeseries&station_id="

df = pd.read_csv('truck_flow_results.csv')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=not DEBUG, slow_mo=10)
    page = browser.new_page()
    page.goto('https://pems.dot.ca.gov/')

    try:
        # Login
        print("Logging in...")
        page.fill('input#username', credentials.username)
        page.fill('input#password', credentials.password)
        page.click('input[type=submit]')
        
        if "Login Failed" in page.content():
            raise Exception("Login failed!")
        print("Login successful.")

        with pd.ExcelWriter('station_data.xlsx', engine='openpyxl') as writer:
            counter = 0
            for index, row in df.iterrows():
                if MAX_STATIONS and counter >= MAX_STATIONS:
                    break
                station = row.iloc[0]
                truck_flow = row.iloc[1]
                if truck_flow == 1:
                    try:
                        url = BASE_URL + str(station)
                        page.goto(url)

                        # Wait for the dropdown selector to appear with a reduced timeout (1 second)
                        page.wait_for_selector('select[id=q]', timeout=1000)  # 1000ms = 1 second
                        
                        # Try to select the 'truck_flow' option with a reduced timeout (1 second)
                        page.select_option('select[id=q]', value='truck_flow', timeout=1000)  # 1000ms = 1 second
                        page.click('input[type="image"][alt="View Table"]')

                        # Scrape table
                        table = page.wait_for_selector("table.inlayTable", timeout=10000)

                        # Wait for at least one row to appear
                        page.wait_for_selector("table.inlayTable tbody tr", timeout=10000)

                        # Extract the full table HTML
                        html = table.evaluate("node => node.outerHTML")
                        #print("Extracted HTML:\n", html)  # Debugging step

                        # Read table using pandas
                        scraped_data = pd.read_html(html)[0]

                        if scraped_data.empty:
                            print(f"Station {station}: Empty table")
                            continue

                        # Save to Excel
                        scraped_data.to_excel(writer, sheet_name=str(station))
                        counter += 1
                        print(f"Saved station {station}")
                        page.wait_for_timeout(1000)

                    except Exception as e:
                        print(f"Error processing station {station}: {e}")
                        continue

            # Ensure at least one sheet exists
            if counter == 0:
                pd.DataFrame({"Error": ["No valid stations processed"]}).to_excel(
                    writer, sheet_name="Error"
                )

    except Exception as e:
        print(f"Critical error: {e}")
    finally:
        browser.close()