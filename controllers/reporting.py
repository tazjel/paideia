# coding: utf8

if 0:
    from gluon import current, Auth, SQLFORM
    from gluon.dal import DAL
    auth = Auth()
    db = DAL()
    request = current.request

from paideia_stats import Stats
#from paideia_bugs import Bug


@auth.requires_membership(role='administrators')
def index():
    reports = dict(attempts='Attemps Log',)
    return dict(reports=reports)


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
    not_in_path = steps.find(lambda row: not row.id in path_steps)

    # find any steps/paths that have been deactivated
    deactivated = [s for s in steps if s.status == 1]

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
