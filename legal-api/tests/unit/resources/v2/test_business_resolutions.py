# Copyright © 2023 Province of British Columbia
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests to assure the business-resolutions end-point.

Test-Suite to ensure that the /businesses../resolutions endpoint is working as expected.
"""
import pytest
from http import HTTPStatus

from legal_api.models import Party, Resolution
from legal_api.services.authz import ACCOUNT_IDENTITY, PUBLIC_USER, STAFF_ROLE, SYSTEM_ROLE
from tests import FROZEN_DATETIME
from tests.unit.models import factory_business
from tests.unit.services.utils import create_header


@pytest.mark.parametrize('test_name,role', [
    ('public-user', PUBLIC_USER),
    ('account-identity', ACCOUNT_IDENTITY),
    ('staff', STAFF_ROLE),
    ('system', SYSTEM_ROLE)
])
def test_get_business_resolutions(app, session, client, jwt, requests_mock, test_name, role):
    """Assert that business resolutions are returned."""
    identifier = 'CP1234567'
    resolution_text = 'bla bla'
    business = factory_business(identifier)
    signing_party = Party(first_name='signing', last_name='party')
    resolution = Resolution(resolution_date=FROZEN_DATETIME,
                            resolution_type=Resolution.ResolutionType.SPECIAL.value,
                            signing_date=FROZEN_DATETIME,
                            resolution=resolution_text)

    resolution.party = signing_party
    business.resolutions = [resolution]
    business.save()

    # mock response from auth to give view access (not needed if staff / system)
    requests_mock.get(f"{app.config.get('AUTH_SVC_URL')}/entities/{identifier}/authorizations", json={'roles': ['view']})

    rv = client.get(f'/api/v2/businesses/{identifier}/resolutions',
                    headers=create_header(jwt, [role], identifier)
                    )
    # check
    assert rv.status_code == HTTPStatus.OK
    assert 'resolutions' in rv.json
    assert rv.json == {'resolutions': [resolution.json]}


def test_get_share_classes_unauthorized(app, session, client, jwt, requests_mock):
    """Assert that share classes are not returned for an unauthorized user."""
    # setup
    identifier = 'CP7654321'
    business = factory_business(identifier)
    business.save()

    requests_mock.get(f"{app.config.get('AUTH_SVC_URL')}/entities/{identifier}/authorizations", json={'roles': []})

    # test
    rv = client.get(f'/api/v2/businesses/{identifier}/resolutions',
                    headers=create_header(jwt, [PUBLIC_USER], identifier)
                    )
    # check
    assert rv.status_code == HTTPStatus.UNAUTHORIZED
    assert rv.json == {'message': f'You are not authorized to view resolutions for {identifier}.'}
