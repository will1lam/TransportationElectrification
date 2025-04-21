#Used to first with credientals.py to determine whether traffic data is available. 
#Needs pems_output.xlsx downloaded for the stations of a given highway route.
#Then use truckFlowData.py to download the data for stations that have data.

from playwright.sync_api import sync_playwright
import pandas as pd
import credentials

# Load the Excel file
file_path = 'pems_output.xlsx'
sheet_name = 'Report Data'  # Assuming the data is in the first sheet
df = pd.read_excel(file_path, sheet_name=sheet_name)

# Extract all sensor IDs from column H
sensor_ids = df['ID'].dropna().unique()  # Drop NaN values and get unique IDs

# Base URL
base_url = "https://pems.dot.ca.gov/?dnode=VDS&content=loops&tab=det_timeseries&station_id="

# Construct URLs for all IDs
urls = [base_url + str(int(sensor_id)) for sensor_id in sensor_ids]

# Initialize a list to store the results
results = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=10)
    page = browser.new_page()
    page.goto('https://pems.dot.ca.gov/')

    try:
        # Fill login form
        page.fill('input#username', credentials.username)
        page.fill('input#password', credentials.password)
        page.click('input[type=submit]')

        # Wait for a post-login element to confirm login
        page.wait_for_selector('div.text', timeout=3000)  # Wait up to 2 seconds for login confirmation
        print("Login successful.")

        for url in urls:
            try:
                # Extract the sensor ID from the URL
                sensor_id = url.split('station_id=')[1]
                print(f"Processing URL: {url} (Sensor ID: {sensor_id})")

                # Navigate to the current URL
                page.goto(url)
                
                # Wait for the dropdown selector to appear with a reduced timeout (1 second)
                page.wait_for_selector('select[id=q]', timeout=1000)  # 1000ms = 1 second
                
                # Try to select the 'truck_flow' option with a reduced timeout (1 second)
                page.select_option('select[id=q]', value='truck_flow', timeout=1000)  # 1000ms = 1 second
                
                # If successful, print a success message
                print(f"Selected 'truck_flow' for URL: {url}")

                # Record 1 for truck_flow  
                results.append({'ID': sensor_id, 'Truck_Flow': 1})
                print(f"Added result: ID={sensor_id}, Truck_Flow=1")
            
            except Exception as e:
                # If 'truck_flow' is not found or any other error occurs, record 0 for truck_flow
                print(f"Skipping URL: {url} - 'truck_flow' not found or error: {e}")
                results.append({'ID': sensor_id, 'Truck_Flow': 0})
                print(f"Added result: ID={sensor_id}, Truck_Flow=0")
    
    except Exception as e:
        # Handle any unexpected errors during the process
        print(f"An error occurred: {e}")
    
    finally:
        # Close the browser after processing the URLs
        browser.close()

# Print the results list for debugging
print("Results list:")
print(results)

# Create a DataFrame from the results
results_df = pd.DataFrame(results)

# Save the DataFrame to a CSV file
results_df.to_csv('truck_flow_results.csv', index=False)
print("Results saved to 'truck_flow_results.csv'")