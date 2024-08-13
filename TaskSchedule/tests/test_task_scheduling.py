import unittest
from unittest.mock import patch
from app.model.model import ConfigFaker, Location, Staff, Task, Slot, StaffState, CurrentTaskConfig, StaffConfig, LocationConfig, NewTaskConfig
from app.services.task_scheduler import TaskScheduler

class TestTaskScheduler(unittest.TestCase):

    def setUp(self):
        """Set up mock data for testing."""
        # Mock configuration
        self.mock_config = ConfigFaker(
            start_end_date=["2024-01-01", "2024-01-01"],
            location=LocationConfig(random_range = [5, 10]),
            new_task=NewTaskConfig(
                random_range=[50, 100],
                slot_start_range=[8, 18],
                slot_duration= 200),
            current_task=CurrentTaskConfig(assign_max_num_tasks=3),
            staffs=StaffConfig(
                random_range=[10, 20],
                shift_choice=[[8, 12], [13, 17]],
                transition_velocity=60)  # 60 km/h
            )

        # Mock locations
        self.locations = [
            Location(locationId="loc1", latitude=10.0, longitude=20.0),
            Location(locationId="loc2", latitude=15.0, longitude=25.0)
        ]

        # Mock tasks
        self.newTasks = [
            Task(taskId="task1", locationId="loc1", slot=Slot(startDate="2024-01-01", endDate="2024-01-01", slotStart=10, slotEnd=12), taskAssignmentStatus=""),
            Task(taskId="task2", locationId="loc2", slot=Slot(startDate="2024-01-01", endDate="2024-01-01", slotStart=840, slotEnd=900), taskAssignmentStatus="")
        ]

        # Mock staff
        self.staffs = [
            Staff(staffId="staff1", locationId="loc1", availableDateShiftSlots=[
                Slot(startDate="2024-01-01", endDate="2024-01-01", slotStart=8, slotEnd=18)
            ])
        ]

        self.scheduler = TaskScheduler(config=self.mock_config, locations=self.locations, newTasks=self.newTasks, staffs=self.staffs)

    @patch('geopy.distance.geodesic')
    def test_assign_tasks_to_staff(self, mock_geodesic):
        """Test that tasks are assigned to staff based on availability and location."""
        self.scheduler.assign_tasks_to_staff()

        self.assertEqual(len(self.scheduler.currentTasks), 1)
        self.assertEqual(self.scheduler.currentTasks[0].assignedStaffId, "staff1")
        self.assertEqual(self.scheduler.currentTasks[0].taskAssignmentStatus, "SCHEDULED")

    def test_is_staff_available(self):
        """Test that staff availability is correctly determined."""
        staff_state = StaffState(
            staffId="staff1",
            locationId="loc1",
            currentTasks=[],
            availableSlot=Slot(startDate="2024-01-01", endDate="2024-01-01", slotStart=8, slotEnd=18)
        )
        task = self.newTasks[0]

        is_available = self.scheduler.is_staff_available(staff_state, task)
        self.assertTrue(is_available)

    @patch('geopy.distance.geodesic')
    def test_can_reach_task_on_time(self, mock_geodesic):
        """Test that the staff's ability to reach a task on time is correctly determined."""
        staff_state = StaffState(
            staffId="staff1",
            locationId="loc1",
            currentTasks=[],
            availableSlot=Slot(startDate="2024-01-01", endDate="2024-01-01", slotStart=8, slotEnd=18)
        )
        task = self.newTasks[1]

        can_reach = self.scheduler.can_reach_task_on_time(staff_state, task)
        self.assertTrue(can_reach)

    def test_has_reached_max_tasks(self):
        """Test that staff's task limit is correctly enforced."""
        staff_state = StaffState(
            staffId="staff1",
            locationId="loc1",
            currentTasks=self.newTasks[:2],  # Staff already has 2 tasks
            availableSlot=Slot(startDate="2024-01-01", endDate="2024-01-01", slotStart=8, slotEnd=18)
        )

        has_not_reached_limit = self.scheduler.has_reached_max_tasks(staff_state)
        self.assertFalse(has_not_reached_limit)

        # Add one more task to reach the limit
        staff_state.currentTasks.append(self.newTasks[0])
        has_not_reached_limit = self.scheduler.has_reached_max_tasks(staff_state)
        self.assertTrue(has_not_reached_limit)

    def test_get_staff_last_state(self):
        """Test that the staff's last state is correctly retrieved."""
        # First test with no current tasks
        staff = self.staffs[0]
        staff_state = self.scheduler.get_staff_last_state(staff, "2024-01-01")

        self.assertEqual(staff_state.staffId, "staff1")
        self.assertEqual(staff_state.locationId, "loc1")
        self.assertEqual(staff_state.availableSlot.slotStart, 8)
        self.assertEqual(staff_state.availableSlot.slotEnd, 18)

        # Now add a current task and test again
        self.newTasks[0].assignedStaffId = staff_state.staffId
        self.scheduler.currentTasks.append(self.newTasks[0])
        staff_state = self.scheduler.get_staff_last_state(staff, "2024-01-01")

        self.assertEqual(staff_state.staffId, "staff1")
        self.assertEqual(staff_state.locationId, "loc1")
        self.assertEqual(staff_state.availableSlot.slotStart, 12)  # After the first task ends
        self.assertEqual(staff_state.availableSlot.slotEnd, 18)

if __name__ == '__main__':
    unittest.main()
