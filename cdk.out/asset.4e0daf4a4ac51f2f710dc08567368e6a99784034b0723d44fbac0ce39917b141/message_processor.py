import json
import boto3
import ocpp.messages
from datetime import datetime
from urllib import parse
from ocpp.v201.enums import Action
from ocpp.v201.enums import RegistrationStatusType

from DB.DatabaseAccessLayer import ChargePointDAL, NetworkDAL
from status import ConnectorStatus, mapStringToConnectorStatus


uri = "mongodb+srv://hard:"+parse.quote_plus("titanic2")+"@egs.buswwxl.mongodb.net/?retryWrites=true&w=majority"
dbName = "charge_points"
charge_point_collection = "charge_points"
network_collection = "charge_points"
iot = boto3.client("iot-data", region_name=os.environ["AWS_REGION"])

chargePointDatabase = ChargePointDAL(uri, dbName, charge_point_collection)
networkDatabase = NetworkDAL(uri, dbName, network_collection)

def lambda_handler(event, _):
    print(event)
    print(f"{event=}")
    for record in event["Records"]:
        print(f"{record=}")
        handle_record(record)

    return


def handle_record(record):
    body = json.loads(record["body"])
    charge_point_id = body["chargePointId"]
    message = ocpp.messages.unpack(json.dumps(body["message"]))

    handle_charge_point_message(charge_point_id, message)


def handle_charge_point_message(charge_point_id, message):
    print(f"{message.action=} received from {charge_point_id=}")

    if message.action == Action.BootNotification:
        return handle_boot_notification(charge_point_id, message)
    elif message.action == Action.Heartbeat:
        return handle_heartbeat(charge_point_id, message)
    elif message.action == Action.RequestStartTransaction:
        return handle_start_transaction(charge_point_id, message)
    elif message.action == Action.RequestStopTransaction:
        return handle_stop_transaction(charge_point_id, message)
    elif message.action == Action.StatusNotification:
        return handle_status_notification(charge_point_id, message)
    

    return handle_unsupported_message(charge_point_id, message)

def load_balancing_algorithm(active_chargers, network_id):
    #For now an equal distribution

    max_load = networkDatabase.getNetworkSurplusById(network_id)  #Max allowable load needs to be grabbed from another database
    
    calculated_amps_at_charge_points  = max_load//active_chargers

    request = create_change_configuration_request("MaxCurrent", calculated_amps_at_charge_points)

    for charge_point_id in active_chargers:
        send_message_to_charge_point(charge_point_id, request)

def add_active_charger_to_network(charge_point_id):
   #use charge_point_id to find network_id and set status to charging
   #and then aggregate chargers in the network with the charging flag and set charging
   #Additionally must check charger status
    charge_point = chargePointDatabase.getChargePoint(charge_point_id)
    chargePointDatabase.updateStatus(charge_point_id, ConnectorStatus.CHARGING)

    network_id = charge_point["network_id"]

    active_chargers = chargePointDatabase.getChargePointsbyNetworkIdAndStatus(network_id, ConnectorStatus.CHARGING) # need to grab from database as list of charge_point_ids with charging status within same network


    load_balancing_algorithm(active_chargers,network_id)

def remove_active_charger(charge_point_id):
    charge_point = chargePointDatabase.getChargePoint(charge_point_id)
    chargePointDatabase.updateStatus(charge_point_id, ConnectorStatus.AVAILABLE)
    
    network_id = charge_point["network_id"]

    active_chargers = chargePointDatabase.getChargePointsbyNetworkIdAndStatus(network_id, ConnectorStatus.CHARGING) # need to grab from database as list of charge_point_ids with charging status within same network


    load_balancing_algorithm(active_chargers,network_id)

def create_change_configuration_request(key, value):
    # Unique message ID for the request
    message_id = str(uuid.uuid4())  # Generate a unique UUID for each message

    # Construct the ChangeConfiguration request
    change_configuration_request = {
        "messageId": message_id,
        "action": "ChangeConfiguration",
        "request": {
            "key": key,
            "value": value
        }
    }

    return change_configuration_request


def generate_transaction_id():
    return 0 ##Change to actual generator

def handle_start_transaction(charge_point_id, message):

    charge_point = chargePointDatabase.getChargePoint(charge_point_id)

    if charge_point['status'] != ConnectorStatus.AVAILABLE.value:
        response_payload = {
            "idTagInfo": {
                "status": "Rejected"  
            }
        }
        response = message.create_call_result(**response_payload)
    
        send_message_to_charge_point(charge_point_id, response)
    
    else:
        transaction_id = generate_transaction_id()
        
        response = message.create_call_result.StartTransactionPayload(
                transaction_id = transaction_id,
                id_tag_info={"status": "Accepted"}
            )
        send_message_to_charge_point(charge_point_id,response)

        add_active_charger_to_network(charge_point_id)


def handle_stop_transaction(charge_point_id, message):
    # Extract the transaction ID from the request
    transaction_id = message.payload.transaction_id

    # Here you can add any logic you need to handle when a transaction stops.
    # For example, updating a database, logging the event, etc.

    # Create the StopTransaction response
    response = message.create_call_result({
        "transaction_id": transaction_id,
        # Additional fields as required by your application logic
    })
    remove_active_charger(charge_point_id)
    # Send the response to the charge point
    send_message_to_charge_point(charge_point_id, response)

def handle_boot_notification(charge_point_id, message):
    charging_station_info = message.get('chargingStation', {})
    modem_info = message.get('modem', {})

    chargePointDatabase.addChargePoint(charge_point_id, modem_info, charging_station_info)

    response = message.create_call_result(
        {
            "currentTime": datetime.utcnow().isoformat(),
            "interval": 10,  # set default interval period in seconds
            "status": RegistrationStatusType.accepted,
        }
    )
    return send_message_to_charge_point(charge_point_id, response)


def handle_heartbeat(charge_point_id, message):
    response = message.create_call_result(
        {"currentTime": datetime.utcnow().isoformat()}
    )

    return send_message_to_charge_point(charge_point_id, response)


def handle_status_notification(charge_point_id, message):

    status = mapStringToConnectorStatus(message.status)
    chargePointDatabase.updateStatus(charge_point_id, status)

    response = message.create_call_result({})

    return send_message_to_charge_point(charge_point_id, response)


def handle_unsupported_message(charge_point_id, message):
    response = message.create_call_result(
        {"error": f"Command [{message.action}] not implemented."}
    )

    return send_message_to_charge_point(charge_point_id, response)


def update_charge_point_shadow(charge_point_id, message):
    iot_request = {
        "topic": f"$aws/things/{charge_point_id}/shadow/update",
        "qos": 1,
        "payload": json.dumps({"state": {"reported": message}}),
    }
    print(f"{iot_request=}")

    iot_response = iot.publish(**iot_request)
    print(f"{iot_response=}")

    return iot_response


def send_message_to_charge_point(charge_point_id, message):
    iot_request = {
        "topic": f"{charge_point_id}/out",
        "qos": 1,
        "payload": message.to_json(),
    }
    print(f"{iot_request=}")

    iot_response = iot.publish(**iot_request)
    print(f"{iot_response=}")

    return iot_response