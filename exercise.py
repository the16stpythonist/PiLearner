__author__ = 'Jonas'
__version__ = '0.0.0'

import configparser
import datetime
import inspect
import random
import os


# Dynamic assignment of the project path on a module level, as this will grant a few more possibilities, when moving
# the project within te file structure. ONe could also think about dynamically and temporaryly adding the path to the
# PYTHONPATH before main execution, so this would have to be a dependency of the project
config = configparser.ConfigParser()
config.read("config.ini")
PROJECT_PATH = config["Paths"]["project_dir"]


def reset_exercise_progress(subject, subsubject, name):
    """
    resets the progress of the specified exercise, that means deleting the history and resetting the statistical info
    :param subject: (string) The subject of the exercise
    :param subsubject: (string) The subsubject of the exercise
    :param name: (string) The name of the Exercise
    :return: (void)
    """
    # checking whether the given path exists
    subject_path = "{0}\\subjects\\{1}".format(PROJECT_PATH, subject)
    if not os.path.exists(subject_path):
        raise NotADirectoryError("The subject {0} with the path '{1}' does not exist".format(subject, subject_path))
    subsubject_path = "{0}\\{1}".format(subject_path, subsubject)
    if not os.path.exists(subsubject_path):
        raise NotADirectoryError("The subsubject {0} with the given path {1} does not exist".format(subsubject,
                                                                                                    subsubject_path))
    exercise_path = "{0}\\{1}".format(subsubject_path, name)
    if not os.path.exists(exercise_path):
        raise NotADirectoryError("The exercise {0} with the given path {1} does not exist".format(name, exercise_path))

    # loading config file
    config = configparser.ConfigParser()
    config_path = "{0}\\config.ini".format(exercise_path)
    config.read(config_path)

    # resetting the statistical info
    for statistic_info in dict(config["STATISTIC"]).keys():
        config["STATISTIC"][statistic_info] = 0

    # deleting the history
    config["HISTORY"] = {}

    # saving the changed config
    with open(config_path, mode="w") as file:
        config.write(file)


def load_exercise(subject, subsubject, name):
    """
    Since the Exercise class is constructed by using a bunch of descriptive arguments for initialization (which I think
    is good programming practice, because it best imitates the real life notion of an object) this function works as
    a wrapper to easily create Exercise objects with minimal information, making further use of the Exercise module
    more confinient.
    Thinking about it one really only needs three parameters for specifying an exercise, the subject, the subsubject
    and its name, since this will create a path directly referencing the exercise folder, in which the content and
    additional information can be extracted from the files within. But because this rather resembles a process than a
    object, it is done via a old school function.
    :param subject: (string) The subject of the exercise
    :param subsubject: (string) The subsubject of the exercise
    :param name: (string) The name of the Exercise
    :return: (Exercise) Returns the exact exercise, that is being fully described, by the given 3 parameters
    """

    # checking whether the given path exists
    subject_path = "{0}\\subjects\\{1}".format(PROJECT_PATH, subject)
    if not os.path.exists(subject_path):
        raise NotADirectoryError("The subject {0} with the path '{1}' does not exist".format(subject, subject_path))
    subsubject_path = "{0}\\{1}".format(subject_path, subsubject)
    if not os.path.exists(subsubject_path):
        raise NotADirectoryError("The subsubject {0} with the given path {1} does not exist". format(subsubject,
                                                                                                     subsubject_path))
    exercise_path = "{0}\\{1}".format(subsubject_path, name)
    if not os.path.exists(exercise_path):
        raise NotADirectoryError("The exercise {0} with the given path {1} does not exist".format(name, exercise_path))

    # loading config file
    config = configparser.ConfigParser()
    config.read("{0}\\config.ini".format(exercise_path))

    # later on making the difference between the mathematical and social exercises
    max_points = int(config["INFO"]["max_points"])
    use_frequency = float(config["STATISTIC"]["use_frequency"])
    last_used = float(config["STATISTIC"]["last_use"])
    average_points = float(config["STATISTIC"]["average_points"])

    # loading the content latex string
    content = ""
    with open("{0}\\content.tex".format(exercise_path), mode="r") as content_file:
        content = content_file.read()

    # loading the answer string
    answer = ""
    with open("{0}\\answer.tex".format(exercise_path), mode="r") as answer_file:
        answer = answer_file

    return Exercise(name, max_points, content, answer, average_points, last_used, use_frequency, exercise_path)


