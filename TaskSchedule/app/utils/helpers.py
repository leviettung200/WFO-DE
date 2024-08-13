import yaml
from fastapi import Request, HTTPException
from app.model.model import ConfigFaker
from app.utils.logger import logger

async def get_config_data(request: Request) -> ConfigFaker:
    """Parses and validates the configuration data from the request body."""
    try:
        body = await request.body()
        config_yaml = yaml.safe_load(body)
        config = ConfigFaker(**config_yaml)
        return config
        
    except yaml.YAMLError as e:
        logger.error(str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        logger.error(str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(str(e))
        raise HTTPException(status_code=400, detail=str(e))
