from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
from kivy.uix.codeinput import CodeInput
from kivy.uix.treeview import TreeView
from kivy.uix.treeview import TreeViewLabel
from kivy.uix.treeview import TreeViewNode
from kivy.uix.scrollview import ScrollView
from kivy.properties import StringProperty
from kivy.properties import ListProperty
from kivy.properties import BooleanProperty
from kivy.properties import NumericProperty
from kivy.properties import ObjectProperty
from kivy.uix.button import Button

from kivy.clock import Clock

from kivy.uix.screenmanager import ScreenManager
from kivy.uix.screenmanager import Screen
from kivy.graphics import Color
from kivy.graphics import Rectangle

from pygments.lexers.markup import TexLexer
from pygments.style import Style
from pygments.formatters.html import HtmlFormatter
import pygments.token as pygtoken

import datetime
import exercise
import time
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

PILEARN_COLOR_CODE = "7A9E6D"
PILEARN_COLOR_LIST = [0.458, 0.6, 0.407, 1]

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


class LabeledValidityTextInput(LabeledTextInput):
    """
    An abstract base class of a text input for numeric values only. The class is based on the LabelTextInput and thus
    offers the basic functionality, that the expected type of input can be displayed to the used as a string within
    the input widget, that will disappear as soon as the widget is focused and reappear, when the the widget is being
    unfocused again.
    This is an abstract base class in a way, that it does not directly implement a functionality of checking the type
    of the entered input for being numeric, but it implements the property boolean 'is_valid_input' and the
    changing of the background color of the widget according to the state of this property (light red in case the
    property is false/input invalid and light green if the property is True/valid input).

    Notes:
        - A class inheriting from this abstract base class does not have to implement the changing of the background
        color, but only has to change the boolean state of the 'is_valid_input' property, which will trigger the
        callback, that actually changes the color

    Attributes:
        color_list_invalid: This list contains the information for a red background color, that is 30% transparent and
            should be used as the the background for the text input, when an invalid input is being entered
        color_list_valid: This list contains the information for a green background color, that is 30% transparent and
            should be used as the background color for the text input, when the entered input of a text input widget
            is valid
        is_valid_input: The boolean value of whether or not the currently entered input is valid or not
    """
    # When setting for example the background color for a widget in kivy the color property will be set by a list,
    # consisting 4 of float values, from 0 to 1, the first value being the intensity of red in the expected color, the
    # second value the intensity of green, the third value the intensity of blue (RGB format) and the fourth value
    # being the alpha channel of the color, which is basically the opacity, which the color is supposed to have.

    # This list contains the information for a red background color, that is 30% transparent and should be used as the
    # the background for the text input, when an invalid input is being entered
    color_list_invalid = ListProperty([1, 0.7, 0.7, 1])
    # This list contains the information for a green background color, that is 30% transparent and should be used as
    # the background color for the text input, when the entered input of a text input widget is valid
    color_list_valid = ListProperty([0.7, 1, 0.7, 1])
    # Indicates whether the currently entered input in the text input widget is valid (,meaning whether it is numeric
    # or not)
    is_valid_input = BooleanProperty(False)

    def __init__(self, label_text="numeric"):
        LabeledTextInput.__init__(self, label_text)

    def on_is_valid_input(self, *args):
        """
        The callback method for the observer event in case the state of the boolean property that indicates the
        validity of the entered input of the text input widget changes.
        Upon a change in the boolean state of the property occurred, the method will check which state the property
        is currently in. In case the property is False, indicating an invalid input within the widget, the background
        of the widget will be changed to a light red, in case the property is True, indicating a valid input in the
        widget, the background of the widget will be changed to a light green
        Args:
            *args: -

        Returns:
        void
        """
        # Upon a change of the valid input boolean property, checking into which state it actually changed and then
        # changing the background color to a slight red in case the input is invalid and a slight green, in case the
        # background color is valid
        if self.is_valid_input:
            self.background_color = self.color_list_valid
        else:
            self.background_color = self.color_list_invalid

    def is_valid(self):
        """
        Returns:
        The boolean value of whether or not the entered input is valid
        """
        return self.is_valid_input

    def set_input_validity(self, boolean_value):
        """
        Changes the boolean property of whether or not the entered input inside the widgets input field is valid,
        whatever the criteria of validity may be
        Args:
            boolean_value: The boolean value, which the is valid text input property is supposed to be set to

        Returns:
        void
        """
        self.is_valid_input = boolean_value

    def set_input_valid(self):
        """
        Sets the property of whether the input is valid or not to be True
        Returns:
        void
        """
        self.set_input_validity(True)

    def set_input_invalid(self):
        """
        Sets the boolean property of whether ot not the input is valid to False
        Returns:
        void
        """
        self.set_input_validity(False)


