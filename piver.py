"""
USAGE:
To use the piver module as a building block for a given project one has to:

1) The Server:
It is recommended to create a new Server class, that inherits from the 'PiverServer' class, as the server itself can
then be assigned with new tasks and new properties/attributes. Far more important though is the creation of a new
handler class, inheriting from the 'PiverRequestHandler' class, which is the core class for adding new functionality.
If the developer wants to add a new remote functionality of the server, that can be called by the client, he simply has
to add the according method to the handler class (The first parameter of that method has to be reserved for the
RequestTransfer object, that triggered the method call) and define its parameters, it will automatically be called by,
when the server receives a RequestTransfer object, that specifies said method by its string name

2) The Client:
A new Client class has to be created. The client class has to inherit from the 'BaseClient' class of the piver module.
This class already provides the necessary functionality to establish a socket connection to the server if given the
ip and the port, login and obtain an authentication code and send request objects pretty easily.
A new remote functionality of the server in the form of a new method for the handler class can be called by the client,
by passing the string name of this method and a list with parameters for that method to the 'request' method of the
client object

User profiles can be extended as one wishes, as long as the original functionality of organizing the login data
(username, password) is not being shadowed.
"""
import configparser
import socketserver
import threading
import datetime
import socket
import random
import pickle
import time
import os


def get_project_path():
    """
    Reads the config file within the project folder and returns the project path, that is specified within that config
    file
    Returns:
    The string of the project path
    """
    # Creating a new config parser object to read the INI file within the project folder, from which the path to this
    # project folder is being derived
    config = configparser.ConfigParser()
    config.read("config.ini")
    project_path = config["Paths"]["project_dir"]
    return project_path

PROJECT_PATH = get_project_path()


class BaseUserProfile:
    """
    The 'BaseUserProfile' is a (abstract) base class for all further, more specific UserProfile classes. This class
    contains the most basic and required properties of a user profile, which are the username and the password.

    Attributes:
        username: The string user name, under which the user is registered on the server
        password: The string password for the users account
    """
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def get_password(self):
        """
        Returns:
        The password of the user, the profile belongs to
        """
        return self.password

    def get_username(self):
        """
        Returns:
        The username with which the profile is connected
        """
        return self.username


class UserDict(dict):
    """
    The UserDict class is a specialized dictionary class, that has to be created during the runtime of the server
    program, it manages all user profiles
    """
    def __init__(self):
        super(UserDict, self).__init__()
        pass

    def user_exists(self, username):
        """
        Checks Whether or not the user exists/ is registered in the servers database
        Args:
            username: The string of the username in question

        Returns:
        The boolean value of whether or not the user exists
        """
        # If the user existed, the username would have to be a key of the dictionary, whose assigned value would be
        # the UserProfile of the according user
        user_exists = username in self.keys()
        return user_exists

    def password_valid(self, username, password):
        """
        Checks whether or not the given password is the correct password for the given username
        Args:
            username: The string format of the username, whose password is to be checked
            password: The string format of the password in question

        Returns:
        The boolean value of whether or not the specified password is actually correct for the given username
        """
        # The methods goes on and loads the correct password, that is stored within the user profile and then compares
        # it to the password in question
        user_profile = self[username]
        stored_password = user_profile.get_password()
        if password == stored_password:
            return True
        else:
            return False


class BaseTransferObject:

    def __init__(self, authentication_code):
        self.authentication_code = authentication_code

    def get_authentication(self):
        return self.authentication_code


class LoginTransfer:
    """
    Objects of this class are being used to establish for the first communication attempt between a client program and
    the server. By sending an object of this type the user identifies himself with his username and his password to
    request an authentication code, that can be used as an temporary identifier for all further communication.
    The authentication code exists, so that the server knows which user profile to activate/edit upon receiving a
    request.

    Attributes:
        username: The string of the username of the user, requesting the authentication code
        password: The string of the password of the user requesting the authentication code
        authentication_code: Is None at first (upon creation) but gets set to the string of the authentication code
            by the server and maintains that value, when being sent back to the user
    """
    def __init__(self, username, password):
        # Assigning the given username and password as object attributes, so they are stored during the pickled socket
        # transfer
        self.username = username
        self.password = password
        # After the object has been created by the user side of the program it is being sent to the server, where a
        # authentication code is being created by the authentication guard and then added as attribute to this object
        # then the object is being sent back to the user, where the authentication code can be stored and used
        self.authentication_code = None

    def get_username(self):
        """
        Returns:
        The string of the username, of the user, that sent the login request
        """
        return self.username

    def get_password(self):
        """
        Returns:
        The string of the password of the user
        """
        return self.password

    def set_password(self, password):
        """
        Sets the password of the user profile to the new password
        Args:
            password: The string password

        Returns:
        void
        """
        self.password = password

    def get_authentication(self):
        """
        Notes:
            This method should only by called, once the object was sent back from the server, as the authentication code
            property of such an object is None, until one is being created and added by the server.
        Returns:
        The string format of the authentication code, that was created for the user.
        """
        return self.authentication_code

    def add_authentication_code(self, authentication_code):
        """
        Adds the authentication code, that was created for the user with the specified username and password, as the
        authentication_code property of the object
        Args:
            authentication_code: The string format of the authentication code, created by the authentication guard

        Returns:
        void
        """
        self.authentication_code = authentication_code


