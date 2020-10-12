from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.service import Service

import time

#
# Classes
#
class Review:
    def __init__(self, id, rating):
        self.Id = id
        self.Rating = rating
        self.Itinerary = ""

        self.Region = ""
        self.Class = ""
        self.DateOfReview = ""
        self.DateofTravel = ""
        self.Title = ""
        self.Text = ""

    def setItinerary(self, itinerary):
        self.Itinerary = itinerary


class Itinerary:
    def __init__(self, origin, destination):
        self.Origin = origin
        self.Destination = destination
    

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



def getReviews(driver, reviewIds):
    return

# parseReview
def parseReviewDiv(reviewDiv):
    review = ""
    print(reviewDiv.text)
    
    return review




#
# getReviewCount()
#
# Get's the total number of reviews for a property
#   driver: A handle to the selenium webdriver
#   class:  The specific class of the span tag that holds the review count
def getReviewCount(driver, classId):
    reviewCountSpan = driver.find_element_by_class_name(classId)

    reviewCount = reviewCountSpan.text[0:6]
    reviewCount = reviewCount.replace(',', '')
    reviewCount = int(reviewCount) 

    return reviewCount

#
# getAllReviews(driver, url, reviewCount)
#
def getReviews(driver, url, reviewCount):

    urlTemplate = url.replace('.html', '-or{}.html')

    reviews = []
    offset = 0

    while(True):
        reviewUrl = urlTemplate.format(offset)

        reviewSubset = getReviewsForUrl(driver, reviewUrl)
        if not reviewSubset:
            break

        reviews += reviewSubset

        if len(reviewSubset) < 5:
            break
      
        offset += 5

        # For testing purposes, let's stop after fetching a few reviews
        if offset > 5:
            break

    return reviews

#
# getReviewsForUrl
#
def getReviewsForUrl(driver, url):
    # Get the review url page
    driver.get(url)
    time.sleep(5)

    companyName = driver.find_element_by_xpath('//h1[@class="_3ggwzaPV"]')
    
    reviews = []
    reviewDivs = driver.find_elements_by_xpath('//div[@data-reviewid]')
    for reviewDiv in reviewDivs:
        reviewId = reviewDiv.get_attribute('data-reviewid') 
        rating   = getReviewRating(reviewDiv)
        review   = Review(reviewId, rating)

        review.setItinerary(getReviewItinerary(reviewDiv))

        # Add the review to the list
        reviews.append(review)

    return reviews

#
# getReviewRating(reviewDiv)
#
# The rating for the review is stored as a class on an inner span with two classes applied
# The first class identifies it as a "bubble rating", while the second defines the level from 1 to 5
# 
# Example class="ui_bubble_rating bubble_10"
#
def getReviewRating(reviewDiv):
    ratingString = (((reviewDiv.find_element_by_class_name('ui_bubble_rating')).get_attribute('class')).split())[1]
    rating = (int(ratingString[-2:]))
    rating = rating/10

    return rating

#
# getReviewItinerary
#
def getReviewItinerary(reviewDiv):
    itineraryString = (reviewDiv.find_elements_by_class_name('_3tp-5a1G')[0]).text
    itineraryList = itineraryString.split(' - ')
    itinerary = Itinerary(itineraryList[0], itineraryList[1])

    return itinerary
####
#
# Entry Point
#
####
#driver = startWebDriverService()
driver = startWebDriver()

# Get the Reviews for Alaska Airlines
baseUrl = 'https://www.tripadvisor.com/Airline_Review-d8729017-Reviews-Alaska-Airlines.html'
driver.get(baseUrl)
time.sleep(5) 

airlineReviewCountClassId = '_2tNtmCyi'
reviewCount = getReviewCount(driver, airlineReviewCountClassId)

reviews = getReviews(driver, baseUrl, reviewCount)

for review in reviews:
    print(review.Id, review.Rating, review.Itinerary.Origin, review.Itinerary.Destination)