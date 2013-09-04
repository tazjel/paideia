# coding: utf8
from paideia import Walk

if 0:
    from gluon import current
    request = current.request
    session = current.session
    response = current.response
    auth = current.auth
    db = current.db

"""
These controller functions handle user-interactions for the game proper. It
does not cover any admin actions, content creation, or retrieval and
display of student performance statistics.

Wherever possible, business logic is kept out of these controllers and is
provided by classes in modules/paideia. Controllers access
that logic through two public methods:

- paideia.Walk.map
- paideia.Walk.start

The controller functions interact with these views:
- exploring/index.html (frame for the game ui)
- exploring/walk.load (main game ui)
- exploring/patherror.load (error screen)
- exploring/calendar.load (ajax calendar widget)

Errors are sent (by routes.py) to default/oops
"""


@auth.requires_login()
def index():
    """
    Present the frame for the game interface, which will then load via ajax
    using the walk() controller below. Preparation of the necessary session
    variables has now been moved to Walk.__init__ and doesn't need to happen
    here.

    :Permissions: user must be logged in.
    """
    print 'getting index'
    print 'vars', request.vars
    print 'args', request.args
    return {}


@auth.requires_login()
def walk():
    """
    Present the various stages of the game ui and handle user responses.

    This is the main function for presenting various states of the game
    user interface. These states are determined by the first url argument.
    The states are:

    - map (default; present navigation map)
    - step (Present prompt to begin a step OR evaluate user response and
        present the appropriate feedback and further navigation options.)
    - error

    The 'step' state elicits two different behaviours from the
    paideia module, depending on whether the web2py request object includes a
    submitted user response.
    - no: begin a step (choose appropriate path/step and retrieve prompt)
    - yes: evaluate the user's reply to the previous step prompt

    This function is intended to be accessed only via ajax, so its only view
    is exploring/walk.load. This view should be presented in the #page
    element of exploring/index.html.
    """
    request = current.request
    print "starting walk controller"

    if not request.vars.loc:
        request.vars.loc = None
    walk = Walk(request.vars.loc)
    rvars = request.vars
    rargs = request.args
    print "in controller:"
    print "args:", request.args
    print "vars:", request.vars

    # TODO: implement failsafe here to avoid accidental submission of blank
    # form (require delay and require non-empty

    # When user begins exploring (also default) present map
    if (not rargs) or (rargs[0] == 'map'):
        return {'map': walk.map()}
    else:
        stepargs = {}
        stepargs['response_string'] = rvars['response'] if \
            ('response' in rvars and 'response' not in [' ', None]) else None

        return walk.start(**stepargs)

    # TODO: re-implement in module
    # if user wants to retry a failed step
    #elif request.args(0) == 'retry':
        #if debug: print '\ncontroller exploring.walk() state: retry'
        #last_pathid = session.walk['retry'][0]
        #last_stepid = session.walk['retry'][1]
        #walk.activate_step(last_pathid, last_stepid)
        #return walk.step.ask()

    # TODO: re-implement in module
    # test a specific path
    #elif request.args(0) == 'test':
        #if debug: print '\ncontroller exploring.walk() state: test'
        #pathid = request.vars['path']
        #stepid = request.vars['step']
        #walk.activate_step(pathid, stepid)
        #return walk.step.ask()