class RequestTransfer(BaseTransferObject):
    """
    The 'RequestTransfer' objects, or request objects in short, are created by the client side program and then sent
    to the server. They are created with the intention of triggering some sort of action and a response within the
    server. This requested action of the server side program is being specified by passing the request object the
    string name of a method, more specifically a method of the handler object, that is created by the server once the
    request was received and then handles the incoming communication attempt.
    If a developer now wanted to add a new remote action to the project that uses piver servers the functionality would
    only have to be implemented as a method of the handler object and then a request object with the methods name
    would have to be sent to the server. The request objects also requires the 'parameter_list' parameter, which is
    a list of all the positional parameters, that should additionally be added to the method call of the handler.
    Once the action within the server side program has been successfully executed, a response of some sort will have
    been created. This response is then added to the request object and the object is being send back to the client,
    where the response can be read.

    Attributes:
        authentication_code: The string authentication code of the client object, that created the request object
        request_subject: the string method name of the method of the handler object to be called
        parameter_list: The list of all the positional parameters to be added to the method call
    """
    def __init__(self, authentication_code, request_subject, parameter_list):
        super(RequestTransfer, self).__init__(authentication_code)
        self.request_subject = request_subject
        self.parameters = parameter_list
        self.response = None

    def add_response(self, response):
        """
        The response to the initial RequestTransfer object sent to the server does not contain a response. Its
        'response' property is empty. The response is being created by the server side program, then added to the object
        and the object is being sent back to the client, now containing the response.
        This method is for the server to add the generated response to the object.
        Args:
            response: whatever object the server uses as a response to the initial request

        Returns:
        void
        """
        self.response = response

    def get_method_name(self):
        """
        The RequestTransfer object is being created by the client side program, it will contain the information about
        the 'request_subject', which essentially is the name of the method of the RequestHandler object, that is to be
        called within the server side program.
        Therefore this method returns exactly this method name, which is the subject of the request
        Returns:
        The string of the method name
        """
        return self.request_subject

    def get_parameter_list(self):
        """
        Since many of the RequestHandlers methods processes are dependant on additional parameters, those parameters
        can also be passed to the server by putting them (IN ORDER) into a parameter list, that is also being
        transported with the RequestTransfer object.
        Returns:
        The list, containing all the POSITIONAL arguments of the method to call
        """
        return self.parameters

    def get_response(self):
        """
        The response to the initial RequestTransfer object sent to the server does not contain a response. Its
        'response' property is empty. The response is being created by the server side program, then added to the object
        and the object is being sent back to the client, now containing the response.
        This method returns the value of the objects attribute 'response'. Should only be called after the object came
        back from the server, as the attribute will be None before.
        Returns:
        Whatever object the server created as response to the initial request
        """
        return self.response