class ExerciseHistory:
    """
    The ExerciseHistory objects are basically dictionary style sequnces, that contain the record of all past uses of
    one exercise. The internal dictionary assigns every achieved points (value) to the datetime it was solved (key).
    The Objects wrap the functionality of easily adding entries, creating subsequnces based on time intervals and
    the calculation of the average points.
    :ivar dict: (dict) the internal dictionary actually containing the data
    """

    def __init__(self):
        # The dictionary in which the data will be stored, with the date of use being the date time and the item being
        # the amount of points achieved that day
        self.dict = {}

    def add(self, datetime_timestamp, points):
        """
        adds a new entry to the sequence
        :param datetime_timestamp: (int) the timestamp from the date_time object
        :param points: (float) the amount of points reached
        :return: (void)
        """
        # adding the new entry to the dictionary
        self.dict[str(datetime_timestamp)] = str(points)

    def get_dictionary(self):
        """
        :return: (dict) the internal dictionary
        """
        return self.dict

    def get_average_points(self, start=None, stop=None):
        """
        Calculates the average points of the exercise within the given index span. On default uses all entries
        :param start: (int) the start index, by normal python slicing convention
        :param stop: (int) the end index, by normal python slicing convention
        :return: (float) the average amount of points within the range
        """
        point_list = list(self.dict.values())
        # slicing the list, in case indexes were passed
        if stop is not None:
            point_list = point_list[:stop]
        if start is not None:
            point_list = point_list[start:]
        # calculating the total amount of points and then dividing it by the amount by the amount of entries
        total_points = 0
        for points in point_list:
            total_points += float(points)
        return float(total_points / len(point_list))

    def get_interval(self, datetime_timestamp_start, datetime_timestamp_end):
        """
        creates a new ExerciseHistory object from the existing one, only containing the entries from within the
        specified time interval
        :param datetime_timestamp_start: (float) the datetime.timestamp of the time the interval starts
        :param datetime_timestamp_end: (float) the datetime.timestamp of the time the interval ends
        :return: (ExerciseHistory) the new sliced interval of the History
        """
        date_list = list(self.dict.keys())
        new_history = ExerciseHistory()
        for date in date_list:
            # only adding those entries, whose timestamps are bigger than the minimum and smaller than the max
            if float(date) >= datetime_timestamp_start and float(date) <= datetime_timestamp_end:
                new_history.add(date, self.dict[date])
        return new_history

    def keys(self):
        return list(self.dict.keys())

    def values(self):
        return list(map(lambda x:int(x), self.dict.values()))

    def __contains__(self, item):
        """
        When using the 'y in x' syntax on this object it will check whether the key exists, rather than the item, since
        one would rather want to know if the exercise was done on a given date
        :param item:
        :return:
        """
        return item in self.keys()

    def __iter__(self):
        return self.dict.__iter__()

    def __getitem__(self, item):
        if isinstance(item, str):
            if item in self.keys():
                return int(self.dict[item])
        elif isinstance(item, int):
            if str(item) in self.keys():
                return int(self.dict[str(item)])

    def __setitem__(self, key, value):
        self.dict[key] = value

    def __len__(self):
        return len(self.dict)


