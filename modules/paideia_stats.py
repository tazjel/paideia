import calendar
import datetime
from pytz import timezone
from gluon import current, DIV, H4, TABLE, THEAD, TBODY, TR, TD, SPAN, A, URL
from pprint import pprint


class Stats(object):
    '''
    Provides various statistics on student performance.
    '''
    Name = "paideia_stats"
    verbose = True

    def __init__(self, user_id=None, auth=None):
        if self.verbose: print '\nInitializing Stats object =================='
        if auth is None:
            auth = current.auth
        if user_id is None:
            user_id = auth.user_id
        self.user_id = user_id
        #assert type(user_id) == str
        self.loglist = self.log_list()

    def step_log(self, logs=None, user_id=None, duration=None, db=None):
        '''
        Get record of a user's steps attempted in the last seven days.
        '''
        now = datetime.datetime.utcnow()
        if user_id is None:
            user_id = self.user_id
            print 'user:', user_id
        if duration is None:
            duration = datetime.timedelta(days=7)
        if db is None:
            db = current.db
        if logs is None:
            logs = db((db.attempt_log.id > 0) &
                    (db.attempt_log.name == user_id)).select()
            print len(logs)
            logs = logs.find(lambda row: (now - row.dt_attempted) <= duration)
            print len(logs)
        logset = []
        stepset = set(l.step for l in logs)

        for step in stepset:
            steprow = db.steps[step]
            steplogs = logs.find(lambda row: row.step == step)
            stepcount = len(steplogs)
            stepright = steplogs.find(lambda row: row.score == 1)
            stepwrong = steplogs.find(lambda row: row.score == 0)

            try:
                last_wrong = max([s.dt_attempted for s in stepwrong])
                last_wrong = datetime.datetime.date(last_wrong)
            except ValueError:
                last_wrong = 'never'

            try:
                right_since = len([s for s in stepright
                                if s.dt_attempted > last_wrong])
            except TypeError:
                right_since = stepcount

            steptags = {t: {'tagname': db.tags[t].tag,
                        'badge': db(db.badges.tag == t).select().first().badge_name}
                            for t in steprow.tags}
            print steptags

            step_dict = {'step': step,
                        'count': stepcount,
                        'right': len(stepright),
                        'wrong': len(stepwrong),
                        'last_wrong': last_wrong,
                        'right_since': right_since,
                        'tags': steptags,
                        'prompt': steprow.prompt,
                        'logs': steplogs,
                        'duration': duration}
            logset.append(step_dict)
            if logset == []:
                logset = [{'duration': duration}]
        return logset

    def active_tags(self):
        '''
        Find the
        '''
        if self.verbose: print 'calling Stats.active_tags() ------------------'
        db = current.db
        debug = True
        try:
            atag_s = db(db.tag_progress.name == self.user_id).select().first()
            atags = {}
            atags1 = atags['cat1'] = list(set(atag_s.cat1))  # remove dup's
            atags2 = atags['cat2'] = list(set(atag_s.cat2))
            atags3 = atags['cat3'] = list(set(atag_s.cat3))
            atags4 = atags['cat4'] = list(set(atag_s.cat4))
            atags5 = atags['rev1'] = list(set(atag_s.rev1))  # remove dup's
            atags6 = atags['rev2'] = list(set(atag_s.rev2))
            atags7 = atags['rev3'] = list(set(atag_s.rev3))
            atags8 = atags['rev4'] = list(set(atag_s.rev4))
            for c, lst in atags.iteritems():
                # allow for possibility that tag hasn't got badge yet
                try:
                    atags[c] = [db(db.badges.tag ==
                                   t).select().first().badge_name for t in lst]
                    if debug: print 'found badges for tags', lst
                except AttributeError:
                    if debug: print 'no badges for tags', lst
                    pass
            try:
                total = []
                for c in [atags1, atags2, atags3, atags4]:
                    if c: total.extend(c)
                atags['total'] = len(total)
            except:
                atags['total'] = 'an unknown number of'

            latest_rank = atag_s.latest_new
            # fix any leftover records with latest rank stuck at 0
            if latest_rank == 0:
                atag_s.update_record(latest_new=1)
                latest_rank = 1
                if debug: print 'position in tag progression:', latest_rank
            latest_tags = db(db.tags.position == latest_rank).select()
            if latest_tags is None:
                latest_badges = ['Sorry, I can\'t find it!']
            else:
                latest_badges = []
                for t in latest_tags:
                    l = db(db.badges.tag == t).select().first()
                    if l:
                        latest_badges.append(l.badge_name)
                        if debug: print 'found record for tag', t
                    else:
                        if debug: print 'no record for tag', t
                        pass
                if latest_badges is None:
                    latest_badges = ['Sorry, I couldn\'t find that!']
                atags['latest'] = latest_badges
        except Exception, e:
            print type(e), e
            atags['total'] = "Can't calculate total number of active badges."
            atags['latest'] = ["Can't find the most recent badge awarded."]

        return atags

    def log_list(self):
        """
        Collect and return a dictionary in which the keys are datetime.date()
        objects and the values are an integer representing the number of
        attempt_log entries on that date by the user represented by
        self.user_id.

        These datetimes and totals are corrected from UTC to the user's
        local time zone.
        """
        if self.verbose: print 'calling Stats.log_list() ---------------------'
        debug = False
        db = current.db

        log_query = db(db.attempt_log.name == self.user_id)
        logs = log_query.select(db.attempt_log.dt_attempted)
        loglist = {}

        #offset from utc time used to generate and store time stamps
        #TODO: Get utc time offset dynamically from user's locale
        if debug: print db.auth_user[self.user_id]
        tz_name = db.auth_user[self.user_id].time_zone
        tz = timezone(tz_name)
        if debug: print 'timezone =', tz

        # count the number of attempts for each unique date
        for log in logs:
            newdatetime = tz.fromutc(log.dt_attempted)
            newdate = datetime.date(newdatetime.year,
                                    newdatetime.month,
                                    newdatetime.day)
            if newdate in loglist:
                loglist[newdate] += 1
            else:
                loglist[newdate] = 1

        return loglist

    def monthstats(self, year=None, month=None):
        '''
        Assemble and return a dictionary with the weeks. If the year and
        month desired are not supplied as arguments (in integer form),
        this method will by default provide stats for the current month and
        year.
        '''
        if self.verbose: print 'calling Stats.monthstats() -------------------'
        debug = True

        # get current year and month as default
        if not month:
            month = datetime.date.today().month
        if not year:
            year = datetime.date.today().year

        # use calendar module to get month structure
        monthcal = calendar.monthcalendar(year, month)
        if debug: pprint(monthcal)

        monthdict = {'year': year, 'month_name': month}

        month_list = []
        #build nested list containing stats organized into weeks
        for week in monthcal:
            week_list = []
            for day in week:
                day_set = [day, 0]

                for dtime, count in self.loglist.items():
                    if dtime.month == month and dtime.day == day:
                        day_set[1] = count

                week_list.append(day_set)
            month_list.append(week_list)

        if debug: pprint(month_list)
        monthdict['calstats'] = month_list

        return monthdict

    def monthcal(self, year=None, month=None):
        '''
        Assemble and return an html calendar displaying the number of
        attempts per day in the month 'month' for the user represented
        by self.user_id.

        The calendar is returned as a web2py DIV helper.
        '''
        debug = True
        db = current.db
        # TODO: get settings for this user's class requirements
        memberships = db(
                        (db.auth_group.id == db.auth_membership.group_id)
                        & (db.auth_membership.user_id == self.user_id)
                        ).select()
        if debug: print memberships

        # get current year and month as default
        if not month:
            month = datetime.date.today().month
        else: month = int(month)
        if not year:
            year = datetime.date.today().year
        else: year = int(year)

        # get structured data to use in building table
        data = self.monthstats(year, month)
        if debug: print 'data=', data

        nms = calendar.month_name
        monthname = nms[data['month_name']]

        # Create wrapper div with title line and month name
        mcal = DIV(SPAN('Questions answered each day in',
                        _class='monthcal_intro_line'),
                    _class='paideia_monthcal')

        tbl = TABLE(_class='paideia_monthcal_table')
        tbl.append(THEAD(TR('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')))
        tb = TBODY()
        for week in data['calstats']:
            weeknum = data['calstats'].index(week)
            weekrow = TR()
            for day in week:
                # add table cell for this day
                weekrow.append(TD(_id='{}-{}'.format(weeknum, day[0])))
                # append empty span if no day number
                if day[0] == 0:
                    weekrow[-1].append(SPAN('', _class='cal_num'))
                else:
                    weekrow[-1].append(SPAN(str(day[0]),
                                    _class='cal_num'))
                # append a span with the day's attempt-count (if non-zero)
                if day[1] != 0:
                    weekrow[-1].append(SPAN(str(day[1]),
                                        _class='cal_count'))
            tb.append(weekrow)  # append week to table body
            if debug: print 'weekrow =', weekrow

        # build nav link for previous month
        prev_month = (month - 1) if month > 1 else 12
        if prev_month == 12:
            prev_year = year - 1
        else:
            prev_year = year
        prev_link = A('previous', _href=URL('reporting', 'calendar.load',
                        args=[self.user_id, prev_year, prev_month]),
                        _class='monthcal_prev_link',
                        cid='tab_calendar')
        mcal.append(prev_link)

        # build nav link for next month
        next_month = (month + 1) if month < 12 else 1
        if next_month == 1:
            next_year = year + 1
        else:
            next_year = year

        next_link = A('next', _href=URL('reporting', 'calendar.load',
                        args=[self.user_id, next_year, next_month]),
                        _class='monthcal_next_link',
                        cid='tab_calendar')
        mcal.append(next_link)
        mcal.append(H4(monthname))

        tbl.append(tb)
        mcal.append(tbl)

        #TODO: Add weekly summary counts to the end of each table
        #row (from self.dateset)

        return mcal
