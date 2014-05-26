import calendar
import datetime
# from collections import Counter
from dateutil.parser import parse
import traceback
from copy import copy
from pytz import timezone, utc
from gluon import current, DIV, SPAN, A, URL, UL, LI, B
from gluon import TAG
from paideia_utils import make_json, load_json
from paideia import Categorizer
from pprint import pprint
from itertools import chain, groupby


class Stats(object):
    '''
    Provides various statistics on student performance.

    Exposes the following methods as its public interface:

    :active_tags():         Returns
    :get_max():             Returns the user's current set
    :get_sets():            Returns a list of the tag id's in each of the four
                                categories, along with their badge names.
    :tags_over_time():      Returns a dictionary of dates with the number of
                                attempts for each active tag on that date.
    :sets_over_time():
    :paths_over_time():     Returns a dictionary of dates with the number of
                                attempts for each active tag on that date.
    :monthcal():            Returns an html calendar for one month of user
                                performance stats.
    :store_stats():         Returns True if it successfully collates any
                                fresh performance data for the current user in
                                db.user_stats. Otherwise returns False


    :set_badges_scale():    Returns a dictionary of set numbers with lists of
                             badges in each set as values. The badges should
                             be represented by a tuple including tag_id,
                             badge_name, and badge_description.
    badge_level_ring - ring chart of badges in each
    badges_time_line - multiple line chart showing number of badges in
                        each level over time.
    attempts_time_line - line chart showing number of attempts per day (week)?
    attempts_step_time_line - stacked area chart showing number of attempts
                                for each step attempted per day.
    attempts_tag_time_line - stacked area chart showing number of attempts
                                for each step attempted per day.
    attempts_set_time_line - stacked area chart showing number of attempts
                                for each step attempted per day.

    Allows reporting on:
        - badges/level

        - trw/day/badge
        - trw/day/level
        - trw/day/set
        - trw/day/step

        - attempts/day (total)
        - attempts/day/level, badge, set, step

        - count badges over time (total, by set, by level)
        Flag:
            - repeated steps the same day
            - excessive changes in stats
    '''
    Name = "paideia_stats"

    def __init__(self, user_id=None, auth=None, cache=None, duration=None):
        """
        Initialize Stats object for tracking paideia user statistics.

        At this stage compiles
        - basic user information (user_id, auth_user row, readable name)
        - tag_progress information (dict)
        - user's tag records,

        """
        db = current.db
        auth = current.auth
        self.utcnow = datetime.datetime.utcnow()
        self.alerts = {}

        # user info --------------------------------------------------
        user_id = auth.user_id if user_id is None else user_id
        self.user_id = user_id
        self.user = db.auth_user(user_id)
        self.name = '{}, {}'.format(self.user.last_name, self.user.first_name)

        # class/group info --------------------------------------------------
        msel = db((db.auth_membership.user_id == self.user_id) &
                  (db.auth_membership.group_id == db.auth_group.id)).select()
        try:
            self.targetcount = [m.auth_group.paths_per_day for m in msel
                                if m.auth_group.paths_per_day][0]
        except IndexError:  # no group target for user
            self.targetcount = 20

        # progress through tag sets and levels ---------------------
        self.tag_progress = db(db.tag_progress.name == self.user_id
                               ).select().first().as_dict()
        self.tag_recs = db(db.tag_records.name == self.user_id
                           ).select().as_list()  # cacheable=True
        # TODO: find and notify re. duplicate tag_records rows
        self.badge_levels, self.review_levels = self._find_badge_levels()
        self.tags = [tup[1] for v in self.badge_levels.values() for tup in v]

        # date of each tag promotion
        self.badges_begun = db(db.badges_begun.name == self.user_id).select()
        if len(self.badges_begun) > 1:
            self.alerts['duplicate badges_begun records'] = [bb.id for bb
                                                        in self.badges_begun]

    def get_name(self):
        """
        Return the specified user's name as a single string, last name first.
        """
        return self.name

    def store_stats(self, statsdict, lastdt):
        '''
        Store aggregate user statistics provided by statsdict in db.user_stats.

        Argument lastdt is the updated datetime of the last user_stats row for
        the current user. This is used to determine whether that last row needs
        to be completed with data from statsdict.

        '''
        # TODO: Should there also be an annual aggregate?
        db = current.db
        data = {}
        for year, weeks in statsdict.iteritems():
            for weeknum, weekstuff in weeks.iteritems():
                dts = sorted(weekstuff[0].keys())
                done = 1 if not weeknum == weeks.keys()[-1] else 0

                weekdata = {'name': self.user_id,
                            'year': year,
                            'week': weeknum,
                            'updated': datetime.datetime.now(),
                            'day1': dts[0], 'day2': dts[1], 'day3': dts[2],
                            'day4': dts[3], 'day5': dts[4], 'day6': dts[5],
                            'day7': dts[6],
                            'count1': dts[0], 'count2': dts[1], 'count3': dts[2],
                            'count4': dts[3], 'count5': dts[4], 'count6': dts[5],
                            'count7': dts[6],
                            'logs_by_tag': make_json(weekstuff[1]),
                            'logs_right': weekstuff[2],
                            'logs_wrong': weekstuff[3],
                            'done': done
                            }
                # finish any unfinished week
                if year == statsdict.keys()[0] and \
                        weeknum == weeks.keys()[0] and \
                        lastdt.isocalendar()[1] == weeks.keys()[0] and \
                        lastdt.isocalendar()[0] == year:
                    openrow = db(db.user_stats.name == self.user_id
                                 ).select().last()

                    weekdata['updated'] = datetime.datetime.now()
                    for f in ['count1', 'count2', 'count3', 'count4',
                              'count5', 'count6', 'count7']:
                        weekdata[f].extend(openrow[f])
                    opentags = load_json(openrow['logs_by_tag'])
                    for k, v in weekdata['logs_by_tag']:
                        weekdata['logs_by_tag'][k].extend(opentags[k])
                    weekdata['logs_right'] = weekstuff[2]
                    weekdata['logs_wrong'] = weekstuff[3]
                # or add new row
                data.append(weekdata)

    """
    DEPRECATED
    def step_log(self, logs=None, user_id=None, duration=None):
        '''
        Get record of a user's steps attempted in the last seven days.

        TODO: move this aggregate data to a db table "user_stats" on calculation.
        '''
        db = current.db
        # now = self.utcnow
        # user_id = self.user_id
        duration = self.duration
        logs = self.logs

        logset = []
        stepset = set(l['step'] for l in logs)
        tag_badges = self.tag_badges

        for step in stepset:
            steprow = db.steps[step].as_dict()
            steplogs = [l for l in logs if l['step'] == step]
            stepcount = len(steplogs)
            stepright = [s for s in steplogs if abs(s['score'] - 1) < 0.001]
            stepwrong = [s for s in steplogs if abs(s['score'] - 1) >= 0.001]

            try:
                last_wrong = max([s['dt_attempted'] for s in stepwrong if
                                 s['dt_attempted']])
                if isinstance(last_wrong, str):
                    last_wrong = parse(last_wrong)
                last_wrong = datetime.datetime.date(last_wrong)
            except ValueError:
                last_wrong = 'never'

            try:
                right_since = len([s for s in stepright
                                if s['dt_attempted'] > last_wrong])
            except TypeError:
                right_since = stepcount
            steptags = {t: {'tagname': tag_badges[t]['tag'],
                            'badge': tag_badges[t]['badge'],
                            'description': tag_badges[t]['description']}
                        for t in steprow['tags']
                        if t in tag_badges.keys()}
            # check for tags without badges
            # TODO: move this check to maintenance cron job
            for t in steprow['tags']:
                if t not in tag_badges.keys():
                    print 'There seems to be no badge for tag {}'.format(t)
                    print 'Removing tag'
                    newtags = steprow['tags']
                    newtags.remove(t)
                    print 'new tags are', newtags
                    db.steps[step] = {'tags': newtags}  # shorthand update
                    mail = current.mail
                    mail.send(mail.settings.sender,
                            'Paideia error: Removed bad tag',
                            'There seems to be no badge for tag {}. That tag '
                            'number has been removed from step '
                            '{}'.format(t, steprow['id']))
            step_dict = {'step': step,
                         'count': stepcount,
                         'right': len(stepright),
                         'wrong': len(stepwrong),
                         'last_wrong': last_wrong,
                         'right_since': right_since,
                         'tags': steptags,
                         'prompt': steprow['prompt'],
                         'logs': steplogs}
            logset.append(step_dict)

        return {'loglist': logset, 'duration': duration}
    """

    def _add_tag_data(self, tag_recs):
        """
        Return list of tag records with additional fields for tag information.
        """
        db = current.db
        for t in tag_recs:
            trow = db.tags(t['tag'])
            if not trow:
                brow = None
            else:
                brow = db(db.badges.tag == trow.id).select().first()
            try:
                if trow.tag_position > 100:
                    t['set'] = None
                else:
                    t['set'] = trow.tag_position
            except (RuntimeError, AttributeError):
                t['set'] = None
            try:
                t['slides'] = trow.slides
            except (RuntimeError, AttributeError):
                t['slides'] = None
            try:
                t['bname'] = brow.badge_name
                t['bdescr'] = brow.description
            except (RuntimeError, AttributeError):
                t['bname'] = 'missing badge for tag {}'.format(t['tag'])
                t['bdescr'] = None
        return tag_recs

    def _add_promotion_data(self, tag_recs):
        """
        Return list of tag records with additional fields for promoriont data.

        New fields are:
            - dt_cat1, dt_cat2, dt_cat3, dt_cat4
            - prettydate_cat1, prettydate_cat2, prettydate_cat3,
              prettydate_cat4
        """
        for idx, t in enumerate(tag_recs):
            try:
                bbrows = [b for b in self.badges_begun if b.tag == t['tag']][0]
            except IndexError:
                bbrows = None

            for k in range(1, 5):
                cat = 'cat{}'.format(k)
                dt = self._local(bbrows[cat]) if bbrows and bbrows[cat] else None
                prettydate = dt.strftime('%b %e, %Y') \
                    if isinstance(dt, datetime.datetime) else None
                tag_recs[idx]['{}_reached'.format(cat)] = (dt, prettydate)

        return tag_recs

    def _add_log_data(self, tag_recs):
        """
        Add a key-value pair giving log counts to each tag record.

        logs_by_week:   dict of {weeknumber: {date: [list of log ids]} including only
                        those attempts for steps tagged with this tag.

        logs_right:     list of log ids for correct attempts with this tag.

        logs_wrong:     list of log ids for incorret attempts with this tag.
        """
        db = current.db
        # usrows = db(db.user_stats.name == self.user_id).select()
        usrows = self._get_logs_for_range()
        for t in tag_recs:
            tag = t['tag']
            t['logs_by_week'] = copy(usrows)
            t['logs_right'] = []
            t['logs_wrong'] = []
            for year, yeardata in usrows.iteritems():
                for weeknum, yrdata in yeardata.iteritems():
                    try:
                        bytag = yrdata[1][str(tag)]
                        weeklogs = {}
                        for day, count in yrdata[0].iteritems():
                            try:
                                weeklogs[parse(day)] = [c for c in count if c in bytag]
                            except (AttributeError, TypeError):
                                weeklogs[day] = [c for c in count if c in bytag]
                        t['logs_by_week'][year][weeknum] = weeklogs
                        t['logs_right'].extend([l for l in yrdata[2] if l in bytag])
                        t['logs_wrong'].extend([l for l in yrdata[3] if l in bytag])
                    except KeyError:  # no logs for this tag that week
                        pass
                    except IndexError:
                        print 'malformed usrows for ', tag, 'in week', weeknum
            all_logs = t['logs_right'] + t['logs_wrong']
            all_rows = db(db.attempt_log.id.belongs(all_logs)).select(db.attempt_log.score)
            t['avg_score'] = sum([r.score for r in all_rows]) / len(all_rows) \
                if all_rows else None
            if isinstance(t['avg_score'], float):
                t['avg_score'] = round(t['avg_score'], 1)
        return tag_recs

    def active_tags(self, now=None):
        '''
        Find the tags that are currently active for this user, categorized 1-4.

        Returns a list of dictionaries, one per active tag for this user. Each
        dictionary includes the following keys:
        - from db.tag_records
            [tag]               int, tag row id
            [times_right]       double, total number of times right
            [times_wrong]       double, total number of times wrong
            [tlw]               datetime
            [tlr]               datetime

        ------calculated here -------------------------------------------------
            [rw_ratio]          ratio of times_right to times_wrong as a double.
            [delta_w]           length of time since last wrong answer
            [delta_r]           length of time since last right answer
            [delta_rw]          length of time between last right answer
                                        and previous wrong answer (0 if last
                                        answer was wrong).

        ------from self.badge_levels and self.review_levels -------------------
            [curlev]                highest level attained for tag
            [revlev]                current level used for path selection

        ------from _add_tag_data() --------------------------------------------
        - from db.tags
            [set]               the "position" in set progression, int
        - from db.badges
            [bname]
            [bdesc]

        ------from _add_progress_data()----------------------------------------
        - from db.badges_begun
            [cat1_reached]          a tuple of (datetime, prettydate string)
            [cat2_reached]          a tuple of (datetime, prettydate string)
            [cat3_reached]          a tuple of (datetime, prettydate string)
            [cat4_reached]          a tuple of (datetime, prettydate string)

        ------from ????--------------------------------------------------------
        - from db.user_stats
            [datecounts]            a dictionary of dates with the number of
                                        right and wrong attempts on each day.
        - from db.steps
            [steplist]              a list of steps tagged with this tag
            [steplist2]             a list of steps tagged with this tag as
                                        tags_secondary
            [steplist3]             a list of steps tagged with this tag as
                                        tags_ahead

        '''
        tr = [r for r in self.tag_recs if r['tag'] in self.tags]
        # shorten keys for readability
        shortforms = {'tlast_right': 'tlr',
                      'tlast_wrong': 'tlw',
                      'times_right': 'tright',
                      'times_wrong': 'twrong'}
        for k, alt in shortforms.iteritems():
            for idx, row in enumerate(tr):
                if k in row.keys():
                    tr[idx][alt] = row[k]
                    del tr[idx][k]
        now = self.utcnow if not now else now
        for idx, t in enumerate(tr):
            # remove unnecessary keys
            tr[idx] = {k: v for k, v in t.iteritems()
                    if k not in ['id', 'name', 'in_path', 'step',
                                 'secondary_right']}

            # get right/wrong ratio
            try:
                tr[idx]['rw_ratio'] = t['tright'] / t['twrong']
            except (ZeroDivisionError, TypeError):
                tr[idx]['rw_ratio'] = t['tright']

            # parse last_right and last_wrong into readable form
            try:
                t['tlw'] = tr[idx]['tlw'] = parse(t['tlw'])
                t['tlw'] = tr[idx]['tlw'] = parse(t['tlr'])
            except AttributeError:
                pass

            # get time deltas
            for i in ['r', 'w']:
                try:
                    tr[idx]['delta_' + i] = now - t['tl' + i]
                except TypeError:  # record is timezone-aware, shouldn't be yet
                    t['tl' + i] = t['tl' + i].replace(tzinfo=None)
                    tr[idx]['delta_' + i] = now - t['tl' + i]
            tr[idx]['delta_rw'] = tr[idx]['tlr'] - tr[idx]['tlr'] \
                if tr[idx]['tlr'] > tr[idx]['tlw'] \
                else datetime.timedelta(days=0)

            # localize datetimes and add readable string for display
            for i in ['tlr', 'tlw']:
                t[i] = self._local(t[i])
                strf = '%b %e' if t[i].year == now.year else '%b %e, %Y'
                tr[idx][i] = (t[i], t[i].strftime(strf))

            # add level data
            pprint(self.badge_levels)
            tr[idx]['curlev'] = [l for l, tgs in self.badge_levels.iteritems()
                                 if t['id'] in [tg[1] for tg in tgs]]
            tr[idx]['revlev'] = [l for l, tgs in self.review_levels.iteritems()
                                 if t['id'] in [tg[1] for tg in tgs]]

            # add rw_ratio
            try:
                tr[idx]['rw_ratio'] = t['tright'] / t['twrong']
            except (ZeroDivisionError, TypeError):
                tr[idx]['rw_ratio'] = t['tright']


        try:
            tr = self._add_tag_data(tr)
            tr = self._add_promotion_data(tr)
            # tr = self._add_log_data(tr)
            self.tagrecs_expanded = tr
            return tr  # make_json(tr.as_list())
        except Exception:
            print traceback.format_exc(5)
            return None

    def get_max(self):
        """
        Return an integer corresponding to the user's furthest badge set.

        The 'badge set' is actually the series of ints in db.tags.tag_position.

        """
        max_set = self.tag_progress['latest_new'] \
            if self.tag_progress['latest_new'] else 1
        return max_set

    def _local(self, dt, tz=None):
        """
        Return a datetime object localized to self.user's time zone.

        NB: The pytz.localize function just adds timezone information to the
        utc datetime object. To actually adjust the datetime you need to get
        the local offset from utc and add it manually.

        The tz argument is simply for dependency injection during testing.

        """
        tz = self.user.tz_obj if not tz else tz
        dt = utc.localize(dt)
        try:
            newdt = tz.normalize(dt.astimezone(tz))
        except (TypeError, AttributeError):
            dt = parse(dt)
            newdt = tz.normalize(dt.astimezone(tz))
        return newdt

    def get_badge_levels(self):
        """
        Return the current self.badge_levels value.
        """
        return self.badge_levels

    def _find_badge_levels(self):
        """
        Return a dictionary listing the user's badges in levels 1-4.
        """
        db = current.db
        rank = self.tag_progress['latest_new']
        categories = {k: v for k, v in self.tag_progress.iteritems()
                      if k != 'latest_new'}
        c = Categorizer(rank, categories, self.tag_recs,
                        self.user_id, utcnow=self.utcnow)
        bls = c.categorize_tags()['tag_progress']
        bl_ids = {k: v for k, v in bls.iteritems() if k[:3] == 'cat'}
        badge_levels = {}
        for k, v in bl_ids.iteritems():
            level = int(k[3:])
            badgelist = []
            for tag in v:
                mybadge = db.badges(db.badges.tag == tag)
                badge_name = mybadge.badge_name if mybadge \
                    else 'tag id: {}'.format(tag)
                badgelist.append((badge_name, tag))
            badge_levels[level] = badgelist

        rl_ids = {k: v for k, v in bls.iteritems() if k[:3] == 'rev'}
        review_levels = {}
        for k, v in rl_ids.iteritems():
            level = int(k[3:])
            badgelist = []
            for tag in v:
                mybadge = db.badges(db.badges.tag == tag)
                badge_name = mybadge.badge_name if mybadge \
                    else 'tag id: {}'.format(tag)
                badgelist.append((badge_name, tag))
            review_levels[level] = badgelist

        return badge_levels, review_levels

    def get_goal(self):
        """
        """
        term = "This term"
        set_target = None
        sets_left = None
        return term, set_target, sets_left

    def _make_logs_into_weekstats(self, logs):
        """
        Return a dictionary of the provided log data structured as in db.user_stats.

        NB: datetime.isocalendar is weird at the beginning and end of a year.
        The first week of a year is the first in which there is a Thursday. So
        an initial Friday or Saturday can be left in the previous year's last
        week or a final Mon, Tues, Wed can be added to the next year's first
        week.
        """
        db = current.db
        logs = logs.as_list()
        for log in logs:
            # use local time for organizing of weeks/days
            # but keep dt_attempted as utc
            log['isocal'] = self._local(log['dt_attempted']).isocalendar()

        years_iter = groupby(logs, key=lambda log: log['isocal'][0])
        weekstats = {}
        for yr, yearlogs in years_iter:
            weeks_iter = groupby(yearlogs,
                                           key=lambda log: log['isocal'][1])
            weeksdict = {}
            for weeknum, weeklogs in weeks_iter:
                weeklogs = [l for l in weeklogs]
                counts = {}
                logs_right = [l['id'] for l in weeklogs
                              if abs(l['score'] - 1) < 0.001]
                logs_wrong = [l['id'] for l in weeklogs
                              if abs(l['score'] - 1) >= 0.001]
                logs_by_tag = {}
                for log in weeklogs:
                    tags = db.steps(log['step']).tags
                    for t in tags:
                        logs_by_tag.setdefault(t, []).append(log['id'])
                days_iter = groupby(weeklogs,
                                              key=lambda d: self._local(d['dt_attempted']).date())
                for day, daylogs in days_iter:
                    daylogs = [d['id'] for d in daylogs]
                    counts[day] = daylogs
                weeksdict[weeknum] = (counts, logs_by_tag,
                                      logs_right, logs_wrong)
            weekstats[yr] = weeksdict
        return weekstats

    def _get_logs_for_range(self, startdate=None, stopdate=None):
        '''
        Assemble and return a dictionary of weeks with log-data for each day.

        {year: {week#: ({datetime: [log ids],
                         datetime: [log ids],
                         datetime: [log ids],
                         datetime: [log ids],
                         datetime: [log ids],
                         datetime: [log ids],
                         datetime: [log ids]},
                        {tagid: [logs with that tag],
                         tagid: [logs]},
                        [logs_right],
                        [logs_wrong]
                        ),
                }
         }
        '''
        db = current.db
        # get utc equivalents of start and stop in user's time zone
        naivestop = stopdate if stopdate else self.utcnow
        naivestart = startdate if startdate else datetime.datetime(2012, 1, 1, 0, 0)
        tz_name = self.user.time_zone if self.user.time_zone \
            else 'America/Toronto'
        tz = timezone(tz_name)
        stopwtz = tz.localize(naivestop)
        startwtz = tz.localize(naivestart)
        ustop = stopwtz.astimezone(utc)
        ustart = startwtz.astimezone(utc)

        usdict = {}
        usrows = db((db.user_stats.name == self.user_id) &
                    (db.user_stats.day7 > ustart) &
                    (db.user_stats.day7 < ustop)).select()
        usrows = usrows.as_list()
        if usrows:
            # weeks and days organized by user's local time
            # but datetimes themselves are still utc
            years = range(ustart.year, ustop.year + 1)
            usdict = {}
            for year in years:
                myrows = [r for r in usrows if r['year'] == year]
                usdict[year] = {}
                for m in myrows:
                    usdict[year][m['week']] = ({m['day1']: m['count1'],
                                                m['day2']: m['count2'],
                                                m['day3']: m['count3'],
                                                m['day4']: m['count4'],
                                                m['day5']: m['count5'],
                                                m['day6']: m['count6'],
                                                m['day7']: m['count7']
                                                },
                                               load_json(m['logs_by_tag']),
                                               m['logs_right'],
                                               m['logs_wrong'])
        # add new logs without user_stats rows
        updated = usrows[-1]['updated'] if usrows else ustart
        newlogs = db((db.attempt_log.name == self.user_id) &
                     (db.attempt_log.dt_attempted < ustop) &
                     (db.attempt_log.dt_attempted > updated)).select()
        if newlogs:
            newus = self._make_logs_into_weekstats(logs=newlogs)
            # newstored = self.store_stats(newus)
            if usrows:
                usdict = usrows
                usdict.extend(newus)
            else:
                usdict = newus

        return usdict  # newstored

    def monthcal(self, year=None, month=None):
        '''
        Assemble and return an html calendar displaying the number of
        attempts per day in the month 'month' for the user represented
        by self.user_id.

        The calendar is returned as a web2py DIV helper.

        The calendar html structure is:

        <table border="0" cellpadding="0" cellspacing="0" class="month">\n
        <tr>
            <th class="month" colspan="7">December 2013</th>
        </tr>\n
        <tr>
            <th class="sun">Sun</th>
            <th class="mon">Mon</th>
            <th>class="tue">Tue</th>
            <th>class="wed">Wed</th>
            <th>class="thu">Thu</th>
            <th>class="fri">Fri</th>
            <th>class="sat">Sat</th>
        </tr>\n
        <tr>
            <td class="sun">1</td>
            <td class="mon">2</td>
            <td class="tue">3</td>
            <td class="wed">4</td>
            <td class="thu">5</td>
            <td class="fri">6</td>
            <td class="sat">7</td>
        </tr>\n
        ...
        <tr>
            <td class="sun">29</td>
            <td class="mon">30</td>
            <td class="tue">31</td>
            <td class="noday">\xc2\xa0</td>
            <td class="noday">\xc2\xa0</td>
            <td class="noday">\xc2\xa0</td>
            <td class="noday">\xc2\xa0</td>
        </tr>\n
        </table>\n
        '''
        # TODO: get settings for this user's class requirements
        month = datetime.date.today().month if not month else int(month)
        year = datetime.date.today().year if not year else int(year)
        monthend = calendar.monthrange(year, month)[1]
        monthname = calendar.month_name[month]
        rangelogs = self._get_logs_for_range(datetime.datetime(year, month, 1, 0, 0),
                                             datetime.datetime(year, month, monthend, 23, 59))
        newmcal = calendar.HTMLCalendar(6).formatmonth(year, month)
        mycal = TAG(newmcal)
        try:
            try:
                daycounts = {parse(k): len(v)
                             for week in rangelogs[year].values()
                             for k, v in week[0].iteritems()}
            except (TypeError, AttributeError):
                daycounts = {k: len(v)
                             for week in rangelogs[year].values()
                             for k, v in week[0].iteritems()}
            # Create html calendar and add daily count numbers
            for week in mycal.elements('tr'):
                weekcount = 0
                for day in week.elements('td[class!="noday"]'):
                    try:
                        mycount = [v for k, v in daycounts.iteritems()
                                   if k.day == int(day[0])][0]
                        countspan = SPAN(mycount, _class='daycount')
                        if mycount >= self.targetcount:
                            countspan['_class'] = 'daycount full'
                            weekcount += 1
                        day.append(countspan)
                    except (ValueError, IndexError):
                        pass
                    day[0] = SPAN(day[0], _class='cal_num')
                if weekcount >= 5:
                    week[-1].append(SPAN(_class='icon-ok success'))
        except KeyError:  # if no logs for this month
            pass

        dropdown = self._monthpicker(calendar, year, month, monthname)
        mycal.elements('th.month')[0][0] = dropdown
        for link in self._navlinks(year, month):
            mycal.elements('th.month')[0].insert(0, link)
        wrap = DIV(_class='paideia_monthcal')
        wrap.append(SPAN('Questions answered each day in',
                         _class='monthcal_intro_line'))
        wrap.append(mycal)
        # TODO: Add weekly summary counts to the end of each table

        return wrap

    def _navlinks(self, year, month):
        """
        Return two html anchor elements for navigating to the previous and next
        months.
        """
        prev_month = (month - 1) if month > 1 else 12
        prev_year = year if prev_month < 12 else year - 1
        next_month = (month + 1) if month < 12 else 1
        next_year = year if next_month > 1 else year + 1
        links = {'next': (next_month, next_year, 2,
                          SPAN(_class='icon-chevron-right')),
                 'previous': (prev_month, prev_year, 0,
                              SPAN(_class='icon-chevron-left'))}
        linktags = []
        for k, v in links.iteritems():
            mylink = A(v[3], _href=URL('reporting', 'calendar.load',
                                       args=[self.user_id, v[1], v[0]]),
                       _class='monthcal_nav_link {}'.format(k),
                       cid='tab_calendar')
            linktags.append(mylink)
        return linktags

    def _monthpicker(self, calendar, year, month, monthname):
        """
        Return an html dropdown menu of months since 2011.
        """
        years = range(year, 2011, -1)
        picker_args = {'_class': 'dropdown-menu',
                       '_role': 'menu',
                       '_aria-labelledby': 'month-label'}
        picker = UL(**picker_args)
        for y in years:
            for m in range(12, 1, -1):
                if not (m > month and y == year):
                    picker.append(LI(A('{} {}'.format(calendar.month_name[m], y),
                                    _href=URL('reporting', 'calendar.load',
                                              args=[self.user_id, y, m]),
                                    _tabindex='-1')))
            picker.append(LI(_class='divider'))

        label_args = {'_id': 'month-label',
                      '_role': 'button',
                      '_class': 'dropdown-toggle',
                      '_data-toggle': 'dropdown',
                      '_data-target': '#',
                      '_href': '#'}
        dropdown = SPAN(A('{} {} '.format(monthname, year),
                         B(_class='caret'),
                         **label_args),
                       picker,
                       _class='dropdown')

        return dropdown