class PiverClient:
    """
    The base class for all further, individual client classes. The client object is an object that has to be created and
    alive during the runtime of the client side program of a piver project. The client essentially manages all
    communication with the server and is supposed to wrap more complex interactions between client and server into
    simple methods.
    To really use a client object it has to be created and then logged into the server system by calling the 'login'
    method with the username and password of the registered user, by doing so the client obtains a authentication
    code, that is required by any tranfer object sent through the socket connection, so that the server can identify
    which request to execute for which user, without the client having to transmit the sensitive login information.
    The client requires the server ip and the server to establish socket connections
    """
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.authentication_code = None

    def login(self, username, password):
        """
        This method attempts to log into the server using the users data, that is specified by the username and the
        password. A LoginTransfer object is being sent to the server and in response a authentication code is being
        created and sent back as a response. The authentication code is then being assigned as the value to the clients
        'authentication_code' property and also returned. The authentication code is being used as a temporary
        identifier, that has to be sent with every following communication with the server, so the server knows
        which request belongs to which user and which users profile is to be modified.

        Raises:
            ConnectionRefusedError: In case the username is not registered in the server database
            PermissionError: In case the password is not correct

        Args:
            username: The string of the username
            password: The string of the password

        Returns:
        The string of the authentication code
        """
        # Creating the 'LoginTransfer' object, that signals the server, that the sent request is an attempted login
        # for obtaining an authentication code for the specified user.
        login_transfer = LoginTransfer(username, password)
        # Sending the object and getting the response from the send method. The response is supposed to be the very
        # same object, that was sent, only with the now created authentication code added
        login_transfer_response = self.send(login_transfer)
        authentication_code = login_transfer_response.get_authetication()
        self.authentication_code = authentication_code
        return authentication_code

    def download_file(self, relative_server_path, save_path, blocking=False):
        """
        Downloads a file from the server.
        Sends a request for the file download, which triggers the server to check for the existance of the file,
        specified by 'relative_server_path'. If the file exists the server acquires an open port and starts a
        'FileSendServer' on it and sends the port of the server as a response back to the client.
        The client then starts a 'ClientFileDownloader' object(thread) that automatically downloads the file and saves
        it as specified by 'save_path'. The method can be blocking, meaning it waits till the download is finished, or
        starts it and lets it run as a thread
        Args:
            relative_server_path: The string path that specifies the file to download. The path is supposed to be
                relative to the servers main folder, meaning that files, that dont belong to the server cannot be
                downloaded.
            save_path: The string path to where the file is supposed to the saved to. In case the path does not
                refer to an already existing file, the file is being created.
            blocking: The boolean value of whether or not the method is supposed to wait till the download is finished
                or not
        Returns:
        The string path of the saved file
        """
        # Requesting the 'download_file' method of the server, that checks for the existence of the file and opens a
        # FileSendServer for the requested file in case the path was correct
        file_server_port = self.request("download_file", relative_server_path)
        # Creating a downloader object, that automatically downloads the file from the FileSendServer, that has been
        # started at the server side program
        downloader = SimpleClientFileDownloader(self.server_ip, file_server_port, save_path)
        downloader.start()
        if blocking:
            # Waiting for the receiving process to finish in case the method was set to be blocking
            downloader.wait()

        # returning the full file path of the received file
        return save_path

    def request(self, method_name, parameter_list):
        """
        This method will create a 'RequestTransfer' object and send it to the server, using the authentication of the
        client object (An error will be raised in case no authentication has been obtained up to call of this method).
        The request system works by specifying a method of the servers RequestHandler object by its string name, that
        is supposed to be executed in the server side program. The 'parameter_list' parameter gives the option to pass
        the additional parameters to the method of the servers handler object.
        Once the handler object successfully executed the requested method, a response of some sort will have been
        created and is then being sent back to the client and this response is also being returned by this method

        Args:
            method_name: The string name of the method of the handler object to be called
            parameter_list: The list containing the positional arguments to this method in order

        Returns:
        Whatever the response to the specific request was
        """
        # Calling the 'check_login' method to check whether or not the client object already obtained the necessary
        # authentication code, raises an exception in the case there is no authentication code yet
        self.check_login()
        # Creating the 'RequestTransfer' object, to send to the server
        request_transfer = RequestTransfer(self.authentication_code, method_name, parameter_list)
        request_transfer_response = self.send(request_transfer)
        # returning the response
        return request_transfer_response.get_response()

    def send(self, obj, timeout=10):
        """
        Creates a socket, that connects to the PiverServer, by using the IP and the port attributes of the object and
        then sends the given object pickled, as a byte sequence through the given socket to the server. The method will
        then instantly wait for the server to make a response through the very same socket connection and returns the
        response as a BYTE SEQUENCE.

        Raises:
            socket.SO_ERROR: The socket error is being fetched by a try except statement, so that the socket can be
                properly closed first, but the very same error is then raised again, so that the higher level
                functionality can handle its occurrance properly
            Exception: The socket connection works by the user sending a specific transfer object to accomplish/trigger
                a specific task within the server side program, which in turn then sends back a response.
                In case the initial request was faulty though the server would send back some sort of Exception object,
                describing the error, that occured during the processing of the request.
        Args:
            obj: The object to be send through the socket to the server
            timeout: The amount of time in seconds, after which the connect should be terminated

        Returns:
        A byte sequence, that has been received in response to the sent object. Byte sequence is most likely a
        pickled object.
        """
        # Pickling the passed object into a byte sequence, setting up the socket with the server information given from
        # the objects attributes and then connects to the server
        pickled_object = pickle.dumps(obj)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        server_tuple = self._get_server_tuple()
        sock.connect(server_tuple)

        # Sends the pickled object through the socket and then instantly waits for the server response
        try:
            sock.sendall(pickled_object)
            response = sock.recv(8192)
        except socket.SO_ERROR as error:
            sock.close()
            raise error

        sock.close()
        # In case the received object was an exception, indication that an error occurred during the processing of the
        # initial request, the exception will be risen
        self._raise_exception(response)

        return response

    def check_login(self):
        """
        Checks whether the client object is logged into the server system or not. More specifically: Checking whether
        the client object posses an authentication code, that is needed for all communication with the server.
        Raises a PermissionError in case the client is not logged in.
        This method is supposed to be called before calling any other method, that sends transfer objects, that rely on
        valid authentication codes.
        Returns:
        void
        """
        if not self.is_logged_in():
            error_message = "The client does not have a authentication code. Log in first!"
            raise PermissionError(error_message)

    def is_logged_in(self):
        """
        Returns:
        The boolean value of whether the client is logged into the server system, meaning the client posses an
        authentication code
        """
        authentication_code_exists = self.authentication_code is not None
        return authentication_code_exists

    def _get_server_tuple(self):
        """
        Simply assembles the server information given, which is the server ip address and the server port into a tuple,
        which is needed for the socket connections
        Returns:
        The tuple, whose first item is the server ip address as string and the second is the server port as int
        """
        server_tuple = (self.server_ip, self.server_port)
        return server_tuple

    @staticmethod
    def _raise_exception(received_object):
        """
        The socket connection works by the user sending a specific transfer object to accomplish/trigger a specific
        task within the server side program, which in turn then sends back a response.
        In case the initial request was faulty though the server would send back some sort of Exception object,
        describing the error, that occured during the processing of the request.
        This method has to be called on the received object, as it will raise the exception in case it is one.
        Args:
            received_object: The received object, that came back as the response to the initial request

        Returns:
        void
        """
        if isinstance(received_object, Exception):
            raise received_object


