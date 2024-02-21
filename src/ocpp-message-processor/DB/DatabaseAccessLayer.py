from urllib import parse
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from bson import ObjectId
from status import ChargePointStatus
uri = "mongodb+srv://hard:"+parse.quote_plus("titanic2")+"@egs.buswwxl.mongodb.net/?retryWrites=true&w=majority"
# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
# Send a ping to confirm a successful connection

class ChargePointDAL:
    def __init__(self, uri, dbName, collectionName):
        self.client = MongoClient(uri, server_api=ServerApi('1'))
        self.db = client[dbName]
        self.collection = self.db[collectionName]

    def getChargePointsbyNetworkId(self, network_id, status):
        query = {
        'network_id': network_id
        }
        results = list(self.collection.find(query))
        return results
    
    def getChargePointsbyNetworkIdAndStatus(self, network_id, status):
        query = {
        'status': status.value,
        'network_id': network_id
        }
        results = list(self.collection.find(query))
        return results
    def updateStatus(self,cp_id, status):
        obj_id = ObjectId(cp_id)
        result = self.collection.update_one(
                    {'_id': obj_id},
                    {'$set': {'status': status.value}})
        return result
    def getChargePoint(self, cp_id):
        obj_id = ObjectId(cp_id)
        query = {
            '_id' : {obj_id}
        }
        results = list(self.collection.find(query))
        return results
    def addChargePoint(self, cp_id, modem_info, charging_station_info):
        # Extracting information from the chargingStation and modem sections
        
        model = charging_station_info.get('model')
        vendor_name = charging_station_info.get('vendorName')
        serial_number = charging_station_info.get('serialNumber')
        firmware_version = charging_station_info.get('firmwareVersion')
        
        iccid = modem_info.get('iccid')
        imsi = modem_info.get('imsi')

        charge_point = {
        "chargePointId": cp_id,
        "model": model,
        "vendorName": vendor_name,
        "serialNumber": serial_number,
        "firmwareVersion": firmware_version,
        "iccid": iccid,
        "imsi": imsi,
        "status": ChargePointStatus.AVAILABLE
        }

        self.collection.insert_one(charge_point)

class NetworkDAL:
    def __init__(self, uri, dbName, collectionName):
        self.client = MongoClient(uri, server_api=ServerApi('1'))
        self.db = client[dbName]
        self.collection = self.db[collectionName]

    def getNetworkSurplusById(self, network_id):
        query = {
        '_id': network_id
        }
        results = list(self.collection.find_one(query))
        return results["surplus"]
    def registerNetwork(self, surplus, location):
        network = {
            "surplus" : surplus,
            "location" : location
        }
        self.collection._insert_one(network)
        
    
## Boilerplate to test connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

