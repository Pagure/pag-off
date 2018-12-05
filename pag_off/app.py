# -*- coding: utf-8 -*-

"""
 (c) 2016-2017 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>

"""

import argparse
import configparser
import logging
import os
import sys

from tabulate import tabulate

import pag_off.exceptions
import pag_off.utils


_log = logging.getLogger(__name__)

CONFIGS = [
    '/etc/pag-off.conf',
    os.path.expanduser('~/.config/pag-off.conf'),
    os.path.join(os.getcwd(), 'pag-off.conf')
]

MIN_CONFIG = {
    'main': ['base_url', 'location'],
    'user': ['name', 'default_email']
}


def do_clone(args, config):
    """ Clone the desired git repository. """
    base_url = config.get('main', 'base_url')
    if base_url:
        base_url.rstrip('/')
    print(base_url)
    url = '{0}/{1}/{2}'.format(base_url, args.repo, args.project)
    print(url)
    print('This has not yet been implemented')


def do_update(args, config):
    """ Runs git pull--rebased on the desired git repository. """
    _log.debug('project:        %s', args.project)
    location = os.path.expanduser(config.get('main', 'location'))
    project_folder = os.path.join(location, args.project)
    _log.debug('Running git pull --rebase on:        %s', project_folder)
    pag_off.utils._run_shell_cmd(
        ['git', 'pull', '--rebase'],
        directory=project_folder
    )
    print('%s updated' % args.project)


def do_list(args, config):
    """ List the tickets in the specified git repository. """
    _log.debug('project:        %s', args.project)
    _log.debug('status:         %s', args.status)
    _log.debug('tags:           %s', args.tag)
    _log.debug('sort:           %s', args.sort)
    _log.debug('mine:           %s', args.mine)
    _log.debug('assignee:       %s', args.assignee)
    _log.debug('author:         %s', args.author)
    _log.debug('milestone:      %s', args.milestone)

    if args.status.lower() not in ['open', 'closed', 'all']:
        pag_off.exceptions.InvalidStatus(
            'Status: %s in not in the list of supported statuses' %
            args.status)

    tags = args.tag.split(',') if args.tag else []
    # clean empty tags
    tags = [t.strip() for t in tags if t.strip()]
    location = os.path.expanduser(config.get('main', 'location'))
    ticket_fold = os.path.join(location, args.project)
    _log.debug('folder:         %s', ticket_fold)
    assignee = None
    if args.mine:
        assignee = config.get('user', 'name')
    elif args.assignee:
        assignee = args.assignee
    tickets = pag_off.utils.load_tickets(
        ticket_fold, status=args.status, tags=tags,
        assignee=assignee, author=args.author,
        milestone=args.milestone,
    )
    table = []
    headers = None
    cnt = 0
    if tickets:
        headers = [
            '#id', 'title', 'Opened', 'Modified', 'Reporter', 'Assignee']
        reverse = True if args.sort.lower() == 'newer' else False
        for key in sorted(tickets, reverse=reverse):
            data = tickets[key]
            assignee = data.get('assignee')
            table.append([
                key,
                data['title'],
                pag_off.utils.humanize(data['date_created']),
                pag_off.utils.humanize(data['last_updated']),
                data['user']['name'],
                assignee['name'] if assignee else ''
            ])
            cnt += 1
    else:
        table.append(['No tickets found with these criterias'])
    print(tabulate(table, headers=headers))
    if cnt:
        print('%s tickets found' % cnt)


def do_view(args, config):
    """ Displays the content the tickets in the specified git repository.
    """
    _log.debug('project:        %s', args.project)
    _log.debug('ticket:         %s', args.ticket_id)

    location = os.path.expanduser(config.get('main', 'location'))
    ticket_fold = os.path.join(location, args.project)
    _log.debug('folder:         %s', ticket_fold)
    ticket = pag_off.utils.load_tickets(
        ticket_fold, ticket_id=args.ticket_id)[0]
    print(pag_off.utils.ticket2str(ticket))


