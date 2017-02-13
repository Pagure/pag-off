# -*- coding: utf-8 -*-

"""
 (c) 2016 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>

"""

import argparse
import configparser
import logging
import os
import sys


LOG = logging.getLogger(__name__)
CONFIGS = [
    '/etc/pag-off.conf',
    os.path.expanduser('~/.config/pag-off.conf'),
    os.path.join(os.getcwd(), 'pag-off.conf')
]

MIN_CONFIG = {
    'main': ['base_url']
}

def do_clone(args, config):
    """ Clone the desired git repository. """
    base_url = config.get('main', 'base_url')
    if base_url:
        base_url.rstrip('/')
    print(base_url)
    url = '{0}/{1}/{2}'.format(base_url, args.repo, args.project)
    print(url)


def parse_arguments():
    """ Set-up the argument parsing. """
    parser = argparse.ArgumentParser(
        description='Interact with your pagure project\s tickets/PRs offline')

    parser.add_argument(
        '--debug', default=False, action='store_true',
        help='Increase the verbosity of the information displayed')

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
                '{1}'.format(sec, file_read)
            )
        else:
            for opt in MIN_CONFIG[sec]:
                if not config.has_option(sec, opt):
                    invalid_conf = True
                print(
                    'No `{1}` option found in the section `{0}` in any of '
                    'your configuration files: {2}'.format(
                        sec, opt, file_read)
                )

    if invalid_conf:
        return 3

    logging.basicConfig()
    if args.debug:
        LOG.setLevel(logging.DEBUG)

    # Act based on the arguments given
    return_code = 0
    try:
        args.func(args, config)
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        return_code = 1
    except Exception as err:
        print('Error: {0}'.format(err))
        logging.exception("Generic error catched:")
        return_code = 2

    return return_code


if __name__ == '__main__':
    sys.exit(main())