class IntegerTextInput(LabeledValidityTextInput):
    """
    This class represents a TextInput widget, that is espacially designed for expecting the input of an integer value.
    The class is based on the LabelTextInput and thus offers the basic functionality, that the expected type of input
    can be displayed to the used as a string within the input widget, that will disappear as soon as the widget is
    focused and reappear, when the the widget is being unfocused again.
    The class implements a boolean property of whether or not the entered input is convertable to an integer or not.
    If the input is invalid, the background color of the widget will be set to light red, if it is valid however the
    background color is bing turned into a slight green.
    """
    def __init__(self, label_text="int"):
        LabeledValidityTextInput.__init__(self, label_text)

    def on_text(self, *args):
        """
        The callback method for the observer event in case the 'text' property of the widget changed.
        Upon changing the text property, which is the the complete string of the entered input, it is attempted to
        convert this string to integer type value. In case the conversion is possible setting the input to valid, but in
        case the conversion raised an exception, the input will be set to invalid
        Returns:
        void
        """
        try:
            # Trying to convert the the entered input, that is given, by the 'text' property into an integer type and
            # setting the input of the input widget to True, which will indicate to the user by changing the background
            # color of the widget to a light green automatically (call back of the validity
            int(self.text)
            self.set_input_valid()
        except ValueError:
            # In case the attempted conversion raised an exception, the input is being set as invalid, indicated by a
            # light red background
            self.set_input_invalid()


class FloatTextInput(LabeledValidityTextInput):
    """
    This class represents a TextInput widget, that is especially designed for expecting the input of an float value.
    The class is based on the LabelTextInput and thus offers the basic functionality, that the expected type of input
    can be displayed to the used as a string within the input widget, that will disappear as soon as the widget is
    focused and reappear, when the the widget is being unfocused again.
    The class implements a boolean property of whether or not the entered input is convertable to a float or not.
    If the input is invalid, the background color of the widget will be set to light red, if it is valid however the
    background color is bing turned into a slight green.
    """
    def __init__(self, label_text="int"):
        LabeledValidityTextInput.__init__(self, label_text)

    def on_text(self, *args):
        """
        The callback method for the observer event in case the 'text' property of the widget changed.
        Upon changing the text property, which is the the complete string of the entered input, it is attempted to
        convert this string to float type value. In case the conversion is possible setting the input to valid, but in
        case the conversion raised an exception, the input will be set to invalid
        Returns:
        void
        """
        try:
            # Trying to convert the the entered input, that is given, by the 'text' property into an integer type and
            # setting the input of the input widget to True, which will indicate to the user by changing the background
            # color of the widget to a light green automatically (call back of the validity
            float(self.text)
            self.set_input_valid()
        except ValueError:
            # In case the attempted conversion raised an exception, the input is being set as invalid, indicated by a
            # light red background
            self.set_input_invalid()


class ColoredButtonLabel(Button):
    """
    This widget is essentially a Button, although visually it rather looks like label, because the background of the
    widget was removed is being replaced by a choosable plain color.
    """
    color_list = ListProperty([])

    def __init__(self, color_list=[1, 1, 1, 1]):
        Button.__init__(self)
        self.color_list = color_list

    def on_color_list(self, *args):
        """
        The callback function for when the color_list attribute is being changed
        Args:
            *args:

        Returns:

        """
        self.background_color = self.color_list
        self.background_normal = ""

    def set_background_color(self, red, green, blue, opacity):
        """
        Sets the background color of the widget to the new mix of the given RGB format. All value have to be in a
        float range from 0 to 1

        Returns:
        void
        """
        # simply setting a new value to the color list attribute, as the callback of the observer property will then
        # automatically change the background color of the widget
        self.color_list = [red, green, blue, opacity]

    def on_size(self, *args):
        self.text_size = self.width - 20, 0


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

    font_size = NumericProperty(0)

    def __init__(self, subject, subsubject, font_size=13):
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
        self.grid_layout_submit.height = 30

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

        # Changing the font size attribute at last because the changing will trigger an observer event, as the font size
        # is a observer kivy numeric property, and the call back already changes all the font sizes.
        # Calling that callback any earlier an error would be raised, since the callback would then attempt to change
        # the font size attributes of sub-widgets, that werent initialized at that point.
        self.font_size = font_size

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

    def on_font_size(self, *args):
        """
        The callback for the observer Event in case the font size of the widget was changed. The method will update
        the new changed font size to all other subwidgets with some sort of Text display.
        (Maybe add the feature that the hight of those widgets changes dynamically as well, because at the point the
        changing of the font size will fuck up the format)
        :param args:
        :return:
        """
        # Updating the font size of all the input widgets
        self.text_input_latex.font_size = self.font_size
        self.text_input_points.font_size = self.font_size
        self.text_input_name.font_size = self.font_size

        # Updating the font size of all the labels
        self.label_description.font_size = self.font_size
        self.label_info.font_size = self.font_size

        # Updating the font size of the button
        self.button_submit.font_size = self.font_size

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


class MainScreen(Screen):

    def __init__(self, screen_manager):
        Screen.__init__(self)
        self.menu = MainMenu()
        self.add_widget(self.menu)
        self.name = "main"

        # The screen manager widget, which is needed to change the screens
        self.screen_manager = screen_manager

        self.menu.button_exams.bind(on_press=self.switch_exams_screen)

    def switch_exams_screen(self, *args):
        """
        Switches the current screen of the screen manager to display the exams menu
        Args:
            *args: -

        Returns:
        void
        """
        # The screen manager in the PiLearner project works with the "SlideTransition" transition, which has the
        # property 'direction', that is a string defining into which direction the current screen slides off to make
        # to make space for the new screen. In the PiLearn app the all transitions from a menu to a sub menu will go
        # left and all transitions back up the hierarchy towards the main screen go right.
        self.screen_manager.transition.direction = "left"
        # Changing the screen to the 'exams' screen
        self.screen_manager.current = "exams"


