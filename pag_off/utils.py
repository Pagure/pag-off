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


def ticket2str(ticket):
    """ Return a string to display a ticket to the user. """
    #print(ticket)
    tmpl = """#{id}: {title}

From:       {user}
Date:       {date_created}
Tags:       {tags}
Assignee:   {assignee}
Private:    {private}
Status:     {status}
Priority:   {priority}
Blocks:     {blocks}
Depends:    {depends}
Milestone:  {milestone}
Last update:{last_updated}

{content}""".format(**{
        'id': ticket['id'],
        'title': ticket['title'],
        'date_created': humanize(ticket['date_created']),
        'user': ticket['user']['name'],
        'tags': ', '.join(ticket['tags']),
        'assignee': ticket['assignee']['name'] if ticket['assignee'] else '',
        'private': ticket['private'],
        'status': ticket['status'],
        'priority': ticket['priority'],
        'blocks': ', '.join(ticket['blocks']),
        'depends': ', '.join(ticket['depends']),
        'milestone': ticket['milestone'],
        'last_updated': humanize(ticket['last_updated']),
        'content': ticket['content'],
    })

    for comment in ticket['comments']:
        tmpl += """
        --------------------

* {user}  -- {date}

{comment}
""".format(**{
    'user': comment['user']['name'],
    'date': humanize(comment['date_created']),
    'comment': comment['comment'],
    })

    return tmpl
