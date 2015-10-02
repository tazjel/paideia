# coding: utf8

if 0:
    from gluon import current, Auth, SQLFORM, URL, Field, IS_DATE
    from gluon.dal import DAL
    auth = Auth()
    db = DAL()
    request, response = current.request, current.response

from paideia_stats import Stats
# from pprint import pprint
# from plugin_utils import islist
#from paideia_bugs import Bug
import datetime
from dateutil.parser import parse


@auth.requires_membership(role='administrators')
def index():
    reports = dict(attempts='Attempts Log',)
    return dict(reports=reports)


def vocabulary():
    """
    """
    auth = current.auth

    lemmas = db(db.lemmas.first_tag == db.tags.id).select(orderby=db.tags.tag_position)
    sets = list(set([s.tags.tag_position for s in lemmas]))
    myprog = db.tag_progress(db.tag_progress.name == auth.user_id)
    mylevel = myprog.latest_new if myprog else 1

    for l in lemmas:
        lid = l.lemmas.id

        # Get number of paths and steps using the lemma
        mysteps = db(db.steps.lemmas.contains(lid)).select()
        if mysteps:
            stepids = [s.id for s in mysteps]
            mypaths = db(db.paths.steps.contains(stepids)).select()
        l['lemmas']['stepcount'] = len(mysteps) if mysteps else 0
        l['lemmas']['pathcount'] = len(mypaths) if 'mypaths' in locals() and mypaths else 0

        # Assemble string with principle parts and/or irregular forms
        myparts = ''
        if l['lemmas']['future'] and l['lemmas']['future'] not in ['None', 'none']:
            partnames = [l['lemmas']['future'], l['lemmas']['aorist_active'],
                         l['lemmas']['perfect_active'], l['lemmas']['perfect_passive'],
                         l['lemmas']['aorist_passive']]
            myparts = '{}, {}, {}, {}, {}'.format(*partnames)
        elif l['lemmas']['genitive_singular'] \
                and l['lemmas']['genitive_singular'] not in ['None', 'none']:
            myparts = 'gen. {}'.format(l['lemmas']['genitive_singular'])

        if l['lemmas']['other_irregular'] \
                and l['lemmas']['other_irregular'] not in ['None', 'none']:
            if myparts == '':
                myparts += '{}'.format(l['lemmas']['other_irregular'])
            else:
                myparts += ' ({})'.format(l['lemmas']['other_irregular'])
        l['lemmas']['myparts'] = myparts

    mylemmas = [l for l in lemmas if l['tags']['tag_position'] <= mylevel]

    # Include files for Datatables jquery plugin and bootstrap css styling
    response.files.append("https://cdn.datatables.net/r/bs/jq-2.1.4,jszip-2.5.0,"
                          "pdfmake-0.1.18,dt-1.10.9,b-1.0.3,b-colvis-1.0.3,b-html5-1.0.3,"
                          "b-print-1.0.3,fc-3.1.0,r-1.0.7,sc-1.3.0,se-1.0.1/"
                          "datatables.min.css")
    response.files.append("https://cdn.datatables.net/r/bs/jq-2.1.4,jszip-2.5.0,"
                          "pdfmake-0.1.18,dt-1.10.9,b-1.0.3,b-colvis-1.0.3,"
                          "b-html5-1.0.3,b-print-1.0.3,fc-3.1.0,r-1.0.7,sc-1.3.0,"
                          "se-1.0.1/datatables.min.js")

    return {'lemmas': lemmas,
            'mylemmas': mylemmas,
            'mylevel': mylevel}


@auth.requires_membership(role='administrators')
def paths_by_tag():
    """
    Returns a dictionary providing information about the use of grammar tags.

    The first key is 'taglist'. Its value is a list of dictionaries, one for
    each tag in db.tags. The dictionary keys/values are:
        id -        the tag id (int)
        name -      the tag name (str)
        position -  the level of the tag in the game progression (int)
        badge -     a tuple including the id [0] and name [1] of the badge
                    corresponding to the current tag
        stepdict -  a dictionary holding three keys–'tags', 'tags_secondary',
                    and 'tags_ahead'–with Rows objects as values. These are
                    the steps which have the current tag listed in the named
                    field.
        pathdict -  a dictionary with the same keys and structure as stepdict
                    except that it

    In addition to 'taglist', the top-level return dictionary also includes
    three other keys/values:
        tag_conflict -  Indicates whether any of the primary tags assigned to
                        a path/step
        not_in_path -   A list of ids for steps that have not been used in any
                        path.
        deactivated -   A list of ids for steps that have a 'status' value of 1
    """
    tags = db().select(db.tags.ALL)
    steps = db().select(db.steps.ALL)
    paths = db().select(db.paths.ALL)
    badges = db().select(db.badges.ALL)
    slides = db().select(db.plugin_slider_decks.ALL)

    taglist = []

    for t in tags:
        # find all steps/paths with this tag
        stepsdict = {}
        pathsdict = {}
        for f in ['tags', 'tags_secondary', 'tags_ahead']:
            try:
                stepset = steps.find(lambda row: t.id in row[f])
                idlist = [p.id for s in stepset for p in paths
                        if s.id in p.steps]
                pathset = paths.find(lambda row: row.id in set(idlist))
                pathsdict[f] = pathset
            except TypeError:
                pathsdict[f] = []
                stepset = []  # handle case where row[f] is None
            stepsdict[f] = stepset

        # find the badge corresponding to this tag
        badge = badges.find(lambda row: row.tag == t.id)

        # find the slide sets addressing this tag
        if t.slides is None:
            tag_slides = None
        else:
            tag_slides = slides.find(lambda row: row.id in t.slides)

        tagdict = {'id': t.id,
                   'name': t.tag,
                   'position': t.tag_position,
                   'badge': badge,
                   'stepsdict': stepsdict,
                   'pathsdict': pathsdict,
                   'tag_slides': tag_slides,
                   }
        print tagdict['position']
        taglist.append(tagdict)

    taglist = sorted(taglist, key=lambda k: k['position'])
    print [t['position'] for t in taglist]
    pset = set([t['position'] for t in taglist])
    positions = {}
    for p in pset:
        positions[p] = [tag for tag in taglist if tag['position'] == p]

    # find any steps not used in a path
    path_steps = [s for p in paths for s in p['steps']]
    not_in_path = steps.find(lambda row: row.id not in path_steps)

    # find any steps/paths that have been deactivated
    deactivated = [s for s in steps if s.status == 2]

    for l in [not_in_path, deactivated]:
        if len(l) == 0:
            l = None

    return {'positions': positions,
            'tag_conflicts': tag_conflicts,
            'not_in_path': not_in_path,
            'deactivated': deactivated}


