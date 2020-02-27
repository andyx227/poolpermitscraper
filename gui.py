import datetime
import os
import threading
from enum import Enum
from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk

import web_driver


class Status(Enum):
    NORMAL = 0
    BOT_IS_RUNNING = 1
    BOT_STOPPED_RUNNING = 2
    BOT_IS_UPDATING_FILE = 3
    BOT_STOPPED_UPDATING_FILE = 4
    BOT_ERROR = 5


class Title:
    def __init__(self, master):
        self.frame = Frame(master)
        self.frame.pack()

        self.title = Label(self.frame, text="Pool Permit Scraper Bot")
        self.title.pack()


class Form:
    def __init__(self, master):
        self.filename = "No file chosen."

        self.frame = Frame(master)
        self.frame.pack()

        self.label_start = Label(self.frame, text="Start Date")
        self.label_end = Label(self.frame, text="End Date")
        self.label_choose_file = Label(self.frame, text="Choose File to Update: ")
        self.label_filename = Label(self.frame, text="No file chosen.")

        self.entry_start = Entry(self.frame)
        self.entry_end = Entry(self.frame)

        self.button_choose_file = ttk.Button(self.frame, text="Choose file", command=self.get_filename)

        # Grid setup
        self.label_start.grid(row=0, sticky=E)
        self.label_end.grid(row=1, sticky=E)
        self.label_choose_file.grid(row=2, sticky=E)
        self.label_filename.grid(row=2, column=1)

        self.entry_start.grid(row=0, column=1, columnspan=2, sticky=EW)
        self.entry_start.insert(0, "mm/dd/yyyy")
        self.entry_start.bind("<Button-1>", lambda event: self.clear_placeholder(event, self.entry_start))
        self.entry_end.grid(row=1, column=1, columnspan=2, sticky=EW)
        self.entry_end.insert(0, "mm/dd/yyyy")
        self.entry_end.bind("<Button-1>", lambda event: self.clear_placeholder(event, self.entry_end))

        self.button_choose_file.grid(row=2, column=2)

    def get_filename(self):
        self.filename = filedialog.askopenfilename(initialdir=os.path.expanduser("~/Desktop/"),
                                                   title="Choose file",
                                                   filetypes=(("csv files", "*.csv"),))
        if self.filename == "":
            self.filename = "No file chosen."
        self.label_filename.config(text=self.filename)

    def clear_placeholder(self, event, entry):
        if entry.get() == "mm/dd/yyyy":
            entry.delete(0, END)


