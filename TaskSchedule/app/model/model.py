from pydantic import BaseModel, field_validator, model_validator
from typing import List, Optional
from datetime import datetime


class LocationConfig(BaseModel):
    random_range: List[int]
    
    @field_validator('random_range')
    def validate_staff_range(cls, v):
        if len(v) != 2 or v[0] > v[1]:
            raise ValueError("random_range must have exactly two elements, and the first must be less than or equal to the second.")
        return v
    
class NewTaskConfig(BaseModel):
    random_range: List[int]
    slot_start_range: List[int]
    slot_duration: int
    
    @field_validator('random_range')
    def validate_staff_range(cls, v):
        if len(v) != 2 or v[0] > v[1]:
            raise ValueError("random_range must have exactly two elements, and the first must be less than or equal to the second.")
        return v
    
    
    @field_validator('slot_start_range')
    def validate_ranges(cls, v):
        if len(v) != 2 or v[0] > v[1]:
            raise ValueError("slot_start_range must have exactly two elements, and the first must be less than or equal to the second.")
        if v[0] < 0 or v[1] > 1440:
            raise ValueError("slot_start_range must be a positive integer within a practical range (0-1440 minutes).")
        return v

    @field_validator('slot_duration')
    def validate_slot_duration(cls, v):
        if v <= 0 or v > 1440:
            raise ValueError("slot_duration must be a positive integer within a practical range (1-1440 minutes).")
        return v

class StaffConfig(BaseModel):
    random_range: List[int]
    shift_choice: List[List[int]]
    transition_velocity: int

    @field_validator('random_range')
    def validate_staff_range(cls, v):
        if len(v) != 2 or v[0] > v[1]:
            raise ValueError("random_range must have exactly two elements, and the first must be less than or equal to the second.")
        return v

    @field_validator('shift_choice')
    def validate_shift_choice(cls, v):
        for shift in v:
            if len(shift) != 2 or shift[0] >= shift[1]:
                raise ValueError("Each shift in shift_choice must have exactly two elements, and the first must be less than the second.")
        return v

    @field_validator('transition_velocity')
    def validate_transition_velocity(cls, v):
        if v <= 0:
            raise ValueError("transition_velocity must be a positive integer.")
        return v
    
class CurrentTaskConfig(BaseModel):
    assign_max_num_tasks: int
    
    @field_validator('assign_max_num_tasks')
    def validate_assign_max_num_tasks(cls, v):
        if v < -1:
            raise ValueError("assign_max_num_tasks must be -1 or a non-negative integer.")
        return v

class ConfigFaker(BaseModel):
    start_end_date: List[str]
    location: LocationConfig
    new_task: NewTaskConfig
    staffs: StaffConfig
    current_task: CurrentTaskConfig

    @field_validator('start_end_date')
    def validate_start_end_date(cls, v):
        if len(v) != 2:
            raise ValueError("start_end_date must have exactly two dates.")
        start_date, end_date = v
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Dates must be in 'YYYY-MM-DD' format.")
        if start_dt > end_dt:
            raise ValueError("start_end_date: Start date must be earlier than or equal to the end date.")
        return v
    
    @model_validator(mode='before')
    def validate_date_range(cls, values):
        start_end_date = values.get('start_end_date')
        if start_end_date:
            start_dt = datetime.strptime(start_end_date[0], "%Y-%m-%d")
            end_dt = datetime.strptime(start_end_date[1], "%Y-%m-%d")
            if (end_dt - start_dt).days > 90:
                raise ValueError("The date range should not exceed 3 months.")
        return values
    
class Location(BaseModel):
    """Represents a location with an ID and coordinates."""
    locationId: str
    latitude: float
    longitude: float

class Slot(BaseModel):
    """Represents a time slot for tasks or staff availability."""
    startDate: str
    endDate: str
    slotStart: int
    slotEnd: int

class Task(BaseModel):
    """Represents a task with its location, time slot, and assignment status."""
    locationId: str
    slot: Slot
    taskId: str
    taskAssignmentStatus: str
    assignedStaffId: Optional[str] = None

class Staff(BaseModel):
    """Represents a staff member with their ID, location, and available slots."""
    staffId: str
    locationId: str
    availableDateShiftSlots: List[Slot]

class StaffState(BaseModel):
    """Represents current state of a staff member with their ID, location, available slots, current tasks."""
    staffId: str
    locationId: str
    availableSlot: Optional[Slot] = None
    currentTasks: Optional[List[Task]] = None