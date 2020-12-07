import csv
import logging
from logging import log, raiseExceptions
import platform


import selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException


logging.basicConfig(level=logging.WARN)

D_PATH_CHROMEDRIVER = {
    'Windows':'./thirdparty/chromedriver.exe',
    'Darwin':'./thirdparty/chromedriver'
}


#
# Classes
#

class Review:
    def __init__(self, id, rating):
        self.Id = id
        self.Rating = rating

        self.Date = ""
        self.TravelDate = ""
        self.Title = ""
        self.Text = ""

        self.Itinerary = ""
        self.Reviewer = ""
        self.CategoryRatings = {}

    def setItinerary(self, itinerary):
        self.Itinerary = itinerary

    def setReviewer(self, reviewer):
        self.Reviewer = reviewer

class Itinerary:
    def __init__(self, origin, destination, region, cabin):
        self.Origin = origin
        self.Destination = destination
        self.Region = region
        self.Cabin = cabin

class Reviewer:
    def __init__(self, id, name, location):
        self.Id = id
        self.Name = name
        self.Location = location

class UnsupportedOSError(Exception):
    pass
    
#
# Functions
#

def getChromeDriverPath():
    """ Selects the correct ChromeDriver version depending on OS. 
    Currently supported: 'Windows' or 'Darwin' (Mac) 
    """
    sOS = platform.system()
    if not sOS in D_PATH_CHROMEDRIVER: raise UnsupportedOSError
    return D_PATH_CHROMEDRIVER.get(sOS, None)


def startWebDriverService():
    """ Starts the web driver as a service, this improves performance and does not require a manual start
    of the chrome driver.
    TODO: Make it actually work.
    """
    service = Service(D_PATH_CHROMEDRIVER)
    service.start()
    driver = webdriver.Remote(service.service_url)
    return driver


def startWebDriver():
    """ Starts the web driver for scraping. For best performance, make sure you start the chromedriver
    before running this python script.
    """
    options = Options()
    options.headless = True
    options.add_argument('log-level=1') # Set chrome to log WARNINGs and above   
    driver = webdriver.Chrome(getChromeDriverPath(), options=options)
    return driver


def getReviewCount(driver, classId):
    """Get's the total number of reviews for a property
        driver: A handle to the selenium webdriver
        class:  The specific class of the span tag that holds the review count
    """
    reviewCountSpan = driver.find_element_by_class_name(classId)

    reviewCount = reviewCountSpan.text[0:6]
    reviewCount = reviewCount.replace(',', '')
    reviewCount = int(reviewCount) 

    return reviewCount


def getReviewsForUrl(driver, userReviewDriver, url):
    """Each page has five reviews, this will get the high level review information for each review, and 
    then iterate through each review to get *even more* :) detail information by calling the url for
    each individual review.
    """
    # Get the review url page
    driver.get(url)
    

    reviewDivs = getReviewDivs(driver)
    
    reviews = []
    for reviewDiv in reviewDivs:
        reviewId = getReviewId(reviewDiv)
        rating   = getReviewRating(reviewDiv)
        review   = Review(reviewId, rating)

        # Get Itinerary
        review.setItinerary(getReviewItinerary(reviewId, reviewDiv))
        review = getReviewDetail(userReviewDriver, reviewDiv, review)
        
        # Add the review to the list
        reviews.append(review)

    return reviews

def getReviewDivs(driver):
    reviewDivs = driver.find_elements_by_xpath('//div[@data-reviewid]')
    return reviewDivs

def getReviewId(reviewDiv):
    reviewId = reviewDiv.get_attribute('data-reviewid') 
    return reviewId

def getReviewRating(reviewDiv):
    """ The rating for the review is stored as a class on an inner span with two classes applied
    The first class identifies it as a "bubble rating", while the second defines the level from 1 to 5

    Example: class="ui_bubble_rating bubble_10"
    """
    ratingString = (((reviewDiv.find_element_by_class_name('ui_bubble_rating')).get_attribute('class')).split())[1]
    rating = (int(ratingString[-2:]))
    rating = rating/10

    return rating


