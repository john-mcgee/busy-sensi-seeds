# -*- coding: utf-8 -*-
"""
Created on Mon Dec  9 13:56:18 2019

@author: John-McGee
"""
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
import time
import numpy as np
import pandas as pd
from getpass import getpass


sku_list = [] #List of SKUS to be iterated through to guide pack data collection
pack_dlist = [] #List of dicts to be converted to dataframe and dumped

#Login to service
def login(user, passw):
    username = browser.find_element_by_name("name")
    username.clear()
    username.send_keys(user)
    
    password = browser.find_element_by_name("pass")
    password.clear()
    password.send_keys(passw)

    browser.find_element_by_xpath("//input[@value='Log in']").click()
    
    #Select Reno as Location
    time.sleep(1)
    dropdown = Select(browser.find_element_by_id('edit-active-location'))
    dropdown.select_by_visible_text('LocationName - City')

    # Save user location settings  
    time.sleep(1)
    browser.find_element_by_xpath("//input[@value='Save Settings']").click()

#Request page via browser and return page html
def soup(url="NO URL"):
    if url != "NO URL":
        browser.get(url)
        time.sleep(1)
    html = browser.page_source
    page = BeautifulSoup(html, 'lxml')
    return page

#Scrape all SKUs on a single page and append to sku_list
def sku_page():
    sku_rows = soup().find("tbody").find_all("tr")
    for item in sku_rows:
        row_data = item.get_text(separator=',')
        row_split = row_data.split(",")
        sku = row_split[5].strip("\n").strip()
        sku_list.append(sku)
    time.sleep(1)

# Scrape all Pack IDs and iterate through pack links to build pack data list
def inv_page(url):
    try:
        product_desc = soup(url).find("h1", class_="title").text
    except:
        # 30-sec timer then retry when page is not retreived properly
        print("Stalled. Retrying in 30 sec...")
        time.sleep(30)
        product_desc = soup(url).find("h1", class_="title").text
    time.sleep(1)
    
    # Look for valid pack IDs and create list of URLs
    inv_test = soup().find("table", id="mj_inv_packages")
    if inv_test != None:
        inv_rows = soup().find("table", id="mj_inv_packages").find_all("a")
        for inv in inv_rows:
            detail_urls = []
            if "package-details" in inv["href"] and inv.text != "Edit":
                detail_urls.append(inv["href"])
                pack_id = inv.text.strip(" - INACTIVE")
                
                # Iterate through every url associated with pack IDs to get adtl pack ID
                for url in detail_urls:
                    detail_site = "https://i.gomjfreeway.com{url}".format(url=url)
                    try:
                        adtl_id = soup(detail_site).find("input", id="edit-addl-package-id")["value"]
                    except:
                        print("Stalled. Retrying in 30 sec...")
                        time.sleep(30)
                        adtl_id = soup(detail_site).find("input", id="edit-addl-package-id")["value"]
                    pack_dict = {
                            "Pack ID" : pack_id,
                            "Product" : product_desc,
                            "Adtl Pack ID" : adtl_id,
                            "SKU" : sku_each}
                    pack_dlist.append(pack_dict)
                    time.sleep(1)
 
# Prepare the soup and login
site_url = "https://i.gomjfreeway.com/LocationName/"
chrome_options = Options()
browser = webdriver.Chrome()
soup(site_url)
username = input("Username: ")
password = getpass(prompt="Password: ")               
login(username, password)

# Navigate to inventory page and scrape first page
browser.get("https://i.gomjfreeway.com/LocationName/inventory/")

# Click next page and repeat page scrape until no more pages
error_count = 0
while error_count == 0:
    sku_page()
    try:
        time.sleep(1)
        browser.find_element_by_xpath("//li[@class='pager-next']").click()
    except:
        print("Can't find next page. Try again in 5 secs")
        time.sleep(5)
        try:
            browser.find_element_by_xpath("//li[@class='pager-next']").click()
        except:
            print("Done with SKUs")
            error_count = 1
            
# Save SKUs to CSV as backup and break loop
sku_df = pd.DataFrame({'count':range(len(sku_list))})
sku_df['Sku'] = pd.Series(sku_list)
sku_df.to_csv('SKU-active.csv', index=False)
    
# Iterate through the SKU list and navigate to each SKU inventory page
for sku_each in sku_list:  
    inv_page("https://i.gomjfreeway.com/LocationName/node/{sku}/adjust/any/".format(sku=sku_each))

# Create datafrome from list of dicts and dump to CSV
df_packs = pd.DataFrame(pack_dlist, columns=["Pack ID", "Product", "Adtl Pack ID","SKU"])
df_packs.to_csv('packs-active.csv', index=False)


        