def week_bounds(weekday=None):
    '''
    Return datetime objects representing the last day of this week and previous.

    alternate version:

    def week_magic(day):
        day_of_week = day.weekday()

        to_beginning_of_week = datetime.timedelta(days=day_of_week)
        beginning_of_week = day - to_beginning_of_week

        to_end_of_week = datetime.timedelta(days=6 - day_of_week)
        end_of_week = day + to_end_of_week

        return (beginning_of_week, end_of_week)
    '''
    today = datetime.datetime.utcnow() if not weekday else weekday
    thismonth = calendar.monthcalendar(today.year, today.month)

    thisweek = [w for w in thismonth if today.day in w][0]
    today_index = thisweek.index(today.day)
    tw_index = thismonth.index(thisweek)

    lastweek = thismonth[tw_index - 1]
    delta = datetime.timedelta(days=(8 + today_index))
    lw_firstday = today - delta

    tw_prev = None
    if 0 in thisweek:
        if thisweek.index(0) < thisweek.index(today.day):
            lastmonth = calendar.monthcalendar(today.year, today.month - 1)
            tw_prev = lastmonth[-1]
            lastweek = lastmonth[-2]
            thisweek = [d for d in chain(thisweek, tw_prev) if d != 0]

    lw_prev = None
    if 0 in lastweek:
        lastmonth = calendar.monthcalendar(today.year, today.month - 1)
        lw_prev = lastmonth[-1]
        lastweek = [d for d in chain(lastweek, lw_prev) if d != 0]

    return lastweek, lw_firstday, thisweek


def get_weeks(year=None):
    """
    Return a list of lists, one for each week in the year.

    The list for each week contains seven datetime.datetime objects, one for
    each weekday, in their calendar order.
    """
    year = datetime.datetime.utcnow().year if not year else year
    cal = calendar.Calendar().yeardatescalendar(year)
    months = [m for row in cal for m in row]
    weeks = []
    for m in months:
        for w in m:
            if w not in weeks:
                weeks.append(w)
    return weeks


def get_offset(user):
    '''
    Return the user's offset from utc time based on their time zone.
    '''
    try:
        user.auth_user.offset
    except AttributeError:
        today = datetime.datetime.utcnow()
        now = timezone('UTC').localize(today)
        tz_name = user.auth_user.time_zone if user.auth_user.time_zone \
            else 'America/Toronto'
        offset = now - timezone(tz_name).localize(today)  # when to use "ambiguous"?
    return offset
