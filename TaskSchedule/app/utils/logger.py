import logging

# Set up logging
logging.basicConfig(
    format= '%(asctime)s - %(levelname)-8s - %(name)s:%(lineno)d - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)