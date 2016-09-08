from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.codeinput import CodeInput
from kivy.properties import StringProperty
from kivy.properties import ListProperty
from kivy.properties import BooleanProperty
from kivy.uix.button import Button
from kivy.graphics import Color

from pygments.lexers.markup import TexLexer
from pygments.style import Style
from pygments.formatters.html import HtmlFormatter
import pygments.token as pygtoken

import exercise
import exam
import os


class OrangeStyle(Style):
    default_style = ""
    styles = {
        pygtoken.Comment: "#8F8F8F",
        pygtoken.Keyword: "#FF9500",
        pygtoken.Number: "#3B9696",
        pygtoken.String: "#21D191",
        pygtoken.Name:  "#DEDEDE",
        pygtoken.Name.Variable: "#DEDEDE",
        pygtoken.Name.Function: "#DEDEDE",
        pygtoken.Name.Class: "#DEDEDE",
        pygtoken.Operator: "#FF9500",
        pygtoken.Text: "#DEDEDE",
        pygtoken.Generic: "#DEDEDE",
        pygtoken.Punctuation: "#DEDEDE",
        pygtoken.Escape: "#DEDEDE"
    }

COLOR_DICT = {
    "white": "DEDEDE",
    "light gray": "CCCCCC",
    "gray": "616161",
    "red": "D61818",
    "light red": "D49390",
    "green": "3AD126",
    "light green": "ACD49F",
    "blue": "397AD4",
    "magenta": "D439B7"
}


def color_markup(color_string, string):
    """
    Returns the given string inside the kivy markup tags for coloring it according to the color code passed as string
    Args:
        color_string: The string of the Hexadecimal value representing the color to mark the text in
        string: The actual content, that is to be colored/marked
    Returns:
        The passed 'string' within kivy markup tags for the color represented by the color code 'color_string'
    """
    markup_string = "[color={}]{}[/color]".format(color_string, string)
    return markup_string


class LabeledTextInput(TextInput):
    """
    This class implements all features of the parent class TextInput. (info: kwargs are not enabled)
    Instead of needing a descriptive Label on top or in front of this input widget, to show the user what kind of input
    is expected, this descriptive string will be the content of the input widget from the beginning on.
    This label string will disappear as soon as the input line is focused and reappear, when it is empty again.
    """
    label_text = StringProperty("")

    def __init__(self, label_text=""):
        super(LabeledTextInput, self).__init__()
        # The label_text is the string, that is supposed to be displayed, when the widget is inactive. So instead of
        # using a label in front of the input widget to clearify what kind of input is supposed to be entered, the
        # description of that will be the text content of the input widget itself.
        self.label_text = label_text
        self.text = self.label_text

    def _on_focus(self, instance, value, *largs):
        """
        Callback method for the focus Event.
        Implements the behaviour, that the descriptive text within the widget disappears as soon as the widget is
        focused and reappears as soon as the widget is unfocused and empty
        """
        super(LabeledTextInput, self)._on_focus(instance, value, largs)
        if self.text == self.label_text:
            self.text = ""

        elif self.text == "":
            self.text = self.label_text
            # Resetting the background color to the standard white, because there may be some applications of this class
            # where the background is being changed, but when the descriptive info text is being displayed one would
            # want the neutral white color anyways
            self.background_color = (1, 1, 1, 1)

    def on_label_text(self, *args):
        """
        simply updates the text property of the widget in case the label_text property is changed or set after the
        constructor.
        Returns:
            Void
        """
        if self.text == "":
            self.text = self.label_text


class LatexCodeInput(CodeInput):

    def __init__(self):
        super(LatexCodeInput, self).__init__()
        self.lexer = TexLexer()
        self.style = HtmlFormatter(style="friendly").style