def do_comment(args, config):
    """ Allows the user to comment on a specific ticket
    """
    _log.debug('project:        %s', args.project)
    _log.debug('ticket:         %s', args.ticket_id)

    location = os.path.expanduser(config.get('main', 'location'))
    ticket_fold = os.path.join(location, args.project)
    _log.debug('folder:         %s', ticket_fold)
    ticket, filepath = pag_off.utils.load_tickets(
        ticket_fold, ticket_id=args.ticket_id)
    comment = input('Comment: ')
    print(pag_off.utils.add_comment(ticket, filepath, comment, config))


def do_take(args, config):
    """ Allows the user to self-assign a specific ticket
    """
    _log.debug('project:        %s', args.project)
    _log.debug('ticket:         %s', args.ticket_id)

    location = os.path.expanduser(config.get('main', 'location'))
    ticket_fold = os.path.join(location, args.project)
    _log.debug('folder:         %s', ticket_fold)
    ticket, filepath = pag_off.utils.load_tickets(
        ticket_fold, ticket_id=args.ticket_id)
    print(pag_off.utils.take_ticke(ticket, filepath, config))


def do_close(args, config):
    """ Allows the user to comment on a specific ticket
    """
    _log.debug('project:        %s', args.project)
    _log.debug('ticket:         %s', args.ticket_id)

    location = os.path.expanduser(config.get('main', 'location'))
    ticket_fold = os.path.join(location, args.project)
    _log.debug('folder:         %s', ticket_fold)

    # Get the closed_as options
    close_statuses = pag_off.utils.get_field_tickets(
        ticket_fold, 'close_status')
    print('Close status available: %s' % ', '.join(close_statuses or []))

    ticket, filepath = pag_off.utils.load_tickets(
        ticket_fold, ticket_id=args.ticket_id)
    close_status = input('Close status: ')
    if close_status and close_statuses and \
            close_status not in close_statuses:
        print('This status is not in the list')
    else:
        print(pag_off.utils.close_ticket(
            ticket, filepath, config, close_status))


