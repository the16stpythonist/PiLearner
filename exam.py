__author__ = "Jonas Teufel"
__version__ = "0.0.0"

import PiLearner.exercise as exercise
import configparser
import datetime
import time
import os


LATEX_EXAM_HEADER = r"""\documentclass[a4paper, 12pt]{article}

% Nutzung der deutschen Rechtschreibung und Laute
\usepackage[german]{babel}
\usepackage[utf8]{inputenc}
\usepackage{amsmath}
\newcommand{\abs}[1]{\ensuremath{\left\vert#1\right\vert}}
\usepackage{setspace}
\usepackage{gensymb}
\usepackage{geometry}
% \usepackage[colorinlistoftodos]{todonotes}

% Einbindung des "biblatex" Pakets, welches die Möglichkeiten der
% Bibliographie erweitert. Nutzt die im Projektverzeichnis befindliche
% Datei "bibliography.bib" als Quelle für BiBTeX-Verweise
% \usepackage{csquotes}
% \usepackage[style=verbose-ibid]{biblatex}
%\addbibresource{bibliography.bib}

% Den Zeilenabstand auf den Wert 1.43 setzen, da dies in Latex äquivalent
% zu einem "tatsächlichen" Zeilenabstand von 1.5 ist
\setstretch {1.433}
% Ränder so anpassen, dass mehr Platz ausgenutzt wird, man den Druck aber
% trotzdem noch gut an der linken Seite lochen und einordnen kann
\geometry{verbose,a4paper,tmargin=25mm,bmargin=25mm,lmargin=30mm,rmargin=20mm}

% HOW TO INSERT SINGLE FIGURES
% Das "float" package wird gebraucht um Latex zu forcen, das Bild an genau der ausgewählten Stelle einzufügen
\usepackage{float}
\usepackage{graphicx}
% \begin{figure}[H]
% \caption{Example text}
% \centering
% \includegraphics[width=0.5\textwidth]{Filename}
% \label{fig:name}
% \end{figure}
"""

LATEX_EXAM_TITLE = r"""
\begin{document}
\setstretch{1.0}
\begin{center}
\fbox{\fbox{\parbox{16cm}{\centering \huge {\it %%subject%%} - PiLearn Prüfung \\
\LARGE {\it %%subsubject%%}\\
\today}}}
\end{center}
\setstretch {1.433}
\vspace{5mm}
Name: \vspace{1mm} \hrule\\[3mm]"""

LATEX_EXAM_EXERCISE_HEADER = r"""
\noindent {\large \bf Aufgabe %%index%% - \normalsize %%name%%} \hfill {\small /%%max_points%%P.}
\newline \noindent """


def create_exam(subject, subsubject, max_points):
    """
    A wrapper function to destill the process of the creation of an exam down to one function and removing the necessity
    to bundle this functionality within the Exam class where it would feel unintuitive and contra object-oriented.
    The function creates an exam object of the passed subject and subsubject, generates a PDF file from that object and
    also generates the session file to the corresponding test. Session files are being used to be able to file in the
    answers and the achieved points to the right exercises, even after their objects have been removed from the
    temporary memory after the end of the program runtime.
    :param subject:
    :param subsubject:
    :return:
    """
    # creating the exam object and creating the actual content
    exam = Exam(subject, subsubject, max_points=max_points)
    exam.create_content()

    # generating the pdf
    generate_pdf(exam)

    # generating the session file
    session_file_path = "{0}\\exams\\{1} - {2}.session".format(exercise.PROJECT_PATH, exam.subject, exam.subsubject)
    # creating the file and writing the content to it
    with open(session_file_path, mode="w", encoding="utf-8") as file:
        # writing the exercise names into the session file
        for exercise_object in exam.exercise_list:
            file.write("{0}\n".format(exercise_object.name))


def generate_pdf(exam_obj):
    """
    When passed an exam_object this function will go on and create a TEX file from the content string of the exam and
    then convert the TEX file into a PDF file using PDFLATEX in a operating system command issued from within python
    :param exam_obj: (Exam) The exam, which to make the PDF file from
    :return: (void)
    """
    # creating a temporary .tex file with the whole content string in the exams folder of the project
    tex_file_path = "{0}\\exams\\{1}.tex".format(exercise.PROJECT_PATH, exam_obj.subject)
    # creating the file and writing the content to it
    with open(tex_file_path, mode="w", encoding="utf-8") as file:
        file.write(exam_obj.content)
    # giving the order to create the pdf
    os.system("pdflatex -interaction nonstopmode {0}".format(tex_file_path))


