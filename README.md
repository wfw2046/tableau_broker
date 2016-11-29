# tableau_broker is service broker for tableau
## 获取catalog：
    GET /v2/catalog
## 创建instance,会再tableau—server中创建一个site并创建这个site的超管用户，可以用过这个用户登陆server，
    PUT /v2/service_instances/<instance_id>
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
 其中body中的plan_id为必填
## 删除instance提供基础用户名密码验证
    DELETE /v2/service_instances/<instance_id>

