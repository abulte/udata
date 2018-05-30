from datetime import datetime, timedelta
from dateutil.parser import parse

from flask import current_app, json

from udata.core.storages import chunks
from udata.core.storages.api import META
from udata.tasks import get_logger, job

log = get_logger(__name__)


@job('purge-chunks')
def purge_chunks(self):
    log.info('Purging uploaded chunks')
    max_retention = timedelta(seconds=current_app.config['UPLOAD_MAX_RETENTION'])
    meta_files = (f for f in chunks.list_files() if f.endswith(META))
    for filename in meta_files:
        metadata = json.loads(chunks.read(filename))
        if datetime.now() - parse(metadata['lastchunk']) >= max_retention:
            uuid = metadata['uuid']
            log.info('Removing %s expired chunks', uuid)
            to_remote = (f for f in chunks.list_files() if f.startswith(uuid))
            for f in to_remote:
                chunks.delete(f)