class Exercise:
    """
    The Exercise class is mainly designated to encapsulate the information and attributes an exercise is meant to
    posses or consist of.
    The Exercises itself consist of two relatively different types of attributes/information:
    1.) The Essential Information
        Every attribute that is essential to ones understanding of the concept of an exercise. SO it basically describes
        those attributes without which an exercise would not work, these are the name, which is an identifier to
        differentiate between different exercises, the maximum amount of achievable points and the actual content of the
        exercise.
    2.) The Statistical Information
        Those attributes, that are not essential to the functionality of the object, but provide additional information
        to enhance the algorithm, that statistically chooses which exercises to use in an exam.

    :ivar name: (string) The identifier of the exercise and the name that is to be displayed on the written exam later
    :ivar max_points: (int) The maximum amount of points one can achieve with this exercise
    :ivar points: (int) the actual amount of achieved points
    :ivar content: (string) The string containing the actual content of the exercise, written in LaTeX

    :ivar average_points: (float) The statistical average amount of achieved points throughout all uses
    :ivar use_frequency: (int) The total amount of all uses throughout all exams
    :ivar history: (ExerciseHistory) the object containing the history of the exercise, meaning a list of all past
    solves and achieved points of the exercise
    """
    def __init__(self, name, max_points, content, answer, average_points, last_use, use_frequency, path):
        # Setting the identifying name odf the excercise object
        self.name = name
        # Setting the maximum points, the average amount of points the user has in this exercise and initializing
        # the amount of points gathered to zero
        self.average_points = average_points
        self.max_points = max_points
        self.points = 0
        # The content and the answer string
        self.content = content
        self.answer = answer
        # Initializing the status of the exercise to 'not solved yet'
        self.solved = False
        # Setting the last time of use and the use frequency
        self.last_use = last_use
        self.use_frequency = use_frequency
        # The Path in which the file is being stored
        self._path = path

        # creates the history object of the exercise
        self.history = self._load_history(self._path)

    def solve(self, points):
        """
        This method is meant to be called at the point one has already finished the generated exam and is entering the
        achieved results back into the system. This will then proceed to update the statistical attributes of
        the exercise, once the amount of achieved points was passed.
        WORKING PRINCIPLE:
        Aside from simply calling the time.time() function as the last time of use and incrementing the total amount of
        uses, this method will also update the average points. The average amount of points is calculated by the
        history of the exercise, the object, that contains the record of all previous uses of the exercise.
        :param points: (int) The achieved amount of points for the exercise, when solving the exam
        :return: (void)
        """
        self.solved = True
        self.points = points
        # Incrementing the total amount of all times the exercise has been used
        self.use_frequency += 1
        # adding the most recent solve to the history
        self.history.add(datetime.datetime.today().timestamp(), points)
        # updating the average points by using the history of the exercise
        self.average_points = self.history.get_average_points()

    def save(self):
        """
        The save method transfers the information, stored in the Exercise object from the temporary runtime memory into
        the longtime persistent memory/file structure. Therefore the exercsie needs knowledge of its own folderpath.
        It then goes on and reads its orignial information from the 'config.ini' file in the exercise folder, changes
        only the statistical information (since, if you think about it, its literally the only thing that will ever
        change during the runtime existence of an exercise object) and then writes the new ini-config tree into the file
        NOTE:
        Since this function only saves the data, that is already stored within the attributes of the exercise object,
        one would want to call the 'solve' function before saving.
        :return: (void)
        """
        # creating the ConfigParser to save the new Statistical data. First loading the old config specs
        config = configparser.ConfigParser()
        config_path = "{0}\\config.ini".format(self._path)
        config.read(config_path)
        # the dictionary of entries in the statistical section of the .ini file
        statistic_dict = {"average_points": self.average_points, "use_frequency": self.use_frequency,
                          "last_use": self.last_use}
        # replacing the old specs with the updated Statistic and writing to the file
        config["STATISTIC"] = statistic_dict
        config["HISTORY"] = self.history.get_dictionary()
        config["INFO"]["name"] = self.name
        config.write(open(config_path, mode="w"))

    def is_solved(self):
        """
        returns whether the exercise has been solved or not
        :return: (boolean) the status of the exercise
        """
        return self.solved

    @staticmethod
    def _load_history(exercise_path):
        """
        Creates a ExerciseHistory object for the history, when passed the path to the according root folder of the
        exercise
        :param exercise_path: (string) the path to the root folder of the exercise
        :return: (ExerciseHistory) the exercise history of the exercise, whose root path was passed
        """
        # creating the history object and the config parser to read the history from the file
        history = ExerciseHistory()
        config = configparser.ConfigParser()
        config_path = "{}\\config.ini".format(exercise_path)
        config.read(config_path)

        # checking whether the exercise config even has a history creating one in case it hasn't
        if "HISTORY" not in config.keys():
            config.add_section("HISTORY")
            with open(config_path, mode="w") as file:
                config.write(file)
            return history

        # adding the entries of the 'History' dict to the history object one by one
        for key in dict(config["HISTORY"]).keys():
            history.add(float(key), float(config["HISTORY"][key]))
        return history