class AuthenticationGuard:
    """
    The AuthenticationGuard object is one of the main instances during the server runtime. It is created on server
    startup and does not require/load any data from memory. The AuthenticationGuard stores and manages the
    authentication code system.
    Whenever a user wants to communicate/connect with the server system for the first time, the profile information
    (username and password) have to be transmitted, the server then creates a individual authentication code for the
    user, which the user side program has to use as a prefix to all requests, so that the user does not have to enter
    his info all the time, and that the server knows for whose user profile the incoming request are supposed to be
    processed.

    THE CODE
    The code itself consists of two separate parts, that are being separated by a double point ":".
    The first part simply is a random number in the range from 1 to 1000, turned into a hexadecimal value, to add
    a safety buffer, so that each code is individual.
    The second part is a timestamp integer code, from the python "datetime" module, that describes the time exactly
    24 hours into the future from the moment of creating the code. The timestamp is also turned into a hexadecimal
    in an attempt to save space. The timestamp functions as an expiration date, after which the code cannot be used
    anymore and the user has to login to get a new one.

    Aside from providing the creation and storage of the existing codes, the AuthenticationGuard also manages, the
    reference of which codes have been assigned to which users, that means that a RequestHandler has to consult the
    Guard object, to obtain the username, from which the request came. The Guard object also contains the functionality
    to counter check for the validity of those codes

    Attributes:
        existing_codes: The list, that contains the codes that are currently active
        user_dictionary: The dictionary, that contains the reference of which user is in possession of which
            authentication code, the codes being the keys and the usernames being the values to them

    """
    # The amount of time a authentication code is considered to be valid, beginning from the moment of creation
    CODE_LIFETIME_HOURS = 24

    def __init__(self):
        # The object will keep track of the already existing codes by storing all existing codes within this list
        self.existing_codes = []

        # This dictionary will contain information about which code was distributed to which user. The keys will be the
        # string versions of the given authentication code and the assigned value will be the username of the user,
        # currently in possession of the code
        self.user_dictionary = {}

    def create_authentication_code(self, username):
        """
        Creates a authentication code for the user, whose username was passed to the method. Authentication codes are
        part of the authentication process of the PiLearn Server system. After the user submits username/password on a
        one time occasion, the server sends a created authentication code in response, which the user side program
        has to use as a prefix to all requests, so that the user does not have to enter his info all the time, and that
        the server knows for whose user profile the incoming request are supposed to be processed.

        THE CODE
        The code itself consists of two separate parts, that are being separated by a double point ":".
        The first part simply is a random number in the range from 1 to 1000, turned into a hexadecimal value, to add
        a safety buffer, so that each code is individual.
        The second part is a timestamp integer code, from the python "datetime" module, that describes the time exactly
        24 hours into the future from the moment of creating the code. The timestamp is also turned into a hexadecimal
        in an attempt to save space. The timestamp functions as an expiration date, after which the code cannot be used
        anymore and the user has to login to get a new one.

        EXAMPLE
        authentication code: '0x21f:0x57e76895'

        Args:
            username: The username string, for which the authentication code is being created

        Returns:
        The string of the created authentication code
        """
        is_valid = False
        authentication_code = ""
        while not is_valid:
            # The authentication code consists of two separate parts. The first part is a randomly generated integer in
            # the in the range from 1 to 1000 turned into a hexadecimal. The second part is a timestamp, that is created
            # to reflect the time exactly 24 hours after the moment in which the code was created. The timestamp
            # functions not only as a definite identifier, but also as an expire date for the authentication code.
            # The timestamp is also being turned into a hexadecimal, in the attempt to save digits
            random_number = hex(random.randint(1, 1000))

            # Creating the current datetime object and adding a timedelta of 24 hours
            current_datetime = datetime.datetime.now()
            future_datetime = current_datetime + datetime.timedelta(hours=self.CODE_LIFETIME_HOURS)
            # The timestamp is being concerted to integer before being converted to hex, because the timestamp is a
            # float number and hex() doesnt convert floats. The information resolution of the timestamp after the
            # int conversion still correctly reflects seconds
            future_datetime_timestamp = hex(int(future_datetime.timestamp()))

            authentication_code = "{}:{}".format(str(random_number), str(future_datetime_timestamp))
            if authentication_code not in self.existing_codes:
                is_valid = True

        # Adding the authentication code to the list of already existing codes, so that users will not get the same
        # code and adding the username reference to the dictionary of users, currently possessing a authentication code.
        self.existing_codes.append(authentication_code)
        self.user_dictionary[authentication_code] = username

        return authentication_code

    def user_exists(self, username):
        """
        Args:
            username: The string format of the username in question

        Returns:
        The boolean value of whether or not a user with the given username currently possesses am authentication code
        """
        if username in self.user_dictionary:
            return True
        else:
            return False

    def is_valid_authentication(self, authentication_code):
        """
        Checks whether or not the passed authentication code is still valid or not, by converting it back into the
        datetime object, that was stored within the code (which was created to last for 24 hours, back at the point of
        creation). If the code's datetime is still bigger than the current datetime, returns True, otherwise deletes
        the code from internal reference and returns False.
        Args:
            authentication_code: The string authentication code, that is to be checked

        Returns:
        The boolean value of whether or not the authentication code is still valid
        """
        # Converting the given code into the datetime object, that was stored within the code and then comparing it to
        # the current datetime object. In case it is bigger, the code is not expired yet and the method returns True.
        # Otherwise the code will be deleted from the list and the dictionary and the method will return False
        code_datetime = self.get_datetime_from_authentication_code(authentication_code)
        current_datetime = datetime.datetime.now()

        if code_datetime > current_datetime:
            return True
        else:
            self.existing_codes.remove(authentication_code)
            del self.user_dictionary[authentication_code]
            return False

    def get_username(self, authentication_code):
        """
        Gets the username, that was assigned to the given authentication code from the internal dictionary reference
        Args:
            authentication_code: The string authentication code for which the username is requested

        Returns:
        The username, to the user, which is currently in possession of the passed authentication code
        """
        # The method checks whether the code exists or not, but there is no consequence in case it doesnt, because
        # there would not be a situation in which a unknown authentication code would have been used.
        # TODO: add exception anyways
        if authentication_code in self.user_dictionary.keys():
            return self.user_dictionary[authentication_code]

    def get_authentication_code(self, username):
        """
        Searches for the username in question to be part of the internal dictionaries values and returnes the according
        key (authentication code) once found.
        Args:
            username: The string format of the username for which to return the authentication code for

        Returns:
        The string format of the authentication code
        """
        # Simply iterates through the dictionary values, which are the user names and if the given username is the same
        # as a username of the dictionary, the key (code) belonging to that user will be returned.
        for authentication_code in self.user_dictionary.keys():
            current_username = self.user_dictionary[authentication_code]
            if current_username == username:
                return authentication_code
        # If the loop terminating, without anything being returned raising a KeyError to be handled
        raise KeyError("The user '{}' does not posses an authentication code!")



    @staticmethod
    def get_timestamp_from_authentication_code(authentication_code):
        """
        Converts the given authentication code string into the datetime timestamp integer, that was being stored within
        the code
        Args:
            authentication_code: The string of the authentication code, that is to be converted into a timestamp

        Returns:
        The integer timestamp, that was stored inside the code. The expiration date of the code
        """
        # Splitting the code by its separator to get the two segments individually, then first converting the second
        # part from string to hex(base 16) and then to integer
        code_segments = authentication_code.split(":")
        code_timestamp = int(int(code_segments[1], 16))
        return code_timestamp

    @staticmethod
    def get_datetime_from_authentication_code(authentication_code):
        """
        Converts the given authentication code string into the datetime object, that was being stored within
        the codes timestamp
        Args:
            authentication_code: The string of the authentication code, that is to be converted into datetime object

        Returns:
        The datetime object, whose information was stored inside the code. The expiration date of the code
        """
        code_timestamp = AuthenticationGuard.get_timestamp_from_authentication_code(authentication_code)
        code_datetime = datetime.datetime.fromtimestamp(code_timestamp)
        return code_datetime


