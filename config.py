VERSION = '2.4'
SERVER="http://localhost"
X_BROKER_API_VERSION = 2.3
X_BROKER_API_VERSION_NAME = 'X-Broker-Api-Version'
TAB_BASE_URL = "http://localhost/#/site/"
TAB_USR_NAME = "admin"
TAB_PWD = "adminwfw"
# plans
big_plan = {
    "id": "b001",
    "name": "large",
    "description": "A large dedicated service with a 20g storage quota",
    "free": True
}

small_plan = {
    "id": "b002",
    "name": "small",
    "description": "A small dedicated service with a 10g storage quota ",
    "free": True
}
BIG_PLAN_VAR={
    "userQuota":"20",
    "storageQuota":"4096"
}
SMALL_PLAN_VAR={
    "userQuota":"10",
    "storageQuota":"2048"
}
# services
BIG_SERVICE = {'id': 'big_service', 'name': 'bigService', 'description': 'small quota', 'bindable': True,
               'plans': [big_plan]}

SMALL_SERVICE = {'id': 'small_service', 'name': 'Service', 'description': 'bigquota', 'bindable': True,
                 'plans': [small_plan]}
