from abc import ABC, abstractmethod

class ConnectedPinInterface(ABC):
    @abstractmethod
    def getAddress(self) -> int:
        pass

    @abstractmethod
    def getPinNumber(self) -> int:
        pass

    @abstractmethod
    def onChange(self, value: int) -> None:
        pass