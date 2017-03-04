# -*- coding: utf-8 -*-

"""
 (c) 2017 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>

"""

class PagOffException(Exception):
    """ Generic exception sub-classed by all of pag-off's exceptions. """
    pass


class InvalidStatus(PagOffException, ValueError):
    """ Raised when the status specified by the user is not in the list of
    expected statuses.
    """
    pass