def get_session_path(subject, subsubject):
    """
    returns the path of the session file of the given subject. This will only assemble a string and does not say, that
    the file actually exists
    :param subject: (string) the subject of the exam
    :param subsubject: (string) the subsubject of the exam
    :return: (string) the path of the session file to the specified subject
    """
    # assembling the path of the session file to the specified subject
    session_name = "{} - {}.session".format(subject, subsubject)
    session_path = "{}\\exams\\{}".format(exercise.PROJECT_PATH, session_name)
    return session_path


def session_exists(subject, subsubject):
    """
    checks and returns whether there exists a open session to the specified subject
    :param subject: (string) the subject of the exam to check
    :param subsubject: (string) the subsubject of the exam to check
    :return: (bool) whether the session exists or not
    """
    # simply checking for the existence of the session file
    return os.path.exists(get_session_path(subject, subsubject))


def get_session_content(subject="", subsubject="", sessionfile_path=""):
    """
    returns the contents of the session file specified in the form of a list, containing the names of all exercises,
    that were used in the session
    :param subject: (string) the subject of the exam
    :param subsubject: (string) the subsubject of the exam
    :return: (list) the list of all exercise names used in session
    """
    if sessionfile_path == "":
        # creating the actual path of the session file, in case the path was not specified
        session_path = get_session_path(subject, subsubject)
    else:
        if os.path.exists(sessionfile_path) and ".session" in sessionfile_path:
            session_path = sessionfile_path
        else:
            raise FileNotFoundError("Session content couldnt be read, file '{}' no session".format(sessionfile_path))
    # opening the session file and reading its content
    session_lines_list = []
    with open(session_path, mode="r") as file:
        session_lines_list = file.read().split("\n")

    # getting rid of the new line characters in the line list, so that only the actual content lines sty in it
    while "" in session_lines_list:
        session_lines_list.remove("")

    return session_lines_list


def get_session_path_list():
    """
    Returns:
    A list containing the string paths to all the currently existing session files
    """
    # Getting the path to the folder, in which the session files are stored. Iterating through the file names of the
    # files within that 'exams' folder, building the full file paths and checking for them actually being files and for
    # their file extensions.
    session_path_list = []
    exams_path = get_exams_path()
    file_name_list = os.listdir(exams_path)
    for file_name in file_name_list:
        file_path = os.path.join(exams_path, file_name)
        if os.path.isfile(file_path):
            # Getting the extension type from the file name. In case the file has the 'session' extension, adding it
            # to the list of session file paths
            extension_name = file_name.split(".")[1]
            if extension_name == "session":
                session_path_list.append(file_path)
    return session_path_list


def get_session_name_list():
    """
    Returns:
    A list, containing the string names (without the file extensions) of all the currently existing session files
    """
    session_name_list = []
    session_path_list = get_session_path_list()
    for session_path in session_path_list:
        session_name = get_session_name(session_path)
        session_name_list.append(session_name)
    return session_name_list


def get_session_name(session_path):
    """
    Args:
        session_path: The path string of the session file, whose name should be returned

    Returns:
    The name of the session file without the extension
    """
    # Getting the file name with extension from the whole path
    file_name = os.path.basename(session_path)
    # Because it can be assumed, that only the paths of actual session paths are being passed onto this function
    # the actual name of the function without the extension can be obtained by removing the '.session' substring
    file_name = file_name.replace(".session", "")
    return file_name


def exam_from_session(subject="", subsubject="", sessionfile_path=""):
    """
    creates and returns an Exam object instance, that was build with all the exercises from the session file specified.
    The session file can be specified by passing either:
    - the subject and the subsubject, so the function will search for a according session file
    - straight up the path of the session file
    :param subject: (string) the subject of the exam
    :param subsubject: (string) the subsubject of the exam
    :param sessionfile_path: (string) the path to an specific session file
    :return: (Exam) the exam object, representing the open session
    """
    # acquiring the session content
    exercise_names_list = []
    subject_name = subject
    subsubject_name = subsubject
    if sessionfile_path == "":
        exercise_names_list = get_session_content(subject=subject, subsubject=subsubject)
    else:
        exercise_names_list = get_session_content(sessionfile_path=sessionfile_path)
        # getting the subject and subsubject from the file path, since they are important and probably weren't
        # passed as parameters, when the path already was.
        # Session file naming convention: "subject - subsubject.session"
        sessionfile_name_split = os.path.basename(sessionfile_path).replace(".session", "").replace(" ", "").split("-")
        subject_name = sessionfile_name_split[0]
        subsubject_name = sessionfile_name_split[1]

    # building a list with exercises from the names
    exercise_list = exercise.ExerciseList()
    for exercise_name in exercise_names_list:
        exercise_list.append(exercise.load_exercise(subject_name, subsubject_name, exercise_name))

    # building the exam object with the list of exercise objects
    exam = Exam(subject=subject_name, subsubject=subsubject_name, exercise_list=exercise_list)

    return exam


