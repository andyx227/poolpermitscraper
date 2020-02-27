import datetime
import platform
import sys

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoSuchWindowException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait

import scraper
from EC_permit_result import PermitResult
from EC_permit_result import ResultType
from PoolPermitReaderWriter import CSVReaderWriter


def get_list_of_links_to_permit(driver):
    """
    Return a non-empty list of links to permit with a
    "Permit Issued" status. Must contain at least two
    links. This function should only be called when the
    web page displays a list of multiple permits.
    Unexpected behavior may occur otherwise.

    Parameters
    ----------
    driver: WebDriver
        Instance of WebDriver provided by Selenium.

    Returns
    -------
    list
        List of links to each permit. Will contain at
        least two links.

    """

    try:
        permit_display_zone = driver.find_element_by_xpath("//div[@id='ctl00_cphPaneBand_pnlPaneBand'][@class='datazone']")
        permits = permit_display_zone.find_elements_by_xpath(".//tr[@class='possegrid'][@style='cursor: pointer;']")
        links_to_permit = []
    except NoSuchWindowException:
        raise
    except NoSuchElementException:
        raise
    except WebDriverException:
        raise

    for p in permits:
        try:
            status = p.find_element_by_xpath(".//span[contains(@id, 'PWebPermitStatus')]")
            if status.text != "Permit Issued":
                continue

            link = p.find_element_by_xpath(".//input[@value='View']").get_attribute("onclick")
            # Remove single quotes and "location.href=" substring from link
            clean_link = link.replace("'", "").replace("location.href=", "")
            links_to_permit.append(clean_link)
        except NoSuchWindowException:
            raise
        except NoSuchElementException:
            raise
        except WebDriverException:
            raise

    return links_to_permit


def get_permit_from_links(driver, links, csv_rw):
    """
    From a list of links, go to each link to
    extract a permit's information. Each permit's
    info will be saved into a csv file, which is
    handled by extract_permit_info().

    Parameters
    ----------
    driver: WebDriver
        Instance of WebDriver provided by Selenium.
    links: list
        List of links where each link will lead to a
        web page that displays a permit's info.
    csv_rw: CSVReaderWriter
        Instance of CSVReaderWriter.

    """

    for link in links:
        try:
            driver.get(link)  # Go to the link
        except WebDriverException:
            raise

        try:
            result = WebDriverWait(driver, 10).until(PermitResult())
            if not result:
                raise NoSuchElementException
            scraper.get_permit_info(driver.page_source, driver.current_url, csv_rw)
        except NoSuchWindowException:
            raise
        except TimeoutException:
            raise
        except WebDriverException:
            raise


def update_permit_completion_date(driver, csv_rw):
    """
    Go through each permit without a completed
    date and check the website to see if the
    permit has been updated with a completed date.
    Updates the corresponding permit in the
    csv_rw.permits list if it has been updated
    with a completed date.

    Parameters
    ----------
    driver: WebDriver
        Instance of WebDriver provided by Selenium.
    csv_rw: CSVReaderWriter
        Instance of CSVReaderWriter.

    Returns
    -------
    list
        List of permits that have been updated with
        a completed date.

    """

    uncompleted_permits = csv_rw.get_list_of_uncompleted_permits()
    updated_permits = []
    for idx, permit in uncompleted_permits:
        try:
            driver.get(permit["Permit URL"])
        except WebDriverException:
            raise WebDriverException

        try:
            result = WebDriverWait(driver, 10).until(PermitResult())
            if not result:
                raise NoSuchElementException
            completion_date = scraper.get_permit_completion_date(driver.page_source)
            if completion_date == "":
                continue
            else:
                csv_rw.permits[idx]["Completed Date"] = completion_date
                updated_permits.append(csv_rw.permits[idx])
        except NoSuchWindowException:
            raise
        except TimeoutException:
            raise
        except WebDriverException:
            raise

    return updated_permits


def write_updated_permits_to_csv(updated_permits, csv_rw):
    """
    Write permits with updated completion date to
    a csv file.

    Parameters
    ----------
    updated_permits: list
        A list containing the permits with
        updated completion date.
        
    csv_rw: CSVReaderWriter
        An instance of CSVReaderWriter

    """

    for permit in updated_permits:
        csv_rw.write_permit_to_csv(permit)


