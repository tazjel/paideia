# coding: utf8

# TODO: rework to use plugin_listandedit as a widget

#@auth.requires_membership(role='administrators')
#def question():
    #questions = db().select(db.questions.ALL, orderby = db.questions.question)
    #return dict(questions = questions)

#@auth.requires_membership(role='administrators')
#def quiz():
    #quizzes = db().select(db.quizzes.ALL, orderby = db.quizzes.quiz)
    #return dict(quizzes = quizzes)

@auth.requires_membership(role='administrators')
def user():
    users = db().select(db.auth_user.ALL, orderby = db.auth_user.last_name)
    return dict(users = users)

#@auth.requires_membership(role='administrators')
#def tags():
    #tags = db().select(db.tags.ALL, orderby = db.tags.tag)
    #return dict(tags = tags)

#@auth.requires_membership(role='administrators')
#def bug():
    #the_q = request.args[0]
    #the_status = request.args[1]
    #if the_status == 1:
        #bugs = db((db.q_bugs.question == the_q) & ((db.q_bugs.bug_status == the_status) | (db.q_bugs.bug_status == None))).select()
    #else:
        #bugs = db((db.q_bugs.question == the_q) & (db.q_bugs.bug_status == the_status)).select()
    #return dict(bugs = bugs)

def news():
    newslist = db(db.news).select(orderby = ~db.news.date_submitted)
    if db((db.auth_membership.user_id == auth.user_id) & (db.auth_membership.group_id == 1)).select():
        button = A('new story', _href=URL('creating', 'news.load'), cid='modal_frame', _class='create_link news_create_link')
    else:
        button = ''
    return dict(newslist = newslist, button = button)

def slides():
    slidelist = db(db.plugin_slider_decks.id > 0).select(orderby= db.plugin_slider_decks.position);
    slides = UL()
    for s in slidelist:
        slides.append(LI(A(s.deck_name, _href=URL('plugin_slider', 'start_deck.load', args=[s.id]), cid='slideframe')))

    return dict(slides=slides)

