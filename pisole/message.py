class Message:

    message_color_dict = {"white": "DEDEDE",
                          "red": "D61818",
                          "green": "3AD126",
                          "blue": "397AD4",
                          "magenta": "D439B7"}

    def __init__(self, string, prefix, short_prefix, color):
        """
        an object representing a message or outcome information of a command, mainly to encapsulate the information
        of such a message's content, type, ui coloring and prefix info in a single object, that can be transported through a
        multiprocessing Queue and also easily accessed

        :ivar content: (string) The content of the message

        :ivar prefix: (string) The prefix of the message, indicating the user in a non color ui, which type of message is
        being displayed (error, info, result...) in square brackets
        EXAMPLE:
        [PREFIX] content...

        :ivar short_prefix: (string) The short symbol for the message type, being an alternative prefix to a full word
        EXAMPLE:
        [i] content...

        :ivar color: (string) the name of a color (that has to exist in the internal color dictionary), in which the message
        should appear, if possible in the corresponding ui environment
        """
        self.content = string

        # adding the brackets to the prefix strings
        self.prefix = self._add_prefix_brackets(prefix)
        self.short_prefix = self._add_prefix_brackets(short_prefix)

        # color
        self.color_name = ""
        self.color = ""
        if color in self.message_color_dict.keys():
            self.color_name = color
            self.color = self.message_color_dict[self.color_name]

        elif color[0] == "#" and len(color) == 7:
            self.color = color

        else:
            self.color_name = "white"
            self.color = self.message_color_dict[self.color_name]

    def get_string(self, short_prefix=False):
        """
        Returns the string representation of the Message
        :param short_prefix: (boolean) whether the shortened prefix is to be used or not
        :return: (string)
        """
        pass

    def __str__(self):
        return self.get_string()

    @staticmethod
    def _add_prefix_brackets(prefix_string):
        """
        puts the string into the '[]' brackets, so it is marked as a message type prefix, signaling which type of
        message is being displayed.
        :param prefix_string: the prefix, which to put into the brackets
        :return: (string) the prefix string within the brackets
        """
        return ''.join(["[", prefix_string, "]"])


class InfoMessage(Message):
    """
    an object representing a informational message about a runtime event of the corresponding command, mainly to
    encapsulate the information of such a message's content, type, ui coloring and prefix info in a single object, that
    can be transported through a multiprocessing Queue and also easily accessed

    :ivar content: (string) The content of the message

    :ivar prefix: (string) The prefix of the message, indicating the user in a non color ui, which type of message is
    being displayed (error, info, result...) in square brackets
    EXAMPLE:
    [PREFIX] content...

    :ivar short_prefix: (string) The short symbol for the message type, being an alternative prefix to a full word
    EXAMPLE:
    [i] content...

    :ivar color: (string) the name of a color (that has to exist in the internal color dictionary), in which the message
    should appear, if possible in the corresponding ui environment
    """

    def __init__(self, string):
        super(InfoMessage, self).__init__(string, "INFO", "*", "white")

    def get_string(self, short_prefix=False):
        """
        Returns the string representation of the Message
        :param short_prefix: (boolean) whether the shortened prefix is to be used or not
        :return: (string)
        """
        return_string_list = []
        if short_prefix:
            return_string_list.append(self.short_prefix)
        else:
            return_string_list.append(self.prefix)
        return_string_list.append(" ")
        return_string_list.append(self.content)
        return ''.join(return_string_list)

    def get_kivy(self, short_prefix=False):
        """
        Returns the string representation of the string, in addition to the color information of the Message added in
        form of the kivy markup language tags, to be compatible to print onto a kivy label/widget.
        :param short_prefix: (boolean) whether the shortened prefix is to be used or not
        :param newline: (boolean) whether a new line should be started after displaying the prefix or not
        :return: (string)
        """
        return_string_list = ["[color={0}]".format(self.color), "[b]"]
        if short_prefix:
            return_string_list.append(self.short_prefix)
        else:
            return_string_list.append(self.prefix)
        return_string_list.append("[/b]")
        return_string_list.append(" ")
        return_string_list.append(self.content)
        return_string_list.append("[/color]")
        return ''.join(return_string_list)


