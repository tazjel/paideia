# -*- coding: utf-8 -*-
from gluon import current
from gluon import IMG, URL, INPUT, FORM, SQLFORM, SPAN, DIV, UL, LI, A, Field
from gluon import IS_NOT_EMPTY
from random import randint
import re
import datetime
from itertools import chain


class Walk(object):
    """
    Main interface class for the paideia module, intended to be called by
    the controller.
    """

    def __init__(self, loc_alias, user=None, attempt_log=None,
                tag_records=None, tag_progress=None,
                response_string=None, db=None):
        """Initialize a Walk object."""
        # inject dependencies
        self.user = user
        if not db:
            self.db = current.db

        # initialize or re-activate User object
        if not self.user:
            try:
                session = current.session
                self.user = session.user
            except:
                auth = current.auth
                user_id = auth.user_id
                userdata = db.auth_user[user_id].as_dict()

                if not attempt_log:
                    attempt_log = db(db.attempt_log.name == user_id).select()
                    tag_records = tag_records.as_list()
                if not tag_records:
                    tag_records = db(db.tag_records.name == user_id).select()
                    tag_records = tag_records.as_list()
                if not tag_progress:
                    tag_progress = db(db.tag_progress.name == user_id).select()
                    tag_progress_length = len(tag_progress)  # TODO log if > 1
                    tag_progress = tag_progress.first().as_dict()
                    # Handle first-time users, who won't have db row to fetch
                    if not tag_progress:
                        db.tag_progress.insert(latest_new=1)
                        tag_progress = db(db.tag_progress.name ==
                                                self.user.get_id()).select()
                        tag_progress = tag_progress.first().as_dict()

                self.user = User(userdata, loc_alias, attempt_log,
                                tag_records, tag_progress)

        self.response_string = response_string

    def map(self):
        """
        Return the information necessary to present the paideia navigation
        map interface.
        """
        pass

    def ask(self):
        """Return the information necessary to initiate a step interaction."""

        p = self.user.get_path()
        s = p.get_next_step()
        prompt = s.get_prompt()
        responder = s.get_responder()
        self.store_user()

        return {'prompt': prompt, 'responder': responder}

    def reply(self, response_string):
        """docstring for __reply__"""

        p = self.user.get_path()
        path_id = p.get_id()

        s = p.get_current_step()
        step_id = s.get_id()

        reply = s.get_reply(response_string)
        tags = reply['tags']
        score = reply['score']
        times_right = reply['times_right']
        times_wrong = reply['times_wrong']

        record_id = self._record_step(path_id, step_id, tags, score,
                                    times_right, times_wrong, response_string)

        bug_reporter = BugReporter(record_id, path_id, step_id,
                                    tags, score, response_string)
        p.complete_step(step_id)

        if p.check_for_end() is True:
            self.user._complete_path(path_id)

        self._store_user()

        return {'reply': reply, 'bug_reporter': bug_reporter}

    def _record_step(self, tag_records, categories, new_tags):
        """Record this session's progress"""
        # record awarding of and new tags in table db.badges_begun
        if new_tags:
            for n in new_tags:
                tag_record = db((db.badges_begun.name == user) &
                        (db.badges_begun.tag == n))
                if not tag_record.count():
                    db.badges_begun.insert(**{'name': user, 'tag': n,
                                        category: datetime.datetime.utcnow()})
                else:
                    trecord.update({category: datetime.datetime.utcnow()})

        # - if tags new or promoted, change 'cat' lists
        for cat in new_badges:
            if new_badges[cat] is not None:
                for t in new_badges[cat]:
                    try:
                        oldcat = [c for c, v in update_cats.iteritems()
                                    if (type(v) == list) and (t in v)][0]
                        update_cats[oldcat].remove(t)
                    except IndexError:
                        print 'This tag appears to be new; not removing from \
                                old position'
                    if not update_cats[cat]:
                        update_cats[cat] = [t]
                    else:
                        update_cats[cat].append(t)

        # new max-category values
        # record this session's working categorization as 'review' categories
        update_cats['rev1'] = categories['cat1']
        update_cats['rev2'] = categories['cat2']
        update_cats['rev3'] = categories['cat3']
        update_cats['rev4'] = categories['cat4']

        # do this here so that we can compare db to categories first
        # TODO: this is a bad place to update the db values
        db(db.tag_progress.name == user).update(**update_cats)

        result = []
        if [result.append(lst) for k, lst in new_badges.iteritems() if lst]:
            return new_badges
        else:
            return None

    def _complete_path(self):
        pass


