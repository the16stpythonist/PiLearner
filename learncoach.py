from email.mime.text import MIMEText

import configparser
import threading
import datetime
import exercise
import smtplib
import random
import pickle
import exam
import math
import time
import os

progress_path = "{}\\progress".format(exercise.PROJECT_PATH)
config_path = "{}\\config.ini".format(exercise.PROJECT_PATH)


def get_email():
    """
    returns the email address, that was specified in the config file of the project
    :return: (string)
    """
    config = configparser.ConfigParser()
    config.read(config_path)
    return config["Info"]["email"]


def names_all_learning_processes(with_path=False):
    """
    Returns a list with either only the names or complete paths of the learning process files existing, depending on the
    parameter
    :param with_path: (boolean) whether the full path or only the names shall be subject of the list
    :return: (list) the list of existing learning process names or paths
    """
    if with_path:
        path_list = list(map(lambda x: "{}\\{}".format(progress_path, x), os.listdir(progress_path)))
        return path_list
    return os.listdir(progress_path)


def list_learning_processes():
    """
    Returns a list with all learning process objects, that were saved as pickled files in the progress folder
    :return: (list) list of LearningProcess objects
    """
    learning_processes = []
    learning_processes_paths = names_all_learning_processes(with_path=True)
    for path in learning_processes_paths:
        learning_processes.append(load_learning_process(file_path=path))
    return learning_processes


def subject_from_learning_process_filename(learning_process_filename):
    """
    calculates and returns a list [subject, subsubject] from the filename of a learning process file
    :param learning_process_filename: (string) the filename of a learning process file
    :return: (list) [subject, subsubject]
    """
    possible_separators = ["_", "-", "+"]
    for separator in possible_separators:
        if separator in learning_process_filename:
            filename_without_expansion = learning_process_filename.split(".")[0]
            split_filename = filename_without_expansion.replace(" ","").split(separator)
            return [split_filename[0], split_filename[1]]


def load_learning_process(subject="", subsubject="", file_path=""):
    """
    loads the specified learning process file as unpickled object into the memory and return it
    :param subject: (string) the subject
    :param subsubject: (string) the subsubject
    :param file_path: (string) the filepath to the file
    :return: (LearningProcess) the pickled learning process object
    """
    # assembling the filepath to the stored object depending on what parameters were passed
    pickled_file_path = ""
    if file_path != "":
        pickled_file_path = file_path
    else:
        if subject == "" or subsubject == "":
            raise FileNotFoundError("There is no learning process file without name")
        else:
            pickled_file_path = "{}\\{}_{}.pkl".format(progress_path, subject, subsubject)
    # using pickle to load the object from the file
    with open(pickled_file_path, mode="rb") as file:
        return pickle.load(file)


def save_learning_process(learning_process):
    """
    saves the learning process objects passed to the function into individual files via pickle
    :param learning_process: (LearningProcess) the objects to pickle
    :return: (void)
    """
    # assembling the filepath, into which it has to be saved
    file_path = "{}\\progress\\{}_{}.pkl".format(exercise.PROJECT_PATH, learning_process.subject,
                                                 learning_process.subsubject)
    # opening the file and pickle dumping the object into it
    with open(file_path, mode="wb+") as file:
        pickle.dump(learning_process, file)


