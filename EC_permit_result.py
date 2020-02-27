from enum import Enum

from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoSuchWindowException


# There are three possible results when searching for permits:
# ------------------------------------------------------------
# 1) Single Result    - a span element will appear with the following innerHTML: Master Permit
# 2) Multiple Result  - a "Search Again" button will appear
# 3) No result        - a center element with class "posseerror" will appear with the following
#                       innerHTML: No applications of this type were received on the given date.


class PermitResult:
    def __init__(self):
        self.xpathToSingleResultSpanElement = "//div[@id='ctl00_cphTitleBand_pnlTitleBand']/div[1]/span[1]"
        self.xpathToMultipleResultButtonElement = "//input[@value='Search Again']"
        self.xpathToNoResultCenterElement = "//center[@class='posseerror']"

    def __call__(self, driver):
        try:
            single_result_span = driver.find_element_by_xpath(self.xpathToSingleResultSpanElement)
            inner_html = single_result_span.get_attribute("innerHTML")
            if "Master Permit" in inner_html:
                return ResultType.SINGLE
        except NoSuchElementException:
            pass
        except NoSuchWindowException:
            return False
        except AttributeError:
            return False

        try:
            driver.find_element_by_xpath(self.xpathToMultipleResultButtonElement)
            return ResultType.MULTIPLE
        except NoSuchElementException:
            pass
        except NoSuchWindowException:
            return False

        try:
            driver.find_element_by_xpath(self.xpathToNoResultCenterElement)
            return ResultType.NONE
        except NoSuchElementException:
            pass
        except NoSuchWindowException:
            return False

        return False


class ResultType(Enum):
    SINGLE = 1
    MULTIPLE = 2
    NONE = 3