class PathChooser(object):
    pass


class Location(object):
    """
    Represents a location in the game world.
    """

    def __init__(self, id_num, db=None):
        """Initialize a Location object."""
        if db is None:
            db = current.db
        self.db = db
        self.id_num = id_num
        self.data = db.locations[id_num]

    def get_alias(self):
        """Return the alias of the current Location as a string."""
        return self.data.alias

    def get_name(self):
        """Return the name of the current Location as a string.
        This 'name' is used in the svg map to identify the location."""
        return self.data.location

    def get_readable(self):
        """
        Return the readable name of the current Location as a string.
        This is used to identify the location in communication with the user.
        """
        return self.data.readable

    def get_bg(self):
        """Return the background image of the current Location as a web2py
        IMG helper object."""
        url = URL('static/images', self.db.images[self.data.bg_image].image)
        bg = IMG(_src=url)
        return bg

    def get_id(self):
        """
        Return the id for the database row representing the current
        Location (as an int).
        """
        return self.data.id


class Npc(object):
    '''
    Represents one non-player character in the game
    '''

    def __init__(self, id_num, db=None):
        """
        initialize an npc object with database data for the character
        with the provided id
        """
        if db is None:
            db = current.db
        self.db = db
        self.id_num = id_num
        self.data = db.npcs[id_num]

        # get image here so that db interaction stays in __init__ method
        image_id = self.data.npc_image
        self.image = db.images[image_id].image

    def get_id(self):
        """return the database row id of the current npc"""
        return self.id_num

    def get_name(self):
        """return the name of the current npc"""
        return self.data.name

    def get_image(self):
        """
        Return a web2py IMG helper object with the image for the current
        npc character.
        """
        url = URL('static/images', self.db.images[self.data.npc_image].image)
        img = IMG(_src=url)
        return img

    def get_locations(self):
        """docstring for get_locations"""
        locs = [Location(l) for l in self.data.location]
        return locs

    def get_description(self):
        """docstring for get_locations"""
        return self.data.notes


class NpcChooser(object):
    """
    Choose an npc to engage the user in the current step, based on the current
    location and the parameters of the step itself.
    """
    def __init__(self, step, location, prev_npc, prev_loc):
        """
        Initialize an NpcChooser object.
        """
        pass

    def choose(self):
        """
        Choose an npc for the selected step.
        If possible, continue with the same npc. Otherwise, select a different
        one that can engage in the selected step.
        """
        available = step.get_npcs()
        # TODO: step.get_npcs returns ids or Npc objects?

        if ((location.get_readable() == prev_loc.get_readable()) and
            (prev_npc.get_id() in available)):
            return prev_npc
        else:
            available2 = [n for n in available
                            if n.get_id() == prev_npc.get_id()
                            and location.get_id() in n.get_locations()]
            if len(available2) > 1:
                return available2[randint(0, len(available2) - 1)]
            else:
                return available2[0]


class BugReporter(object):
    """
    Class representing a bug-reporting widget to be presented along with the
    evaluation of the current step.
    """
    def __init__(step_id, user_response, record_id):
        """Initialize a BugReporter object"""
    pass