class MainMenu(GridLayout):
    """
    This Widget is the Main Menu, that is shown upon starting up the PiLearn App. it inherits from a kivy GridLayout
    widget and thus organizes all its subwidgets in a grid, more specifically a purely vertical grid (only one
    column and multiple rows) with the rows being in different sizes.
    The first subwidget of the menu is a label displaying the project name "PiLearner" with the "Pi" being
    highlighted with a slight green coloring and the font size of the labels content being twice as big as the font
    size of the whole menu widget in general.
    After the first Label there is a number of kivy Buttons, meant to act as the trigger to transition into the
    sub menu/ sub screen, the buttons label indicate. The callback function for the method is not being assigned in
    this class though, as this is merely the instance of the main menu adding basic logic and mainly the graphical
    layout of the menu

    Attributes:
        font_size: The 'NumericProperty' that stores the widgets font size. Upon simply changing it, the font size
            attributes of all the subwidgets are changed as well.
    """
    font_size = NumericProperty(0)

    def __init__(self, font_size=15):
        # Initializing the super class
        GridLayout.__init__(self)
        self.spacing = 10
        self.padding = 10
        self.rows = 4
        self.cols = 1

        # Creating the Label, that is being used as the header for the main menu. Using the string that was passed as
        # the parameter 'header_string' as the header of the main menu
        header_text_list = [color_markup(PILEARN_COLOR_CODE, "Pi"), "Learner\n"]
        header_text = ''.join(header_text_list)
        self.label_header = Label()
        self.label_header.text = header_text
        self.label_header.markup = True
        self.label_header.size_hint_y = None
        self.label_header.height = 90
        self.add_widget(self.label_header)

        # Creating the Button object, from which to navigate the main menu later on.
        # Creating the 'Exams' Button, that calls the exams menu
        self.button_exams = Button()
        self.button_exams.text = "Exams"
        self.button_exams.size_hint_y = None
        self.button_exams.height = 40
        self.add_widget(self.button_exams)

        # Creating the 'Subjects' Button, that calls the sub menu for the subjects
        self.button_subjects = Button()
        self.button_subjects.text = "Subjects"
        self.button_subjects.size_hint_y = None
        self.button_subjects.height = 40
        self.add_widget(self.button_subjects)

        # Creating the 'Options' Button, that calls the sub menu for modifying the applications options
        self.button_options = Button()
        self.button_options.text = "Options"
        self.button_options.size_hint_y = None
        self.button_options.height = 40
        self.add_widget(self.button_options)

        # Assigning the font size last, because the assignment or rather the changing of the font size attribute of the
        # object will trigger its assigned callback value, since the font size attribute is a kivy, observed numeric
        # property. The callback adjusts the font size attributes of all subwidgets to match the font size of the top
        # level widget. Changing the value and thus calling the callback any sooner would result in a error, due the
        # non existing subwidgets
        self.font_size = font_size

    def on_font_size(self, *args):
        """
        The callback for the observer Event in case the font size of the widget was changed. The method will update
        the new changed font size to all other subwidgets with some sort of Text display.
        (Maybe add the feature that the hight of those widgets changes dynamically as well, because at the point the
        changing of the font size will fuck up the format)
        Returns:
        void
        """
        self.button_exams.font_size = self.font_size
        self.button_subjects.font_size = self.font_size
        self.button_options.font_size = self.font_size

        self.label_header.font_size = self.font_size * 2


class ExamsScreen(Screen):

    def __init__(self, screen_manager):
        Screen.__init__(self)
        self.menu_exams = ExamsMenu()
        self.add_widget(self.menu_exams)
        self.name = "exams"

        self.screen_manager = screen_manager

        # Creating the 'solve exam' screen, which is empty on default
        self.screen_solve_exam = SolveExamScreen()
        self.screen_manager.add_widget(self.screen_solve_exam)

        # Binding the press of the button, which is on top of the exams menu (which is also the label displaying the
        # name of the sub menu currently in) to switch back to the main menu if pressed
        self.menu_exams.button_header.bind(on_press=self.switch_main_menu)

        # Binding the press of the 'solve' button on the lower end of the screen to the 'solve_exam' method, which
        # loads the exam object according to the selected tree view node, creates a SolveExamMenu and sets this Menu
        # to be the 'solve exam' screen of the screen manager and then changes to that screen.
        self.menu_exams.button_solve.bind(on_press=self.solve_exam)

    def switch_main_menu(self, *args):
        """
        Switches the current screen of the screen manager to display the main screen again.
        The callback method for the label button, which is on top of the  exams menu and displays which menu the screen
        manager is currently in
        Args:
            *args: -

        Returns:
        void
        """
        # The screen manager in the PiLearner project works with the "SlideTransition" transition, which has the
        # property 'direction', that is a string defining into which direction the current screen slides off to make
        # to make space for the new screen. In the PiLearn app the all transitions from a menu to a sub menu will go
        # left and all transitions back up the hierarchy towards the main screen go right.
        self.screen_manager.transition.direction = "right"
        # Switching the current scrren back to be the main screen
        self.screen_manager.current = "main"

    def solve_exam(self, *args):
        # Getting the exam object from the currently selected tree view node
        exam_object = self.menu_exams.get_selected_exam()

        # Setting up the solve exam screen
        self.screen_solve_exam.solve(exam_object)

        # Using the screen manager to change the screen to the solve exam screen
        self.screen_manager.transition.direction = "left"
        self.screen_manager.current = "solve exam"


