import csv
import os


class CSVReaderWriter:
    def __init__(self, csv_filename, create_new_file=True):
        """
        Initialize a CSVReaderWriter object.

        Parameters
        ----------
        csv_filename: str
            Name of the csv file.
        create_new_file: bool
            If true, create a new file with the
            given filename. If file already exists,
            original content will be overwritten. If
            false, open and read an existing csv file
            with the given filename.

            Note: New csv files will be saved onto the
            user's desktop.

        """

        self.permits = []
        self.filename = csv_filename if ".csv" in csv_filename else csv_filename + ".csv"

        if create_new_file:
            self.filename = os.path.expanduser("~/Desktop/") + self.filename  # Save this csv file onto user's desktop
            self.file = open(self.filename, mode="w")
        else:
            self.file = open(self.filename, mode="a+")
            self.file.seek(0)  # Go to the start of the file
            self.reader = csv.DictReader(self.file)
            for row in self.reader:
                self.permits.append(row)  # Make copy of all current data in file

        self.writer = csv.DictWriter(self.file, fieldnames=["Application Date", "Completed Date", "Address",
                                                            "Applicant", "Contractor", "Job Value Cost",
                                                            "Permit URL"])

    def write_permit_to_csv(self, permit_data):
        """
        Appends the data from permit_data to self.data.
        This function does not actually write to the
        csv file to save compute time.

        Parameters
        ----------
        permit_data: dict
            A dictionary that contains the
            following information for a permit:

            - Application Date
            - Completed Date (if exists, leave blank if not)
            - Address
            - Applicant
            - Contractor
            - Job Value Cost
            - Permit URL

        """

        self.permits.append(permit_data)

    def update_permit_in_csv(self, permit_idx, new_permit_data):
        """
        Update a particular permit in the self.permits list.

        Parameters
        ----------
        permit_idx: int
            For locating the permit to be updated
            in the self.permits list.
        new_permit_data: dict
            A dictionary containing the updated
            data for the permit at index @permit_idx

        """

        self.permits[permit_idx] = new_permit_data

    def get_list_of_uncompleted_permits(self):
        """
        Go through all the permits in self.permits
        and return all permits without a completed date.

        Returns
        -------
        list
            A list of 2-tuples containing the index
            of the uncompleted permit in self.permits
            and the uncompleted permit itself.

        """

        return [(idx, permit) for idx, permit in enumerate(self.permits) if permit["Completed Date"] == ""]

    def save_csv(self):
        """
        Delete all old contents in the csv file and then
        write all data in self.permits into the file.

        """
        self.file.truncate(0)  # Delete all old content in file
        self.writer.writeheader()
        for permit in self.permits:
            self.writer.writerow(permit)

    def close_csv(self):
        """
        Close the csv file. Should be called before
        program quits to release memory and only
        when certain that the csv file won't be
        opened again.

        """

        self.file.close()
