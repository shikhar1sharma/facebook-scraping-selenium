# -*- coding: utf-8 -*-
import atexit
import os
import pickle
import json
import time
import urllib

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
    )

# Enter your own facebook username and password
USERNAME = 'fb_username'
PASSWORD = 'fb_password'

# What to search for, in Unicode.
SEARCH = 'сирия вагнер'

# Path where to store the JSON result file.
DESTINATION_PATH = 'result.json'

# How many times to scroll down the page.
SCROLL_COUNT = 30

# How much seconds to do dynamic waits.
WAIT_TIME = 10


# Chrome driver should be un
executable_path=os.path.join('chromedriver')

options = webdriver.ChromeOptions()
options.add_argument('--ignore-certificate-errors')

# 1-Allow, 2-Block, 0-default
preferences = {
    "profile.default_content_setting_values.notifications" : 2,
    "profile.default_content_setting_values.location": 2,
    # We don't need images, only the URLs.
    "profile.managed_default_content_settings.images": 2,
    }
options.add_experimental_option("prefs", preferences)


browser = webdriver.Chrome(
    executable_path=executable_path,
    chrome_options=options,
    )
browser.wait = WebDriverWait(browser, WAIT_TIME)


def close_browser(driver):
    """
    Close the browser.
    """
    try:
        driver.close()
    except WebDriverException:
        # Might be already closed.
        pass

# Make sure browser is always closed, even on errors.
atexit.register(close_browser, browser)


def fb_login(driver):
    """
    Login to facebook using username and password.
    """
    driver.get('https://www.facebook.com/')
    usr = driver.find_element_by_name("email")
    usr.send_keys(USERNAME)
    password = driver.find_element_by_name("pass")
    password.send_keys(PASSWORD)
    password.send_keys(Keys.RETURN)
    raw_input(
        "Confirm that you authenticated with the right user.\n"
        "Check no browser popups are there."
        )


def scroll_progressive_to_bottom(driver):
    """
    Slowly scroll to the bottom of the page, waiting for new content to be loaded.
    """
    time.sleep(5)

    bottom = 0
    for attempt_count in xrange(SCROLL_COUNT):
        # Scroll down so that we load another chunk.
        driver.execute_script("window.scrollBy(0,10000);")
        new_bottom = driver.execute_script(
            "return document.documentElement.scrollTop || document.body.scrollTop")

        if bottom == new_bottom:
            # It looks like we no longer need to scroll.
            try:
                driver.find_element_by_css_selector(
                    '#pagelet_scrolling_pager .uiMorePagerLoader')
            except NoSuchElementException:
                # We no longer have to indicator that more content needs to be
                # loaded.
                # We are done.
                return

            # It looks like we are at the bottom but we need to wait
            # more.
            time.sleep(7)

        bottom = new_bottom

        # Do one more scroll in advance before the wait.
        driver.execute_script("window.scrollBy(0,10000);")
        time.sleep(6)

    # Check to see if we have the end of results marker and print a warning,
    # if we don't have the marker
    try:
        driver.find_element_by_css_selector('#browse_end_of_results_footer')
    except NoSuchElementException:
        print "We hit the end, without an end marker"


def move_to_element(driver, element):
    """
    Get element in the current viewport and have to mouse over it.
    """
    actions = ActionChains(driver)
    actions.move_to_element(element)
    actions.perform()


def go_to_page_list(search):
    """
    Go to the page listing all public posts matching `search` provides as
    Unicode text.
    """
    search_encoded = urllib.quote(search)
    browser.get(
        "https://www.facebook.com/search/str/%s/stories-keyword/stories-public" % (search_encoded,))


def fb_dump_posts(driver):
    """
    Search the posts and return the post details as a list of dicts with keys.
    * Name
    * Date
    * Post
      * Post
      * Link
    * Comments
    * Shares
    * Like
    """
    result = []

    # Get the dynamic class name of the posts.
    first_post = driver.find_element_by_css_selector('#BrowseResultsContainer > div:first-child')
    post_class = first_post.get_attribute('class')

    posts = driver.find_elements_by_class_name(post_class)
    for post in posts:
        if not post.text:
            print "It looks like there are still posts... but can't scroll"
            continue

        data = {
            'Post': {
                'Post': 'no-content',
                'Link': [],
                },
            'Comments': 0,
            'Shares': 0,
            'Like': 0,
            }

        # Scroll to post, click the content and wait to load.
        move_to_element(driver, post)
        post.click()
        time.sleep(2)

        content = post.find_element_by_css_selector('div.userContent')

        # Get name and date.
        # Name is H5 and date is an abbr close to h5.
        data['Name'] = post.find_element_by_css_selector("h5").text
        timestamp = post.find_element_by_css_selector("h5 + div abbr")
        data['Date'] = timestamp.get_attribute('data-utime')

        # Get content and image link
        data['Post']['Post'] = content.text
        # We use many to not handle not found exception.
        images = post.find_elements_by_css_selector('div.userContent + div a img.img')
        for image in images:
            data['Post']['Link'].append(image.get_attribute('src'))
        print "Got %s" % (len(images))

        # Get post reactions
        # First is a div containing the comments + shared
        # Next lasts are the likes
        # Shared are after comments.
        reactions = post.find_elements_by_css_selector("form div.clearfix > div")
        # But we might have no likes and comments, and in that case we only
        # have a single row for actions.
        if len(reactions) > 1 and reactions[0].text:
            comments_shares = reactions[0].find_elements_by_css_selector("a")

            for link in comments_shares:
                kind = link.get_attribute('data-comment-prelude-ref')
                # Both Commants and Shares are A elements, but the comments have
                # an extra attribute.
                if kind == 'action_link_bling':
                    data['Comments'] = link.text
                else:
                    data['Shares'] = link.text

            if reactions[1].text:
                # We have likes.
                data['Like'] = reactions[1].find_element_by_css_selector("a[rel=ignore] span").text

        result.append(data)

    return result


#
# Here we put all together.
#

fb_login(browser)
go_to_page_list(SEARCH)
scroll_progressive_to_bottom(browser)
result = fb_dump_posts(browser)
print "Writing %s" % len(result)
with open(DESTINATION_PATH, 'wb') as stream:
    json.dump(result, stream)