class ExamsMenu(GridLayout):

    font_size = NumericProperty(0)

    def __init__(self, font_size=15):
        GridLayout.__init__(self)
        self.cols = 1
        self.rows = 3
        self.padding = 5
        self.spacing = 5

        # Creating the first subwidget to the overall menu, which has the function of a info label about which menu is
        # currently open. The widget actually being a button though, it seems like a label, but clicking it will result
        # in the screen changing back to the main menu
        self.button_header = ColoredButtonLabel()
        self.button_header.color_list = PILEARN_COLOR_LIST
        self.button_header.text = "Exams"
        self.button_header.size_hint_y = None
        self.button_header.halign = "left"
        self.button_header.height = 35
        self.add_widget(self.button_header)

        # Creating the main 'TreeView' widget, that contains the information about the exams
        self.scroll_view_tree = ScrollView()
        self.tree_view = TreeView(root_options=dict(text="exams"), hide_root=True)
        self.tree_view.size_hint_y = None

        # The sub node of the main tree view widget, that contains the names of the pending exams.
        # The sub nodes to the pending exams node are being loaded by the separate method 'add_pending_exams_tree' and
        # are based on the list of currently existing 'session' files within the 'exams' folder of the project
        self.label_tree_pending_exams = TreeViewLabel()
        self.label_tree_pending_exams.text = "pending exams"
        self.tree_node_pending_exams = self.tree_view.add_node(self.label_tree_pending_exams)

        self.add_pending_exams_tree()

        self.scroll_view_tree.add_widget(self.tree_view)
        self.add_widget(self.scroll_view_tree)

        # The Grid layout containing the two Buttons, that are located at the end of the window.
        # The buttons are to be aligned horizontally, therefore an additional layout is needed on top of the main
        # menu widget being a layout as well (a strictly vertical though).
        self.grid_layout_buttons = GridLayout()
        self.grid_layout_buttons.cols = 2
        self.grid_layout_buttons.rows = 1
        self.grid_layout_buttons.padding = 5
        self.grid_layout_buttons.spacing = 10
        self.grid_layout_buttons.size_hint_y = None
        self.grid_layout_buttons.height = 40
        self.add_widget(self.grid_layout_buttons)

        # The button, that triggers the solve procedure for a given, pending exam, that was selected within the tree
        # view widget
        self.button_solve = Button()
        self.button_solve.text = "solve"
        self.grid_layout_buttons.add_widget(self.button_solve)

        # The button, which triggers the creation of a new exam
        self.button_create = Button()
        self.button_create.text = "create"
        self.grid_layout_buttons.add_widget(self.button_create)

        self.font_size = font_size

    def add_pending_exams_tree(self):
        """
        This method loads the names of all open session found in the 'exams' folder of the project and adds the names
        as a sub node label to the pending exams node of the tree view widget.
        The method should be called after the tree view widget and the pending exams node for the tree view have already
        been created
        Returns:
        void
        """
        # Getting the list of the names of all currently existing session files. Session files being the files that are
        # being stored inside the 'exams' folder of the project and that contain the information about an 'open session'
        # aka a pending exam
        session_name_list = exam.get_session_name_list()

        # Creating a sub node to the pending exams node for every session name within the list
        for session_name in session_name_list:
            tree_label = TreeViewLabel(text=session_name)
            self.tree_view.add_node(tree_label, self.tree_node_pending_exams)

    def on_font_size(self, *args):
        # Updating the font size of the header button/label to be a little bigger than the overall font size
        self.button_header.font_size = self.font_size + 5

        # Updating the font size of the buttons at the end of the page to be exactly the overall font size
        self.button_solve.font_size = self.font_size
        self.button_create.font_size = self.font_size

        # Updating the TreeView widget nodes
        self.label_tree_pending_exams.font_size = self.font_size - 1
        pending_exams_nodes = self.tree_node_pending_exams.nodes
        for node in pending_exams_nodes:
            node.font_size = self.font_size - 2

    def get_selected_node(self):
        """
        Returns:
        The widget, that is currently selected within the tree view
        """
        return self.tree_view.get_selected_node()

    def get_selected_exam(self):
        """
        Returns:
        The Exam object, that was built from the session file to the selected tree view node
        """
        # The string property 'text' of the selected tree view label contains the session name of the exam in question.
        # The session name is a string of the format '{subject} - {subsubject}', the subject and subsubject names can
        # be calculated by splitting the string by the ' - ' substring. The subject and subsubject are then used to
        # load the exam from the session.
        selected_node = self.get_selected_node()
        session_name = selected_node.text
        session_name_split = session_name.split(" - ")
        subject = session_name_split[0]
        subsubject = session_name_split[1]
        exam_object = exam.exam_from_session(subject=subject, subsubject=subsubject)
        return exam_object


