from app.model.model import ConfigFaker, Location, Staff, Task, Slot, StaffState
from app.utils.logger import logger
from geopy.distance import geodesic
from typing import List

class TaskScheduler():
    """Handles the task scheduling process."""
    
    def __init__(self, config: ConfigFaker, locations: List[Location], newTasks: List[Task], staffs: List[Staff]):
        """Initialize data for task scheduling: locations, tasks, staffs, and current tasks."""
        self.assign_max_num_tasks = config.current_task.assign_max_num_tasks
        self.transition_velocity = config.staffs.transition_velocity
        
        self.locations = locations
        self.newTasks = newTasks
        self.staffs = staffs
        self.currentTasks: List[Task] = []
    
    def assign_tasks_to_staff(self):
        """
        Assigns tasks to staff based on their availability, location, and current tasks.
        """
        for task in self.newTasks[:]:  # Use a slice to iterate, as we'll be modifying the list
            assigned_staff = self.find_eligible_staff(task)
            if assigned_staff:
                task.assignedStaffId = assigned_staff.staffId
                task.taskAssignmentStatus = "SCHEDULED"
                self.currentTasks.append(task)
                self.newTasks.remove(task)

    def find_eligible_staff(self, task: Task) -> Staff:
        """
        Find an eligible staff member to assign the task to.
        Eligibility is based on staff availability, location, and current tasks.
        """
        try:
            for staff in self.staffs:
                staff_state = self.get_staff_last_state(staff, task.slot.startDate)
                if (self.is_staff_available(staff_state, task) and 
                    self.can_reach_task_on_time(staff_state, task) and 
                    not self.has_reached_max_tasks(staff_state)):
                    return staff
        except Exception as e:
            logger.error(f"Error finding eligible staff: {str(e)}")
            return None

    def is_staff_available(self, staff_state: StaffState, task: Task) -> bool:
        """
        Check if the staff is available based on the task slot and staff's available slot.
        """
        if (staff_state.availableSlot.startDate == task.slot.startDate and
            staff_state.availableSlot.endDate == task.slot.endDate and
            staff_state.availableSlot.slotStart <= task.slot.slotStart and
            staff_state.availableSlot.slotEnd >= task.slot.slotEnd):
            return True
        return False

    def can_reach_task_on_time(self, staff_state: StaffState, task: Task) -> bool:
        """
        Check if the staff can reach the task location on time based on the travel time.
        """
        try:
            for location in self.locations:
                if location.locationId == staff_state.locationId:
                    last_location = location
                if location.locationId == task.locationId:
                    task_location = location
            travel_time = self.calculate_travel_time_mins(last_location, task_location)
            
            return travel_time + staff_state.availableSlot.slotStart <= task.slot.slotStart
        except Exception as e:
            logger.error(f"Error checking travel time: {str(e)}")
            return False

    def has_reached_max_tasks(self, staff_state: StaffState) -> bool:
        """
        Check if the staff has reached the maximum number of tasks they can handle.
        """
        UNLIMITED_TASKS = -1
        if self.assign_max_num_tasks == UNLIMITED_TASKS:
            return False
        return len(staff_state.currentTasks) >= self.assign_max_num_tasks

    def get_staff_last_state(self, staff: Staff, target_date: str) -> StaffState:
        """
        Get all data of the staff on the specific date (location, last task end time)
        """
        current_tasks = [task for task in self.currentTasks if task.assignedStaffId == staff.staffId and task.slot.startDate == target_date]
        # Initialize unavailable slot
        available_slot = Slot(startDate=target_date, endDate=target_date, slotStart=0, slotEnd=0)
        
        if current_tasks:
            latest_task = max(current_tasks, key=lambda task: task.slot.slotEnd)
            latest_location = latest_task.locationId
            
            available_slot.slotStart = latest_task.slot.slotEnd            
            available_slot.slotEnd = next((slot.slotEnd for slot in staff.availableDateShiftSlots if slot.startDate == target_date), 0)
        else:
            latest_location = staff.locationId
            available_slot.slotStart = next((slot.slotStart for slot in staff.availableDateShiftSlots if slot.startDate == target_date), 0)
            available_slot.slotEnd = next((slot.slotEnd for slot in staff.availableDateShiftSlots if slot.startDate == target_date), 0)
        return StaffState(staffId=staff.staffId, 
                          locationId=latest_location, 
                          currentTasks=current_tasks, 
                          availableSlot=available_slot)
    
    def calculate_travel_time_mins(self, start_location: Location, end_location: Location) -> float:
        """Calculates the travel time between two locations in minutes."""
        try:
            distance = geodesic(
                (start_location.latitude, start_location.longitude),
                (end_location.latitude, end_location.longitude)
            ).kilometers
            travel_time = (distance / self.transition_velocity) * 60
            return travel_time
        except Exception as e:
            logger.error(f"Error calculating travel time: {str(e)}")
            raise
