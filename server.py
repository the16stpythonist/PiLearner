from piver import get_project_path

from piver import PiverRequestHandler
from piver import BaseUserProfile
from piver import UserDict

import pickle
import os

PROJECT_PATH = get_project_path()


def load_password(username):
    """
    Loads the password of the user, that is specified by the passed username. The password is being stored inside
    a plain text file within the users profile folder
    Args:
        username: The username of the user of which the password should be returned

    Returns:
    The string password, belonging to the specified username
    """
    # Creating the path to the username's profile folder. Every user is assigned a folder within the servers side
    # filesystem of the project. The actual profile folders are within the sub folder 'profiles' though
    user_path = get_user_path(username)
    password_file_path = "{}\\password.txt".format(user_path)
    with open(password_file_path, "r") as file:
        password = file.read()

    return password


def load_learning_process_list(username):
    """
    Loads the list of learning progress objects of the specified username. The progress of a user is being stored as
    pickled byte sequences within the servers filesystem, they are specifically located within the 'progress' folder
    of an individual user, specified by the username
    Args:
        username: The username of which the progress is to be loaded

    Returns:
    A list containing the 'LearningProcess' objects, that describe the schedule and the progress of
    """
    # Creating the path to the username's profile folder. Every user is assigned a folder within the servers side
    # filesystem of the project. The actual profile folders are within the sub folder 'profiles' though
    user_path = get_user_path(username)

    # Creating the path to the folder of the user profile, in which the progress files are being stored
    progress_folder_path = "{}\\process".format(user_path)

    progress_list = []
    progress_file_names = os.listdir(progress_folder_path)
    for progress_file_name in progress_file_names:
        # Creating the file path to the actual progress file and then oping up the file to read its content and
        # unpickle it
        progress_file_path = "{}\\{}".format(progress_folder_path, progress_file_name)
        with open(progress_file_path, "rb")as progress_file:
            content = progress_file.readall()
        progress_object = pickle.loads(content)
        progress_list.append(progress_object)
    return progress_list


def load_user_profile(username):
    """
    loads the data of a users profile, specified by his username, from the filesystem of the server and creates  and
    returns a 'PiLearnUserProfile' object from the data.
    After the runtime of the server program profiles of the individual users are stored as separate folders within the
    'profiles' folder of the main server directory, the user profile folders being named by the usernames.
    The profile folders contain a 'password.txt' that stores the users password as palin text and another folder, called
    'process', which itself contains several different files with the pickled 'LearningProcess' objects of the
    different subjects
    Args:
        username: The username of the user, whose profile is to be loaded

    Returns:
    The 'PiLearnUserProfile' of the user, specified by the username, that was created by the data stored within the
    filesystem of the project
    """
    # Creating the path to the username's profile folder. Every user is assigned a folder within the servers side
    # filesystem of the project. The actual profile folders are within the sub folder 'profiles' though
    user_path = get_user_path(username)

    # Getting the password, that is required for the construction of a user profile object
    password = load_password(username)

    # Getting the list of learning process objects for the user
    learning_processes = load_learning_process_list(username)

    # Constructing the actual user profile object
    user_profile = PiLearnUserProfile(username, password, learning_processes)
    return user_profile


def get_user_path(username):
    """
    Args:
        username: The username to the users profile path, that is requested

    Returns:
    The path to the folder, that contains all the servers stored data about an individual user, specified by the
    username
    """
    # Creating the path to the username's profile folder. Every user is assigned a folder within the servers side
    # filesystem of the project. The actual profile folders are within the sub folder 'profiles' though
    user_path = "{}\\profiles\\{}".format(PROJECT_PATH, username)
    return user_path


def get_username_list():
    """
    Returns:
    A list containing all the strings of all usernames, that are currently registered in the server
    """
    # Creating the path of the profiles folder, in which the folders for the individual user profiles are being stored.
    # Since all the folders within the 'profiles' folder belong to a user and are named by the username they belong
    # to, creating a list with all the folder names within the 'profiles' folder
    profiles_path = "{}\\profiles".format(PROJECT_PATH)
    profiles_folder_contents = os.listdir(profiles_path)
    username_list = []
    for item in profiles_folder_contents:
        item_path = os.path.join(profiles_path, item)
        if os.path.isdir(item_path):
            username_list.append(item)
    return username_list


