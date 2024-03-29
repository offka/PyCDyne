import httplib, urllib
from xml.dom import minidom
from datetime import datetime

class PyCDYNEKeysException(Exception):
    pass

class PyCDYNEResponseException(Exception):
    pass

class PyCDYNE(object):

    API_HOST = "sms2.cdyne.com"
    API_PATH = "/sms.svc"
    API_LICENSE = ""
    API_METHODS = {
        "simple_sms_send": {
            "method": "SimpleSMSsend",
            "type": "GET",
            "keys": ['PhoneNumber', 'Message']
        },
        "simple_sms_send_with_postback": {
            "method": "SimpleSMSsendWithPostback",
            "type": "GET",
            "keys": ['PhoneNumber', 'Message', 'StatusPostBackURL']
        },
        "cancel_message": {
            "method": "CancelMessage",
            "type": "GET",
            "keys": ['MessageID']
        },
        "get_message_status": {
            "method": "GetMessageStatus",
            "type": "GET",
            "keys": ['MessageID']
        },
        "get_message_status_by_reference_id": {
            "method": "GetMessageStatusByReferenceID",
            "type": "GET",
            "keys": ['ReferenceID']
        },
        "get_unread_incoming_messages": {
            "method": "GetUnreadIncomingMessages",
            "type": "GET",
            "keys": []
        }
    }
    CONNECTION_TIMEOUT = 10
    RESPONSE_STATUS_OK = 200


    def __init__(self, license):
        self.API_LICENSE = license


    def __validate_keys(self, params, keys):
        """
        Validate required keys in params
        """
        if not sorted(keys) == sorted(params.keys()):
            raise PyCDYNEKeysException("One or more of required parameters is missing: %s" % keys)


    def __get_typed_node_data(self, node):
        """
        Returning typed node values
        """
        boolean_fields = ['Cancelled', 'Queued', 'Sent']
        datetime_fields = ['SentDateTime']

        name = node.parentNode.nodeName
        data = node.data

        if name in boolean_fields:
            return True if data == u"true" else False

        if name in datetime_fields:
            return datetime.strptime(data, "%Y-%m-%dT%H:%M:%S")

        return data


    def __xml_to_dict(self, node):
        """
        Convert XML response to dictionary
        """

        response = {}
        if node.hasChildNodes():
            for child in node.childNodes:
                if isinstance(child, minidom.Element):
                    if (len(child.childNodes) == 1) and (isinstance(child.childNodes[0], minidom.Text)):
                        response.update({
                            child.nodeName: self.__get_typed_node_data(child.childNodes[0])
                        })
                    else:
                        response.update({
                            child.nodeName: self.__xml_to_dict(child)
                        })

        return response


    def __send_request(self, method, request_type, params):
        """
        Send request to service
        """
        params.update({
            'LicenseKey': self.API_LICENSE
        })
        params = urllib.urlencode(params)

        connection = httplib.HTTPConnection(self.API_HOST, timeout=self.CONNECTION_TIMEOUT)
        request_path = "%s/%s" % (self.API_PATH, method)

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent':'Mozilla/4.0'
        }

        if request_type == "POST":
            connection.request(request_type, request_path, params, headers)

        else:
            connection.request(request_type, "%s?%s" % (request_path, params), "", headers)

        response = connection.getresponse()

        if response.status == self.RESPONSE_STATUS_OK:
            return self.__xml_to_dict(minidom.parse(response))

        raise PyCDYNEResponseException("Invalid server response: %s" % response.read())


    # CDYNE API METHODS

    def __getattr__(self, name):
        if self.API_METHODS.has_key(name):
            setattr(self, "CALL_METHOD", name)
            return self.call

        raise AttributeError()


    def call(self, params):

        method = self.API_METHODS.get(self.CALL_METHOD).get("method")
        request_type = self.API_METHODS.get(self.CALL_METHOD).get("type")
        keys = self.API_METHODS.get(self.CALL_METHOD).get("keys")
        delattr(self, "CALL_METHOD")

        self.__validate_keys(params, keys)
        return self.__send_request(method, request_type, params)


# Debug section
if __name__ == "__main__":
    client = PyCDYNE("13")
    print client.simple_sms_send({
        "PhoneNumber": "1234567890",
        "Message": "This Is A Test"
    })