class Step(object):
    '''
    This class represents one step (a single question and response
    interaction) in the game.
    '''

    def __init__(self, step_id, loc, prev_loc, prev_npc_id,
                    next_step_id=None,
                    path=None,
                    db=None):
        """docstring for __init__"""
        if db is None:
            db == current.db
        self.db = db
        self.data = db.steps[step_id]
        self.repeating = False  # set to true if step already done today
        self.loc = loc
        self.prev_loc = prev_loc
        self.prev_npc_id = prev_npc_id
        self.npc = None
        self.path = path
        self.next_step_id = next_step_id

    def get_id(self):
        """
        Return the id of the current step as an integer.
        """
        return self.data.id

    def get_tags(self):
        """
        Return a list of tag id's
        """
        primary = self.data.tags
        secondary = self.data.tags_secondary
        return {'primary': primary, 'secondary': secondary}

    def get_prompt(self, username=None):
        """
        Return the prompt information for the step. In the Step base class
        this is a simple string. Before returning, though, any necessary
        replacements or randomizations are made.
        """
        self._check_location()
        raw_prompt = self.data.prompt
        prompt = self._make_replacements(raw_prompt, username)
        # prompt no longer tagged or converted to markmin here, but in view

        instructions = self._get_instructions()

        npc = self.get_npc()  # duplicate choice prevented in get_npc()
        npc_image = self.npc.get_image()

        return {'prompt': prompt,
                'instructions': instructions,
                'npc_image': npc_image}

    def _make_replacements(self, raw_string, username=None, reps=None):
        """
        Return the provided string with tokens replaced by personalized
        information for the current user.
        """
        if username is None:
            auth = current.auth
            uname = auth.user['first_name']

        if reps is None:
            reps = {}
        reps['[[user]]'] = username

        new_string = raw_string
        for k, v in reps.iteritems():
            new_string = new_string.replace(k, v)

        return new_string

    def get_responder(self):
        """
        Return form providing navigation options after prompt that does not
        require any answer.
        """
        map_button = A("Map", _href=URL('walk'),
                        cid='page',
                        _class='button-yellow-grad back_to_map icon-location')
        responder = DIV(map_button)
        return responder

    def get_npc(self):
        """Return an Npc object appropriate for this step"""
        if self.npc:  # ensure choice is made only once for each step
            return self.npc
        else:
            npcs_for_step = self.data.npcs
            npc_list = [n for n in npcs_for_step
                        if self.loc.get_id() in self.db.npcs[n].location]
            if self.prev_npc_id in npc_list:
                self.npc = Npc(self.prev_npc_id)
                return self.npc
            else:
                pick = npc_list[randint(0, len(npc_list) - 1)]
                self.npc = Npc(pick)
                return self.npc

    def _get_instructions(self):
        """
        Return an html list containing the instructions for the current
        step. Value is returned as a web2py UL() object.
        """
        instructions = self.data.instructions
        if instructions is None or instructions == []:
            return None
        else:
            list = UL(_class='step_instructions')
            for item in instructions:
                item_row = self.db.step_instructions[item]
                item_text = item_row.text
                list.append(LI(item_text))

            return list

    def _check_location(self):
        """docstring for get_locations"""
        # TODO: no code
        pass


class StepRedirect(Step):
    '''
    A subclass of Step. Handles the user interaction when the user needs to be
    sent to another location.
    '''

    def _make_replacements(self, prompt_string, username=None,
                                                    db=None, next_step=None):
        """
        Return the string for the step prompt with context-based information
        substituted for tokens framed by [[]].
        """
        session = current.session
        if db is None:
            db = current.db

        next_loc = 'somewhere else in town'  # generic default
        # if mid-way through a path, send to next viable location
        # TODO: find a way to set this value to another location with an
        # available path if the current step is the last in its path.
        if self.next_step_id:
            next_locids = db.steps[self.next_step_id].locations
            # find a location that actually has a readable name
            raw_locs = [db.locations[n].readable for n in next_locids]
            next_locs = [n for n in raw_locs if not n is None]
        elif next_step:
            next_locids = db.steps[next_step].locations
            # find a location that actually has a readable name
            raw_locs = [db.locations[n].readable for n in next_locids]
            next_locs = [n for n in raw_locs if not n is None]
        else:
            pass

        reps = {'[[next_loc]]': next_loc}
        new_string = super(StepRedirect, self)._make_replacements(
                                                            prompt_string,
                                                            reps=reps,
                                                            username=username)

        return new_string


