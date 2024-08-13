from datetime import datetime, timedelta
import random
from typing import List
import uuid
from app.utils.logger import logger
from app.model.model import ConfigFaker, Location, Slot, Staff, Task

class DataGenerator:
    """Handles the generation of data for task scheduling."""
    
    def __init__(self, config: ConfigFaker):
        """Initialize configuration data for generating data."""
        self.location = config.location
        self.new_task = config.new_task
        self.staffs = config.staffs
        # self.staffs.shift_choice.append(None)  # Add a shift choice for staff being unavailable
        self.current_task = config.current_task
        self.start_date = datetime.strptime(config.start_end_date[0], "%Y-%m-%d")
        self.end_date = datetime.strptime(config.start_end_date[1], "%Y-%m-%d")
        
    def generate_locations(self) -> List[Location]:
        """Generates a list of locations based on the configuration."""
        LATITUDE_RANGE = (-90, 90)
        LONGITUDE_RANGE = (-180, 180)
        total_location = random.randint(
            self.location.random_range[0],
            self.location.random_range[1]
            )
        locations = []
        for _ in range(total_location):
            locations.append(
                Location(
                    locationId=str(uuid.uuid4()),
                    latitude = random.uniform(*LATITUDE_RANGE),
                    longitude = random.uniform(*LONGITUDE_RANGE))
                )
        return locations
    
    def generate_new_tasks_daily(self, task_date: str, locations: List[Location], tasks_per_day: int) -> List[Task]:
        """
        Generate tasks per day based on the configuration data and locations.
        New_task must have slot date within task_date (a day of start_end_date)
        """
        tasks = []
        for _ in range(tasks_per_day):
            slot_start = random.randint(
                self.new_task.slot_start_range[0],
                self.new_task.slot_start_range[1]
            )
            slot_end = slot_start + self.new_task.slot_duration
            slot = Slot(startDate=task_date,
                    endDate=task_date,
                    slotStart=slot_start,
                    slotEnd=slot_end)
            
            task = Task(
                locationId=random.choice(locations).locationId,
                slot=slot,
                taskId=str(uuid.uuid4()),
                taskAssignmentStatus= "OPEN"
            )
            tasks.append(task)
        return tasks
    
    def generate_new_tasks(self, locations: List[Location]) -> List[Task]:
        """Generates new tasks based on the given locations and configuration."""
        MAX_TASKS_PER_DAY = 10000
        task_date = self.start_date
        new_tasks = []
        total_tasks = 0
        # Generate new tasks for each day from start to end date
        while task_date <= self.end_date:
            tasks_per_day = random.randint(
                self.new_task.random_range[0],
                self.new_task.random_range[1]
            )
            total_tasks += tasks_per_day

            # Check if adding daily tasks exceeds the total limit
            if total_tasks > MAX_TASKS_PER_DAY:
                tasks_per_day = MAX_TASKS_PER_DAY - total_tasks

            daily_tasks = self.generate_new_tasks_daily(str(task_date.date()), locations, tasks_per_day)
            new_tasks.extend(daily_tasks)
            task_date += timedelta(days=1)
        return new_tasks

    def generate_available_date_shift_slots(self) -> List[Slot]:
        """
        Generate available date shift slot each day for staff based on start_end_date and shift_choice in config_data.
        """
        available_date_shift_slots = []
        slot_date = self.start_date
        while slot_date <= self.end_date:
            shift_slot_time = random.choice(self.staffs.shift_choice)
            # Check if shift_slot_time is None which means staff is not available
            # if shift_slot_time is None:
            #     slot_date += timedelta(days=1)
            #     continue
            slot = Slot(
                startDate=str(slot_date.date()),
                endDate=str(slot_date.date()),
                slotStart=shift_slot_time[0],
                slotEnd=shift_slot_time[1]
            )
            available_date_shift_slots.append(slot)
            slot_date += timedelta(days=1)
        return available_date_shift_slots
    
    def generate_staffs(self, locations: List[Location]) -> List[Staff]:
        """Generates staff members based on the given locations and configuration."""
        
        staffs = []
        total_staff = random.randint(
            self.staffs.random_range[0],
            self.staffs.random_range[1]
        )
        # Staff have multiple shifts but each day staff only have 1 shift chosen randomly, the list of shift slot would be stored in availableDateShiftSlots

        for _ in range(total_staff):
            staff = Staff(
                staffId=str(uuid.uuid4()),
                locationId=random.choice(locations).locationId,
                availableDateShiftSlots=self.generate_available_date_shift_slots()
            )
            staffs.append(staff)
        return staffs