class PiverServer(socketserver.TCPServer, socketserver.ThreadingMixIn):
    """
    The PiLearnServer class is a subclass of the socketserver.TCPServer class from the python 'socketserver' module.
    The socketserver module wraps the functionality of python sockets into a slightly higher level server object/
    application, that deals with TCP socket connections on its own and the developer using it just has to pass the
    connection information (ip, port) and a HandlerClass to the server object.
    The handler class then simply defines a 'handle()' method, that deals with all incoming connections to the server.

    Because the PiLearnServer also inherits from the socketserver.ThreadingMixIn, it additionally has the
    functionality that the server spawns a new handler Thread for each incoming request/connection

    The PiLearnServer specifically also requires a reference to the instance of the AuthenticationGuard object, which
    is used to assign individual authentication codes to the users login in. With those codes the requests of a user
    can be identified and used to modifiy his profile information only. Codes are checked for validity, as they expire
    after some time

    Notes:
        To use the PiLearnServer it has to be created by passing it the server address a reference to what handler class
        to use and the currently active AuthenticationGuard object.
        The server is started by calling the 'server_forever' method and is terminated, by te the 'shutdown' method.
        It also has to be closed by calling the 'server_close' method

    Examples:
        # Example on how to use the server
        authentication_guard = AuthenticationGuard()
        server = PiLearnServer(('localhost', 5000), PiLearnHandler, authentication_guard)
        server.serve_forever()
        # ...the server handles all the requests
        server.shutdown()
        server.server_close()

    Attributes:
        server_address: A tuple, whose first element is the string ip address of the server, mostly localhost, and the
            second element being an integer, that dictates, to which port the server is supposed to bind
        RequestHandlerClass: A reference to the class, that handles the incoming connections and the data
        authentication_guard: The AuthenticationGuard object for the server, to manage the indivudual user codes
    """
    def __init__(self, server_address, RequestHandlerClass, authentication_guard, user_dict, port_manager,
                 bind_and_activate=True):
        # Initializing the actual Server class from the python 'socketserver' module and also adding the attribute of
        # the authentication guard, to make it available within the handling method later
        super(PiverServer, self).__init__(server_address, RequestHandlerClass, bind_and_activate=bind_and_activate)
        self.authentication_guard = authentication_guard
        self.user_dict = user_dict
        self.port_manager = port_manager


