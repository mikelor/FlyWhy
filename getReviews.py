import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service


# startWebDriverService()
# Starts the web driver as a service, this improves performance and does not require a manual start
# of the chrome driver.
# TODO: Make it actually work.
def startWebDriverService():
    service = Service('./thirdparty/chromedriver.exe')
    service.start()
    driver = webdriver.Remote(service.service_url)

    return driver

# startWebDriver()
# Starts the web driver for scraping. For best performance, make sure you start the chromedriver
# before running this python script.
def startWebDriver():
    driver = webdriver.Chrome('./thirdparty/chromedriver.exe')
    return driver

# Get's the total number of reviews for a property
#   driver: A handle to the selenium webdriver
#   class:  The specific class of the span tag that holds the review count
def getReviewCount(driver, classId):
    reviewCountSpan = driver.find_element_by_class_name(classId)

    reviewCount = reviewCountSpan.text[0:6]
    reviewCount = reviewCount.replace(',', '')
    reviewCount = int(reviewCount) 

    return reviewCount

def getReviewIds(driver):
    return

def getReviews(driver, reviewIds):
    return

# parseReviews
def parseReviews(driver, url):
    # Get the review url page
    driver.get(url)
    time.sleep(5)

    companyName = driver.find_element_by_xpath('//h1[@class="_3ggwzaPV"]')

    reviewIds = getReviewIds(driver)
    if not reviewIds:
        return

    getReviews(driver, reviewIds)

    items = []
    print()

    return reviewIds

# getAllReviews
def getAllReviews(driver, url, reviewCount):

    urlTemplate = url.replace('.html', '-or{}.html')

    items = []
    offset = 0

    while(True):
        subpageUrl = urlTemplate.format(offset)

        subpageItems = parseReviews(driver, subpageUrl)
        if not subpageItems:
            break

        items += subpageItems

        if len(subpageItems) < 5:
            break

      
        offset += 5

        # For testing purposes, let's stop after fetching a few reviews
        if offset > 10:
            break

    return items



# Entry Point
#driver = startWebDriverService()
driver = startWebDriver()

# Get the Reviews for Alaska Airlines
baseUrl = 'https://www.tripadvisor.com/Airline_Review-d8729017-Reviews-Alaska-Airlines.html'
driver.get(baseUrl)
time.sleep(5) 


airlineReviewCountClassId = '_2tNtmCyi'
reviewCount = getReviewCount(driver, airlineReviewCountClassId)
print(reviewCount)

getAllReviews(driver, baseUrl, reviewCount)