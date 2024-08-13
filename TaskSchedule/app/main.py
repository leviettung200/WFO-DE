from fastapi import FastAPI, HTTPException, Depends
from app.model.model import ConfigFaker
from app.utils.helpers import get_config_data
from app.utils.logger import logger
from app.services.data_generator import DataGenerator
from app.services.task_scheduler import TaskScheduler

app = FastAPI()

@app.post("/generate")
async def generate_data(config: ConfigFaker = Depends(get_config_data)):
    """Endpoint for generating data based on the provided configuration."""
    try:
        data_generator = DataGenerator(config)
        locations = data_generator.generate_locations()
        newTasks = data_generator.generate_new_tasks(locations)
        return {"locations": locations, "newTasks": newTasks}
    except Exception as e:
        logger.error(f"Error generating data: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error - Error generating data")  
    
@app.post("/schedule")
async def schedule_tasks(config: ConfigFaker = Depends(get_config_data)):
    """Endpoint for scheduling tasks based on the provided configuration."""
    try:
        data_generator = DataGenerator(config)
        locations = data_generator.generate_locations()
        newTasks = data_generator.generate_new_tasks(locations)
        staffs = data_generator.generate_staffs(locations)
        scheduler = TaskScheduler(config, locations, newTasks, staffs)
        scheduler.assign_tasks_to_staff()
        return {"newTasks": scheduler.newTasks, "locations": scheduler.locations, "currentTasks": scheduler.currentTasks, "staffs": scheduler.staffs}
    except Exception as e:
        logger.error(f"Error scheduling tasks: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error - Error scheduling tasks")