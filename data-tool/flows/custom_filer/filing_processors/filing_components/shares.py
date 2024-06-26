# Copyright © 2020 Province of British Columbia
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
"""Manages the share structure for a business."""
from __future__ import annotations

from typing import Dict, List, Optional

from dateutil.parser import parse
from legal_api.models import Business, Resolution, ShareClass, ShareSeries


def update_share_structure(business: Business, share_structure: Dict) -> Optional[List]:
    """Manage the share structure for a business.

    Assumption: The structure has already been validated, upon submission.

    Other errors are recorded and will be managed out of band.
    """
    if not business or not share_structure:
        # if nothing is passed in, we don't care and it's not an error
        return None

    err = []

    if resolution_dates := share_structure.get('resolutionDates'):
        for resolution_dt in resolution_dates:
            try:
                d = Resolution(
                    resolution_date=parse(resolution_dt).date(),
                    resolution_type=Resolution.ResolutionType.SPECIAL.value
                )
                business.resolutions.append(d)
            except (ValueError, OverflowError):
                err.append(
                    {'error_code': 'FILER_INVALID_RESOLUTION_DATE',
                     'error_message': f"Filer: invalid resolution date:'{resolution_dt}'"}
                )

    if share_classes := share_structure.get('shareClasses'):
        try:
            delete_existing_shares(business)
        except:  # noqa:E722 pylint: disable=bare-except; catch all exceptions
            err.append(
                {'error_code': 'FILER_UNABLE_TO_DELETE_SHARES',
                 'error_message': f"Filer: unable to delete shares for :'{business.identifier}'"}
            )
            # we're FUBAR, do not load the new shares
            return err

        try:
            for share_class_info in share_classes:
                share_class = create_share_class(share_class_info)
                business.share_classes.append(share_class)
        except KeyError:
            err.append(
                {'error_code': 'FILER_UNABLE_TO_SAVE_SHARES',
                 'error_message': f"Filer: unable to save new shares for :'{business.identifier}'"}
            )

    return err


def delete_existing_shares(business: Business):
    """Delete the existing share classes and series for a business."""
    if existing_shares := business.share_classes.all():
        for share_class in existing_shares:
            business.share_classes.remove(share_class)


def create_share_class(share_class_info: dict) -> ShareClass:
    """Create a new share class and associated series."""
    share_class = ShareClass(
        name=share_class_info['name'],
        priority=share_class_info['priority'],
        max_share_flag=share_class_info['hasMaximumShares'],
        max_shares=share_class_info.get('maxNumberOfShares', None),
        par_value_flag=share_class_info['hasParValue'],
        par_value=share_class_info.get('parValue', None),
        currency=share_class_info.get('currency', None),
        special_rights_flag=share_class_info['hasRightsOrRestrictions']
    )
    share_class.skip_share_class_listener = True

    share_class.series = []
    for series in share_class_info['series']:
        share_series = ShareSeries(
            name=series['name'],
            priority=series['priority'],
            max_share_flag=series['hasMaximumShares'],
            max_shares=series.get('maxNumberOfShares', None),
            special_rights_flag=series['hasRightsOrRestrictions']
        )
        share_series.skip_share_series_listener = True
        share_class.series.append(share_series)

    return share_class