class LearningProcess:
    """
    An object representing the process of learning a specific subject/subsubject.
    In theory the learning process, that is accomplished with this object is divided into three stages in this case
    three time intervals, that are specified by the following characteristics:
    1) In the first stage the interval between the repetitions in the form of PiLearn exams are the shortest with just
       a few days and the length of the exams is moderate. The intensive training prevents progress being lost due to
       a too long pause in between. After the first stage the content is transitioned into the long term memory, but
       only very loosely.
    2) The Second stage has intervals of around 1-2 weeks in between exams and a little bigger exams. During this time
       the content gets anchored into the long term memory.
    3) The third stage has very long intervals and small exams. It just exists to freshen up the already good memory
       from time to time.
    The object itself holds the options ans variables to create a schedule like just described, as well as track the
    progress, the user has with this schedule.
    """
    # the base values for the length of the time intervals in between exams of the different intervals
    FIRST_INTERVAL_TIMEDELTA = datetime.timedelta(days=3)
    SECOND_INTERVAL_TIMEDELTA = datetime.timedelta(days=12)
    THIRD_INTERVAL_TIMEDELTA = datetime.timedelta(days=30)

    # the base values for the max points of the exams in the different intervals
    FIRST_INTERVAL_MAX_POINTS = 20
    SECOND_INTERVAL_MAX_POINTS = 28
    THIRD_INTERVAL_MAX_POINTS = 18

    def __init__(self, subject, subsubject):
        # Both schedule and progress are lists, that contain tuples/lists [timestamp, points]
        # the schedule contains the dates and amount of points, that are planned to be done
        self.schedule = []
        # the progress is the list of exams actually done
        self.progress = []

        # the subject described
        self.subject = subject
        self.subsubject = subsubject

        # since the main loop of the observing process that is gonna check this learning process will obviously run
        # multiple times a day, it would sent the user too many notices if there was no variable to store, whether
        # that already happened or not
        # whether the user was already reminded of the next upcoming exam
        self.user_reminded = False

        # the amount of exams that have already been done to this moment, so the process can register when there
        # is new exam in the history of subject
        self.history = exam.load_subject_history(self.subject, self.subsubject)
        self.exams_already_done = len(self.history)

    def create_schedule(self, exam_count=20, time_multiplier=1.0, max_points_multiplier=1.0,
                        max_points_randomizer_range=2):
        """
        creates a new schedule for the object (overrides any old one).
        :param exam_count: (int) the total amount of exams that have to be done during the learning process
        :param time_multiplier: (float) the multiplier the base timespan between to exams can be modified with
        :param max_points_multiplier: (float) the multiplier the base value of max points per exam can be modified with
        :param max_points_randomizer_range: (int) the range of the randomizer for the max points
        :return: (void)
        """
        # The schedule will be divided in three parts, where the middle interval is slightly bigger
        interval_exam_count = self._split_exam_count_three(exam_count)

        # clearing the schedule before, in case there is already one in place
        self.schedule = []

        current_timestamp = datetime.datetime.today().timestamp()
        interval_timedeltas = [self.FIRST_INTERVAL_TIMEDELTA, self.SECOND_INTERVAL_TIMEDELTA,
                               self.THIRD_INTERVAL_TIMEDELTA]
        interval_max_points = [self.FIRST_INTERVAL_MAX_POINTS, self.SECOND_INTERVAL_MAX_POINTS,
                               self.THIRD_INTERVAL_MAX_POINTS]
        # adding the three intervals to the schedule
        for interval in range(3):

            for i in range(interval_exam_count[interval]):
                # calculating the values relative to what interval the loop is in and applying multiplier to them
                time_delta = interval_timedeltas[interval]
                time_delta = datetime.timedelta(days=int(time_delta.days * time_multiplier))
                current_timestamp = (datetime.datetime.fromtimestamp(current_timestamp) + time_delta).timestamp()
                max_points = int(random.randint(interval_max_points[interval] - max_points_randomizer_range,
                                                interval_max_points[interval] + max_points_randomizer_range))
                max_points = int(max_points * max_points_multiplier)
                # actually adding the two values combined in one list to the schedule list
                self.schedule.append([current_timestamp, max_points])

    def create_exam(self):
        """
        creates an exam of the subject with the maximum amount of points specified in the next entry of the schedule
        :return: (void)
        """
        exam.create_exam(subject=self.subject, subsubject=self.subsubject,
                         max_points=self.schedule[len(self.progress)][1])

    def update_progress(self):
        """
        updates the progress of the learning progress by replacing the old history object with a newly created one
        and checking for differences in exam counts before and after. In case there are new exams they are not only
        added to the progress list, but the max points also replace the value in the according schedule entry, in case
        they differ.
        :return: (void)
        """
        # replacing the history object with a new one
        self.history = exam.load_subject_history(self.subject, self.subsubject)
        # in case the length of the new history is longer than the variable 'exams_already_done', that means a exam has
        # been solved and thus is part of the progress in this learning progress
        if len(self.history) > self.exams_already_done:
            exam_count_difference = len(self.history) - self.exams_already_done
            keys_list = self.history.keys()
            for i in range(exam_count_difference):
                # since not the first few items but the last of the history shall be addressed, the negative index
                reverse_index = -(i+1)
                # applying this index to the key list to get the last few items. Items of the SubjectHistory are lists
                # with three items each [max_points, points, length]
                history_item = self.history[keys_list[reverse_index]]
                # updating the max points of the schedule and adding the timestamp (key) and actual points to progress
                self.schedule[len(self.progress)] = history_item[0]
                self.progress.append([float(keys_list[reverse_index]), history_item[1]])
                self.exams_already_done += 1
            # resetting the user was reminded state, as the exam of the reminder was done
            self.user_reminded = False

    def days_until_exam(self):
        """
        returns the amount of days the next exam has to be done
        :return: (int) the days until the next exam has to be done
        """
        # the index at which the next due exam can be found within the schedule
        lookup_index = len(self.progress)
        # creating a timedelta object from the difference of the datetime timestamp in the list and today()
        timedelta = datetime.datetime.fromtimestamp(self.schedule[lookup_index][0]) - datetime.datetime.today()
        return timedelta.days

    def get_schedule_string(self):
        """
        creates a string representation of the schedule, so it can be reviewed by the user.
        Simple string rep takes the form:

        due date         max points
        2016-08-12       12
        2016-09-1        34
        ...              ...
        :return: (string) the string form of the schedule
        """
        return self._get_simple_list_string_rep(self.schedule, 16, "due date", "max points")

    def get_progress_string(self):
        """
        creates a string representation of the progress, so it can be reviewed by the user.
        Simple string rep takes the form:

        completion date  achieved points
        2016-08-12       12
        2016-09-1        34
        ...              ...
        :return: (string) the string form of the progress
        """
        return self._get_simple_list_string_rep(self.progress, 16, "solve date", "achieved points")

    def is_user_reminded(self):
        """
        since the main loop of the observing process that is gonna check this learning process will obviously run
        multiple times a day, it would sent the user too many notices if there was no variable to store, whether
        that already happened or not
        :return: (boolean) whether the user was already reminded of the next upcoming exam
        """
        return self.user_reminded

    @staticmethod
    def _split_exam_count_three(exam_count, delta=1):
        """
        divides the passed amount of exams in one schedule by three to represent the first, middle and last learning
        interval. The method will not split them equally however, it will split them into three parts, so that the
        middle part is always slightly bigger than the last and first, this difference can be set by delta.
        The method will return a list with three items, them being the integers the method calculated.
        :param exam_count: (int) the number of exams in one schedule
        :return: (list) a list with three items, being the split up parts of the given number of exams
        """
        one_third = float(exam_count) / 3
        # in case the delta value is too big, limiting it to maximum
        if delta >= one_third:
            delta = int(one_third - 1)
        if exam_count % 3 == 0:
            # in case the exam count is dividable by three, subtracting one count from the first and last, so it can be
            # added to the middle one
            split_count_list = [int(one_third - delta), int(one_third + 2 * delta), int(one_third - delta)]
            return split_count_list
        else:
            # in case the cont is not dividable, doing so anyways and rounding the first and last down while rounding
            # the middle one up. This way the total amount will stay the same anyways
            split_count_list = [int(math.floor(one_third) - delta),
                                int(math.floor(one_third) + (exam_count % 3) + (2 * delta)),
                                int(math.floor(one_third) - delta)]
            return split_count_list

    @staticmethod
    def _get_simple_list_string_rep(iterable, column_length, column1_header, column2_header):
        """
        creates a string representation of an iterable, that consits of another iterable with each two entries:
        [[1,2], [1,2], [1,2]].
        The string rep will look like:
        column1 header       column2 header
        2016-08-12           12
        2016-09-1            34
        ...                  ...
        :return: (string) the string form of the list
        """
        column_length_1 = column_length
        string_list = []
        # adding the headers to the list
        string_list.append(column1_header)
        string_list.append(" " * (column_length_1 - len(column1_header)))
        string_list.append(column2_header)
        string_list.append("\n")
        for entry in iterable:
            # adding the actual date to the string
            date_string = str(datetime.datetime.fromtimestamp(entry[0]).date())
            string_list.append(date_string)
            string_list.append(" " * (column_length_1 - len(date_string)))
            # adding the amount of max points to the string
            string_list.append(str(entry[1]))
            string_list.append("\n")
        # removing the last new line from the last string
        string_list.pop(-1)
        # returning the string
        return ''.join(string_list)