def getReviewItinerary(reviewId, reviewDiv):
    """ In this case, we're considering an Itinerary to be a reviewer's origin, destination, region of travel, and class of cabin for 
    travel. We don't have any specifics such as the Date of Travel (other than the "month", or date of review)
    """

    originDestinationString = "  -  "
    originDestinationList = []
    region = ""
    cabin = ""

    try:
        itineraryItems = (reviewDiv.find_elements_by_class_name('_3tp-5a1G'))

        for x, itineraryItem in enumerate(itineraryItems):
            if x == 0:
                originDestinationString = itineraryItem.text

            elif x == 1:
                region = itineraryItem.text
            elif x == 2:
                cabin = itineraryItem.text

    except NoSuchElementException:
        logging.warning(f"No Reviewer.Id found for Review.Id: {reviewId}") 

    originDestinationList = originDestinationString.split(' - ')
    itinerary = Itinerary(originDestinationList[0], originDestinationList[1], region, cabin)

    return itinerary

def getReviewDetail(userReviewDriver, reviewDiv, review):
    """ Dive in a little deeper on this review by finding and then calling the detail review page.
    There is some information that's missing, or just easier to get at on the detail review page, and this can
    potentially be leveraged for other types of reviews
    TODO: #2 Get category ratings if they exist
    """
    userReviewUrl = reviewDiv.find_element_by_class_name('ocfR3SKN').get_attribute('href')
    userReviewDriver.get(userReviewUrl)

    userReviewDiv = userReviewDriver.find_element_by_xpath('//div[@id="review_' + review.Id + '"]') 

    # Get the review
    review.Date = userReviewDiv.find_element_by_xpath('//span[@class="ratingDate relativeDate"]').get_attribute('title')
    review.TravelDate = userReviewDiv.find_element_by_xpath('//div[@data-prwidget-name="reviews_stay_date_hsx"]').text[16:] # Trime "Date of Travel: "
    review.Title = userReviewDriver.find_element_by_xpath('//div/a[@id="rn' + review.Id + '"]/span').text
    review.Text = userReviewDiv.find_element_by_xpath('//div[@class="entry"]/p').text

    # Gather information about the reviewer 

    id = getReviewerId(review.Id, userReviewDiv)
    name = getReviewerName(review.Id, userReviewDiv)
    location = getReviewerLocation(review.Id, userReviewDiv)
    ratingElements = getRatingElements(review.Id, userReviewDiv)
    
    starRatings = []
    ratingCategories = []
 
    # Iterate through the collection and using the modulus function to alternate between parsing
    for x, ratingElement in enumerate(ratingElements):
        if(x % 2) == 0:
            ratingString = (ratingElement.get_attribute('class').split())[1]
            starRating = (int(ratingString[-2:]))
            starRating = starRating/10
            starRatings.append(starRating)
        else:
            category = ratingElement.text
            ratingCategories.append(category)


    for x, categoryText in enumerate(ratingCategories):
        review.CategoryRatings[categoryText] = starRatings[x]

    review.setReviewer(Reviewer(id, name, location))

    return review    

def getReviewerId(reviewId, userReviewDiv):
    id = ""
    try:
        id = userReviewDiv.find_element_by_xpath('//div[@class="member_info"]/div').get_attribute('id') 
        # Remove Pre/Post Text and Isolate the UID (eg UID_A455850D086316E0157BE50C4EB2115E-SRC_773635392). 
        id = (((id.split('_'))[1]).split('-'))[0]
    except NoSuchElementException:
        logging.warning(f"No Reviewer.Id found for Review.Id: {reviewId}")

    return id

def getReviewerLocation(reviewId, userReviewDiv):
    location = ""
    try:
        location = userReviewDiv.find_element_by_xpath('//div[@class="location"]/span').text
    except NoSuchElementException:
        logging.warning(f"No location found for Review.Id: {reviewId}")

    return location
    
def getReviewerName(reviewId, userReviewDiv):
    name=""
    try:
        name = userReviewDiv.find_element_by_xpath('//div[@class="username mo"]/span').text
    except NoSuchElementException:
        logging.warning(f"No name found for Review.Id: {reviewId}")
    
    return name

def getRatingElements(reviewId, userReviewDiv):
    """
    This returns a collection of divs that contain both the bubble rating and rating description
    """
    ratingElements = userReviewDiv.find_elements_by_xpath('//div[@id="review_' + reviewId + '"]//li[@class="recommend-answer"]/div')
    return ratingElements

