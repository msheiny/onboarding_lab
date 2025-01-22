from nautobot.apps.jobs import register_jobs

from .location_import import LocationImporter


register_jobs(LocationImporter)
