import csv
from nautobot.dcim.models import Location, LocationType
from nautobot.extras.jobs import Job, TextVar
from nautobot.extras.models import Status


class LocationImporter(Job):
    csv_content = TextVar(description="CSV content to import")

    class Meta:
        """Takes in a CSV file, builds out locations."""

        name = "Location Importer"

    def _type_not_found(self, type: str) -> LocationType:
        location_result = LocationType.objects.get(name=type)
        if not location_result:
            raise EnvironmentError(f"Type {type} not found")
        return location_result

    def before_start(self, task_id, args, kwargs) -> None:
        """Validate city, state, and DC types already exist. Grab type references."""
        self.city_type = self._type_not_found(type="City")
        self.state_type = self._type_not_found(type="State")
        self.dc_type = self._type_not_found(type="Data Center")
        self.branch_type = self._type_not_found(type="Branch")

    def _validate_state(self, state: str) -> str:
        if len(state) == 2:
            raise ValueError(f"State {state} should be fully expanded, not a 2 letter code")
        return state.capitalize()

    def run(self, csv_content: str):
        self.logger.info("Running Location Importer")

        for row in csv.DictReader(csv_content.splitlines(), fieldnames=["name", "city", "state"]):
            if row["name"] == "name":
                continue
            else:
                try:
                    active_state = Status.objects.get(name="Active")

                    state = Location.objects.get_or_create(
                        name=self._validate_state(row["state"]), location_type=self.state_type, status=active_state
                    )
                    city = Location.objects.get_or_create(
                        name=row["city"], location_type=self.city_type, parent=state[0], status=active_state
                    )

                    site_name = row["name"]
                    if site_name.endswith("DC"):
                        site_type = self.dc_type
                    elif site_name.endswith("BR"):
                        site_type = self.branch_type
                    else:
                        raise ValueError(f"Site name {site_name} does not end with DC or BR")

                    Location.objects.get_or_create(
                        name=site_name, location_type=site_type, parent=city[0], status=active_state
                    )
                    self.logger.info(f"Created location {site_name}")
                except ValueError as e:
                    self.logger.error(f"Error processing {row}")
                    self.logger.error(e)
                    continue
