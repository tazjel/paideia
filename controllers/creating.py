# coding: utf8
from paideia_bugs import Bug

if 0:
    from gluon import current, URL, A, H3
    from gluon.dal import DAL
    from gluon.tools import Auth, Crud
    request, session = current.request, current.session
    response, T, cache = current.response, current.t, current.cache
    crud = Crud()
    db = DAL()
    auth = Auth()


@auth.requires_membership(role="administrators")
def tag():
    edit_form = crud.create(db.tags)
    closer = A('close', _href=URL('#'), _class='close_link')
    the_title = H3('Create a New Tag')

    return {'form': edit_form, 'closer': closer, 'the_title': the_title}


@auth.requires_login()
def bug():
    """
    Return the modal form allowing a user to submit a content bug.
    """
    return {}


@auth.requires_login()
def submit_bug():
    """
    Create a new bug report for a step.
    The step_id is now being passed in as bug_step_id instead of step_id as it was
    Apparently conflicting with some other step id:  JOB <jboakye@bwachi.com> 20141003
    """
    vbs = True
    if vbs: print 'controller.bug:'
    rvars = request.vars
    if vbs: print 'vars are', rvars
    b = Bug(step_id=rvars.bug_step_id, path_id=rvars.path_id, loc_id=rvars.loc_id)
    if vbs: print 'created bug object successfully'
    if vbs: print 'bug is', b
    logged = b.log_new(rvars.answer, rvars.log_id, rvars.score)
    if vbs: print 'logged bug - response is', logged
    return {'success': logged}