class StepText(Step):
    """
    A subclass of Step that adds a form to receive user input and evaluation of
    that input. Handles only a single string response.
    """

    def get_responder(self):
        """
        Return the html form to allow the user to respond to the prompt for
        this step.
        """
        form = SQLFORM.factory(
                    Field('response', 'string',
                            requires=IS_NOT_EMPTY()),
                            _autocomplete='off'
                )
        return form

    def get_reply(self, user_response=None):
        """docstring for get_reply"""
        if not user_response:
            request = current.request
            user_response = request.vars['response']

        readable = self._get_readable()

        result = StepEvaluator(response)
        reply_text = result['reply']
        tips = result['tips']
        score = result['score']
        tr = result['times_right']
        tw = result['times_wrong']
        ur = result['user_response']
        tags = self.get_tags()
        sid = self.get_id()
        pid = self.get_path()
        # the following class/method both records the user's performance
        # on this step instance AND returns the BugReporter object

        return {'response': user_response,
                'reply_text': reply_text,
                'bug_reporter': bug_reporter,
                'tips': tips,
                'readable_short': readable['readable_short'],
                'readable_long': readable['readable_long']}

    def _get_readable(step_data=None):
        """
        Return two strings containing the shorter and the longer forms of the
        readable correct answer samples for this step.
        """
        if step_data is None:
            step_data = self.step_data

        readable = self.step_data.readable_response
        if '|' in readable:
            i = len(readable)
            if i > 1:
                i = 2
            readable_short = readable.split('|')[:(i + 1)]
            readable_short = [unicode(r, 'utf-8') for r in readable_short]
            readable_long = readable.split('|')
            readable_long = [unicode(r, 'utf-8') for r in readable_long]
        else:
            readable_short = [readable]
            readable_long = None

        return {'readable_short': readable_short,
                'readable_long': readable_long}


class StepMultipleChoice(Step):
    """
    A subclass of Step that adds a form to receive multiple-choice user input
    and evaluation of that input.
    """
    pass


class StepEvaluator(object):
    '''
    This class evaluates the user's response to a single step interaction and
    handles the data that results.
    '''

    def __init__(self, answers, tips):
        """Initializes a StepEvaluator object"""
        self.answers = answers
        self.tips = tips

    def get_eval(self, user_response=None):
        """
        Return the user's score for this step attempt along with "tips" text
        to be displayed to the user in case of a wrong answer.
        """
        if not user_response:
            request = current.request
            user_response = request.vars['response']
        user_response = user_response.strip()
        answers = self.answers

        # Compare the student's response to the regular expressions
        try:
            if re.match(answers[0], user_response, re.I):
                score = 1
                reply = "Right. Κάλον."
            elif len(answers) > 1 and re.match(answers[1],
                                                    user_response, re.I):
                score = 0.5
                #TODO: Get this score value from the db instead of hard
                #coding it here.
                reply = "Οὐ κάκον. You're close."
                #TODO: Vary the replies
            elif len(answers) > 2 and re.match(answers[2],
                                                    user_response, re.I):
                #TODO: Get this score value from the db instead of hard
                #coding it here.
                score = 0.3
                reply = "Οὐ κάκον. You're close."
            else:
                score = 0
                reply = "Incorrect. Try again!"

            # Set the increment value for times wrong, depending on score
            if score < 1:
                times_wrong = 1
            else:
                times_wrong = 0

        # Handle errors if the student's response cannot be evaluated
        except re.error:
            redirect(URL('index', args=['error', 'regex']))
            reply = 'Oops! I seem to have encountered an error in this step.'
            readable_short = None
            readable_long = None

        tips = self.tips  # TODO: customize tips for specific errors

        return {'score': score,
                'times_wrong': times_wrong,
                'reply': reply,
                'user_response': user_response,
                'tips': tips}


