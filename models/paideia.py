# coding: utf8

from plugin_ajaxselect import AjaxSelect
from itertools import chain
import datetime
import os
import re

if 0:
    from gluon import URL, current, Field, IS_IN_DB, SQLFORM
    response = current.response
    request = current.request
    auth = current.auth
    db = current.db

#js file necessary for AjaxSelect widget
response.files.insert(5, URL('static',
                      'plugin_ajaxselect/plugin_ajaxselect.js'))
response.files.append(URL('static', 'plugin_ajaxselect/plugin_ajaxselect.css'))

dtnow = datetime.datetime.utcnow


#TODO: Fix this regex validator
class IS_VALID_REGEX(object):
    """
    custom validator to check regex in step definitions against the given
    readable responses.
    """
    def __init__(self):
        self.error_message = 'Given answers do not satisfy regular expression.'

    def __call__(self, value):
        request = current.request
        answers = request.vars.readable_response
        alist = answers.split('|')
        regex = value.encode('string-escape')
        for a in alist:
            if re.match(a.strip(), regex, re.I):
                print a.strip()
                print 'it matched!'
            else:
                print 'answer ', a, ' did not match the regex provided.'
                print regex
                return (value, self.error_message)
        return (value, None)

#TODO:Allow for different class profiles with different settings
db.define_table('app_settings',
    Field('class_id', 'string'),
    Field('paths_per_day', 'integer', default=20),
    Field('days_per_week', 'integer', default=5)
    )

db.define_table('images',
    Field('image', 'upload',
          uploadfolder=os.path.join(request.folder, "static/images")),
    Field('title', 'string'),
    Field('description', 'string'),
    format='%(title)s')

db.define_table('audio',
    Field('clip', 'upload',
          uploadfolder=os.path.join(request.folder, "static/audio")),
    Field('title', 'string'),
    Field('description', 'string'),
    format='%(title)s')

db.define_table('journals',
    Field('user', db.auth_user, default=auth.user_id),
    Field('pages', 'list:reference pages'),
    format='%(user)s')

db.define_table('pages',
    Field('page', 'text'),
    format='%(page)s')

db.define_table('categories',
    Field('category'),
    Field('description'),
    format='%(category)s')

db.define_table('tags',
    Field('tag', 'string'),
    Field('position', 'integer'),
    format='%(tag)s')

db.define_table('locations',
    Field('location'),
    Field('alias'),
    Field('bg_image', db.images),
    format='%(location)s')

db.define_table('npcs',
    Field('name', 'string'),
    Field('location', 'list:reference locations'),
    Field('npc_image', db.images),
    Field('notes', 'text'),
    format='%(name)s')
db.npcs.location.requires = IS_IN_DB(db, 'locations.id',
                                     db.locations._format, multiple=True)
db.npcs.location.widget = lambda field, value: \
                        AjaxSelect().widget(field, value, 'locations',
                                    multi='basic',
                                    lister='editlinks')

db.define_table('inv_items',
    Field('item_name', 'string'),
    Field('item_image', db.images),
    format='%(item_name)s')

db.define_table('inventory',
    Field('owner', db.auth_user, default=auth.user_id),
    Field('items_held', 'list:reference inv_items'),
    format='%(owner)s inventory')

#this table is deprecated
#TODO: refactor out questions entirely
db.define_table('questions',
    Field('question', 'text'),
    Field('answer'),
    Field('value', 'double', default=1.0),
    Field('readable_answer'),
    Field('answer2', default='null'),
    Field('value2', 'double', default=0.5),
    Field('answer3', default='null'),
    Field('value3', 'double', default=0.3),
    Field('frequency', 'double'),
    Field('tags', 'list:reference tags'),
    Field('tags_secondary', 'list:reference tags'),
    Field('status', 'integer'),
    Field('npcs', 'list:reference npcs'),
    Field('next', 'list:reference questions'),
    Field('audio', 'upload', uploadfolder=os.path.join(request.folder,
        "static/audio")),
    format='%(question)s')
db.questions.npcs.requires = IS_IN_DB(db, 'npcs.id',
                                db.npcs._format, multiple=True)
db.questions.npcs.widget = lambda field, value: AjaxSelect().widget(field,
                                                    value, 'npcs',
                                                    multi='basic')
