__author__ = 'Jonas'
import re
import os
import pickle
import inspect
import configparser
import JTSv2.execute as execute
import JTSv2.lib.stringutil as stringops


ILLEGAL_CHARACTERS_FUNCTION_NOMENCLATURE = [" ", ",", ".", "-", "+"]

BUILTIN_FUNCTION_NAMES =["abs", "all", "any", "ascii", "bin", "bool", "bytearray", "bytes", "callable", "char",
                         "classmethod", "compile", "complex", "delattr", "dict", "dir", "divmod", "enumerate", "eval",
                         "exec", "filter", "float", "format", "frozenset", "getattr", "globals", "hasattr", "hash",
                         "help", "hex", "id", "input", "int", "isinstance", "issubclass", "iter", "len", "list",
                         "locals", "map", "max", "memoryview", "min", "next", "object", "oct", "open", "ord", "pow",
                         "print", "property", "range", "repr", "reversed", "round", "set", "setattr", "slice", "sorted",
                         "staticmethod", "str", "sum", "super", "tuple", "type", "vars", "zip"]


def translate(input_str, first_parameter):
    translated_string = input_str
    # translated_string = _translate_environmental_variables(input_str)
    translated_string = _translate_commands(translated_string, first_parameter)
    return translated_string


# Currently not in use for the Pisole Project
def _translate_environmental_variables(input_string):
    """
    given the string of the terminal input this function will translate referenced environmental variables (Env
    variables are specified by adding a dollar '$' prefix to the variable name, example '$test = 3') into strings, that
    are used as keys for the 'EnV' Dictionary, example 'EnV['$test'] = 3', as that is the EnvironmentalVariableContainer
    as he is known within the execute methods namespace.

    EXAMPLE:
    "$Hallo = $No and '$Hallo'"
    > "EnV['$Hallo'] = EnV['$No'] and '$Hallo'"

    :param input_string:
    :return:
    """
    translated_string = input_string
    env_variable_list = _find_environmental_variables(input_string)
    for variable_name in env_variable_list:
        translated_string = stringops.replace_ignore_in_quotationmarks(translated_string, variable_name,
                                                                       "EnV['{var}']".format(var=variable_name))
    return translated_string


def _translate_commands(input_string, first_parameter):
    """
    This function was originally a part of the JTShell Project´, but has been modified to do translations for the
    smaller Pisole project.

    Since the Pisole Project is fairly simple and essentially only uses the functions within a single python module
    as commands, there is no big need for translation as the function names can be pulled into the local namespace of
    the main pisole module by one single "import everything" call.
    But those functions still need to be passed the actaul PisoleConsole object, so the command functions can perform
    interactions with the ui widget.
    This function essentially uses the original JTSHell algorithm to identify and split the input command string into
    the individual commands and simply adds the string given by the parameter 'first_parameter' as first parameter to
    every non-builtin functioncall inside the input string.

    :param input_string: (string) the string of the execution command, issued by the user of the console
    :param first_parameter: (string) This string will be added as first parameter to every function call within the
    input_string, that isnt a builtin function
    :return: (string) The translated string that can be straight used be dynamically executed by the python interpreter
    """
    translated_string = input_string

    command_list = _find_whole_commands(input_string)

    for command in command_list:
        command_name = _get_commandname(command)

        # checking whether the current function call is a legit custom command or a python builtin, that is being used
        # in case the reference dictionary doesnt know the command name, assuming it is a builtin or whatever
        # skipping to the next command
        if command_name in BUILTIN_FUNCTION_NAMES:
            continue

        # In case there is a exclamation mark in front of the command, this means, that the command si supposed to be
        # run as a background process, therefore putting the main function call into background() function call, which
        # is a function within the execute module, that expects an executer object and the execution statement as string
        # so it can execute it as a Process.
        translated_command = stringops.replace_ignore_in_quotationmarks(command, command_name + "(", ''.join([command_name,
                                                                                          "({},".format(first_parameter)]))

        # replacing the command with the translated command in the finished string
        translated_string = stringops.replace_ignore_in_quotationmarks(translated_string, command, translated_command)

    return translated_string