def load_subject_history(subject, subsubject):
    """
    creates a SubjectHistory object, that represents the history of all past uses and exams of the subject of the
    exam specified
    :param subject: (string) the subject of the exam
    :param subsubject: (string) the subsubject of the exam
    :return: (SubjectHistory) the history of the given subject
    """
    # loading the config
    config = configparser.ConfigParser()
    config_path = "{}\\subjects\\{}\\{}\\config.ini".format(exercise.PROJECT_PATH, subject, subsubject)
    config.read(config_path)
    # the new dictionary to be returned
    history = SubjectHistory()
    for key in dict(config["HISTORY"]).keys():
        item_split = config["HISTORY"][key].split(";")
        item_split = list(map(lambda x: int(x), item_split))
        history.add(float(key), *item_split)
    # returning the history object
    return history


def save_history_solved_exam(solved_exam):
    """
    Takes an exam object, that is completely solved, and adds its parameters max_points, points and length as a new
    entry to the history object and then saves it into the config file of the subject persistently
    :param solved_exam: (Exam) the instance of an Exam, that has been completely solved
    :return: (boolean) whether the save was successful or not
    """
    subject = solved_exam.subject
    subsubject = solved_exam.subsubject
    # loading the config
    config = configparser.ConfigParser()
    config_path = "{}\\subjects\\{}\\{}\\config.ini".format(exercise.PROJECT_PATH, subject, subsubject)
    config.read(config_path)
    # checking whether the exam is actually solved
    if solved_exam.is_solved():
        # creating the history object if the exam
        history = load_subject_history(subject, subsubject)
        # adding a new entry to the history
        history.add(datetime.datetime.today().timestamp(), solved_exam.max_points, solved_exam.points,
                    solved_exam.length)
        # using the dictionary from the history for the config parser
        config["HISTORY"] = history.get_config_compatible_dict()
        # saving the config parser
        with open(config_path, mode="w") as file:
            config.write(file)
        return True
    else:
        return False


def get_exams_path():
    """
    Returns:
    The path to the 'exams' folder of the project, inside which the session files and the actual pdf exams are
    stored in
    """
    exams_path = "{}\\exams".format(exercise.PROJECT_PATH)
    return exams_path


