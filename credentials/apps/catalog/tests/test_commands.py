import ddt
import responses
import slumber
from django.core.management import call_command
from django.test import TestCase
from faker import Faker

from credentials.apps.catalog.models import Course, CourseRun, Organization, Program
from credentials.apps.catalog.tests.factories import OrganizationFactory, ProgramFactory
from credentials.apps.core.tests.factories import SiteConfigurationFactory
from credentials.apps.core.tests.mixins import SiteMixin


@ddt.ddt
class CopyCatalogCommandTests(SiteMixin, TestCase):
    COMMAND_NAME = 'copy_catalog'
    faker = Faker()

    PROGRAMS = [
        {
            'uuid': '33f0dded-fee9-4dec-a333-b9d8c2c82bd5',
            'title': 'A Fake Program',
            'type': 'MicroMasters',
            'authoring_organizations': [
                {
                    'uuid': '33f0dded-fee9-4dec-a333-b9d8c2c82bd2',
                    'key': 'FakeX',
                    'name': 'Fake University',
                },
            ],
            'courses': [
                {
                    'uuid': '33f0dded-fee9-4dec-a333-b9d8c2c82bd4',
                    'key': 'FakeX+Course1',
                    'title': 'Course 1',
                    'owners': [
                        {
                            'uuid': '33f0dded-fee9-4dec-a333-b9d8c2c82bd2',
                            'key': 'FakeX',
                            'name': 'Fake University',
                        },
                    ],
                    'course_runs': [
                        {
                            'uuid': '33f0dded-fee9-4dec-a333-b9d8c2c82bd3',
                            'key': 'course-v1:FakeX+Course1+Run1',
                            'title': 'Course 1',
                            'start': '2018-01-01T00:00:00Z',
                            'end': '2018-06-01T00:00:00Z',
                        },
                    ],
                },
            ],
        },
        {
            'uuid': '33f0dded-fee9-4dec-a333-c9d8c2c82bd5',
            'title': 'A Second Fake Program',
            'type': 'Professional Certificate',
            'authoring_organizations': [
                {
                    'uuid': '33f0dded-fee9-4dec-a333-c9d8c2c82bd2',
                    'key': 'BakeX',
                    'name': 'Bake University',
                },
            ],
            'courses': [
                {
                    'uuid': '33f0dded-fee9-4dec-a333-c9d8c2c82bd4',
                    'key': 'CakeX+Course1',
                    'title': 'Course 1',
                    'owners': [
                        {
                            'uuid': '33f0dded-fee9-4dec-a333-c9d8c2c82bd1',
                            'key': 'CakeX',
                            'name': 'Cake University',
                        },
                    ],
                    'course_runs': [
                        {
                            'uuid': '33f0dded-fee9-4dec-a333-c9d8c2c82bd3',
                            'key': 'course-v1:CakeX+Course1+Run1',
                            'title': 'Course 1',
                            'start': '2018-01-01T00:00:00Z',
                            'end': '2018-06-01T00:00:00Z',
                        },
                        {
                            'uuid': '33f0dded-fee9-4dec-a333-c9d8c2c82bd4',
                            'key': 'course-v1:CakeX+Course1+Run2',
                            'title': 'Course 2',
                            'start': '2018-02-01T00:00:00Z',
                            'end': '2018-07-01T00:00:00Z',
                        },
                    ],
                },
            ],
        },
    ]

    def setUp(self):
        # pylint: disable=no-member
        super(CopyCatalogCommandTests, self).setUp()
        self.site_configuration = SiteConfigurationFactory.build(segment_key=self.faker.word())

    def call_command(self, **kwargs):
        """ Helper method for interacting with the copy_catalog management command """
        call_command(self.COMMAND_NAME, **kwargs)

    @staticmethod
    def wrap_programs(programs, final=True):
        return {
            'count': len(programs),
            'next': None if final else 'more',  # we don't actually parse this value
            'prev': None,
            'results': programs,
        }

    def mock_programs_response(self, body, page=1, page_size=None, **kwargs):
        endpoint = 'programs/?exclude_utm=1&page=' + str(page)
        if page_size:
            endpoint = endpoint + '&page_size=' + str(page_size)
        self.mock_catalog_api_response(endpoint, body, **kwargs)

    def assertProgramsSaved(self):
        self.assertEqual(Program.objects.all().count(), len(self.PROGRAMS))
        for program in self.PROGRAMS:
            Program.objects.get(uuid=program['uuid'])

        self.assertEqual(Organization.objects.all().count(), 3)
        Organization.objects.get(key='FakeX')
        Organization.objects.get(key='BakeX')
        Organization.objects.get(key='CakeX')

        self.assertEqual(Course.objects.all().count(), 2)
        Course.objects.get(key='FakeX+Course1')
        Course.objects.get(key='CakeX+Course1')

        self.assertEqual(CourseRun.objects.all().count(), 3)
        CourseRun.objects.get(key='course-v1:FakeX+Course1+Run1')
        CourseRun.objects.get(key='course-v1:CakeX+Course1+Run1')
        CourseRun.objects.get(key='course-v1:CakeX+Course1+Run2')

    def assertFirstSaved(self):
        self.assertEqual(Program.objects.all().count(), 1)
        Program.objects.get(uuid=self.PROGRAMS[0]['uuid'])

        self.assertEqual(Organization.objects.all().count(), 1)
        Organization.objects.get(key='FakeX')

        self.assertEqual(Course.objects.all().count(), 1)
        Course.objects.get(key='FakeX+Course1')

        self.assertEqual(CourseRun.objects.all().count(), 1)
        CourseRun.objects.get(key='course-v1:FakeX+Course1+Run1')

    @responses.activate
    def test_happy_path(self):
        """ Verify the command creates programs as expected, when nothing is amiss. """
        self.mock_access_token_response()
        self.mock_programs_response(self.wrap_programs(self.PROGRAMS))
        self.call_command()

        self.assertProgramsSaved()

    @responses.activate
    def test_page_size(self):
        """ Verify the command handles page_size. """
        self.mock_access_token_response()
        self.mock_programs_response(self.wrap_programs([self.PROGRAMS[0]], final=False), 1, 1)
        self.mock_programs_response(self.wrap_programs([self.PROGRAMS[1]]), 2, 1)
        self.call_command(page_size=1)

        self.assertProgramsSaved()

    @responses.activate
    def test_parse_error(self):
        """ Verify the command handles parsing errors. """
        self.mock_access_token_response()

        # Use two responses to ensure we're atomic about any errors
        self.mock_programs_response(self.wrap_programs([self.PROGRAMS[0]], final=False), 1, 1)
        self.mock_programs_response({}, 2, 1)

        with self.assertRaises(KeyError):
            self.call_command(page_size=1)

        self.assertFirstSaved()

    @responses.activate
    def test_server_error(self):
        """ Verify the command handles a server error. """
        self.mock_access_token_response()

        # Use two responses to ensure we're atomic about any errors
        self.mock_programs_response(self.wrap_programs([self.PROGRAMS[0]], final=False), 1, 1)
        self.mock_programs_response({}, 2, 1, status=500)

        with self.assertRaises(slumber.exceptions.HttpServerError):
            self.call_command(page_size=1)

        self.assertFirstSaved()

    @responses.activate
    def test_update(self):
        """ Verify the command updates existing data. """
        OrganizationFactory(site=self.site,
                            uuid='33f0dded-fee9-4dec-a333-b9d8c2c82bd2',
                            key='OldX')
        ProgramFactory(site=self.site,
                       uuid='33f0dded-fee9-4dec-a333-c9d8c2c82bd5',
                       title='Old Program')

        self.mock_access_token_response()
        self.mock_programs_response(self.wrap_programs(self.PROGRAMS))
        self.call_command()

        self.assertProgramsSaved()

        org = Organization.objects.get(uuid='33f0dded-fee9-4dec-a333-b9d8c2c82bd2')
        self.assertNotEqual(org.key, 'OldX')

        program = Program.objects.get(uuid='33f0dded-fee9-4dec-a333-c9d8c2c82bd5')
        self.assertNotEqual(program.title, 'Old Program')

    @responses.activate
    def test_keep_old_data(self):
        """ Verify that we don't destroy existing but obsolete data. """
        # org with a uuid that won't be in data we get back
        org = OrganizationFactory(site=self.site,
                                  uuid='44f0dded-fee9-4dec-a333-b9d8c2c82bd2',
                                  key='OldX')
        program = ProgramFactory(site=self.site,
                                 uuid='33f0dded-fee9-4dec-a333-c9d8c2c82bd5',
                                 title='Old Program')
        program.authoring_organizations.add(org)  # pylint: disable=no-member

        self.mock_access_token_response()
        self.mock_programs_response(self.wrap_programs(self.PROGRAMS))
        self.call_command()

        org = Organization.objects.get(uuid='44f0dded-fee9-4dec-a333-b9d8c2c82bd2',
                                       key='OldX')

        # But note that it will no longer be connected to our program
        program = Program.objects.get(uuid='33f0dded-fee9-4dec-a333-c9d8c2c82bd5')
        self.assertNotIn(org, program.authoring_organizations.all())