def _find_command_names(input_str):
    """
    If given the string of a terminal input, the function will  search for all command calls within the input and then
    return a list containing the names of all commands that are called.
    The Commands are identified by the brackets they have to be followed by just as they have to in regular python

    EXAMPLE:
    "Command() and Test()"
    > ['Command', 'Test']

    :param input_str: (string) the terminal input issued by the user
    :returns: (list)
    """
    command_list = []
    reg = re.compile("""[^().,\-+"'#*'\s]*\(""")
    for string in stringops.split_string_structures(input_str):
        if not((string[0] == "'" or string[0] == '"') and (string[-1] == "'" or string[-1] == '"')):
            command_list += re.findall(reg, string)
    return list(map(lambda x: x.replace(" ", "").replace("(", ""), command_list))


def _get_commandname(command_string):
    """
    if given the string of a whole command, returns only the name of the command

    EXAMPLE:
    'Command(100, 'hello')'
    > 'Command'

    :param command_string:
    :return:
    """
    return command_string[:command_string.find("(")]


def _find_whole_commands(input_str):
    """
    If given a string, that once came from a terminal input, this function will find every function call within the
    string. The whole function, with brackets and parameters included will then be added to a command list, which will
    also be returned.
    The function will also separately append every nested function (functions, that were passed as parameters) at any
    given recursive depth.

    EXAMPLE:
    "This(This('hallo')) and That('not()')"
    > ["This(This('hallo'))", "That('not()')", "This('hallo')"]

    :param input_str: (string) the string, that is supposed to contain function calls, that have to get found
    :return: (list) a list of string, that contain the whole function calls with the bracket body
    """
    command_list = []
    string_list = stringops.split_string_structures(input_str)

    # the algorithm will go through the string list, that was separated by the "split_string_structures" function of
    # the stringops module, that returns the string contents split by whether they are enclosed by quotes or not.
    # Inside the strings, that are not 'quoted', it'll first search commands with the
    # '_find_commands_without_string_parameters(string)' function and append those to the command list.
    # Furthermore the actual procedure will count the excess opening brackets of string before the quoted string, to
    # determine how many pairs of brackets enclose the quoted part. By itering through the string in reverse the
    # functionparts to the according excess brackets are added to a temporary string. In case there are excess opening
    # brackets, evrything is added to the temporary list until there are enough (not already paired) closing brackets
    # in a further substring, so that the temp string can be added as new command

    incomplete_command = []
    excess_opening_brackets = 0
    for string in string_list:
        if not((string[0] == "'" or string[0] == '"') and (string[-1] == "'" or string[-1] == '"')):
            command_list += _find_commands_without_string_parameters(string)

            carryover = excess_opening_brackets
            if excess_opening_brackets > 0:
                bracket_balance = 0
                temporary_character_list = []
                for character in string:
                    temporary_character_list.append(character)
                    if character == "(":
                        bracket_balance -= 1
                    elif character == ")":
                        bracket_balance += 1
                        if bracket_balance == excess_opening_brackets:
                            incomplete_command.append(''.join(temporary_character_list))
                            command_list.append(''.join(incomplete_command))
                            incomplete_command = []
                            break

                incomplete_command.append(''.join(temporary_character_list))

            excess_opening_brackets = string.count("(") - string.count(")") + carryover
            if excess_opening_brackets > 0:
                temporary_character_list = []
                bracket_balance = 0
                index = -1
                while index >= -len(string):
                    character = string[index]
                    temporary_character_list.append(character)
                    if character == ")":
                        bracket_balance -= 1
                    elif character == "(":
                        bracket_balance += 1
                    if bracket_balance == excess_opening_brackets:
                        if character in ILLEGAL_CHARACTERS_FUNCTION_NOMENCLATURE:
                            temporary_character_list.reverse()
                            incomplete_command.append(''.join(temporary_character_list[1:]))
                            break
                        elif index == -len(string):
                            temporary_character_list.reverse()
                            incomplete_command.append(''.join(temporary_character_list))
                            break
                    index -= 1

        else:
            if excess_opening_brackets > 0:
                incomplete_command.append(string)

    # recursively the function will call itself, as long is it notices, that within one of its commands is another
    # command call, as it is indeed possible to use a command call as the parameter of another command as 'deep' as
    # one wants. Copying the command list before, as one cannot edit an iterator during iteration
    _command_list = command_list
    for command in _command_list:
        if stringops.count_ignore_in_quotationmarks(command, "(") > 1:
            command_list += _find_whole_commands(command[command.find("(") + 1:len(command) - 1])

    return command_list


