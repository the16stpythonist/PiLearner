__author__ = "Jonas Teufel"
__version__ = "0.0.0"

import PiLearner.exercise as exercise
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
    def __init__(self, subject, subsubject, max_points=20):
        self.subject = subject
        self.subsubject = subsubject
        self.max_points = max_points
        self.creation_date = time.time()

        # loading the list of exercises
        exercise_name_list = os.listdir("{0}\\subjects\\{1}\\{2}".format(exercise.PROJECT_PATH, subject, subsubject))
        exercise_object_list = []
        for exercise_name in exercise_name_list:
            exercise_object_list.append(exercise.load_exercise(subject, subsubject, exercise_name))
        self.exercise_list = exercise.ExerciseList(exercise_object_list)

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

    def get_content(self):
        return self.content

    def get_exercise_paths_list(self):
        return self.exercise_list.get_paths_list()
