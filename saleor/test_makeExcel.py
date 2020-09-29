import xlwt
from .product.models import ProductType, Attribute, AttributeProduct, AttributeVariant

L = [
    'Category_name',
    'Category_slug',
    'Category_tree_id',
    'Category_background_image',
    'ProductType_name',
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
    'WarehouseStock_quantity'
]

def make_excel():
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
    name = 'Glasses'
    pro = ProductType.objects.filter(name=name)
    Public_attr = AttributeProduct.objects.filter(product_type=pro[0])
    Variant_attr = AttributeVariant.objects.filter(product_type=pro[0])
    for i in range(0, len(Public_attr)):
        at = Attribute.objects.filter(pk=Public_attr[i])
        Public_a.append(at[0])
    n = len(L) + len(Public_attr)
    for i in range(0,len(Public_a)):
        sheet.write(0, n - 1 + i, 'Public_Attribute_slug')
        sheet.write(0, n - 1 + i, Public_a[i])
    for j in range(0, len(Variant_attr)):
        bt = Attribute.objects.filter(pk=Variant_attr[j])
        Variant_a.append(bt[0])
    for j in range(0,len(Variant_a)):
        sheet.write(0, n - 1 + j, 'Variant_Attribute_slug')
        sheet.write(0, n - 1 + j, Variant_a[j])

    wb.save('1.xls')













if __name__ == '__main__':
    make_excel()