class Path(object):
    def __init__(self):
        """docstring for __init__"""
        self.completed_steps = []
        self.next_step_id = None

    def get_next_step(self, db=None):
        """docstring for get_next_step"""
        pass


class PathChooser(object):
    def __init__(self):
        """docstring for __init__"""
        pass


class User(object):
    """
    An object representing the current user, including his/her performance
    data and the paths completed and active in this session.
    """

    def __init__(self, userdata, loc_alias, tag_records, tag_progress,
                            attempt_log=None):
        """Initialize a paideia.User object."""
        self.tag_progress = tag_progress
        self.rank = tag_progress['latest_new']
        self.name = userdata['first_name']
        self.user_id = userdata['id']
        self.path = None
        self.completed_paths = None
        self.categories = None
        self.old_categories = None
        self.new_badges = None
        self.blocks = None
        self.inventory = None
        self.cats_counter = 0
        self.session_start = datetime.datetime.utcnow()
        self.last_npc = None
        self.last_loc = None
        self.loc = None

    def get_id(self):
        """Return the id (from db.auth_user) of the current user."""
        return self.user_id

    def _get_start_time(self):
        """docstring for fname"""
        return self.session_start

    def get_new_badges(self):
        """Return a dictionary of tag ids newly introduced or promoted"""
        return self.new_badges

    def get_completed(self):
        """Return a dictionary of paths completed so far during the session."""
        return self.completed_paths

    def get_path(self):
        """Return the currently active Path object."""
        if self.path:
            return self.path
        else:
            path = PathChooser(self.categories).choose()
            self.path = path
            return path

    def _get_categories(self, rank=None, categories=None, old_categories=None,
                            tag_records=None, cats_counter=None):
        """
        Return a categorized dictionary with four lists of tag id's.

        This method is important primarily to decide whether a new
        categorization is necessary before instantiating a Categorizer object
        # do we need to create new categorizer object each time?
        """
        if not rank:
            rank = self.rank
        if not tag_records:
            tag_records = self.tag_records
        if not cats_counter:
            cats_counter = self.cats_counter
        if not categories:
            categories = self.categories
        if not old_categories:
            old_categories = self.old_categories
        # only re-categorize every 10th evaluated step
        if cats_counter < 10:
            self.cats_counter = cats_counter + 1
            return self.categories
        else:
            self.old_categories = self.categories
            c = Categorizer(rank, categories, tag_records)
            cat_result = c.categorize()
            categories = cat_result['categories']
            self.categories = categories
            self.cats_counter = cats_counter + 1
            if cat_result['new_tags']:
                self.set_block('new_tags', cat_result['new_tags'])
            return categories

    def _get_blocks(self):
        """docstring"""
        return self.blocks

    def _set_block(self, block_type, *args):
        """docstring for _set_block"""
        if block_type == 'new_tags':
            self.blocks.append(BlockNewTags(*args))

    def _complete_path(self):
        """docstring"""
        self.completed_paths.append(self.path.get_id())
        self.last_npc = self.path.get_active_step().get_npc()['id']
        self.last_loc = self.path.get_active_step().get_npc()['id']
        self.path = None
        return True


