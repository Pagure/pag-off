# -*- coding: utf-8 -*-

"""
 (c) 2017 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>

"""

import json
import logging
import os

import arrow


_log = logging.getLogger(__name__)


def load_tickets(ticket_fold, status='Open', ticket_id=None):
    """ Load the tickets present in the specified folder, filter them with
    the given filters and return a dict of
        { ticket_id: ticket_data }

    :kwarg ticket_fold: The folder containing the JSON blobs of the tickets
        to load
    :type ticket_fold: str
    :kwarg status: The status to filter the issues returned with.
        Can be: Open, Closed or All. Defaults to 'Open'.
        This filter is un-used when searching a specifying a ticket_id.
    :type status: str
    :kwarg ticket_id: The identifier of the issue to return.
    :type ticket_id: int or str
    :return: The ticket data in a dict which key in the ticket identifier
    :rtype: dict

    """
    _log.info('Loading tickets from: %s', ticket_fold)

    tickets = {}

    for filename in os.listdir(ticket_fold):
        filepath = os.path.join(ticket_fold, filename)
        if not os.path.isfile(filepath):
            continue
        _log.debug('Loading file: %s', filepath)
        try:
            with open(filepath) as stream:
                data = json.load(stream)
        except json.decoder.JSONDecodeError:
            _log.info(
                'Could not load file: %s, continuing without', filepath)
        _id = data['id']

        if str(_id) == str(ticket_id):
            return data

        if status != 'all':
            if data['status'].lower() != status.lower():
                continue
        tickets[_id] = data

    return tickets


def humanize(date):
    """ Make the date human-friendly. """
    if date:
        return arrow.get(date).humanize()
