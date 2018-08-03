# facebook-scraping-selenium
This is a project for scraping facebook posts using selenium. 

This script is used to scrape data of the comments related to a search result.
Go to all the public post for that serach https://www.facebook.com/search/str/SEACH_TERM_HERE/stories-keyword/stories-public
Then you will see a lot of posts. For every post it captures:

1) Content of whole post(click See more ).
2) number of shares.
3) Number of likes.
4) Number of comments.
5) If there is any photo, its link is saved.
6) Option to select number of pages to scroll.
7) Store the results in JSON format in a file.

Script should be written in Python 2.7
The script should use Selenium 3.11.0 or higher.
Should use Google Chrome

Implementation details:
Don’t use class names as they will change, especially those which start with underscore.
It might need a few tweaks, as the facebook changes from time to time.

Have username and password as hardcoded variables in the script.
Ask for a search term (can be multiple words and should support Unicode input)
Ask for path to a file where to store the results.



