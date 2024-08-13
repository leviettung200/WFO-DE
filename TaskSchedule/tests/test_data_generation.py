from datetime import datetime, timedelta
import unittest
from typing import List
from app.model.model import ConfigFaker, Location, Slot, Staff, Task, StaffState, LocationConfig, NewTaskConfig, StaffConfig, CurrentTaskConfig
from app.services.data_generator import DataGenerator

class TestDataGenerator(unittest.TestCase):
    def setUp(self):
        self.config = ConfigFaker(
            location=LocationConfig(random_range=[5, 10]),
            new_task=NewTaskConfig(
                random_range=[50, 100],
                slot_start_range=[8, 18],
                slot_duration=2
            ),
            staffs=StaffConfig(
                random_range=[10, 20],
                shift_choice=[[8, 12], [13, 17]],
                transition_velocity=10
            ),
            start_end_date=["2023-04-01", "2023-04-30"],
            current_task=CurrentTaskConfig(assign_max_num_tasks=-1)
        )
        self.data_generator = DataGenerator(self.config)

    def test_generate_locations(self):
        locations = self.data_generator.generate_locations()
        self.assertIsInstance(locations, List)
        self.assertGreaterEqual(len(locations), self.config.location.random_range[0])
        self.assertLessEqual(len(locations), self.config.location.random_range[1])
        for location in locations:
            self.assertIsInstance(location, Location)
            self.assertIsInstance(location.locationId, str)
            self.assertGreaterEqual(location.latitude, -90)
            self.assertLessEqual(location.latitude, 90)
            self.assertGreaterEqual(location.longitude, -180)
            self.assertLessEqual(location.longitude, 180)

    def test_generate_new_tasks_daily(self):
        locations = self.data_generator.generate_locations()
        tasks = self.data_generator.generate_new_tasks_daily("2023-04-01", locations, 10)
        self.assertIsInstance(tasks, List)
        self.assertEqual(len(tasks), 10)
        for task in tasks:
            self.assertIsInstance(task, Task)
            self.assertIsInstance(task.locationId, str)
            self.assertIsInstance(task.slot, Slot)
            self.assertEqual(task.slot.startDate, "2023-04-01")
            self.assertEqual(task.slot.endDate, "2023-04-01")
            self.assertGreaterEqual(task.slot.slotStart, self.config.new_task.slot_start_range[0])
            self.assertLessEqual(task.slot.slotStart, self.config.new_task.slot_start_range[1])
            self.assertEqual(task.slot.slotEnd, task.slot.slotStart + self.config.new_task.slot_duration)
            self.assertEqual(task.taskAssignmentStatus, "OPEN")
            self.assertIsNone(task.assignedStaffId)

    def test_generate_new_tasks(self):
        locations = self.data_generator.generate_locations()
        tasks = self.data_generator.generate_new_tasks(locations)
        self.assertIsInstance(tasks, List)
        start_date = datetime.strptime(self.config.start_end_date[0], "%Y-%m-%d")
        end_date = datetime.strptime(self.config.start_end_date[1], "%Y-%m-%d")
        self.assertGreaterEqual(len(tasks), self.config.new_task.random_range[0] * (end_date - start_date).days)
        self.assertLessEqual(len(tasks), self.config.new_task.random_range[1] * (end_date - start_date).days)
        for task in tasks:
            self.assertIsInstance(task, Task)
            self.assertIsInstance(task.locationId, str)
            self.assertIsInstance(task.slot, Slot)
            self.assertGreaterEqual(task.slot.slotStart, self.config.new_task.slot_start_range[0])
            self.assertLessEqual(task.slot.slotStart, self.config.new_task.slot_start_range[1])
            self.assertEqual(task.slot.slotEnd, task.slot.slotStart + self.config.new_task.slot_duration)
            self.assertEqual(task.taskAssignmentStatus, "OPEN")
            self.assertIsNone(task.assignedStaffId)
    
    def test_generate_available_date_shift_slots(self):
        slots = self.data_generator.generate_available_date_shift_slots()
        self.assertIsInstance(slots, List)
        start_date = datetime.strptime(self.config.start_end_date[0], "%Y-%m-%d")
        end_date = datetime.strptime(self.config.start_end_date[1], "%Y-%m-%d")
        self.assertEqual(len(slots), (end_date - start_date + timedelta(days=1)).days)
        for slot in slots:
            self.assertIsInstance(slot, Slot)
            self.assertIsInstance(slot.startDate, str)
            self.assertIsInstance(slot.endDate, str)
            self.assertIsInstance(slot.slotStart, int)
            self.assertIsInstance(slot.slotEnd, int)
            self.assertIn(slot.slotStart, [choice[0] for choice in self.config.staffs.shift_choice])
            self.assertIn(slot.slotEnd, [choice[1] for choice in self.config.staffs.shift_choice])

    def test_generate_staffs(self):
        locations = self.data_generator.generate_locations()
        staffs = self.data_generator.generate_staffs(locations)
        self.assertIsInstance(staffs, List)
        self.assertGreaterEqual(len(staffs), self.config.staffs.random_range[0])
        self.assertLessEqual(len(staffs), self.config.staffs.random_range[1])
        start_date = datetime.strptime(self.config.start_end_date[0], "%Y-%m-%d")
        end_date = datetime.strptime(self.config.start_end_date[1], "%Y-%m-%d")
        self.assertEqual(len(staffs[0].availableDateShiftSlots), (end_date - start_date + timedelta(days=1)).days)
        for staff in staffs:
            self.assertIsInstance(staff, Staff)
            self.assertIsInstance(staff.staffId, str)
            self.assertIsInstance(staff.locationId, str)
            self.assertIn(staff.locationId, [loc.locationId for loc in locations])
            self.assertIsInstance(staff.availableDateShiftSlots, List)
            for slot in staff.availableDateShiftSlots:
                self.assertIsInstance(slot, Slot)
                self.assertIn(slot.slotStart, [choice[0] for choice in self.config.staffs.shift_choice])
                self.assertIn(slot.slotEnd, [choice[1] for choice in self.config.staffs.shift_choice])


if __name__ == '__main__':
    unittest.main()
