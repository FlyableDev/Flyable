from flyable.data.lang_type import LangType
import flyable.data.lang_type as type


class NodeInfo:
    """
    NodeInfo supplements Python ast nodes with extra information.
    It keeps track of :
    - types
    - id
    - optimization information
    - and more
    """

    def __init__(self):
        self.__type = LangType()

    def get_type(self):
        return self.__type


# Name
class NodeInfoNameLocalVarCall(NodeInfo):
    '''
    This node info indicates that the code should use an alloca variable
    '''

    def __init__(self, var):
        self.__var = var

    def get_var(self):
        return self.__var


# Attribut call
class NodeInfoAttrCall(NodeInfo):
    '''
    This node info indicates that the code need to directly load the attribut of an object
    '''

    def __init__(self, attr):
        self.__attr = attr
        self.__type = attr.get_type()

    def get_attr(self):
        return self.__attr


class NodeInfoPythonAttrCall(NodeInfo):
    '''
    This node info indicates that the code need to call an python obj attribute
    '''

    def __init__(self, id):
        self.__id = id
        self.__type = type.get_python_obj_type()

    def get_id(self):
        return self.__id


# Func call

class NodeInfoCallBuildIn(NodeInfo):
    """
    Node representing a call to a build-in func
    """

    def __init__(self, func):
        self.__func = func

    def get_func(self):
        return self.__func


class NodeInfoCallProc(NodeInfo):
    """
    Node representing a proc call
    """

    def __init__(self, func):
        self.__func = func

    def get_func(self):
        return self.__func


class NodeInfoCallNewInstance(NodeInfo):
    """
    Node representing a call to a new instance
    """

    def __init__(self, id, impl):
        self.__id = id
        self.__impl = impl

    def get_id(self):
        return self.__id

    def get_func_impl(self):
        return self.__impl

    def get_type(self):
        return LangType(LangType.Type.OBJECT, id)


class NodeInfoCallObjFunc(NodeInfo):
    """
    Node representing a direct func call
    """

    def __init__(self, func_impl):
        self.__func = func_impl
        self.__type = func_impl.get_type()

    def get_func(self):
        return self.__func


class NodeInfoCallObjVirtualFunc(NodeInfo):
    """
    Node representing an object indirect call
    """

    def __init__(self, func_impl):
        self.__func = func_impl

    def get_func(self):
        return self.__func


class NodeInfoPyCall(NodeInfo):

    def __init__(self, id_name):
        self.__name = id_name
        self.__type = type.get_python_obj_type()

    def get_name(self):
        return self.__name


# Op call
class NodeInfoOpPythonCall(NodeInfo):
    """
    Info about an operator that calls a Python function.
    Exemple :
    a + b #  Leads to the call of __add__(a,b)
    """

    def __init__(self, name):
        self.__name = name

    def get_name(self):
        return self.__name


class NodeInfoOpPrimCall(NodeInfo):
    """
    Represents a direct primitive operation
    """

    def __init__(self, left_type, right_type):
        self.__left_type = left_type
        self.__right_type = right_type
        self.__type = left_type

        # As soon that there is a float type, the result is a float type
        if (left_type == type.get_dec_type() or right_type == type.get_dec_type()):
            self.__type = type.get_dec_type()


# Import

class NodeInfoImportPython(NodeInfo):

    def __init__(self, var):
        self.__var = var
        self.__type = var.get_type()

    def get_var(self):
        return self.__var


class NodeInfoImportPythonModule(NodeInfo):

    def __init__(self, var):
        self.__var = var
        self.__type = var.get_type()

    def get_var(self):
        return self.__var

# With
class NodeInfoWith(NodeInfo):

    def __init__(self,with_types,vars):
        self.__vars = vars
        self.__with_types = with_types

    def get_vars(self):
        return self.__vars

    def get_with_types(self):
        return self.__with_types


# Comprehension
class NodeInfoComprehension(NodeInfo):

    def __init__(self,var):
        self.__var = var

    def get_var(self):
        return self.__var