class Categorizer(object):
    """
    A class that categorizes a user's active tags based on past performance.

    The categories range from 1 (need immediate review) to 4 (no review
    needed). Returns a dictionary with four keys corresponding to the four
    categories. The value for each key is a list holding the id's
    (integers) of the tags that are currently in the given category.
    """

    def __init__(self, rank, categories, tag_records):
        """Initialize a paideia.Categorizer object"""
        self.rank = rank
        self.tag_records = tag_records
        self.old_categories = categories

    def categorize_tags(self, rank=None, tag_records=None,
                            old_categories=None, db=None):
        """Return a categorized dictionary of tags"""
        if not rank:
            rank = self.rank
        if not old_categories:
            old_categories = self.old_categories
        if not tag_records:
            tag_records = self.tag_records
        if not db:
            db = current.db

        # if user has not tried any tags yet, start first set
        if tag_records[0] is None:
            categories = {}
            categories['cat1'] = self._introduce_tags()
            return categories
        else:
            # otherwise, categorize tags that have been tried
            categories = self._core_algorithm()
            categories = self._add_untried_tags(categories)
            # Remove any duplicates and tags beyond the user's current ranking
            for k, v in categories.iteritems():
                if v:
                    newv = [t for t in v if db.tags[t].position <= rank]
                    categories[k] = list(set(newv))

            # changes in categorization since last time
            # this is where 'rev' categories are reintroduced
            cat_changes = self._find_cat_changes(categories, old_categories)
            promoted = cat_changes['promoted']
            new_tags = cat_changes['new_tags']
            demoted = cat_changes['demoted']
            tag_progress = cat_changes['categories']

            # If there are no tags left in category 1, introduce next set
            if not categories['cat1']:
                starting = self._introduce_tags()
                categories['cat1'] = starting
                new_tags['cat1'].append(starting)

            # Re-insert 'latest new' to match tag_progress table in db
            tag_progress['latest_new'] = self.rank

            return {'tag_progress': tag_progress,
                    'new_tags': new_tags,
                    'promoted': promoted,
                    'demoted': demoted}

    def _core_algorithm(self, tag_records=None, utcnow=None):
        """
        Return dict of the user's active tags categorized by past performance.

        The record_list argument should be a list of dictionaries, each of
        which includes the following keys and value types:
            {'tag_id': <int>,
             'last_right': <datetime>,
             'last_wrong': <datetime>,
             'times_right': <float>,
             'times_wrong': <float>}

        The return value is a dict with the following keys and value types:
            {'cat1': [int, int ...],
             'cat2': [],
             'cat3': [],
             'cat4': []}

        TODO: Could this be done by a cron job or separate background process?
        TODO: Factor in how many times a tag has been successful or not
        TODO: Require that a certain number of successes are recent
        TODO: Look at secondary tags as well
        """
        categories = {'cat1': [], 'cat2': [], 'cat3': [], 'cat4': []}
        if not utcnow:
            utcnow = datetime.datetime.utcnow()
        if not tag_records:
            tag_records = self.tag_records

        for record in tag_records:
            #note: arithmetic operations yield datetime.timedelta objects
            right_dur = utcnow - record['last_right']
            right_wrong_dur = record['last_right'] - record['last_wrong']

            # spaced repetition algorithm for promotion from cat1
            # ======================================================
            # for category 2
            if ((right_dur < right_wrong_dur)
                    # don't allow promotion from cat1 within 1 day
                    and (right_wrong_dur > datetime.timedelta(days=1))
                    # require at least 10 right answers
                    and (record['times_right'] >= 10)) \
                or ((record['times_right'] > 0)  # prevent zero division error
                    and ((record['times_wrong'] / record['times_right'])
                                                                        <= 0.2)
                    and (right_dur <= datetime.timedelta(days=2))) \
                or ((record['times_wrong'] == 0)  # prevent zero division error
                    and (record['times_right'] >= 20)):
                    # TODO: add condition here requiring recent correct after
                    # a gap in activity.
                    # allow for 1 wrong answer for every 5 correct
                    # promote in any case if the user has never had a wrong
                    # answer in 20+ attempts
                # ==================================================
                # for cat3
                if right_wrong_dur.days >= 7:
                    # ==============================================
                    # for cat4
                    if right_wrong_dur.days > 30:
                        # ==========================================
                        # for immediate review
                        if right_wrong_dur > datetime.timedelta(days=180):
                            category = 'cat1'  # Not tried for 6 months
                        else:
                            category = 'cat4'  # Not due, delta > a month
                    else:
                        category = 'cat3'  # delta between a week and month
                else:
                    category = 'cat2'  # Not due but delta is a week or less
            else:
                category = 'cat1'  # Spaced repetition requires review

            categories[category].append(record['tag_id'])

        return categories

    def _introduce_tags(rank=None, db=None):
        """
        Add the next set of tags to cat1 in the user's tag_progress

        Returns a dictionary of categories identical to that returned by
        categorize_tags
        """
        if not db:
            db = current.db
        if not rank:
            rank = self.rank

        if rank in (None, 0):
            rank == 1
        else:
            rank += 1

        newtags = [t['id'] for t in db(db.tags.position == rank).select()]

        return newtags

    def _add_untried_tags(self, categories, rank=None, db=None):
        """Return the categorized list with any untried tags added to cat1"""
        if not rank:
            rank = self.rank
        if not db:
            db = current.db

        left_out = []
        for r in range(1, rank + 1):
            newtags = [t.id for t in db(db.tags.position == r).select()]
            alltags = list(chain(*categories.values()))
            left_out.extend([t for t in newtags if t not in alltags])
        if left_out:
            categories['cat1'].extend(left_out)

        return categories

    def _find_cat_changes(self, categories, old_categories):
        """Determine whether any of the categorized tags are new or promoted"""
        if old_categories:
            demoted = {}
            new_tags = {}
            promoted = {}
            for category, lst in categories.iteritems():
                if lst:
                    # TODO: does this work to index dictionary keys?
                    catindex = categories.keys().index(category)

                    # was tag in a higher category before?
                    # remove from current cat, place in same level review cat
                    # then re-insert in its old cat (max reached)
                    gt_oldcats = dict((k, old_categories[k]) for k
                           in ['cat1', 'cat2', 'cat3', 'cat4'][catindex+1:])
                    gt_oldcats_flat = [chain([val for cat
                                            in gt_oldcats.values()
                                            if cat for val in cat])]
                    revcat = category.replace('cat', 'rev')
                    for tag in lst:
                        if tag in gt_oldcats_flat:
                            categories[category].pop(tag)
                            demoted[revcat].append(tag)
                            oldcat = [k for k,v in gt_oldcats if v == tag]
                            categories[oldcat].append(tag)

                    # was tag already in this category? Just collect list.
                    same_oldcat = [t for t in lst
                                        if t in old_categories[category]]

                    # was tag in a lower category?
                    # add to dictionary of 'promoted' tags
                    lt_oldcats = dict((k, old_categories[k]) for k
                           in ['cat1', 'cat2', 'cat3', 'cat4'][:catindex])
                    lt_oldcats_flat = [chain([val for cat
                                            in lt_oldcats.values()
                                            if cat for val in cat])]
                    promoted[category] = [t for t in lst
                                            if t in lt_oldcats_flat]

                    # was tag not in any dictionary?
                    # add to dictionary of 'new_tags'
                    new = [t for t in lst if
                                    (t not in same_oldcat) and
                                    (t not in lt_oldcats_flat) and
                                    (t not in gt_oldcats_flat)]
                    if new:
                        new_tags[category] = new
                        # TODO: also record in badges_begun
            # TODO: make sure to add any 'rev' categories that are empty
            return {'categories': categories,
                    'demoted': demoted,
                    'promoted': promoted,
                    'new_tags': new_tags}
        else:
            return {'categories': categories,
                    'demoted': None,
                    'promoted': None,
                    'new_tags': None}

    def _clean_tag_records(record_list=None, db=None):
        """
        Find and remove any duplicate entries in record_list.

        This method is really safeguarding against faulty db updating in Walk.
        It should probably be deprecated, or should simply log a silent error
        when a duplicate is detected.
        """
        discrete_tags = set([t['tag'] for t in record_list])
        kept = []
        if len(record_list) > len(discrete_tags):
            for tag in discrete_tags:
                shortlist = record_list.find(lambda row: row.tag == tag)
                kept.append(shortlist[0].id)
                if len(shortlist) > 1:
                    for row in shortlist[1:]:
                        row.delete_record()
            record_list = record_list.find(lambda row: row.id in kept)


class Block(object):
    """docstring"""
    pass
