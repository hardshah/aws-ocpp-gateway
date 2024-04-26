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
    if string.upper() == "AVAILABLE":
      return ConnectorStatus.AVAILABLE
    elif string.upper() == "PREPARING":
      return ConnectorStatus.PREPARING
    elif string.upper() == "CHARGING" :
      return ConnectorStatus.CHARGING
    elif string.upper() == "SUSPENDED_EVSE":
      return ConnectorStatus.SUSPENDED_EVSE
    elif string.upper() == "SUSPENDED_EV":
      return ConnectorStatus.SUSPENDED_EV
    elif string.upper() == "FINISHING":
      return ConnectorStatus.FINISHING
    elif string.upper() == "RESERVED":
      return ConnectorStatus.RESERVED
    elif string.upper() == "UNAVAILABLE":
      return ConnectorStatus.UNAVAILABLE
    elif string.upper() == "FAULTED":
      return ConnectorStatus.FAULTED
    else:
      return Exception("Unrecognized Status")
          