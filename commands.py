import PiLearner.learncoach as learncoach
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


def reset_progress(console, subject="", subsubject="", exercise=""):
    """
    resets the progress of the exercise or all exercises of the entire folder, specified by the parameters. Specifically
    will delete the history of the individual exercises and reset their statistical values. Without parameters the
    whole project progress will be destroyed, will ask a safety question before doing so though.
    :param console: -
    :param subject: (string) the name of the subject
    :param subsubject: (string) the name of the subsubject
    :param exercise: (string) the name of the exercise
    :return:
    """
    if subject == "" or subsubject == "":
        # asking for a security question, since it could be fatal deleting all progress by accident
        is_valid = False
        while not is_valid:
            answer = str(console.prompt_input("Security Question. Name of this project: (or stop)"))
            if answer.upper() == "PILEARNER":
                is_valid = True
            elif answer.upper() == "STOP":
                console.print_error(KeyboardInterrupt("progress reset stopped!"))
                return 0

    # assembling the path from which everything has to be reset
    path_string_list = [project_directory, "\\subjects"]
    if subject != "":
        path_string_list.extend(["\\", subject])
    if subsubject != "":
        path_string_list.extend(["\\", subsubject])
    if exercise != "":
        path_string_list.extend(["\\", exercise])
    path = ''.join(path_string_list)

    # walking down the tree of the path and modifying each config file. os.wal -> (root, folders, files)
    total_amount = 0
    for tuple in os.walk(path):
        if "config.ini" in tuple[2]:
            exercise_path = tuple[0]

            # loading config file
            config = configparser.ConfigParser()
            config_path = "{0}\\config.ini".format(exercise_path)
            config.read(config_path)

            # resetting the statistical info
            for statistic_info in dict(config["STATISTIC"]).keys():
                config["STATISTIC"][statistic_info] = str(0)

            # deleting the history
            config["HISTORY"] = {}

            # saving the changed config
            with open(config_path, mode="w") as file:
                config.write(file)

            console.print_info("resetting exercise '{}'".format(os.path.basename(exercise_path)))
            total_amount += 1

    console.print_result("Successfully cleared {} exercises in '{}'".format(total_amount, path))
    return total_amount


def create_exam(console, subject, subsubject, max_points, dest_path=""):
    console.print_info("Attempting to generate an exam about '{0} - {1}'".format(subject, subsubject))
    # creating the exam with the given parameters
    try:
        exam.create_exam(subject, subsubject, max_points)
    except Exception as e:
        raise e
        console.print_error(e)
    # theoretically the creation process is finished. Only cleaning up the left overs now
    console.print_info("Finished creation process")
    time.sleep(0.01)
    return True


def create_schedule(console, subject, subsubject, exam_count):
    """
    creates a schedule and learning process object for the given subject, with the given amount of total exams
    :param console: -
    :param subject: (string) the subject to schedule
    :param subsubject: (string) the subsubject to schedule
    :param exam_count: (int) the total amount of exams to solve during the whole process
    :return: (void)
    """
    console.print_info("Creating schedule for '{} - {}'".format(subject, subsubject))
    # creating the learning process object and calling the schedule creation method
    learning_process = learncoach.LearningProcess(subject, subsubject)
    learning_process.create_schedule(exam_count=exam_count)
    console.print_info("schedule created")
    # now saving the learning process object as file
    learncoach.save_learning_process(learning_process)
    console.print_result("learning schedule '{} - {}' saved")


def active_schedules(console):
    """
    shows all active learning processes
    :param console: -
    :return: (void)
    """
    name_list = learncoach.names_all_learning_processes(with_path=False)
    name_list =list(map(lambda x: x.replace("_", " - ").replace(".pkl", "") + "\n", name_list))
    console.print_info(''.join(["Active learning processes:\n\n"] + name_list))


def show_schedule(console, subject, subsubject):
    """
    displays the schedule of the specified subject
    :param console: -
    :param subject: (string) the subject
    :param subsubject: (string) the sub subject
    :return: (string) the string representation of the schedule
    """
    # loading the learning process object, that contains the schedule
    learning_process = learncoach.load_learning_process(subject, subsubject)
    # printing the schedules string rep
    schedule_string = learning_process.get_schedule_string()
    console.print_info("The schedule of '{} - {}':\n\n{}".format(subject, subsubject, schedule_string))
    return schedule_string


def show_progress(console, subject, subsubject):
    """
    displays the schedule of the specified subject
    :param console: -
    :param subject: (string) the subject
    :param subsubject: (string) the sub subject
    :return: (string) the string representation of the schedule
    """
    # loading the learning process object, that contains the schedule
    learning_process = learncoach.load_learning_process(subject, subsubject)
    # printing the schedules string rep
    progress_string = learning_process.get_progress_string()
    console.print_info("The schedule of '{} - {}':\n\n{}".format(subject, subsubject, progress_string))
    return progress_string


def solve_exam(console, subject, subsubject):
    """
    solves the exam specified by the parameters
    :param console: -
    :param subject: (string) the subject
    :param subsubject: (string) the subsubject
    :return: (int) the amount of achieved points
    """
    console.print_info("Attempting to solve the open session for '{0} - {1}'".format(subject, subsubject))
    session_file_path = "{0}\\exams\\{1} - {2}.session".format(exercise.PROJECT_PATH, subject, subsubject)
    # creating the path, that leads to the session file of the according subject, no matter it existing or not
    session_path = exam.get_session_path(subject, subsubject)

    # checking whether there actually exists an open session for the specified subject
    if exam.session_exists(subject, subsubject):
        console.print_info("Session for '{}' exists".format(session_path))
        # reading the session file, getting a list of the names of all used exercises
        exercise_name_list = exam.get_session_content(subject, subsubject)
        # creating a exam object from the session file
        session_exam = exam.exam_from_session(subject, subsubject)
        # itering through the list of exercise names
        for exercise_name in exercise_name_list:
            exercise_obj = session_exam.exercise_list[exercise_name]
            # prompting the user to enter the amount of reached points
            points = ""
            while not isinstance(points, int):
                try:
                    points = int(console.prompt_input(
                        "The exercise '{0}' has {1} max points. How many did you achieve?".format(exercise_name,
                                                                                                  exercise_obj.max_points)))
                except ValueError:
                    console.print_info("That is no valid integer! Try again...")
            # solving and saving the exercise
            session_exam.solve_exercise(exercise_name, points)
            console.print_info("solved with {} points".format(points))
        console.print_info("Deleting the session file")
        os.remove(session_file_path)
        minutes = ""
        while not isinstance(minutes, int):
            try:
                minutes = int(console.prompt_input("How long did the exam take you? (in minutes)"))
            except ValueError:
                console.print_info("That is no valid integer! Try again...")
        # solving the required length of the exam at last. Multiplying by 60 as seconds are required
        session_exam.solve_length(minutes * 60)
        # saving the exam as another entry in its subject history
        exam.save_history_solved_exam(session_exam)
        # updating the progress of an eventual learning process
        try:
            learncoach.load_learning_process(subject, subsubject).update_progress()
            console.print_result("learning process updated!")
        except Exception as e:
            console.print_error(e)
        console.print_result("The pending exam '{0} - {1}' has been solved!".format(subject, subsubject))
    else:
        raise FileNotFoundError("There exists no open session for the given subjects!")
