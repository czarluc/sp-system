from django.urls import include, path, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import url
from .views import invsys, warehouse, planner, assembly

urlpatterns = [
    path('', invsys.home, name='home'),

    path('warehouse/', include(([
        path('', warehouse.WarehouseHome, name='warehouse_home'),
        path('test/', warehouse.WarehouseTest, name='warehouse_test'),
        #--Check Inventory
        path('CreateItem/', warehouse.CreateItem, name='whse_add_item'),
        path('CreateProd/', warehouse.CreateProdwithItems, name='whse_add_prod'),
        path('CreateProd/SelectItem', warehouse.CreateProd_SelectItem, name='whse_add_prod_selectitem'),

        #--DASHBOARD
        #SAMPLE DASHBOARD
        re_path(r'^Dashboard_get_data/$', warehouse.Dashboard_get_data, name='Dashboard_get_data'),
        re_path(r'^Dashboard_update_data/$', warehouse.Dashboard_update_data, name='Dashboard_update_data'),
        #WHSE UTILIZATION
        re_path(r'^Dashboard_get_whseutil/$', warehouse.Dashboard_get_whseutil, name='Dashboard_get_whseutil'),
        #RECEIVING DASHBOARD
        re_path(r'^Dashboard_get_purchinbound/$', warehouse.Dashboard_get_purchinbound, name='Dashboard_get_purchinbound'),
        re_path(r'^Dashboard_get_purchstatus/$', warehouse.Dashboard_get_purchstatus, name='Dashboard_get_purchstatus'),
        #PUTAWAY DASHBOARD
        re_path(r'^Dashboard_get_putaway/$', warehouse.Dashboard_get_putaway, name='Dashboard_get_putaway'),
        #COMP ISSUANCE DASHBOARD
        re_path(r'^Dashboard_get_compissuance/$', warehouse.Dashboard_get_compissuance, name='Dashboard_get_compissuance'),
        #PART REQUEST DASHBOARD
        re_path(r'^Dashboard_get_partreq/$', warehouse.Dashboard_get_partreq, name='Dashboard_get_partreq'),
        #PART RETURN DASHBOARD
        re_path(r'^Dashboard_get_partret/$', warehouse.Dashboard_get_partret, name='Dashboard_get_partret'),
        #PRODUCT RECEIVE DASHBOARD
        re_path(r'^Dashboard_get_prodrec/$', warehouse.Dashboard_get_prodrec, name='Dashboard_get_prodrec'),
        #PRODUCT SHIP DASHBOARD
        re_path(r'^Dashboard_get_prodship/$', warehouse.Dashboard_get_prodship, name='Dashboard_get_prodship'),
        #---


        #--Receiving-Receive Shipment
        path('InboundShipment/', warehouse.InboundShipment, name='InboundShipment'),
        path('InboundShipment/SelectPO', warehouse.InboundShipment_SelectPONum, name='InboundShipment_SelectPONum'),

        path('ReceiveShipment/SelectPO', warehouse.ReceiveShipment_SelectPONum, name='ReceiveShipment_SelectPONum'),
        path('ReceiveShipment/', warehouse.ReceiveShipment, name='ReceiveShipment'),
        path('ContinueReceiveShipment/', warehouse.ContinueReceiveShipment, name='ContinueReceiveShipment'),
        path('ContinueReceiveShipment/SelectPO', warehouse.ContinueReceiveShipment_SelectPO, name='ContinueReceiveShipment_SelectPO'),
        path('ResolvePO/', warehouse.ResolvePO_Function, name='ResolvePO'),
        path('ResolvePO/SelectPO', warehouse.ResolvePO_SelectPO, name='ResolvePO_SelectPO'),
        path('ViewShipmentSummary/', warehouse.ViewShipmentSummary, name='ViewShipmentSummary'),
        path('UpdatePO/', warehouse.UpdatePO, name='UpdatePO'),
        path('ViewOpenPO/', warehouse.ViewOpenPO, name='ViewOpenPO'),
        path('ViewClosedPO/', warehouse.ViewClosedPO, name='ViewClosedPO'),
        path('ViewResolvedPO/', warehouse.ViewResolvedPO, name='ViewResolvedPO'),
        
        path('ExportReceivedShipment/', warehouse.ExportReceivedShipment, name='ExportReceivedShipment'),
        
        #--Put Away
        path('GeneratePutAwaySchedule/', warehouse.GeneratePutAwaySchedule, name='GeneratePutAwaySchedule'),
        path('GeneratePutAwaySchedule/SelectItem', warehouse.GeneratePutAwaySchedule_SelectItem, name='GeneratePutAwaySchedule_SelectItem'),
        path('GeneratePutAwaySchedule/Autoselect', warehouse.GeneratePutAwaySchedule_Autoselect, name='GeneratePutAwaySchedule_Autoselect'),
        path('FinishPutAway/', warehouse.FinishPutAway, name='FinishPutAway'),
        path('FinishPutAway/SelectPASched', warehouse.FinishPutAway_SelectPASched, name='FinishPutAway_SelectPASched'),
        re_path(r'^FinishPutAway/SelectItem/(?P<pk>[0-9]+)/', warehouse.FinishPutAway_SelectPAItem, name='FinishPutAway_SelectPAItem'),
        path('ViewPutAwaySummary/', warehouse.ViewPutAwaySummary, name='ViewPutAwaySummary'),
        path('ViewOngoingPutAway/', warehouse.ViewOngoingPutAway, name='ViewOngoingPutAway'),
        path('ExportPutAway/', warehouse.ExportPutAway, name='ExportPutAway'),
        
        #--Component Issuance
        path('ViewPendingWO/', warehouse.ViewPendingWO, name='ViewPendingWO'),
        path('GenerateCompIssuanceSchedule/', warehouse.GenerateCompIssuanceSchedule, name='GenerateCompIssuanceSchedule'),
        path('GenerateCompIssuanceSchedule/SelectWO', warehouse.GenerateCompIssuanceSchedule_SelectWO, name='GenerateCompIssuanceSchedule_SelectWO'),
        path('ViewCompIssuanceSummary/', warehouse.ViewCompIssuanceSummary, name='ViewCompIssuanceSummary'),
        path('ViewOngoingCompIssuance/', warehouse.ViewOngoingCompIssuance, name='ViewOngoingCompIssuance'),
        path('ExportCompIssuanceSummary/', warehouse.ExportCompIssuanceSummary, name='ExportCompIssuanceSummary'),
        
        #--Shipping
        path('ReceiveProduct/', warehouse.ReceiveProduct, name='ReceiveProduct'),
        path('ReceiveProduct/SelectProdSched', warehouse.ReceiveProduct_SelectProdSched, name='ReceiveProduct_SelectProdSched'),
        re_path(r'^ReceiveProduct/(?P<pk>[0-9]+)/SelectWhseBin/Select/', warehouse.ReceiveProduct_SelectWhseBin_Select, name='ReceiveProduct_SelectWhseBin_Select'),
        re_path(r'^ReceiveProduct/(?P<pk>[0-9]+)/SelectWhseBin/', warehouse.ReceiveProduct_SelectWhseBin, name='ReceiveProduct_SelectWhseBin'),
        path('ShipProduct/', warehouse.ShipProduct, name='ShipProduct'),
        path('ShipProduct/SelectWONum', warehouse.ShipProduct_SelectWONum, name='ShipProduct_SelectWONum'),
        path('ShipProduct/add_event', warehouse.add_event, name='add_event'),
        path('ViewShippedProducts/', warehouse.ViewShippedProducts, name='ViewShippedProducts'),
        path('ExportShippedProducts/', warehouse.ExportShippedProducts, name='ExportShippedProducts'),
        
        path('ViewReceivedProducts/', warehouse.ViewReceivedProducts, name='ViewReceivedProducts'),
        path('ExportReceivedProducts/', warehouse.ExportReceivedProducts, name='ExportReceivedProducts'),
        

        #--Check Inventory
        path('GenerateCCSchedule/', warehouse.GenerateCCSchedule, name='GenerateCCSchedule'),
        path('FinishCycleCount/', warehouse.FinishCycleCount, name='FinishCycleCount'),
        path('ViewCycleCountSummary/', warehouse.ViewCycleCountSummary, name='ViewCycleCountSummary'),
        
        #--Part Request
        path('GeneratePartRequestSchedule/', warehouse.GeneratePartRequestSchedule, name='GeneratePartRequestSchedule'),
        path('GeneratePartRequestSchedule/SelectItem', warehouse.GeneratePartRequestSchedule_SelectItem, name='GeneratePartRequestSchedule_SelectItem'),
        path('FinishPartReqIssuance/', warehouse.FinishPartReqIssuance, name='FinishPartReqIssuance'),
        path('FinishPartReqIssuance/SelectPartReqSched/', warehouse.FinishPartReqIssuance_SelectPartReqSched, name='FinishPartReqIssuance_SelectPartReqSched'),
        re_path(r'^FinishPartReqIssuance/(?P<pk>[0-9]+)/SelectPartReqItem/', warehouse.FinishPartReqIssuance_SelectItem, name='FinishPartReqIssuance_SelectItem'),
        path('ViewPartReqSummary/', warehouse.ViewPartReqSummary, name='ViewPartReqSummary'),
        path('ViewOngoingPartReqIssuance/', warehouse.ViewOngoingPartReqIssuance, name='ViewOngoingPartReqIssuance'),
        path('ExportPartReqIssuance/', warehouse.ExportPartReqIssuance, name='ExportPartReqIssuance'),
        
        #--Component Return
        path('GenerateCompReturnSchedule/', warehouse.GenerateCompReturnSchedule, name='GenerateCompReturnSchedule'),
        path('GenerateCompReturnSchedule/SelectItem', warehouse.GenerateCompReturnSchedule_SelectItem, name='GenerateCompReturnSchedule_SelectItem'),
        path('FinishCompReturn/', warehouse.FinishCompReturn, name='FinishCompReturn'),
        path('FinishCompReturn/SelectCompReturnSched/', warehouse.FinishCompReturn_SelectCompReturnSched, name='FinishCompReturn_SelectCompReturnSched'),
        re_path(r'^FinishCompReturn/(?P<pk>[0-9]+)/SelectCompReturnItem/', warehouse.FinishCompReturn_SelectItem, name='FinishCompReturn_SelectItem'),
        path('ViewCompReturnSummary/', warehouse.ViewCompReturnSummary, name='ViewCompReturnSummary'),
        path('ViewOngoingCompReturn/', warehouse.ViewOngoingCompReturn, name='ViewOngoingCompReturn'),
        path('ExportCompReturn/', warehouse.ExportCompReturn, name='ExportCompReturn'),
        
        #--Packing
        path('GeneratePackingSchedule/', warehouse.GeneratePackingSchedule, name='GeneratePackingSchedule'),
        path('GeneratePackingSchedule/SelectItem', warehouse.GeneratePackingSchedule_SelectItem, name='GeneratePackingSchedule_SelectItem'),
        path('FinishPacking/', warehouse.FinishPacking, name='FinishPacking'),
        path('FinishPacking/SelectPASched', warehouse.FinishPacking_SelectPASched, name='FinishPacking_SelectPASched'),
        path('ViewPackingSummary/', warehouse.ViewPackingSummary, name='ViewPackingSummary'),
        path('ViewOngoingPacking/', warehouse.ViewOngoingPacking, name='ViewOngoingPacking'),

        #--WHSE UPDATES
        path('ReportDMMR/', warehouse.ReportDMMR, name='ReportDMMR'),
        path('ReportDMMR/SelectItem', warehouse.ReportDMMR_SelectItem, name='ReportDMMR_SelectItem'),
        path('ReportDFMR/', warehouse.ReportDFMR, name='ReportDFMR'),
        path('ReportDFMR/SelectItem', warehouse.ReportDFMR_SelectItem, name='ReportDFMR_SelectItem'),
        path('ReportSysAdj/', warehouse.ReportSysAdj, name='ReportSysAdj'),
        path('ReportSysAdj/SelectItem', warehouse.ReportSysAdj_SelectItem, name='ReportSysAdj_SelectItem'),
        path('DismantleProduct/', warehouse.DismantleProduct, name='DismantleProduct'),
        path('DismantleProduct/SelectProduct', warehouse.DismantleProduct_SelectProduct, name='DismantleProduct_SelectProduct'),
        path('TransferItem/', warehouse.TransferItem, name='TransferItem'),
        path('TransferItem/SelectItem', warehouse.TransferItem_SelectItem, name='TransferItem_SelectItem'),
        
        #--WHSE UPDATES
        path('WarehouseAdjustments/', warehouse.WarehouseAdjustments, name='WarehouseAdjustments'),
        path('ExportWarehouseAdjustments/', warehouse.ExportWarehouseAdjustments, name='ExportWarehouseAdjustments'),
        
        #--WHSE LOCATIONS
        path('CheckInboundLobby/', warehouse.CheckInboundLobby, name='CheckInboundLobby'),
        path('CheckReceivingLobby/', warehouse.CheckReceivingLobby, name='CheckReceivingLobby'),
        path('CheckVDRLobby/', warehouse.CheckVDRLobby, name='CheckVDRLobby'),
        path('CheckWarehouse/', warehouse.CheckWarehouse, name='CheckWarehouse'),
        path('CheckWarehouse_getImage/', warehouse.CheckWarehouse_getImage, name='CheckWarehouse_getImage'),
        path('CheckAssemblyItem/', warehouse.CheckAssemblyItem, name='CheckAssemblyItem'),
        path('CheckAssemblyDiscrepancy/', warehouse.CheckAssemblyDiscrepancy, name='CheckAssemblyDiscrepancy'),
        path('CheckShippingLobby/', warehouse.CheckShippingLobby, name='CheckShippingLobby'),

        #--VIEW INVENTORY
        path('CheckItem/', warehouse.CheckItem, name='CheckItem'),
        path('CheckProduct/', warehouse.CheckProduct, name='CheckProduct'),
        path('ViewItemTransactions/', warehouse.ViewItemTransactions, name='ViewItemTransactions'),
        path('ViewProductTransactions/', warehouse.ViewProductTransactions, name='ViewProductTransactions'),
        

        #--EDIT INVENTORY
        path('EditItem/', warehouse.EditItem, name='EditItem'),
        path('EditProduct/', warehouse.EditProduct, name='EditProduct'),
        path('EditProduct_getparts/', warehouse.EditProduct_getparts, name='EditProduct_getparts'),
        path('EditProduct/SelectItem/', warehouse.EditProduct_SelectItem, name='EditProduct_SelectItem'),
        
        #--CREATE/UPDATE WAREHOUSE BIN
        path('CreateWarehouseBin/', warehouse.CreateWarehouseBin, name='CreateWarehouseBin'),
        path('EditWarehouseBin/', warehouse.EditWarehouseBin, name='EditWarehouseBin'),
        path('EditWarehouseBin_getparts/', warehouse.EditWarehouseBin_getparts, name='EditWarehouseBin_getparts'),
        
        #--BULK CREATE WHSE BIN--
        path('ImportWarehouseBin/', warehouse.ImportWarehouseBin, name='ImportWarehouseBin'),
        
        

    ], 'invsys'), namespace='warehouse')),

    path('planner/', include(([
        path('', planner.PlannerHome, name='planner_home'),
        #--Work Order Creation
        path('CreateWO/', planner.CreateWO, name='CreateWO'),
        path('CreateWO/SelectProduct', planner.CreateWO_SelectProduct, name='CreateWO_SelectProduct'),
        re_path(r'^CreateWO/(?P<pk>[0-9]+)/ScheduleWorkOrder/', planner.CreateWO_ScheduleWO_pk, name='CreateWO_ScheduleWO_pk'),
        path('ScheduleWorkOrder/add_schedule', planner.add_schedule, name='add_schedule'),
        path('ViewWO/', planner.ViewWO, name='ViewWO'),
        re_path(r'^ViewWO_getDetails/$', planner.ViewWO_getDetails, name='ViewWO_getDetails'),
        re_path(r'^ViewWO_getPDF/$', planner.ViewWO_getPDF, name='ViewWO_getPDF'),
        
        path('ExportWO/', planner.ExportWO, name='ExportWO'),
        
        #--Check Parts
        path('CheckPart/', planner.CheckPart, name='CheckPart'),
        path('CheckProduct/', planner.CheckProduct, name='CheckProduct'),

        #COMP ISSUANCE DASHBOARD
        re_path(r'^Dashboard_get_compissuance/$', planner.Dashboard_get_compissuance, name='Dashboard_get_compissuance'),
        
        #ISSUANCE TIMELINESS
        #re_path(r'^Dashboard_get_issuance_time/$', planner.Dashboard_get_issuance_acc, name='Dashboard_get_issuance_acc'),
        #re_path(r'^Dashboard_update_issuance_time/$', planner.Dashboard_update_issuance_acc, name='Dashboard_update_issuance_acc'),
        #WORK ORDER STATUS
        re_path(r'^Dashboard_get_wostatus/$', planner.Dashboard_get_wostatus, name='Dashboard_get_wostatus'),

        #ASSEMBLY PRODUCTIVITY
        re_path(r'^Dashboard_get_assprod/$', planner.Dashboard_get_assprod, name='Dashboard_get_assprod'),
        
    ], 'invsys'), namespace='planner')),

    path('assembly/', include(([
        path('', assembly.AssemblyHome, name='assembly_home'),
        
        #--Component Issuance
        path('FinishCompIssuance/', assembly.FinishCompIssuance, name='FinishCompIssuance'),
        path('FinishCompIssuance/SelectCompIssuanceSched/', assembly.FinishCompIssuance_SelectCompIssuanceSched, name='FinishCompIssuance_SelectCompIssuanceSched'),
        path('ViewCompIssuanceSummary/', assembly.ViewCompIssuanceSummary, name='ViewCompIssuanceSummary'),
        
        #--Assembly Updates
        path('FinishAssembly/', assembly.FinishAssembly, name='FinishAssembly'),
        path('FinishAssembly/SelectProdSched/', assembly.FinishAssembly_SelectProdSched, name='FinishAssembly_SelectProdSched'),
        path('FinishCoupling/', assembly.FinishCoupling, name='FinishCoupling'),
        path('FinishCoupling/SelectProdSched/', assembly.FinishCoupling_SelectProdSched, name='FinishCoupling_SelectProdSched'),
        path('FinishTesting/', assembly.FinishTesting, name='FinishTesting'),
        path('FinishTesting/SelectProdSched/', assembly.FinishTesting_SelectProdSched, name='FinishTesting_SelectProdSched'),
        path('ViewPendingWO/', assembly.ViewPendingWO, name='ViewPendingWO'),
        
        #--Shrinkage Parts
        path('ReportShrinkage/', assembly.ReportShrinkage, name='ReportShrinkage'),
        path('ReportShrinkage/SelectProdSched/', assembly.ReportShrinkage_SelectProdSched, name='ReportShrinkage_SelectProdSched'),
        re_path(r'^ReportShrinkage/(?P<pk>[0-9]+)/SelectItem/', assembly.ReportShrinkage_SelectItem, name='ReportShrinkage_SelectItem'),
        path('ViewShrinkageSummary/', assembly.ViewShrinkageSummary, name='ViewShrinkageSummary'),
        path('ExportShrinkage/', assembly.ExportShrinkage, name='ExportShrinkage'),
        

        #--PartRequestIssuance
        path('FinishPartReqIssuance/', warehouse.FinishPartReqIssuance, name='FinishPartReqIssuance'),
        path('FinishPartReqIssuance/SelectPartReqSched/', warehouse.FinishPartReqIssuance_SelectPartReqSched, name='FinishPartReqIssuance_SelectPartReqSched'),
        path('ViewPartReqSummary/', assembly.ViewPartReqSummary, name='ViewPartReqSummary'),
        

        #-- SIDEBAR GET ASSEMBLYLINE
        re_path(r'^Sidebar_get_assemblyline/$', assembly.Sidebar_get_assemblyline, name='Sidebar_get_assemblyline'),

        #WORK ORDER STATUS
        re_path(r'^Dashboard_get_wostatus/$', assembly.Dashboard_get_wostatus, name='Dashboard_get_wostatus'),

        #ASSEMBLY TIMELINESS
        re_path(r'^Dashboard_get_asstime/$', assembly.Dashboard_get_asstime, name='Dashboard_get_asstime'),
        
        #PRODUCTION VOLUME
        re_path(r'^Dashboard_get_assprod/$', assembly.Dashboard_get_assprod, name='Dashboard_get_assprod'),
        
    ], 'invsys'), namespace='assembly')),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)