@auth.requires_membership(role='administrators')
def tag_conflicts():
    """
    Return a list of steps with tags at conflicting positions in the progression.
    """
    tag_conflicts = []
    steps = db().select(db.steps.ALL)
    tags = db().select(db.tags.ALL)
    for t in tags:
        for s in steps:
            try:
                positions = [tags.find(lambda row: row.id == t.id).first().tag_position
                            for mytag in s.tags]
                if len(set(positions)) > 1:
                    tag_conflicts.append(s.id)
                else:
                    pass
            except TypeError:
                pass
    return tag_conflicts


@auth.requires_membership(role='administrators')
def attempts():
    if len(request.args) > 0:
        form = SQLFORM.grid(db.attempt_log.name == request.args[0])
    else:
        form = SQLFORM.grid(db.attempt_log)
    return dict(form=form)


@auth.requires_membership(role='administrators')
def user():
    # Scripts for charts
    response.files.append('//cdnjs.cloudflare.com/ajax/libs/d3/3.4.10/d3.min.js')
    response.files.append(URL('static', 'js/user_stats.js'))

    # Include files for Datatables jquery plugin and bootstrap css styling
    response.files.append('//cdnjs.cloudflare.com/ajax/libs/datatables/1.10.0/'
                          'js/jquery.dataTables.min.js')
    response.files.append('//cdnjs.cloudflare.com/ajax/libs/datatables-colvis/1.1.0/'
                          'js/datatables.colvis.min.js')
    response.files.append('//cdnjs.cloudflare.com/ajax/libs/datatables-colvis/1.1.0/'
                          'css/datatables.colvis.min.css')
    response.files.append("https://cdn.datatables.net/fixedcolumns/3.0.1/js/"
                          "dataTables.fixedColumns.min.js")  # fixedColumns plugin
    response.files.append("https://cdn.datatables.net/fixedcolumns/3.0.1/css/"
                          "dataTables.fixedColumns.css")  # fixedColumns plugin css
    response.files.append("https://cdn.datatables.net/plug-ins/28e7751dbec/"
                          "integration/bootstrap/3/dataTables.bootstrap.css")  # bootstrap css

    user = request.args[0]
    return {'id': user}


def calendar():
    '''
    Provides a calendar with user activity information for a given month/year.
    Intended to be used via an ajax component on the user's profile and the
    instructor's user reports.
    '''
    user_id = request.args[0]
    year = request.args[1]
    month = request.args[2]

    s = Stats(user_id)
    cal = s.monthcal(year, month)

    return {'cal': cal}


def tag_counts():
    '''
    Return a dictionary of data on user activity around tag categories.

    '''
    nowdate = datetime.datetime.combine(datetime.date.today(),
                                        datetime.time(0, 0, 0, 0))

    if 'start_date' in request.vars.keys():
        sdt = parse(request.vars['start_date'])
        startdate = datetime.datetime.combine(sdt, datetime.time(0, 0, 0, 0))
    else:
        startdate = nowdate - datetime.timedelta(days=2)
    print 'startdate', startdate

    if 'end_date' in request.vars.keys():
        edt = parse(request.vars['end_date'])
        enddate = datetime.datetime.combine(edt, datetime.time(0, 0, 0, 0))
    else:
        enddate = nowdate
    print 'enddate', enddate

    uid = request.vars['user_id'] if 'user_id' in request.vars.keys() else None

    tagdata = Stats(uid).get_tag_counts_over_time(start=startdate,
                                                  end=enddate,
                                                  uid=uid)

    form = SQLFORM.factory(Field('start_date', 'date', default=startdate.date()),
                           Field('end_date', 'date', default=enddate.date()),
                           Field('user_id', 'list:reference auth_user',
                                 default=uid, readable=False, writable=False),
                           _name='tag_counts_form',
                           _id='tag_counts_form'
                           )
    requires = IS_DATE(format='%Y-%m-%d', error_message='must be YYYY-MM-DD!')

    return {'tagdata': tagdata,
            'form': form}
