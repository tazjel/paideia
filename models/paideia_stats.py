import calendar, datetime

if 0:
    from gluon import current, SQLFORM, redirect, A, URL
    from gluon.tools import Auth, Crud
    from gluon.dal import DAL
    db = DAL()
    auth = Auth()
    cache=current.cache
    T = current.t
    response = current.response
    service = current.service
    request = current.request
    session = current.session
    crud = Crud()

class paideia_stats:
    # calculates stats for paideia student performance
    Name = "paideia_stats"


    def __init__(self, user_id):
        """
        Collects and returns student performance statistics based on scores earned on attempted questions.

        This function returns the following attributes:
        score_avg -- Straightforward average of scores, presented as a percentage.
        """
        self.user_id = user_id
        try:
            attempts = db(db.attempt_log.name == self.user_id).select()
            s=db.attempt_log.score.sum()
            row = db(db.attempt_log.name == self.user_id).select(s).first()
            answer = row[s]
            self.score_avg = round(answer/len(attempts)*100)
        except:
            self.score_avg = "Can't calculate average"

class paideia_timestats:
    def __init__(self, user_id):
        """
        Collects and returns student performance statistics based on question categories and time relationships between the present, the last successful attempt, and the last unsuccessful attempt.

        This function returns the vollowing attributes:
        total_len -- The total number of questions that have been attempted by the current student
        total_cat1 -- Total number of questions attempted that are currently in category 1
        total_cat2 -- Total number of questions attempted that are currently in category 2
        total_cat3 --  Total number of questions attempted that are currently in category 3
        total_cat4 --  Total number of questions attempted that are currently in category 4
        percent_cat1 -- Percentage of questions attempted that are currently in category 1
        percent_cat2 -- Percentage of questions attempted that are currently in category 2
        percent_cat3 -- Percentage of questions attempted that are currently in category 3
        percent_cat4 -- Percentage of questions attempted that are currently in category 4
        """

        # get statistics for different classes of questions
        self.user_id = user_id
        the_records = db(db.question_records.name == self.user_id).select()
        self.total_len = float(len(the_records))
        try:
            cat1 = db((db.question_records.name == self.user_id) & (db.question_records.category == 1)).select()
            self.total_cat1 = len(cat1)
            self.percent_cat1 = round((int(self.total_cat1)/self.total_len)*100, 1)
        except:
            self.total_cat1 = "Can't calculate number"
            self.percent_cat1 = ""
        try:
            cat2 = db((db.question_records.name == self.user_id) & (db.question_records.category == 2)).select()
            self.total_cat2 = len(cat2)
            self.percent_cat2 = round((int(self.total_cat2)/self.total_len)*100, 1)
        except:
            self.total_cat2 = "Can't calculate number"
            self.percent_cat2 = ""
        try:
            cat3 = db((db.question_records.name == self.user_id) & (db.question_records.category == 3)).select()
            self.total_cat3 = len(cat3)
            self.percent_cat3 = round((int(self.total_cat3)/self.total_len)*100, 1)
        except:
            self.total_cat3 = "Can't calculate number"
            self.percent_cat3 = ""
        try:
            cat4 = db((db.question_records.name == self.user_id) & (db.question_records.category == 4)).select()
            self.total_cat4 = len(cat4)
            self.percent_cat4 = round((int(self.total_cat4)/self.total_len)*100, 1)
        except:
            self.total_cat4 = "Can't calculate number"
            self.percent_cat4 = ""

class paideia_weeklycount:
    def __init__(self, user_id):
        """
        Collect and return the number of questions attempted per day and per week

        returns the following variables:
        dateset -- a list of tuples, each of which contains three values: month, first day of week, number attempted
        """
        self.user_id = user_id
        logs = db(db.attempt_log.name == self.user_id).select(db.attempt_log.dt_attempted)

        loglist = {}

        #offset from utc time used to generate and store time stamps
        utcvar = int(-5)

        for log in logs:
            newdatetime = log.dt_attempted - datetime.timedelta(hours=utcvar)
            newdate = datetime.date(newdatetime.year, newdatetime.month, newdatetime.day)
            if newdate in loglist:
                loglist[newdate] += 1
            else:
                loglist[newdate] = 1

        this_year = datetime.date.today().year
        self.dateset = {}
        self.htmlcal = ''
        for month in range(1,12):
            monthcal = calendar.monthcalendar(this_year, month)
            
            #build dict containing stats organized into weeks
            if month not in self.dateset:
                self.dateset[month] = {}
                m = self.dateset[month]
            for week in monthcal:
                weekday = week[0]
                if weekday not in self.dateset[month]:
                    m[weekday] = {}
                    w = m[weekday]
                for day in week:
                    w[day] = ''
                     
                for dt, count in loglist.items():
                    if dt.month == month and dt.day in week:
                        w[dt.day] = count
            
            #now build html calendar as string with stats embedded
            nms = calendar.month_name
            monthname = nms[month]
            self.htmlcal += '<h4>' + monthname + '</h4><table class="weeklycount">'
            for week in monthcal:
                w = week[0]
                self.htmlcal += '<tr>'
                if (month in self.dateset) and (w in self.dateset[month]):
                    the_m = self.dateset[month]
                    the_w = the_m[w]
                    for day in week:
                        self.htmlcal+= '<td>'
                        self.htmlcal+= '<span class="cal_num">' + str(day) + '</span>'
                        if day in the_w:
                            self.htmlcal+='<span class="cal_count">' + str(the_w[day]) + '</span>'
                        self.htmlcal+= '</td>'
                else:
                    for day in week:
                        self.htmlcal+= '<td>'
                        self.htmlcal+= '<span class="cal_num">' + str(day) + '</span>'
                        self.htmlcal+= '</td>'
                self.htmlcal += '</tr>'
            self.htmlcal += '</table>'
            #TODO: Add weekly summary counts to the end of each table row (from self.dateset)
            