# TODO: update doc string
class Exam:
    """
    The class that represents the Exam. The Exam consists of information about the subject and its subsubject, the
    maximum amount of achievable points and the date of creation.
    It essentially uses a ExerciseList to both organize and choose the exercises to be tho content of the exam.
    The actual content is being assembled as a string, whose content is entirely written as LaTeX, so that the string
    can be written into a TEX file, so that it can be presented to the user as a PDF file after the conversion process

    :ivar subject: (string) The subject, the exam is about
    :ivar subsubject: (string) the more specific subcatagory of the specified subject, the xam is about
    :ivar max_points: (int)  The maximum amount of points, that is achievable with this exam
    """
    def __init__(self, subject="", subsubject="", max_points=20, exercise_list=()):
        self.subject = subject
        self.subsubject = subsubject
        self.max_points = max_points
        # the amount of time the user took to complete the exam
        self.length = 0
        # the actual amount of points achieved
        self.points = 0
        # the exact moment it was created
        self.creation_date = datetime.datetime.today().timestamp()

        # loading the list of exercises
        if len(exercise_list) == 0:
            exercise_name_list = os.listdir("{0}\\subjects\\{1}\\{2}".format(exercise.PROJECT_PATH, subject,
                                                                             subsubject))
            # excluding the subject config file from the name list
            exercise_name_list.remove("config.ini")
            exercise_object_list = []
            for exercise_name in exercise_name_list:
                exercise_object_list.append(exercise.load_exercise(subject, subsubject, exercise_name))
            self.exercise_list = exercise.ExerciseList(exercise_object_list)

        else:
            if isinstance(exercise_list, exercise.ExerciseList):
                self.exercise_list = exercise_list
                self.max_points = self.calculate_max_points()
            else:
                raise TypeError("The passed list doesnt contain Exercise objects")

        # the content string, holding the actual exam as a latex string
        self.content = r""

    def _choose_content_exercises(self):
        """
        Originally the Exam object is created with an internal ExerciseList, which contains all Exercises available to
        the given subject specification. This function basically gets rid of one exercise at the time by calling the
        'eliminate_exercise' method of the ExerciseList (the method, implementing the random-statistical decision
        algorithm for choosing exercises) until the accumulated maximum amount of points of the whole list is below
        the points specified for the exam to have.
        Additionally this method sorts the ExerciseList, so that those Exercises with the least amount of points is
        first, by calling the 'sort_by_points' method of the ExerciseList
        :return: (void)
        """
        # eliminating random exercises from the list of possible exercises until the sum of their points is lower or
        # even with the specified amount of max allowed points of the exam
        while self.exercise_list.max_points > self.max_points:
            self.exercise_list.eliminate_exercise()

        # finally sorting the list of exercises beginning with those with the least and ending with the most points
        self.exercise_list.sort_by_points()

    def create_content(self):
        # generating the exercise list, from which the content will be created
        self._choose_content_exercises()
        self.max_points = self.calculate_max_points()

        # assembling the static header strings
        content_string_list = [LATEX_EXAM_HEADER,
                     LATEX_EXAM_TITLE.replace("%%subject%%", self.subject).replace("%%subsubject%%", self.subsubject)]

        # adding the strings of the exercises
        index = 1
        for exerc in self.exercise_list:
            exercise_string = LATEX_EXAM_EXERCISE_HEADER.replace("%%name%%", exerc.name)
            exercise_string = exercise_string.replace("%%max_points%%", str(exerc.max_points))
            exercise_string = exercise_string.replace("%%index%%", str(index))
            content_string_list.append(exercise_string)
            content_string_list.append(exerc.content)
            content_string_list.append(r"\\[4mm] ")
            index += 1

        content_string_list.append(r" \end{document} ")
        # converting the list of string into a single string
        self.content = ''.join(content_string_list)

    def solve_exercise(self, exercise_name, points):
        """
        solves the exercise with the specified name and passed amount of points and then saves the changes to the
        filesystem persistantly, by calling the save method of each exercise.
        :param exercise_name: (string) the name of the exercise to solve and save
        :param points: (int) the amount of points achieved
        :return: (void)
        """
        self.points += points
        exer = self.exercise_list[exercise_name]
        exer.solve(points)
        exer.save()

    def solve_length(self, time_seconds):
        """
        solves the amount of time the user took to complete the exam
        :param time_seconds: (int) the time in seconds
        :return: (void)
        """
        self.length = time_seconds

    def is_solved(self):
        """
        returns whether the exam is fully solved, meaning every single exercise being solved and the length of the exam
        being entered
        :return: (boolean) the status of the exam
        """
        # first checking for all exercises to be solved
        for exer in self.exercise_list:
            if not exer.is_solved():
                return False
        # second check is whether the length of the exam has been solved
        return self.length != 0

    def get_content(self):
        return self.content

    def calculate_max_points(self):
        """
        calculates the max points of the exam
        :return: (int) the max points
        """
        max_points = 0
        for exer in self.exercise_list:
            max_points += exer.max_points
        return max_points

    def get_exercise_paths_list(self):
        return self.exercise_list.get_paths_list()


class SubjectHistory(exercise.ExerciseHistory):

    def __init__(self):
        super(SubjectHistory, self).__init__()

    def add(self, datetime_timestamp, max_points, achieved_points, length_seconds):
        """
        adds a new entry to the sequence
        :param datetime_timestamp: (float) the timestamp value, representing the time, the exam was solved
        :param max_points: (int) the amount of points the exam had
        :param achieved_points: (int) the amount of points actually achieved
        :param length_seconds: (int) the amount of time it took the user to complete the exam
        :return: (void)
        """
        self.dict[datetime_timestamp] = [max_points, achieved_points, length_seconds]

    def get_config_compatible_dict(self):
        """
        returns a dictionary, that represents the the history object, but is compatible with the configparser module,
        as both keys and values are strings. The original three item list of the history object containing the items:
        max_points (m), points (p) and length (l) [m, p, l], will be converted into a single string, where the items
        are separated by a semicolon 'm;p;l'
        :return: (dict) the dictionary that can be used as part of the config parser, without further augmenting
        """
        config_dict = {}
        for key in self.keys():
            item_list = self.dict[key]
            item_string = "{};{};{}".format(item_list[0], item_list[1], item_list[2])
            config_dict[key] = item_string
        return config_dict

    def __getitem__(self, item):
        return self.dict[item]