db.questions.tags.requires = IS_IN_DB(db, 'tags.id',
                                db.tags._format, multiple=True)
db.questions.tags.widget = lambda field, value: AjaxSelect().widget(field,
                                                    value, 'tags',
                                                    refresher=True,
                                                    multi='basic')
db.questions.tags_secondary.requires = IS_IN_DB(db, 'tags.id',
                                        db.tags._format, multiple=True)
db.questions.tags_secondary.widget = lambda field, value: AjaxSelect().widget(
                                                    field, value, 'tags',
                                                    multi='basic')

db.define_table('step_types',
    Field('type'),
    Field('widget'),
    Field('step_class'),
    format='%(type)s')

db.define_table('step_hints',
    Field('label'),
    Field('text', 'text'),
    format='%(label)s')

db.define_table('step_instructions',
    Field('label'),
    Field('text', 'text'),
    format='%(label)s')

#TODO: transfer all questions data over to steps table
db.define_table('steps',
    Field('prompt', 'text'),
    Field('prompt_audio', db.audio, default=0),
    Field('widget_type', db.step_types, default=1),
    Field('widget_image', db.images, default=0),
    Field('options', 'list:string'),
    Field('response1'),
    Field('readable_response'),
    Field('outcome1', default=None),
    Field('response2', default=None),
    Field('outcome2', default=None),
    Field('response3', default=None),
    Field('outcome3', default=None),
    Field('hints', 'list:reference step_hints'),
    Field('instructions', 'list:reference step_instructions'),
    Field('tags', 'list:reference tags'),
    Field('tags_secondary', 'list:reference tags'),
    Field('npcs', 'list:reference npcs'),
    Field('locations', 'list:reference locations'),
    Field('status', 'integer'),
    format='%(prompt)s')
db.steps.options.widget = SQLFORM.widgets.list.widget
#db.steps.response1.requires = IS_VALID_REGEX()
db.steps.npcs.requires = IS_IN_DB(db, 'npcs.id',
                                      db.npcs._format, multiple=True)
db.steps.npcs.widget = lambda field, value: AjaxSelect().widget(
                                                field, value, 'npcs',
                                                multi='basic',
                                                lister='editlinks')
db.steps.tags.requires = IS_IN_DB(db, 'tags.id',
                                      db.tags._format, multiple=True)
db.steps.tags.widget = lambda field, value: AjaxSelect().widget(
                                                field, value, 'tags',
                                                refresher=True,
                                                multi='basic',
                                                lister='editlinks')
db.steps.tags_secondary.requires = IS_IN_DB(db, 'tags.id',
                                                db.tags._format,
                                                multiple=True)
db.steps.tags_secondary.widget = lambda field, value: AjaxSelect().widget(
                                                field, value, 'tags',
                                                multi='basic',
                                                lister='editlinks')
db.steps.locations.requires = IS_IN_DB(db, 'locations.id',
                                                db.locations._format,
                                                multiple=True)
db.steps.locations.widget = lambda field, value: AjaxSelect().widget(
                                                field, value, 'locations',
                                                multi='basic',
                                                lister='editlinks')
db.steps.hints.requires = IS_IN_DB(db, 'step_hints.id',
                                                db.step_hints._format,
                                                multiple=True)
db.steps.hints.widget = lambda field, value: AjaxSelect().widget(
                                                    field, value, 'step_hints',
                                                    multi='basic',
                                                    lister='editlinks')
db.steps.instructions.requires = IS_IN_DB(db, 'step_instructions.id',
                                                db.step_instructions._format,
                                                multiple=True)
db.steps.instructions.widget = lambda field, value: AjaxSelect().widget(
                                                    field, value,
                                                    'step_instructions',
                                                    multi='basic',
                                                    lister='editlinks')


#this table is deprecated
#TODO: do we need an equivalent for steps? The same data could be retrieved as
# needed from the attempts_log table.
db.define_table('question_records',
    Field('name', db.auth_user, default=auth.user_id),
    Field('question', db.questions),
    Field('times_right', 'double'),
    Field('times_wrong', 'double'),
    Field('tlast_wrong', 'datetime', default=dtnow),
    Field('tlast_right', 'datetime', default=dtnow),
    Field('category', db.categories)
    )

