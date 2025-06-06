# Copyright © 2025 Province of British Columbia
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
"""The Unit Tests for the Transition email processor."""
from unittest.mock import patch

import pytest
from legal_api.models import Filing

from entity_emailer.email_processors import transition_notification
from tests.unit import prep_transition_filing


@pytest.mark.parametrize('status', [
    (Filing.Status.PAID.value),
    (Filing.Status.COMPLETED.value)
])
def test_transition_notification(app, session, mocker, status):
    """Assert Transition notification is created."""
    # setup filing + business for email
    legal_name = 'test business'
    filing = prep_transition_filing(session, 'BC1234567', '1', status, legal_name)
    token = 'token'
    # test processor
    mocker.patch(
        'entity_emailer.email_processors.transition_notification.get_entity_dashboard_url',
        return_value='https://dummyurl.gov.bc.ca')
    with patch.object(transition_notification, '_get_pdfs', return_value=[]) as mock_get_pdfs:
        with patch.object(transition_notification, 'get_recipient_from_auth',
                          return_value='recipient@email.com'):
            email = transition_notification.process(
                {'filingId': filing.id, 'type': 'transition', 'option': status}, token)

            assert 'recipient@email.com' in email['recipients']
            if status == Filing.Status.PAID.value:
                assert email['content']['subject'] == 'Confirmation of Filing from the Business Registry'
            else:
                assert mock_get_pdfs.call_args[0][2]['identifier'] == 'BC1234567'
                assert email['content']['subject'] == 'Transition Documents from the Business Registry'

            assert email['content']['body']
            assert email['content']['attachments'] == []
            assert mock_get_pdfs.call_args[0][0] == status
            assert mock_get_pdfs.call_args[0][1] == token
            assert mock_get_pdfs.call_args[0][3] == filing
