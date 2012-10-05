# coding: utf8
#!/usr/bin/python
#found when running python2.7 web2py.py -S paideia -M -R test_runner.py

import os
import unittest
import cPickle as pickle
from mocker import Mocker

from gluon import *
from gluon import current
from gluon.contrib.test_helpers import form_postvars
from gluon.shell import exec_environment

from applications.paideia.modules.paideia_exploring import get_paths


def create_and_login_test_user(db, first_name, last_name, email, password):
    '''
    Create a new user for running tests and log in.

    The test user should not already exist, but if it does, delete it, so
    that there is no trace of the test user in the test database.
    '''

    db = current.db

    # Check if the test user already exists. If it does, delete it
    users = db(db.auth_user.email == email).select()
    if users:
        for user in users:
            db(db.auth_user.id == user.id).delete()

    crypt = CRYPT(key=auth.settings.hmac_key)
    crypt_pass = crypt(password)[0]

    user_id = db.auth_user.insert(
        first_name=first_name,
        last_name=last_name,
        email=email,
        password=crypt_pass
    )

    db.commit()

    session.auth = Storage(
        user=user_id,
        expiration=auth.settings.expiration,
        hmac_key=web2py_uuid(),
    )

    user = auth.login_bare(email, password)

    return user


class Paideia_exploringModule(unittest.TestCase):
    '''
    Unit test suite for paideia_exploring module
    '''

    def __init__(self, p):

        global auth, session, request

        unittest.TestCase.__init__(self, p)

        self.db = current.db

    def setUp(self):

        session = current.session

        # Create a test user and log in
        user = create_and_login_test_user(
            db=self.db,
            first_name='Test',
            last_name='User',
            email='test_user@test.com',
            password='testing'
        )

        execfile('applications/paideia/controllers/exploring.py', globals())

        self.walk = Walk()
        self.walk.save_session_data()

        # Make sure we're starting with a user with no previous game history
        self._verify_walk_start()

    def tearDown(self):

        session.walk = None

        # Remove user
        path_logs = self.db(self.db.path_log.name == auth.user_id).select()

        self.db(self.db.tag_records.name == auth.user_id).delete()
        self.db(self.db.tag_progress.name == auth.user_id).delete()
        self.db(self.db.path_log.name == auth.user_id).delete()
        self.db(self.db.attempt_log.name == auth.user_id).delete()

        self.db.commit()

    ##### Utility methods

    def _verify_walk_start(self):
        '''
        Verify that the logged in user is the test user and that the user has
        no game history.
        '''

        email = auth.user.email
        expected_email = 'test_user@test.com'
        self.assertEqual(
            email,
            expected_email,
            'Invalid test user - got %s (expected %s)' % (email,
                                                          expected_email)
        )

        for attr in ('active_location', 'path', 'step'):
            value = getattr(self.walk, attr)
            self.assertIsNone(
                value,
                "walk.%s should be None (got %s)" % (attr, value)
            )

        # Active paths
        self.assertEqual(
            self.walk.active_paths,
            {},
            "walk.active_paths should be empty (got %s)" %
                                                    self.walk.active_paths
        )

        # Tag sets
        self.assertEqual(
            self.walk.tag_set,
            {},
            "walk.tag_set should be empty (got %s)" % self.walk.tag_set
        )

        # Completed paths
        self.assertEqual(
            self.walk.completed_paths,
            set(),
            "walk.completed_paths should be empty (got %s)" %
                                                    self.walk.completed_paths
        )

        self.assertGreater(
            len(self.walk.map.locations),
            0,
            'Map has no locations'
        )

        # Tag records
        record_count = len(self.db(self.db.tag_records.name ==
                                                        auth.user.id).select())
        self.assertEqual(
            record_count,
            0,
            'Test user has %s tag records (should have none)' % record_count
        )

        # Tag progress
        tag_progress = self.db(self.db.tag_progress.name ==
                                                 auth.user.id).select().first()
        self.assertIsNone(
            tag_progress,
            'Test user has tag progress (should have none)'
        )

        # Path logs
        path_logs = self.db(self.db.path_log.name == auth.user.id).select()
        self.assertEqual(
            len(path_logs),
            0,
            'Test user has path logs (should have none)'
        )

        # Attempt logs
        attempt_logs = self.db(self.db.attempt_log.name ==
                                                        auth.user.id).select()
        self.assertEqual(
            len(attempt_logs),
            0,
            'Test user has attempt logs (should have none)'
        )

    def get_location(self, alias):
        '''
        Return a location object given its alias.
        '''

        location = self.db(self.db.locations.alias == alias).select().first()
        image = IMG(
            _src=URL('default', 'download',
                     args=self.db.locations[location.id].background)
        )

        return Location(location, image)

    ##### Test cases

    ### Walk

    def test_categorize_tags_new_user(self):
        '''
        Test Walk.categorize_tags for a new user.
        '''

        self.walk.categorize_tags()

        for category, value in self.walk.tag_set.items():
            if category == 1:
                self.assertEqual(
                    len(value),
                    1,
                    'There should be only one tag in category %s (got %s)' %
                                                    (category, len(value))
                )

                tag = db.tags(value[0])

                self.assertEqual(
                    tag.id,
                    61,
                    'The only tag in category 1 should have id = 61'
                                                    '(got id %s)' % tag.id
                )

                self.assertEqual(
                    tag.position,
                    1,
                    'The tags in category 1 should have position 1'
                                                    '(got %s)' % tag.position
                )

            else:
                self.assertEqual(
                    len(value),
                    0,
                    'There should be no tags in category %s (got %s)' %
                                                    (category, len(value))
                )

    def test_introduce_new_user(self):
        '''
        Test Walk.introduce for a new user.
        '''

        tags = self.walk._introduce()

        self.assertEqual(
            len(tags),
            1,
            'Only one tag should be introduced (got %s)' % len(tags)
        )

        self.assertEqual(
            tags[0],
            61,
            'The only introduced tag should have id = 61 (got id %s)' %
                                                                    tags[0]
        )

    def test_unfinished_new_user(self):
        '''
        Test Walk.unfinished for a new user.
        '''

        self.walk.unfinished()

        self.assertEqual(
            self.walk.active_paths,
            {},
            'A new user should have no active paths (got %s)' %
                                                    self.walk.active_paths
        )