class RunBotButtons:
    def __init__(self, master, form):
        self.status_bar = None
        self.status = Status.NORMAL
        self.form = form

        self.frame = Frame(master)
        self.frame.pack()

        self.button_run = ttk.Button(self.frame, text="Run Bot", command=self.run_bot_thread)
        self.button_update = ttk.Button(self.frame, text="Update File", command=self.update_file_thread)

        self.button_run.grid(row=0)
        self.button_update.grid(row=0, column=2)

    def set_status_bar_object(self, status_bar):
        """
        Set an instance of StatusBar to self.status_bar.
        This is needed to call the change_status_message()
        function in the StatusBar object.

        Parameters
        ----------
        status_bar: StatusBar
            An instance of StatusBar. Displays
            various messages to the user based
            on the current status of the bot.

        """

        self.status_bar = status_bar

    def run_bot_thread(self):
        """
        A wrapper for self.run_bot().

        The self.run_bot() function will be run in a
        thread so that the GUI doesn't get held up
        when the function is executing.

        """

        self.button_run.config(state=DISABLED)

        formatted_date_range = self.check_date_format()

        if not formatted_date_range:
            self.button_run.config(state=NORMAL)
            return
        else:
            start_datetime, end_datetime, delta = formatted_date_range
            run_bot_thread = threading.Thread(target=self.run_bot, args=(start_datetime, end_datetime, delta,))
            run_bot_thread.start()

    def run_bot(self, start_datetime, end_datetime, delta):
        """
        Executes web_driver.run_bot(). When the
        function finishes executing, the "Run Bot"
        button will be re-enabled.

        """

        if self.status_bar is not None:
            self.status_bar.change_status_message(Status.BOT_IS_RUNNING)

        if not web_driver.run_bot(start_datetime, end_datetime, delta):
            self.status_bar.change_status_message(Status.BOT_ERROR)
        else:
            if self.status_bar is not None:
                self.status_bar.change_status_message(Status.BOT_STOPPED_RUNNING)
        self.button_run.config(state=NORMAL)

    def update_file_thread(self):
        """
        A wrapper for self.update_file().

        The self.update_file() function will be run in a
        thread so that the GUI doesn't get held up
        when the function is executing.

        """

        self.button_update.config(state=DISABLED)
        if self.form.filename == "No file chosen.":
            messagebox.showwarning(title="No File Chosen", message="Please choose a file to update and try again.")
            self.button_update.config(state=NORMAL)
            return

        update_file_thread = threading.Thread(target=self.update_file)
        update_file_thread.start()

    def update_file(self):
        """
        Executes web_driver.update_file(). When the
        function finishes executing. the "Update File"
        button will be re-enabled.

        """

        if self.status_bar is not None:
            self.status_bar.change_status_message(Status.BOT_IS_UPDATING_FILE)

        if not web_driver.update_file(self.form.label_filename.cget("text")):
            self.status_bar.change_status_message(Status.BOT_ERROR)
        else:
            if self.status_bar is not None:
                self.status_bar.change_status_message(Status.BOT_STOPPED_UPDATING_FILE)
        self.button_update.config(state=NORMAL)

    def check_date_format(self):
        """
        Date format is mm/dd/yyyy

        Returns
        -------
        tuple
            A 3-tuple filled with the start
            datetime, end datetime, and the
            date difference (delta) respectively.
            The datetime is referring to the Python
            datetime object. Return None if the
            input date is not in a valid format.

        """

        start_date = self.form.entry_start.get().split("/")
        end_date = self.form.entry_end.get().split("/")

        if len(start_date) != 3 or len(end_date) != 3:
            messagebox.showwarning(title="Invalid Date Format", message="Please enter your date in the format: mm/dd/yyyy")
            return None

        if len(start_date[0]) != 2 or len(start_date[1]) != 2 or len(start_date[2]) != 4:
            messagebox.showwarning(title="Invalid Date Format", message="Please enter your date in the format: mm/dd/yyyy")
            return None

        if len(end_date[0]) != 2 or len(end_date[1]) != 2 or len(end_date[2]) != 4:
            messagebox.showwarning(title="Invalid Date Format", message="Please enter your date in the format: mm/dd/yyyy")
            return None

        try:
            # Convert date from string to integer
            start_date = [int(date) for date in start_date]
            end_date = [int(date) for date in end_date]

            start = datetime.datetime(start_date[2], start_date[0], start_date[1])
            end = datetime.datetime(end_date[2], end_date[0], end_date[1])
            delta = end - start
            if delta.days < 0:
                raise DateRangeInvalid
        except ValueError:
            messagebox.showwarning(title="Invalid Date", message="Please enter a valid date.")
            return None
        except TypeError:
            messagebox.showwarning(title="Invalid Date Format", message="Date must only contain numbers.")
            return None
        except DateRangeInvalid:
            messagebox.showwarning(title="Invalid Date Range", message="End date is earlier than start date. Please check your dates and try again.")
            return None

        # Format start and end date to: mmm dd, yyyy
        start_ts = datetime.datetime.strptime(self.form.entry_start.get(), "%m/%d/%Y").timestamp()
        end_ts = datetime.datetime.strptime(self.form.entry_end.get(), "%m/%d/%Y").timestamp()
        start_datetime = datetime.datetime.fromtimestamp(start_ts)
        end_datetime = datetime.datetime.fromtimestamp(end_ts)
        return start_datetime, end_datetime, delta


class StatusBar:
    def __init__(self, master):
        self.frame = Frame(master)
        self.frame.pack()

        self.status = Label(self.frame,
                            text="Enter a date range above and click \"Run Bot\" to start.\n"
                                 "To update an existing file, choose the file and click \"Update File\".",
                            bd=1,
                            relief=SUNKEN,
                            anchor=W)

        self.status.pack()

    def change_status_message(self, status):
        if status == Status.NORMAL:
            self.status.config(text="Enter a date range above and click \"Run Bot\" to start.\n"\
                                    "To update an existing file, choose the file and click \"Update File\".")
        elif status == Status.BOT_IS_RUNNING:
            self.status.config(text="Bot is gathering permits from the date range you specified.\n"\
                                    "Please wait...")
        elif status == Status.BOT_STOPPED_RUNNING:
            self.status.config(text="Bot has finished gathering permits.\n"\
                                    "A csv file containing the permit(s) has been saved on your desktop.\n"\
                                    "The name of this file is in the format: <start date>_to_<end date>_permits")
        elif status == Status.BOT_IS_UPDATING_FILE:
            self.status.config(text="Bot is updating the permit(s) from the file you specified.\n"\
                                    "Please wait...")
        elif status == Status.BOT_STOPPED_UPDATING_FILE:
            self.status.config(text="Bot has finished updating permits in the given file.\n"\
                                    "A csv file containing updated permits has been saved to your desktop.\n"\
                                    "The name of this file is in the format: updated_<original name of the file>.")
        elif status == Status.BOT_ERROR:
            self.status.config(text="An error occurred while running the bot.\n"
                                    "Please keep the browser window open when running the bot and make sure you have\n"
                                    "internet connection.")


class DateRangeInvalid(Exception):
    def __init__(self):
        pass


def main():
    root = Tk()
    root.resizable(width=0, height=0)
    root.title("Pool Permit Scraper")

    Title(root)
    form = Form(root)
    run_bot = RunBotButtons(root, form)
    status_bar = StatusBar(root)
    run_bot.set_status_bar_object(status_bar)

    root.mainloop()


if __name__ == "__main__":
    main()