class PiverRequestHandler(socketserver.BaseRequestHandler):

    def __init__(self, request, client_address, server):
        # IMPORTANT INFO:
        # The following code of this constructor method is the original code used within the  python 'socketserver'
        # module to instantiate the a BaseRequestHandler. The system the actual TCP server finishes a request is by
        # simply instantiating the Handler class and passing it the information of the request, the client_address
        # and a instance of the server itself
        self.request = request
        self.client_address = client_address
        self.server = server
        self.setup()
        try:
            self.handle()
        finally:
            self.finish()

        # Now begins the new code:
        # Considering the object behind the server attribute is an instance of the PiLearnServer class, the
        # authentication guard object could be accessed via the server object, but the reference to the authentication
        # guard object is additionally being wrapped into an attribute of this very class, simplifying access
        self.authentication_guard = self.server.authentication_guard
        self.user_dict = self.server.user_dict
        self.port_manager = self.server.port_manager

    def handle(self):
        # Waiting for the data of any of the users clients to be received
        data = self.request.recv(4096)

        # As the protocol dictates everything that passes this socket connection has to be serialized/pickled object
        # of some sort, the received data is being loaded with the pickle module
        try:
            received_object = pickle.loads(data)
        except pickle.UnpicklingError as error:
            # TODO: add behaviour for unpinklling error
            pass

        # Checking whether or not the received request is a first time login attempt or an actual action request
        # of an already authenticated user.
        # In case the received object is indeed a login request calls the 'login' method, that processes the transfer
        # object and generates the appropriate response object
        if isinstance(received_object, LoginTransfer):
            response = self.login(received_object)

        else:
            # First getting the authentication of the sent object (the protocol dictates, that every object passing this
            # socket connect has to inherit from the BaseTransferObject class and thus contain the information about the
            # authentication code and methods to obtain this information
            authentication_code = received_object.get_authentication()
            is_valid = self.authentication_guard.is_valid_authentication(authentication_code)
            if not is_valid:
                # TODO: What to to in case the authentication code is not valid anymore
                pass

            # Now checking for the object type to determine to which sub-handling method to redirect the object to
            if isinstance(received_object, RequestTransfer):
                # In case the object is a request object, the handler object will redirect the processing of the
                # received object to the designated method
                response = self.handle_request(received_object)

        # sending the generated response back to the client
        pickled_response = pickle.dumps(response)
        self.request.sendall(pickled_response)

    def login(self, login_transfer):
        """
        The method which processes the received requests from the socket connection, that turn out to be login requests
        from the sending clients. Login requests are represented by the 'LoginTransfer' objects. They contain the
        information about the username and the password, that the user had entered on the client side of the
        connection, after verifying, that both the username and password exist and are correct, the method creates a
        authentication code by calling the AuthenticationGuard, creates the reference from this individual code to the
        username, adds the fresh authentication code to the LoginTransfer object and returns that object, so it can
        be sent back to the client side as a response

        Notes:
            Could return:

            ConnectionRefusedError: In case the method gets passed a LoginTransfer object with a username, that is not
                registered in the servers system
            PermissionError: In case the method gets passed a LoginTransfer object, whose username exists, but whose
                password is not correct (The password doesnt match with the password, that was stored in the servers
                memory)

        Args:
            login_transfer: The 'LoginTransfer' object, that was received and now is to be processed

        Returns:
        The same 'LoginTransfer' object, that was passed, but having added the created, individual authentication code
        to it, that the user can use
        """
        username = login_transfer.get_username()
        password = login_transfer.get_password()
        # First checks whether the user actually exists or not by calling the user dict object.
        # The user dict object stores the reference to all existing user profiles with them being the values to the
        # usernames as keys.
        # In case the user does not exists, returns a ConnectionRefusedError to send back as an response to who ever
        # attempted to login with an non existent username
        user_exists = self.user_dict.user_exists(username)
        if not user_exists:
            error_message = "The username '{}' does not exist!".format(username)
            return ConnectionRefusedError(error_message)

        # In case the username existed, the validity of the password to the username is now being checked.
        # In case the password is not correct, returns a PermissionError to send back as an response to the user,
        # to whom the username belongs
        password_valid = self.user_dict.password_valid(username, password)
        if not password_valid:
            error_message = "The password for the given username '{}' is not correct".format(username)
            return PermissionError(error_message)

        # If the login request came from a user, that already posses an authentication code, that is valid simply
        # sending the stored one to the user again, instead of creating a new one
        if self.authentication_guard.user_exists(username):
            authentication_code = self.authentication_guard.get_authentication_code(username)
            login_transfer.add_authentication_code(authentication_code)

        else:
            # Creating the code authentication code and adding it to the LoginTransfer object before returning that
            # object to be sent back to the client side program fro the user to utilize.
            authentication_code = self.authentication_guard.create_authentication_code(username)
            login_transfer.add_authentication_code(authentication_code)

        return login_transfer

    def handle_request(self, received_object):
        """
        This method is the first instance of handling the incoming requests. Those 'RequestTransfer' objects, that are
        passed to this method, contain a authentication code, so the following processes know which user to assign the
        action, they contain the string name of a method of handler object and a list with parameters to pass to this
        method.
        This method uses the method name string and the parameter list to actually call the requested method and return
        the response, that has been returned by this specific method
        Args:
            received_object: The 'RequestTransfer' object specifying, which method to call

        Returns:
        The response, that has been generated by the method, that was requested
        """
        # Getting the string method name of the method that is supposed to be called and checking whether such a method
        # even exists or not. In case the method does not exists, this method will return
        method_name = received_object.get_method_name()
        method_exists = hasattr(self, method_name)
        if not method_exists:
            error_message = "The server RequestHandler does not support a method named '{}'".format(method_name)
            return AttributeError(error_message)

        parameter_list = received_object.get_parameter_list()
        # Calling the specified method of the this handler object with the parameters from the parameter list.
        # Excepting a TypeError due to a possibly wrong amount or wrong type of passed parameters
        method = getattr(self, method_name)
        try:
            response = method(received_object, *parameter_list)
            received_object.add_response(response)
        except Exception as error:
            return error

        # Returning the response, that was generated by the method, that was called through the request
        return received_object

    def change_password(self, received_object, password):
        """
        Changes the password of the user to the new password
        Args:
            received_object:
            password: The new password string

        Returns:
        The new password string
        """
        user_profile = self.get_user_profile(received_object)
        user_profile.set_password(password)
        return password

    def download_file(self, received_object, relative_server_path):
        """
        The method being called, when a user request to download a file, specified by the path 'relative_server_path'.
        The method checks whether the requested file exists (raises an error in case it doesnt) acquires an open port
        from the port manager, starts a FileSendServer with the file and the port and sends the port of the server
        back to the user as a response
        Args:
            received_object: -
            relative_server_path: The string path that specifies the file to download. The path is supposed to be
                relative to the servers main folder, meaning that files, that dont belong to the server cannot be
                downloaded.

        Returns:
        The integer port number on which the file server is listening for an incoming connection of a downloader
        """
        # Getting the user profile of the user, which sent the request
        user_profile = self.get_user_profile(received_object)

        # This method is in charge of initializing the download of a file from the server to the client. The
        # 'relative_server_path' parameter is supposed to contain the string path of the file which is meant to be
        # downloaded by the client, the path being relative to the server programs main directory though.
        # Creating the absolute path of the requested file, by joining the project path with the relative server path
        file_path = os.path.join(PROJECT_PATH, relative_server_path)
        file_exists = os.path.isfile(file_path)
        if not file_exists:
            raise FileNotFoundError("The requested file at '{}' does not exist".format(file_path))

        # Acquiring an open port from the port manager and starting an open FileSendServer, to wait for an incoming
        # socket connection from the client
        port = self.port_manager.acquire()
        file_server = SimpleFileSendServer(port, file_path)
        file_server.start()

        # Sending the port of the file server back to the client, so that the client can start a downloader thread,
        # connecting to the file server, that downloads the file
        return port

    def get_username(self, received_object):
        """
        First gets the authentication code from the received object and then passes the code to the authentication
        guard to get and return the username associated with the authentication code/request
        Args:
            received_object:

        Returns:
        The string username of the user, from which the request object was sent
        """
        authentication_code = received_object.get_authentication()
        username = self.authentication_guard[authentication_code]
        return username

    def get_user_profile(self, received_object):
        """
        Gets the authentication code from the received object, then passes the code the the authentication guard to get
        the username and then passes the username to the user dictionary to get the actual 'UserProfile' object, which
        is then returned
        Args:
            received_object:

        Returns:
        The 'UserProfile' object, that belongs to the user, that sent the request
        """
        username = self.get_username(received_object)
        user_profile = self.user_dict[username]
        return user_profile