#    def test_pick_path(self):
#        '''
#        Test Walk.pick_path for a new user.
#        '''
#
#        self.walk.categorize_tags()
#        self.walk.unfinished()
#
#        location = Location('domusA')
#        self.walk.pick_path(location)
#        self.walk.active_location = location
#
#        expected_path_ids = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 21)
#        expected_paths = self.db(self.db.paths.id.belongs(expected_path_ids)
                                  # ).select()
#
#        # Since path is picked at random, just check that the selected path is
#        # one of the possibilities
#        self.assertIn(
#            self.walk.path.id,
#            expected_path_ids,
#            'Picked incorrect path: %s is not in %s' % (self.walk.path.id,
                                                         # expected_paths)
#        )
#
#        expected_path = expected_paths[
                                # expected_path_ids.index(self.walk.path.id)]
#        self.assertEqual(
#            self.walk.step.step.id,
#            expected_path.steps[0],
#            'Picked incorrect step: expected %s got %s' %
                            # (expected_path.steps[0], self.walk.step.step.id)
#        )
#
#    def test_find_paths(self):
#        '''
#        Test walk.find_paths for a new user.
#        '''
#
#        expected = ((1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 21), 1)
#
#        self.walk.categorize_tags()
#        self.walk.unfinished()
#
#        location = Location('domusA')
#
#        for category in (1, 2, 3, 4):
#            category_paths, category = self.walk.find_paths(category,
                                            # location, self.walk.get_paths())
#
#            self.assertEqual(
#                tuple(p.id for p in category_paths),
#                expected[0],
#                'Category %s: Found incorrect paths:\n\texpected %s\n\tgot
                               # %s' % (category, expected[0], category_paths)
#            )
#
#            self.assertEqual(
#                category,
#                expected[1],
#                'Category %s: Found incorrect category:\n\texpected %s\n\tgot
                                    # %s' % (category, expected[1], category)
#            )

    ### Step

#     def test_get_npc_no_active_location(self):
#         '''
#         Test Step.get_npc() where there is no active location.
#         '''

#         self.walk.active_location = None
#         self.walk.save_session_data()

#         step = Step(1)

#         npc = step.get_npc()

#         self.assertIsNone(
#             npc,
#             'NPC should be none - got %s' % npc
#         )

    def test_get_npc_active_location(self):
        '''
        Test Step.get_npc() where there is an active location.
        '''

        self.walk.active_location = Location('domus_A')
        self.walk.save_session_data()

        step = Step(1)

        npc = step.get_npc()

        expected_ids = (2, 3, 8, 14, 17, 31, 40)
        expected = self.db(self.db.npcs.id.belongs(expected_ids)).select()

        self.assertIn(
            npc.npc.id,
            expected_ids,
            'Picked incorrect NPC: %s is not in %s' % (
                npc.npc, [n.id for n in expected])
        )

        # Session should be updated
        self.assertEqual(
            step.step.id,
            session.walk['step'],
            'Session incorrectly updated: expected %s got %s' % (
                step.step.id, session.walk['step'])
        )

    def test_prompt(self):
        '''
        Test Step.prompt.

        TODO: Test audio prompt when it's implemented
        '''

        step = Step(1)

        prompt = step.get_prompt()

        expected = '<span>How could you write the word &quot;meet&quot;' \
                                                'using Greek letters?</span>'

        self.assertEqual(
            str(prompt),
            expected,
            'Incorrect prompt:\n\texpected: %s\n\tactual:   %s' % (expected,
                                                                     prompt)
        )

    def ___test_responder(self):
        '''
        Test Step.responder().
        '''

        pass

    ### NPC

    def test_npc(self):
        '''
        Test npc creation.
        '''

        npc_id = 2

        npc = self.db.npcs(npc_id)
        for k, v in sorted(globals().items()):
            print 'DEBUG: %s --> %s' % (k, v)
            print
        npc_obj = Npc(npc_id)

        expected = '<img src="/paideia/static/images/'\
                'images.image.85a960241dc29f1b.776f6d616e312e706e67.png" />'
        self.assertEqual(
            str(npc_obj.image),
            expected,
            'Incorrect image:\n\texpected: %s\n\tactual:   %s' %
                                                    (expected, npc_obj.image)
        )
