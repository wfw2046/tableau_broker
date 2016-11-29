import string
import random
import bottle
import os
from config import *
import requests  # Contains methods used to make HTTP requests
import xml.etree.ElementTree as ET  # Contains methods used to build and parse XML
import etcd

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


xmlns = {'t': 'http://tableau.com/api'}



class ApiCallError(Exception):
    pass


class UserDefinedFieldError(Exception):
    pass


def _encode_for_display(text):
    """
    Encodes strings so they can display as ASCII in a Windows terminal window.
    This function also encodes strings for processing by xml.etree.ElementTree functions.

    Returns an ASCII-encoded version of the text.
    Unicode characters are converted to ASCII placeholders (for example, "?").
    """
    return text.encode('ascii', errors="backslashreplace").decode('utf-8')


def _check_status(server_response, success_code):
    """
    Checks the server response for possible errors.

    'server_response'       the response received from the server
    'success_code'          the expected success code for the response
    Throws an ApiCallError exception if the API call fails.
    """
    if server_response.status_code != success_code:
        parsed_response = ET.fromstring(server_response.text)

        # Obtain the 3 xml tags from the response: error, summary, and detail tags
        error_element = parsed_response.find('t:error', namespaces=xmlns)
        summary_element = parsed_response.find('.//t:summary', namespaces=xmlns)
        detail_element = parsed_response.find('.//t:detail', namespaces=xmlns)

        # Retrieve the error code, summary, and detail if the response contains them
        code = error_element.get('code', 'unknown') if error_element is not None else 'unknown code'
        summary = summary_element.text if summary_element is not None else 'unknown summary'
        detail = detail_element.text if detail_element is not None else 'unknown detail'
        error_message = '{0}: {1} - {2}'.format(code, summary, detail)
        raise ApiCallError(error_message)
    return


def sign_in(server, username, password, site=""):
    """
    Signs in to the server specified with the given credentials

    'server'   specified server address
    'username' is the name (not ID) of the user to sign in as.
               Note that most of the functions in this example require that the user
               have server administrator permissions.
    'password' is the password for the user.
    'site'     is the ID (as a string) of the site on the server to sign in to. The
               default is "", which signs in to the default site.
    Returns the authentication token and the site ID.
    """
    url = server + "/api/{0}/auth/signin".format(VERSION)

    # Builds the request
    xml_request = ET.Element('tsRequest')
    credentials_element = ET.SubElement(xml_request, 'credentials', name=username, password=password)
    ET.SubElement(credentials_element, 'site', contentUrl=site)
    xml_request = ET.tostring(xml_request)

    # Make the request to server
    server_response = requests.post(url, data=xml_request)
    _check_status(server_response, 200)

    # ASCII encode server response to enable displaying to console
    server_response = _encode_for_display(server_response.text)

    # Reads and parses the response
    parsed_response = ET.fromstring(server_response)

    # Gets the auth token and site ID
    token = parsed_response.find('t:credentials', namespaces=xmlns).get('token')
    site_id = parsed_response.find('.//t:site', namespaces=xmlns).get('id')
    user_id = parsed_response.find('.//t:user', namespaces=xmlns).get('id')
    return token, site_id, user_id


def sign_out(server, auth_token):
    """
    Destroys the active session and invalidates authentication token.
    'server'        specified server address
    'auth_token'    authentication token that grants user access to API calls
    """
    url =server + "/api/{0}/auth/signout".format(VERSION)
    server_response = requests.post(url, headers={'x-tableau-auth': auth_token})
    _check_status(server_response, 204)
    return

def error(error):
    bottle.response.content_type = 'application/json'
    return '{"error": "%s"}' % error.body


def authenticate(username, password):
    if username != TAB_USR_NAME or password != TAB_PWD:
        return False
    return True


# @bottle.route('/v2/catalog', method='GET')
# @bottle.auth_basic(authenticate)
# def catalog():
#     api_version = bottle.request.headers.get('X-Broker-Api-Version')
#     if not api_version or float(api_version) < X_BROKER_API_VERSION:
#         bottle.abort(409, "Missing or incompatible %s. Expecting version %0.1f or later" % (
#             X_BROKER_API_VERSION_NAME, X_BROKER_API_VERSION))
#     return {"services": [SMALL_SERVICE, BIG_SERVICE]}


# ========================catalog end================================



