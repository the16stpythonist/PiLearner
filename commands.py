import PiLearner.exercise as exercise
import PiLearner.exam as exam
import configparser
import inspect
import shutil
import time
import os

config_parser = configparser.ConfigParser()
config_parser.read("config.ini")
project_directory = config_parser["Paths"]["project_dir"]


def echo(console, string):
    console.print_info(string)
    return console.prompt_input("now")


def create_exam(console, subject, subsubject, max_points, dest_path=""):
    console.print_info("Attempting to generate an exam about '{0} - {1}'".format(subject, subsubject))
    # creating the exam with the given parameters
    try:
        exam.create_exam(subject, subsubject, max_points)
    except Exception as e:
        console.print_error(e)
    # theoretically the creation process is finished. Only cleaning up the left overs now
    console.print_info("Finished creation process")
    time.sleep(0.01)

    # printing the path of the file
    if os.path.exists("{0}\\{1}.pdf".format(exercise.PROJECT_PATH, subject)):
        console.print_result("Exam succesfully generated in folder '{0}'".format(project_directory))

    # removing the files, that were also created by the latex converter, but are useless for the user
    os.remove("{0}\\{1}.aux".format(project_directory, subject))
    os.remove("{0}\\{1}.log".format(project_directory, subject))

    full_subject_name = ''.join([subject, " - ", subsubject])
    # moving the file into the exams folder
    new_path = "{0}\\exams\\{1}.pdf".format(exercise.PROJECT_PATH, full_subject_name)
    shutil.move("{0}\\{1}.pdf".format(project_directory, subject),
                new_path)
    if os.path.exists(new_path):
        console.print_result("Exam successfully moved to folder '{0}\\exams\\{1}.pdf'".format(exercise.PROJECT_PATH,
                                                                                            full_subject_name))

    # copying the exam file into the folder, that was additionally specified by the dest_path variable
    if dest_path != "":
        destination_path = dest_path + "\\{}.pdf".format(full_subject_name)
        shutil.copy(new_path, destination_path)
        console.print_result("Exam successfully copied to folder '{0}'".format(destination_path))
    return True


def main(console, subject, subsubject):
    """

    :param console:
    :param subject:
    :param subsubject:
    :return: (int) the amount of achieved points
    """
    console.print_info("Attempting to solve the open session for '{0} - {1}'".format(subject, subsubject))
    session_file_path = "{0}\\exams\\{1} - {2}.session".format(exercise.PROJECT_PATH, subject, subsubject)

    # checking whether there actually exists an open session for the given subject
    if os.path.exists(session_file_path):
        console.print_info("The open session file '{0}' was found!".format(session_file_path))
        # reading the contents of the session file
        with open(session_file_path, mode="r") as file:
            session_file_content = file.read()
        # splitting it into the list of names of used exercises
        exercise_name_list = session_file_content.split("\n")
        # removing empty lines
        while "" in exercise_name_list:
            exercise_name_list.remove("")
        # laoding each exercise object into memeory and calling the solve method to add a new solved point to the set
        for exercise_name in exercise_name_list:
            exercise_obj = exercise.load_exercise(subject, subsubject, exercise_name)
            points = ""
            # prompting for user input
            while not isinstance(points, int):
                try:
                    points = int(console.prompt_input("The exercise '{0}' has {1} max points. How many did you achieve?".format(exercise_name, exercise_obj.max_points)))
                except:
                    console.print_info("That is no valid integer! Try again...")
            exercise_obj.solve(points)
            console.print_info("The exercise has been solved with {0} points and now it has {1} points on average on a total of {2} uses".format(points, exercise_obj.average_points, exercise_obj.use_frequency))
            exercise_obj.save()
        console.print_info("Deleting the session file")
        os.remove(session_file_path)
        console.print_result("The pending exam '{0} - {1}' has been solved!".format(subject, subsubject))
    else:
        console.print_error(FileNotFoundError("There exists no open session for the given subjects!"))