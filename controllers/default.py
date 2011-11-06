# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a samples controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - call exposes all registered services (none by default)
#########################################################################

import datetime

if 0:
    from gluon import current
    from gluon.tools import Auth
    from gluon.dal import DAL
    db = DAL()
    auth = Auth()
    response = current.response
    session = current.session
    request = current.request
    from applications.paideia.models.paideia_stats import *
    from applications.paideia.models.paideia_bugs import *
    

def index():
    """
    example action using the internationalization operator T and flash
    rendered by views/default/index.html or views/generic.html
    """
    return dict(message=T('Hello World'))

def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    # create instance of paideia_stats class from models
    s = paideia_stats(auth.user_id)
    t = paideia_timestats(auth.user_id)
    w = paideia_weeklycount(auth.user_id)
    b = paideia_bugs()
    blist = b.bugresponse(auth.user_id)
    session.debug = blist
    return dict(form=auth(), score_avg=s.score_avg, total_len = t.total_len, total_cat1 = t.total_cat1, total_cat2 = t.total_cat2, total_cat3 = t.total_cat3, percent_cat1 = t.percent_cat1, percent_cat2 = t.percent_cat2, percent_cat3 = t.percent_cat3, total_cat4 = t.total_cat4, percent_cat4 = t.percent_cat4, htmlcal = w.htmlcal, blist = blist)

def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request,db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()


@auth.requires_signature()
def data():
    """
    http://..../[app]/default/data/tables
    http://..../[app]/default/data/create/[table]
    http://..../[app]/default/data/read/[table]/[id]
    http://..../[app]/default/data/update/[table]/[id]
    http://..../[app]/default/data/delete/[table]/[id[
    http://..../[app]/default/data/select/[table]
    http://..../[app]/default/data/search/[table]
    but URLs bust be signed, i.e. linked with
      A('table',_href=URL('data/tables',user_signature=True))
    or with the signed load operator
      LOAD('default','data.load',args='tables',ajax=True,user_signature=True)
    """
    return dict(form=crud())

@auth.requires_membership(role='administrators')
def send_mail():
    addr = db(db.auth_user.id == session.the_student).select(db.auth_user.email)
    subj = session.mail_subject
    msg = session.mail_message

    if mail.send(to=addr, subject=subj, message=msg):
        response.flash('mail sent successfully')
    else:
        response.flash('There was a problem sending the mail.')

    return

@auth.requires_membership(role='administrators')
def bulk_cat_qs():
    records = db(db.question_records.id > 0).select()
    counter = 0
    for record in records:
        #figure out how the student is doing with this question
        last_right = record.last_right
        last_wrong = record.last_wrong
        now_date = datetime.date.today()
        right_dur = now_date-last_right
        wrong_dur = now_date-last_wrong
        rightWrong_dur = last_right - last_wrong
        #categorize this question based on student's performance
        if right_dur < wrong_dur:
            if (right_dur < rightWrong_dur) and (right_dur < datetime.timedelta(days=170)):
                if right_dur > datetime.timedelta(days=14):
                    cat = 4
                else:
                    cat = 3
            else:
                cat = 2
        else:
            cat = 1
        # update database with categorization
        db(db.question_records.id == record.id).update(category = cat)
        # count each record updated
        counter += 1
        session.debug = record.id

    message = "Success. I categorized ", counter, " records."

    return dict(message = message)
