from typing import Any, List
from cortex.pipelines.processors import Processor
import logging  
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Pipeline:
    """
    Manages the execution of a sequence of processors.
    """

    def __init__(self, processors: List[Processor]):
        self.processors = processors

    async def execute(self, data: Any, context: dict) -> Any:
        """
        Executes the pipeline by passing data through each processor in sequence.
        Args:
            data: The initial input data to process.
            context: The context dictionary containing additional information.

        Returns:
            The final output data after processing.
        """
        logger.info(f"Starting pipeline execution with {len(self.processors)} processors...")
        for processor in self.processors:
            processor_name = processor.__class__.__name__
            logger.info(f"Processing with {processor_name}...")

            try:
                data = await processor.process(data, context)
                logger.info(f"{processor_name} completed successfully.")
            except Exception as e:
                logger.error(f"Error occurred while processing with {processor_name}: {e}")
                # Optionally, you can re-raise the exception or handle it as needed
                raise
        logger.info("Pipeline execution completed.")
        return data