class ExerciseList:
    """
    The ExerciseList objects define custom containers/sequences specialiced on holding only Exercise objects within its
    internal list. The ExerciseList is widely accessible as every other list, as one could acces the length with the
    len() function and iterate through the exercises with, utilizing a for loop.
    The class was mainly introduced due to the need of custom behaviour when handling a sequence of exercises, which
    would be unintuitive and clunky when just using a standard list. These custom features include:
    - Sorting the inner sequence by the use of custom criteria, such as the different attributes of the Exercise objects
    - The built-in algorithm to randomly+statistically determine which exercises should be incoorporated into the exam

    :ivar list: (list) The actual list object, in which the Exercise objects are being stored in
    :ivar max_points: (int) Zhe accumulated amount of maximum points of all the exercises being stored
    """
    def __init__(self, *exercises):
        # Checking whether the argument exercises is a single list of Exercise objects or directly multiple such objects
        # and building the internal list either way
        self.list = []

        if len(exercises) == 1 and isinstance(exercises[0], list):
            self.list = exercises[0]
        else:
            self.list = list(exercises)

        # Setting up the check variable to know, when there are no more exercises available
        self.empty = True
        if len(self) >= 1:
            self.empty = False

        # The list containing t6he accumulated amount of maximum points aof all exercises
        self.max_points = 0
        self._update_max_points()

    def append(self, exercise):
        """
        when passed a Exercise object as parameter, appends it to the sequence
        :param exercise: (Exercise) The object to be added
        :return: (void)
        """
        self.list.append(exercise)

    def eliminate_exercise(self):
        """
        This method is the implementation of the algorithm, that chooses the exercises to be used in a test. The method
        will basically remove an exercise of choice from the list. To determine which exercise is to be removed from the
        list, the method works in two steps, the first being pure random choice and the second step a random decision,
        whose probabilities are influenced by the statistical data of the exercises. This is how the two steps work:
        1.) The 'random' module of the python standard library helps to totally randomly determine two Exercises from
            the total ExerciseList. Those two Exercises will then enter the decision step:
        2.) For the decision about which of the two exercises will be elimintaed from the list both of them are
            initialized with a 50/50 chance. Then their statistical values are being compared as followed:
            The one that has been used more often will receive a higher possibility to be removed (so its not the same
            exercises all the time), whereas the exercise with more average mistakes is less likely to be removed,
            since the user had difficulties with the exercise and should probably practice more to master its content.
        :return: (void)
        """
        # The First stage of the decision process
        # Two exercises are randomly (with the same possibility) chosen by utilizing the python 'random' module
        compare_exercises = random.sample(self.list, 2)

        # The Second stage of the decision process
        # comparing the two sampled exercises, by modifying their respective possibility of being eliminated, using
        # their statistical data.

        # creating the possibility list. initializing it with a fifty-fifty chance at first
        compare_exercises_possibilities = [0.5, 0.5]

        # increasing the elimination possibility of the exercise, that was already used more often, than the other,
        # using the use difference
        use_difference = compare_exercises[0].use_frequency - compare_exercises[1].use_frequency
        compare_exercises_possibilities[0] += use_difference * 0.01
        compare_exercises_possibilities[1] -= use_difference * 0.01

        # decrasing the elimination possibility of the exercise, the user had averagly more mistakes with
        average_mistakes_difference = compare_exercises[1].average_points - compare_exercises[0].average_points
        compare_exercises_possibilities[0] -= average_mistakes_difference * 0.02
        compare_exercises_possibilities[1] += average_mistakes_difference * 0.02

        # using those generated possibilities for making the final random decision
        random_float = float(random.randrange(0, 100, 1)) / 100
        if random_float <= compare_exercises_possibilities[0]:
            self.list.remove(compare_exercises[0])
        else:
            self.list.remove(compare_exercises[1])

        # updating the maximum sum of points of all exercises
        self._update_max_points()

    def sort_by_points(self):
        """
        Sorts the internal list of Exercise objects, so that it begins with the exercises with the least maximum points
        and ends with those that offer the most max points. This should most likely be used before the creation of the
        exam as an exam should begin with the easy exercises so it can progressively get harder.
        The method implements the Bubble Sort algorithm to do the sorting.
        :return: (void)
        """
        for n in range(len(self.list)):
            for i in range(len(self.list)-1):
                exercise1 = self.list[i]
                exercise2 = self.list[i+1]
                if exercise2.max_points <= exercise1.max_points:
                    self.list[i] = exercise2
                    self.list[i+1] = exercise1

    def get_paths_list(self):
        path_list = []
        for exercise in self.list:
            path_list.append(exercise._path)
        return path_list

    def _update_max_points(self):
        """
        After a change of the lists makeup has occured this function should be called to keep the attribute of maximum
        points properly up to date
        :return: (void)
        """
        self.max_points = 0
        for exercise in self.list:
            self.max_points += exercise.max_points

    def __len__(self):
        return len(self.list)

    def __iter__(self):
        return self.list.__iter__()

    def __getitem__(self, exercise_name):
        """
        returns the exercise object with the given name.
        Since the object is not based upon a dictionary, but a list, the method will loop through the list until it
        finds the exercise with the given name, vanilla style. Raises a key error in case there is no exercise with
        the given name
        :param exercise_name: (string) the name of the exercise, whose object should be returned
        :return: (Exercise) the exercise with the given name
        """
        for exercise in self.list:
            if exercise.name == exercise_name:
                return exercise
        raise KeyError("There is no exercise by the name '{}' in the list".format(exercise_name))
