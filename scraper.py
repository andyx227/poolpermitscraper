import re

from bs4 import BeautifulSoup


def get_permit_info(source, permit_url, csv):
    """
    Extracts necessary information from the HTML source and
    saves it into a csv file. The source must only contain
    info for a single permit. The permit must not have an
    "Application Cancelled" status or an empty address.

    Extracts and saves the following information from @source:
    - Application Date
    - Completed Date (if exists)
    - Address
    - Applicant
    - Contractor
    - Job Value Cost

    Parameters
    ----------
    source : str
        The page source derived from Selenium.
    permit_url: str
        The URL displaying the permit info.
    csv: CSVReaderWriter
        Instance of CSVReaderWriter object.

    """

    soup = BeautifulSoup(source, "html.parser")

    application_status = soup.find("span", id=re.compile("PWebPermitStatus"))
    street_address = soup.find("span", id=re.compile("AddressDisplay"))
    if street_address is None or application_status is None:
        return
    if street_address.text == "" or application_status.text == "Application Cancelled":
        return

    application_date = soup.find("span", id=re.compile("CreatedDate"))
    completed_date = soup.find("span", id=re.compile("CompletedDate"))
    applicant = soup.find("span", id=re.compile("WebApplicantDisplay"))
    contractor = soup.find("span", id=re.compile("WebContractorDisplay"))
    job_value = soup.find("span", id=re.compile("JobValue"))

    # Replace <br> tags with newline
    for br in street_address("br"):
        br.replace_with("\n")
    for br in contractor("br"):
        br.replace_with("\n")

    permit_data = {
        "Application Date": application_date.text,
        "Completed Date": completed_date.text,
        "Address": street_address.text,
        "Applicant": applicant.text,
        "Contractor": contractor.text,
        "Job Value Cost": job_value.text,
        "Permit URL": permit_url
    }

    csv.write_permit_to_csv(permit_data)

    # ---------------------------------------------------
    #                       DEBUG
    # ---------------------------------------------------
    # print("Street address: " + street_address.text)
    # print("Application date: " + application_date.text)
    # print("Completed date: " + completed_date.text)
    # print("Applicant: " + applicant.text)
    # print("Contractor: " + contractor.text)
    # print("Job value: " + job_value.text)


def get_permit_completion_date(source):
    """
    Extract permit's completion date from source.

    Parameters
    ----------
    source: str
        The HTML source containing a permit's info.

    Returns
    -------
    str
        The string containing the permit's completion
        date. No completion date is signified by an
        empty string.

    """

    soup = BeautifulSoup(source, "html.parser")
    return soup.find("span", id=re.compile("CompletedDate")).text
