import json
import mimetypes
import os
import tempfile
import xlrd
import xlwt
from typing import Union
from django.db import connection

from django.http import (
    HttpRequest,
    FileResponse,
    HttpResponseNotFound,
    JsonResponse,
    HttpResponseNotAllowed, HttpResponse,
)
from django.shortcuts import get_object_or_404

from .utils.digital_products import (
    digital_content_url_is_valid,
    increment_download_count,
)

import logging
import traceback

from django.conf import settings
from django.shortcuts import render
from django.views.generic import View

from .models import (
    AssignedProductAttribute,
    AssignedVariantAttribute,
    Attribute,
    AttributeProduct,
    AttributeValue,
    AttributeVariant,
    Category,
    Collection,
    CollectionProduct,
    Product,
    ProductImage,
    ProductType,
    ProductVariant,
    DigitalContentUrl
)
from ..warehouse.models import Stock, Warehouse
from ..account.models import Address
from ..menu.models import MenuItem





def digital_product(request, token: str) -> Union[FileResponse, HttpResponseNotFound]:
    """Return the direct download link to content if given token is still valid."""

    qs = DigitalContentUrl.objects.prefetch_related("line__order__user")
    content_url = get_object_or_404(qs, token=token)  # type: DigitalContentUrl
    if not digital_content_url_is_valid(content_url):
        return HttpResponseNotFound("Url is not valid anymore")

    digital_content = content_url.content
    digital_content.content_file.open()
    opened_file = digital_content.content_file.file
    filename = os.path.basename(digital_content.content_file.name)
    file_expr = 'filename="{}"'.format(filename)

    content_type = mimetypes.guess_type(str(filename))[0]
    response = FileResponse(opened_file)
    response["Content-Length"] = digital_content.content_file.size

    response["Content-Type"] = str(content_type)
    response["Content-Disposition"] = "attachment; {}".format(file_expr)

    increment_download_count(content_url)
    return response