class PiLearnUserProfile(BaseUserProfile):

    def __init__(self, username, password, learning_processes):
        BaseUserProfile.__init__(self, username, password)
        self.learning_processes = learning_processes

    def save(self):
        """
        Saves all the runtime data back into the filesystem
        Returns:
        void
        """
        # Saving the password of the user
        self.save_password()
        # Saving the learning process files of the user as pickled objects into text files
        self.save_learning_processes()

    def save_learning_processes(self):
        """
        Saves the learning processes back into the filesystem as pickled byte sequences within the 'process' folder
        within the profile folder of the user
        Returns:
        void
        """
        # Getting the path to the 'process' folder in the users profile folder
        user_path = get_user_path(self.username)
        process_path = "{}\\process".format(user_path)

        for learning_process in self.learning_processes:
            learning_process._save(process_path)

    def save_password(self):
        """
        Saves the password of the user as plain text into the 'password.txt' of the users profile folder
        Returns:
        void
        """
        user_path = get_user_path(self.username)
        password_file_path = "{}\\password.txt".format(user_path)
        with open(password_file_path, "w+") as file:
            file.write(self.password)

    def get_learning_process(self, subject, subsubject):
        """
        Searches the internal list of active learning process object for the user to find a learning process, that
        matches the specified subject and subsubject. Returns the learning process object if found. In case there is no
        matching learning process raises an excpetion.

        Raises:
            KeyError: In case there is no learning process object for the given subject and subsubject

        Args:
            subject: The subject of the requested learning process
            subsubject: The subsubject of the requested learning process

        Returns:
        The learning process for the specified subject and subsubject
        """
        # Iterating through the list of learning processes and returning the learning process, that matches both the
        # given subject and the subsubject.
        # In case no learning process with the given specifications exists for the user raises a KeError exception
        for learning_process in self.learning_processes:
            learning_process_subject = learning_process.subject
            learning_process_subsubject = learning_process.subsubject
            if learning_process_subject == subject and learning_process_subsubject == subsubject:
                return learning_process

        error_string = "user {}, does not have learning process for {} - {}".format(self.username, subject, subsubject)
        raise KeyError(error_string)

    def set_learning_process(self, learning_process):
        """
        If there already exists a learning process with the same subject and subsubject as the given 'learning_process',
        the old list item will be replaced by the new one.
        In case there is no though, the new one will simply be appended to the list of learning processes of the user
        Args:
            learning_process: The new 'LearningProcess' object

        Returns:
        void
        """
        # If there already is a learning process object with the same subject and subsubject of the new object, the new
        # one cant just be added, as there would be two objects describing the same matter. So first the replace
        # method is called, it will return whether a replacement happened or not. In case there was no replacement,
        # the new object is simply added to the list
        was_replaced = self._replace_learning_process(learning_process)
        if not was_replaced:
            self.learning_processes.append(learning_process)

    def _replace_learning_process(self, new_learning_process):
        """
        Attempts to replace the current learning process object of the user, that is specified by the subject
        and subsubject of the new learning process object. The method returns whether there was an actual
        replacement of a currently existing list item or not.
        In case there was no replacement, the method wont do anything else
        Args:
            new_learning_process: The new 'LearningProcess' object

        Returns:
        The boolean value of whether or not a list item was actually replaced or not
        """
        subject = new_learning_process.subject
        subsubject = new_learning_process.subsubject
        # Iterates through the list of the learning process objects, by index, so that the list item can be changed.
        # The method will then return, if the replacement happened or not
        for index in range(len(self.learning_processes)):
            learning_process = self.learning_processes[index]
            # Getting the subject and the subsubject of the current learning process to compare with the values,
            # passed as parameters
            learning_process_subject = learning_process.subject
            learning_process_subsubject = learning_process.subsubject
            if learning_process_subject == subject and learning_process_subsubject == subsubject:
                # Replacing the learning process item within the list at the current index with the new object
                self.learning_processes[index] = new_learning_process
                return True
        return False


class PiLearnUserDict(UserDict):

    def __init__(self):
        UserDict.__init__(self)

    def load_profiles(self):
        """
        loads the UserProfile objects from the filesystem and uses the usernames as the keys to the profile objects as
        values of the dictionary
        Returns:
        void
        """
        # Loading the list with all currently registered username and loading the user profile for every one of them.
        # The usernames are the keys to access the actual profile objects of this dictionary
        username_list = get_username_list()

        for username in username_list:
            user_profile = load_user_profile(username)
            self[username] = user_profile

    def save_profiles(self):
        """
        Saves all the profiles
        Returns:
        void
        """
        for username in self.keys():
            self.save_profile(username)

    def save_profile(self, username):
        """
        Saves the profile of the user with the passed username
        Args:
            username: The username for the profile to save

        Returns:
        void
        """
        self[username].save()


class PiLearnRequestHandler(PiverRequestHandler):

    def __init__(self, request, client_address, server):
        PiverRequestHandler.__init__(self, request, client_address, server)

    def set_learning_process(self, received_object, learning_process):
        """
        If there already exists a learning process with the same subject and subsubject as the given 'learning_process',
        the old list item will be replaced by the new one.
        In case there is no though, the new one will simply be appended to the list of learning processes of the user
        Args:
            received_object:
            learning_process: The new 'LearningProcess' object

        Returns:
        True
        """
        # Getting the username of the user, that sent the request
        user_profile = self.get_user_profile(received_object)

        user_profile.set_learning_process(learning_process)
        return True

    def get_learning_process(self, received_object, subject, subsubject):
        """
        Gets the learning process object for the given subject and subsubject from the requesting users
        Args:
            received_object:

        Returns:
        The requested 'LearningProcess' object or a KeyError if there is no object with the specified subject and
        subsubject
        """
        # Getting the username of the user, that sent the request
        user_profile = self.get_user_profile(received_object)

        learning_process = user_profile.get_learning_process(subject, subsubject)
        return learning_process
