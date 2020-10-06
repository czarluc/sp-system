from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm
from django.contrib import admin
from .models import *

class UserAdmin(BaseUserAdmin):
    add_form = UserCreationForm
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'is_bot_flag', 'password1', 'password2')}
        ),
    )


class Purchase_Order_Admin(admin.ModelAdmin):
    readonly_fields = ['purchase_date']

admin.site.register(User, UserAdmin)
admin.site.register(Assembly)
admin.site.register(AssemblyLine)
admin.site.register(Assembly_Line_Assignment)
admin.site.register(Events)


#MASTER TABLES
admin.site.register(Item)
admin.site.register(Uom)
admin.site.register(ItemCat)
admin.site.register(ProdClass)
admin.site.register(Product)
admin.site.register(ProductItemList)
admin.site.register(Assembly_Items)
admin.site.register(Assembly_Discrepancy)
admin.site.register(Warehouse)
admin.site.register(Warehouse_Items)
admin.site.register(Warehouse_Products)
admin.site.register(Work_Order)
admin.site.register(Work_Order_Item_List)


#Receiving
admin.site.register(Purchase_Order)
admin.site.register(Purchase_Order_Item)
admin.site.register(InboundLobby)
admin.site.register(Shipment_PO)
admin.site.register(Shipment)
admin.site.register(Receive_Shipment_Item)
admin.site.register(Shipment_Summary)
admin.site.register(Receiving_Lobby)
admin.site.register(VDR_Lobby)
admin.site.register(Shipment_Transaction)
admin.site.register(RecLobby_Transaction)
admin.site.register(VDRLobby_Transaction)
admin.site.register(VDR_To_Receiving_Transaction)
admin.site.register(ResolvePO)
admin.site.register(ResolvePO_Transaction)



#PUT AWAY
admin.site.register(Put_Away_Schedule)
admin.site.register(Put_Away_Items)
admin.site.register(Put_Away_Summary)
admin.site.register(Put_Away_Finish_Transaction)
admin.site.register(Put_Away_Schedule_Transaction)


#PRODUCTION SCHEDULE
admin.site.register(WO_Production_Schedule)

#WOISSUANCE
admin.site.register(WO_Issuance_Schedule)
admin.site.register(WO_Issuance_Item)
admin.site.register(WO_Issuance_Summary)
admin.site.register(WO_Issuance_RecItem)
admin.site.register(WO_Issuance_List)
admin.site.register(WO_Allocation_Transaction)
admin.site.register(WO_Issuance_Finish_Transaction)
admin.site.register(WO_Issuance_Disc_Transaction)


#WO ASSEMBLY UPDATES
admin.site.register(WO_Assembly)
admin.site.register(WO_Coupling)
admin.site.register(WO_Testing)
admin.site.register(WO_Finished)

#RECEIVE PRODUCT
admin.site.register(RecProduct_Item_Transaction)
admin.site.register(RecProduct_Product_Transaction)
admin.site.register(RecProduct_ProductToShipLobby_Transaction)
admin.site.register(RecProduct_ProductToWhse_Transaction)

#SHIPPING
admin.site.register(Shipping_Lobby)
admin.site.register(Shipping_Outbound)
admin.site.register(Shipping_Outbound_Transaction)

#SHRINKAGE
admin.site.register(Shrinkage_Type)
admin.site.register(Shrinkage_Ass_Report)
admin.site.register(Shrinkage_Ass_Item)
admin.site.register(Shrinkage_Ass_Report_Transaction)
admin.site.register(Shrinkage_Ass_Item_Transaction)

#PART REQUEST
admin.site.register(Request_Schedule)
admin.site.register(Request_Item)
admin.site.register(Request_RecItem)
admin.site.register(Request_Summary)
admin.site.register(Request_Schedule_Transaction)
admin.site.register(Request_Finish_Transaction)
admin.site.register(Request_DiscSummary_Transaction)

#COMPONENT RETURN
admin.site.register(ComponentReturn_Schedule)
admin.site.register(ComponentReturn_Item)
admin.site.register(ComponentReturn_RecItem)
admin.site.register(ComponentReturn_Summary)
admin.site.register(ComponentReturn_Schedule_Transaction)
admin.site.register(ComponentReturn_Summary_Transaction)


#IAF
admin.site.register(IAF_code)
admin.site.register(IAF_whse)
admin.site.register(IAF_operator)
admin.site.register(IAF_Report)
admin.site.register(IAF_Item)
admin.site.register(IAF_Add_Transaction)
admin.site.register(IAF_Subt_Transaction)
admin.site.register(IAF_Prod)
admin.site.register(IAF_Prod_Subt_Transaction)

#DAMAGED MATERIALS
admin.site.register(DMMR_Report)
admin.site.register(DMMR_Item)
admin.site.register(DMMR_Transaction)

#DEFECTIVE MATERIALS
admin.site.register(DFMR_Report)
admin.site.register(DFMR_Item)
admin.site.register(DFMR_Transaction)

#SYSTEM ADJUSTMENT
admin.site.register(SA_Report)
admin.site.register(SA_Item)
admin.site.register(SA_Subt_Transaction)
admin.site.register(SA_Add_Transaction)

#DISMANTLE
admin.site.register(Dismantle_Report)
admin.site.register(Dismantle_Product)
admin.site.register(Dismantle_Item)
admin.site.register(Dismantle_Product_Transaction)
admin.site.register(Dismantle_Item_Transaction)

#TRANSFER
admin.site.register(Transfer_Report)
admin.site.register(Transfer_Item)
admin.site.register(Transfer_Subt_Transaction)
admin.site.register(Transfer_Add_Transaction)