logger = logging.getLogger(__name__)


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
        File = request.FILES.get("file", None)
        try:
            fd, tmp = tempfile.mkstemp()
            with os.fdopen(fd, 'wb') as out:
                out.write(File.read())
            wb = xlrd.open_workbook(tmp)
            table = wb.sheets()[0]
            nrows = table.nrows
            ncols = table.ncols
            for i in range(nrows):
                # print(i)
                if i > 1:
                    self.parse_data(table,i,ncols)
            data = table.row(1)
            # print(type(table.cell_value(1,1)))
        finally:
            os.unlink(tmp)
        return JsonResponse(data="11", status=200, safe=False)
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
        try:
            path = os.path.join(
                settings.PROJECT_ROOT, "saleor", "product", "template.json"
            )
            with open(path) as f:
                db_items = json.load(f)
            # print(table,"+",row,"+",cols)

            assignedProductAttribute = {}
            assignedVariantAttribute = {}
            attribute = db_items["attribute"]
            primary_categories = db_items["primary_categories"]
            secondary_category = db_items["secondary_category"]
            public_attribute = []
            variant_attribute = []
            attributeProduct = db_items["attributeproduct"]
            public_attributeValue = []
            variant_attributeValue = []
            attributeValue = db_items["attributevalue"]
            category_p = db_items["Category_p"]
            category_s = db_items["Category_s"]
            warehouse = {}
            warehouseStock = {}
            collection = {}
            collectionProduct = {}
            product = db_items["product"]
            productImage = db_items["productimage"]
            productImageList = []
            productType = db_items["producttype"]
            productVariant = db_items["productvariant"]
            accountaddress = {}
            for i in range(cols):
                dt = table.cell_value(0,i-1)
                # print(dt)
                if "Category_" in dt:
                    value = table.cell_value(row,i-1)
                    key = dt.split("Category_")[1]
                    category_p[key] = value
                    category_s[key] = value
                elif "primary_categories" in dt:
                    value = table.cell_value(row, i - 1)
                    # key = dt.split("ProductType_")[1]
                    primary_categories["name"] = value
                    category_p['name'] = value
                elif "secondary_category" in dt:
                    value = table.cell_value(row, i - 1)
                    # key = dt.split("ProductType_")[1]
                    secondary_category["name"] = value
                    category_s['name'] = value
                    productType["name"] = value
                elif "ProductType_" in dt:
                    value = table.cell_value(row, i - 1)
                    key = dt.split("ProductType_")[1]
                    productType[key] = value
                elif "Product_" in dt:
                    value = table.cell_value(row, i - 1)
                    key = dt.split("Product_")[1]
                    product[key] = value
                elif "ProductImage" in dt:
                    value = table.cell_value(row, i - 1)
                    # print(value)
                    if value == "":
                        continue
                    else:
                        key = dt.split("_")[1]
                        productImageList.append({key:value})
                        # print(productImageList)
                elif "Public_Attribute_" in dt:
                    # print(public_attribute,"Public_Attribute_")
                    value1 = table.cell_value(1, i - 1)
                    key1 = dt.replace("Public_Attribute_",'')
                    public_attribute.append({key1:value1})
                    value = table.cell_value(row, i - 1)
                    key = dt.replace("Public_Attribute_",'')
                    public_attributeValue.append({key:value})
                elif "Variant_Attribute_" in dt:
                    value1 = table.cell_value(1, i - 1)
                    key1 = dt.replace("Variant_Attribute_",'')
                    variant_attribute.append({key1: value1})
                    value = table.cell_value(row, i - 1)
                    key = dt.replace("Variant_Attribute_",'')
                    variant_attributeValue.append({key: value})
                elif "ProductVariant_" in dt:
                    value = table.cell_value(row, i - 1)
                    key = dt.split("ProductVariant_")[1]
                    productVariant[key] = value
                elif "Warehouse_" in dt:
                    value = table.cell_value(row, i - 1)
                    key = dt.split("Warehouse_")[1]
                    warehouse[key] = value
                elif "WarehouseStock_" in dt:
                    value = table.cell_value(row, i - 1)
                    key = dt.split("WarehouseStock_")[1]
                    warehouseStock[key] = value
                elif "Account_address_" in dt:
                    value = table.cell_value(row, i - 1)
                    key = dt.split("Account_address_")[1]
                    if key == "postal_code":
                        value = int(value)
                        value = str(value)
                        print(value)
                    accountaddress[key] = value

            category_p_pk = self.deal_category_p(category_p)
            category_s_pk = self.deal_category_s(category_s, category_p_pk)
            productType_pk = self.deal_productType(productType)
            product_pk = self.deal_product(product, productType_pk, category_s_pk)
            productVariant_pk = self.deal_productVariant(productVariant, product_pk)
            try:
                for i in range(0, len(productImageList)):
                    # print(i,len(productImageList))
                    self.deal_productImage(productImage, productImageList[i], product_pk)
            except Exception as e:
                print(e)
            public_attributeList = self.deal_attribute(public_attribute, attribute)
            variant_attributeList = self.deal_attribute(variant_attribute, attribute)
            public_attribute_pk_list = self.deal_attributeValue(public_attributeValue, attributeValue, public_attributeList)
            variant_attribute_pk_list = self.deal_attributeValue(variant_attributeValue, attributeValue, variant_attributeList)
            attributeProduct_pk_list = self.deal_attributeProduct(AttributeProduct, public_attributeList, attributeProduct, productType_pk)
            attributeVariant_pk_list = self.deal_attributeProduct(AttributeVariant, variant_attributeList, attributeProduct, productType_pk)
            assignedProductAttribute_pk_list = self.deal_assignedProductAttribute(AssignedProductAttribute, product_pk,attributeProduct_pk_list,assignedProductAttribute)
            # self.deal_assignedProductAttribute_value(public_attribute_pk_list,assignedProductAttribute_pk_list)
            assignedVariantAttribute_pk_list = self.deal_assignedVariantAttribute(productVariant_pk, attributeVariant_pk_list, assignedVariantAttribute)
            address_pk = self.deal_accountaddress(accountaddress)
            warehouse_pk = self.deal_warehouse(warehouse,address_pk)
            self.deal_warehouseStock(warehouseStock, productVariant_pk, warehouse_pk)
            primary_pk = self.deal_primary_categories(category_p_pk, primary_categories)
            print(primary_pk,"000000000000")
            secondary_pk = self.deal_secondary_category(category_s_pk, secondary_category, primary_pk)


        finally:
            pass


    def deal_category_p(self,category):
        category['slug'] = category["name"]
        defaults = category
        name = category["name"]
        # print(name,"name")
        try:
            CategoryObj, _ = Category.objects.update_or_create(name=name, defaults=defaults)
            return CategoryObj.pk
        except Exception as e:
            print(e,"name")

    def deal_category_s(self, category, category_p_pk):
        category['slug'] = category["name"]
        category['parent_id'] = category_p_pk
        defaults = category
        name = category["name"]
        # print(name,"name")
        try:
            CategoryObj, _ = Category.objects.update_or_create(name=name, defaults=defaults)
            return CategoryObj.pk
        except Exception as e:
            print(e,"name")




    def deal_productType(self, productType):
        name = productType["name"]
        productType["slug"] = productType["name"]
        defaults = productType
        Type, _ = ProductType.objects.update_or_create(name=name, defaults=defaults)
        return Type.pk


    def deal_product(self,product, productType_pk, category_pk):
        defaults = product
        name = product["name"]
        description = product["description"]
        defaults['seo_description'] = product["description"]
        defaults['product_type_id'] = productType_pk
        defaults['category_id'] = category_pk
        defaults['slug'] = product["name"]
        # print(defaults,"[[[[[[[[[[[[[[[[[")
        Product_pk, _ = Product.objects.update_or_create(name=name, description=description, defaults=defaults)
        return Product_pk.pk


    def deal_productVariant(self,productVariant,product_pk):
        name = productVariant["name"]
        sku = productVariant["sku"] = int(productVariant["sku"])
        defaults = productVariant
        defaults['product_id'] = product_pk
        print(name,"name",sku,"sku")
        Variant,_ = ProductVariant.objects.update_or_create(name=name, sku=sku, defaults=defaults)
        return Variant.pk


    def deal_productImage(self,productImage,obj,product_pk):
        productImage["image"] = obj["image"]
        defaults = productImage
        defaults['product_id'] = product_pk
        image = productImage["image"]
        product_id = product_pk
        try:
            ProductImage.objects.update_or_create(image=image, product_id=product_id, defaults=defaults)
        except Exception as e:
            print(e,"[[[[[")


    def deal_attribute(self,list,attribute):
        attr_pk_list = []
        # print(777,list,attribute)
        try:
            for i in range(0,len(list)):

                slug = attribute["slug"] = list[i]["slug"]
                attribute["name"] = list[i]["slug"]
                defaults = attribute
                # print(defaults)
                bute,_ = Attribute.objects.update_or_create(slug=slug, name=slug, defaults=defaults)
                attr_pk_list.append(bute.pk)
        except Exception as e:
            print(e,"[[[[[")
        return attr_pk_list


    def deal_attributeValue(self,ValueList,attributeValue,pkList):
        list = []
        for i in range(0,len(ValueList)):
            attributeValue["attribute_id"] = pkList[i]
            slug = attributeValue["slug"] = attributeValue["name"] = ValueList[i]['slug']
            print(slug)
            defaults = attributeValue
            # print(defaults)
            attributevalue,_ = AttributeValue.objects.update_or_create(slug=slug, name=slug, defaults=defaults)
            list.append(attributevalue.pk)
        return list


    def deal_attributeProduct(self, obj, attribute_idList, attributeProduct, product_type_id):
        attributeProduct_pk_list = []
        for i in range(0,len(attribute_idList)):
            attribute_id = attributeProduct["attribute_id"] = attribute_idList[i]
            attributeProduct["product_type_id"] = product_type_id
            defaults = attributeProduct
            Value,_ = obj.objects.update_or_create(attribute_id=attribute_id, product_type_id=product_type_id, defaults=defaults)
            attributeProduct_pk_list.append(Value.pk)
        return attributeProduct_pk_list


    def deal_assignedProductAttribute(self, obj, product_id, assignment_idList, assignedProductAttribute):
        list = []
        for i in range(0,len(assignment_idList)):
            assignedProductAttribute["product_id"] = product_id
            assignment_id = assignedProductAttribute["assignment_id"] = assignment_idList[i]
            defaults = assignedProductAttribute
            Obj,_ = obj.objects.update_or_create(assignment_id=assignment_id, product_id=product_id, defaults=defaults)
            list.append(Obj.pk)
        return list



    def deal_assignedVariantAttribute(self, product_id, assignment_idList, assignedProductAttribute):
        list = []
        for i in range(0,len(assignment_idList)):
            assignedProductAttribute["variant_id"] = product_id
            assignment_id = assignedProductAttribute["assignment_id"] = assignment_idList[i]
            defaults = assignedProductAttribute
            # print(assignment_id,"assignment_id",product_id,"product_id", defaults)
            Obj,_ = AssignedVariantAttribute.objects.update_or_create(assignment_id=assignment_id, variant_id=product_id, defaults=defaults)
            list.append(Obj.pk)
        return list

    def deal_warehouse(self, warehouse,address_pk):
        defaults = warehouse
        name = defaults["name"]
        defaults['address_id'] = address_pk
        # print(name,"name")
        try:
            warehouseObj,_ = Warehouse.objects.update_or_create(name=name, defaults=defaults)
            return warehouseObj.pk
        except Exception as e:
            print(e,"name")

    def deal_warehouseStock(self, warehouseStock, productVariant_pk, warehouse_pk):
        defaults = warehouseStock
        product_variant_id = productVariant_pk
        warehouse_id = warehouse_pk

        try:
            Stock.objects.update_or_create(product_variant_id=product_variant_id, warehouse_id=warehouse_id, defaults=defaults)
        except Exception as e:
            print(e,"name")

    def deal_accountaddress(self,accountaddress):
        defaults = accountaddress
        company_name = defaults['company_name']
        street_address_1 = defaults['street_address_1']
        try:
            address,_ = Address.objects.update_or_create(company_name=company_name, street_address_1=street_address_1, defaults=defaults)
            return address.pk
        except Exception as e:
            print(e,"company_name")

        pass

    def deal_assignedProductAttribute_value(self,public_attribute_pk_list,assignedProductAttribute_pk_list):
        # cursor = connection.cursor
        # for i in range(0,len(public_attribute_pk_list)):
        #     print(assignedProductAttribute_pk_list[i])
        #     print(public_attribute_pk_list[i])
        #     cursor.execute('insert into product_assignedproductattribute_values ("assignedproductattribute_id", "attributevalue_id") VALUES ({}, {});'.format(assignedProductAttribute_pk_list[i],public_attribute_pk_list[i]))
        #     pass
        # result = cursor.fetchall()
        # # 关闭游标
        # cursor.close()
        pass

    def deal_primary_categories(self, category_pk, primary_categories):
        primary_categories["category_id"] = category_pk
        defaults = primary_categories
        name = defaults["name"]
        Obj, _ = MenuItem.objects.update_or_create(name=name, category_id=category_pk, defaults=defaults)
        return Obj.pk


    def deal_secondary_category(self, category_s_pk, secondary_category, category_p_pk):
        secondary_category["category_id"] = category_s_pk
        secondary_category["parent_id"] = category_p_pk
        defaults = secondary_category
        print(defaults)
        name = defaults["name"]
        Obj, _ = MenuItem.objects.update_or_create(name=name, category_id=category_s_pk, defaults=defaults)
        return Obj.pk

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


