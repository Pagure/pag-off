Pag-off
=======

:Author:  Pierre-Yves Chibon <pingou@pingoured.fr>


pag-off is a small utility tool to interact with pagure issues and pull-requests
offline.

It will allow you to clone the ticket or pull-request repo of a project hosted
on pagure. List all the open tickets or pull-requests and interact with them.

Homepage: https://pagure.io/pag-off


Get it running
==============

There are several options when it comes to a development environment. Vagrant
will provide you with a virtual machine which you can develop on, or you can
install it directly on your host machine.


* Retrieve the sources::

    git clone https://pagure.io/pag-off.git
    cd pag-off


* create the virtualenv::

      virtualenv pag-off_env
      source ./pag-off_env/bin/activate


* Get the project running::

    python setup.py develop


* Run it::

    ./runserver.py
