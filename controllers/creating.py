# coding: utf8

@auth.requires_membership(role="administrators")
def question():
    edit_form = crud.create(db.questions)
    closer = A('close', _href=URL('#'), _class='close_link')
    the_title = H3('Create a New Question')

    return dict(form = edit_form, closer=closer, the_title=the_title)


@auth.requires_membership(role="administrators")
def quiz():
    edit_form = crud.create(db.quizzes)
    closer = A('close', _href=URL('#'), _class='close_link')
    the_title = H3('Create a New Quiz')

    return dict(form = edit_form, closer=closer, the_title=the_title)

@auth.requires_membership(role="administrators")
def tag():
    edit_form = crud.create(db.tags)
    closer = A('close', _href=URL('#'), _class='close_link')
    the_title = H3('Create a New Tag')

    return dict(form = edit_form, closer=closer, the_title=the_title)

@auth.requires_login()
def q_bug():
    db.q_bugs.insert(question=session.qID, a_submitted=request.vars.answer)
    response.flash = 'Thanks for reporting this potential bug.'
    return dict(message = 'If this turns out to be a bug it will be taken into account as we track your learning.')

@auth.requires_membership(role='administrators')
def news():
    form = crud.create(db.news)
    the_title = H3('Create a New News Story')
    closer = A('close', _href=URL('#'), _class='close_link')

    return dict(form = form, the_title = the_title, closer = closer)
