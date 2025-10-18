from abc import ABC, abstractmethod
from typing import Any

class Processor(ABC):
    """
    An abstract base class for all processors in the Cortex pipeline.
    """

    @abstractmethod
    async def process(self, data: Any, context: dict) -> Any:
        """
        Process the input data and return the result.

        Args:
            data: The input data to process.
            context: The context dictionary containing additional information.

        Returns:
            The processed output data.
        """
        pass