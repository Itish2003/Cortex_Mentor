import asyncio
from typing import Any, List, Union
from cortex.pipelines.processors import Processor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Pipeline:
    """
    Manages the execution of a sequence of processors, supporting parallel execution.
    """

    def __init__(self, processors: List[Union[Processor, List[Processor]]]):
        self.processors = processors

    async def _execute_sequential_step(self, processor: Processor, data: Any, context: dict) -> Any:
        """Executes a single processor sequentially."""
        processor_name = processor.__class__.__name__
        logger.info(f"Processing sequentially with {processor_name}...")
        try:
            data = await processor.process(data, context)
            logger.info(f"{processor_name} completed successfully.")
            return data
        except Exception as e:
            logger.error(f"Error occurred while processing with {processor_name}: {e}")
            raise

    async def _execute_parallel_step(self, processors: List[Processor], data: Any, context: dict) -> Any:
        """Executes a list of processors in parallel."""
        tasks = []
        for processor in processors:
            processor_name = processor.__class__.__name__
            logger.info(f"Processing in parallel with {processor_name}...")
            tasks.append(processor.process(data, context))
        
        parallel_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(parallel_results):
            if isinstance(result, Exception):
                processor_name = processors[i].__class__.__name__
                logger.error(f"Error occurred in parallel processor {processor_name}: {result}")
                raise result
            if isinstance(result, dict):
                if isinstance(data, dict):
                    data.update(result)
                else:
                    data = result
            else:
                logger.warning(f"Parallel processor {processors[i].__class__.__name__} returned non-dict result: {result}")

        logger.info("Parallel processing step completed.")
        return data

    async def execute(self, data: Any, context: dict) -> Any:
        """
        Executes the pipeline by passing data through each processor or group of parallel processors.
        Args:
            data: The initial input data to process.
            context: The context dictionary containing additional information.

        Returns:
            The final output data after processing.
        """
        logger.info(f"Starting pipeline execution with {len(self.processors)} steps...")
        for step in self.processors:
            if isinstance(step, list):
                data = await self._execute_parallel_step(step, data, context)
            else:
                data = await self._execute_sequential_step(step, data, context)
        logger.info("Pipeline execution completed.")
        return data