class ExerciseCreation(GridLayout):

    list_exercise_objects = ListProperty([])

    name_valid = BooleanProperty(False)
    points_valid = BooleanProperty(False)
    content_valid = BooleanProperty(False)

    def __init__(self, subject, subsubject):
        super(ExerciseCreation, self).__init__()

        self.subject = subject
        self.subsubject = subsubject
        # This method will load all the exercises of the specified subject into the list property of this widget.
        # The method is void and will not return anything
        self.load_exercise_list()

        # The final widget will have four layers of individual widgets stacked on top of each other (rows)
        self.cols = 1
        self.rows = 4
        self.padding = 5
        self.spacing = 5

        # The description label will contain the information, for which subject the exercise will be created. This
        # information will be bold, which means the text markup has to be activated for the Label.
        description = "Exercise in '[b]{} - {}[/b]'".format(self.subject, self.subsubject)
        self.label_description = Label()
        self.label_description.markup = True
        self.label_description.text = description
        self.label_description.size_hint_y = None
        self.label_description.height = 25
        self.add_widget(self.label_description)

        # Just a little below the description label should be two text input widgets, with which the name of the
        # exercise and the max amount of achievable points can be entered.
        # Since those widgets are supposed to go next to each other, they will be added to a separate GridLayout first
        # and this GridLayout will then be added to this widget itself
        self.gridlayout_text_inputs = GridLayout()
        self.gridlayout_text_inputs.cols = 2
        self.gridlayout_text_inputs.rows = 1
        self.gridlayout_text_inputs.spacing = 10
        self.gridlayout_text_inputs.size_hint_y = None
        self.gridlayout_text_inputs.height = 30

        # The LabeledTextInput widgets dont need a descriptive label in front of them, as they contain the description
        # string of what should be entered as default text content themselves.
        # To add such a description, the 'label_text' property of the widget has to be set to the wanted string.
        self.text_input_name = LabeledTextInput()
        self.text_input_name.label_text = "exercise name"
        # important: The binding of this callback method has to be AFTER the text changed, if not it will result in
        # a bug, that displays the wrong background color in the beginning (only in the beginning though)
        self.text_input_name.bind(text=self.on_text_input_name)
        self.text_input_name.multiline = False
        self.text_input_name.size_hint_x = 0.8

        self.text_input_points = LabeledTextInput()
        self.text_input_points.label_text = "max points"
        self.text_input_points.bind(text=self.on_text_input_points)
        self.text_input_points.multiline = False
        self.text_input_points.size_hint_x = 0.2

        self.gridlayout_text_inputs.add_widget(self.text_input_name)
        self.gridlayout_text_inputs.add_widget(self.text_input_points)

        # Adding the GridLayout to the top widget
        self.add_widget(self.gridlayout_text_inputs)

        # The next widget is the actual TextInput, designed for entering the LaTeX code of the actual function.
        self.text_input_latex = LatexCodeInput()
        self.text_input_latex.multiline = True
        self.text_input_latex.size_hint_y = 0.7

        self.add_widget(self.text_input_latex)

        # The last row of the main widget GridLayout will contain the submit button, that has to be pressed to save the
        # the exercise object persistently into the file system, and the a info label, that prints, if and what is wrong
        # with the input specifics of the widget.
        # Since the two widgets are supposed to go next to each other they will first be stored in a separate GridLayout
        # that will be added to the main widget.
        self.grid_layout_submit = GridLayout()
        self.grid_layout_submit.cols = 2
        self.grid_layout_submit.rows = 1
        self.grid_layout_submit.spacing = 5
        self.grid_layout_submit.size_hint_y = None
        self.grid_layout_submit.height = 35

        # The button widget, that has to be pressed to save the exercise
        self.button_submit = Button()
        self.button_submit.text = "submit"
        self.button_submit.bind(on_press=self.on_submit)
        self.button_submit.size_hint_x = None
        self.width = 100
        self.grid_layout_submit.add_widget(self.button_submit)

        # The Label widget, that displays the status of the input infromation
        self.label_info = Label()
        self.label_info.markup = True
        self.label_info.text = "No input has been entered yet"
        self.grid_layout_submit.add_widget(self.label_info)

        self.add_widget(self.grid_layout_submit)

    def load_exercise_list(self):
        """
        A instance of this widget contains a list, that is supposed to contain the Exercise objects of all exercises,
        that belong to the subject, that was specified for the widget.
        This method does not return anything, it simply loads all those Exercise objects from the file system as
        objects into this list attribute of the widget.
        :return:
        """
        # clearing the list of exercise objects first, just in case the load method is being called to update aside
        # from the construction
        self.list_exercise_objects.clear()

        # Assembling the path to the directory of the subject to which the exercise is to be added
        subject_path = self.get_subject_path()

        # looping through the names of the folders in the subject folder. Those folders resemble one exercise each, with
        # the folder name also being the name of the exercise itself. To load the exercises, the program will loop
        # through the list of those names and use the execise modules functions to create Exercise objects according
        # to the data, saved within the respective folders
        subject_folder_content = os.listdir(subject_path)
        for name in subject_folder_content:
            if name != "config.ini":
                exercise_object = exercise.load_exercise(self.subject, self.subsubject, name)
                self.list_exercise_objects.append(exercise_object)

    def get_subject_path(self):
        """
        returns the path to the subjects folder of the project
        Returns:
            The string path to the subjects folder of the string path
        """
        # Assembling the path to the directory of the subject to which the exercise is to be added
        project_path = exercise.PROJECT_PATH
        subject_path = "{}\\subjects\\{}\\{}".format(project_path, self.subject, self.subsubject)

        return subject_path

    def on_text_input_name(self, *args):
        """
        The callback method for the observer events on the text property of the input widget for the name of the
        exercise. This method will constantly check the entered string and indicate whether it is valid, by marking the
        input widget background light green, or invalid, by marking the input widget background light red.
        The widget is invalid, if the name that was entered belongs to an already existing exercise of the subject.
        Args:
            args: standard
        Returns:
            void
        """
        # Checking the text property of the input widget for the name of the exercise. The input is not acceptable
        # when the name and thus the exercise itself already exists.
        # In case the exercise does ideed already exist and the input is invalid, this method does not only turn the
        # boolean property for the validation false, but also turns the background of the input widget red and prints
        # an error to the info label.
        # In case it is valid though the background of the widget is marked with a light green.
        name = self.text_input_name.text
        if self.exercise_already_exists(name):
            self.text_input_name.background_color = (1, 0.7, 0.7, 1)
            self.print_error_info("There already exists a command with the entered name!")
            self.name_valid = False
        else:
            self.text_input_name.background_color = (0.7, 1, 0.7, 1)
            self.clear_info_label()
            self.name_valid = True

    def on_text_input_points(self, *args):
        """
        The callback method for the observer event on the text property of the input widget for the max amount of
        points. This method will check the entered string and indicate whether it is valid, by marking the
        input widget background light green, or invalid, by marking the input widget background light red.
        The input is valid in case it is a number/integer
        Args:
            args: standard
        Returns:
            void
        """
        # Checking the text property of the input widget for the maximum amount of points, which has to be an integer.
        # In case input is an integer and the input is invalid, this method does not only turn the
        # boolean property for the validation false, but also turns the background of the input widget red and prints
        # an error to the info label.
        # In case it is valid though the background of the widget is marked with a light green.
        points = self.text_input_points.text
        try:
            points = int(points)
            self.text_input_points.background_color = (0.7, 1, 0.7, 1)
            self.clear_info_label()
            self.points_valid = True
        except ValueError:
            self.text_input_points.background_color = (1, 0.7, 0.7, 1)
            self.print_error_info("Enter a valid integer for the amount of points!")
            self.points_valid = False

    def on_submit(self, *args):
        """
        The callback method for when the submit button of the widget is being pressed. The method will check whether the
        strings entered into the input widgets are valid parameters for exercise creation, that would include the
        exercise name not already existing, the max amount of points actually being an integer and the content input
        not being empty. In case all conditions are met the 'save_exercise' method is called and a new exercise folder
        will be created.
        :return:
        """
        # Checks whether the name and the pints are valid using their corresponding boolean attributes and also checks
        # the content briefly in the sense, that it just should not be empty.
        # In case these conditions are met initiates the saving process of the Exercise into the file system.
        if self.points_valid and self.name_valid and self.text_input_latex.text != "":
            self.save_exercise()

    def save_exercise(self):
        """
        This method calls the function that actaully creates a new exercise folder within the filesystem of the project
        with the parameters, from the designated input widgets. The method itself does not implements validity checks
        of some sort and thus should only be called in case the entered parameters are valid.
        Returns:
            void
        """
        name = self.text_input_name.text
        points = int(self.text_input_points.text)
        content = self.text_input_latex.text

        # Calling the function, that actually creates a new exercise folder within the filesystem of the project
        exercise.create_exercise(self.subject, self.subsubject, name, points, content, "none")

        # Adding the newly created exercise object to the list of already existing objects, so that the exercise can
        # not be overwritten. (Little Hackery: Calling the callback for the input widget afterwards to update the
        # highlighting color)
        created_exercise = exercise.load_exercise(self.subject, self.subsubject, name)
        self.list_exercise_objects.append(created_exercise)

        self.on_text_input_name()

    def print_error_info(self, string):
        """
        Prints the passed string as a error message to the user, informing him about which part of the done input was
        wrong. Printing, in this case, means putting the string with red markup color as the text of the info label
        in the bottom right corner of the widget
        Args:
            string: The string that is supposed to be printed as the info message
        Returns:
            void
        """
        # Creating the string with color markup red, to symbolize the error aspect
        light_red_color_code = COLOR_DICT["red"]
        info_string = color_markup(light_red_color_code, string)

        # Using the just created string as the text property of the info label
        self.label_info.text = info_string

    def clear_info_label(self):
        """
        Simply resets the contents of the info label.
        :return:
        """
        self.label_info.text = "Please enter the contents of the exercise"

    def exercise_already_exists(self, exercise_name):
        """
        Checks whether the string passed as 'exercise_name' is the name belonging to an already existing exercise
        object if the subject.
        Args:
            exercise_name: The string name of the exercise in question
        Returns:
            The boolean value of whether or not the exercise already exists
        """
        for exercise_object in self.list_exercise_objects:
            if exercise_name == exercise_object.name:
                return True
        return False