db.define_table('tag_progress',
    Field('name', db.auth_user, default=auth.user_id),
    Field('latest_new', 'integer'),  # not tag id but order ranking
    Field('cat1', 'list:reference tags'),
    Field('cat2', 'list:reference tags'),
    Field('cat3', 'list:reference tags'),
    Field('cat4', 'list:reference tags'),
    format='%(name)s, %(latest_new)s')

db.define_table('paths',
    Field('label'),
    Field('steps', 'list:reference steps'),
    format='%(label)s')
db.paths.steps.requires = IS_IN_DB(db, 'steps.id',
                                   db.steps._format, multiple=True)
db.paths.steps.widget = lambda field, value: AjaxSelect().widget(
                                        field, value, 'steps',
                                        refresher=True,
                                        multi='basic',
                                        lister='editlinks',
                                        sortable='true')


class PathsVirtualFields(object):
    # def locations(self):
    #     # TODO: This only gets locations from one of the steps in the path
    #     steprows = db(db.steps.id.belongs(self.paths.steps)).select().first()
    #     return steprows.locations

    def tags(self):
        steprows = db(db.steps.id.belongs(self.paths.steps)).select()
        nlists = [s.tags for s in steprows]
        return list(chain.from_iterable(nlists))
db.paths.virtualfields.append(PathsVirtualFields())

db.define_table('path_log',
    Field('name', db.auth_user, default=auth.user_id),
    Field('path', db.paths),
    Field('dt_started', 'datetime', default=dtnow),
    Field('last_step', db.steps),
    Field('dt_completed', 'datetime', default=None)
    )
db.path_log.name.requires = IS_IN_DB(db, 'auth_user.id', db.auth_user._format)
db.path_log.path.requires = IS_IN_DB(db, 'paths.id', db.paths._format)
db.path_log.last_step.requires = IS_IN_DB(db, 'steps.id', db.steps._format)

db.define_table('attempt_log',
    Field('name', db.auth_user, default=auth.user_id),
    Field('step', db.steps),
    Field('path', db.paths),
    Field('score', 'double'),
    Field('dt_attempted', 'datetime', default=dtnow)
    )
db.attempt_log.name.requires = IS_IN_DB(db, 'auth_user.id',
                                db.auth_user._format)
db.attempt_log.step.requires = IS_IN_DB(db, 'steps.id', db.steps._format)
db.attempt_log.path.requires = IS_IN_DB(db, 'paths.id', db.paths._format)

db.define_table('tag_records',
    Field('name', db.auth_user, default=auth.user_id),
    Field('tag', db.tags),
    Field('times_right', 'double'),
    Field('times_wrong', 'double'),
    Field('tlast_wrong', 'datetime', default=dtnow),
    Field('tlast_right', 'datetime', default=dtnow),
    Field('path', db.paths),
    Field('step', db.steps)
    )
db.tag_records.name.requires = IS_IN_DB(db, 'auth_user.id',
                                    db.auth_user._format)
db.tag_records.tag.requires = IS_IN_DB(db, 'tags.id', db.tags._format)
db.tag_records.step.requires = IS_IN_DB(db, 'steps.id', db.steps._format)
db.tag_records.path.requires = IS_IN_DB(db, 'paths.id', db.paths._format)

db.define_table('bug_status',
    Field('status_label'),
    format='%(status_label)s')

db.define_table('bugs',
    Field('step', db.steps),
    Field('path', db.paths),
    Field('location', db.locations),
    Field('user_response'),
    Field('user_name', db.auth_user, default=auth.user_id),
    Field('date_submitted', 'datetime', default=dtnow),
    Field('bug_status', db.bug_status, default=5),
    Field('admin_comment', 'text'),
    Field('prev_lastright', 'datetime'),
    Field('prev_lastwrong', 'datetime'),
    format='%(step)s')

db.define_table('news',
    Field('story', 'text'),
    Field('title', 'string'),
    Field('name', db.auth_user, default=auth.user_id),
    Field('date_submitted', 'datetime', default=dtnow),
    Field('last_edit', 'datetime', default=dtnow),
    format='%(title)s')
