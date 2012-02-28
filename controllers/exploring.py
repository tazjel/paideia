# coding: utf8
if 0:
    from gluon import current, redirect, URL, SQLFORM, A, Field, IS_NOT_EMPTY
    from gluon.dal import DAL
    from gluon.tools import Auth
    request,session,response,T,cache=current.request,current.session,current.response,current.T,current.cache
    db = DAL()
    auth = Auth()
    from applications.paideia.modules.paideia_exploring import paideia_path, counter
    from applications.paideia.modules.paideia_questions import question

from applications.paideia.modules.paideia_exploring import paideia_path, counter, map
from paideia_questions import question

def stepinit():
    #find out what location has been entered
    curr_loc = request.vars['loc']
    
    #find out what paths (if any) are currently active
    paths = session.active_path or None
    
    #check to see whether any constraints are in place (globally or for this location)
    
    #if no constraints and no active path start new path
    return dict()
    

def stepask():
    #check to see whether a path is active and determines the next step
    if session.active_path:
        pass
    
    #if not, initiate new path 
    if not request.vars.response:
        set_path = paideia_path()
        set_counter = counter()
        the_question = question()
        the_question.selectq()

    form = SQLFORM.factory(
        Field('response', 'string', requires=IS_NOT_EMPTY())
    )
    if form.accepts(request.vars,session):
        session.response = request.vars.response
        redirect(URL('index', args=['reply']))

    return dict(question=session.question_text, form=form)


def stepreply():
    #see whether answer matches any of the three answer fields
    q = question()
    the_eval = q.evalq()

    #build response to user
    if session.eval == 'correct':
        the_reply = "Right. Κάλη."
    elif session.eval == 'partial':
        the_reply = "Οὐ κάκος. You're close."
    else:
        the_reply = "Incorrect. Try again!"

    #add a record for this attempt in db.attempt_log
    db.attempt_log.insert(question=session.q_ID, score=q.score, quiz=session.path_id)

    return dict(reply=the_reply, answer=session.readable_answer, raw_answer=session.answer, score=session.score)


def patherror():
    if request.args(1) == 'unknown':
        db.q_bugs.insert(question=session.qID, a_submitted=request.vars.answer)
        #TODO: fix problem with changing column name for status
        #db(db.questions.id==session.qID).update(qqq_status=1);
    if request.args(1) == 'regex':
        db.q_bugs.insert(question=session.qID, a_submitted=request.vars.answer)
        #db(db.questions.id==session.qID).update(qqq_status=1);
    message = "Oops! Something about that question confused me, and I'm not sure whether your answer was right. Let's try another one."
    button = A('continue', _href=URL('index', args=['ask']), _class='button-green-grad next_q', cid=request.cid)
    #don't include this question in counting the number attempted
    session.q_counter -= 1
    return dict(message = message, button = button)


@auth.requires_login()
def index():

    #when user begins exploring (also default)
    if (request.args(0) == 'start') or (not request.args):
        the_map = map()
        for i in ['blocks', 'active_path', 'completed_paths']:
            if not session[i]:
                print i
                session[i] = None
             
        return dict(locs = the_map.locs, map_image = the_map.image)

    #after user selects quiz (or 'next question')
    elif request.args(0) == 'ask':
        return stepinit()

    #after submitting answer
    elif request.args(0) == 'reply':
        return stepreply()
    
    elif request.args(0) == 'error':
        return patherror()
        
    