class StopwatchBase(GridLayout):
    """
    This class is the abstract base class for future stopwatch classes, as it implements the main logic, that updates
    the object properties of passed hours, minutes and seconds and implements methods to start and pause the time
    measurement.
    The time is measured by utilizing the python 'time' module. At the starting moment of the stopwatch, the first time
    stamp is being saved as an object property and then the current time property is constantly being updated by a
    scheduled kivy clock event, that updates the current time property a few times a second, thus calling the callback
    of its observer, inside which the time difference between the current and the starting time is calculated and
    converted into three separate values for the passed hours, minutes and seconds and stored as object properties.

    Notes:
        If the StopwatchBase class is to be used, the developer only has to add the graphical widgets to the
        constructor of this widget, which already is a GridLayout. The updating of the graphics display can be done
        inside the callback function for the current_time property: 'on_current_time(self, args)', as it is called
        twice a second while the stopwatch is running (Note that it shouldnt be overwritten, but rather extended,
        meaning, that the super() function should be called first)

    Attributes:
        start_time: The float value of the timestamp returned by the time.time() function, that was calculated in the
            moment the stopwatch was started
        current_time: The float value of the timestamp returned by the time.time() function, that is constantly being
            updated to match the actual current timestamp, but only while the stopwatch is running
        pause_time: The float value of the timestamp, calculated by the time.time() function, that was calculated in the
            moment the stopwatch was paused the last time
        hours: The integer value of how many hours the stopwatch has measured
        minutes: The integer value of how many minutes the stopwatch has measured
        seconds: The integer value of how many seconds the stopwatch has measured
        running: The boolean value of whether the stopwatch is currently running
    """
    start_time = NumericProperty(0)
    current_time = NumericProperty(0)
    pause_time = NumericProperty(0)

    hours = NumericProperty(0)
    minutes = NumericProperty(0)
    seconds = NumericProperty(0)

    running = BooleanProperty(False)

    def __init__(self):
        GridLayout.__init__(self)
        self.event = None

    def on_current_time(self, *args):
        """
        The callback function for the observer event in case the current time property of the widget was changed.
        After the stopwatch was started the current time property is constantly getting updated to match the actual
        current time, given by the time.time() function, thus this method is also called multiple times per second.
        This method calculates the difference between the start time of the stopwatch and the current time and
        converts the pure seconds value into three distinct values for the hours, minutes and seconds.
        Args:
            *args:

        Returns:
        void
        """
        # Calculating the time difference between the start time and the current time in seconds. Dividing this value
        # by 3600 and floor rounding it to get the amount of hours, multiplying the difference between the rounded and
        # the actual float value by 60 to get the amount of minutes left after building the hours.
        # Repeating the procedure with the minutes and seconds to convert the total amount og seconds into the three
        # distinct values for the hours, minutes and seconds
        time_difference = self.current_time - self.start_time

        hours_float = time_difference / 3600
        self.hours = int(hours_float)
        minutes_float = (hours_float - self.hours) * 60
        self.minutes = int(minutes_float)
        seconds_float = (minutes_float - self.minutes) * 60
        self.seconds = int(seconds_float)

    def start(self, *args):
        """
        starts the time measurement of the stopwatch
        Args:
            *args:

        Returns:
        void
        """
        # The pause time property is 0 on default and contains a time.time() timestamp for the moment the stopwatch
        # was paused, in case the pause method was called.
        # If the pause time value is bigger than the start time value, which means the watch was stopped at one point
        # after it was started, the original start time is being shifted by the amount of time, that passed between
        # the stop moment and the re-start, so that the difference between the start time and the current time is the
        # same after the unpause as it was in the moment of pausing
        if self.pause_time > self.start_time:
            time_difference = time.time() - self.pause_time
            self.start_time += time_difference
        else:
            self.start_time = time.time()
        self.running = True

        # Creating the actual clock interval, that calls the set current time method of this widget every half a
        # second, basically constantly updating the current time property to actually reflect the current time.
        # Because the property is observed, its callback is called as many times as the value changes. The callback
        # then actually contains the functionality of updating the widgets labels to display the time
        self.event = Clock.schedule_interval(self.update_current_time, 0.5)

    def pause(self, *args):
        """
        Pauses the stopwatch
        Args:
            *args:

        Returns:
        void
        """
        # Documenting the pause time, as for the functionality of the time measurement when the watch is being paused
        # the time difference between the moment of pausing the the moment of re starting the watch is essential and
        # can only be calculated if the moment of pause is saved.
        self.pause_time = time.time()
        if self.running:
            # Only in case the watch is actually running, the scheduled event of upadting the current time is being
            # canceled, therefore stopping the label upadte as well
            Clock.unschedule(self.event)
            self.running = False

    def update_current_time(self, *args):
        """
        Sets the current time value in seconds, given by the time.time(), as the current time property of the widget.
        If the stopwatch was started this function would be repeatedly called, mainly to trigger the callback method
        of the 'current_time' property's observer
        Args:
            *args:

        Returns:
        void
        """
        self.current_time = time.time()