# TODO: Maybe add Traceback information and origin process information
class ErrorMessage(Message):
    """
    an object representing a message about a exception occuring in the corresponding command, mainly to encapsulate
    of such a message's content, type, ui coloring and prefix info in a single object, that can be transported through a
    multiprocessing Queue and also easily accessed

    :ivar content: (string) The content of the message

    :ivar prefix: (string) The prefix of the message, indicating the user in a non color ui, which type of message is
    being displayed (error, info, result...) in square brackets
    EXAMPLE:
    [PREFIX] content...

    :ivar short_prefix: (string) The short symbol for the message type, being an alternative prefix to a full word
    EXAMPLE:
    [i] content...

    :ivar color: (string) the name of a color (that has to exist in the internal color dictionary), in which the message
    should appear, if possible in the corresponding ui environment

    :ivar exception_name: (string) The Type of exception passed as content of the error
    """
    def __init__(self, excepetion):
        # setting the exceptions content as the main message string
        string = str(excepetion)
        super(ErrorMessage, self).__init__(string, "ERROR", "!", "red")

        # adding a field for the exceptions name
        self.exception_name = type(excepetion).__name__

    def get_string(self, short_prefix=False):
        """
        Returns the string representation of the Error/Exception in the following form:

        [PREFIX] ExcpetionName
        error message of the exception

        :param short_prefix: whether the shortened prefix is to be used or not
        :return: (string)
        """
        return_string_list = []
        if short_prefix:
            return_string_list.append(self.short_prefix)
        else:
            return_string_list.append(self.prefix)
        return_string_list.append(" ")
        return_string_list.append(self.exception_name)
        return_string_list.append("\n")
        return_string_list.append(self.content)
        return ''.join(return_string_list)

    def get_kivy(self, short_prefix=False):
        """
        Returns the string representation of the string, in addition to the color information of the Message added in
        form of the kivy markup language tags, to be compatible to print onto a kivy label/widget.
        :param short_prefix: (boolean) whether the shortened prefix is to be used or not
        :param newline: (boolean) whether a new line should be started after displaying the prefix or not
        :return: (string)
        """
        return_string_list = ["[color={0}]".format(self.color), "[b]"]
        if short_prefix:
            return_string_list.append(self.short_prefix)
        else:
            return_string_list.append(self.prefix)
        return_string_list.append("[/b] {0}\n".format(self.exception_name))
        return_string_list.append("{0}[/color]".format(self.content))
        return ''.join(return_string_list)


class ResultMessage(Message):
    """
    an object representing a result message or outcome information of a command, mainly to encapsulate the information
    of such a message's content, type, ui coloring and prefix info in a single object, that can be transported through a
    multiprocessing Queue and also easily accessed

    :ivar content: (string) The content of the message

    :ivar prefix: (string) The prefix of the message, indicating the user in a non color ui, which type of message is
    being displayed (error, info, result...) in square brackets
    EXAMPLE:
    [PREFIX] content...

    :ivar short_prefix: (string) The short symbol for the message type, being an alternative prefix to a full word
    EXAMPLE:
    [i] content...

    :ivar color: (string) the name of a color (that has to exist in the internal color dictionary), in which the message
    should appear, if possible in the corresponding ui environment
    """
    def __init__(self, string):
        super(ResultMessage, self).__init__(string, "RESULT", "+", "green")

    def get_string(self, short_prefix=False, newline=False):
        """
        Returns the string representation of the Message
        :param short_prefix: (boolean) whether the shortened prefix is to be used or not
        :param newline: (boolean) whether a new line should be started after displaying the prefix or not
        :return: (string)
        """
        return_string_list = []
        if short_prefix:
            return_string_list.append(self.short_prefix)
        else:
            return_string_list.append(self.prefix)
        return_string_list.append(" ")
        if newline:
            return_string_list.append("\n")
        return_string_list.append(self.content)
        return ''.join(return_string_list)

    def get_kivy(self, short_prefix=False, newline=False):
        """
        Returns the string representation of the string, in addition to the color information of the Message added in
        form of the kivy markup language tags, to be compatible to print onto a kivy label/widget.
        :param short_prefix: (boolean) whether the shortened prefix is to be used or not
        :param newline: (boolean) whether a new line should be started after displaying the prefix or not
        :return: (string)
        """
        return_string_list = ["[color={0}]".format(self.color), "[b]"]
        if short_prefix:
            return_string_list.append(self.short_prefix)
        else:
            return_string_list.append(self.prefix)
        return_string_list.append("[/b] ")
        if newline:
            return_string_list.append("\n")
        return_string_list.append("{0}[/color]".format(self.content))
        return ''.join(return_string_list)


class InputPromptMessage(Message):

    def __init__(self, string):
        super(InputPromptMessage, self).__init__(string, "INPUT", "IN", "blue")

    def get_string(self, short_prefix=False, newline=False):
        """
        Returns the string representation of the Message
        :param short_prefix: (boolean) whether the shortened prefix is to be used or not
        :param newline: (boolean) whether a new line should be started after displaying the prefix or not
        :return: (string)
        """
        return_string_list = []
        if short_prefix:
            return_string_list.append(self.short_prefix)
        else:
            return_string_list.append(self.prefix)
        return_string_list.append(" ")
        if newline:
            return_string_list.append("\n")
        return_string_list.append(self.content)
        return ''.join(return_string_list)

    def get_kivy(self, short_prefix=False, newline=False):
        """
        Returns the string representation of the string, in addition to the color information of the Message added in
        form of the kivy markup language tags, to be compatible to print onto a kivy label/widget.
        :param short_prefix: (boolean) whether the shortened prefix is to be used or not
        :param newline: (boolean) whether a new line should be started after displaying the prefix or not
        :return: (string)
        """
        return_string_list = ["[color={0}]".format(self.color), "[b]"]
        if short_prefix:
            return_string_list.append(self.short_prefix)
        else:
            return_string_list.append(self.prefix)
        return_string_list.append("[/b] ")
        if newline:
            return_string_list.append("\n")
        return_string_list.append("{0}[/color]".format(self.content))
        return ''.join(return_string_list)