@bottle.route('/v2/service_instances/<instance_id>', method='PUT')
@bottle.auth_basic(authenticate)
def provision(instance_id):
    """
    Provision an instance of this service
    for the given org and space

    PUT /v2/service_instances/<instance_id>:
        <instance_id> is provided by the Cloud
          Controller and will be used for future
          requests to bind, unbind and deprovision

    BODY:
        {
          "service_id":        "<service-guid>",
          "plan_id":           "<plan-guid>",
          "organization_guid": "<org-guid>",
          "space_guid":        "<space-guid>"
        }

    return:
        JSON document with details about the
        services offered through this broker
    """
    provision_details = bottle.request.json
    print type(provision_details)
    print provision_details["plan_id"]
    if provision_details is None or provision_details["plan_id"] not in ["big_service","small_service"]:
        bottle.abort(400,"bad request must contain plan_id")
    if provision_details["plan_id"]=="big_service":
        userQuota=BIG_PLAN_VAR["userQuota"]
        storageQuota=BIG_PLAN_VAR["storageQuota"]
    elif provision_details["plan_id"]=="small_service":
        userQuota = SMALL_PLAN_VAR["userQuota"]
        storageQuota = SMALL_PLAN_VAR["storageQuota"]

    print "user quota is "+userQuota
    auth_token, site_id, user_id = sign_in(SERVER, TAB_USR_NAME, TAB_PWD, site="")
    url =  SERVER + "/api/{0}/sites".format(VERSION)
    sid = id_generator(6,"1234567890abcdefghijklmnopqrstuvwxyzQWERTYUIOPASDFGHJKLZXCVBNM")


    new_site_name = sid
    new_content_url = sid
    username = sid
    user_fullname = sid
    userrole = "ContentAndUsers"
    user_site_role = "SiteAdministrator"
    disableSubscriptions = ""
    user_password = sid
    # Builds the request
    xml_request = ET.Element('tsRequest')
    credentials_element = ET.SubElement(xml_request, 'site', name=new_site_name, contentUrl=new_content_url,
                                        adminMode=userrole,
                                        userQuota=userQuota, storageQuota=storageQuota,
                                        disableSubscriptions=disableSubscriptions)
    xml_request = ET.tostring(xml_request)
    # Create site
    server_response = requests.post(url, headers={'x-tableau-auth': auth_token}, data=xml_request)
    xml_response = ET.fromstring(_encode_for_display(server_response.text))


    #add user to site
    sign_out(SERVER, auth_token)
    dest_site=new_content_url
    auth_token, site_id, user_id = sign_in(SERVER, TAB_USR_NAME, TAB_PWD, site=dest_site)
    url= SERVER + "/api/{0}/sites/{1}/users".format(VERSION,site_id)
    xml_request = ET.Element('tsRequest')
    add_to_site = ET.SubElement(xml_request, 'user',name=username, siteRole="SiteAdministrator",
                                         authSetting="ServerDefault")
    xml_request = ET.tostring(xml_request)
    server_response = requests.post(url, headers={'x-tableau-auth': auth_token}, data=xml_request)
  #  _check_status(server_response, 201)

    #update user
    parsed_response = ET.fromstring(server_response.text)
    u_id = parsed_response.find('t:user', namespaces=xmlns).get('id')
    url = SERVER + "/api/{0}/sites/{1}/users/{2}".format(VERSION,site_id,u_id)
    xml_request = ET.Element('tsRequest')
    up_usr = ET.SubElement(xml_request, 'user', fullName=username, email="",
                                         password=user_password,siteRole=user_site_role,authSetting="ServerDefault")
    xml_request = ET.tostring(xml_request)
    # Make the request to server
    server_response = requests.put(url, headers={'x-tableau-auth': auth_token}, data=xml_request)
    client = etcd.Client(host='127.0.0.1', port=2379)
    try:
        client.write('/instants/' + instance_id, new_site_name, prevExist=False)
    except etcd.EtcdAlreadyExist:
        bottle.abort(410, "Already exist")
    print server_response
    print site_id
    _check_status(server_response, 200)
    if _check_status(server_response, 200) is None:
        bottle.response.status = 201
        return {"username": username, "password": user_password}


@bottle.route('/v2/service_instances/<instance_id>', method='DELETE')
@bottle.auth_basic(authenticate)
def deprovision(instance_id):
    client = etcd.Client(host='127.0.0.1', port=2379)
    try:
        dest_site = client.read('/instants/' + instance_id).value
        print dest_site
        auth_token, site_id, user_id = sign_in(SERVER, TAB_USR_NAME, TAB_PWD, site=dest_site)
        # sign_out(SERVER, auth_token)
        url = SERVER + "/api/{0}/sites/{1}".format(VERSION, site_id)
        # auth_token, site_id, user_id = sign_in(SERVER, TAB_USR_NAME, TAB_PWD, site="")
        server_response = requests.delete(url, headers={'x-tableau-auth': auth_token})
        if _check_status(server_response, 204) is None:
            bottle.response.status = 201
            client.delete('/instants/' + instance_id)
            return {"status":"success"}
        else:
            return {"status":"error"}
    except etcd.EtcdAlreadyExist:
        return {"status":"error"}


@bottle.error(401)
@bottle.error(409)
def error(error):
    bottle.response.content_type = 'application/json'
    return '{"error": "%s"}' % error.body


def authenticate(username, password):
    return True


@bottle.route('/v2/catalog', method='GET')
@bottle.auth_basic(authenticate)
def catalog():
    api_version = bottle.request.headers.get('X-Broker-Api-Version')
    if not api_version or float(api_version) < X_BROKER_API_VERSION:
        bottle.abort(409, "Missing or incompatible %s. Expecting version %0.1f or later" % (
        X_BROKER_API_VERSION_NAME, X_BROKER_API_VERSION))
    return {"services": [BIG_SERVICE, SMALL_SERVICE]}

if __name__ == '__main__':
    port = int(os.getenv('PORT', '8080'))
    bottle.run(host='0.0.0.0', port=port, debug=True, reloader=False)