class SimpleStopwatch(StopwatchBase):
    """
    This widget is a stopwatch widget built from simple
    """
    font_size = NumericProperty(0)

    def __init__(self, font_size=30):
        StopwatchBase.__init__(self)
        # The grid layout of this widget will consist of two rows, one row being for the descriptive labels, that show
        # which type of time unit is being tracked in the column they are in and the second row being for the labels,
        # that actually display the numbers of the time.
        # There will be three columns, being for the tracking of hours, minutes and seconds
        self.cols = 3
        self.rows = 2
        self.padding = 5
        self.spacing = 5

        # THE DESCRIPTIVE LABELS OF THE FIRST ROW
        self.descriptive_label_height = 20

        self.label_hours_description = Label()
        self.label_hours_description.text = "hours"
        self.label_hours_description.size_hint_y = None
        self.label_hours_description.height = self.descriptive_label_height
        self.add_widget(self.label_hours_description)

        self.label_minutes_description = Label()
        self.label_minutes_description.text = "minutes"
        self.label_minutes_description.size_hint_y = None
        self.label_minutes_description.height = self.descriptive_label_height
        self.add_widget(self.label_minutes_description)

        self.label_seconds_description = Label()
        self.label_seconds_description.text = "seconds"
        self.label_seconds_description.size_hint_y = None
        self.label_seconds_description.height = self.descriptive_label_height
        self.add_widget(self.label_seconds_description)

        # THE LABELS ACTUALLY CONTAINING THE NUMBERS FOR THE TIME
        self.numbers_label_height = 50

        self.label_hours = Label()
        self.label_hours.text = "00"
        self.label_hours.size_hint_y = None
        self.label_hours.height = self.numbers_label_height
        self.add_widget(self.label_hours)

        self.label_minutes = Label()
        self.label_minutes.text = "00"
        self.label_minutes.size_hint_y = None
        self.label_minutes.height = self.numbers_label_height
        self.add_widget(self.label_minutes)

        self.label_seconds = Label()
        self.label_seconds.text = "00"
        self.label_seconds.size_hint_y = None
        self.label_seconds.height = self.numbers_label_height
        self.add_widget(self.label_seconds)

        self.font_size = font_size
        self.on_size()

    def on_font_size(self, *args):
        """
        The callback function for the observer Event in case the font size property was changed. The method will adjust
        the font sizes of all sub widgets of the main widget based on the new main font size.
        The labels, that actually contain the numbers for the time measurement will be assigned the exact font size as
        the main font size, while the font size of the descriptive labels will be adjusted to be smaller than the main
        font size by the factor ~4
        Args:
            *args: -

        Returns:
        void
        """
        # Assigning the actual font size to the labels, that actually display the numbers for the time meassurement,
        # so naturally, that is supposed to be a fairly big number.
        self.label_hours.font_size = self.font_size
        self.label_minutes.font_size = self.font_size
        self.label_seconds.font_size = self.font_size

        # The font sizes of the descriptive Labels on the other hand ware supposed to be a lot smaller. in this case
        # by the factor 3
        description_font_size = int(self.font_size / 4)
        self.label_hours_description.font_size = description_font_size
        self.label_minutes_description.font_size = description_font_size
        self.label_seconds_description.font_size = description_font_size

    def on_size(self, *args):
        """
        The callback function for the observer event in case the size property changed, meaning the actual widget was
        resized in some way. The method will adjust the main font size of the widget (which is gonna be the same as the
        font size of the number labels) to be smaller than the width by a factor of ~5.
        The font size is being changed to be a dependent on the width, because this way the distance between the
        individual labels will stay constant, which looks better than a constant font size.
        Args:
            *args: -

        Returns:
        void
        """
        # Updating the font size of the widget. The ration of width by font size is supposed to be approx. 4.5
        # If this calculated font size does not exceed the maximum size, which is at approx. 60% of the widget height,
        # the calculated font size is being used as the actual font size.
        # In case the max size is exceeded, the font size is being set as the max size and then, to maintain the widget
        # integrity/ratios, the excess width is being substracted from the effective widget width by extending the left
        # and right padding by half the value.
        font_size = int(self.width / 4.5)
        max_font_size = int(self.height * 0.6)
        if font_size <= max_font_size:
            self.font_size = font_size

        else:
            #
            self.font_size = max_font_size
            # The ratio of width to height is supposed to be 3(width) to 1(height). If the ratio is not given the
            # padding left and right is being adjusted so that the effective ratio of the actual label widgets matches
            # up to 3/1
            ratio = self.width / self.height
            excess_width = ratio * self.height - 300
            padding = int(excess_width / 2)
            self.padding = [padding, 5, padding, 5]

    def on_current_time(self, *args):
        """
        The callback function for the observer event in case the current time property of the widget was changed.
        After the stopwatch was started the current time property is constantly getting updated to match the actual
        current time, given by the time.time() function, thus this method is also called multiple times per second.
        This method calculates the difference between the start time of the stopwatch and the current time and
        converts the pure seconds value into three distinct values for the hours, minutes and seconds and changes the
        main labels text properties to display exactly those values
        Args:
            *args:

        Returns:
        void
        """
        # Calling the method of the parent class, because it updates the hours, minutes and seconds property, which are
        # needed / essential for the function of the whole widget
        super(SimpleStopwatch, self).on_current_time(*args)

        # Setting the label texts to the values given by the calculation
        self.label_hours.text = str(self.hours)
        self.label_minutes.text = str(self.minutes)
        self.label_seconds.text = str(self.seconds)


