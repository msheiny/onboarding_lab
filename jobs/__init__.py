from nautobot.apps.jobs import register_jobs

from jobs.location_import import LocationImporter


register_jobs(LocationImporter)
