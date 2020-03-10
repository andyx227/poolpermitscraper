from enum import Enum

from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoSuchWindowException


class ZipCodeResult:
    def __init__(self):
        self.xpathToErrorElement = "//div[@class='server-error address-tAddress help-block']"
        self.xpathToZipCodeResultElement = "//div[@class='zipcode-result-address']"

    def __call__(self, driver):
        try:
            driver.find_element_by_xpath(self.xpathToErrorElement)
            return ZipCodeResultType.ERROR
        except NoSuchElementException:
            pass
        except NoSuchWindowException:
            return False

        try:
            driver.find_element_by_xpath(self.xpathToZipCodeResultElement)
            return ZipCodeResultType.FOUND
        except NoSuchElementException:
            return False
        except NoSuchWindowException:
            return False


class ZipCodeResultType(Enum):
    ERROR = 1
    FOUND = 2