def _addHeadersToCsv(fCsv):
    """ Add headers to a CSV filestream handle """
    reviewFileWriter = csv.writer(fCsv, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
        
    reviewFileWriter.writerow(["Id",
                                "Rating",
                                "Reviewer.Id",
                                "Reviewer.Name",
                                "Reviewer.Location",
                                "Itinerary.Origin",
                                "Itinerary.Destination",
                                "Itinerary.Region",
                                "Itinerary.Cabin",
                                "Date",
                                "TravelDate",
                                "Title",
                                "Text",
                                "CategoryRatings"])

    return fCsv


def appendToCsv(reviews, fCsv):
    """ Append the data to a csv filestream handle. """

    reviewFileWriter = csv.writer(fCsv, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
        
    for review in reviews:
        reviewFileWriter.writerow([review.Id, 
                                    review.Rating, 
                                    review.Reviewer.Id,
                                    review.Reviewer.Name,
                                    review.Reviewer.Location,
                                    review.Itinerary.Origin, 
                                    review.Itinerary.Destination, 
                                    review.Itinerary.Region, 
                                    review.Itinerary.Cabin,
                                    review.Date,
                                    review.TravelDate,
                                    review.Title,
                                    review.Text,
                                    review.CategoryRatings])

    return fCsv


def streamReviewsToCsv(
        max=5,
        offset=0, 
        pathCsv='./data/raw/myreviews{}.csv', 
        baseUrl='https://www.tripadvisor.com/Airline_Review-d8729017-Reviews-Alaska-Airlines-or{}.html', 
        preview=False):
    """
    Fetch reviews by page and stream to CSV file

    Parameters:
        - max: stop after this number of reviews is reached, or set to None to continue exhaustively
        - pathCsv: file path to save the desired csv file 
        - preview: print the results to terminal

    """
    urlTemplate = baseUrl

    # baseUrl will not contain a template if started at root url, so let's add it
    if baseUrl.find('-or{}.html') == -1:
        urlTemplate = baseUrl.replace('.html', '-or{}.html')


    # Start the primary webdriver that loops through the pages of reviews
    driver = startWebDriver()
    driver.implicitly_wait(15) 
    
    # Startup a second webdriver to bring up more detail pages on the user review while
    # still maintaining the original driver to page through all reviews
    userReviewDriver = startWebDriver()
    userReviewDriver.implicitly_wait(15)

    # Open a new CSV file and add the headers.  Note: it will clobber an existing file.
    fReviewCsv = open(pathCsv.format(offset), "w", encoding="utf-8")
    fReviewCsv = _addHeadersToCsv(fReviewCsv)

    # Get the Reviews for given airline at the base url
    driver.get(baseUrl)

    # Get the total review count for informational purposes
    airlineReviewCountClassId = '_2tNtmCyi'
    reviewCount = getReviewCount(driver, airlineReviewCountClassId)
    print(f"Fetching {max} of {reviewCount} reviews...")

    # Loop through all the results or until you hit the max and stream results
    while(True):
        reviewUrl = urlTemplate.format(offset)
        reviewSubset = getReviewsForUrl(driver, userReviewDriver, reviewUrl)

        # If not more reviews, complete loop
        if not reviewSubset: break

        # Preview reviews in terminal
        if preview:
            for review in reviewSubset:
                print("|".join([str(x) for x in [review.Id,
                    review.Rating,
                    review.Reviewer.Id,
                    review.Reviewer.Name,
                    review.Reviewer.Location,
                    review.Itinerary.Origin,
                    review.Itinerary.Destination,
                    review.Itinerary.Region,
                    review.Itinerary.Cabin,
                    review.Date,
                    review.TravelDate,
                    review.Title,
                    review.Text]]))

        # Batch save reviews to file
        fReviewCsv = appendToCsv(reviewSubset, fReviewCsv)

        # Update counter
        offset += len(reviewSubset)
        print(f"{offset} Reviews Processed @ {reviewUrl}")


        if max and offset >= max: 
            print("Desired max {max} reviews reached {offset}, stopping now.")
            break

    # Cleanup
    fReviewCsv.close()
    

if __name__ == "__main__":
    streamReviewsToCsv(
        20000,
        0,
        './data/raw/myreviews{}.csv',
        'https://www.tripadvisor.com/Airline_Review-d8729017-Reviews-Alaska-Airlines-or{}.html',
        False)