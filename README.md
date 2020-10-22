# FlyWhy
Why do people fly an airline, and how do they feel about it over time.

A recent web article on [The biggest pain points in air travel and how to fix them - TNMT](https://tnmt.com/the-biggest-pain-points-in-air-travel/), got me thinking on how we might analyze just [Alaska Airlines TripAdvisor Reviews](https://www.tripadvisor.com/ShowUserReviews-g1-d8729017-r773099398-Alaska_Airlines-World.html).
		
To that end, I started this side project, "FlyWhy: Why do people fly an airline, and how do they feel about it over time."

The goals are threefold:

  1. Analyze the TripAdvisor Reviews to Derive Insights that could be leveraged for action.
  1. Learn Python
  1. Learn Text Analytics and Natural Language Processing (NLP) algorithms

## Background on Prior Attempts			 
Original attempt was to use Python on Linux (so this could eventually be run on Databricks in Azure Cloud), following the the technique outlined in this link, [NLP-with-Python/Web scraping Hilton Hawaiian Village TripAdvisor Reviews.py at master · susanli2016/NLP-with-Python (github.com)](https://github.com/susanli2016/NLP-with-Python/blob/master/Web%20scraping%20Hilton%20Hawaiian%20Village%20TripAdvisor%20Reviews.py). This script utilized the BeautifulSoup library for screen scraping. Unfortunately, the TripAdvisor site executed a lot of JavaScript which BS does not handle.

After a few more rabbit holes and trying to use headless chrome on Windows Subsystem for Linux (WSL), I switched to Puppeteer/C#. This would not allow me to accomplish my 2nd learning objective above.

To get back on track, I asked our internal team members for additional guidance.

Feedback from internal collaborators suggested:
  1. I've also had good luck with the PhantomJS driver for Selenium for lightweight headless deploys... still pretty heavy compared to beautifulsoup but can be helpful depending on the need. Here's a quick article I pulled up on PhantomJS: https://realpython.com/headless-selenium-testing-with-python-and-phantomjs/

  1. Selenium

I was able to get over the hurdle, and get started scraping reviews. This project on github is the result.

If you're interested in learning, or would like to give some constructive feedback, please join in on the fun.