#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import traceback


from django.conf import settings
from django.shortcuts import render
from django.views.generic import View

from django.http import (
    HttpRequest,
    FileResponse,
    HttpResponseNotFound,
    JsonResponse,
    HttpResponseNotAllowed, HttpResponse,
)

from alipay.aop.api.AlipayClientConfig import AlipayClientConfig
from alipay.aop.api.DefaultAlipayClient import DefaultAlipayClient

from alipay.aop.api.domain.AlipayTradeCreateModel import AlipayTradeCreateModel
from alipay.aop.api.request.AlipayTradeCreateRequest import AlipayTradeCreateRequest
from alipay.aop.api.response.AlipayTradeCreateResponse import AlipayTradeCreateResponse

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    filemode='a',)
logger = logging.getLogger('')

class test_upload(View):
    # This class is our implementation of `graphene_django.views.GraphQLView`,
    # which was extended to support the following features:
    # - Playground as default the API explorer (see
    # https://github.com/prisma/graphql-playground)
    # - file upload (https://github.com/lmcgartland/graphene-file-upload)
    # - query batching
    # - CORS

    executor = None
    root_value = None

    def __init__(
        self,  executor=None, root_value=None
    ):
        super().__init__()
        self.executor = executor
        self.root_value = root_value

    def dispatch(self, request, *args, **kwargs):
        # Handle options method the GraphQlView restricts it.
        if request.method == "GET":
            if settings.DEBUG:
                return render("graphql/playground.html")
            return HttpResponseNotAllowed(["OPTIONS", "POST"])

        if request.method == "OPTIONS":
            response = self.options(request, *args, **kwargs)
        elif request.method == "POST":
            # grTest(request,request)
            response = self.handle_query(request)
        else:
            return HttpResponseNotAllowed(["GET", "OPTIONS", "POST"])
        # Add access control headers
        response["Access-Control-Allow-Origin"] = settings.ALLOWED_GRAPHQL_ORIGINS
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response[
            "Access-Control-Allow-Headers"
        ] = "Origin, Content-Type, Accept, Authorization"
        return response

    def handle_query(self, request: HttpRequest):
        pass

        # try:
        #     data = self.parse_body(request)
        # except ValueError:
        #     return JsonResponse(
        #         data={"errors": [self.format_error("Unable to parse query.")]},
        #         status=400,
        #     )
        #
        # if isinstance(data, list):
        #     responses = [self.get_response(request, entry) for entry in data]
        #     result = [response for response, code in responses]
        #     status_code = max((code for response, code in responses), default=200)
        # else:
        #     result, status_code = self.get_response(request, data)
        # return JsonResponse(data=result, status=status_code, safe=False)


    def parse_data(self, table, row, cols):
        pass





    def get_response(self, request: HttpRequest, data: dict):
        execution_result = self.execute_graphql_request(request, data)
        status_code = 200
        if execution_result:
            response = {}
            if execution_result.errors:
                response["errors"] = [
                    self.format_error(e) for e in execution_result.errors
                ]
            if execution_result.invalid:
                status_code = 400
            else:
                response["data"] = execution_result.data
            result = response
        else:
            result = None
        return result, status_code

    def get_root_value(self):
        return self.root_value


def test_alipay():
    # 实例化客户端
    alipay_client_config = AlipayClientConfig()
    alipay_client_config.server_url = 'https://openapi.alipaydev.com/gateway.do'
    alipay_client_config.app_id = '请填写appi_id'
    alipay_client_config.app_private_key = '请填写开发者私钥去头去尾去回车，单行字符串'
    alipay_client_config.alipay_public_key = '请填写支付宝公钥，单行字符串'
    client = DefaultAlipayClient(alipay_client_config, logger)

    # 构造请求参数对象
    model = AlipayTradeCreateModel()
    model.out_trade_no = "20150320010101001";
    model.total_amount = "88.88";
    model.subject = "Iphone6 16G";
    model.buyer_id = "2088102177846880";
    request = AlipayTradeCreateRequest(biz_model=model)

    # 执行API调用
    try:
        response_content = client.execute(request)
    except Exception as e:
        print(traceback.format_exc())

    if not response_content:
        print("failed execute")
    else:
        # 解析响应结果
        response = AlipayTradeCreateResponse()
        response.parse_response_content(response_content)
        # 响应成功的业务处理
        if response.is_success():
            # 如果业务成功，可以通过response属性获取需要的值
            print("get response trade_no:" + response.trade_no)
        # 响应失败的业务处理
        else:
            # 如果业务失败，可以从错误码中可以得知错误情况，具体错误码信息可以查看接口文档
            print(response.code + "," + response.msg + "," + response.sub_code + "," + response.sub_msg)