class SolveExamScreen(Screen):

    menu_solve_exam = ObjectProperty(Label())

    def __init__(self):
        # Initializing the super class
        Screen.__init__(self)
        self.name = "solve exam"
        self.add_widget(self.menu_solve_exam)

    def solve(self, exam_object):
        self.remove_widget(self.menu_solve_exam)
        self.menu_solve_exam = SolveExamMenu(exam_object)
        self.add_widget(self.menu_solve_exam)


class SolveExamMenu(GridLayout):

    def __init__(self, exam_object):
        # Initializing the super class
        GridLayout.__init__(self)
        self.cols = 1
        self.rows = 2
        self.padding = 5
        self.spacing = 5

        self.exam = exam_object
        self.name = "{}-{}".format(self.exam.subject, self.exam.subsubject)

        self.button_header = ColoredButtonLabel()
        self.button_header.color_list = PILEARN_COLOR_LIST
        self.button_header.text = self.name
        self.button_header.size_hint_y = None
        self.button_header.halign = "left"
        self.button_header.height = 35
        self.add_widget(self.button_header)

        # The actual widget to solve the exam
        self.solve_exam = SolveExam(self.exam)
        self.add_widget(self.solve_exam)


class ExercisePointsInput(GridLayout):
    """
    This class represents a widget, that allows the input of the amount of achieved points for a given exercise.
    The widget base is a grid layout, with 1 row and 2 columns. A label being the first widget on the left, making up
    about 70% of the widgets width and displaying the string of the specified exercise name. The second widget on the
    left being an IntegerTextInput widget for entering the amount of achieved points. The input widget will indicate,
    whether the input is valid for as the amount of points, by changing the background color to a light red in case the
    input is invalid (string not convertible to int or the int value being bigger than the value of actual

    Attributes:
        font_size: The kivy NumericProperty for the font size of the widget and thus also the font size of the both
            individual subwidgets

    Args:
        exercise_object: The Exercise object, the widget is supposed to represent
        font_size: The integer value of the font size, the widgets are supposed to have
    """
    font_size = NumericProperty(0)

    def __init__(self, exercise_object, font_size=12):
        # Initializing the super class
        GridLayout.__init__(self)
        self.rows = 1
        self.cols = 2
        self.spacing = 5

        # An instance of this object has to be created, by passing the exercise_object, which the widget is supposed
        # to represent
        self.exercise = exercise_object
        self.exercise_name = self.exercise.name
        self.max_points = self.exercise.max_points

        # The label, displaying the name of the exercise to grade
        self.label_exercise_name = Label()
        self.label_exercise_name.text = self.exercise_name
        self.label_exercise_name.bind(size=self.label_exercise_name.setter("text_size"))
        self.label_exercise_name.size_hint_x = 0.7
        self.label_exercise_name.halign = "left"
        self.label_exercise_name.valign = "middle"
        self.add_widget(self.label_exercise_name)

        # The input widget for the points
        self.integer_input_points = IntegerTextInput("points")
        self.integer_input_points.size_hint_x = None
        self.integer_input_points.bind(text=self.on_text)
        self.add_widget(self.integer_input_points)

        self.font_size = font_size

    def on_text(self, *args):
        """
        The callback method, that is being bound to the obesrver event of the text property of the input widget.
        The method first checks whether the entered input is an integer, by calling the actual callback method of the
        input widget, which is an instance of the class 'IntegerTextInput' and updating the validity property of the
        input widget accordingly. In case the input is indeed an integer type value, the method gies on and checks
        whether or not the entered value for the points does exceed the maximum amount of points possible for the
        exercise.
        Args:
            *args: -

        Returns:
        void
        """
        # Calling the 'on_text' of the super class, as that method is the first instance of checking the input validity,
        # as it checks for the input bing an integer to begin with
        self.integer_input_points.on_text()

        # In case the entered input is indeed an integer, the text will be converted to this integer value. If this
        # integer value is bigger than the maximum amount of points possible for the exercise though, the input widget
        # will be set to have an invalid input anyways
        if self.integer_input_points.is_valid():
            point_value = int(self.integer_input_points.text)
            if point_value > self.max_points or point_value < 0:
                self.integer_input_points.set_input_invalid()

    def on_font_size(self, *args):
        """
        The callback method for the observer event in case the font size of the overall widget is changed.
        The method simply updates the font sizes of the individual widgets (The labvel with the exrecise name and the
        input widget for the points) to be the font size, specified for the overall widget
        Args:
            *args: -

        Returns:
        void
        """
        # Updating the font size of the label with the name of the exercise to match the font size of the overall widget
        self.label_exercise_name.font_size = self.font_size

        # Updating the font size of the input widget for the points to match the font size of the overall widget
        self.integer_input_points.font_size = self.font_size

    def get_points(self):
        """
        Returns:
        The integer value of the entered points in case the entered input of the input widget is actually valid and
        returns None in case the input is invalid
        """
        if self.integer_input_points.is_valid():
            return int(self.integer_input_points.text)
        else:
            return None


