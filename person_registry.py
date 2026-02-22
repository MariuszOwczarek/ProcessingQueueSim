import random
import yaml
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from uuid import UUID, uuid4
import logging
from time import sleep
import csv

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class Config:
    def __init__(self, config_path):
        self.config_path = config_path

    def load(self):
        try:
            with open(self.config_path) as f:
                config = yaml.safe_load(f)
            return config
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Config file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Config file is invalid YAML: {e}")


class Statuses(Enum):
    UNASSIGNED = auto()
    ASSIGNED = auto()
    WAITING = auto()
    COMPLETED = auto()


class Person:
    def __init__(self, name, surname, email, processing_time):
        self.name: str = name
        self.surname: str = surname
        self.email: str = email
        self.processing_time: int = processing_time
        self.assigned_at: datetime | None = None
        self.registered_at: datetime | None = None
        self.completed_at: datetime | None = None
        self.status: Statuses = Statuses.UNASSIGNED
        self.id_no: UUID = uuid4()

    def __str__(self):
        return (f'{self.name} {self.surname}, '
                f'Email:{self.email}, '
                f'Assigned:{self.assigned_at}, '
                f'Registered:{self.registered_at}, '
                f'Completed:{self.completed_at}, '
                f'Status:{self.status.name}, '
                f'Processing time:{self.processing_time} ')

    def register(self):
        self.registered_at = datetime.now()
        self.status = Statuses.WAITING

    def assign(self):
        self.assigned_at = datetime.now()
        self.status = Statuses.ASSIGNED


class Registry:
    def __init__(self, limit: int = 20):
        self.limit = limit
        self.__assigned_list: list[Person] = []
        self.__awaiting_queue: list[Person] = []
        self.__completed_list: list[Person] = []
        self.__seen_ids: set[UUID] = set()

    @property
    def assigned_list(self):
        return tuple(self.__assigned_list)

    @property
    def completed_list(self):
        return tuple(self.__completed_list)

    @property
    def awaiting_queue(self):
        return tuple(self.__awaiting_queue)

    @property
    def available_tickets(self) -> int:
        return self.limit - len(self.__assigned_list)

    def add(self, person: Person):
        if person.id_no in self.__seen_ids:
            logger.info("You cannot add the same person twice")
            return

        self.__seen_ids.add(person.id_no)

        if person.registered_at is None:
            person.register()

        if self.available_tickets > 0:
            person.assign()
            self.__assigned_list.append(person)
        else:
            self.__awaiting_queue.append(person)

    def promote(self):
        while self.__awaiting_queue and self.available_tickets > 0:
            next_person = self.__awaiting_queue.pop(0)
            next_person.assign()
            self.__assigned_list.append(next_person)

    def complete(self, person):
        person.completed_at = datetime.now()
        person.status = Statuses.COMPLETED
        self.__assigned_list.remove(person)
        self.__seen_ids.discard(person.id_no)
        self.__completed_list.append(person)
        self.promote()

    def save(self, file):
        with open(file, 'w', encoding="UTF-8") as f:
            data = csv.writer(f, delimiter=',')
            data.writerow(["Id_no",
                           "Name",
                           "Surname",
                           "Email",
                           "Registered",
                           "Assigned",
                           "Completed"])

            for record in self.__completed_list:
                data.writerow([
                    str(record.id_no),
                    record.name,
                    record.surname,
                    record.email,
                    (record.registered_at.isoformat()
                     if record.registered_at else ""),
                    (record.assigned_at.isoformat()
                     if record.assigned_at else ""),
                    (record.completed_at.isoformat()
                     if record.completed_at else "")
                ])

    def report_detailed(self, added: int = 0, finished: int = 0):
        assigned_count = len(self.__assigned_list)
        awaiting_count = len(self.__awaiting_queue)
        completed_count = len(self.__completed_list)
        logger.info(f"Users Added: {added} | "
                    f"Users Finished: {finished} | "
                    f"Users Assigned: {assigned_count}/{self.limit} | "
                    f"Users Awaiting: {awaiting_count} | "
                    f"Users Completed total: {completed_count}")


@dataclass
class PersonGenerator:
    min_user_per_tick: int
    max_user_per_tick: int
    min_processing_time: int
    max_processing_time: int
    names: list[str]
    surnames: list[str]

    def generate(self):
        list_users = []
        number_users = random.randint(self.min_user_per_tick,
                                      self.max_user_per_tick)

        for _ in range(number_users):
            name = random.choice(self.names)
            surname = random.choice(self.surnames)
            email = f'{name}.{surname}@gmail.com'
            processing_time = random.randint(self.min_processing_time,
                                             self.max_processing_time)

            list_users.append(Person(name=name,
                                     surname=surname,
                                     email=email,
                                     processing_time=processing_time))
        return list_users


class PipelineOrchestrator:
    def __init__(self,
                 registry: Registry,
                 generator: PersonGenerator,
                 tick_interval: int,
                 tick_time_interval: int):

        self.registry = registry
        self.generator = generator
        self.tick_interval = tick_interval
        self.tick_time_interval = tick_time_interval

    def run(self):
        try:
            while self.tick_interval > 0:
                self.tick_interval -= 1

                for person in self.registry.assigned_list:
                    person.processing_time -= 1

                finished = [p for p in self.registry.assigned_list
                            if p.processing_time <= 0]

                for person in finished:
                    self.registry.complete(person)

                users = self.generator.generate()
                for user in users:
                    self.registry.add(user)

                self.registry.report_detailed(len(users), len(finished))
                sleep(self.tick_time_interval)
        except KeyboardInterrupt:
            logger.info("Simulation stopped by user")

        logger.info(f"Simulation finished. "
                    f"Total completed: {len(self.registry.completed_list)}")

        self.registry.save(file=config["file"]["output"])
        logger.info("Process Saved")


if __name__ == "__main__":

    config = Config("config.yaml").load()

    if config["registry"]["limit"] <= 0:
        raise ValueError("Registry limit must be positive")

    registry = Registry(limit=config["registry"]["limit"])
    generator = PersonGenerator(config["generator"]["min_user_per_tick"],
                                config["generator"]["max_user_per_tick"],
                                config["generator"]["min_processing_time"],
                                config["generator"]["max_processing_time"],
                                config["generator"]["names"],
                                config["generator"]["surnames"])

    pipeline = PipelineOrchestrator(registry,
                                    generator,
                                    config["pipeline"]["tick_interval"],
                                    config["pipeline"]["tick_time_interval"])
    pipeline.run()
