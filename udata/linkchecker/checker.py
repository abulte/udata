# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from datetime import datetime, timedelta

from flask import current_app

from .backends import get as get_linkchecker


def _get_check_keys(the_dict):
    return {k: v for k, v in the_dict.iteritems() if k.startswith('check:')}


def get_cache(resource):
    '''Return a cached version from a resource's check if any and fresh'''
    if resource.extras.get('check:date'):
        cache_duration = current_app.config['LINKCHECKING_CACHE_DURATION']
        limit_date = datetime.now() + timedelta(seconds=cache_duration)
        if resource.extras['check:date'] <= limit_date:
            return _get_check_keys(resource.extras)


def check_resource(resource):
    '''
    Check a resource availability against a linkchecker backend

    The linkchecker used can be configured on a resource basis by setting
    the `resource.extras['check:checker']` attribute with a key that points
    to a valid `udata.linkcheckers` entrypoint. If not set, it will
    fallback on the default linkchecker defined by the configuration variable
    `LINKCHECKING_DEFAULT_LINKCHECKER`.

    Returns
    -------
    dict or (dict, int)
        Check results dict and status code (if error).
    '''
    cached_check = get_cache(resource)
    if cached_check:
        return cached_check
    linkchecker_type = resource.extras.get('check:checker')
    LinkChecker = get_linkchecker(linkchecker_type)
    if not LinkChecker:
        return {'error': 'No linkchecker configured.'}, 503
    result = LinkChecker().check(resource)
    if not result:
        return {'error': 'No response from linkchecker'}, 503
    elif result.get('check:error'):
        return {'error': result['check:error']}, 500
    elif not result.get('check:status'):
        return {'error': 'No status in response from linkchecker'}, 503
    # store the check result in the resource's extras
    resource.extras.update(_get_check_keys(result))
    resource.save()
    return result