class ExamPointsInput(GridLayout):
    """
    This class represents a widget, that enables the user input for the amount of reached points for a given exam
    object. The widgets base is a grid layout, with vertically stacked ExercisePointsInput widgets for each of the
    exercises, that are part of the exam.

    Attributes:
        font_size: The kivy NumericProperty for the font size of the widget and thus also the font size of every
            individual sub widget
        exercise_points_input_widgets: The kivy ListProperty for the list, containing references to all the individual
            input widget objects, that are part of the main grid layout.
        exam: The Exam object, to be represented
        exercise_list: The ExerciseList object of the Exam object, being a container object for all the Exercise
            objects, that are part of the exam.

    Args:
        exam_object: The Exam object, to be represented
    """
    # The font size of the overall widget, that will be passed on to the individual sub widgets
    font_size = NumericProperty(0)
    # This list will contain the all the ExercisePointsInput widgets, that are being created from the Exercise objects,
    # that are part of the exam, represented by this widget
    exercise_points_input_widgets = ListProperty([])

    def __init__(self, exam_object, font_size=12):
        # Initializing the super class
        GridLayout.__init__(self)
        self.cols = 1
        self.padding = 5
        self.spacing = 5

        # An instance of this widget is being created by passing the Exam object of the exam, which the widget is meant
        # to represent. The Exam object contains the main ExerciseList, which can be iterated through to get all
        # Exercise objects, that are part of the Exam.
        self.exam = exam_object
        self.exercise_list = self.exam.exercise_list

        # Setting the amount rows of the grid layout to match the amount of exercises in the exam aka the length of the
        # exercise list fo the exam
        self.rows = len(self.exercise_list)

        # Iterating through the list opf Exercise object, that are part of the given exam object and creating a
        # ExercisePointsInput widget for every one of them, adding them to the list attribute, through which they can
        # be accessed later on before actually adding the widget to the main grid layout
        for exercise_object in self.exercise_list:
            exercise_points_input = ExercisePointsInput(exercise_object)
            exercise_points_input.size_hint_y = None
            exercise_points_input.height = 30
            self.exercise_points_input_widgets.append(exercise_points_input)
            self.add_widget(exercise_points_input)

        self.font_size = font_size

    def on_font_size(self, *args):
        """
        The callback method for the observer event in case the font size property of the widget was changed.
        The method will update the font size of all the sub widgets to match the font size of the main widget
        Args:
            *args:

        Returns:
        void
        """
        # Upon the font size property of the main widget (grid layout) was changed, passing on that change to the sub
        # to the sub widgets, by itering through the list of widgtes and upadating their font size
        for exercise_points_input in self.exercise_points_input_widgets:
            exercise_points_input.font_size = self.font_size

    def is_valid(self):
        """
        Checks every single input widget for its input validity, in case only one of them is invalid makes the whole
        main widget invalid
        Returns:
        whether or not all the input widgets within this main wigdets are valid or not
        """
        # First assuming all the inputs are valid and checking all the input widgets, but returning False in case one
        # of the widgets turns out to have invalid input. In case the loop exits that would mean False wasnt already
        # returned, so no input was invalid
        for exercise_points_input in self.exercise_points_input_widgets:
            if not exercise_points_input.is_valid():
                return False
        return True


class SolveExam(GridLayout):

    font_size = NumericProperty(0)

    def __init__(self, exam_object, font_size=12):
        # Initialising the super class
        GridLayout.__init__(self)
        self.cols = 1
        self.rows = 4
        self.padding = 5
        self.spacing = 5

        self.exam = exam_object

        # The button on top of the widget will be used to open the PDF file of the exam in a separate reader app
        self.button_open_exam = Button()
        self.button_open_exam.text = "Open Exam PDF"
        self.button_open_exam.size_hint_y = None
        self.button_open_exam.height = 40
        self.add_widget(self.button_open_exam)

        # The ScrollView for the main exam points input widget
        self.scroll_view_exercises = ScrollView()
        self.exam_points_input = ExamPointsInput(self.exam)
        # Important: To use a ScrollView widget, the size hint for the axis that is supposed to be scrollable has to be
        # set to None and the minimum size of that axis (height for y, width for x) has to be bound to the setter of
        # the actual size of that axis. Otherwise the scroll view wont work
        self.exam_points_input.size_hint_y = None
        self.exam_points_input.bind(minimum_height=self.exam_points_input.setter("height"))
        self.scroll_view_exercises.add_widget(self.exam_points_input)
        self.add_widget(self.scroll_view_exercises)

        # The grid layout containing the three buttons to control the stop watch
        self.grid_layout_buttons = GridLayout()
        self.grid_layout_buttons.cols = 3
        self.grid_layout_buttons.rows = 1
        self.grid_layout_buttons.spacing = 5
        self.grid_layout_buttons.size_hint_y = None
        self.grid_layout_buttons.height = 35

        self.button_start = Button()
        self.button_start.text = "start"
        self.grid_layout_buttons.add_widget(self.button_start)

        self.button_pause = Button()
        self.button_pause.text = "pause"
        self.grid_layout_buttons.add_widget(self.button_pause)

        self.button_finish = Button()
        self.button_finish.text = "finish"
        self.grid_layout_buttons.add_widget(self.button_finish)

        self.add_widget(self.grid_layout_buttons)

        # The Stopwatch widget to meassure the time, the exam took.
        self.stop_watch = SimpleStopwatch()
        self.stop_watch.size_hint_y = None
        self.stop_watch.height = 90
        self.add_widget(self.stop_watch)