class download_excel(View):
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
        PrimaryCategories = request.POST.get('primary_categories')
        SecondaryCategory = request.POST.get('secondary_category')
        try:
            output = self.write_data(PrimaryCategories,SecondaryCategory)
        finally:
            pass
        import time
        # response = FileResponse(output)
        response = HttpResponse(output.getvalue())
        output.close()
        response['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response['Content-Disposition'] = 'attachment;filename={0}_{1}.xls'.format(
            'Galasses', int(time.time()))
        response[
            'Access-Control-Expose-Headers'] = 'Content-Disposition'  # （可不选）网关 跨域获取  Content-Disposition

        # response.write(STR)
        # response = HttpResponse(output.getvalue())
        # print(type(output.getvalue()))
        # output.close()
        return response




    def write_data(self, PrimaryCategories,SecondaryCategory):
        L = [
            'primary_categories',
            'secondary_category',
            'Category_tree_id',
            'Category_background_image',
            'ProductType_has_variants',
            'ProductType_weight',
            'Product_name',
            'Product_description',
            'Product_price_amount',
            'Product_minimal_variant_price_amount',
            'Product_weight',
            'ProductImage1_image',
            'ProductImage2_image',
            'ProductImage3_image',
            'ProductImage4_image',
            'ProductImage5_image',
            'ProductImage6_image',
            'ProductImage7_image',
            'ProductVariant_sku',
            'ProductVariant_name',
            'ProductVariant_price_override_amount',
            'ProductVariant_cost_price_amount',
            'Warehouse_name',
            'Warehouse_company_name',
            'Warehouse_email',
            'Warehouse_slug',
            'WarehouseStock_quantity',
            'Account_address_first_name',
            'Account_address_last_name',
            'Account_address_company_name',
            'Account_address_street_address_1',
            'Account_address_street_address_2',
            'Account_address_city',
            'Account_address_postal_code',
            'Account_address_country',
            'Account_address_country_area',
            'Account_address_phone',
            'Account_address_city_area'
        ]

        Public_a = []
        Variant_a = []
        wb = xlwt.Workbook()
        sheet = wb.add_sheet("sheet1", cell_overwrite_ok=True)
        style = xlwt.XFStyle()
        pattern = xlwt.Pattern()
        pattern.pattern = xlwt.Pattern.SOLID_PATTERN
        pattern.pattern_fore_colour = xlwt.Style.colour_map['red']
        style.pattern = pattern
        for i in range(0, len(L)):
            sheet.write(0, i, L[i], style)
            sheet.write(1, i, L[i], style)
            sheet.col(i).width = 256*26
        name = SecondaryCategory
        pro = ProductType.objects.filter(name=name)
        Public_attr = AttributeProduct.objects.filter(product_type=pro[0])
        Variant_attr = AttributeVariant.objects.filter(product_type=pro[0])
        for i in range(0, len(Public_attr)):
            at = Attribute.objects.filter(pk=Public_attr[i].attribute_id)
            Public_a.append(at[0])
        n = len(L)
        # print(Public_a,'Public_a',n)
        for i in range(0,len(Public_a)):
            sheet.write(0, n + i, 'Public_Attribute_slug', style)
            sheet.write(1, n + i, Public_a[i].name, style)
            sheet.col(n - 1 + i).width = 256 * 26
        for j in range(0, len(Variant_attr)):
            bt = Attribute.objects.filter(pk=Variant_attr[j].attribute_id)
            Variant_a.append(bt[0])
        n = len(L) + len(Public_attr)
        for j in range(0,len(Variant_a)):
            sheet.write(0, n + j, 'Variant_Attribute_slug', style)
            sheet.write(1, n + j, Variant_a[j].name, style)
            sheet.col(n - 1 + j).width = 256 * 26

        sheet.write(2, 0, PrimaryCategories)
        sheet.write(2, 1, SecondaryCategory)
        # sheet.write(2, 2, '4')

        import io

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        # wb.save('test.xls')
        return output
