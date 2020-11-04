import csv
import logging
import platform
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

logging.basicConfig(level=logging.INFO)

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
    service = Service()
    service.start()
    driver = webdriver.Remote(service.service_url)

    return driver


def startWebDriver():
    """ Starts the web driver for scraping. For best performance, make sure you start the chromedriver
    before running this python script.
    """
    options = Options()
    options.headless = True

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
    time.sleep(1)

    ## companyName = driver.find_element_by_xpath('//h1[@class="_3ggwzaPV"]')
    
    reviews = []
    reviewDivs = driver.find_elements_by_xpath('//div[@data-reviewid]')
    for reviewDiv in reviewDivs:
        reviewId = reviewDiv.get_attribute('data-reviewid') 
        rating   = getReviewRating(reviewDiv)
        review   = Review(reviewId, rating)

        # Get Itinerary
        review.setItinerary(getReviewItinerary(reviewDiv))
        
        review = getReviewDetail(userReviewDriver, reviewDiv, review)
        
        # Add the review to the list
        reviews.append(review)

    return reviews


def getReviewRating(reviewDiv):
    """ The rating for the review is stored as a class on an inner span with two classes applied
    The first class identifies it as a "bubble rating", while the second defines the level from 1 to 5

    Example: class="ui_bubble_rating bubble_10"
    """
    ratingString = (((reviewDiv.find_element_by_class_name('ui_bubble_rating')).get_attribute('class')).split())[1]
    rating = (int(ratingString[-2:]))
    rating = rating/10

    return rating


def getReviewItinerary(reviewDiv):
    """ In this case, we're considering an Itinerary to be a reviewer's origin, destination, region of travel, and class of cabin for 
    travel. We don't have any specifics such as the Date of Travel (other than the "month", or date of review)
    """
    originDestinationString = (reviewDiv.find_elements_by_class_name('_3tp-5a1G')[0]).text
    originDestinationList = originDestinationString.split(' - ')

    region =  (reviewDiv.find_elements_by_class_name('_3tp-5a1G')[1]).text
    cabin =  (reviewDiv.find_elements_by_class_name('_3tp-5a1G')[2]).text

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
    time.sleep(1)

    userReviewDiv = userReviewDriver.find_element_by_xpath('//div[@id="review_' + review.Id + '"]') 

    # Get the review
    review.Date = userReviewDiv.find_element_by_xpath('//span[@class="ratingDate relativeDate"]').get_attribute('title')
    review.TravelDate = userReviewDiv.find_element_by_xpath('//div[@data-prwidget-name="reviews_stay_date_hsx"]').text[16:] # Trime "Date of Travel: "
    review.Title = userReviewDriver.find_element_by_xpath('//div/a[@id="rn' + review.Id + '"]/span').text
    review.Text = userReviewDiv.find_element_by_xpath('//div[@class="entry"]/p').text

    # Gather information about the reviewer 
    id = userReviewDiv.find_element_by_xpath('//div[@class="member_info"]/div').get_attribute('id')  # TODO: Parse the user ID string to just the substring 
    name = userReviewDiv.find_element_by_xpath('//div[@class="username mo"]/span').text 
    location = userReviewDiv.find_element_by_xpath('//div[@class="location"]/span').text 

    # Gather Category Ratings
    # This returns a collection of divs that contain both the bubble rating and rating description
    # I'm iterating through the collection and using the modulus function to alternate between parsing
    # I'm sure there's a more elegant way to do this
    ratingElements = userReviewDiv.find_elements_by_xpath('//div[@id="review_' + review.Id + '"]//li[@class="recommend-answer"]/div')
    starRatings = []
    ratingCategories = []
    x = 0
    for ratingElement in ratingElements:
        if(x % 2) == 0:
            ratingString = (ratingElement.get_attribute('class').split())[1]
            starRating = (int(ratingString[-2:]))
            starRating = starRating/10
            starRatings.append(starRating)
        else:
            category = ratingElement.text
            ratingCategories.append(category)

        x = x + 1

    x = 0
    for categoryText in ratingCategories:
        review.CategoryRatings[categoryText] = starRatings[x]
        x = x + 1

    review.setReviewer(Reviewer(id, name, location))

    return review    


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


def batchWriteToCsv(reviews, fCsv):
    """ Write out the data (with headers) to a csv filestream handle in one batch. """
    
    reviewFileWriter = csv.writer(fCsv, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
    
    fCsv = _addHeadersToCsv(fCsv)

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
        pathCsv='./data/raw/myreviews.csv', 
        baseUrl='https://www.tripadvisor.com/Airline_Review-d8729017-Reviews-Alaska-Airlines.html', 
        preview=False):
    """
    Fetch reviews by page and stream to CSV file

    Parameters:
        - max: stop after this number of reviews is reached, or set to None to continue exhaustively
        - pathCsv: file path to save the desired csv file 
        - preview: print the results to terminal

    """
    urlTemplate = baseUrl.replace('.html', '-or{}.html')

    # Start the primary webdriver that loops through the pages of reviews
    driver = startWebDriver()
    
    # Startup a second webdriver to bring up more detail pages on the user review while
    # still maintaining the original driver to page through all reviews
    userReviewDriver = startWebDriver()

    # Open a new CSV file and add the headers.  Note: it will clobber an existing file.
    fReviewCsv = open(pathCsv, "w", encoding="utf-8")
    fReviewCsv = _addHeadersToCsv(fReviewCsv)

    # Get the Reviews for given airline at the base url
    driver.get(baseUrl)
    time.sleep(2) 

    # Get the total review count for informational purposes
    airlineReviewCountClassId = '_2tNtmCyi'
    reviewCount = getReviewCount(driver, airlineReviewCountClassId)
    logging.info(f"Fetching {max} of {reviewCount} reviews...")

    # Loop through all the results or until you hit the max and stream results
    offset = 0
    while(True):
        reviewUrl = urlTemplate.format(offset)
        reviewSubset = getReviewsForUrl(driver, userReviewDriver, reviewUrl)

        # If not more reviews, complete loop
        if not reviewSubset: break

        # Preview reviews in terminal
        if preview:
            for review in reviewSubset:
                logging.info("|".join([str(x) for x in [review.Id,
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
        logging.info(f"Total retrieved: {offset}")

        if max and offset >= max: 
            logging.info("Desired max reviews reached, stopping now.")
            break

    # Cleanup
    fReviewCsv.close()
    

if __name__ == "__main__":
    streamReviewsToCsv(max=10, preview=False)