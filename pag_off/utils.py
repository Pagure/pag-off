# -*- coding: utf-8 -*-

"""
 (c) 2017 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>

"""

import datetime
import json
import logging
import os
import subprocess

import arrow


_log = logging.getLogger(__name__)


def _run_shell_cmd(command, directory, return_stdout=False):
    """ Invoke the specified shall command

    """
    proc = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=directory)
    stdout, stderr = proc.communicate()
    if proc.returncode != 0:
        error_msg = ('The command "{0}" failed with "{1}"'
                     .format(' '.join(command), stderr))
        raise Exception(error_msg)
    if return_stdout:
        return stdout.strip()


def load_tickets(ticket_fold, status='Open', ticket_id=None, tags=None,
                 assignee=None, author=None, milestone=None):
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
    :kwarg tags: A list of tags the issue must have to be returned.
    :type tags: list
    :kwarg assignee: The username of the assignee of the tickets to return
    :type assignee: str
    :kwarg author: The username of the author of the tickets to return
    :type author: str
    :kwarg milestone: The milestone of the tickets to return
    :type milestone: str
    :return: The ticket data in a dict which key in the ticket identifier
    :rtype: dict

    """
    _log.info('Loading tickets from: %s', ticket_fold)

    tickets = {}

    for filename in os.listdir(ticket_fold):
        filepath = os.path.join(ticket_fold, filename)

        if not os.path.isfile(filepath):
            _log.debug(
                'Path %s does not point to a file, passing', filepath)
            continue

        if '.' in filename:
            _log.debug(
                'There is a "." in the filename, that is invalid, passing')
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
            return (data, filepath)

        if status != 'all':
            if data['status'].lower() != status.lower():
                continue

        if tags:
            ext = False
            for tag in tags:
                if tag not in data['tags']:
                    ext = True
                    break
            if ext:
                continue

        if assignee is not None:
            if not data['assignee']:
                continue
            elif data['assignee']['name'] != assignee:
                continue

        if author is not None:
            if data['user']['name'] != author:
                continue

        if milestone is not None:
            if data['milestone'] != milestone:
                continue

        tickets[_id] = data

    return tickets


def get_field_tickets(ticket_fold, field):
    """ From all the tickets present in the specified folder, return the
    list of value for the specified field.

    :arg ticket_fold: The folder containing the JSON blobs of the tickets
        to load
    :type ticket_fold: str
    :arg field: The field to search for in the tickets
    :type field: str
    :return: The values found in the ticket for the given field
    :rtype: list

    """
    _log.info('Loading tickets from: %s', ticket_fold)

    output = set()

    for filename in os.listdir(ticket_fold):
        filepath = os.path.join(ticket_fold, filename)

        if not os.path.isfile(filepath):
            _log.debug(
                'Path %s does not point to a file, passing', filepath)
            continue

        if '.' in filename:
            _log.debug(
                'There is a "." in the filename, that is invalid, passing')
            continue

        _log.debug('Loading file: %s', filepath)
        try:
            with open(filepath) as stream:
                data = json.load(stream)
        except json.decoder.JSONDecodeError:
            _log.info(
                'Could not load file: %s, continuing without', filepath)

        if field in data:
            if data[field]:
                output.add(data[field])

    return list(output)


def humanize(date):
    """ Make the date human-friendly. """
    if date:
        return arrow.get(date).humanize()


def ticket2str(ticket):
    """ Return a string to display a ticket to the user. """
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
        d = {
            'user': comment['user']['name'],
            'date': humanize(comment['date_created']),
            'comment': comment['comment']
        }
        tmpl += """
        --------------------
* {user}  -- {date}

