# -*- coding: utf-8 -*-

if 0:
    from gluon import current, URL, SPAN, XML, A
    response, request, T = current.response, current.request, current.t
    auth = current.auth
from datetime import datetime

"""
This file includes the menu content along with other meta content and global
layout settings
"""

# Meta =====================================================================

response.title = request.application
response.mobiletitle = request.application
response.subtitle = T('Learning New Testament Greek in Context')

#http://dev.w3.org/html5/markup/meta.name.html
response.meta.author = 'Ian W. Scott'
response.meta.description = 'An online, interactive course in ' \
                            'New Testament Greek'
response.meta.keywords = 'Greek, koine, New Testament, language, ' \
                         'education, learning'
response.meta.generator = 'Web2py Enterprise Framework'
response.meta.copyright = XML('All content copyright &copy; 2011-{}, '
                              'Ian W. Scott. Source code available on '.format(datetime.now().year),
                              A('GitHub', _href="https://github.com/monotasker/paideia"))

# Layout ===================================================================

response.left_sidebar_enabled = 0
response.right_sidebar_enabled = 0
response.fluid_layout = True

# Menu =====================================================================

response.menu = [(SPAN(T(' Home'), _class='icon-home'), False,
                  URL('default', 'index'), []),
                 (SPAN(T(' Map'), _class='icon-map-marker'), False,
                  URL('exploring', 'index'), []),
                 (SPAN(T(' Slides'), _class='icon-picture'), False,
                  URL('listing', 'slides'), [])
                 ]
m = response.menu

if auth.has_membership('administrators', auth.user_id) or auth.is_impersonating():
    m += [(SPAN(T(' Admin'), _class='icon-cog'), False, None,
           [(SPAN(T(' Create'), _class='icon-leaf'), False, None,
             [(SPAN(T(' Slide decks'), _class='icon-tasks'), False, URL('editing',
                                            'listing.html',
                                            args=['plugin_slider_decks'])),
              (SPAN(T(' Slides'), _class='icon-film'), False, URL('editing',
                                       'listing.html',
                                       args=['plugin_slider_slides'],
                                       vars={'orderby': 'slide_name'})),
              (SPAN(T(' Paths'), _class='icon-road'), False, URL('editing',
                                      'listing.html',
                                      args=['paths'])),
              (SPAN(T(' Steps'), _class='icon-plus-sign-alt'), False, URL('editing',
                                      'listing.html',
                                      args=['steps'])),
              (SPAN(T(' Tags'), _class='icon-tag'), False, URL('editing',
                                     'listing.html',
                                     args=['tags'])),
              (SPAN(T(' Badges'), _class='icon-certificate'), False, URL('editing',
                                       'listing.html',
                                       args=['badges'])),
              (SPAN(T(' Instructions'), _class='icon-check'), False, URL('editing',
                                             'listing.html',
                                             args=['step_instructions'])),
              (SPAN(T(' Hints'), _class='icon-question'), False, URL('editing',
                                      'listing.html',
                                      args=['step_hints'])),
              (SPAN(T(' NPCs'), _class='icon-group'), False, URL('editing',
                                     'listing.html',
                                     args=['npcs'])),
              (SPAN(T(' locations'), _class='icon-screenshot'), False, URL('editing',
                                          'listing.html',
                                          args=['locations'])),
              (SPAN(T(' classes'), _class='icon-group'), False, URL('editing',
                                       'listing.html',
                                       args=['classes'])),
              (SPAN(T(' images'), _class='icon-picture'), False, URL('editing',
                                       'listing.html',
                                       args=['images'])),
              ]),

            (SPAN(T(' Reports'), _class='icon-bar-chart'), False, None,
             [(SPAN(T(' Users'), _class='icon-group'), False,
                    URL('listing', 'user')),
              (SPAN(T(' Individual user'), _class='icon-group'), False,
                    URL('reporting', 'user', args=[0])),
              (SPAN(T(' New Bug reports'), _class='icon-warning-sign'), False,
                    URL('editing',
                        'listing.html', args=['bugs'],
                        vars={'restrictor': {'bug_status': 5}})),
              (SPAN(T(' Confirmed Bug reports'), _class='icon-stethoscope'),
                    False,
                    URL('editing',
                        'listing.html', args=['bugs'],
                        vars={'restrictor': {'bug_status': 1}})),
              (SPAN(T(' All Bug reports'), _class='icon-frown'), False,
                    URL('editing', 'listing.html', args=['bugs'])),
              (SPAN(T(' Paths by tag'), _class='icon-tags'), False,
                    URL('reporting', 'paths_by_tag')),
              (SPAN(T(' Attempt log'), _class='icon-list-alt'), False,
                    URL('reporting', 'attempts')),
              ]),

            (SPAN(T(' Utils'), _class='icon-cog'), False, None,
             [(SPAN(T(' Make paths'), _class='icon-cog'), False,
                    URL('util', 'make_path')),
              (SPAN(T(' Bulk update'), _class='icon-cog'), False,
                    URL('util', 'bulk_update')),
              (SPAN(T(' Impersonate'), _class='icon-cog'), False,
                    URL('default', 'user', args=['impersonate'])),
              ]),

            (SPAN(T(' Web IDE'), _class='icon-code'), False,
                  URL('admin', 'default', 'index')),
            (SPAN(T(' Web IDE'), _class='icon-frown'), False,
                  URL('admin', 'default', 'errors/paideia')),
            (SPAN(T(' Database'), _class='icon-sitemap'), False,
                  URL('appadmin', 'index')),
            ])
          ]