def get_permit(driver, csv_rw):
    """
    Get permits from the source given by @driver.
    
    Wrapper for get_permit_info() and
    get_permit_from_links().

    Parameters
    ----------
    driver: WebDriver
        An instance of WebDriver from Selenium
    csv_rw: CSVReaderWriter
        An instance of CSVReaderWriter

    """

    try:
        result = WebDriverWait(driver, 10).until(PermitResult())
        if result == ResultType.SINGLE:
            # print("Single result")
            scraper.get_permit_info(driver.page_source, driver.current_url, csv_rw)
        elif result == ResultType.MULTIPLE:
            # print("Multiple result")
            get_permit_from_links(driver, get_list_of_links_to_permit(driver), csv_rw)
        elif result == ResultType.NONE:
            # print("No result")
            pass
        else:
            raise NoSuchElementException
    except NoSuchWindowException:
        raise
    except TimeoutException:
        raise
    except NoSuchElementException:
        raise
    except WebDriverException:
        raise


def get_form_for_permit_search(driver, url):
    """
    Navigate to the permit search page and
    extract the entry fields for application
    date and application type, and also extract
    the "Search" button

    Parameters
    ----------
    driver: WebDriver
        An instance of WebDriver from Selenium
    url: str
        Url that leads to the permit search page.

    """

    try:
        driver.get(url)
    except WebDriverException:
        raise WebDriverException

    # Extract the following inputs from the website:
    # ----------------------------------------------
    #               Application Date
    #               Application Type
    #               Search button
    # ----------------------------------------------
    try:
        application_date = driver.find_element_by_id("CreatedDate_1209113_S0")
        application_type = Select(driver.find_element_by_name("JobApplicationTypeSearch_1209113_S0"))
        search_button = driver.find_element_by_xpath("//input[@value='Search']")
    except NoSuchWindowException:
        raise NoSuchWindowException
    except NoSuchElementException:
        raise NoSuchElementException
    except WebDriverException:
        raise WebDriverException

    return application_date, application_type, search_button


def run_bot(start_datetime, end_datetime, delta):
    """
    The entry point for extracting permit info.

    Extract permit info from @start_datetime
    to @end_datetime. If an error occurs
    during extraction, no permits will
    be saved to a csv file and the function
    will return immediately.

    Parameters
    ----------
    start_datetime: datetime
        The date from which to start
        extracting permit info.
    end_datetime: datetime
        The last date from which to
        extract permit info.
    delta: timedelta
        The date difference between
        @start_datetime and @end_datetime.

    Returns
    -------
    bool
        False if an error occurred when
        extracting permit info, True
        otherwise.

        Note: The function will
        immediately return if an error
        arises.

    """

    # sys._MEIPASS is given by PyInstaller. If this attribut doesn't exist,
    # then we must we running the script itself, not the deployed application.
    try:
        path_to_driver = sys._MEIPASS + "/chromedriver"
    except AttributeError:
        path_to_driver = "./chromedriver"

    driver = webdriver.Chrome(executable_path=path_to_driver)

    start_date = start_datetime.strftime("%b %d, %Y")
    end_date = end_datetime.strftime("%b %d, %Y")

    filename = start_date + "_to_" + end_date + "_permits"
    csv_rw = CSVReaderWriter(filename, create_new_file=True)   # Prepare object to interact with csv file

    date = start_datetime
    # --------------------------------------------
    # DEBUG - Use Dec 20, 2019 for single result
    # DEBUG - Use Dec 17, 2019 for multiple result
    # DEBUG - Use Dec 25, 2019 for no result
    # --------------------------------------------
    for _ in range(delta.days + 1):
        try:
            application_date, application_type, search_button = get_form_for_permit_search(driver, "https://developdallas.dallascityhall.com/Default.aspx?PossePresentation=ByAppDate")
        except NoSuchWindowException:
            print("WINDOW CLOSED ERROR: The browser window has been closed.")
            csv_rw.close_csv()
            return False
        except NoSuchElementException:
            print("NO ELEMENT FOUND ERROR: Could not find necessary element from web page. "
                  "Layout of site might have changed, or no internet connection.")
            close_driver(driver)
            csv_rw.close_csv()
            return False
        except WebDriverException:
            print("INTERNAL ERROR: WebDriver threw an exception. Possibly because user quit the browser window before page was loaded.")
            close_driver(driver)
            csv_rw.close_csv()
            return False

        application_date.clear()
        application_date.send_keys(date.strftime("%b %d, %Y"))  # Date is in the format: mmm dd, yyyy
        application_type.select_by_value("Swimming Pool Permit")
        search_button.click()

        try:
            get_permit(driver, csv_rw)
        except NoSuchWindowException:
            print("WINDOW CLOSED ERROR: The browser window has been closed.")
            csv_rw.close_csv()
            return False
        except NoSuchElementException:
            print("NO ELEMENT FOUND ERROR: Could not find necessary element from web page. "
                  "Layout of site might have changed, or no internet connection.")
            close_driver(driver)
            csv_rw.close_csv()
            return False
        except TimeoutException:
            print("TIMEOUT ERROR: could not find any result in the 10 second time limit. Check internet connection.")
            close_driver(driver)
            csv_rw.close_csv()
            return False
        except WebDriverException:
            print("INTERNAL ERROR: WebDriver threw an exception. Possibly because user quit the browser window before page was loaded.")
            close_driver(driver)
            csv_rw.close_csv()
            return False

        date = date + datetime.timedelta(days=1)

    close_driver(driver)
    csv_rw.save_csv()
    csv_rw.close_csv()
    return True