def _find_commands_without_string_parameters(string):
    """
    If given a string, that once came from a terminal input, this function will find every function call within that
    string, under the condition, that within the body (in the brackets) of those functions there is no string. The
    whole function with every parameter and brackets will be put into an unsorted list as a substring.
    The function will also separately append every nested function (functions, that were passed as parameters) at any
    given recursive depth

    EXAMPLE:
    "This(This()) and That()"
    > ["This(This())", "That()", "This()"]

    :param string: (string) the string, that is supposed to contain function calls, without string parameters, that
                            have to get found
    :return: (list) a list of string, that contain the whole function calls with the barcket body
    """
    command_list = []

    # The algorithm will append characters to the temporary string, that is represented by the character list, until
    # it either finds a character, that couldn't be part of a function name or a opening bracket(which is the defining
    # element to identify any function). Upon finding the bracket it'll "switch modes" as indicated by the boolean state
    # variable. In this mode it'll just add every letter to the temp string, since they should be legit as parameters
    # Itll only check for brackets. Whenever it hits an opening bracket it'll ignore the next closing bracket as they'll
    # most likely belong together, but in case it hits a closing bracket, when the "bracket balance" is zero it knows,
    # that the parameter bracket is now finished, so it resets the mode and adds the now gathered temp string to the
    # command list
    temporary_character_list = []
    temporary_string_is_command = False
    bracket_balance = 0
    for character in string:
        temporary_character_list.append(character)

        # breaking the current loop stage when an illegal character has been found
        if character in ILLEGAL_CHARACTERS_FUNCTION_NOMENCLATURE and not temporary_string_is_command:
            temporary_character_list = []
            continue
        if character == "(":
            if temporary_string_is_command:
                bracket_balance -= 1
            else:
                temporary_string_is_command = True
        elif character == ")":
            if temporary_string_is_command:
                if bracket_balance == 0:
                    command_list.append(''.join(temporary_character_list))
                    temporary_character_list = []
                    temporary_string_is_command = False
                    continue
                else:
                    bracket_balance += 1
            else:
                temporary_character_list = []
                continue

    # recursively the function will call itself, as long is it notices, that within one of its commands is another
    # command call, as it is indeed possible to use a command call as the parameter of another command as 'deep' as
    # one wants. Copying the command list before, as one cannot edit an iterator during iteration
    _command_list = command_list
    for command in _command_list:
        if command.count(")") > 1 and command.count("(") > 1:
            command_list += _find_commands_without_string_parameters(command[command.find("(") + 1:len(command) - 1])

    return command_list


def _find_environmental_variables(input_string):
    """
    If given a string, that once came from a terminal input, this function will find every referenced environmental
    variable, that is not part of a string and return a list, containing the string names of there variables
    :param input_string:
    :return:
    """
    variable_list = []
    string_list = stringops.split_string_structures(input_string)
    reg = re.compile("""\$[^'".,()\-+\s=;:]+""")
    for string in string_list:
        if len(string) > 0 and not((string[0] == "'" or string[0] == '"') and (string[-1] == "'" or string[-1] == '"')):
            variable_list += re.findall(reg, string)
    return variable_list