{comment}""".format(**d)

    return tmpl


def add_comment(ticket, filepath, comment, config):
    """ Adds a given comment to the specified ticket. """
    tmpl = {
        'comment': comment,
        'date_created': datetime.datetime.utcnow().strftime('%s'),
        'edited_on': None,
        'editor': None,
        'id': None,
        'notification': False,
        'parent': None,
        'user': {
            'name': config.get('user', 'name'),
            'default_email': config.get('user', 'default_email'),
        }
    }
    ticket['comments'].append(tmpl)
    print(ticket2str(ticket))
    conf = input('Confirm comment [y/N]: ')
    if conf.lower() not in ['yes', 'y']:
        return 'canceled'

    ticket['last_updated'] = datetime.datetime.utcnow().strftime('%s')

    with open(filepath, 'w') as stream:
        stream.write(json.dumps(
            ticket, sort_keys=True, indent=4,
            separators=(',', ': '))
        )
    folder, uid = filepath.rsplit('/', 1)
    _run_shell_cmd(
        ['git', 'commit', '-m',
         'Updated issue %s: %s' % (uid, ticket['title']),
         uid
         ],
        directory=folder
    )
    return 'done'


def take_ticke(ticket, filepath, config):
    """ Assign a ticket to the current user. """
    comment = "**Metadata Update from @%s**:\n"\
        "- Issue assigned to %s" % (
            config.get('user', 'name'),
            config.get('user', 'name'),
        )

    tmpl = {
        'comment': comment,
        'date_created': datetime.datetime.utcnow().strftime('%s'),
        'edited_on': None,
        'editor': None,
        'id': None,
        'notification': True,
        'parent': None,
        'user': {
            'name': config.get('user', 'name'),
            'default_email': config.get('user', 'default_email'),
        }
    }
    ticket['comments'].append(tmpl)

    ticket['assignee'] = {
        'name': config.get('user', 'name'),
        'default_email': config.get('user', 'default_email'),
    }

    print(ticket2str(ticket))
    conf = input(
        'Confirm assigning this ticket to %s [y/N]: ' % (
            config.get('user', 'name')))
    if conf.lower() not in ['yes', 'y']:
        return 'canceled'

    with open(filepath, 'w') as stream:
        stream.write(json.dumps(
            ticket, sort_keys=True, indent=4,
            separators=(',', ': '))
        )
    folder, uid = filepath.rsplit('/', 1)
    _run_shell_cmd(
        ['git', 'commit', '-m',
         'Close issue %s: %s' % (uid, ticket['title']),
         uid
         ],
        directory=folder
    )
    return 'done'


def close_ticket(ticket, filepath, config, close_status=None):
    """ Close the specified ticket, potentially with the specified
    close_status.
    """
    comment = "**Metadata Update from @%s**:\n"\
        "- Issue status updated to: Closed (was: %s)" % (
            config.get('user', 'name'),
            ticket["status"]
        )
    if close_status:
        comment += "\n- Issue close_status updated to: %s" % (close_status)

    tmpl = {
        'comment': comment,
        'date_created': datetime.datetime.utcnow().strftime('%s'),
        'edited_on': None,
        'editor': None,
        'id': None,
        'notification': True,
        'parent': None,
        'user': {
            'name': config.get('user', 'name'),
            'default_email': config.get('user', 'default_email'),
        }
    }
    ticket['comments'].append(tmpl)

    print(ticket2str(ticket))
    t = ' '
    if close_status:
        t = ' as %s ' % close_status
    conf = input('Confirm closing this ticket%s[y/N]: ' % t)
    if conf.lower() not in ['yes', 'y']:
        return 'canceled'

    ticket['status'] = 'Closed'
    ticket['closed_at'] = datetime.datetime.utcnow().strftime('%s')
    ticket['last_updated'] = datetime.datetime.utcnow().strftime('%s')
    if close_status:
        ticket['close_status'] = close_status

    with open(filepath, 'w') as stream:
        stream.write(json.dumps(
            ticket, sort_keys=True, indent=4,
            separators=(',', ': '))
        )
    folder, uid = filepath.rsplit('/', 1)
    _run_shell_cmd(
        ['git', 'commit', '-m',
         'Close issue %s: %s' % (uid, ticket['title']),
         uid
         ],
        directory=folder
    )
    return 'done'