class SimpleClientFileDownloader(threading.Thread):
    """
    This object enables the download of file from a server to a client. The clients ip does not have to be know to the
    server, only the servers public host address and the used port have to be known to the client. Also on the server
    side there has to be running a 'SimpleFileSendServer' (more specifically one for every downloading client), that
    listens on the specified port. The client will go on and establish a connection to the server and repeatedly send
    little ping packages, to which the server responds with chunks of ~1KB of the files data until all the data
    has been transferred to the client.

    Attributes:
        server_ip: The string, containing the servers IP address or hostname
        server_port: The port on which the "SimpleFileSendServer" is running on the server
        file: The file open() object in byte mode
        receiving: The boolean value of whether or not the client is currently receiving data

    Args:
        server_ip: The string, containing the servers IP address or hostname
        server_port: The port on which the "SimpleFileSendServer" is running on the server
        file_path: The string path to the file, into which the received data is to be saved in. If the path does not
            refer to an already existing file, a file will be created (in case the folder structure exists)
    """
    def __init__(self, server_ip, server_port, file_path):
        threading.Thread.__init__(self)
        self.server_ip = server_ip
        self.server_port = server_port

        # Creating the file object in byte mode and with the permission to create a new file if none already exists
        self.file = open(file_path, mode="wb+")

        self.receiving = False

    def run(self):
        address_tuple = (self.server_ip, self.server_port)
        self.receiving = True

        # Creating the socket object and connecting it it the server
        sock = socket.socket()
        sock.connect(address_tuple)

        try:
            while self.receiving:
                # Sending a short message through the socket, so the server side program knows when a new cycle begins
                sock.sendall(b"ok")
                # receiving the actual data chunk of the file and writing it to the file object
                data = sock.recv(1024)
                self.file.write(data)
        except Exception as e:
            pass
        finally:
            # Closing the socket and the file
            sock.close()
            self.receiving = False
            self.file.close()

    def wait(self):
        """
        Upon being called simply blocks the program flow until the full file has been received
        Returns:
        void
        """
        while self.receiving:
            time.sleep(0.01)