def parse_arguments():
    """ Set-up the argument parsing. """
    parser = argparse.ArgumentParser(
        description='Interact with your pagure project\s tickets/PRs offline')

    parser.add_argument(
        '--debug', default=False, action='store_true',
        help='Increase the verbosity of the information displayed')
    parser.set_defaults(func=lambda a, k: print(parser.format_help()))

    subparsers = parser.add_subparsers(title='actions')

    # CLONE
    parser_clone = subparsers.add_parser(
        'clone',
        help='Clone a specified repository')
    parser_clone.add_argument(
        'project',
        help="Name of the project on pagure, can be: <project>, "
             "<namespace>/project, fork/<user>/<project> or "
             "fork/<user>/<namespace>/<project>")
    parser_clone.add_argument(
        'repo',
        help="The type of repository to clone: tickets or pull-requests")
    parser_clone.set_defaults(func=do_clone)

    # UPDATE
    parser_update = subparsers.add_parser(
        'update',
        help='Update a specified repository')
    parser_update.add_argument(
        'project',
        help="Name of the project on pagure, can be: <project>, "
             "<namespace>/project, fork/<user>/<project> or "
             "fork/<user>/<namespace>/<project>")
    parser_update.set_defaults(func=do_update)

    # LIST
    parser_list = subparsers.add_parser(
        'list',
        help='List the tickets in the specified repository')
    parser_list.add_argument(
        'project',
        help="Name of the project on pagure, can be: <project>, "
             "<namespace>/project, fork/<user>/<project> or "
             "fork/<user>/<namespace>/<project>")
    parser_list.add_argument(
        'status', default='Open', nargs="?",
        help="Status of the tickets to show, can be: Open, Closed, All "
             "(cas insensitive). Defaults to: Open")
    parser_list.add_argument(
        '--sort', default='newer',
        help="Specifies in which order the tickets should be shown, can be: "
             "newer or older (cas insensitive). Defaults to: newer")
    parser_list.add_argument(
        '--tag',
        help="One or more (comma separated) tags to filter the issues with")
    parser_list.add_argument(
        '--mine', default=False, action='store_true',
        help="Filter issues assigned to you")
    parser_list.add_argument(
        '--assignee',
        help="Return only the ticket assigned to this person")
    parser_list.add_argument(
        '--author',
        help="Return only the ticket opened to this person")
    parser_list.add_argument(
        '--milestone',
        help="Return only the ticket opened for the specified milestone")
    parser_list.set_defaults(func=do_list)

    # VIEW
    parser_view = subparsers.add_parser(
        'view',
        help='View the details of the tickets in the specified repository')
    parser_view.add_argument(
        'project',
        help="Name of the project on pagure, can be: <project>, "
             "<namespace>/project, fork/<user>/<project> or "
             "fork/<user>/<namespace>/<project>")
    parser_view.add_argument(
        'ticket_id',
        help="Identifier of the ticket in this project")
    parser_view.set_defaults(func=do_view)

    # COMMENT
    parser_comment = subparsers.add_parser(
        'comment',
        help='Comment on a ticket in the specified repository')
    parser_comment.add_argument(
        'project',
        help="Name of the project on pagure, can be: <project>, "
             "<namespace>/project, fork/<user>/<project> or "
             "fork/<user>/<namespace>/<project>")
    parser_comment.add_argument(
        'ticket_id',
        help="Identifier of the ticket in this project")
    parser_comment.set_defaults(func=do_comment)

    # CLOSE
    parser_comment = subparsers.add_parser(
        'close',
        help='Close a ticket in the specified repository')
    parser_comment.add_argument(
        'project',
        help="Name of the project on pagure, can be: <project>, "
             "<namespace>/project, fork/<user>/<project> or "
             "fork/<user>/<namespace>/<project>")
    parser_comment.add_argument(
        'ticket_id',
        help="Identifier of the ticket in this project")
    parser_comment.set_defaults(func=do_close)

    # TAKE
    parser_take = subparsers.add_parser(
        'take',
        help='Self-assign a ticket')
    parser_take.add_argument(
        'project',
        help="Name of the project on pagure, can be: <project>, "
             "<namespace>/project, fork/<user>/<project> or "
             "fork/<user>/<namespace>/<project>")
    parser_take.add_argument(
        'ticket_id',
        help="Identifier of the ticket in this project")
    parser_take.set_defaults(func=do_take)

    return parser.parse_args()


def main():
    """ Start of the application. """
    # Parse the arguments
    args = parse_arguments()

    # Load the configuration file
    config = configparser.ConfigParser()
    file_read = config.read(CONFIGS)

    # Validate the configuration loaded
    invalid_conf = False
    for sec in MIN_CONFIG:
        if not config.has_section(sec):
            invalid_conf = True
            print(
                'No `{0}` section found in any of your configuration files: '
                '{1}'.format(sec, ', '.join(file_read))
            )
        else:
            for opt in MIN_CONFIG[sec]:
                if not config.has_option(sec, opt):
                    invalid_conf = True
                    print(
                        'No `{1}` option found in the section `{0}` in any of '
                        'your configuration files: {2}'.format(
                            sec, opt, ', '.join(file_read))
                    )

    if invalid_conf:
        if not file_read:
            print(
                'Configuration files can be located in any of: %s' %
                CONFIGS)
        return 3

    logging.basicConfig()
    if args.debug:
        _log.setLevel(logging.DEBUG)
        l = logging.getLogger('pag_off.utils')
        l.setLevel(logging.DEBUG)

    # Act based on the arguments given
    return_code = 0
    try:
        args.func(args, config)
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        return_code = 1
    except pag_off.exceptions.PagOffException as err:
        print(err)
        return_code = 4
    except Exception as err:
        print('Error: {0}'.format(err))
        logging.exception("Generic error catched:")
        return_code = 2

    return return_code


if __name__ == '__main__':
    sys.exit(main())
