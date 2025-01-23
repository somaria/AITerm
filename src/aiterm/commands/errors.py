"""
Custom exceptions for command handling
"""

class CommandError(Exception):
    """Base class for command-related exceptions"""
    pass

class CommandInterpretationError(CommandError):
    """Raised when there is an error interpreting a command"""
    pass

class CommandExecutionError(CommandError):
    """Raised when there is an error executing a command"""
    pass

class CommandNotFoundError(CommandError):
    """Raised when a command is not found"""
    pass

class CommandPermissionError(CommandError):
    """Raised when there are insufficient permissions to execute a command"""
    pass