class LearningCoach:
    """
    The learn coach object is some sort of observer, that is meant to run seperatly from the main PiLearn program. It
    is meant to run all the time as a background process (It consumes virtually no CPU power, only activates every
    three hours anyways). The main loop continuesly loads and saves the LearningProcess objects from the filesystem
    and checks if an exam is due for any if them, in case there is a exam due in 3 days or less for one of the active
    subjects, the Coach will issue the creation of this very exam and send a reminder email to the user (email
    specified in the config of the project), that the exam should be done within the next 3 days. Additionally the coach
    is also responsible for keeping track on the progress that has been made, meaning to add/update the progress
    attributes of each learning process in case a change (solved exam) can be registered.
    """
    def __init__(self):
        super(LearningCoach, self).__init__()
        self.email = get_email()

    def run(self):
        # running the main loop all the time, since the Thread is supposed to be a background progress
        while True:
            # since the intervals between the are pretty macroscopic pausing the Thread for 3 hours (10800 seconds)
            time.sleep(2)

            # getting list of all learning process objects
            learning_processes = list_learning_processes()

            # looping through the list and checking the due dates for the next exams
            for learning_process in learning_processes:
                # In case the next exam of the learning process is due in or less days and the user wasnt reminded yet
                # sends an email reminder and creates the exam
                if learning_process.days_until_exam() <= 3 and not learning_process.is_user_reminded():
                    self.send_reminder_email(learning_process)
                    # learning_process.create_exam()
                    learning_process.user_reminded = True

                # Updating the progress for every learning process
                learning_process.update_progress()

                # saving the learning process objects into the files
                save_learning_process(learning_process)

    # TODO: Find a better solution for the email thing, all the settings has to enable for the use are too complicated
    def send_reminder_email(self, learning_process):
        """
        sends an email from the email address specified in the config of the project to the exact same email, which is
        supposed to be the users mail address. The mail simply contains a message, that a new exam has been created and
        is due in three days, meaning the user should be solving it in this time span.
        :param learning_process: (LearningProcess) the learning process object, whose next exam is due
        :return: (void)
        """
        # the string content of the email
        content_string_list = ["Hello", "\n\n", "your next scheduled exam of the subject '", learning_process.subject,
                               " - ", learning_process.subsubject, "' is due in ",
                               str(learning_process.days_until_exam()),
                               "days. The exam has already been created in your exams folder.", "\n\n",
                               "Sincerely,\n- the PiLearner Coach"]
        content_string = ''.join(content_string_list)

        # creating the message object from the string
        msg = MIMEText(content_string)
        msg["Subject"] = "PiLearner '{} - {}'".format(learning_process.subject, learning_process.subsubject)
        msg["From"] = self.email
        msg["To"] = self.email

        # send the email via the smtp server
        smtp_server = smtplib.SMTP("127.0.0.1")
        smtp_server.send_message(msg)
        smtp_server.quit()


if __name__ == "__main__":
    learning_process = LearningProcess("Test", "SubTest")
    learning_process.create_schedule()
    save_learning_process(learning_process)
    coach = LearningCoach()
    coach.run()