class SimpleFileSendServer(threading.Thread):
    """
    This object enables the download of a file from the server to a client.The clients ip does not have to be know to
    the server, only the servers public host address and the used port have to be known to the client. This object has
    to be created and running on the server side. If a "SimpleClientFileDownloader" is then created and started within
    a client and connects to this server by addressing the correct port, a connection is being established. The client
    will then send little ping messages, to which this server responds with chunks (~1KB) of the files data.

    Attributes:
        ip: The localhost address string
        port: The integer port on which this server is listening
        file: The byte reading open()-fileobject of the file to be sent
        sending: The boolean value of whether or not the server is currently sending data

    Args:
        port: The port, on which the server is supposed to listen on
        file_path: The string path to the file that is supposed to be sent
    """
    def __init__(self, port, file_path):
        threading.Thread.__init__(self)
        self.ip = "localhost"
        self.port = port

        self.file = open(file_path, "rb")

        self.sending = False

    def run(self):
        # Creating a socket object and setting it up to act as a server on the local host ip and the given port,
        # accepting only the first incoming connection request as this whole objects purpose is only to transfer one
        # single file and for that only one connection/socket is needed
        address_tuple = (self.ip, self.port)
        sock = socket.socket()
        sock.bind(address_tuple)
        sock.listen(5)

        connection, address = sock.accept()
        self.sending = True

        try:
            while self.sending:
                # first waiting to receive something from the client to know when it is ready and then reading and
                # sending the next chunk of the file
                connection.recv(1024)
                data = self.file.read(1024)
                if not data:
                    self.sending = False
                connection.send(data)
        except Exception as e:
            pass
        finally:
            # closing the file and the socket
            self.sending = False
            connection.close()
            self.file.close()


class PortManager(list):

    def __init__(self, port_range):
        list.__init__(self, port_range)

    def acquire(self):
        self.pop(0)

    def release(self, port):
        self.append(port)
