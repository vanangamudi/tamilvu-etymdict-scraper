from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium import webdriver

# Start the WebDriver and load the page
wd = webdriver.Firefox()
wd.get(URL)

# Wait for the dynamically loaded elements to show up
WebDriverWait(wd, 10).until(
    EC.visibility_of_element_located((By.CLASS_NAME, "pricerow")))

# And grab the page HTML source
html_page = wd.page_source
wd.quit()

# Now you can use html_page as you like
from bs4 import BeautifulSoup
soup = BeautifulSoup(html_page)
