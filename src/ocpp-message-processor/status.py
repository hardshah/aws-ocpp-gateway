from enum import Enum, unique

@unique
class ConnectorStatus(Enum):
    AVAILABLE = 1
    PREPARING = 2
    CHARGING = 3
    SUSPENDED_EVSE = 4
    SUSPENDED_EV = 5
    FINISHING = 6
    RESERVED = 7
    UNAVAILABLE = 8
    FAULTED = 9

class ChargePointStatus(Enum):
    AVAILABLE = 1
    PARTIALLY_OCCUPIED = 2
    OCCUPIED = 3
    FAULTED = 4

def mapStringToConnectorStatus(string):
    match string.upper():
        case "AVAILABLE":
          return ConnectorStatus.AVAILABLE
        case "PREPARING":
          return ConnectorStatus.PREPARING
        case "CHARGING":
          return ConnectorStatus.CHARGING
        case "SUSPENDED_EVSE":
          return ConnectorStatus.SUSPENDED_EVSE
        case "SUSPENDED_EV":
          return ConnectorStatus.SUSPENDED_EV
        case "FINISHING":
          return ConnectorStatus.FINISHING
        case "RESERVED":
          return ConnectorStatus.RESERVED
        case "UNAVAILABLE":
          return ConnectorStatus.UNAVAILABLE
        case "FAULTED":
          return ConnectorStatus.FAULTED
        case _:
          return Exception("Unrecognized Status")
          