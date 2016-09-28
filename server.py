import configparser
import socketserver
import threading
import datetime
import socket
import random
import pickle


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


class UserProfile:

    def __init__(self, username, password, progresses):
        self.username = username
        self.password = password

    def get_password(self):
        """
        Returns:
        The password of the user, the profile belongs to
        """
        return self.password


class UserDict(dict):

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

class RequestObject(BaseTransferObject):

    def __init__(self, authentication_code, request_subject, parameter_list):
        super(RequestObject, self).__init__(authentication_code)
        self.request_subject = request_subject
        self.parameters = parameter_list


class PiLearnClient:

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

    def send(self, obj, timeout=10):
        """
        Creates a socket, that connects to the PiServer, by using the IP and the port attributes of the object and then
        sends the given object pickled, as a byte sequence through the given socket to the server. The method will then
        instantly wait for the server to make a response through the very same socket connection and returns the
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


class PiLearnServer(socketserver.TCPServer, socketserver.ThreadingMixIn):
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
    def __init__(self, server_address, RequestHandlerClass, authentication_guard, user_dict, bind_and_activate=True):
        # Initializing the actual Server class from the python 'socketserver' module and also adding the attribute of
        # the authentication guard, to make it available within the handling method later
        super(PiLearnServer, self).__init__(server_address, RequestHandlerClass, bind_and_activate=bind_and_activate)
        self.authentication_guard = authentication_guard
        self.user_dict = user_dict


class TCPRequestHandler(socketserver.BaseRequestHandler):

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

            response = ""
            # Now checking for the object type to determine to which sub-handling method to redirect the object to
            if isinstance(received_object, RequestObject):
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
            error_string = "The username '{}' does not exist!".format(username)
            return ConnectionRefusedError(error_string)

        # In case the username existed, the validity of the password to the username is now being checked.
        # In case the password is not correct, returns a PermissionError to send back as an response to the user,
        # to whom the username belongs
        password_valid = self.user_dict.password_valid(username, password)
        if not password_valid:
            error_string = "The password for the given username '{}' is not correct".format(username)
            return PermissionError(error_string)

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
        pass