def update_file(filename):
    """
    The entry point for updating file.

    Update the permits contained the the file. Wrapper
    for update_permit_completion_date(). If an error occurs
    during update, no permits will be saved to a csv
    file and the function will return immediately.
    
    Otherwise, a new csv file will be created to store the updated
    permits. The master file will also reflect the updates. 

    Parameters
    ----------
    filename: str
        The absolute path to the csv file containing
        the permits.

    Returns
    -------
    bool
        False if an error occurred when
        updating permit, True otherwise.

        Note: The function will
        immediately return if an error
        arises.

    """

    # sys._MEIPASS is given by PyInstaller. If this attribut doesn't exist,
    # then we must we running the script itself, not the deployed application.
    try:
        path_to_driver = sys._MEIPASS + "/chromedriver"
    except AttributeError:
        path_to_driver = "./chromedriver"

    driver = webdriver.Chrome(executable_path=path_to_driver)
    try:
        driver.get("https://developdallas.dallascityhall.com/Default.aspx?PossePresentation=ByAppDate")
    except WebDriverException:
        print("INTERNAL ERROR: WebDriver threw an exception. Possibly because user quit the browser window before page was loaded.")
        close_driver(driver)
        return False

    csv_rw_master = CSVReaderWriter(filename, create_new_file=False)
    
    # Get the csv file's name
    names = []
    if platform.system() == "Windows":
        names = filename.split("\\")
    elif platform.system() == "Darwin":  # MacOS
        names = filename.split("/")
    csv_filename = names[len(names) - 1]

    try:
        updated_permits = update_permit_completion_date(driver, csv_rw_master)
    except NoSuchWindowException:
        print("WINDOW CLOSED ERROR: Browser window has already been closed.")
        csv_rw_master.close_csv()
        return False
    except NoSuchElementException:
        print("NO ELEMENT FOUND ERROR: Could not find necessary element from web page. Layout of site might have changed.")
        csv_rw_master.close_csv()
        close_driver(driver)
        return False
    except TimeoutException:
        print("TIMEOUT ERROR: could not find any result in the 10 second time limit. Check internet connection.")
        csv_rw_master.close_csv()
        close_driver(driver)
        return False
    except WebDriverException:
        print("INTERNAL ERROR: WebDriver threw an exception. Possibly because user quit the browser window before page was loaded.")
        csv_rw_master.close_csv()
        close_driver(driver)
        return False

    # Prepare object to write updated permits to a new csv file
    csv_rw_updated = CSVReaderWriter("updated_" + csv_filename)

    if len(updated_permits) > 0:
        write_updated_permits_to_csv(updated_permits, csv_rw_updated)

    # Clean up
    close_driver(driver)
    csv_rw_master.save_csv()
    csv_rw_master.close_csv()
    csv_rw_updated.save_csv()
    csv_rw_updated.close_csv()
    return True


def close_driver(driver):
    try:
        driver.close()
    except NoSuchWindowException:
        pass