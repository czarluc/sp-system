from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Avg, Count
from django.forms import inlineformset_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import (CreateView, DeleteView, DetailView, ListView, UpdateView)
from ..decorators import warehouse_required
from ..forms import *
from ..models import *
from django.views import generic
from django.core.exceptions import ObjectDoesNotExist
import datetime as dt
from django.http import JsonResponse
from itertools import chain
from datetime import date, timedelta, datetime
import json
from django.utils import timezone
import pytz

class WarehouseSignUpView(CreateView):
    model = User
    form_class = WarehouseSignUpForm
    template_name = 'registration/signup_form.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'warehouse'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('warehouse:warehouse_home')

@login_required
@warehouse_required
def WarehouseHome(request):
    return render(request, 'invsys/warehouse/warehouse_home.html')

@login_required
@warehouse_required
def WarehouseTest(request):
    if request.method == 'GET':

        whse_query = Warehouse.objects.all().values(
            'id',
            'bin_location',
            'rack',
            'column',
            'layer',
            'direction',
            'image').order_by('rack','column')

        print(whse_query)

        return render(request, 'invsys/warehouse/whsetest.html', { 'whse_set':whse_query })
    elif request.method == 'POST':
        return redirect('warehouse:warehouse_home')

@login_required
@warehouse_required
def ImportWarehouseBin(request):
    if request.method == 'GET':

        whseformset = WarehouseBinFormset(queryset=Warehouse.objects.none(), prefix='form')

        return render(request, 'invsys/warehouse/CheckInv/ImportWarehouseBin.html', {'whseformset':whseformset})
    
    elif request.method == 'POST':
        whseformset = WarehouseBinFormset(request.POST , request.FILES, prefix='form')

        if whseformset.is_valid():

            counter = 1;
            form_counter = 0;
            for whseform in whseformset:
                if counter < len(whseformset):
                    form_whsebin = whseform.save(commit=False)

                    item_cat = ItemCat.objects.get(item_cat=request.POST.get('form-'+str(form_counter)+'-item_cat'))
                    prod_class = ProdClass.objects.get(prod_class=request.POST.get('form-'+str(form_counter)+'-prod_class'))

                    whsebin = Warehouse.objects.create(
                        bin_location=form_whsebin.rack+form_whsebin.column+"-"+form_whsebin.layer+form_whsebin.direction,
                        rack=form_whsebin.rack,
                        column=form_whsebin.column,
                        layer=form_whsebin.layer,
                        direction=form_whsebin.direction,
                        item_cat=item_cat,
                        prod_class=prod_class)
                    whsebin.full_clean()
                    whsebin.save()

                    #whsebin.save()
                    counter += 1
                    form_counter += 1

        return redirect('home')

#Check Inventory
#--Create Item--
@login_required
@warehouse_required
def CreateItem(request):
    if request.method == 'GET':
        item_form = ItemModelForm(request.GET or None)

        uom_query = Uom.objects.all().values(
            'id',
            'uom')

        item_cat_query = ItemCat.objects.all().exclude(item_cat="Product").values(
            'id',
            'item_cat')

        prod_class_query = ProdClass.objects.all().values(
            'id',
            'prod_class')

        return render(request, 'invsys/warehouse/CheckInv/CreateItem.html', {
            'item_form':item_form,
            'uom_set':uom_query,
            'item_cat_set':item_cat_query,
            'prod_class_set':prod_class_query})

    elif request.method == 'POST' :
        item_form = ItemModelForm(request.POST, request.FILES)

        if item_form.is_valid():
            item_obj = item_form.save(commit=False)
            item_obj.save()           
        else:
            print("item_form")
            print(item_form.errors)

        return redirect('home')
#--Create Product--
@login_required
@warehouse_required
def CreateProdwithItems(request):
    template_name = 'invsys/warehouse/CheckInv/CreateProd.html'
    if request.method == 'GET':
        newproductform = ProductModelForm(request.GET or None)
        formset = ProductItemListFormset(queryset=ProductItemList.objects.none())

        uom_query = Uom.objects.all().values(
            'id',
            'uom')

        prod_class_query = ProdClass.objects.all().exclude(prod_class="None").values(
            'id',
            'prod_class')


        return render(request, template_name, {
            'productform': newproductform,
            'formset': formset,
            'uom_set':uom_query,
            'prod_class_set':prod_class_query})
    elif request.method == 'POST' :
        newproductform = ProductModelForm(request.POST, request.FILES)
        formset = ProductItemListFormset(request.POST)

        if newproductform.is_valid() and formset.is_valid():
            # Save the Product first before its items
            prod = newproductform.save()
            prod.save()

            counter = 1
            for form in formset:
                if counter < len(formset):
                    #Loop through each form in the formset to get each of the items
                    part = form.save(commit=False)
                    part.prod_number = prod
                    part.save()
                    counter += 1
        else:
            print(newproductform.errors)
            print(formset.errors)
        return redirect('home')
@login_required
@warehouse_required
def CreateProd_SelectItem(request):
    itemset = Item.objects.all()
    return render(request, 'invsys/warehouse/CheckInv/CreateProd_SelectItem.html', {'itemset':itemset})


#Receiving
#--Inbound Shipment--
@login_required
@warehouse_required
def InboundShipment(request):
    template_name = 'invsys/warehouse/Receiving/InboundShipment.html'
    if request.method == 'GET':
        shipmentform = ShipmentForm(request.GET or None)
        shipmentpoformset = ShipmentPOFormset(queryset=Shipment_PO.objects.none(), prefix='formpo')
        shipment = Shipment.objects.all()
        if len(shipment) > 0:
            next_shipmentid = Shipment.objects.order_by('-shipment_num').first().shipment_num + 1
        else:
            next_shipmentid = 1
        return render(request, template_name, {'shipmentform': shipmentform,'shipmentpoformset': shipmentpoformset,'next_shipmentid': next_shipmentid})
    
    elif request.method == 'POST' :
        shipmentform = ShipmentForm(request.POST, request.FILES)
        
        now = datetime.now().replace(tzinfo=pytz.utc)

        if shipmentform.is_valid():
            # Save the Product first before its items
            shipment = shipmentform.save(commit=False)
            shipment.save()

            shipmentpoformset = ShipmentPOFormset(request.POST , request.FILES, prefix='formpo')
            print(shipmentpoformset)
            if shipmentpoformset.is_valid():
                print("VALID")
                print(shipmentpoformset)

                counter = 1
                for shipmentpo in shipmentpoformset:
                    #Loop through each form in the formset to get each of the items
                    if counter < len(shipmentpoformset):
                        newshipmentpo = shipmentpo.save(commit=False)
                        newshipmentpo.shipment_num = shipment
                        newshipmentpo.save()
                        counter += 1

                new_inboundlobby = InboundLobby.objects.create(
                    shipment_num=shipment,
                    date_in=now)
                new_inboundlobby.full_clean()
                new_inboundlobby.save()

            else:
                print("shipmentpoformset")
                print(shipmentpoformset.errors)

        else:
            print("shipmentform")
            print(shipmentform.errors)
        return redirect('home')

@login_required
@warehouse_required
def InboundShipment_SelectPONum(request):

    ship_po_query = Shipment_PO.objects.filter( validated=False ).values(
        'po_num__po_number')

    ship_po_list = []
    for ship_po in ship_po_query:
        ship_po_list.append( ship_po.get('po_num__po_number') )

    ponumset = Purchase_Order.objects.filter(cleared=False).exclude(po_number__in=ship_po_list).values(
    'po_number',
    'purchase_date',
    )
    poitemset = Purchase_Order_Item.objects.values(
    'po_number__po_number',
    'item_number__item_number',
    'item_quantity', 
    'item_number__item_desc',
    'item_number__uom__uom', 
    )
    return render(request, 'invsys/warehouse/Receiving/InboundShipment_SelectPONum.html', {'poitemset':poitemset, 'ponumset':ponumset})


#--Receive Shipment--
@login_required
@warehouse_required
def ReceiveShipment(request):
    template_name = 'invsys/warehouse/Receiving/ReceiveShipment.html'
    if request.method == 'GET':
        shipmentitemformset = ReceiveShipmentItemFormset(queryset=Receive_Shipment_Item.objects.none(), prefix='formitem')
        shipmentsummaryformset = ShipmentSummaryFormset(queryset=Shipment_Summary.objects.none(), prefix='formsum')

        return render(request, template_name, {'shipmentitemformset': shipmentitemformset,'shipmentsummaryformset': shipmentsummaryformset})
    elif request.method == 'POST' :
        ship_po = request.POST.get("shipment_po")

        shipment_po_object = Shipment_PO.objects.get(id=ship_po)

        shipmentitemformset = ReceiveShipmentItemFormset(request.POST , request.FILES, prefix='formitem')
        shipmentsummaryformset = ShipmentSummaryFormset(request.POST, request.FILES, prefix='formsum')
        print(shipmentitemformset)
        if shipmentitemformset.is_valid() and shipmentsummaryformset.is_valid():
            
            counter = 1
            for shipmentitem in shipmentitemformset:
                #Loop through each form in the formset to get each of the items
                if counter < len(shipmentitemformset):
                    newshipmentitem = shipmentitem.save(commit=False)
                    newshipmentitem.shipment_po = shipment_po_object
                    newshipmentitem.save()
                    counter += 1

            counter = 1
            for shipmentsummary in shipmentsummaryformset:
                #Loop through each form in the formset to get each of the items
                if counter < len(shipmentsummaryformset):
                    newshipmentsummary = shipmentsummary.save(commit=False)
                    newshipmentsummary.shipment_po = shipment_po_object
                    newshipmentsummary.save()
                    counter += 1

            checkPO(shipment_po_object)
            shipment_po_object.validated = True
            shipment_po_object.save()
            checkRemShippingInbound(shipment_po_object.shipment_num.shipment_num)#Searches for Shipments from ship num to remove to inbound lobby#add clear shipment if all ship_pos are validated
        else:
            print("shipmentitemformset")
            print(shipmentitemformset.errors)
            print("shipmentsummaryformset")
            print(shipmentsummaryformset.errors)

        return redirect('home')

def checkRemShippingInbound(shipment_num):
    ship_po_query = Shipment_PO.objects.filter(shipment_num__shipment_num=shipment_num)

    total_po = 0
    total_val = 0
    for ship_po in ship_po_query:
        total_po += 1
        if ship_po.validated == True:
            total_val += 1

    if total_po == total_val:
        shipment_obj = Shipment.objects.get(shipment_num=shipment_num)
        shipment_obj.cleared = True
        shipment_obj.save()
        DeleteInboundLobby(shipment_num)

def DeleteInboundLobby(shipment_num):
    inbound_lobby_obj = InboundLobby.objects.get(shipment_num__shipment_num=shipment_num)
    inbound_lobby_obj.delete()

def checkPO(shipment_po):
    po_object = Purchase_Order.objects.filter(po_number=shipment_po.po_num)
    po_item_object = Purchase_Order_Item.objects.filter(po_number=shipment_po.po_num)
    shipmentsummary = Shipment_Summary.objects.filter(shipment_po=shipment_po)
    received = 0
    cleared = 0
    issue = 0
    notreceived = 0
    totalreqCount = 0

    for po_item in po_item_object:
        totalreqCount+=1

    notreceived = totalreqCount - received
    for summaries in shipmentsummary:
        received += 1
        if summaries.discrepancy == False: #Summary has no discrepancy
            cleared += 1
        else:
            issue += 1

    for po in po_object:
        if received == totalreqCount:
            if cleared == totalreqCount: #All items in PO are good and no discrepancy
                po.cleared = True
                po.issues = False
                po.save()

                for summaries in shipmentsummary: #add items to the receiving lobby
                    AddtoReceivingLobby(
                        summaries.shipment_po.po_num.po_number,
                        summaries.item_number,
                        summaries.total_received_quantity)
                
                for summaries in shipmentsummary: #add shipment transac
                    AddShipmentTransac(
                        summaries.shipment_po.shipment_num.shipment_num,
                        summaries.item_number,
                        summaries.total_received_quantity)

            else:
                po.cleared = False
                po.issues = True

                for summaries in shipmentsummary: #add items to the vdr lobby
                    AddtoVDRLobby(
                        summaries.shipment_po.po_num.po_number,
                        summaries.item_number,
                        summaries.purchased_quantity,
                        summaries.total_received_quantity)

                for summaries in shipmentsummary: #add shipment transac
                    AddShipmentTransac(
                        summaries.shipment_po.shipment_num.shipment_num,
                        summaries.item_number,
                        summaries.total_received_quantity)
                
        else:
            po.cleared = False
            po.issues = True

            for summaries in shipmentsummary: #add items to the vdr lobby
                AddtoVDRLobby(
                    summaries.shipment_po.po_num.po_number,
                    summaries.item_number,
                    summaries.purchased_quantity,
                    summaries.total_received_quantity)

            #add shipment transac
            for summaries in shipmentsummary: #add shipment transac
                AddShipmentTransac(
                    summaries.shipment_po.shipment_num.shipment_num,
                    summaries.item_number,
                    summaries.total_received_quantity)
        po.save()
def AddtoVDRLobby(refnum,itemnum,itemquan,recquan):
    v = VDR_Lobby.objects.create(
        po_number=refnum, 
        item_number=itemnum,
        purchased_quantity=itemquan,
        received_quantity=recquan,
        status="Waiting for PO Decision")
    v.full_clean()
    v.save()
    RecordVDRLobbyTransac(refnum,itemnum,recquan)
def AddtoReceivingLobby(refnum,itemnum,recquan):
    r = Receiving_Lobby.objects.create(
        reference_number=refnum, 
        item_number=itemnum,
        received_quantity=recquan,
        scheduled_quantity=0,
        status="Waiting for Put Away")
    r.full_clean()
    r.save()
    RecordRecLobbyTransac(refnum,itemnum,recquan)
def RecordRecLobbyTransac(refnum,itemnum,itemquan):
    rtransac = RecLobby_Transaction.objects.create(
        reference_number=refnum,
        transaction_type="Shipment to Receiving Lobby",
        transaction_location="Receiving Lobby",
        item_number=itemnum,
        item_quantity=itemquan)
    rtransac.full_clean()
    rtransac.save()
def RecordVDRLobbyTransac(refnum,itemnum,itemquan):
    vtransac = VDRLobby_Transaction.objects.create(
        reference_number=refnum,
        transaction_type="Shipment to VDR Lobby",
        transaction_location="Receiving Lobby",
        item_number=itemnum,
        item_quantity=itemquan)
    vtransac.full_clean()
    vtransac.save()
def AddShipmentTransac(refnum,itemnum,itemquan):
    s = Shipment_Transaction.objects.create(
        reference_number=refnum,
        transaction_type="Receiving Shipment",
        transaction_location="Receiving Lobby",
        item_number=itemnum,
        item_quantity=itemquan)
    s.full_clean()
    s.save()
def converttoBool(str):
    if str == 'false':
        return False
    else:
        return True
@login_required
@warehouse_required
def ReceiveShipment_SelectPONum(request):
    shipment_query = Shipment.objects.filter(cleared=False).values(
        'shipment_num',
        'dr_num',
        'rr_num',
        'invoice_num',
        'ship_trucking',
        'ship_category',
        'container_num',
        'container_type',
        'awl_bl',
        'notes',
        'date_dr',
        'date_warehouse',)

    shipment_list = []
    for shipment in shipment_query:
        shipment_list.append(shipment.get('shipment_num'))

    shipment_po_query = Shipment_PO.objects.filter(shipment_num__shipment_num__in=shipment_list, validated=False, po_num__cleared=False, po_num__issues=False).values(
        'id',
        'shipment_num__shipment_num',
        'po_num__po_number',
        'po_num__supplier',
        'po_num__purchase_date',)

    ship_list = []
    for shipment in shipment_po_query:
        ship_list.append(shipment.get('shipment_num__shipment_num'))

    shipment_query = Shipment.objects.filter(shipment_num__in=ship_list).values(
        'shipment_num',
        'dr_num',
        'rr_num',
        'invoice_num',
        'ship_trucking',
        'ship_category',
        'container_num',
        'container_type',
        'awl_bl',
        'notes',
        'date_dr',
        'date_warehouse',)

    po_list = []
    for po in shipment_po_query:
        po_list.append(po.get('po_num__po_number'))

    poitemset = Purchase_Order_Item.objects.filter(po_number__in=po_list).values(
    'po_number__po_number',
    'item_number__item_number',
    'item_quantity', 
    'item_number__item_desc',
    'item_number__uom__uom',)

    return render(request, 'invsys/warehouse/Receiving/ReceiveShipment_SelectPONum.html', {
        'shipment_set':shipment_query,
        'shipment_po_set':shipment_po_query,
        'poitemset':poitemset})


#--Continue Receive Shipment--
@login_required
@warehouse_required
def ContinueReceiveShipment(request):
    template_name = 'invsys/warehouse/Receiving/ContinueReceiveShipment.html'
    if request.method == 'GET':
        shipmentform = ShipmentForm_VDR(request.GET or None)
        shipmentitemformset = ReceiveShipmentItem_VDR_Formset(queryset=Receive_Shipment_Item.objects.none(), prefix='formsetitem')
        shipmentsummaryformset = ShipmentSummary_VDR_Formset(queryset=Shipment_Summary.objects.none(), prefix='formsetsum')
        return render(request, template_name, {'shipmentform': shipmentform,'shipmentitemformset': shipmentitemformset,'shipmentsummaryformset': shipmentsummaryformset})
    elif request.method == 'POST' :

        ship_po = request.POST.get("shipment_po")
        shipment_po_object = Shipment_PO.objects.get(id=ship_po)
        po_number_obj = Purchase_Order.objects.get(po_number=shipment_po_object.po_num.po_number)

        shipmentitemformset = ReceiveShipmentItem_VDR_Formset(request.POST , request.FILES, prefix='formsetitem')
        shipmentsummaryformset = ShipmentSummary_VDR_Formset(request.POST, request.FILES, prefix='formsetsum')

        print(shipmentitemformset)
        if shipmentitemformset.is_valid() and shipmentsummaryformset.is_valid():
            #delete past rec ship items
            ship_items_fake = Receive_Shipment_Item.objects.filter(shipment_po__po_num=po_number_obj)

            #delete past rec ship sums
            ship_sum_fake = Shipment_Summary.objects.filter(shipment_po__po_num=po_number_obj)

            for ship_item in ship_items_fake:
                ship_item.delete()

            for ship_sum in ship_sum_fake:
                ship_sum.delete()

            counter = 1
            for shipment_item in shipmentitemformset:
                #Loop through each form in the formset to get each of the items
                if counter < len(shipmentitemformset):
                    newshipmentitem = shipment_item.save(commit=False)
                    newshipmentitem.save()
                    counter += 1
            counter = 1
            for shipment_summary in shipmentsummaryformset:
                #Loop through each form in the formset to get each of the items
                if counter < len(shipmentsummaryformset):
                    newshipmentsummary = shipment_summary.save(commit=False)
                    newshipmentsummary.save()
                    counter += 1
            checkPO_VDR(shipment_po_object)
            shipment_po_object.validated = True
            shipment_po_object.save()
            checkRemShippingInbound(shipment_po_object.shipment_num.shipment_num)#Searches for Shipments from ship num to remove to inbound lobby
        else:
            print("shipmentitemformset.errors")
            print(shipmentitemformset.errors)
            print("shipmentsummaryformset.errors")
            print(shipmentsummaryformset.errors)
        return redirect('home')
def checkPO_VDR(shipment_po):
    po_object = Purchase_Order.objects.filter(po_number=shipment_po.po_num.po_number)
    po_item_object = Purchase_Order_Item.objects.filter(po_number=shipment_po.po_num)
    shipmentsummary = Shipment_Summary.objects.filter(shipment_po__po_num=shipment_po.po_num)
    shipment_items = Receive_Shipment_Item.objects.filter(shipment_po__po_num=shipment_po.po_num)
    vdrlobby_items = VDR_Lobby.objects.filter(po_number=shipment_po.po_num.po_number)
    received = 0
    cleared = 0
    issue = 0
    notreceived = 0
    totalreqCount = 0
    now = datetime.now().replace(tzinfo=pytz.utc)
    date_today = now.strftime("%Y-%m-%d") 
    time_today = now.strftime("%H:%M:%S")

    for po_item in po_item_object:
        totalreqCount+= 1

    notreceived = totalreqCount - received
    for summaries in shipmentsummary:
        received += 1
        if summaries.discrepancy == False: #Summary has no discrepancy
            cleared += 1
        else:
            issue += 1

    for po in po_object:
        if received == totalreqCount:
            if cleared == totalreqCount: #All items in PO are good and no discrepancy
                po.cleared = True
                po.issues = False
                po.save()
                print("PO CLEARED")
                for summaries in shipmentsummary: #add items to the receiving lobby
                    AddtoReceivingLobby(summaries.shipment_po.po_num.po_number, summaries.item_number, summaries.total_received_quantity)
                    AddVDR_to_RecLbby_Transac(summaries.shipment_po.po_num.po_number, summaries.item_number, summaries.total_received_quantity)

                for items in shipment_items: #RECORD ONLY ITEMS RECEIVED TODAY--CHECK IN SHIPMENT ITEMS
                    if items.date_validated.strftime("%Y-%m-%d") == date_today:
                        print("ITEM RECEIVED TODAY")
                        AddShipmentTransac(items.shipment_po.shipment_num.shipment_num, items.item_number, items.item_quantity)
                        if checkExistingVDRLobby(items.shipment_po.po_num.po_number, items.item_number): #Increment Received Parts
                            existing_vdr = getexisting_vdr(items.shipment_po.po_num.po_number, items.item_number)
                            existing_vdr.received_quantity += int(items.item_quantity)
                            existing_vdr.date_received = date_today
                            existing_vdr.time_received = time_today
                            existing_vdr.save()
                            RecordVDRLobbyTransac(items.shipment_po.po_num.po_number,items.item_number,items.item_quantity)
                        else: #Create new VDR Lobby Item
                            pur_quan = getItempur_Quan(items.item_number, items.shipment_po.po_num)
                            AddtoVDRLobby(items.shipment_po.po_num.po_number, items.item_number, pur_quan, items.item_quantity)
                    else:
                        print("NOT ITEM RECEIVED TODAY")
                        AddShipmentTransac(items.shipment_po.shipment_num.shipment_num, items.item_number, 0)
                
                for item in vdrlobby_items:
                    item.status = "Resolved"
                    item.save()

                DeleteVDRLobbyItems()


            else:
                po.cleared = False
                po.issues = True
                po.save()
                print("PO NOT CLEARED")
                for items in shipment_items: #RECORD ONLY ITEMS RECEIVED TODAY--CHECK IN SHIPMENT ITEMS
                    if items.date_validated.strftime("%Y-%m-%d") == date_today:
                        print("ITEM RECEIVED TODAY")
                        AddShipmentTransac(items.shipment_po.shipment_num, items.item_number, items.item_quantity)
                        if checkExistingVDRLobby(items.shipment_po.po_num.po_number, items.item_number): #Increment Received Parts
                            existing_vdr = getexisting_vdr(items.shipment_po.po_num.po_number, items.item_number)
                            existing_vdr.received_quantity += int(items.item_quantity)
                            existing_vdr.date_received = date_today
                            existing_vdr.time_received = time_today
                            existing_vdr.save()
                            RecordVDRLobbyTransac(items.shipment_po.po_num.po_number,items.item_number,items.item_quantity)
                        else: #Create new VDR Lobby Item
                            pur_quan = getItempur_Quan(items.item_number, items.shipment_po.po_num)
                            AddtoVDRLobby(items.shipment_po.po_num.po_number, items.item_number, pur_quan, items.item_quantity)
                    else:
                        print("NOT ITEM RECEIVED TODAY")
                        AddShipmentTransac(items.shipment_po.shipment_num, items.item_number, 0)

        else:
            po.cleared = False
            po.issues = True
            po.save()
            print("PO NOT CLEARED")
            for summaries in shipmentsummary: #add items to the vdr lobby
                AddtoVDRLobby(summaries.shipment_po.po_num.po_number, summaries.item_number, summaries.purchased_quantity, summaries.total_received_quantity)

            #add shipment transac
            for summaries in shipmentsummary: #add shipment transac
                AddShipmentTransac(summaries.shipment_po.shipment_num, summaries.item_number, summaries.total_received_quantity)

        po.save()
def getItempur_Quan(item_num, po_num):
    pur_item = Purchase_Order_Item.objects.get(po_number=po_num,item_number=item_num)
    pur_quan = pur_item.item_quantity
    return pur_quan
def getexisting_vdr(po_num, item_num):
    vdritems_query = VDR_Lobby.objects.get(po_number=po_num, item_number=item_num)
    return vdritems_query
def checkExistingVDRLobby(po_num, item_num):
    vdritems_query = VDR_Lobby.objects.filter(po_number=po_num, item_number=item_num)
    if(not(vdritems_query)): #if vdritems_query is empty
        return False  
    else: #if vdritems_query is not empty
        return True
def DeleteVDRLobbyItems():
    vdrlobby_items = VDR_Lobby.objects.all()
    for item in vdrlobby_items:
        if item.status == "Resolved":
            item.delete()
def AddVDR_to_RecLbby_Transac(refnum,itemnum,itemquan):
    rtransac = VDR_To_Receiving_Transaction.objects.create(
        reference_number=refnum,
        transaction_type="Resolved VDR",
        transaction_location="Receiving Lobby",
        item_number=itemnum,
        item_quantity=itemquan)
    rtransac.full_clean()
    rtransac.save()
@login_required
@warehouse_required
def ContinueReceiveShipment_SelectPO(request):
    template_name = 'invsys/warehouse/Receiving/ContinueReceiveShipment_SelectPO.html'
    shipment_query = Shipment.objects.filter(cleared=False).values(
        'shipment_num',
        'dr_num',
        'rr_num',
        'invoice_num',
        'ship_trucking',
        'ship_category',
        'container_num',
        'container_type',
        'awl_bl',
        'notes',
        'date_dr',
        'date_warehouse',)

    shipment_list = []
    for shipment in shipment_query:
        shipment_list.append(shipment.get('shipment_num'))

    shipment_query = Shipment_PO.objects.filter(shipment_num__in=shipment_list, validated=False, po_num__issues=True).values(
        'shipment_num__shipment_num',
        'shipment_num__dr_num',
        'shipment_num__rr_num',
        'shipment_num__invoice_num',
        'shipment_num__ship_trucking',
        'shipment_num__ship_category',
        'shipment_num__container_num',
        'shipment_num__container_type',
        'shipment_num__awl_bl',
        'shipment_num__notes',
        'shipment_num__date_dr',
        'shipment_num__date_warehouse',)

    shipment_po_query = Shipment_PO.objects.filter(shipment_num__shipment_num__in=shipment_list, validated=False, po_num__issues=True).values(
        'id',
        'shipment_num__shipment_num',
        'po_num__po_number',
        'po_num__supplier',
        'po_num__purchase_date',)

    po_list = []
    for po in shipment_po_query:
        po_list.append(po.get('po_num__po_number'))

    poitemset = Purchase_Order_Item.objects.filter(po_number__in=po_list).values(
        'po_number__po_number',
        'item_number__item_number',
        'item_quantity', 
        'item_number__item_desc',
        'item_number__uom__uom',)

    recship_items_query = Receive_Shipment_Item.objects.filter(shipment_po__po_num__po_number__in=po_list).values(
        'shipment_po__id',
        'shipment_po__po_num__po_number',
        'date_validated',
        'start_time_validation',
        'end_time_validation',
        'validation_time',
        'item_number__item_number',
        'item_quantity',
        'notes',)

    recship_sum_query = Shipment_Summary.objects.filter(shipment_po__po_num__po_number__in=po_list).values(
        'shipment_po__id',
        'shipment_po__po_num__po_number',
        'item_number__item_number',
        'purchased_quantity',
        'total_received_quantity',
        'discrepancy',
        'discrepancy_quantity',
        'issue',
        'received',)

    return render(request, template_name, {
        'shipment_set':shipment_query,
        'shipment_po_set':shipment_po_query,
        'poitemset':poitemset,
        'recship_items_set':recship_items_query,
        'recship_sum_set':recship_sum_query})

#Resolve PO
@login_required
@warehouse_required
def ResolvePO_Function(request):
    template_name = 'invsys/warehouse/Receiving/ResolvePO.html'
    if request.method == 'GET':

        resolvepo_form = ResolvePOForm(request.GET or None)

        return render(request, template_name, {'resolvepo_form': resolvepo_form})
    elif request.method == 'POST' :

        resolvepo_form = ResolvePOForm(request.POST, request.FILES)
        now = datetime.now().replace(tzinfo=pytz.utc)

        print(resolvepo_form)
        if resolvepo_form.is_valid():

            resolve_po = resolvepo_form.save(commit=False)
            resolve_po.date_resolved = now
            resolve_po.save()

            Resolve_CheckPO(resolve_po.po_num)
            DeleteRecLobbyBin_ResolvePO()
        else:
            print("resolvepo_form.errors")
            print(resolvepo_form.errors)
        return redirect('home')


def Resolve_CheckPO(po_number):
    po_object = Purchase_Order.objects.filter(po_number=po_number)
    po_item_object = Purchase_Order_Item.objects.filter(po_number=po_number)
    shipmentsummary = Shipment_Summary.objects.filter(shipment_po__po_num=po_number)
    shipment_items = Receive_Shipment_Item.objects.filter(shipment_po__po_num=po_number)
    vdrlobby_items = VDR_Lobby.objects.filter(po_number=po_number)

    for po in po_object: #All items in PO are now good and regardless with discrepancy
        po.cleared = True
        po.issues = False
        po.save()

        print("PO CLEARED")
        for summaries in shipmentsummary: #add items to the receiving lobby
            AddtoReceivingLobby(summaries.shipment_po.po_num.po_number, summaries.item_number, summaries.total_received_quantity)
            AddVDR_to_RecLbby_Transac(summaries.shipment_po.po_num.po_number, summaries.item_number, summaries.total_received_quantity)
        
        for item in vdrlobby_items:
            item.status = "Resolved"
            item.save()
        DeleteVDRLobbyItems()      

@login_required
@warehouse_required
def ResolvePO_SelectPO(request):
    template_name = 'invsys/warehouse/Receiving/ResolvePO_SelectPO.html'

    po_num_query = Purchase_Order.objects.filter(cleared=False, issues=True).values(
        'po_number',
        'purchase_date',
        'supplier',
        'notes',)

    po_list =[]
    for po_num in po_num_query:
        po_list.append(po_num.get('po_number'))

    shipment_po_query = Shipment_PO.objects.filter(po_num__po_number__in=po_list).values(
        'po_num__po_number',
        'shipment_num__shipment_num',
        'shipment_num__dr_num',
        'shipment_num__rr_num',
        'shipment_num__invoice_num',
        'shipment_num__ship_trucking',
        'shipment_num__ship_category',
        'shipment_num__container_num',
        'shipment_num__container_type',
        'shipment_num__awl_bl',
        'shipment_num__notes',
        'shipment_num__date_dr',
        'shipment_num__date_warehouse',
        'shipment_num__cleared',        
        'validated',)

    ponum_item_list = Purchase_Order_Item.objects.filter(po_number__in=po_list).values(
        'po_number__po_number',
        'item_number__item_number',
        'item_quantity',)
    
    ship_item_list = Receive_Shipment_Item.objects.filter(shipment_po__po_num__po_number__in=po_list).values(
        'shipment_po__shipment_num__shipment_num',
        'shipment_po__po_num__po_number',
        'date_validated',
        'start_time_validation',
        'end_time_validation',
        'validation_time',
        'item_number__item_number',
        'item_number__item_desc',
        'item_quantity',
        'notes',)

    ship_summary_query = Shipment_Summary.objects.filter(shipment_po__po_num__po_number__in=po_list).values(
        'shipment_po__shipment_num__shipment_num',
        'shipment_po__po_num__po_number',
        'item_number__item_number',
        'item_number__item_desc',
        'purchased_quantity',
        'total_received_quantity',
        'discrepancy',
        'discrepancy_quantity',
        'issue',
        'received',)

    ship_sum_list = []
    for ship_sum in ship_summary_query:
        details={}
        po_num = 0
        purch_quan = 0
        tot_rec_quan = 0
        for i in ship_sum:
            if i == 'shipment_po__shipment_num__shipment_num':
                details['ship_num'] = ship_sum[i]
            elif i == 'shipment_po__po_num__po_number':
                po_num = ship_sum[i]
                details['po_num'] = ship_sum[i]
            elif i == 'item_number__item_number':
                details['item_number'] = ship_sum[i]
            elif i == 'item_number__item_desc':
                details['item_desc'] = ship_sum[i]
            elif i == 'purchased_quantity':
                purch_quan = ship_sum[i]
                details['purch_quan'] = ship_sum[i]
            elif i == 'total_received_quantity':
                tot_rec_quan = ship_sum[i]
                details['tot_rec_quan'] = ship_sum[i]
        details['balance'] = int(purch_quan) - int(tot_rec_quan)
        latest_ship_query = Receive_Shipment_Item.objects.filter(shipment_po__po_num__po_number=po_num).order_by('-date_validated').values(
            'date_validated').first()        
        details['date_shipped'] = latest_ship_query.get('date_validated')
        ship_sum_list.append(details)

    return render(request, template_name, {
        'ponum_set':po_num_query,
        'shipment_set':shipment_po_query,
        'ponum_item_set':ponum_item_list,
        'ship_item_set':ship_item_list,
        'ship_summary_set':ship_sum_list})


def DeleteRecLobbyBin_ResolvePO():
    reclobbyset = Receiving_Lobby.objects.order_by('received_quantity')
    for reclobby in reclobbyset:
        if reclobby.received_quantity == 0:
            reclobby.delete()
            
#--View Accomplished Shipments--
@login_required
@warehouse_required
def ViewShipmentSummary(request):
    template_name = 'invsys/warehouse/Receiving/ViewShipmentSummary.html'

    po_query = Purchase_Order.objects.all()

    shipment_po_query = Shipment_PO.objects.all().values(
        'po_num__po_number',
        'shipment_num__shipment_num',
        'shipment_num__dr_num',
        'shipment_num__rr_num',
        'shipment_num__invoice_num',
        'shipment_num__ship_trucking',
        'shipment_num__ship_category',
        'shipment_num__container_num',
        'shipment_num__container_type',
        'shipment_num__awl_bl',
        'shipment_num__notes',
        'shipment_num__date_dr',
        'shipment_num__date_warehouse',
        'shipment_num__cleared',        
        'validated',)

    ponum_item_list = Purchase_Order_Item.objects.all().values(
        'po_number__po_number',
        'item_number__item_number',
        'item_quantity',)
    
    ship_item_list = Receive_Shipment_Item.objects.all().values(
        'shipment_po__shipment_num__shipment_num',
        'shipment_po__po_num__po_number',
        'date_validated',
        'start_time_validation',
        'end_time_validation',
        'validation_time',
        'item_number__item_number',
        'item_number__item_desc',
        'item_quantity',
        'notes',)

    ship_summary_query = Shipment_Summary.objects.all().values(
        'shipment_po__shipment_num__shipment_num',
        'shipment_po__po_num__po_number',
        'item_number__item_number',
        'item_number__item_desc',
        'purchased_quantity',
        'total_received_quantity',
        'discrepancy',
        'discrepancy_quantity',
        'issue',
        'received',)

    ship_sum_list = []
    for ship_sum in ship_summary_query:
        details={}
        po_num = 0
        purch_quan = 0
        tot_rec_quan = 0
        for i in ship_sum:
            if i == 'shipment_po__shipment_num__shipment_num':
                details['ship_num'] = ship_sum[i]
            elif i == 'shipment_po__po_num__po_number':
                po_num = ship_sum[i]
                details['po_num'] = ship_sum[i]
            elif i == 'item_number__item_number':
                details['item_number'] = ship_sum[i]
            elif i == 'item_number__item_desc':
                details['item_desc'] = ship_sum[i]
            elif i == 'purchased_quantity':
                purch_quan = ship_sum[i]
                details['purch_quan'] = ship_sum[i]
            elif i == 'total_received_quantity':
                tot_rec_quan = ship_sum[i]
                details['tot_rec_quan'] = ship_sum[i]
        details['balance'] = int(purch_quan) - int(tot_rec_quan)
        latest_ship_query = Receive_Shipment_Item.objects.filter(shipment_po__po_num__po_number=po_num).order_by('-date_validated').values(
            'date_validated').first()        
        details['date_shipped'] = latest_ship_query.get('date_validated')
        ship_sum_list.append(details)


    return render(request, template_name, 
        {'ponum_set':po_query,
        'shipment_set':shipment_po_query, 
        'ponum_item_set':ponum_item_list, 
        'ship_item_set':ship_item_list,
        'ship_summary_set':ship_sum_list})



#Put Away
#--Generate Put Away Schedule--
@login_required
@warehouse_required
def GeneratePutAwaySchedule(request):
    template_name = 'invsys/warehouse/PutAway/GeneratePutAwaySchedule.html'
    if request.method == 'GET':
        putawayscheduleform = PutAwayScheduleForm(request.GET or None)
        #Populating Initial Forms
        paschedules = Put_Away_Schedule.objects.all()
        if len(paschedules) > 0:
            next_scheduleid = Put_Away_Schedule.objects.order_by('-schedule_num').first().schedule_num + 1
        else:
            next_scheduleid = 1
        putawayitemsform = PutAwayItemFormset(queryset=Put_Away_Items.objects.none())
        return render(request, template_name, {'scheduleform': putawayscheduleform,'itemformset': putawayitemsform, 'scheduleid':next_scheduleid})
    elif request.method == 'POST' :
        scheduleform = PutAwayScheduleForm(request.POST)
        itemformset = PutAwayItemFormset(request.POST, request.FILES)
        if scheduleform.is_valid() and itemformset.is_valid():
            # Save the Schedule first before its items
            paschedule = scheduleform.save()
            paschedule.save()
            counter = 1
            for form in itemformset:
                if counter < len(itemformset):
                    #Loop through each form in the formset to get each of the items
                    paitem = form.save(commit=False)
                    paitem.schedule_num = paschedule
                    paitem.save()
                    recordPAChanges(paitem.id, paitem.item_num, paitem.required_quantity, paitem.reference_number, paitem.bin_location)
                    counter += 1
            
            return redirect('home')
        return redirect('home')
def recordPAChanges(refnum, itemnum, itemquan, pastrefnum, binlocation):
    RecordPASchedTransac(refnum, itemnum, itemquan) #Record Schedule Transactions
    UpdateReceivingLobbyPASched(itemnum, itemquan, pastrefnum) #Update Receiving Lobby 
    UpdateWhseItemPASched(pastrefnum, itemnum, itemquan, binlocation) #Update Whse Bin  
def RecordPASchedTransac(refnum,itemnum,itemquan):
    paschedtransac = Put_Away_Schedule_Transaction.objects.create(
        reference_number=refnum,
        transaction_type="Scheduled for Put Away",
        transaction_location="Receiving Lobby",
        item_number=itemnum,
        item_quantity=itemquan)
    paschedtransac.full_clean()
    paschedtransac.save()
def UpdateReceivingLobbyPASched(itemnum, itemquan, pastrefnum):
    recitem = Receiving_Lobby.objects.get(reference_number=pastrefnum, item_number=itemnum)
    recitem.scheduled_quantity += itemquan
    if recitem.received_quantity == recitem.scheduled_quantity:
        recitem.status = "All parts scheduled for PutAway"
    else:
        recitem.status = "Some parts scheduled for PutAway"
    recitem.save()
def UpdateWhseItemPASched(refnum, itemnum, itemquan, binlocation):
    paschedwhseitem = Warehouse_Items.objects.create(
        bin_location=binlocation,
        item_number=itemnum,
        quantity=itemquan,
        status="Waiting for Put Away",
        reference_number=refnum)
    paschedwhseitem.full_clean()
    paschedwhseitem.save()
@login_required
@warehouse_required
def GeneratePutAwaySchedule_SelectItem(request):
    recstatus = []
    recstatus.append("")
    recstatus.append("None")
    recstatus.append("Some parts scheduled for PutAway")
    recstatus.append("Waiting for Put Away")
    reclobbyitemset = Receiving_Lobby.objects.filter(status__in=recstatus).values(
        'id',
        'reference_number',
        'item_number__item_number',
        'item_number__item_cat__item_cat',
        'item_number__prod_class__prod_class',
        'received_quantity',
        'scheduled_quantity',)
    reclobbyitems = Receiving_Lobby.objects.all()
    reclobbyitemcat = []
    reclobbyitemcat = getRecLobbyItemcat(reclobbyitemcat,reclobbyitems)
    reclobbyitemclass = []
    reclobbyitemclass = getRecLobbyItemclass(reclobbyitemclass,reclobbyitems)
    whsebinlocationset = Warehouse.objects.filter(item_cat__in=reclobbyitemcat, prod_class__in=reclobbyitemclass).values(
        'id',
        'bin_location',
        'item_cat__item_cat',
        'prod_class__prod_class',)
    whsebinlocations = Warehouse.objects.filter(item_cat__in=reclobbyitemcat, prod_class__in=reclobbyitemclass)
    whseitems = Warehouse_Items.objects.filter(bin_location__in=whsebinlocations,status="In Stock").values(
        'id',
        'bin_location__bin_location',
        'item_number__item_number',
        'quantity',)
    return render(request, 'invsys/warehouse/PutAway/GeneratePutAwaySchedule_SelectItem.html', 
        {'reclobbyitems':reclobbyitemset, 
        'whsebinset':whsebinlocationset, 
        'whseitemset':whseitems})  
def getRecLobbyItemcat(reclobbyitemcat,reclobbyitems):
    for item in reclobbyitems:
        reclobbyitemcat.append(item.item_number.item_cat)
    return reclobbyitemcat
def getRecLobbyItemclass(reclobbyitemclass,reclobbyitems):
    for item in reclobbyitems:
        reclobbyitemclass.append(item.item_number.prod_class)
    return reclobbyitemclass

#--GeneratePutAwaySchedule_Autoselect--
@login_required
@warehouse_required
def GeneratePutAwaySchedule_Autoselect(request):

    item_sched_list = json.loads(request.POST.get('item_sched_list[]'))
    done_item_sched_list = [] #item_num, sched_quan, bin_id, bin_loc, ref_num

    for item_sched in item_sched_list:
        item_obj = Item.objects.get(item_number=item_sched[1])
        sched_details = auto_putaway_sched( item_obj, item_sched[2], item_sched[0] )
        done_item_sched_list.append( sched_details )

    data = { 'msg':"FUCK IT WORKED!",
        'done_item_sched_list':done_item_sched_list }
    return JsonResponse(data)

def auto_putaway_sched( item_obj, req_quan, ref_num ):
    sched_details = []
    #get list of whse avail objects based on item category and prod class
    whse_query = Warehouse.objects.filter(item_cat=item_obj.item_cat,prod_class=item_obj.prod_class).order_by('bin_location').values(
        'id',
        'bin_location')

    #do something to add more features like least whse items, and etc.

    bin_id = ''
    bin_loc = ''
    counter = 0
    for whse in whse_query:
        if counter == 0:
            bin_id = whse.get('id')
            bin_loc = whse.get('bin_location')
            break
        counter += 1

    sched_details.append(item_obj.item_number)
    sched_details.append(req_quan)
    sched_details.append(bin_id)
    sched_details.append(bin_loc)
    sched_details.append(ref_num)

    return sched_details

#--Finish Put Away--
@login_required
@warehouse_required
def FinishPutAway(request):
    template_name = 'invsys/warehouse/PutAway/FinishPutAway.html'
    if request.method == 'GET':
        
        pasummaryformset = PutAwaySummaryFormset(queryset=Put_Away_Summary.objects.none(), prefix='formsetsum')
        
        return render(request, template_name, {
            'pasummaryformset': pasummaryformset})

    elif request.method == 'POST' :
        sched_num = request.POST.get("sched_num",'')
        pa_sched = Put_Away_Schedule.objects.get(schedule_num=sched_num)

        pasummaryformset = PutAwaySummaryFormset(request.POST , request.FILES, prefix='formsetsum')

        if pasummaryformset.is_valid():

            now = datetime.now().replace(tzinfo=pytz.utc)
            
            counter = 1
            for pasum_form in pasummaryformset:
                if counter < len(pasummaryformset):
                    pa_sum = pasum_form.save(commit=False)
                    pa_sum.schedule_num = pa_sched
                    pa_sum.date_scheduled = pa_sched.date_scheduled
                    pa_sum.date_stored = now
                    pa_sum.save()
                    counter += 1

            pasum_query = Put_Away_Summary.objects.filter(schedule_num=pa_sched)
            for pa_sum in pasum_query:

                try: #Check if the pa_sum exist in the pa_item
                    pa_item = Put_Away_Items.objects.get(schedule_num=pa_sched, item_num=pa_sum.item_num, bin_location=pa_sum.bin_location, reference_number=pa_sum.reference_number)
                    if (pa_sum.required_quantity >= pa_sum.stored_quantity):
                        print("Stored")
                        pa_item.stored = True
                        pa_item.save()
                        RecordPAFinishTransactions(pa_item.reference_number, pa_sum.item_num, pa_sum.stored_quantity,pa_sum.bin_location)
                        UpdateWhseItemPAFinish(pa_item.reference_number, pa_sum.bin_location, pa_sum.item_num, pa_sum.stored_quantity)
                        UpdateReceivingLobbyPAFinish(pa_item.reference_number, pa_sum.item_num, pa_sum.stored_quantity)

                except pa_item.DoesNotExist: #There are no item in pa_item
                    pass                
                        
            paitems = Put_Away_Items.objects.filter(schedule_num=pa_sched)

            itemcounter = 0
            clearedcounter = 0

            for paitem in paitems:
                itemcounter += 1
                if paitem.stored == True:
                    clearedcounter += 1

            if itemcounter == clearedcounter:
                pa_sched.cleared = True
                pa_sched.save()
        else:
            print("pasummaryformset.errors")
            print(pasummaryformset.errors)
    return redirect('home')

@login_required
@warehouse_required
def FinishPutAway_SelectPASched(request):
    pascheduleset = Put_Away_Schedule.objects.filter(cleared=False).values( #Query for PA schedules
        'schedule_num',
        'date_scheduled',
        'notes',)

    paschedules = Put_Away_Schedule.objects.filter(cleared=False) #Queries for PA Schedule items
    paitems = Put_Away_Items.objects.filter(schedule_num__in=paschedules).values(
        'schedule_num',
        'item_num__item_number',
        'required_quantity',
        'bin_location__id',
        'bin_location__bin_location',
        'reference_number',
        'stored',)

    return render(request, 'invsys/warehouse/PutAway/FinishPutAway_SelectPASched.html', 
        {'pascheduleset':pascheduleset, 
        'paitems':paitems})
@login_required
@warehouse_required
def FinishPutAway_SelectPAItem(request, pk=None):
    paitemset = Put_Away_Items.objects.filter(schedule_num=pk,stored=False).values(
    'item_num__item_number',
    'required_quantity', 
    'bin_location__id',
    'bin_location__bin_location',
    'reference_number',
    'stored',)
    return render(request, 'invsys/warehouse/PutAway/FinishPutAway_SelectPAItem.html', 
        {'paitemset':paitemset})
def RecordPAFinishTransactions(refnum,itemnum,itemquan,binlocation):
    paschedtransac = Put_Away_Finish_Transaction.objects.create(
        reference_number=refnum,
        transaction_type="Finished Item Put Away",
        transaction_location=binlocation,
        item_number=itemnum,
        item_quantity=itemquan)
    paschedtransac.full_clean()
    paschedtransac.save()

def UpdateWhseItemPAFinish(refnum,binlocation,itemnum,itemquan):
    status = []
    status.append("In Stock")
    status.append("Waiting for Put Away")
    whseitems = Warehouse_Items.objects.filter(bin_location=binlocation,item_number=itemnum,status__in=status)

    totalquan = 0
    for item in whseitems:
        totalquan += item.quantity

    pawhseitem = Warehouse_Items.objects.get(bin_location=binlocation,item_number=itemnum,status="Waiting for Put Away",reference_number=refnum)
    
    try: #There are existing items in the warehouse
        finalwhseitem = Warehouse_Items.objects.get(bin_location=binlocation,item_number=itemnum,status="In Stock")
        finalwhseitem.quantity = totalquan
        finalwhseitem.save()
    except Warehouse_Items.DoesNotExist: #There are no items in the warehouse
        whseitem = Warehouse_Items.objects.create(
        bin_location=binlocation,
        item_number=itemnum,
        quantity=itemquan,
        status="In Stock",
        reference_number="None")
        whseitem.full_clean()
        whseitem.save()
    pawhseitem.delete()

def UpdateReceivingLobbyPAFinish(pastrefnum, itemnum, itemquan):
    reclobbyitem = Receiving_Lobby.objects.get(reference_number=pastrefnum, item_number=itemnum)

    tot_req = reclobbyitem.received_quantity

    putawaysummary_query = Put_Away_Summary.objects.filter(reference_number=pastrefnum, item_num=itemnum).values('stored_quantity')

    tot_stored = 0;
    for putawayitem in putawaysummary_query:
        tot_stored += putawayitem.get('stored_quantity')

    if tot_req == tot_stored:
        reclobbyitem.delete()

#--View Put Away Schedule--
@login_required
@warehouse_required
def ViewPutAwaySummary(request):
    pa_sched_list = Put_Away_Schedule.objects.filter().values(
        'schedule_num',
        'date_scheduled',
        'notes',
        'cleared',
        'issues',)
    pa_sum_list = Put_Away_Summary.objects.filter().values(
        'schedule_num__schedule_num',
        'item_num__item_number',
        'required_quantity',
        'stored_quantity',
        'bin_location__bin_location',
        'discrepancy',
        'discrepancy_quantity',
        'status',
        'date_scheduled',
        'date_stored',
        'reference_number',)
    return render(request, 'invsys/warehouse/PutAway/ViewPutAwaySummary.html', 
        {'pasched_set':pa_sched_list,
        'pasum_set':pa_sum_list})

#Component Issuance
#--View Pending WO--
@login_required
@warehouse_required
def ViewPendingWO(request):
    prod_sched_list = WO_Production_Schedule.objects.filter(scheduled=False).values(
        'id',
        'work_order_number__work_order_number',
        'quantity',
        'date_required',
        'status',)
    wo_filter = []
    for prodsched in prod_sched_list:
        wo_filter.append(prodsched.get("work_order_number__work_order_number"))
    prod_list = Work_Order.objects.filter(work_order_number__in=wo_filter).values(
        'work_order_number',
        'prod_number__prod_number',
        'prod_number__prod_desc',
        'prod_number__uom',
        'prod_number__prod_type',
        'prod_number__prod_class',
        'prod_number__barcode',
        'prod_number__price',)
    wo_item_list = Work_Order_Item_List.objects.filter(work_order_number__in=wo_filter).values(
        'work_order_number__work_order_number',
        'item_number__item_number',
        'item_quantity',)
    return render(request, 'invsys/warehouse/CompIssuance/ViewPendingWO.html', 
        {'prod_sched_set':prod_sched_list, 
        'prod_set':prod_list,
        'wo_item_set':wo_item_list,})

#--Generate Component Issuance Schedule--
@login_required
@warehouse_required
def GenerateCompIssuanceSchedule(request):
    template_name = 'invsys/warehouse/CompIssuance/GenerateCompIssuanceSchedule.html'
    if request.method == 'GET':
        compissuescheduleform = CompIssuanceScheduleform(request.GET or None)
        #Populating Initial Forms
        compissueschedules = WO_Issuance_Schedule.objects.all()
        if len(compissueschedules) > 0:
            next_scheduleid = WO_Issuance_Schedule.objects.order_by('-schedule_num').first().schedule_num + 1
        else:
            next_scheduleid = 1
        woissuancelistformset = WO_Issuance_ListFormset(queryset=WO_Issuance_List.objects.none())
        return render(request, template_name, {'scheduleform': compissuescheduleform,'woissueformset': woissuancelistformset, 'scheduleid':next_scheduleid})
    
    elif request.method == 'POST' :
        scheduleform = CompIssuanceScheduleform(request.POST)
        print(scheduleform)
        itemformset = WO_Issuance_ListFormset(request.POST, request.FILES)
        print(itemformset)
        if scheduleform.is_valid() and itemformset.is_valid():
            # Save the Schedule first before its items compissuesched
            compissuesched = scheduleform.save(commit=False)
            compissuesched.save()
            counter = 1
            for form in itemformset:
                if counter < len(itemformset):
                    #Loop through each form in the formset to get each of the items
                    compissueitem = form.save(commit=False)
                    compissueitem.schedule_num = compissuesched
                    prodsched = compissueitem.prod_sched
                    AddWOIssueItems(prodsched, compissuesched)
                    prodsched.scheduled = True
                    prodsched.status = "Waiting for Issuance"
                    prodsched.save()
                    compissueitem.save()
                    counter += 1           
            DeleteWhseItemBin()
            return redirect('home')
        return redirect('home')
def AddWOIssueItems(prodsched, compissuesched):
    woref = prodsched.work_order_number
    woquan = prodsched.quantity

    woitems = Work_Order_Item_List.objects.filter(work_order_number=woref)

    TotalAllocatedBinQuan = 0
    for woitem in woitems:

        itemnum = woitem.item_number
        itemquan = woitem.item_quantity
        totalreq_quan = int(woquan) * int(itemquan)
        totalalloc = 0

        AllocatetoWhseBin_CompIssueSched(itemnum, totalreq_quan, totalalloc, prodsched, woref, compissuesched)
        TotalAllocatedBinQuan = 0
def AllocatetoWhseBin_CompIssueSched(itemnum, totalreq_quan, totalalloc, prodsched, woref, compissuesched):
    whseitemset = Warehouse_Items.objects.filter(status="Allocated for Work Order", item_number=itemnum, bin_location__item_cat=itemnum.item_cat, bin_location__prod_class=itemnum.prod_class, reference_number=woref).order_by('quantity')
    for whsebin in whseitemset:
        if not totalreq_quan == totalalloc:
            totalalloc, whsebin = SubtractBinStock(whsebin, totalreq_quan, totalalloc, itemnum, woref, prodsched, compissuesched)
            whsebin.save()
def SubtractBinStock(whsebin, totalreq, totalalloc, itemnum, wo_num, prodsched, compissuesched):
    allocatedbinquan = 0
    binStock = 0
    remainingalloc = 0
    binStock = whsebin.quantity
    remainingalloc = int(totalreq) - totalalloc

    if remainingalloc < binStock: #Bin stock fulfilled required allocation
        allocatedbinquan = remainingalloc
        whsebin.quantity -= remainingalloc
    elif remainingalloc == binStock: #Bin stock fulfilled required allocation
        allocatedbinquan = remainingalloc
        whsebin.quantity = 0
    elif remainingalloc > binStock: #Bin stock did not fulfill required allocation
        allocatedbinquan = binStock
        whsebin.quantity = 0

    AddtoCompIssuanceItemSchedList(whsebin.bin_location, itemnum, allocatedbinquan, prodsched, compissuesched)
    CreateWhseItemBin_CompIssueSched(whsebin.bin_location, itemnum, allocatedbinquan, prodsched)
    AddAllocationTransac_CompIssueSched(prodsched, whsebin.bin_location, itemnum, allocatedbinquan)
    totalalloc += allocatedbinquan
    return totalalloc, whsebin
def AddtoCompIssuanceItemSchedList(binloc, itemnum, allocquan, prodsched, compissuesched):
    woissueitem = WO_Issuance_Item.objects.create(
        schedule_num=compissuesched,
        prod_sched=prodsched,
        item_num=itemnum,
        item_quantity=allocquan,
        bin_location=binloc,
        )
    woissueitem.full_clean()
    woissueitem.save()
def CreateWhseItemBin_CompIssueSched(binloc, itemnum, allocquan, prodsched):
    whseitemBin = Warehouse_Items.objects.create(
        bin_location=binloc,
        item_number=itemnum,
        quantity=allocquan,
        status="For Component Issuance",
        reference_number=prodsched)
    whseitemBin.full_clean()
    whseitemBin.save()
def AddAllocationTransac_CompIssueSched(refnum,binlocation,itemnum,itemquan):
    compalloctransac = WO_Allocation_Transaction.objects.create(
        reference_number=refnum,
        transaction_type="Work Order Item Allocation",
        transaction_location=binlocation,
        item_number=itemnum,
        item_quantity=itemquan)
    compalloctransac.full_clean()
    compalloctransac.save()
def DeleteWhseItemBin():
    whseitemset = Warehouse_Items.objects.order_by('quantity')
    for whsebin in whseitemset:
        if whsebin.quantity == 0:
            whsebin.delete()

@login_required
@warehouse_required
def GenerateCompIssuanceSchedule_SelectWO(request):
    template_name = 'invsys/warehouse/CompIssuance/GenerateCompIssuanceSchedule_SelectWO.html'

    woprodsched = WO_Production_Schedule.objects.filter(scheduled=False, status="Waiting for Schedule").values(
        'id',
        'work_order_number__work_order_number',
        'work_order_number__prod_number__prod_number',
        'quantity',
        'work_order_number__prod_number__prod_class__prod_class',
        'date_required',)
    
    wos = WO_Production_Schedule.objects.filter(scheduled=False, status="Waiting for Schedule")
    workorders = []
    for wo in wos:
        workorders.append(wo.work_order_number)
    woitemset = Work_Order_Item_List.objects.filter(work_order_number__in=workorders).values(
        'work_order_number__work_order_number',
        'item_number__item_number',
        'item_quantity',)
   
    return render(request, template_name, {'prodschedset':woprodsched,'woitemset':woitemset,})  

#--View Accomplished Component Issuance Schedule--
@login_required
@warehouse_required
def ViewCompIssuanceSummary(request):
    issuance_sched_list = WO_Issuance_Schedule.objects.filter().values(
        'schedule_num',
        'date_scheduled',
        'notes',
        'cleared',
        'issues',)
    issuance_sum_list = WO_Issuance_Summary.objects.filter().values(
        'schedule_num__schedule_num',
        'prod_sched__id',
        'prod_sched__work_order_number',
        'item_num__item_number',
        'totalreq_quan',
        'totalrec_quan',
        'discrepancy',
        'discrepancy_quantity',
        'status',
        'date_received',)
    return render(request, 'invsys/warehouse/CompIssuance/ViewCompIssuanceSummary.html', 
        {'issuance_sched_set':issuance_sched_list,
        'issuance_sum_set':issuance_sum_list})

#--Export Comp Issuance Summary--
@login_required
@warehouse_required
def ExportCompIssuanceSummary(request):

    issuance_sum_list = WO_Issuance_Summary.objects.filter(schedule_num__cleared=True).values(
        'schedule_num__schedule_num',
        'schedule_num__date_scheduled',
        'schedule_num__notes',
        'schedule_num__cleared',
        'schedule_num__issues',

        'prod_sched__id',
        'prod_sched__work_order_number',
        'item_num__item_number',
        'totalreq_quan',
        'totalrec_quan',
        'discrepancy',
        'discrepancy_quantity',
        'status',
        'date_received',)

    return render(request, 'invsys/warehouse/CompIssuance/ExportCompIssuanceSummary.html', 
        {'issuance_sum_set':issuance_sum_list})

#Shipping
#--Receive Product--
@login_required
@warehouse_required
def ReceiveProduct(request):
    template_name = 'invsys/warehouse/Shipping/ReceiveProduct.html'
    if request.method == 'GET':
        wo_finishedform = WO_FinishedForm(request.GET or None)
        
        return render(request, template_name, {'rec_prodform':wo_finishedform, 'user':request.user })
    elif request.method == 'POST' :

        wo_finishedform = WO_FinishedForm(request.POST)
        if wo_finishedform.is_valid():
            #----UPDATE WO_FINISHED LIST----
            wo_finishedform = wo_finishedform.save(commit=False)
            wo_finished = WO_Finished.objects.get(prod_sched=wo_finishedform.prod_sched)
            wo_finished.name_plate = wo_finishedform.name_plate
            wo_finished.label_sticker = wo_finishedform.label_sticker
            wo_finished.iom = wo_finishedform.iom
            wo_finished.qr_code = wo_finishedform.qr_code
            wo_finished.wrnty_card = wo_finishedform.wrnty_card
            wo_finished.packaging = wo_finishedform.packaging
            wo_finished.date_out = wo_finishedform.date_out
            wo_finished.checked_by = wo_finishedform.checked_by
            wo_finished.notes = wo_finishedform.notes
            wo_finished.cleared = True
            if len(request.FILES) != 0:
                wo_finished.image = request.FILES["image"]
            wo_finished.save()
            #-----PROD SCHED UPDATE----
            prod_sched = WO_Production_Schedule.objects.get(id=wo_finishedform.prod_sched.id)
            prod_sched.received = True
            prod_sched.status = "Received Product"
            prod_sched.save()

            checkWO_Finish(prod_sched)#--Check if all WO Schedule are finished--
            
            UpdateAssemblyItems(prod_sched)#-----Update Whse Assembly Items----#----Add Item To Product Transaction---
            
            AddNewProdTransac(prod_sched)#----New Product Transaction-----

            if 'shiplby' == request.POST.get('btn_sel'): #ADD PRODUCT TO SHIPPING LOBBY
                
                
                AddtoShippingLobby(prod_sched, wo_finished.date_out)#----Add Shipping Lobby----
                
                AddtoShippingLobby_Transac(prod_sched, wo_finished.date_out)#----Add Shipping Lobby Transac----
                return redirect('home')

            if 'whse' == request.POST.get('btn_sel'): #add Product To Warehouse
                firsturl = "/warehouse/ReceiveProduct/"
                prod_sched_pk = str(prod_sched.id)
                secondurl = "/SelectWhseBin/"
                return redirect(firsturl+prod_sched_pk+secondurl) #Redirect to Work Order Scheduler

        else:
            print("rec_prodform.errors")
            print(rec_prodform.errors)

        return redirect('home')
def UpdateAssemblyItems(prod_sched):
    assitem_finishset = Assembly_Items.objects.filter(reference_number=prod_sched.id)
    for ass_item in assitem_finishset:#----Add Item To Product Transaction---
        AddItem_to_Prod_Transac(prod_sched.id, ass_item.assemblyline.name, ass_item.item_number, ass_item.quantity)

    for ass_item in assitem_finishset:#----Delete Assembly Line Items---
        ass_item.delete()
def AddItem_to_Prod_Transac(refnum, assemblyline, itemnum, itemquan):
    item_to_prod_transac = RecProduct_Item_Transaction.objects.create(
        reference_number=refnum,
        transaction_type="Product Conversion",
        transaction_location=assemblyline,
        item_number=itemnum,
        item_quantity=itemquan)
    item_to_prod_transac.full_clean()
def AddNewProdTransac(prod_sched):
    item_to_prod_transac = RecProduct_Product_Transaction.objects.create(
        reference_number=prod_sched.id,
        transaction_type="Product Creation",
        transaction_location="In Assembly",
        prod_number=prod_sched.work_order_number.prod_number,
        prod_quantity=prod_sched.quantity)
    item_to_prod_transac.full_clean()
def AddtoShippingLobby(prod_sched, date_rec):
    new_shiplby = Shipping_Lobby.objects.create(
        prod_sched = prod_sched,
        prod_number=prod_sched.work_order_number.prod_number,
        quantity=prod_sched.quantity,
        date_received=date_rec,
        received_by="Warehouse Personnel 1",
        checked_by="Manager 1",
        notes="Notes",
        )
    new_shiplby.full_clean()
    new_shiplby.save()
def AddtoShippingLobby_Transac(prod_sched, date_rec):
    newshiplby_transac = RecProduct_ProductToShipLobby_Transaction.objects.create(
        reference_number=prod_sched.id,
        transaction_type="Product Receiving",
        transaction_date=date_rec,
        transaction_location="In Shipping Lobby",
        prod_number=prod_sched.work_order_number.prod_number,
        prod_quantity=prod_sched.quantity,
        )
    newshiplby_transac.full_clean()
    newshiplby_transac.save()

def checkWO_Finish(prod_sched):
    wo_obj = Work_Order.objects.get( work_order_number=prod_sched.work_order_number.work_order_number )

    prod_sched_query = WO_Production_Schedule.objects.filter( work_order_number__work_order_number = wo_obj.work_order_number )

    total_created = 0;
    total_done = 0;
    for prod_sched in prod_sched_query:
        total_created += 1
        if prod_sched.received == True:
            total_done += 1

    if total_created == total_done: #All work-Order Schedules are done!
        wo_obj.finished_completion_date = datetime.now().replace(tzinfo=pytz.utc)
        wo_obj.finished = True
        wo_obj.save()




@login_required
@warehouse_required
def ReceiveProduct_SelectProdSched(request):
    template_name = 'invsys/warehouse/Shipping/ReceiveProduct_SelectProdSched.html'
    wo_finishlist = WO_Finished.objects.filter(cleared=False).values(
        'prod_sched__id',
        'prod_sched__work_order_number__work_order_number',
        'prod_sched__work_order_number__prod_number__prod_number',
        'prod_sched__work_order_number__prod_number__prod_class__prod_class',
        'prod_sched__quantity',
        'date_received',)

    wo_finishlist_query = WO_Finished.objects.filter(cleared=False)
    prodsched = []
    for wo in wo_finishlist_query:
        prodsched.append(wo.prod_sched.id)

    wo_itemfinishlist = Assembly_Items.objects.filter(reference_number__in=prodsched).values(
        'reference_number',
        'item_number__item_number',
        'quantity',
        'assemblyline__name',)

    return render(request, template_name, {'wo_finishlist':wo_finishlist,'wo_itemfinishlist':wo_itemfinishlist})
def ReceiveProduct_SelectWhseBin(request, pk=None):
    template_name = 'invsys/warehouse/Shipping/ReceiveProduct_SelectWhseBin.html'
    if request.method == 'GET':
        prod_sched = WO_Production_Schedule.objects.filter(id=pk).values(
            'id',
            'work_order_number__work_order_number',
            'work_order_number__prod_number__prod_number',
            'work_order_number__prod_number__prod_class__prod_class',
            'quantity',)

        whseproduct_form = Warehouse_ProductsFormset(queryset=Warehouse_Products.objects.none())

        return render(request, template_name, {'prod_sched':prod_sched, 'whse_product_form':whseproduct_form })
    elif request.method == 'POST' :
        whseproduct_form = Warehouse_ProductsFormset(request.POST)
        if whseproduct_form.is_valid():
            
            prod_sched = WO_Production_Schedule.objects.get(id=pk)
            counter = 1
            for whse_product in whseproduct_form:
                if counter < len(whseproduct_form):
                    print(whse_product)
                    whsebin_product = whse_product.save(commit=False)
                    whsebin_product.prod_number = prod_sched.work_order_number.prod_number
                    whsebin_product.status = "In Stock"
                    whsebin_product.reference_number = prod_sched.id
                    whsebin_product.save()
                    AddWhseProd_Transac(prod_sched.id, whsebin_product.bin_location.bin_location, whsebin_product.prod_number, whsebin_product.quantity)
                    counter += 1
        return redirect('home')
def AddWhseProd_Transac(refnum, transac_loc, prod_number, prod_quan):
    whsebin_transac = RecProduct_ProductToWhse_Transaction.objects.create(
        reference_number=refnum,
        transaction_type="Product Stored in Warehouse",
        transaction_location=transac_loc,
        prod_number=prod_number,
        prod_quantity=prod_quan)
    whsebin_transac.full_clean()
    whsebin_transac.save()
def ReceiveProduct_SelectWhseBin_Select(request, pk=None):
    template_name = 'invsys/warehouse/Shipping/ReceiveProduct_SelectWhseBin_Select.html'
    prod_sched = WO_Production_Schedule.objects.filter(id=pk).values(
        'quantity',)
    prod_sched_query = WO_Production_Schedule.objects.get(id=pk)
    prod_cat = ItemCat.objects.get(item_cat="Product")
    whse_bin_query = Warehouse.objects.filter(item_cat=prod_cat, prod_class=prod_sched_query.work_order_number.prod_number.prod_class).values(
        'id',
        'bin_location',)
    whse_bin_sample = Warehouse.objects.filter(item_cat=prod_cat, prod_class=prod_sched_query.work_order_number.prod_number.prod_class)
    whse_bin_list = []
    for whse_bin in whse_bin_sample:
        whse_bin_list.append(whse_bin)
    whse_prod_query = Warehouse_Products.objects.filter(bin_location__in=whse_bin_list).values(
        'bin_location__id',
        'prod_number',
        'quantity',)
    return render(request, template_name, {
        'whsebin_product':whse_bin_query,
        'prod_sched':prod_sched,
        'whsebin_product_list':whse_prod_query })

#--Ship Product--
@login_required
@warehouse_required
def ShipProduct(request):
    template_name = 'invsys/warehouse/Shipping/ShipProduct.html'

    if request.method == 'GET':
        ship_outboundform = Shipping_OutboundForm(request.GET or None)
        
        return render(request, template_name, {'ship_outboundform':ship_outboundform, 'user':request.user })
    elif request.method == 'POST' :
        ship_outboundform = Shipping_OutboundForm(request.POST)
        now = datetime.now().replace(tzinfo=pytz.utc)

        if ship_outboundform.is_valid():
            #----UPDATE WO_FINISHED LIST----
            ship_outbound = ship_outboundform.save(commit=False) 
            ship_outbound.date_out = now
            ship_outbound.save()           

            wo_num_obj = Work_Order.objects.get(work_order_number=ship_outbound.wo_num)

            ship_lobby_list = Shipping_Lobby.objects.all()

            for ship_lobby in ship_lobby_list:
                if ship_lobby.prod_sched.work_order_number == wo_num_obj:
                    wo_num_obj.shipped = True
                    wo_num_obj.save()
                    AddShipping_Outbound_Transaction(ship_lobby.prod_sched.id, now, ship_lobby.prod_sched.work_order_number.prod_number, ship_lobby.prod_sched.quantity)
                    ship_lobby.delete()
            print("passed through!")
        else:
            print("ship_outboundform")
            print(ship_outboundform)

        return redirect('home')

def AddShipping_Outbound_Transaction(prod_sched, date_sched, prod_num, prod_quan):
    shipping_outbound_transac = Shipping_Outbound_Transaction.objects.create(
        reference_number=prod_sched,
        transaction_type="Production Schedule for Shipping",
        transaction_date=date_sched,
        transaction_location="Shipping Lobby",
        prod_number=prod_num,
        prod_quantity=prod_quan,
        )
    shipping_outbound_transac.full_clean()
    shipping_outbound_transac.save()
@login_required
@warehouse_required
def ShipProduct_SelectWONum(request):
    template_name = 'invsys/warehouse/Shipping/ShipProduct_SelectWONum.html'

    ship_lobby_query = Shipping_Lobby.objects.filter()

    wo_num_list = []
    for ship_lobby in ship_lobby_query:
        if AllProdSchedinShipLobby(ship_lobby.prod_sched.work_order_number):
            wo_num_list.append(ship_lobby.prod_sched.work_order_number.work_order_number)

    wo_num_query = Work_Order.objects.filter(work_order_number__in=wo_num_list).values(
        'work_order_number',
        'customer',
        'order_type',
        'work_order_class',
        'fo_number',
        'barcode',
        'tid_number',
        'prod_number__prod_number',
        'prod_quantity',
        'customer_order_date',
        'otd_customer_req_date',
        'otp_commitment_date',
        'required_completion_date',
        'finished_completion_date',
        'notes',)

    prod_sched_query = WO_Production_Schedule.objects.filter(work_order_number__work_order_number__in=wo_num_list).values(
        'id',
        'work_order_number__work_order_number',
        'quantity',
        'status',)

    return render(request, template_name, {'wo_num_set': wo_num_query,'prod_sched_set': prod_sched_query})

def AllProdSchedinShipLobby(wo_num):
    all_in_shiplobby = True

    wo_num_list = []
    prod_sched_req = WO_Production_Schedule.objects.filter(work_order_number=wo_num)

    for prod_sched in prod_sched_req:
        wo_prodsched = {}
        wo_prodsched['prod_sched'] = prod_sched.id
        if Shipping_Lobby.objects.filter(prod_sched=prod_sched).exists():
            wo_prodsched['in_shiplobby'] = True
        else:
            wo_prodsched['in_shiplobby'] = False
        wo_num_list.append(wo_prodsched)


    for i in wo_num_list:
        if i['in_shiplobby'] == False:
            all_in_shiplobby = False

    return all_in_shiplobby


#Part Request Issuance
#--Generate Part Request Issuance
@login_required
@warehouse_required
def GeneratePartRequestSchedule(request):
    template_name = 'invsys/warehouse/PartRequest/GeneratePartRequestSchedule.html'
    if request.method == 'GET':

        partreqschedule_form = Request_ScheduleForm(request.GET or None)
        #Populating Initial Forms
        partreqschedules = Request_Schedule.objects.all()
        if len(partreqschedules) > 0:
            next_scheduleid = Request_Schedule.objects.order_by('-schedule_num').first().schedule_num + 1
        else:
            next_scheduleid = 1
        partreqitem_formset = Request_ItemFormset(queryset=Request_Item.objects.none())
        return render(request, template_name, {'partreqschedule_form': partreqschedule_form,'partreqitem_formset': partreqitem_formset, 'scheduleid':next_scheduleid})
    
    elif request.method == 'POST' :
        partreqschedule_form = Request_ScheduleForm(request.POST)
        partreqitem_formset = Request_ItemFormset(request.POST, request.FILES)
        if partreqschedule_form.is_valid() and partreqitem_formset.is_valid():
            partreq_schedule = partreqschedule_form.save(commit=False)
            partreq_schedule.save()

            counter = 1
            for partreqitem in partreqitem_formset:
                if counter < len(partreqitem_formset):
                    partreq_item = partreqitem.save(commit=False)
                    partreq_item.schedule_num = partreq_schedule
                    partreq_item.save()
                    UpdateWhseBin_PartReqSched(partreq_item.prod_sched.id, partreq_item.item_number, partreq_item.location_from)
                    AddPartReqSched_Transac(partreq_item.prod_sched.id, partreq_schedule.date_scheduled, partreq_item.location_from.bin_location, partreq_item.item_number, partreq_item.quantity)
                    UpdateShrinkageReport(partreq_item.refnum, partreq_item.item_number)
                    counter += 1

        return redirect('home')
def UpdateWhseBin_PartReqSched(refnum, item_num, bin_loc):
    whsebin_query = Warehouse_Items.objects.filter(bin_location=bin_loc, item_number=item_num, reference_number=refnum, status="Allocated for Part Request")
    for whsebin in whsebin_query:
        whsebin.status = "Scheduled for Request Issuance" 
        whsebin.save()
def AddPartReqSched_Transac(prod_sched, date_sched, bin_loc, item_num, item_quan):
    whsebin_partreqsched_transac = Request_Schedule_Transaction.objects.create(
        reference_number=prod_sched,
        transaction_type="Scheduled for Request Issuance",
        transaction_date=date_sched,
        transaction_location=bin_loc,
        item_number=item_num,
        item_quantity=item_quan,
        )
    whsebin_partreqsched_transac.full_clean()
    whsebin_partreqsched_transac.save()
def UpdateShrinkageReport(report_num, item_num):
    report_query = Shrinkage_Ass_Report.objects.get(report_num=report_num)
    report_item = Shrinkage_Ass_Item.objects.get(report_num=report_query,item_number=item_num)
    report_item.scheduled = True
    report_item.save()
@login_required
@warehouse_required
def GeneratePartRequestSchedule_SelectItem(request):
    template_name = 'invsys/warehouse/PartRequest/GeneratePartRequestSchedule_SelectItem.html'
    shrnk_items = Shrinkage_Ass_Item.objects.filter(scheduled=False).values(
        'report_num__report_num',
        'report_num__prod_sched__id',
        'item_number__item_number',
        'quantity',
        'ass_location__id',
        'ass_location__name',)
    whsebinshrnk_items = Warehouse_Items.objects.filter(status="Allocated for Part Request").values(
        'bin_location__id',
        'bin_location__bin_location',
        'item_number__item_number',
        'quantity',
        'reference_number',)
    whseitem_partreq_list = Warehouse_Items.objects.filter(status="Allocated for Part Request").filter()
    return render(request, template_name, {'shrnk_items': shrnk_items,'whsebinshrnk_items': whsebinshrnk_items})

#--Finish Part Request Issuance
@login_required
@warehouse_required
def FinishPartReqIssuance(request):
    template_name = 'invsys/warehouse/PartRequest/FinishPartReqIssuance.html'
    if request.method == 'GET':
        partreq_summary = PartReq_Issuance_SummaryFormset(queryset=Request_Summary.objects.none(), prefix='formsetsummary')
        
        partreq_issuance_list = Request_Item.objects.filter(cleared=False).values(
            'schedule_num__schedule_num',
            'prod_sched__id',
            'item_number__item_number',
            'quantity',
            'location_from__id',
            'location_from__bin_location',
            'location_to__id',
            'location_to__name',)
        return render(request, template_name, {'partreq_summary':partreq_summary,'partreq_issuance_list':partreq_issuance_list})
    elif request.method == 'POST' :
        
        partreq_summaryformset = PartReq_Issuance_SummaryFormset(request.POST , request.FILES, prefix='formsetsummary')

        if partreq_summaryformset.is_valid():
            partreqissuesched = Request_Schedule.objects.get(schedule_num=request.POST.get('partreqissuesched',''))
            now = datetime.now().replace(tzinfo=pytz.utc)
            date_received = now

            counter = 1    
            for summary_item in partreq_summaryformset:
                if counter < len(partreq_summaryformset):
                    partreq_summary = summary_item.save(commit=False)
                    partreq_summary.schedule_num = partreqissuesched
                    partreq_summary.date_received = date_received
                    partreq_summary.save()

                    partreq_recitem = Request_RecItem.objects.create(
                        schedule_num=partreq_summary.schedule_num,
                        prod_sched=partreq_summary.prod_sched,
                        item_number=partreq_summary.item_number,
                        rec_quantity=partreq_summary.totalrec_quan,
                        date_received=partreq_summary.date_received,
                        notes="None",
                        bin_location=partreq_summary.bin_location,
                        ass_location=partreq_summary.ass_location,)
                    partreq_recitem.save()
                    SubtractBinStock_FinishPartReqIssuance(partreq_recitem, request)

                    AnalyzeIssuance_PartReq(partreq_summary)
                    UpdateReqItems_PartReq(partreq_summary)
                    counter += 1
            
            CheckPartReq_IssuanceSchedule(partreqissuesched)
            DeleteWhseItemBin()
            DeleteAssemblyItem()
            checkcomplete_prodsched_items(partreq_summary.prod_sched.id)
        else:
            print("partreq_summary.errors")
            print(partreq_summary.errors)

        return redirect('home')
def UpdateReqItems_PartReq(partreq_summary):
    part_reqitem = Request_Item.objects.get(schedule_num=partreq_summary.schedule_num, prod_sched=partreq_summary.prod_sched, item_number=partreq_summary.item_number)
    part_reqitem.cleared = True
    part_reqitem.save()
def SubtractBinStock_FinishPartReqIssuance(partreq_recitem, request ):
    itemnum = partreq_recitem.item_number
    bin_loc = partreq_recitem.bin_location
    prodsched = partreq_recitem.prod_sched.id
    recQuan = partreq_recitem.rec_quantity

    whsebinset = Warehouse_Items.objects.filter(bin_location=bin_loc, item_number=itemnum, reference_number=prodsched, status="Scheduled for Request Issuance")
    for whsebin in whsebinset:
        
        whsebin.quantity -= recQuan
        
        if whsebin.quantity < 0:
            
            adjustitems_overissuance( whsebin.bin_location,whsebin.item_number, abs(whsebin.quantity), request )
            whsebin.quantity = 0

        elif whsebin.quantity > 0:

            adjustitems_shortissuance( whsebin.bin_location, whsebin.item_number, abs(whsebin.quantity), request, prodsched )

            whsebin.quantity = 0

        whsebin.save()

def adjustitems_overissuance( whse_bin_adj, item_num_adj, item_quan_adj, request ):
    
    sa_report_newobj = SA_Report.objects.create(
        iaf_whse=IAF_whse.objects.get(whse="WHSE"),
        date_reported=datetime.now().replace(tzinfo=pytz.utc),
        notes="Warehouse Over Issued - New Items")
    sa_report_newobj.full_clean()
    sa_report_newobj.save()

    sa_item_newobj = SA_Item.objects.create(
        report_num=sa_report_newobj,
        bin_location=whse_bin_adj,
        item_number=item_num_adj,
        item_quantity=item_quan_adj,
        iaf_operator=IAF_operator.objects.get(operator="Add"),
        total_cost=int(item_num_adj.price) * item_quan_adj,
        reason="new items from over issuance")
    sa_item_newobj.full_clean()
    sa_item_newobj.save()

    sa_items = []
    sa_items.append(sa_item_newobj)

    #Add transaction because of new items found
    AddSA_Add_Transac(sa_report_newobj.report_num, sa_item_newobj.bin_location.bin_location, sa_item_newobj.item_number, sa_item_newobj.item_quantity)
    #Add IAF Report
    AddIAF_Report(sa_report_newobj.iaf_whse, "Change/Modify/Conversion", "System Adjustment", request.user, sa_items)

def adjustitems_shortissuance( whse_bin_adj, item_num_adj, item_quan_adj, request, prodsched ):
    
    prodsched_obj = WO_Production_Schedule.objects.get(id=prodsched)
    prod_class = prodsched_obj.work_order_number.prod_number.prod_class
    assembly_line_ass = Assembly_Line_Assignment.objects.get(prod_class=prod_class)

    shrnk_report_newobj = Shrinkage_Ass_Report.objects.create(
        prod_sched=prodsched_obj,
        item_number=item_num_adj,
        quantity=item_quan_adj,
        shrinkage_type=Shrinkage_Type.objects.get(shrinkage_type="Loss"),
        reason="Warehouse Short Issued - Short Items",
        date_reported=datetime.now().replace(tzinfo=pytz.utc))
    shrnk_report_newobj.full_clean()
    shrnk_report_newobj.save()

    shrnk_item_newobj = Shrinkage_Ass_Item.objects.create(
        report_num=shrnk_report_newobj,
        item_number=item_num_adj,
        quantity=item_quan_adj,
        scheduled=False,
        ass_location=assembly_line_ass.assemblyline)
    shrnk_item_newobj.full_clean()
    shrnk_item_newobj.save()

    totalallocated = 0

    AllocateWhseItems_Shrnk( shrnk_item_newobj.item_number, shrnk_item_newobj.quantity, totalallocated, shrnk_report_newobj.prod_sched.id )
    UpdateAssemblyItems_Shrnk( shrnk_report_newobj.prod_sched.id, shrnk_item_newobj.item_number, shrnk_item_newobj.quantity )
    AddShrnkReportTransac( shrnk_report_newobj.prod_sched.id, shrnk_report_newobj.date_reported, shrnk_report_newobj.item_number, shrnk_report_newobj.quantity, shrnk_item_newobj.ass_location.name )
    AddShrnkRplItemTransac( shrnk_report_newobj.prod_sched.id, shrnk_report_newobj.date_reported, shrnk_item_newobj.item_number, shrnk_item_newobj.quantity, shrnk_item_newobj.ass_location.name )

def AddShrnkReportTransac(refnum, transac_date, item_number, item_quan, ass_line):
    shrnkreport_transac = Shrinkage_Ass_Report_Transaction.objects.create(
        reference_number=refnum,
        transaction_type="Shrinkage Item Report",
        transaction_date=transac_date,
        transaction_location=ass_line,
        item_number=item_number,
        item_quantity=item_quan,
        )
    shrnkreport_transac.full_clean()
    shrnkreport_transac.save()
def AddShrnkRplItemTransac(refnum, transac_date, item_number, item_quan, ass_line):
    shrnkrplitem_transac = Shrinkage_Ass_Item_Transaction.objects.create(
        reference_number=refnum,
        transaction_type="Shrinkage Item Replacement",
        transaction_date=transac_date,
        transaction_location=ass_line,
        item_number=item_number,
        item_quantity=item_quan,
        )
    shrnkrplitem_transac.full_clean()
    shrnkrplitem_transac.save()
def UpdateAssemblyItems_Shrnk(prod_sched, item_num, item_quan):
    assitem_shrnkset = Assembly_Items.objects.filter(reference_number=prod_sched, item_number=item_num)

    for ass_item in assitem_shrnkset:#----Adjust Assembly Line Item---
        ass_item.quantity -= item_quan
        if(ass_item.quantity == 0):
            ass_item.delete()
        else:
            ass_item.save()
def AllocateWhseItems_Shrnk(itemnum, totalreq, totalalloc, prod_sched):
    whseitemset = Warehouse_Items.objects.filter(status="In Stock", item_number=itemnum, bin_location__item_cat=itemnum.item_cat, bin_location__prod_class=itemnum.prod_class).order_by('quantity')
    for whsebin in whseitemset:
        if not totalreq == totalalloc:
            totalalloc, whsebin = SubtractBinStock_Shrnk(whsebin, totalreq, totalalloc, itemnum, prod_sched)
            whsebin.save() 
def SubtractBinStock_Shrnk(whsebin, totalreq, totalalloc, itemnum, prod_sched):
    allocatedbinquan = 0
    binStock = 0
    remainingalloc = 0
    binStock = whsebin.quantity
    remainingalloc = int(totalreq) - totalalloc
    if remainingalloc < binStock: #Bin stock fulfilled required allocation
        allocatedbinquan = remainingalloc
        whsebin.quantity -= remainingalloc
    elif remainingalloc == binStock: #Bin stock fulfilled required allocation
        allocatedbinquan = remainingalloc
        whsebin.quantity = 0
    elif remainingalloc > binStock: #Bin stock did not fulfill required allocation
        allocatedbinquan = binStock
        whsebin.quantity = 0
    CreateWhseItemBin_Shrnk(whsebin.bin_location, itemnum, allocatedbinquan, prod_sched)
    totalalloc += allocatedbinquan
    return totalalloc, whsebin
def CreateWhseItemBin_Shrnk(binloc, itemnum, allocquan, prod_sched):
    whseitemBin = Warehouse_Items.objects.create(
        bin_location=binloc, 
        item_number=itemnum,
        quantity=allocquan,
        status="Allocated for Part Request",
        reference_number=prod_sched)
    whseitemBin.full_clean()
    whseitemBin.save()
def DeleteWhseItemBin():
    whseitemset = Warehouse_Items.objects.order_by('quantity')
    for whsebin in whseitemset:
        if whsebin.quantity == 0:
            whsebin.delete()
def ReportShrinkage_SelectProdSched(request):
    template_name = 'invsys/assembly/AssemblyShrinkage/ReportShrinkage_SelectProdSched.html'

    prodsched_list = WO_Production_Schedule.objects.filter(scheduled=True, received=False).values( #Only issues work-orders
        'id',
        'work_order_number__work_order_number',
        'work_order_number__prod_number__prod_number',
        'work_order_number__prod_number__prod_class__prod_class',
        'quantity',
        'issued',
        'assembled',
        'coupled',)

    prodsched_listquery = WO_Production_Schedule.objects.filter(issued=True)
    prodsched_set = []
    for prod_sched in prodsched_listquery:
        prodsched_set.append(prod_sched.id)

    wo_itemlist = Assembly_Items.objects.filter(reference_number__in=prodsched_set).values(
        'reference_number',
        'item_number__item_number',
        'quantity',
        'assemblyline__name',)

    return render(request, template_name, {'prodsched_list':prodsched_list,'wo_itemlist':wo_itemlist})
def ReportShrinkage_SelectItem(request, pk=None):
    template_name = 'invsys/assembly/AssemblyShrinkage/ReportShrinkage_SelectItem.html'
    ass_item = Assembly_Items.objects.filter(reference_number=pk).values(
        'item_number__item_number',
        'item_number__item_cat__item_cat',
        'quantity',
        'assemblyline__id',
        'assemblyline__name',)

    return render(request, template_name,{'ass_item':ass_item})
def DeleteAssemblyItem():
    assitem_set = Assembly_Items.objects.order_by('quantity')
    for assitem in assitem_set:
        if assitem.quantity == 0:
            assitem.delete()



def AnalyzeIssuance_PartReq(partreq_summary):
    itemnum = partreq_summary.item_number
    reqQuan = partreq_summary.totalreq_quan
    recQuan = partreq_summary.totalrec_quan
    discQuan = partreq_summary.discrepancy_quantity
    prodsched = partreq_summary.prod_sched.id
    ass_line = partreq_summary.ass_location

    assline_item_list = Assembly_Items.objects.filter(item_number=itemnum, reference_number=prodsched)
    assline_itemdisc_list = Assembly_Discrepancy.objects.filter(item_number=itemnum, reference_number=prodsched)

    if reqQuan < recQuan:
        if not assline_item_list:
            AddtoAssembly_Item_PartReq(itemnum, reqQuan, prodsched, ass_line)
        else:
            for assline in assline_item_list:
                assline.quantity += reqQuan
                assline.save()
        AddtoAssembly_Transac_PartReq(itemnum, reqQuan, prodsched, ass_line)

        if not assline_itemdisc_list:
            AddAssemblyDiscItem_PartReq(itemnum, abs(int(discQuan)), prodsched, ass_line)
        else:
            for assline_disc in assline_itemdisc_list:
                assline_disc.quantity += abs(int(discQuan))
                assline_disc.save()       
        AddRecIssuanceDiscTransac_PartReq(itemnum, discQuan, prodsched, ass_line)

    elif reqQuan == recQuan:
        if not assline_item_list:
            AddtoAssembly_Item_PartReq(itemnum, reqQuan, prodsched, ass_line)
        else:
            for assline in assline_item_list:
                assline.quantity += reqQuan
                assline.save()
        AddtoAssembly_Transac_PartReq(itemnum, reqQuan, prodsched, ass_line)
    elif reqQuan > recQuan:
        if not assline_item_list:
            AddtoAssembly_Item_PartReq(itemnum, recQuan, prodsched, ass_line)
        else:
            for assline in assline_item_list:
                assline.quantity += reqQuan
                assline.save()
        AddtoAssembly_Transac_PartReq(itemnum, recQuan, prodsched, ass_line)

def AddtoAssembly_Item_PartReq(itemnum, reqQuan, prodsched, ass_line):
    ass_item = Assembly_Items.objects.create(
        assemblyline=ass_line,
        item_number=itemnum,
        quantity=reqQuan,
        status="In Assembly",
        reference_number=prodsched)
    ass_item.full_clean()
    ass_item.save()
def AddtoAssembly_Transac_PartReq(itemnum, reqQuan, prodsched, ass_line):
    ass_item_transac = Request_Finish_Transaction.objects.create(
        reference_number=prodsched,
        transaction_type="Part Request Issuance",
        transaction_location=ass_line.name,
        item_number=itemnum,
        item_quantity=reqQuan)
    ass_item_transac.full_clean()
    ass_item_transac.save()
def AddAssemblyDiscItem_PartReq(itemnum, discQuan, prodsched, ass_line):
    ass_item = Assembly_Discrepancy.objects.create(
        assemblyline=ass_line,
        item_number=itemnum,
        quantity=discQuan,
        status="Waiting for Return",
        reference_number=prodsched)
    ass_item.full_clean()
    ass_item.save()
def AddRecIssuanceDiscTransac_PartReq(itemnum, discQuan, prodsched, ass_line):
    ass_discitem = Request_DiscSummary_Transaction.objects.create(
        reference_number=prodsched,
        transaction_type="Part Request Issuance Discrepancy",
        transaction_location=ass_line.name,
        item_number=itemnum,
        item_quantity=discQuan)
    ass_discitem.full_clean()
    ass_discitem.save()
def CheckPartReq_IssuanceSchedule(partreqissuesched):
    partreqlist_set = Request_Item.objects.filter(schedule_num=partreqissuesched)
    schedcount = 0
    clearedcount = 0
    for partreq_list in partreqlist_set:
        schedcount += 1
        if partreq_list.cleared == True:
            clearedcount += 1
    if schedcount == clearedcount:
        partreqissuesched.cleared = True
        partreqissuesched.save()
@login_required
@warehouse_required
def FinishPartReqIssuance_SelectPartReqSched(request):
    template_name = 'invsys/warehouse/PartRequest/FinishPartReqIssuance_SelectPartReqSched.html'
    partreq_issuancesched = Request_Schedule.objects.filter(cleared=False).values(
        'schedule_num',
        'date_scheduled',
        'notes',
        'issues',)
    print(partreq_issuancesched)
    partreqissuance = Request_Schedule.objects.filter(cleared=False)
    partreqissueschedules = []
    for schedule in partreqissuance:
        partreqissueschedules.append(schedule)
    partreq_issuance_list = Request_Item.objects.filter(schedule_num__in=partreqissueschedules).values(
        'schedule_num__schedule_num',
        'prod_sched__id',
        'item_number__item_number',
        'quantity',
        'location_from__id',
        'location_from__bin_location',
        'location_to__id',
        'location_to__name',)

    return render(request, template_name,{'partreq_issuancesched':partreq_issuancesched,'partreq_issuance_list':partreq_issuance_list})
@login_required
@warehouse_required
def FinishPartReqIssuance_SelectItem(request, pk=None):
    template_name = 'invsys/warehouse/PartRequest/FinishPartReqIssuance_SelectItem.html'
    partreq_issuance_list = Request_Item.objects.filter(schedule_num=pk).values(
        'schedule_num__schedule_num',
        'prod_sched__id',
        'item_number__item_number',
        'item_number__item_cat__item_cat',
        'quantity',
        'location_from__id',
        'location_from__bin_location',
        'location_to__id',
        'location_to__name',)

    return render(request, template_name,{'partreq_issuance_list':partreq_issuance_list})

#-- Check wo items
def checkcomplete_prodsched_items(prodsched):
    issues = "None" 

    prodsched_obj = WO_Production_Schedule.objects.get(id=prodsched)
    wo_items_list = Work_Order_Item_List.objects.filter(work_order_number__work_order_number=prodsched_obj.work_order_number.work_order_number)
    

    for wo_item in wo_items_list:
        tot_req = int(prodsched_obj.quantity) * int(wo_item.item_quantity)
        item_num = wo_item.item_number.item_number
        ass_quan = 0

        try:
            assembly_item = Assembly_Items.objects.get(reference_number=prodsched, item_number__item_number=item_num)
            ass_quan = int(assembly_item.quantity)

        except ObjectDoesNotExist as DoesNotExist:
            ass_quan = 0

        if tot_req != ass_quan:
            issues = "Incomplete Items"

    prodsched_obj.issues = issues
    prodsched_obj.save()


#PART REQUEST ISSUANCE
@login_required
@warehouse_required
def ViewPartReqSummary(request):
    template_name = 'invsys/assembly/PartRequest/ViewPartReqSummary.html'
    
    req_sched_list = Request_Schedule.objects.all().values(
        'schedule_num',
        'date_scheduled',
        'cleared',
        'issues',
        'notes',)
    
    req_sum_list = Request_Summary.objects.all().values(
        'schedule_num__schedule_num',
        'prod_sched__work_order_number__work_order_number',
        'prod_sched__id',
        'item_number__item_number',
        'item_number__item_desc',
        'totalreq_quan',
        'totalrec_quan',
        'discrepancy_quantity',
        'status',
        'date_received',
        'bin_location__bin_location',
        'ass_location__name',)

    return render(request, template_name, 
        {'req_sched_set':req_sched_list,
        'req_sum_set':req_sum_list,})

#Component Return
#--Generate Component Return Schedule--
@login_required
@warehouse_required
def GenerateCompReturnSchedule(request):
    template_name = 'invsys/warehouse/CompReturn/GenerateCompReturnSchedule.html'
    if request.method == 'GET':

        compreturnschedule_form = ComponentReturn_ScheduleForm(request.GET or None)
        #Populating Initial Forms
        compreturnschedules = ComponentReturn_Schedule.objects.all()
        if len(compreturnschedules) > 0:
            next_scheduleid = ComponentReturn_Schedule.objects.order_by('-schedule_num').first().schedule_num + 1
        else:
            next_scheduleid = 1
        compreturnitem_formset = ComponentReturn_ItemFormset(queryset=Request_Item.objects.none())
        return render(request, template_name, {'compreturnschedule_form': compreturnschedule_form,'compreturnitem_formset': compreturnitem_formset, 'scheduleid':next_scheduleid})
    
    elif request.method == 'POST' :

        compreturnschedule_form = ComponentReturn_ScheduleForm(request.POST)
        compreturnitem_formset = ComponentReturn_ItemFormset(request.POST, request.FILES)
        if compreturnschedule_form.is_valid() and compreturnitem_formset.is_valid():

            compreturn_schedule = compreturnschedule_form.save(commit=False)
            compreturn_schedule.save()

            counter = 1
            for compreturnitem_form in compreturnitem_formset:
                if counter < len(compreturnitem_formset):
                    compreturn_item = compreturnitem_form.save(commit=False)
                    compreturn_item.schedule_num = compreturn_schedule
                    compreturn_item.save()
                    UpdateAssembly_DiscItems(compreturn_item.location_from, compreturn_item.item_number, compreturn_item.prod_sched.id)
                    AddCompReturnSched_Transac(compreturn_item.location_from, compreturn_item.item_number, compreturn_item.prod_sched.id, compreturn_item.quantity)
                    counter += 1
        return redirect('home')
def UpdateAssembly_DiscItems(ass_line, item_num, prod_sched):
    assdisc_items = Assembly_Discrepancy.objects.filter(assemblyline=ass_line, item_number=item_num, reference_number=prod_sched)
    for ass_disc in assdisc_items:
        ass_disc.status = "Scheduled for Return"
        ass_disc.save()
def AddCompReturnSched_Transac(ass_line, item_num, prod_sched, item_quan):
    ass_discitem = ComponentReturn_Schedule_Transaction.objects.create(
        reference_number=prod_sched,
        transaction_type="Component Return from Discrepancy",
        transaction_location=ass_line.name,
        item_number=item_num,
        item_quantity=item_quan)
    ass_discitem.full_clean()
    ass_discitem.save()
@login_required
@warehouse_required
def GenerateCompReturnSchedule_SelectItem(request):
    template_name = 'invsys/warehouse/CompReturn/GenerateCompReturnSchedule_SelectItem.html'
    assdisc_items = Assembly_Discrepancy.objects.filter(status="Waiting for Return").values(
        'id',
        'assemblyline__id',
        'assemblyline__name',
        'item_number__item_number',
        'quantity',
        'reference_number',)
    return render(request, template_name, {'assdisc_items': assdisc_items})
#--Finish Component Return--
@login_required
@warehouse_required
def FinishCompReturn(request):
    template_name = 'invsys/warehouse/CompReturn/FinishCompReturn.html'
    if request.method == 'GET':

        compreturn_recitem = CompReturn_RecItemFormset(queryset=ComponentReturn_RecItem.objects.none(), prefix='formsetitem')
        compreturn_summary = CompReturn_SummaryFormset(queryset=ComponentReturn_Summary.objects.none(), prefix='formsetsummary')
        
        compreturn_list = ComponentReturn_Item.objects.filter(cleared=False).values(
            'schedule_num__schedule_num',
            'prod_sched__id',
            'item_number__item_number',
            'quantity',
            'location_from__id',
            'location_from__name',)
        return render(request, template_name, {'compreturn_recitem':compreturn_recitem,'compreturn_summary':compreturn_summary,'compreturn_list':compreturn_list})
    
    elif request.method == 'POST' :

        compreturn_summaryformset = CompReturn_SummaryFormset(request.POST , request.FILES, prefix='formsetsummary')

        if compreturn_summaryformset.is_valid():
            compreturn_schedule = ComponentReturn_Schedule.objects.get(schedule_num=request.POST.get('compreturnissuesched',''))
            now = datetime.now().replace(tzinfo=pytz.utc)
            date_received = now

            counter = 1    
            for summary_item in compreturn_summaryformset:
                if counter < len(compreturn_summaryformset):

                    partreq_summary = summary_item.save(commit=False)
                    partreq_summary.schedule_num = compreturn_schedule
                    partreq_summary.date_received = date_received
                    partreq_summary.save()

                    compreturn_recitem = ComponentReturn_RecItem.objects.create(
                        schedule_num=compreturn_schedule,
                        prod_sched=partreq_summary.prod_sched,
                        item_number=partreq_summary.item_number,
                        quantity=partreq_summary.totalrec_quan,
                        date_received=partreq_summary.date_received,
                        notes="None",
                        ass_location=partreq_summary.ass_location,)
                    compreturn_recitem.save()

                    SubtractAssDisc_FinishCompReturn(compreturn_recitem)
                    AddtoCompReturnSummaryTransac(compreturn_recitem.prod_sched.id, compreturn_recitem.item_number, compreturn_recitem.quantity)
                    
                    AddtoReceivingLobby_CompReturn(partreq_summary.prod_sched.id, partreq_summary.item_number, partreq_summary.totalrec_quan)
                    UpdateReqItems_CompReturn(partreq_summary)
                    counter += 1
            
            CheckCompReturnSchedule(compreturn_schedule)
            DeleteAssDiscItem()      

        return redirect('home')
def UpdateReqItems_CompReturn(partreq_summary):
    comp_reqitem = ComponentReturn_Item.objects.get(schedule_num=partreq_summary.schedule_num, prod_sched=partreq_summary.prod_sched, item_number=partreq_summary.item_number)
    if partreq_summary.discrepancy == False:
        comp_reqitem.cleared = True
        comp_reqitem.save()
def SubtractAssDisc_FinishCompReturn(compreturn_recitem):
    itemnum = compreturn_recitem.item_number
    ass_loc = compreturn_recitem.ass_location
    prodsched = compreturn_recitem.prod_sched.id
    recQuan = compreturn_recitem.quantity

    assdisc_items = Assembly_Discrepancy.objects.filter(assemblyline=ass_loc, item_number=itemnum, reference_number=prodsched, status="Scheduled for Return")
    for ass_disc in assdisc_items:
        ass_disc.quantity -= recQuan
        ass_disc.save()
def AddtoReceivingLobby_CompReturn(refnum,itemnum,recquan):
    r = Receiving_Lobby.objects.create(
        reference_number=refnum, 
        item_number=itemnum,
        received_quantity=recquan,
        scheduled_quantity=0,
        status="Waiting for Put Away")
    r.full_clean()
    r.save()
    RecordRecLobbyTransac_CompReturn(refnum,itemnum,recquan)
def RecordRecLobbyTransac_CompReturn(refnum,itemnum,itemquan):
    rtransac = RecLobby_Transaction.objects.create(
        reference_number=refnum,
        transaction_type="Component Return from Assembly",
        transaction_location="Receiving Lobby",
        item_number=itemnum,
        item_quantity=itemquan)
    rtransac.full_clean()
    rtransac.save()
def AddtoCompReturnSummaryTransac(refnum,itemnum,itemquan):
    rtransac = RecLobby_Transaction.objects.create(
        reference_number=refnum,
        transaction_type="Finished Component Return",
        transaction_location="Receiving Lobby",
        item_number=itemnum,
        item_quantity=itemquan)
    rtransac.full_clean()
    rtransac.save()
@login_required
@warehouse_required
def FinishCompReturn_SelectCompReturnSched(request):
    template_name = 'invsys/warehouse/CompReturn/FinishCompReturn_SelectCompReturnSched.html'
    compreturn_sched = ComponentReturn_Schedule.objects.filter(cleared=False).values(
        'schedule_num',
        'date_scheduled',
        'notes',
        'issues',)
    compreturn_sched_list = ComponentReturn_Schedule.objects.filter(cleared=False)
    compreturnschedules = []
    for schedule in compreturn_sched_list:
        compreturnschedules.append(schedule)
    compreturn_item_list = ComponentReturn_Item.objects.filter(schedule_num__in=compreturnschedules).values(
        'schedule_num__schedule_num',
        'prod_sched__id',
        'item_number__item_number',
        'quantity',
        'location_from__id',
        'location_from__name',)

    return render(request, template_name,{'compreturn_sched':compreturn_sched,'compreturn_item_list':compreturn_item_list})
@login_required
@warehouse_required
def FinishCompReturn_SelectItem(request, pk=None):
    template_name = 'invsys/warehouse/CompReturn/FinishCompReturn_SelectItem.html'
    compreturn_list = ComponentReturn_Item.objects.filter(schedule_num=pk).values(
        'schedule_num__schedule_num',
        'prod_sched__id',
        'item_number__item_number',
        'item_number__item_cat__item_cat',
        'quantity',
        'location_from__id',
        'location_from__name',)

    return render(request, template_name,{'compreturn_list':compreturn_list})
def DeleteAssDiscItem():
    assitemdisc_list = Assembly_Discrepancy.objects.order_by('quantity')
    for assitem_disc in assitemdisc_list:
        if assitem_disc.quantity == 0:
            assitem_disc.delete()
def CheckCompReturnSchedule(compreturn_schedule):
    compreturnlist_set = ComponentReturn_Item.objects.filter(schedule_num=compreturn_schedule)
    schedcount = 0
    clearedcount = 0
    for compreturn_list in compreturnlist_set:
        schedcount += 1
        if compreturn_list.cleared == True:
            clearedcount += 1
    if schedcount == clearedcount:
        compreturn_schedule.cleared = True
        compreturn_schedule.save()

def ViewCompReturnSummary(request):
    template_name = 'invsys/warehouse/CompReturn/ViewCompReturnSummary.html'
    
    return_sched_list = ComponentReturn_Schedule.objects.all().values(
        'schedule_num',
        'date_scheduled',
        'cleared',
        'issues',
        'notes',)
    
    return_sum_list = ComponentReturn_Summary.objects.all().values(
        'schedule_num__schedule_num',
        'prod_sched__work_order_number__work_order_number',
        'prod_sched__id',
        'item_number__item_number',
        'item_number__item_desc',
        'totalreq_quan',
        'totalrec_quan',
        'discrepancy_quantity',
        'status',
        'date_received',
        'ass_location__name',)

    return render(request, template_name, 
        {'return_sched_set':return_sched_list,
        'return_sum_set':return_sum_list,})

#WHSE UPDATES
#--REPORT DMMR--
@login_required
@warehouse_required
def ReportDMMR(request):
    template_name = 'invsys/warehouse/WhseUpdate/ReportDMMR.html'
    if request.method == 'GET':

        dmmr_form = DMMR_ReportForm(request.GET or None)
        dmm_reports = DMMR_Report.objects.all() #Populating Initial Forms
        if len(dmm_reports) > 0:
            next_scheduleid = DMMR_Report.objects.order_by('-report_num').first().report_num + 1
        else:
            next_scheduleid = 1
        dmmritem_formset = DMMR_Item_Formset(queryset=DMMR_Item.objects.none())
        
        iaf_whse_query = IAF_whse.objects.all().values(
            'id',
            'whse')

        return render(request, template_name, {
            'dmmr_form': dmmr_form,
            'dmmritem_formset': dmmritem_formset,
            'scheduleid':next_scheduleid,
            'iaf_whse_set':iaf_whse_query})
    
    elif request.method == 'POST' :
        dmmr_form = DMMR_ReportForm(request.POST)
        dmmritem_formset = DMMR_Item_Formset(request.POST, request.FILES)
        if dmmr_form.is_valid() and dmmritem_formset.is_valid():
            dmm_report = dmmr_form.save(commit=False)
            dmm_report.save()

            dmmr_items = []
            counter = 1
            for dmmritem_form in dmmritem_formset:
                if counter < len(dmmritem_formset):
                    dmmr_item = dmmritem_form.save(commit=False)
                    dmmr_item.report_num = dmm_report
                    dmmr_item.iaf_operator = IAF_operator.objects.get(operator="Subtract")
                    dmmr_item.save()
                    UpdateWhseItem_DMMR(dmmr_item.bin_location, dmmr_item.item_number, dmmr_item.item_quantity)
                    AddDMMR_Transac(dmm_report.report_num, dmmr_item.bin_location.bin_location, dmmr_item.item_number, dmmr_item.item_quantity)
                    dmmr_items.append(dmmr_item)
                    counter += 1

            AddIAF_Report(dmm_report.iaf_whse, "Scrap", "Damaged Material", request.user, dmmr_items)
            DeleteWhseItemBin()

        else:
            print("dmmr_form.errors")
            print(dmmr_form.errors)
            print("dmmritem_formset.errors")
            print(dmmritem_formset.errors)
        return redirect('home')
def UpdateWhseItem_DMMR(bin_loc, item_num, item_quan):
    whseitem_DMMR = Warehouse_Items.objects.get(bin_location=bin_loc, item_number=item_num, status="In Stock")
    whseitem_DMMR.quantity -= item_quan 
    whseitem_DMMR.save()
def AddDMMR_Transac(refnum, bin_loc, itemnum, itemquan):
    dmmr_transac = DMMR_Transaction.objects.create(
        reference_number=refnum,
        transaction_type="Damaged Material",
        transaction_location=bin_loc,
        item_number=itemnum,
        item_quantity=itemquan)
    dmmr_transac.full_clean()
    dmmr_transac.save()
def AddIAF_Report(whse, report_type, report_action, user, item_set):
    iaf_report = IAF_Report.objects.create(
        iaf_whse=whse,
        adjustment_type= IAF_code.objects.get(iaf_adjustment=report_type),
        iaf_action=report_action,
        prepared_by=user)
    iaf_report.full_clean()
    iaf_report.save()

    for item in item_set:
        AddIAFItems(iaf_report.report_num, item.item_number, item.bin_location, item.item_quantity, item.iaf_operator, item.total_cost, item.reason)
        if item.iaf_operator.operator == "Subtract": 
            AddIAF_Subt_Transac(iaf_report.report_num, report_action, item.bin_location.bin_location, item.item_number, item.item_quantity)
        else:
            AddIAF_Add_Transac(iaf_report.report_num, report_action, item.bin_location.bin_location, item.item_number, item.item_quantity)
def AddIAF_Subt_Transac(refnum, report_action, bin_loc, item_num, item_quan):
    iaf_subt_transac = IAF_Subt_Transaction.objects.create(
        reference_number=refnum,
        transaction_type=report_action,
        transaction_location=bin_loc,
        item_number=item_num,
        item_quantity=item_quan)
    iaf_subt_transac.full_clean()
    iaf_subt_transac.save()
def AddIAF_Add_Transac(refnum, report_action, bin_loc, item_num, item_quan):
    iaf_add_transac = IAF_Add_Transaction.objects.create(
        reference_number=refnum,
        transaction_type=report_action,
        transaction_location=bin_loc,
        item_number=item_num,
        item_quantity=item_quan)
    iaf_add_transac.full_clean()
    iaf_add_transac.save()
def AddIAFItems(report_num, item_num, bin_loc, item_quan, iaf_operator, tot_cost, reason):
    iaf_item = IAF_Item.objects.create(
        report_num=IAF_Report.objects.get(report_num=report_num),
        item_number=item_num,
        bin_location=bin_loc,
        item_quantity=item_quan,
        iaf_operator=iaf_operator,
        total_cost=tot_cost,
        reason=reason)
    iaf_item.full_clean()
    iaf_item.save()
@login_required
@warehouse_required
def ReportDMMR_SelectItem(request):
    template_name = 'invsys/warehouse/WhseUpdate/ReportDMMR_SelectItem.html'
    whse_items = Warehouse_Items.objects.filter(status="In Stock").values(
        'bin_location__id',
        'bin_location__bin_location',
        'item_number__item_number',
        'item_number__item_desc',
        'item_number__item_cat__item_cat',
        'item_number__prod_class__prod_class',
        'item_number__uom__uom',
        'item_number__price',
        'quantity',)
    return render(request, template_name, {'whse_items': whse_items})

#--REPORT DFMR--
@login_required
@warehouse_required
def ReportDFMR(request):
    template_name = 'invsys/warehouse/WhseUpdate/ReportDFMR.html'
    if request.method == 'GET':

        dfmr_form = DFMR_ReportForm(request.GET or None)
        dfm_reports = DFMR_Report.objects.all() #Populating Initial Forms
        if len(dfm_reports) > 0:
            next_scheduleid = DFMR_Report.objects.order_by('-report_num').first().report_num + 1
        else:
            next_scheduleid = 1
        dfmritem_formset = DFMR_Item_Formset(queryset=DFMR_Item.objects.none())
        
        iaf_whse_query = IAF_whse.objects.all().values(
            'id',
            'whse')

        return render(request, template_name, {
            'dfmr_form': dfmr_form,
            'dfmritem_formset': dfmritem_formset,
            'scheduleid':next_scheduleid,
            'iaf_whse_set':iaf_whse_query})

    elif request.method == 'POST' :
        dfmr_form = DFMR_ReportForm(request.POST)
        dfmritem_formset = DFMR_Item_Formset(request.POST, request.FILES)
        if dfmr_form.is_valid() and dfmritem_formset.is_valid():
            dfm_report = dfmr_form.save(commit=False)
            dfm_report.save()

            dfmr_items = []
            counter = 1
            for dfmritem_form in dfmritem_formset:
                if counter < len(dfmritem_formset):
                    dfmr_item = dfmritem_form.save(commit=False)
                    dfmr_item.report_num = dfm_report
                    dfmr_item.iaf_operator = IAF_operator.objects.get(operator="Subtract")
                    dfmr_item.save()
                    UpdateWhseItem_DFMR(dfmr_item.bin_location, dfmr_item.item_number, dfmr_item.item_quantity)
                    AddDFMR_Transac(dfm_report.report_num, dfmr_item.bin_location.bin_location, dfmr_item.item_number, dfmr_item.item_quantity)
                    dfmr_items.append(dfmr_item)
                    counter += 1

            AddIAF_Report(dfm_report.iaf_whse, "Scrap", "Defective Material", request.user, dfmr_items)
            DeleteWhseItemBin()

        else:
            print("dfmr_form.errors")
            print(dfmr_form.errors)
            print("dfmritem_formset.errors")
            print(dfmritem_formset.errors)
        return redirect('home')
def UpdateWhseItem_DFMR(bin_loc, item_num, item_quan):
    whseitem_DFMR = Warehouse_Items.objects.get(bin_location=bin_loc, item_number=item_num, status="In Stock")
    whseitem_DFMR.quantity -= item_quan 
    whseitem_DFMR.save()
def AddDFMR_Transac(refnum, bin_loc, itemnum, itemquan):
    dfmr_transac = DFMR_Transaction.objects.create(
        reference_number=refnum,
        transaction_type="Defective Material",
        transaction_location=bin_loc,
        item_number=itemnum,
        item_quantity=itemquan)
    dfmr_transac.full_clean()
    dfmr_transac.save()
@login_required
@warehouse_required
def ReportDFMR_SelectItem(request):
    template_name = 'invsys/warehouse/WhseUpdate/ReportDFMR_SelectItem.html'
    whse_items = Warehouse_Items.objects.filter(status="In Stock").values(
        'bin_location__id',
        'bin_location__bin_location',
        'item_number__item_number',
        'item_number__item_desc',
        'item_number__item_cat__item_cat',
        'item_number__prod_class__prod_class',
        'item_number__uom__uom',
        'item_number__price',
        'quantity',)
    return render(request, template_name, {'whse_items': whse_items})

#--REPORT SYS ADJ--
@login_required
@warehouse_required
def ReportSysAdj(request):
    template_name = 'invsys/warehouse/WhseUpdate/ReportSysAdj.html'
    if request.method == 'GET':

        sa_form = SA_ReportForm(request.GET or None)
        sa_reports = SA_Report.objects.all() #Populating Initial Forms
        if len(sa_reports) > 0:
            next_scheduleid = SA_Report.objects.order_by('-report_num').first().report_num + 1
        else:
            next_scheduleid = 1
        saitem_formset = SA_Item_Formset(queryset=SA_Item.objects.none())

        iaf_whse_query = IAF_whse.objects.all().values(
            'id',
            'whse')

        return render(request, template_name, {
            'sa_form': sa_form,
            'saitem_formset': saitem_formset,
            'scheduleid':next_scheduleid,
            'iaf_whse_set':iaf_whse_query})
    
    elif request.method == 'POST' :
        sa_form = SA_ReportForm(request.POST)
        saitem_formset = SA_Item_Formset(request.POST, request.FILES)


        print(sa_form)
        print(saitem_formset)
        if sa_form.is_valid() and saitem_formset.is_valid():
            sa_report = sa_form.save(commit=False)
            sa_report.save()

            sa_items = []
            counter = 1
            for saitem_form in saitem_formset:
                if counter < len(saitem_formset):
                    sa_item = saitem_form.save(commit=False)
                    sa_item.report_num = sa_report
                    sa_item.save()
                    UpdateWhseItem_SA(sa_item.bin_location, sa_item.item_number, sa_item.item_quantity, sa_item.iaf_operator.operator)
                    if sa_item.iaf_operator.operator == "Subtract":
                        AddSA_Subt_Transac(sa_report.report_num, sa_item.bin_location.bin_location, sa_item.item_number, sa_item.item_quantity)
                    else:
                        AddSA_Add_Transac(sa_report.report_num, sa_item.bin_location.bin_location, sa_item.item_number, sa_item.item_quantity)
                    sa_items.append(sa_item)
                    counter += 1

            AddIAF_Report(sa_report.iaf_whse, "Change/Modify/Conversion", "System Adjustment", request.user, sa_items)
            DeleteWhseItemBin()

        else:
            print("sa_form.errors")
            print(sa_form.errors)
            print("saitem_formset.errors")
            print(saitem_formset.errors)
        return redirect('home')
def UpdateWhseItem_SA(bin_loc, item_num, item_quan, iaf_operator):
    whseitem_SA = Warehouse_Items.objects.get(bin_location=bin_loc, item_number=item_num, status="In Stock")
    if iaf_operator == "Subtract":
        whseitem_SA.quantity -= item_quan
    else:
        whseitem_SA.quantity += item_quan
    whseitem_SA.save()
def AddSA_Subt_Transac(refnum, bin_loc, itemnum, itemquan):
    sa_subt_transac = SA_Subt_Transaction.objects.create(
        reference_number=refnum,
        transaction_type="System Adjustment",
        transaction_location=bin_loc,
        item_number=itemnum,
        item_quantity=itemquan)
    sa_subt_transac.full_clean()
    sa_subt_transac.save()
def AddSA_Add_Transac(refnum, bin_loc, itemnum, itemquan):
    sa_add_transac = SA_Add_Transaction.objects.create(
        reference_number=refnum,
        transaction_type="System Adjustment",
        transaction_location=bin_loc,
        item_number=itemnum,
        item_quantity=itemquan)
    sa_add_transac.full_clean()
    sa_add_transac.save()
@login_required
@warehouse_required
def ReportSysAdj_SelectItem(request):
    template_name = 'invsys/warehouse/WhseUpdate/ReportSysAdj_SelectItem.html'
    whse_items = Warehouse_Items.objects.filter(status="In Stock").values(
        'bin_location__id',
        'bin_location__bin_location',
        'item_number__item_number',
        'item_number__item_desc',
        'item_number__item_cat__item_cat',
        'item_number__prod_class__prod_class',
        'item_number__uom__uom',
        'item_number__price',
        'quantity',)

    iafoperator_set = IAF_operator.objects.all().values('id', 'operator')
    return render(request, template_name, {'whse_items': whse_items, 'iafoperator_set':iafoperator_set})

#--DISMANTLE PROD--
@login_required
@warehouse_required
def DismantleProduct(request):
    template_name = 'invsys/warehouse/WhseUpdate/DismantleProduct.html'
    if request.method == 'GET':

        dismprod_form = Dismantle_ReportForm(request.GET or None, prefix='report')
        dismprod_reports = Dismantle_Report.objects.all() #Populating Initial Forms
        if len(dismprod_reports) > 0:
            next_scheduleid = Dismantle_Report.objects.order_by('-report_num').first().report_num + 1
        else:
            next_scheduleid = 1

        dismprod_prod_form = Dismantle_ProductForm(request.GET or None, prefix='prod')
        dismprod_item_formset = Dismantle_Item_Formset(queryset=Dismantle_Item.objects.none())
        
        iaf_whse_query = IAF_whse.objects.all().values(
            'id',
            'whse')

        return render(request, template_name, {
            'dismprod_form': dismprod_form,
            'dismprod_prod_form': dismprod_prod_form,
            'dismprod_item_formset':dismprod_item_formset,
            'scheduleid':next_scheduleid,
            'iaf_whse_set':iaf_whse_query})
    
    elif request.method == 'POST' :
        dismprod_form = Dismantle_ReportForm(request.POST, prefix='report')
        dismprod_prod_form = Dismantle_ProductForm(request.POST, prefix='prod')
        dismprod_item_formset = Dismantle_Item_Formset(request.POST, request.FILES)
        
        if dismprod_form.is_valid() and dismprod_prod_form.is_valid() and dismprod_item_formset.is_valid():
            dismprod_report = dismprod_form.save(commit=False)
            dismprod_report.save()

            dism_prods = []
            dismprod_prod = dismprod_prod_form.save(commit=False)
            dismprod_prod.report_num = dismprod_report
            dismprod_prod.iaf_operator = IAF_operator.objects.get(operator="Subtract")
            dismprod_prod.save()
            UpdateWhse_prod_Dismantle(dismprod_prod.bin_location, dismprod_prod.prod_sched.id, dismprod_prod.prod_quantity)
            DeleteWhseProdBin()
            AddDismProd_Transac(dismprod_prod.prod_sched.id, dismprod_prod.bin_location.bin_location, dismprod_prod.prod_sched.work_order_number.prod_number, dismprod_prod.prod_quantity)
            dism_prods.append(dismprod_prod)
            iaf_report = AddIAF_Report_DismProd(dismprod_report.iaf_whse, "Change/Modify/Conversion", "Product Dismantling", request.user, dism_prods)

            dism_items = []
            counter = 1
            tot_item_quan = 0
            for dismproditem_form in dismprod_item_formset:
                if counter < len(dismprod_item_formset):
                    dismprod_item = dismproditem_form.save(commit=False)
                    dismprod_item.report_num = dismprod_report
                    dismprod_item.prod_sched = dismprod_prod.prod_sched
                    dismprod_item.bin_location = dismprod_prod.bin_location
                    dismprod_item.iaf_operator = IAF_operator.objects.get(operator="Add")
                    dismprod_item.reason = dismprod_prod.reason
                    dismprod_item.save()
                    AddtoReceivingLobby_DismProd(dismprod_prod.prod_sched.id, dismprod_item.item_number, dismprod_item.item_quantity)
                    AddDismItem_Transac(dismprod_prod.prod_sched.id, dismprod_item.bin_location.bin_location, dismprod_item.item_number, dismprod_item.item_quantity)
                    dism_items.append(dismprod_item)
                    counter += 1

            for item in dism_items:
                AddIAFItems(iaf_report.report_num, item.item_number, item.bin_location, item.item_quantity, item.iaf_operator, item.total_cost, item.reason)
                if item.iaf_operator.operator == "Subtract": 
                    AddIAF_Subt_Transac(iaf_report.report_num, "Product Dismantling", item.bin_location.bin_location, item.item_number, item.item_quantity)
                else:
                    AddIAF_Add_Transac(iaf_report.report_num, "Product Dismantling", item.bin_location.bin_location, item.item_number, item.item_quantity)
        else:
            print("dismprod_form.errors")
            print(dismprod_form.errors)
            print("dismprod_prod_form.errors")
            print(dismprod_prod_form.errors)
            print("dismprod_item_formset.errors")
            print(dismprod_item_formset.errors)
        return redirect('home')
def AddIAF_Report_DismProd(whse, report_type, report_action, user, prod_set):
    iaf_report = IAF_Report.objects.create(
        iaf_whse=whse,
        adjustment_type= IAF_code.objects.get(iaf_adjustment=report_type),
        iaf_action=report_action,
        prepared_by=user)
    iaf_report.full_clean()
    iaf_report.save()

    for prod in prod_set:
        AddIAF_DismProd(iaf_report.report_num, prod.prod_sched.work_order_number.prod_number, prod.bin_location, prod.prod_quantity, prod.iaf_operator, prod.total_cost, prod.reason)
        if prod.iaf_operator.operator == "Subtract": 
            AddIAF_Subt_Transac_DismProd(iaf_report.report_num, report_action, prod.bin_location.bin_location, prod.prod_sched.work_order_number.prod_number, prod.prod_quantity)
    return iaf_report
def AddIAF_Subt_Transac_DismProd(refnum, report_action, bin_loc, prod_number, prod_quantity):
    iaf_subt_transac = IAF_Prod_Subt_Transaction.objects.create(
        reference_number=refnum,
        transaction_type=report_action,
        transaction_location=bin_loc,
        prod_number=prod_number,
        prod_quantity=prod_quantity)
    iaf_subt_transac.full_clean()
    iaf_subt_transac.save()
def AddIAF_DismProd(report_num, prod_number, bin_loc, prod_quantity, iaf_operator, tot_cost, reason):
    iaf_prod = IAF_Prod.objects.create(
        report_num=IAF_Report.objects.get(report_num=report_num),
        prod_number=prod_number,
        bin_location=bin_loc,
        prod_quantity=prod_quantity,
        iaf_operator=iaf_operator,
        total_cost=tot_cost,
        reason=reason)
    iaf_prod.full_clean()
    iaf_prod.save()
def AddDismItem_Transac(prod_sched, bin_loc, item_num, item_quan):
    dismitem_transac = Dismantle_Item_Transaction.objects.create(
        reference_number=prod_sched,
        transaction_type="Product Dismantling",
        transaction_location=bin_loc,
        item_number=item_num,
        item_quantity=item_quan)
    dismitem_transac.full_clean()
    dismitem_transac.save()
def AddtoReceivingLobby_DismProd(refnum,itemnum,recquan):
    r = Receiving_Lobby.objects.create(
        reference_number=refnum, 
        item_number=itemnum,
        received_quantity=recquan,
        scheduled_quantity=0,
        status="Waiting for Put Away")
    r.full_clean()
    r.save()
    RecordRecLobbyTransac_DismProd(refnum,itemnum,recquan)
def RecordRecLobbyTransac_DismProd(refnum,itemnum,itemquan):
    rtransac = RecLobby_Transaction.objects.create(
        reference_number=refnum,
        transaction_type="Item from Product Dismantling",
        transaction_location="Receiving Lobby",
        item_number=itemnum,
        item_quantity=itemquan)
    rtransac.full_clean()
    rtransac.save()
def UpdateWhse_prod_Dismantle(bin_loc, prod_sched, dism_quan):
    whseprod_dismantle = Warehouse_Products.objects.get(bin_location=bin_loc, reference_number=prod_sched, status="In Stock")
    whseprod_dismantle.quantity -= int(dism_quan)
    whseprod_dismantle.save()
def DeleteWhseProdBin():
    whseprodset = Warehouse_Products.objects.order_by('quantity')
    for whsebin in whseprodset:
        if whsebin.quantity == 0:
            whsebin.delete()
def AddDismProd_Transac(prod_sched, bin_loc, prod_num, prod_quan):
    dismprod_transac = Dismantle_Product_Transaction.objects.create(
        reference_number=prod_sched,
        transaction_type="Product Dismantling",
        transaction_location=bin_loc,
        prod_number=prod_num,
        prod_quantity=prod_quan)
    dismprod_transac.full_clean()
    dismprod_transac.save()
@login_required
@warehouse_required
def DismantleProduct_SelectProduct(request):
    template_name = 'invsys/warehouse/WhseUpdate/DismantleProduct_SelectProduct.html'
    whse_prods = Warehouse_Products.objects.filter(status="In Stock").values(
        'bin_location__id',
        'bin_location__bin_location',
        'prod_number__prod_number',
        'prod_number__prod_desc',
        'prod_number__prod_class__prod_class',
        'prod_number__uom__uom',
        'prod_number__price',
        'quantity',
        'reference_number',)
    prod_query = Warehouse_Products.objects.filter(status="In Stock")
    prodsched_list = []
    for prod in prod_query:
        prodsched_list.append(prod.reference_number)
    prodsched_set = WO_Production_Schedule.objects.filter(id__in=prodsched_list).values(
        'id',
        'work_order_number__work_order_number',)
    prodsched_query = WO_Production_Schedule.objects.filter(id__in=prodsched_list)
    wo_list = []
    for wo in prodsched_query:
        wo_list.append(wo.work_order_number)
    wo_itemlist_set = Work_Order_Item_List.objects.filter(work_order_number__in=wo_list).values(
        'work_order_number__work_order_number',
        'item_number__item_number',
        'item_number__item_cat__item_cat',
        'item_number__prod_class__prod_class',
        'item_number__price',
        'item_quantity',)
    return render(request, template_name, {'whse_prods': whse_prods, 'prodsched_set':prodsched_set, 'wo_itemlist_set':wo_itemlist_set})

#--Transfer Item--
@login_required
@warehouse_required
def TransferItem(request):
    template_name =  'invsys/warehouse/WhseUpdate/TransferItem.html'
    if request.method == 'GET':

        transfer_form = Transfer_ReportForm(request.GET or None)
        transfer_reports = Transfer_Report.objects.all() #Populating Initial Forms
        if len(transfer_reports) > 0:
            next_reportid = Transfer_Report.objects.order_by('-report_num').first().report_num + 1
        else:
            next_reportid = 1
        transferitem_formset = Transfer_Item_Formset(queryset=Transfer_Item.objects.none())
        
        iaf_whse_query = IAF_whse.objects.all().values(
            'id',
            'whse')

        return render(request, template_name, {
            'transfer_form': transfer_form,
            'transferitem_formset': transferitem_formset,
            'reportid':next_reportid,
            'iaf_whse_set':iaf_whse_query})

    elif request.method == 'POST' :
        
        transfer_form = Transfer_ReportForm(request.POST)
        print(transfer_form)
        
        if transfer_form.is_valid():

            transfer_report = transfer_form.save(commit=False)
            transfer_report.save()

            transferitem_formset = Transfer_Item_Formset(request.POST, request.FILES)
            print(transferitem_formset)
            if transferitem_formset.is_valid():

                transfer_items = []
                counter = 1
                for transferitem_form in transferitem_formset:
                    if counter < len(transferitem_formset):
                        transfer_item = transferitem_form.save(commit=False)
                        transfer_item.report_num = transfer_report
                        transfer_item.save()
                        UpdateWhseItem_Transfer(transfer_item.bin_location, transfer_item.item_number, transfer_item.item_quantity, transfer_item.iaf_operator.operator)
                        if transfer_item.iaf_operator.operator == "Subtract":
                            AddTransfer_Subt_Transac(transfer_report.report_num, transfer_item.bin_location.bin_location, transfer_item.item_number, transfer_item.item_quantity)
                            pass
                        else:
                            pass
                            AddTransfer_Add_Transac(transfer_report.report_num, transfer_item.bin_location.bin_location, transfer_item.item_number, transfer_item.item_quantity)
                        transfer_items.append(transfer_item)
                        counter += 1

                AddIAF_Report(transfer_report.iaf_whse, "Change/Modify/Conversion", "Transfer Item", request.user, transfer_items)
                DeleteWhseItemBin()

            else:
                print("transferitem_formset.errors")
                print(transferitem_formset.errors)

        else:
            print("transfer_form.errors")
            print(transfer_form.errors)
            
        return redirect('home')

def UpdateWhseItem_Transfer(bin_loc, item_num, item_quan, iaf_operator):
    try:
        whseitem_Transfer = Warehouse_Items.objects.get(bin_location=bin_loc, item_number=item_num, status="In Stock")
        if iaf_operator == "Subtract":
            whseitem_Transfer.quantity -= item_quan
        else:
            whseitem_Transfer.quantity += item_quan
        whseitem_Transfer.save()
    except whseitem_Transfer.DoesNotExist: #There are no item in whse bin to transfer
        whseitem_New = Warehouse_Items.objects.create(
            bin_location=bin_loc,
            item_number=item_num,
            quantity=item_quan,
            status="In Stock",
            reference_number="None")
        whseitem_New.full_clean()
        whseitem_New.save()

def AddTransfer_Subt_Transac(refnum, bin_loc, itemnum, itemquan):
    transfer_subt_transac = Transfer_Subt_Transaction.objects.create(
        reference_number=refnum,
        transaction_type="Transfer Item",
        transaction_location=bin_loc,
        item_number=itemnum,
        item_quantity=itemquan)
    transfer_subt_transac.full_clean()
    transfer_subt_transac.save()
def AddTransfer_Add_Transac(refnum, bin_loc, itemnum, itemquan):
    transfer_add_transac = Transfer_Add_Transaction.objects.create(
        reference_number=refnum,
        transaction_type="Transfer Item",
        transaction_location=bin_loc,
        item_number=itemnum,
        item_quantity=itemquan)
    transfer_add_transac.full_clean()
    transfer_add_transac.save()

@login_required
@warehouse_required
def TransferItem_SelectItem(request):
    template_name = 'invsys/warehouse/WhseUpdate/TransferItem_SelectItem.html'

    whse_items_query = Warehouse_Items.objects.filter(status="In Stock")

    item_list = []
    for whse_item in whse_items_query:
        item_list.append(whse_item.item_number)

    whse_bin_query = Warehouse_Items.objects.filter(status="In Stock").values(
        'bin_location__id',
        'bin_location__bin_location',
        'bin_location__item_cat__item_cat',
        'bin_location__prod_class__prod_class',
        'bin_location__barcode',
        'item_number__item_number',
        'quantity',)

    item_query = Item.objects.filter(item_number__in=item_list).values(
        'item_number',
        'item_desc',
        'uom__uom',
        'item_cat__item_cat',
        'prod_class__prod_class',
        'barcode',
        'price',
        'notes',
        'orderpoint',
        'image')

    new_whse_bin_query = Warehouse.objects.all().values(
        'id',
        'bin_location',
        'item_cat__item_cat',
        'prod_class__prod_class',
        'barcode',)

    new_whse_item_query = Warehouse_Items.objects.filter(status="In Stock").values(
        'bin_location__id',
        'bin_location__bin_location',
        'bin_location__item_cat__item_cat',
        'bin_location__prod_class__prod_class',
        'bin_location__barcode',
        'item_number__item_number',
        'quantity',)

    return render(request, template_name, {
        'whse_bin_set': whse_bin_query,
        'item_set': item_query,
        'new_whse_bin_set':new_whse_bin_query,
        'new_whse_item_set':new_whse_item_query})

#Inventory Review
#--Generate Cycle Count Schedule--
@login_required
@warehouse_required
def GenerateCCSchedule(request):
    return render(request, 'invsys/warehouse/InvReview/GenerateCCSchedule.html')
#--Finish Cycle Count--
@login_required
@warehouse_required
def FinishCycleCount(request):
    return render(request, 'invsys/warehouse/InvReview/FinishCycleCount.html')
#--View Accomplished Cycle Count Schedule--
@login_required
@warehouse_required
def ViewCycleCountSummary(request):
    return render(request, 'invsys/warehouse/InvReview/ViewCycleCountSummary.html')


#--UPDATE PURCHASE ORDERS---
@login_required
@warehouse_required
def UpdatePO(request):
    template_name ='invsys/warehouse/Receiving/UpdatePO.html'
    if request.method == 'GET':
        ponumformset = Purchase_Order_Formset(queryset=Purchase_Order.objects.none(), prefix='formsetpo')
        ponum_itemformset = Purchase_Order_Item_Formset(queryset=Purchase_Order_Item.objects.none(), prefix='formsetitem')
        return render(request, template_name, {'ponumformset': ponumformset,'ponum_itemformset': ponum_itemformset})
    elif request.method == 'POST':

        ponumformset = Purchase_Order_Formset(request.POST , request.FILES, prefix='formsetpo')

        if ponumformset.is_valid():
            #Saves the PO Num
            counter = 1
            for po_num_form in ponumformset:
                if counter < len(ponumformset):
                    po_num = po_num_form.save(commit=False)
                    po_num.save()
                    counter += 1


            ponum_itemformset = Purchase_Order_Item_Formset(request.POST , request.FILES, prefix='formsetitem')
            print(ponum_itemformset)
            if ponum_itemformset.is_valid():
                counter = 1
                for po_item_form in ponum_itemformset: #Saves the po items in a list
                    if counter < len(ponum_itemformset):
                        po_item = po_item_form.save(commit=False)
                        po_item.item_number = Item.objects.get(item_number=po_item.item_number)
                        po_item.po_number = Purchase_Order.objects.get(po_number=po_item.po_number)
                        po_item.save()
                        counter += 1

            else:
                print("ponum_itemformset.errors")
                print(ponum_itemformset.errors)
                return redirect('home')

                
            return redirect('home')

        else:
            print("ponumformset.errors")
            print(ponumformset.errors)
            return redirect('home')     
        

#--VIEW OPEN PO---
@login_required
@warehouse_required
def ViewOpenPO(request):
    template_name ='invsys/warehouse/Receiving/ViewOpenPO.html'

    po_rec_query = Purchase_Order.objects.filter(cleared=False,issues=True).values(
        'po_number',
        'purchase_date',
        'notes',
        'issues',)

    po_list = []
    for po in po_rec_query:
        po_list.append(po.get('po_number'))

    ship_po_query = Shipment_PO.objects.filter(po_num__po_number__in=po_list).values(
        'id',
        'po_num__po_number')

    ship_po_list = []
    for ship_po in ship_po_query:
        ship_po_list.append(ship_po.get('id'))

    ship_sum_query = Shipment_Summary.objects.filter(shipment_po__id__in=ship_po_list).values(
        'shipment_po__po_num__supplier',
        'shipment_po__po_num__purchase_date',
        'shipment_po__po_num__po_number',
        'item_number__item_number',
        'item_number__item_desc',
        'purchased_quantity',
        'total_received_quantity',)


    openpo_list = []
    for ship_sum in ship_sum_query:
        details={}
        po_num = 0
        purch_quan = 0
        tot_rec_quan = 0
        for i in ship_sum:
            if i == 'shipment_po__po_num__supplier':
                details['supplier'] = ship_sum[i]
            elif i == 'shipment_po__po_num__purchase_date':
                details['purch_date'] = ship_sum[i]
            elif i == 'shipment_po__po_num__po_number':
                po_num = ship_sum[i]
                details['po_num'] = ship_sum[i]
            elif i == 'item_number__item_number':
                details['item_number'] = ship_sum[i]
            elif i == 'item_number__item_desc':
                details['item_desc'] = ship_sum[i]
            elif i == 'purchased_quantity':
                purch_quan = ship_sum[i]
                details['purch_quan'] = ship_sum[i]
            elif i == 'total_received_quantity':
                tot_rec_quan = ship_sum[i]
                details['tot_rec_quan'] = ship_sum[i]
        details['balance'] = int(purch_quan) - int(tot_rec_quan)
        latest_ship_query = Receive_Shipment_Item.objects.filter(shipment_po__po_num__po_number=po_num).order_by('-date_validated').values(
            'date_validated').first()        
        details['date_shipped'] = latest_ship_query.get('date_validated')
        openpo_list.append(details)


    po_notrec_query = Purchase_Order.objects.filter(cleared=False,issues=False).values(
        'po_number',
        'purchase_date',
        'notes',
        'issues',)

    po_notrec_list = []
    for po in po_notrec_query:
        po_notrec_list.append(po.get('po_number'))

    po_item_query = Purchase_Order_Item.objects.filter(po_number__po_number__in=po_notrec_list).values(
        'po_number__supplier',
        'po_number__purchase_date',
        'po_number__po_number',
        'item_number__item_number',
        'item_number__item_desc',
        'item_quantity',)

    for po_item in po_item_query:
        details={}
        purch_quan = 0
        for i in po_item:
            if i == 'po_number__supplier':
                details['supplier'] = po_item[i]
            elif i == 'po_number__purchase_date':
                details['purch_date'] = po_item[i]
            elif i == 'po_number__po_number':
                details['po_num'] = po_item[i]
            elif i == 'item_number__item_number':
                details['item_number'] = po_item[i]
            elif i == 'item_number__item_desc':
                details['item_desc'] = po_item[i]
            elif i == 'item_quantity':
                purch_quan = po_item[i]
                details['purch_quan'] = po_item[i]
        details['tot_rec_quan'] = 0
        details['balance'] = purch_quan
        details['date_shipped'] = None
        openpo_list.append(details)

    return render(request, template_name, {'openpo_set':openpo_list })

#--VIEW CLOSED PO---
@login_required
@warehouse_required
def ViewClosedPO(request):
    template_name ='invsys/warehouse/Receiving/ViewClosedPO.html'

    po_rec_query = Purchase_Order.objects.filter(cleared=True).values(
        'po_number',
        'purchase_date',
        'notes',
        'issues',)

    po_list = []
    for po in po_rec_query:
        po_list.append(po.get('po_number'))

    ship_po_query = Shipment_PO.objects.filter(po_num__po_number__in=po_list).values(
        'id',
        'po_num__po_number')

    ship_po_list = []
    for ship_po in ship_po_query:
        ship_po_list.append(ship_po.get('id'))

    ship_sum_query = Shipment_Summary.objects.filter(shipment_po__id__in=ship_po_list).values(
        'shipment_po__po_num__supplier',
        'shipment_po__po_num__purchase_date',
        'shipment_po__po_num__po_number',
        'item_number__item_number',
        'item_number__item_desc',
        'purchased_quantity',
        'total_received_quantity',)


    closedpo_list = []
    for ship_sum in ship_sum_query:
        details={}
        po_num = 0
        purch_quan = 0
        tot_rec_quan = 0
        for i in ship_sum:
            if i == 'shipment_po__po_num__supplier':
                details['supplier'] = ship_sum[i]
            elif i == 'shipment_po__po_num__purchase_date':
                details['purch_date'] = ship_sum[i]
            elif i == 'shipment_po__po_num__po_number':
                po_num = ship_sum[i]
                details['po_num'] = ship_sum[i]
            elif i == 'item_number__item_number':
                details['item_number'] = ship_sum[i]
            elif i == 'item_number__item_desc':
                details['item_desc'] = ship_sum[i]
            elif i == 'purchased_quantity':
                purch_quan = ship_sum[i]
                details['purch_quan'] = ship_sum[i]
            elif i == 'total_received_quantity':
                tot_rec_quan = ship_sum[i]
                details['tot_rec_quan'] = ship_sum[i]
        details['balance'] = int(purch_quan) - int(tot_rec_quan)
        latest_ship_query = Receive_Shipment_Item.objects.filter(shipment_po__po_num__po_number=po_num).order_by('-date_validated').values(
            'date_validated').first()        
        details['date_shipped'] = latest_ship_query.get('date_validated')
        closedpo_list.append(details)

    return render(request, template_name, {'closedpo_set':closedpo_list })

#--VIEW RESOLVED PO---
@login_required
@warehouse_required
def ViewResolvedPO(request):
    template_name ='invsys/warehouse/Receiving/ViewResolvedPO.html'

    po_resolve_query = ResolvePO.objects.filter().values(
        'po_num__po_number',
        'date_resolved',
        'notes',)

    po_resolve_list = []
    for po in po_resolve_query:
        po_resolve_list.append(po.get('po_num__po_number'))

    ship_sum_query = Shipment_Summary.objects.filter(shipment_po__po_num__po_number__in=po_resolve_list).values(
        'shipment_po__po_num__supplier',
        'shipment_po__po_num__purchase_date',
        'shipment_po__po_num__po_number',
        'item_number__item_number',
        'item_number__item_desc',
        'purchased_quantity',
        'total_received_quantity',)


    resolvedpo_list = []
    for ship_sum in ship_sum_query:
        details={}
        po_num = 0
        purch_quan = 0
        tot_rec_quan = 0
        for i in ship_sum:
            if i == 'shipment_po__po_num__supplier':
                details['supplier'] = ship_sum[i]
            elif i == 'shipment_po__po_num__purchase_date':
                details['purch_date'] = ship_sum[i]
            elif i == 'shipment_po__po_num__po_number':
                po_num = ship_sum[i]
                details['po_num'] = ship_sum[i]
            elif i == 'item_number__item_number':
                details['item_number'] = ship_sum[i]
            elif i == 'item_number__item_desc':
                details['item_desc'] = ship_sum[i]
            elif i == 'purchased_quantity':
                purch_quan = ship_sum[i]
                details['purch_quan'] = ship_sum[i]
            elif i == 'total_received_quantity':
                tot_rec_quan = ship_sum[i]
                details['tot_rec_quan'] = ship_sum[i]
        details['balance'] = int(purch_quan) - int(tot_rec_quan)
        latest_ship_query = Receive_Shipment_Item.objects.filter(shipment_po__po_num__po_number=po_num).order_by('-date_validated').values(
            'date_validated').first()        
        details['date_shipped'] = latest_ship_query.get('date_validated')
        resolvedpo_list.append(details)

    return render(request, template_name, {'resolvedpo_set':resolvedpo_list })



#--WAREHOUSE ADJUSTMENTS--
@login_required
@warehouse_required
def WarehouseAdjustments(request):
    template_name ='invsys/warehouse/WhseUpdate/WarehouseAdjustments.html'
    if request.method == 'GET':
        iaf_report_list = IAF_Report.objects.filter().values(
            'report_num',
            'iaf_whse__whse',
            'adjustment_type__iaf_code',
            'iaf_action',
            'date_requested',
            'date_approved',
            'date_adjusted',
            'prepared_by',
            'noted_by',)
        iaf_item_list = IAF_Item.objects.filter().values(
            'report_num__report_num',
            'report_num__iaf_whse__whse',
            'item_number__item_number',
            'bin_location__bin_location',
            'item_quantity',
            'iaf_operator__operator',
            'total_cost',
            'reason',
            'report_num__adjustment_type__iaf_code',
            'report_num__iaf_action',
            'report_num__date_requested',
            'report_num__date_approved',
            'report_num__date_adjusted',
            'report_num__prepared_by',
            'report_num__noted_by',)
        iaf_prod_list = IAF_Prod.objects.filter().values(
            'report_num__report_num',
            'report_num__iaf_whse__whse',
            'prod_number__prod_number',
            'bin_location__bin_location',
            'prod_quantity',
            'iaf_operator__operator',
            'total_cost',
            'reason',
            'report_num__adjustment_type__iaf_code',
            'report_num__iaf_action',
            'report_num__date_requested',
            'report_num__date_approved',
            'report_num__date_adjusted',
            'report_num__prepared_by',
            'report_num__noted_by',)
        return render(request, template_name, 
            {'iaf_report_set':iaf_report_list, 
            'iaf_item_set':iaf_item_list,
            'iaf_prod_set':iaf_prod_list,})
        
    elif request.method == 'POST':

        return redirect('home')

#YourModel.objects.filter(YOUR_DATE_FIELD__date=timezone.now())
#samples = Sample.objects.filter(sampledate__gte=datetime.date(2011, 1, 1), sampledate__lte=datetime.date(2011, 1, 31))
#Model.objects.filter(start__lte=qend, end__gte=qstart)
#Sample.objects.filter(date__range=["2011-01-01", "2011-01-31"])
#dates_2011_2013 = [ start_date + datetime.timedelta(n) for n in range(int ((end_date - start_date).days))]

def perdelta(start, end, delta):
    date_list = []
    date_iter = start

    while end > date_iter:
        date_list.append(date_iter)
        date_iter += delta
        if end < date_iter:
            date_list.append(end)

    return date_list

#--SAMPLE UPDATE--
def Dashboard_get_data(request):
    start_date = dt.date(2020, 1, 1)
    now = dt.datetime.now()
    end_date = dt.datetime.strptime(now.strftime("%Y-%m-%d"),'%Y-%m-%d').date()

    date_list = perdelta(start_date, end_date, timedelta(days=25))

    count = []
    counter = 0
    for date in date_list:
        if counter < len(date_list) - 1:
            count.append(Purchase_Order.objects.filter(purchase_date__range=[date, date_list[counter+1]]).count())
            counter += 1
        else:
            count.append(Purchase_Order.objects.filter(purchase_date__range=[date_list[counter-1], date]).count())
            counter += 1

    data = {
        "labels" : date_list,
        "default" : count,
    }
    return JsonResponse(data) # http response
def Dashboard_update_data(request):
    files = request.POST

    start_date = dt.datetime.strptime(files.get("from"), '%Y-%m-%d').date()
    end_date = dt.datetime.strptime(files.get("to"), '%Y-%m-%d').date()

    date_list = perdelta(start_date, end_date, timedelta(days=25))

    count = []
    counter = 0
    for date in date_list:
        if counter < len(date_list) - 1:
            count.append(Purchase_Order.objects.filter(purchase_date__range=[date, date_list[counter+1]]).count())
            counter += 1
        else:
            count.append(Purchase_Order.objects.filter(purchase_date__range=[date_list[counter-1], date]).count())
            counter += 1

    print(date_list)
    print(count)

    data = {
        "labels" : date_list,
        "default" : count,
    }
    return JsonResponse(data) # http response

#WHSE UTIL
def Dashboard_get_whseutil(request):
    whse_query = Warehouse.objects.all().values('bin_location')

    whse_item_query = Warehouse_Items.objects.all().values('bin_location__bin_location').distinct('bin_location__bin_location')
    whse_prod_query = Warehouse_Products.objects.all().values('bin_location__bin_location').distinct('bin_location__bin_location')

    whse_item = []
    for item in whse_item_query:
        whse_item.append(item.get('bin_location__bin_location'))

    whse_prod = []
    for prod in whse_prod_query:
        whse_prod.append(prod.get('bin_location__bin_location'))

    whseitem_query = set(whse_item)
    whseprod_query = set(whse_prod)

    total_whsebin = 0
    loaded_whsebin = 0

    for whsebin in whse_query:
        if whsebin.get('bin_location') in whseitem_query: #bin is with items
            loaded_whsebin += 1

        elif whsebin.get('bin_location') in whseprod_query: #bin is with products
            loaded_whsebin += 1

        total_whsebin += 1

    total_whsebin -= loaded_whsebin

    data = {
        "total_whsebin" : total_whsebin,
        "loaded_whsebin" : loaded_whsebin,
    }
    return JsonResponse(data) # http response

#RECEIVING DASHBOARD
def Dashboard_get_purchinbound(request):
    inbound_query = InboundLobby.objects.all().values('shipment_num__shipment_num')

    shipment_list = []
    for inbound in inbound_query:
        shipment_list.append( inbound.get('shipment_num__shipment_num') )

    shipo_query = Shipment_PO.objects.filter(shipment_num__shipment_num__in=shipment_list).values('validated')

    for_receiving = 0
    validated = 0

    for shipo in shipo_query:
        if shipo.get('validated') == True: #bin is with items
            validated += 1

        for_receiving += 1

    for_receiving -= validated

    data = {
        "for_receiving" : for_receiving,
        "validated" : validated,
    }
    return JsonResponse(data) # http response


def Dashboard_get_purchstatus(request):
    po_query = Purchase_Order.objects.all().values('po_number', 'cleared', 'issues')

    open_po = 0
    closed_po = 0
    vdr_po = 0

    for po in po_query:
        if po.get('cleared') == True: #po is cleared
            closed_po += 1
        if po.get('cleared') == False and po.get('issues') == True:
            vdr_po += 1
        if po.get('cleared') == False and po.get('issues') == False:
            open_po += 1

    data = {
        "open_po" : open_po,
        "closed_po" : closed_po,
        "vdr_po" : vdr_po,
    }
    return JsonResponse(data) # http response

#PUTAWAY DASHBOARD
def Dashboard_get_putaway(request):
    reclobby_query = Receiving_Lobby.objects.all()

    pa_pending = 0
    pa_scheduled = 0

    for reclobby in reclobby_query:
        pa_pending += (reclobby.received_quantity - reclobby.scheduled_quantity)

    paitem_query = Put_Away_Items.objects.filter(stored=False).values('required_quantity')

    for paitem in paitem_query:
        pa_scheduled += paitem.get('required_quantity')

    data = {
        "pa_pending" : pa_pending,
        "pa_scheduled" : pa_scheduled,
    }
    return JsonResponse(data) # http response

#COMP ISSUANCE DASHBOARD
def Dashboard_get_compissuance(request):
    prodsched_query = WO_Production_Schedule.objects.filter(scheduled=False)

    comp_pending = 0
    comp_sched = 0
    comp_issued = 0

    for prodsched in prodsched_query:
        comp_pending += 1

    woissuancesched_query = WO_Issuance_Schedule.objects.filter(cleared=False).values('schedule_num')

    sched_list = []
    for woissuancesched in woissuancesched_query:
        sched_list.append( woissuancesched.get('schedule_num') )

    woissuancelist_query = WO_Issuance_List.objects.filter(schedule_num__schedule_num__in=sched_list).values('cleared')

    for woissuancelist in woissuancelist_query:
        if woissuancelist.get('cleared') == True:
            comp_issued += 1
        elif woissuancelist.get('cleared') == False:
            comp_sched += 1

    data = {
        "comp_pending" : comp_pending,
        "comp_sched" : comp_sched,
        "comp_issued": comp_issued,
    }
    return JsonResponse(data) # http response

#PART REQUEST DASHBOARD
def Dashboard_get_partreq(request):
    partreq_query = Warehouse_Items.objects.filter(status="Allocated for Part Request")

    partreq_pending = 0
    partreq_sched = 0
    partreq_issued = 0

    for partreq in partreq_query:
        partreq_pending += partreq.quantity

    requestsched_query = Request_Schedule.objects.filter(cleared=False).values('schedule_num')

    reqsched_list = []
    for requestsched in requestsched_query:
        reqsched_list.append( requestsched.get('schedule_num') )

    requestitem_query = Request_Item.objects.filter(schedule_num__schedule_num__in=reqsched_list).values('quantity','cleared')

    for requestitem in requestitem_query:

        if requestitem.get('cleared') == True:
            partreq_issued += requestitem.get('quantity')
        else:
            partreq_sched += requestitem.get('quantity')

    data = {
        "partreq_pending" : partreq_pending,
        "partreq_sched" : partreq_sched,
        "partreq_issued": partreq_issued,
    }
    return JsonResponse(data) # http response

#PART RETURN DASHBOARD
def Dashboard_get_partret(request):
    assdiscitems_query = Assembly_Discrepancy.objects.filter(status="Waiting for Return")

    partret_pending = 0
    partret_sched = 0
    partret_issued = 0

    for assdiscitems in assdiscitems_query:
        partret_pending += assdiscitems.quantity

    returnsched_query = ComponentReturn_Schedule.objects.filter(cleared=False).values('schedule_num')

    retsched_list = []
    for returnsched in returnsched_query:
        retsched_list.append( returnsched.get('schedule_num') )

    returnitem_query = ComponentReturn_Item.objects.filter(schedule_num__schedule_num__in=retsched_list).values('quantity','cleared')

    for returnitem in returnitem_query:

        if returnitem.get('cleared') == True:
            partret_issued += returnitem.get('quantity')
        else:
            partret_sched += returnitem.get('quantity')


    data = {
        "partret_pending" : partret_pending,
        "partret_sched" : partret_sched,
        "partret_issued": partret_issued,
    }
    return JsonResponse(data) # http response

#PRODUCT RECEIVE DASHBOARD
def Dashboard_get_prodrec(request):
    prodsched_finishlist = WO_Finished.objects.filter(cleared=False)

    prodrec_pending = 0
    prodrec_received = 0

    for prodsched in prodsched_finishlist:
        prodrec_pending += 1

    now = datetime.now().replace(tzinfo=pytz.utc)

    prodsched_received_query = WO_Finished.objects.filter(cleared=True, date_out=now)

    for prodsched_received in prodsched_received_query:
        prodrec_received += 1

    data = {
        "prodrec_pending" : prodrec_pending,
        "prodrec_received" : prodrec_received,
    }
    return JsonResponse(data) # http response


#PRODUCT SHIP DASHBOARD
def Dashboard_get_prodship(request):
    ship_lobby_query = Shipping_Lobby.objects.all()

    prodship_pending = 0
    prodship_shipped = 0

    for ship_lobby in ship_lobby_query:
        prodship_pending += 1

    now = datetime.now().replace(tzinfo=pytz.utc)

    ship_out_query = Shipping_Outbound.objects.filter(date_out=now)

    for ship_out in ship_out_query:
        prodship_shipped += 1

    data = {
        "prodship_pending" : prodship_pending,
        "prodship_shipped" : prodship_shipped,
    }
    return JsonResponse(data) # http response


#SAMPLE CALENDAR
def calendar(request):
    if request.method == 'GET':
        template_name = 'invsys/warehouse/Shipping/Calendar.html'
        all_events = Events.objects.all()

        return render(request, template_name, 
            {'events':all_events})
    elif request.method == 'POST' :
        return redirect('home')
def add_event(request):
    wo_num = request.POST.get("wo_num")
    prod_sched_set = json.loads(request.POST.get('prod_sched_set[]'))

    print(wo_num)    

    count = 0
    title =''
    date = ''
    wo_num = ''
    print(prod_sched_set)
    for prod_sched in prod_sched_set:
        print(prod_sched)
        for details in prod_sched:
            if count == 0:
                title = details
                print(title)
                count += 1
            elif count == 1:
                date = datetime.datetime.strptime(details, '%Y-%m-%d')
                tz = timezone.get_current_timezone()
                timzone_date = timezone.make_aware(date, tz, True)
                print(date)
                count += 1
            else:
                wo_num = details
                print(wo_num)
                count += 1
        count = 0
        new_event = Events.objects.create(
            name=title,
            start=timzone_date,
            end=timzone_date,
            event_type=wo_num)
        new_event.full_clean()
        new_event.save()

    #title = request.GET.get("title", None)
    #event = Events(name=str(title), start=start, end=end)
    #event.save()
    data = {}
    return JsonResponse(data)

#WHSE LOCATIONS
@login_required
@warehouse_required
def CheckInboundLobby(request):
    template_name = 'invsys/warehouse/WhseLoc/CheckInboundLobby.html'
    inbound_lobby_query = InboundLobby.objects.all().values(
        'shipment_num__shipment_num',
        'date_in',
        'shipment_num__dr_num',
        'shipment_num__rr_num',
        'shipment_num__invoice_num',
        'shipment_num__ship_trucking',
        'shipment_num__ship_category',
        'shipment_num__container_num',
        'shipment_num__container_type',
        'shipment_num__awl_bl',
        'shipment_num__notes',
        'shipment_num__date_dr',
        'shipment_num__date_warehouse',)

    shipment_list = []
    for shipment in inbound_lobby_query:
        shipment_list.append(shipment.get('shipment_num__shipment_num'))

    shipment_query = Shipment.objects.filter(shipment_num__in=shipment_list).values(
        'shipment_num',
        'dr_num',
        'rr_num',
        'invoice_num',
        'ship_trucking',
        'ship_category',
        'container_num',
        'container_type',
        'awl_bl',
        'notes',
        'date_dr',
        'date_warehouse',)

    po_list = []
    for ship_po in shipment_query:
        po_list.append(ship_po.get('shipment_num'))

    po_query = Shipment_PO.objects.filter(shipment_num__in=po_list, validated=False).values(
        'shipment_num__shipment_num',
        'po_num__po_number',
        'po_num__purchase_date',
        'po_num__notes',
        'po_num__supplier',)

    return render(request, template_name, {
        'inbound_lobby_set':inbound_lobby_query,
        'po_set':po_query})

@login_required
@warehouse_required
def CheckReceivingLobby(request):
    template_name = 'invsys/warehouse/WhseLoc/CheckReceivingLobby.html'
    rec_lobby_query = Receiving_Lobby.objects.filter().values(
        'reference_number',
        'item_number__item_number',
        'item_number__item_desc',
        'received_quantity',
        'scheduled_quantity',
        'date_received',
        'time_received',
        'status')

    refnum_list = []
    
    for refnum in rec_lobby_query:
        refnum_list.append(refnum.get('reference_number'))

    po_query = Purchase_Order.objects.all()

    reclobby_list = []

    for po in po_query:
        for ref in rec_lobby_query:
            if po.po_number == ref.get('reference_number'):
                details={}
                for i in ref:
                    details[i] = ref[i]
                details['type'] = 'Purchase Order'
                reclobby_list.append(details)

    woprodsched_query = WO_Production_Schedule.objects.all()

    for woprodsched in woprodsched_query:
        for ref in rec_lobby_query:
            if int(woprodsched.id) == int(ref.get('reference_number')):
                print("TRUE")
                details={}
                for i in ref:
                    details[i] = ref[i]
                details['type'] = 'Item from Product'
                reclobby_list.append(details)

    return render(request, template_name, {
        'rec_lobby_set':reclobby_list})

@login_required
@warehouse_required
def CheckVDRLobby(request):
    template_name = 'invsys/warehouse/WhseLoc/CheckVDRLobby.html'
    vdr_lobby_query = VDR_Lobby.objects.filter().values(
        'po_number',
        'item_number__item_number',
        'item_number__item_desc',
        'purchased_quantity',
        'received_quantity',
        'date_received',
        'time_received',
        'status')
    return render(request, template_name, {
        'vdr_lobby_set':vdr_lobby_query})

@login_required
@warehouse_required
def CheckWarehouse(request):
    template_name = 'invsys/warehouse/WhseLoc/CheckWarehouse.html'
    whse_bin_query = Warehouse.objects.filter().values(
        'bin_location',
        'item_cat__item_cat',
        'prod_class__prod_class',
        'barcode')
    whse_item_query = Warehouse_Items.objects.filter().values(
        'bin_location__bin_location',
        'item_number__item_number',
        'quantity',
        'status',
        'reference_number')
    whse_product_query = Warehouse_Products.objects.filter().values(
        'bin_location__bin_location',
        'prod_number__prod_number',
        'quantity',
        'status',
        'reference_number')

    item_cat_query = ItemCat.objects.all().exclude(item_cat="Product").values(
        'id',
        'item_cat')

    prod_class_query = ProdClass.objects.all().values(
        'id',
        'prod_class')

    return render(request, template_name, {
        'whse_bin_set':whse_bin_query,
        'whse_item_set':whse_item_query,
        'whse_product_set':whse_product_query,
        'item_cat_set':item_cat_query,
        'prod_class_set':prod_class_query})

@login_required
@warehouse_required
def CheckWarehouse_getImage(request):
    files = request.POST

    bin_loc_ajax = files.get("bin_loc")
    bin_loc_obj = Warehouse.objects.filter(bin_location=bin_loc_ajax).values(
        'image')

    bin_loc_image = ""

    for bin_loc in bin_loc_obj:
        bin_loc_image = "/media/" + bin_loc.get("image")

        
    data = {
        "image" : bin_loc_image,
    }

    return JsonResponse(data) # http response

@login_required
@warehouse_required
def CheckAssemblyItem(request):
    template_name = 'invsys/warehouse/WhseLoc/CheckAssemblyItem.html'
    ass_item_query = Assembly_Items.objects.filter().values(
        'assemblyline__name',
        'item_number__item_number',
        'item_number__item_desc',
        'quantity',
        'status',
        'reference_number')

    return render(request, template_name, {
        'ass_item_set':ass_item_query}) 

@login_required
@warehouse_required
def CheckAssemblyDiscrepancy(request):
    template_name = 'invsys/warehouse/WhseLoc/CheckAssemblyDiscrepancy.html'
    ass_disc_query = Assembly_Discrepancy.objects.filter().values(
        'assemblyline__name',
        'item_number__item_number',
        'item_number__item_desc',
        'quantity',
        'status',
        'reference_number')

    return render(request, template_name, {
        'ass_disc_set':ass_disc_query})

@login_required
@warehouse_required
def CheckShippingLobby(request):
    template_name = 'invsys/warehouse/WhseLoc/CheckShippingLobby.html'
    ship_lobby_query = Shipping_Lobby.objects.filter().values(
        'prod_sched__id',
        'prod_number__prod_number',
        'prod_number__prod_desc',
        'quantity',
        'date_received',
        'received_by',
        'checked_by',
        'notes')

    return render(request, template_name, {
        'ship_lobby_set':ship_lobby_query})



#VIEW INVENTORY
@login_required
@warehouse_required
def CheckItem(request):
    template_name = 'invsys/warehouse/ViewInventory/CheckItem.html'

    item_query = Item.objects.all().values(
        'item_number',
        'item_desc',
        'uom__uom',
        'item_cat__item_cat',
        'prod_class__prod_class',
        'barcode',
        'price',
        'notes',
        'orderpoint',
        'image')

    rec_lobby_query = Receiving_Lobby.objects.filter().values(
        'reference_number',
        'item_number__item_number',
        'item_number__item_desc',
        'received_quantity',
        'scheduled_quantity',
        'date_received',
        'time_received',
        'status')

    vdr_lobby_query = VDR_Lobby.objects.filter().values(
        'po_number',
        'item_number__item_number',
        'item_number__item_desc',
        'purchased_quantity',
        'received_quantity',
        'date_received',
        'time_received',
        'status')

    whse_item_query = Warehouse_Items.objects.filter().values(
        'bin_location__bin_location',
        'item_number__item_number',
        'quantity',
        'status',
        'reference_number')

    ass_item_query = Assembly_Items.objects.filter().values(
        'assemblyline__name',
        'item_number__item_number',
        'quantity',
        'status',
        'reference_number')

    ass_disc_query = Assembly_Discrepancy.objects.filter().values(
        'assemblyline__name',
        'item_number__item_number',
        'item_number__item_desc',
        'quantity',
        'status',
        'reference_number')

    item_list = []
    for item in rec_lobby_query:
        details={}
        details['location'] = 'Receiving Lobby'
        for i in item:
            if i == "reference_number":
                details['reference_number'] = item[i]
            elif i == "item_number__item_number":
                details['item_number'] = item[i]
            elif i == 'received_quantity':
                details['quantity'] = item[i]
            elif i == 'status':
                details['status'] = item[i]

        item_list.append(details)

    for item in vdr_lobby_query:
        details={}
        details['location'] = 'VDR Lobby'
        for i in item:
            if i == 'po_number':
                details['reference_number'] = item[i]
            elif i == 'item_number__item_number':
                details['item_number'] = item[i]
            elif i == 'received_quantity':
                details['quantity'] = item[i]
            elif i == 'status':
                details['status'] = item[i]
        item_list.append(details)

    for item in whse_item_query:
        details={}
        for i in item:
            if i == 'bin_location__bin_location':
                details['location'] = item[i]
            elif i == 'item_number__item_number':
                details['item_number'] = item[i]
            elif i == 'quantity':
                details['quantity'] = item[i]
            elif i == 'status':
                details['status'] = item[i]
            elif i == 'reference_number':
                details['reference_number'] = item[i]
        item_list.append(details)

    for item in ass_item_query:
        details={}
        for i in item:
            if i == 'assemblyline__name':
                details['location'] = item[i]
            elif i == 'item_number__item_number':
                details['item_number'] = item[i]
            elif i == 'quantity':
                details['quantity'] = item[i]
            elif i == 'status':
                details['status'] = item[i]
            elif i == 'reference_number':
                details['reference_number'] = item[i]
        item_list.append(details)

    for item in ass_disc_query:
        details={}
        for i in item:
            if i == 'assemblyline__name':
                details['location'] = item[i]
            elif i == 'item_number__item_number':
                details['item_number'] = item[i]
            elif i == 'quantity':
                details['quantity'] = item[i]
            elif i == 'status':
                details['status'] = item[i]
            elif i == 'reference_number':
                details['reference_number'] = item[i]
        item_list.append(details)

    item_cat_query = ItemCat.objects.all().exclude(item_cat="Product").values(
            'id',
            'item_cat')

    prod_class_query = ProdClass.objects.all().values(
        'id',
        'prod_class')

    return render(request, template_name, { 
        'item_master_set':item_query,
        'item_cat_set':item_cat_query,
        'prod_class_set':prod_class_query,
        'item_loc_set':item_list })

@login_required
@warehouse_required
def CheckProduct(request):
    template_name = 'invsys/warehouse/ViewInventory/CheckProduct.html'

    prod_query = Product.objects.all().values(
        'prod_number',
        'prod_desc',
        'uom__uom',
        'prod_type',
        'prod_class__prod_class',
        'barcode',
        'price',
        'notes',
        'image')

    whse_product_query = Warehouse_Products.objects.filter().values(
        'bin_location__bin_location',
        'prod_number__prod_number',
        'quantity',
        'status',
        'reference_number')
    
    ship_lobby_query = Shipping_Lobby.objects.filter().values(
        'prod_sched__id',
        'prod_number__prod_number',
        'prod_number__prod_desc',
        'quantity',
        'date_received',
        'received_by',
        'checked_by',
        'notes')

    prod_list = []
    for item in whse_product_query:
        details={}
        for i in item:
            if i == 'bin_location__bin_location':
                details['location'] = item[i]
            elif i == 'prod_number__prod_number':
                details['prod_number'] = item[i]
            elif i == 'quantity':
                details['quantity'] = item[i]
            elif i == 'status':
                details['status'] = item[i]
            elif i == 'reference_number':
                details['reference_number'] = item[i]
        prod_list.append(details)

    for item in ship_lobby_query:
        details={}
        details['location'] = "Shipping Lobby"
        details['status'] = "Waiting for Shipping"
        for i in item:
            if i == 'prod_sched__id':
                details['reference_number'] = item[i]
            elif i == 'prod_number__prod_number':
                details['prod_number'] = item[i]
            elif i == 'quantity':
                details['quantity'] = item[i]                   
        prod_list.append(details)

    prod_class_query = ProdClass.objects.all().exclude(prod_class="None").values(
        'id',
        'prod_class')

    return render(request, template_name, {
        'prod_master_set':prod_query,
        'prod_loc_set':prod_list,
        'prod_class_set':prod_class_query})

@login_required
@warehouse_required
def ViewItemTransactions(request):
    template_name = 'invsys/warehouse/ViewInventory/ViewItemTransactions.html'

    item_query = Item.objects.all().values(
        'item_number',
        'item_desc',
        'uom__uom',
        'item_cat__item_cat',
        'prod_class__prod_class',
        'barcode',
        'price',
        'notes',
        'orderpoint',
        'image')

    itemtrans_list = []

    #RECEIVING TRANSACTIONS
    recship_trans = Shipment_Transaction.objects.filter().values(
        'reference_number',
        'transaction_type',
        'transaction_date',
        'transaction_location',
        'item_number',
        'item_quantity',)
    reclobby_trans = RecLobby_Transaction.objects.filter().values(
        'reference_number',
        'transaction_type',
        'transaction_date',
        'transaction_location',
        'item_number',
        'item_quantity',)
    vdrlobby_trans = VDRLobby_Transaction.objects.filter().values(
        'reference_number',
        'transaction_type',
        'transaction_date',
        'transaction_location',
        'item_number',
        'item_quantity',)
    vdrtorec_trans = VDR_To_Receiving_Transaction.objects.filter().values(
        'reference_number',
        'transaction_type',
        'transaction_date',
        'transaction_location',
        'item_number',
        'item_quantity',)

    #RECEIVING 
    for recship in recship_trans:
        details={}
        for i in recship:
            if i == 'reference_number':
                details['reference_number'] = recship[i]
            elif i == 'transaction_type':
                details['transaction_type'] = recship[i]
            elif i == 'transaction_date':
                details['transaction_date'] = recship[i]
            elif i == 'transaction_location':
                details['transaction_location'] = recship[i]
            elif i == 'item_number':
                details['item_number'] = recship[i]
            elif i == 'item_quantity':
                details['item_quantity'] = recship[i]
        itemtrans_list.append(details)
    for reclobby in reclobby_trans:
        details={}
        for i in reclobby:
            if i == 'reference_number':
                details['reference_number'] = reclobby[i]
            elif i == 'transaction_type':
                details['transaction_type'] = reclobby[i]
            elif i == 'transaction_date':
                details['transaction_date'] = reclobby[i]
            elif i == 'transaction_location':
                details['transaction_location'] = reclobby[i]
            elif i == 'item_number':
                details['item_number'] = reclobby[i]
            elif i == 'item_quantity':
                details['item_quantity'] = reclobby[i]
        itemtrans_list.append(details)
    for vdrlobby in vdrlobby_trans:
        details={}
        for i in vdrlobby:
            if i == 'reference_number':
                details['reference_number'] = vdrlobby[i]
            elif i == 'transaction_type':
                details['transaction_type'] = vdrlobby[i]
            elif i == 'transaction_date':
                details['transaction_date'] = vdrlobby[i]
            elif i == 'transaction_location':
                details['transaction_location'] = vdrlobby[i]
            elif i == 'item_number':
                details['item_number'] = vdrlobby[i]
            elif i == 'item_quantity':
                details['item_quantity'] = vdrlobby[i]
        itemtrans_list.append(details)
    for vdrtorec in vdrtorec_trans:
        details={}
        for i in vdrtorec:
            if i == 'reference_number':
                details['reference_number'] = vdrtorec[i]
            elif i == 'transaction_type':
                details['transaction_type'] = vdrtorec[i]
            elif i == 'transaction_date':
                details['transaction_date'] = vdrtorec[i]
            elif i == 'transaction_location':
                details['transaction_location'] = vdrtorec[i]
            elif i == 'item_number':
                details['item_number'] = vdrtorec[i]
            elif i == 'item_quantity':
                details['item_quantity'] = vdrtorec[i]
        itemtrans_list.append(details)

    #PUT AWAY TRANSACTIONS
    pa_sched_trans = Put_Away_Schedule_Transaction.objects.filter().values(
        'reference_number',
        'transaction_type',
        'transaction_date',
        'transaction_location',
        'item_number',
        'item_quantity',)
    pa_sum_trans = Put_Away_Finish_Transaction.objects.filter().values(
        'reference_number',
        'transaction_type',
        'transaction_date',
        'transaction_location',
        'item_number',
        'item_quantity',)

    #PUT AWAY
    for pa_sched in pa_sched_trans:
        details={}
        for i in pa_sched:
            if i == 'reference_number':
                details['reference_number'] = pa_sched[i]
            elif i == 'transaction_type':
                details['transaction_type'] = pa_sched[i]
            elif i == 'transaction_date':
                details['transaction_date'] = pa_sched[i]
            elif i == 'transaction_location':
                details['transaction_location'] = pa_sched[i]
            elif i == 'item_number':
                details['item_number'] = pa_sched[i]
            elif i == 'item_quantity':
                details['item_quantity'] = pa_sched[i]
        itemtrans_list.append(details)
    for pa_sum in pa_sum_trans:
        details={}
        for i in pa_sum:
            if i == 'reference_number':
                details['reference_number'] = pa_sum[i]
            elif i == 'transaction_type':
                details['transaction_type'] = pa_sum[i]
            elif i == 'transaction_date':
                details['transaction_date'] = pa_sum[i]
            elif i == 'transaction_location':
                details['transaction_location'] = pa_sum[i]
            elif i == 'item_number':
                details['item_number'] = pa_sum[i]
            elif i == 'item_quantity':
                details['item_quantity'] = pa_sum[i]
        itemtrans_list.append(details)

    #WO ISSUANCE TRANSACTIONS
    woissuance_sched_trans = WO_Allocation_Transaction.objects.filter().values(
        'reference_number',
        'transaction_type',
        'transaction_date',
        'transaction_location',
        'item_number',
        'item_quantity',)
    woissuance_sum_trans = WO_Issuance_Finish_Transaction.objects.filter().values(
        'reference_number',
        'transaction_type',
        'transaction_date',
        'transaction_location',
        'item_number',
        'item_quantity',)
    woissuance_disc_trans = WO_Issuance_Disc_Transaction.objects.filter().values(
        'reference_number',
        'transaction_type',
        'transaction_date',
        'transaction_location',
        'item_number',
        'item_quantity',)

    #WO ISSUANCE
    for woissuance_sched in woissuance_sched_trans:
        details={}
        for i in woissuance_sched:
            if i == 'reference_number':
                details['reference_number'] = woissuance_sched[i]
            elif i == 'transaction_type':
                details['transaction_type'] = woissuance_sched[i]
            elif i == 'transaction_date':
                details['transaction_date'] = woissuance_sched[i]
            elif i == 'transaction_location':
                details['transaction_location'] = woissuance_sched[i]
            elif i == 'item_number':
                details['item_number'] = woissuance_sched[i]
            elif i == 'item_quantity':
                details['item_quantity'] = woissuance_sched[i]
        itemtrans_list.append(details)
    for woissuance_sum in woissuance_sum_trans:
        details={}
        for i in woissuance_sum:
            if i == 'reference_number':
                details['reference_number'] = woissuance_sum[i]
            elif i == 'transaction_type':
                details['transaction_type'] = woissuance_sum[i]
            elif i == 'transaction_date':
                details['transaction_date'] = woissuance_sum[i]
            elif i == 'transaction_location':
                details['transaction_location'] = woissuance_sum[i]
            elif i == 'item_number':
                details['item_number'] = woissuance_sum[i]
            elif i == 'item_quantity':
                details['item_quantity'] = woissuance_sum[i]
        itemtrans_list.append(details)
    for woissuance_disc in woissuance_disc_trans:
        details={}
        for i in woissuance_disc:
            if i == 'reference_number':
                details['reference_number'] = woissuance_disc[i]
            elif i == 'transaction_type':
                details['transaction_type'] = woissuance_disc[i]
            elif i == 'transaction_date':
                details['transaction_date'] = woissuance_disc[i]
            elif i == 'transaction_location':
                details['transaction_location'] = woissuance_disc[i]
            elif i == 'item_number':
                details['item_number'] = woissuance_disc[i]
            elif i == 'item_quantity':
                details['item_quantity'] = woissuance_disc[i]
        itemtrans_list.append(details)

    #PRODUCT CONVERSION TRANSACTIONS
    itemtoprod_trans = RecProduct_Item_Transaction.objects.filter().values(
        'reference_number',
        'transaction_type',
        'transaction_date',
        'transaction_location',
        'item_number',
        'item_quantity',)

    #PRODUCT CONVERSION
    for itemtoprod in itemtoprod_trans:
        details={}
        for i in itemtoprod:
            if i == 'reference_number':
                details['reference_number'] = itemtoprod[i]
            elif i == 'transaction_type':
                details['transaction_type'] = itemtoprod[i]
            elif i == 'transaction_date':
                details['transaction_date'] = itemtoprod[i]
            elif i == 'transaction_location':
                details['transaction_location'] = itemtoprod[i]
            elif i == 'item_number':
                details['item_number'] = itemtoprod[i]
            elif i == 'item_quantity':
                details['item_quantity'] = itemtoprod[i]
        itemtrans_list.append(details)

    #SHRINKAGE TRANSACTION
    shrnk_report_trans = Shrinkage_Ass_Report_Transaction.objects.filter().values(
        'reference_number',
        'transaction_type',
        'transaction_date',
        'transaction_location',
        'item_number',
        'item_quantity',)
    shrnk_item_trans = Shrinkage_Ass_Item_Transaction.objects.filter().values(
        'reference_number',
        'transaction_type',
        'transaction_date',
        'transaction_location',
        'item_number',
        'item_quantity',)

    #SHRINKAGE
    for shrnk_report in shrnk_report_trans:
        details={}
        for i in shrnk_report:
            if i == 'reference_number':
                details['reference_number'] = shrnk_report[i]
            elif i == 'transaction_type':
                details['transaction_type'] = shrnk_report[i]
            elif i == 'transaction_date':
                details['transaction_date'] = shrnk_report[i]
            elif i == 'transaction_location':
                details['transaction_location'] = shrnk_report[i]
            elif i == 'item_number':
                details['item_number'] = shrnk_report[i]
            elif i == 'item_quantity':
                details['item_quantity'] = shrnk_report[i]
        itemtrans_list.append(details)
    for shrnk_item in shrnk_item_trans:
        details={}
        for i in shrnk_item:
            if i == 'reference_number':
                details['reference_number'] = shrnk_item[i]
            elif i == 'transaction_type':
                details['transaction_type'] = shrnk_item[i]
            elif i == 'transaction_date':
                details['transaction_date'] = shrnk_item[i]
            elif i == 'transaction_location':
                details['transaction_location'] = shrnk_item[i]
            elif i == 'item_number':
                details['item_number'] = shrnk_item[i]
            elif i == 'item_quantity':
                details['item_quantity'] = shrnk_item[i]
        itemtrans_list.append(details)

    #PART REQUEST TRANSACTION
    partreq_sched_trans = Request_Schedule_Transaction.objects.filter().values(
        'reference_number',
        'transaction_type',
        'transaction_date',
        'transaction_location',
        'item_number',
        'item_quantity',)
    partreq_sum_trans = Request_Finish_Transaction.objects.filter().values(
        'reference_number',
        'transaction_type',
        'transaction_date',
        'transaction_location',
        'item_number',
        'item_quantity',)
    partreq_disc_trans = Request_DiscSummary_Transaction.objects.filter().values(
        'reference_number',
        'transaction_type',
        'transaction_date',
        'transaction_location',
        'item_number',
        'item_quantity',)

    #PART REQUEST
    for partreq_sched in partreq_sched_trans:
        details={}
        for i in partreq_sched:
            if i == 'reference_number':
                details['reference_number'] = partreq_sched[i]
            elif i == 'transaction_type':
                details['transaction_type'] = partreq_sched[i]
            elif i == 'transaction_date':
                details['transaction_date'] = partreq_sched[i]
            elif i == 'transaction_location':
                details['transaction_location'] = partreq_sched[i]
            elif i == 'item_number':
                details['item_number'] = partreq_sched[i]
            elif i == 'item_quantity':
                details['item_quantity'] = partreq_sched[i]
        itemtrans_list.append(details)
    for partreq_sum in partreq_sum_trans:
        details={}
        for i in partreq_sum:
            if i == 'reference_number':
                details['reference_number'] = partreq_sum[i]
            elif i == 'transaction_type':
                details['transaction_type'] = partreq_sum[i]
            elif i == 'transaction_date':
                details['transaction_date'] = partreq_sum[i]
            elif i == 'transaction_location':
                details['transaction_location'] = partreq_sum[i]
            elif i == 'item_number':
                details['item_number'] = partreq_sum[i]
            elif i == 'item_quantity':
                details['item_quantity'] = partreq_sum[i]
        itemtrans_list.append(details)
    for partreq_disc in partreq_disc_trans:
        details={}
        for i in partreq_disc:
            if i == 'reference_number':
                details['reference_number'] = partreq_disc[i]
            elif i == 'transaction_type':
                details['transaction_type'] = partreq_disc[i]
            elif i == 'transaction_date':
                details['transaction_date'] = partreq_disc[i]
            elif i == 'transaction_location':
                details['transaction_location'] = partreq_disc[i]
            elif i == 'item_number':
                details['item_number'] = partreq_disc[i]
            elif i == 'item_quantity':
                details['item_quantity'] = partreq_disc[i]
        itemtrans_list.append(details)

    #COMPONENT RETURN TRANSACTION
    compret_sched_trans = ComponentReturn_Schedule_Transaction.objects.filter().values(
        'reference_number',
        'transaction_type',
        'transaction_date',
        'transaction_location',
        'item_number',
        'item_quantity',)
    compret_sum_trans = ComponentReturn_Summary_Transaction.objects.filter().values(
        'reference_number',
        'transaction_type',
        'transaction_date',
        'transaction_location',
        'item_number',
        'item_quantity',)

    #COMPONENT RETURN
    for compret_sched in compret_sched_trans:
        details={}
        for i in compret_sched:
            if i == 'reference_number':
                details['reference_number'] = compret_sched[i]
            elif i == 'transaction_type':
                details['transaction_type'] = compret_sched[i]
            elif i == 'transaction_date':
                details['transaction_date'] = compret_sched[i]
            elif i == 'transaction_location':
                details['transaction_location'] = compret_sched[i]
            elif i == 'item_number':
                details['item_number'] = compret_sched[i]
            elif i == 'item_quantity':
                details['item_quantity'] = compret_sched[i]
        itemtrans_list.append(details)
    for compret_sum in compret_sum_trans:
        details={}
        for i in compret_sum:
            if i == 'reference_number':
                details['reference_number'] = compret_sum[i]
            elif i == 'transaction_type':
                details['transaction_type'] = compret_sum[i]
            elif i == 'transaction_date':
                details['transaction_date'] = compret_sum[i]
            elif i == 'transaction_location':
                details['transaction_location'] = compret_sum[i]
            elif i == 'item_number':
                details['item_number'] = compret_sum[i]
            elif i == 'item_quantity':
                details['item_quantity'] = compret_sum[i]
        itemtrans_list.append(details)

    #WHSE UPDATE TRANSACTIONS
    dmmr_trans = DMMR_Transaction.objects.filter().values(
        'reference_number',
        'transaction_type',
        'transaction_date',
        'transaction_location',
        'item_number',
        'item_quantity',)
    dfmr_trans = DFMR_Transaction.objects.filter().values(
        'reference_number',
        'transaction_type',
        'transaction_date',
        'transaction_location',
        'item_number',
        'item_quantity',)
    sa_sub_trans = SA_Subt_Transaction.objects.filter().values(
        'reference_number',
        'transaction_type',
        'transaction_date',
        'transaction_location',
        'item_number',
        'item_quantity',)
    sa_add_trans = SA_Add_Transaction.objects.filter().values(
        'reference_number',
        'transaction_type',
        'transaction_date',
        'transaction_location',
        'item_number',
        'item_quantity',)
    dism_item_trans = Dismantle_Item_Transaction.objects.filter().values(
        'reference_number',
        'transaction_type',
        'transaction_date',
        'transaction_location',
        'item_number',
        'item_quantity',)

    #WHSE UPDATE
    for dmmr in dmmr_trans:
        details={}
        for i in dmmr:
            if i == 'reference_number':
                details['reference_number'] = dmmr[i]
            elif i == 'transaction_type':
                details['transaction_type'] = dmmr[i]
            elif i == 'transaction_date':
                details['transaction_date'] = dmmr[i]
            elif i == 'transaction_location':
                details['transaction_location'] = dmmr[i]
            elif i == 'item_number':
                details['item_number'] = dmmr[i]
            elif i == 'item_quantity':
                details['item_quantity'] = dmmr[i]
        itemtrans_list.append(details)
    for dfmr in dfmr_trans:
        details={}
        for i in dfmr:
            if i == 'reference_number':
                details['reference_number'] = dfmr[i]
            elif i == 'transaction_type':
                details['transaction_type'] = dfmr[i]
            elif i == 'transaction_date':
                details['transaction_date'] = dfmr[i]
            elif i == 'transaction_location':
                details['transaction_location'] = dfmr[i]
            elif i == 'item_number':
                details['item_number'] = dfmr[i]
            elif i == 'item_quantity':
                details['item_quantity'] = dfmr[i]
        itemtrans_list.append(details)
    for sa_sub in sa_sub_trans:
        details={}
        for i in sa_sub:
            if i == 'reference_number':
                details['reference_number'] = sa_sub[i]
            elif i == 'transaction_type':
                details['transaction_type'] = sa_sub[i]
            elif i == 'transaction_date':
                details['transaction_date'] = sa_sub[i]
            elif i == 'transaction_location':
                details['transaction_location'] = sa_sub[i]
            elif i == 'item_number':
                details['item_number'] = sa_sub[i]
            elif i == 'item_quantity':
                details['item_quantity'] = sa_sub[i]
        itemtrans_list.append(details)
    for sa_add in sa_add_trans:
        details={}
        for i in sa_add:
            if i == 'reference_number':
                details['reference_number'] = sa_add[i]
            elif i == 'transaction_type':
                details['transaction_type'] = sa_add[i]
            elif i == 'transaction_date':
                details['transaction_date'] = sa_add[i]
            elif i == 'transaction_location':
                details['transaction_location'] = sa_add[i]
            elif i == 'item_number':
                details['item_number'] = sa_add[i]
            elif i == 'item_quantity':
                details['item_quantity'] = sa_add[i]
        itemtrans_list.append(details)
    for dism_item in dism_item_trans:
        details={}
        for i in dism_item:
            if i == 'reference_number':
                details['reference_number'] = dism_item[i]
            elif i == 'transaction_type':
                details['transaction_type'] = dism_item[i]
            elif i == 'transaction_date':
                details['transaction_date'] = dism_item[i]
            elif i == 'transaction_location':
                details['transaction_location'] = dism_item[i]
            elif i == 'item_number':
                details['item_number'] = dism_item[i]
            elif i == 'item_quantity':
                details['item_quantity'] = dism_item[i]
        itemtrans_list.append(details)

    item_cat_query = ItemCat.objects.all().exclude(item_cat="Product").values(
        'id',
        'item_cat')

    prod_class_query = ProdClass.objects.all().values(
        'id',
        'prod_class')

    return render(request, template_name, {
        'item_master_set':item_query,
        "itemtrans_set":itemtrans_list,
        'item_cat_set':item_cat_query,
        'prod_class_set':prod_class_query})

@login_required
@warehouse_required
def ViewProductTransactions(request):
    template_name = 'invsys/warehouse/ViewInventory/ViewProductTransactions.html'

    prod_query = Product.objects.all().values(
        'prod_number',
        'prod_desc',
        'uom__uom',
        'prod_type',
        'prod_class__prod_class',
        'barcode',
        'price',
        'notes',
        'image',)

    prodtrans_list = []

    #NEW PRODUCT TRANSACTIONS
    newprod_trans = RecProduct_Product_Transaction.objects.filter().values(
        'reference_number',
        'transaction_type',
        'transaction_date',
        'transaction_location',
        'prod_number',
        'prod_quantity',)
    prod_shiplobby_trans = RecProduct_ProductToShipLobby_Transaction.objects.filter().values(
        'reference_number',
        'transaction_type',
        'transaction_date',
        'transaction_location',
        'prod_number',
        'prod_quantity',)
    prod_whse_trans = RecProduct_ProductToWhse_Transaction.objects.filter().values(
        'reference_number',
        'transaction_type',
        'transaction_date',
        'transaction_location',
        'prod_number',
        'prod_quantity',)

    for newprod in newprod_trans:
        details={}
        for i in newprod:
            if i == 'reference_number':
                details['reference_number'] = newprod[i]
            elif i == 'transaction_type':
                details['transaction_type'] = newprod[i]
            elif i == 'transaction_date':
                details['transaction_date'] = newprod[i]
            elif i == 'transaction_location':
                details['transaction_location'] = newprod[i]
            elif i == 'prod_number':
                details['prod_number'] = newprod[i]
            elif i == 'prod_quantity':
                details['prod_quantity'] = newprod[i]
        prodtrans_list.append(details)
    for prod_shiplobby in prod_shiplobby_trans:
        details={}
        for i in prod_shiplobby:
            if i == 'reference_number':
                details['reference_number'] = prod_shiplobby[i]
            elif i == 'transaction_type':
                details['transaction_type'] = prod_shiplobby[i]
            elif i == 'transaction_date':
                details['transaction_date'] = prod_shiplobby[i]
            elif i == 'transaction_location':
                details['transaction_location'] = prod_shiplobby[i]
            elif i == 'prod_number':
                details['prod_number'] = prod_shiplobby[i]
            elif i == 'prod_quantity':
                details['prod_quantity'] = prod_shiplobby[i]
        prodtrans_list.append(details)
    for prod_whse in prod_whse_trans:
        details={}
        for i in prod_whse:
            if i == 'reference_number':
                details['reference_number'] = prod_whse[i]
            elif i == 'transaction_type':
                details['transaction_type'] = prod_whse[i]
            elif i == 'transaction_date':
                details['transaction_date'] = prod_whse[i]
            elif i == 'transaction_location':
                details['transaction_location'] = prod_whse[i]
            elif i == 'prod_number':
                details['prod_number'] = prod_whse[i]
            elif i == 'prod_quantity':
                details['prod_quantity'] = prod_whse[i]
        prodtrans_list.append(details)

    #STORAGE OF PRODUCT TRANSACTION
    shipout_trans = Shipping_Outbound_Transaction.objects.filter().values(
        'reference_number',
        'transaction_type',
        'transaction_date',
        'transaction_location',
        'prod_number',
        'prod_quantity',)
    whsetoshiplobby_trans = Shipping_WhseProduct_Transaction.objects.filter().values(
        'reference_number',
        'transaction_type',
        'transaction_date',
        'transaction_location',
        'prod_number',
        'prod_quantity',)

    for shipout in shipout_trans:
        details={}
        for i in shipout:
            if i == 'reference_number':
                details['reference_number'] = shipout[i]
            elif i == 'transaction_type':
                details['transaction_type'] = shipout[i]
            elif i == 'transaction_date':
                details['transaction_date'] = shipout[i]
            elif i == 'transaction_location':
                details['transaction_location'] = shipout[i]
            elif i == 'prod_number':
                details['prod_number'] = shipout[i]
            elif i == 'prod_quantity':
                details['prod_quantity'] = shipout[i]
        prodtrans_list.append(details)
    for whsetoshiplobby in whsetoshiplobby_trans:
        details={}
        for i in whsetoshiplobby:
            if i == 'reference_number':
                details['reference_number'] = whsetoshiplobby[i]
            elif i == 'transaction_type':
                details['transaction_type'] = whsetoshiplobby[i]
            elif i == 'transaction_date':
                details['transaction_date'] = whsetoshiplobby[i]
            elif i == 'transaction_location':
                details['transaction_location'] = whsetoshiplobby[i]
            elif i == 'prod_number':
                details['prod_number'] = whsetoshiplobby[i]
            elif i == 'prod_quantity':
                details['prod_quantity'] = whsetoshiplobby[i]
        prodtrans_list.append(details)

    #WHSE UPDATE
    dism_prod_trans = Dismantle_Product_Transaction.objects.filter().values(
        'reference_number',
        'transaction_type',
        'transaction_date',
        'transaction_location',
        'prod_number',
        'prod_quantity',)

    for dism_prod in dism_prod_trans:
        details={}
        for i in dism_prod:
            if i == 'reference_number':
                details['reference_number'] = dism_prod[i]
            elif i == 'transaction_type':
                details['transaction_type'] = dism_prod[i]
            elif i == 'transaction_date':
                details['transaction_date'] = dism_prod[i]
            elif i == 'transaction_location':
                details['transaction_location'] = dism_prod[i]
            elif i == 'prod_number':
                details['prod_number'] = dism_prod[i]
            elif i == 'prod_quantity':
                details['prod_quantity'] = dism_prod[i]
        prodtrans_list.append(details)

    prod_class_query = ProdClass.objects.all().exclude(prod_class="None").values(
        'id',
        'prod_class')

    return render(request, template_name, {
        'prod_set':prod_query,
        "prodtrans_set":prodtrans_list,
        'prod_class_set':prod_class_query})


#--Edit Item
@login_required
@warehouse_required
def EditItem(request):
    template_name = 'invsys/warehouse/CheckInv/EditItem.html'
    if request.method == 'GET':
        item_query = Item.objects.all().values(
            'item_number',
            'item_desc',
            'uom__uom',
            'item_cat__item_cat',
            'prod_class__prod_class',
            'barcode',
            'price',
            'notes',
            'orderpoint',
            'image')

        item_cat_query = ItemCat.objects.all().exclude(item_cat="Product").values(
            'id',
            'item_cat')

        prod_class_query = ProdClass.objects.all().values(
            'id',
            'prod_class')

        return render(request, template_name, {
            'item_master_set':item_query,
            'item_cat_set':item_cat_query,
            'prod_class_set':prod_class_query})

    elif request.method == 'POST' :

        item_num_form = request.POST.get("item_number")

        item_obj = Item.objects.get(item_number=item_num_form)

        item_obj.price = request.POST.get("price")
        item_obj.notes = request.POST.get("notes")
        item_obj.orderpoint = request.POST.get("orderpoint")
        if len(request.FILES) != 0:
            item_obj.image = request.FILES["image"]
        item_obj.save()

        return redirect('home')

#--Edit Product
@login_required
@warehouse_required
def EditProduct(request):
    template_name = 'invsys/warehouse/CheckInv/EditProduct.html'
    if request.method == 'GET':

        prod_query = Product.objects.all().values(
            'prod_number',
            'prod_desc',
            'uom__uom',
            'prod_type',
            'prod_class__prod_class',
            'barcode',
            'price',
            'notes',
            'image')

        formset = ProductItemListFormset(queryset=ProductItemList.objects.none())

        prod_class_query = ProdClass.objects.all().exclude(prod_class="None").values(
            'id',
            'prod_class')

        return render(request, template_name, {
            'prod_master_set':prod_query,
            'formset': formset,
            'prod_class_set':prod_class_query})

    elif request.method == 'POST' :

        formset = ProductItemListFormset(request.POST)

        prod_num_form = request.POST.get("prod_num")
        prod_obj = Product.objects.get(prod_number=prod_num_form)

        prod_obj.price = request.POST.get("price")
        prod_obj.notes = request.POST.get("notes")

        if len(request.FILES) != 0:
            prod_obj.image = request.FILES["image"]

        prod_obj.save()

        if formset.is_valid():
            # Save the Product first before its items
            prod_item_list = ProductItemList.objects.filter(prod_number=prod_obj)

            for prod_item in prod_item_list:
                prod_item.delete()


            counter = 1
            for form in formset:
                if counter < len(formset):
                    #Loop through each form in the formset to get each of the items
                    part = form.save(commit=False)
                    part.prod_number = prod_obj
                    part.save()
                    counter += 1

        else:
            print(formset.errors)

        return redirect('home')

def EditProduct_getparts(request):

    files = request.POST

    prod_num = files.get("prod_num")

    proditem_query = ProductItemList.objects.filter(prod_number__prod_number=prod_num).values(
        'item_number__item_number',
        'quantity')

    proditem_list = []

    for proditem in proditem_query:
        proditem_list.append(proditem)

    data = {
        "proditem_set" : proditem_list,
    }

    return JsonResponse(data) # http response

@login_required
@warehouse_required
def EditProduct_SelectItem(request):
    itemset = Item.objects.all()
    return render(request, 'invsys/warehouse/CheckInv/EditProduct_SelectItem.html', {'itemset':itemset})


#--WAREHOUSE BIN
#--Create Warehouse Bin--
@login_required
@warehouse_required
def CreateWarehouseBin(request):
    if request.method == 'GET':

        whsebin_form = WarehouseBinForm(request.GET or None)

        itemcat_query = ItemCat.objects.all().order_by('item_cat').values(
            'id',
            'item_cat',)

        prodclass_query = ProdClass.objects.all().order_by('prod_class').values(
            'id',
            'prod_class',)

        return render(request, 'invsys/warehouse/CheckInv/CreateWarehouseBin.html', {
            'whsebin_form':whsebin_form,
            'itemcat_query':itemcat_query,
            'prodclass_query':prodclass_query,})

    elif request.method == 'POST' :
        whsebin_form = WarehouseBinForm(request.POST, request.FILES)

        if whsebin_form.is_valid():
            whsebin_obj = whsebin_form.save(commit=False)
            whsebin_obj.bin_location = whsebin_obj.rack + whsebin_obj.column + '-' + whsebin_obj.layer + whsebin_obj.direction
            whsebin_obj.save()           
        else:
            print("whsebin_obj")
            print(whsebin_obj.errors)

        return redirect('home')

@login_required
@warehouse_required
def EditWarehouseBin(request):
    template_name = 'invsys/warehouse/CheckInv/EditWarehouseBin.html'
    if request.method == 'GET':

        whsebin_query = Warehouse.objects.all().values(
            'bin_location',
            'item_cat__item_cat',
            'prod_class__prod_class',
            'image',)

        item_cat_query = ItemCat.objects.all().exclude(item_cat="Product").values(
            'id',
            'item_cat')

        prod_class_query = ProdClass.objects.all().values(
            'id',
            'prod_class')

        return render(request, template_name, {
            'whsebin_set':whsebin_query,
            'item_cat_set':item_cat_query,
            'prod_class_set':prod_class_query})

    elif request.method == 'POST' :

        whsebin_form = request.POST.get("bin_loc")

        whsebin_obj = Warehouse.objects.get(bin_location=whsebin_form)

        if len(request.FILES) != 0:
            whsebin_obj.image = request.FILES["image"]

        whsebin_obj.save()

        return redirect('home')

def EditWarehouseBin_getparts(request):

    whsebin_form = request.POST.get("bin_loc")

    whsebin_obj = Warehouse.objects.get(bin_location=whsebin_form)

    whse_products_list = []
    whse_items_list = []

    if whsebin_obj.item_cat.item_cat == "Product":

        whse_products_query = Warehouse_Products.objects.filter(bin_location__bin_location=whsebin_form).values(
            'prod_number__prod_number',
            'quantity',
            'status',
            'reference_number',)

        for whse_products in whse_products_query:
            whse_products_list.append(whse_products)
    
    else:

        whse_items_query = Warehouse_Items.objects.filter(bin_location__bin_location=whsebin_form).values(
            'item_number__item_number',
            'quantity',
            'status',
            'reference_number',)

        for whse_items in whse_items_query:
            whse_items_list.append(whse_items)


    data = { "whse_products_set" : whse_products_list,
    "whse_items_set" : whse_items_list, }

    return JsonResponse(data) # http response



#--- EXPORT RECEIVED SHIPMENTS
@login_required
@warehouse_required
def ExportReceivedShipment(request):
    template_name = 'invsys/warehouse/Receiving/ExportReceivedShipment.html'

    rec_shipment_query = Receive_Shipment_Item.objects.all().values(
        'id',
        'shipment_po__shipment_num__shipment_num',
        'shipment_po__shipment_num__date_dr',
        'shipment_po__shipment_num__date_warehouse',
        'date_validated',
        'start_time_validation',
        'end_time_validation',
        'validation_time',
        'shipment_po__po_num__supplier',
        'shipment_po__shipment_num__ship_category',
        'shipment_po__po_num__po_number',
        'item_number__item_number',
        'item_number__item_desc',
        'item_quantity',
        'item_number__uom__uom',
        'shipment_po__shipment_num__rr_num',
        'shipment_po__shipment_num__dr_num',
        'shipment_po__shipment_num__invoice_num',
        'shipment_po__shipment_num__ship_trucking',
        'shipment_po__shipment_num__container_num',
        'shipment_po__shipment_num__container_type',
        'shipment_po__shipment_num__awl_bl',
        'shipment_po__shipment_num__notes',)

    export_ship_list = []
    for rec_shipment in rec_shipment_query:
        details={}
        po_num = ''
        date_val = ''
        date_whse = ''
        for i in rec_shipment:
            if i == 'id':
                details['rec_num'] = rec_shipment[i]
            elif i == 'shipment_po__shipment_num__shipment_num':
                details['shipment_num'] = rec_shipment[i]
            elif i == 'shipment_po__shipment_num__date_dr':
                details['date_dr'] = rec_shipment[i]
            elif i == 'shipment_po__shipment_num__date_warehouse':
                details['date_whse'] = rec_shipment[i]
                date_whse = rec_shipment[i]
            elif i == 'date_validated':
                details['date_val'] = rec_shipment[i]
                date_val = rec_shipment[i]
            elif i == 'start_time_validation':
                details['start_val'] = rec_shipment[i]
            elif i == 'end_time_validation':
                details['end_val'] = rec_shipment[i]
            elif i == 'validation_time':
                details['time_val'] = rec_shipment[i]
            elif i == 'shipment_po__po_num__supplier':
                details['supplier'] = rec_shipment[i]
            elif i == 'shipment_po__shipment_num__ship_category':
                details['ship_cat'] = rec_shipment[i]
            elif i == 'shipment_po__po_num__po_number':
                details['po_num'] = rec_shipment[i]
                po_num = rec_shipment[i]
            elif i == 'item_number__item_number':
                details['item_num'] = rec_shipment[i]
            elif i == 'item_number__item_desc':
                details['item_desc'] = rec_shipment[i]
            elif i == 'item_quantity':
                details['item_quan'] = rec_shipment[i]
            elif i == 'item_number__uom__uom':
                details['uom'] = rec_shipment[i]
            elif i == 'shipment_po__shipment_num__rr_num':
                details['rr_num'] = rec_shipment[i]
            elif i == 'shipment_po__shipment_num__dr_num':
                details['dr_num'] = rec_shipment[i]
            elif i == 'shipment_po__shipment_num__invoice_num':
                details['invoice_num'] = rec_shipment[i]
            elif i == 'shipment_po__shipment_num__ship_trucking':
                details['ship_trucking'] = rec_shipment[i]
            elif i == 'shipment_po__shipment_num__container_num':
                details['container_num'] = rec_shipment[i]
            elif i == 'shipment_po__shipment_num__container_type':
                details['container_type'] = rec_shipment[i]
            elif i == 'shipment_po__shipment_num__awl_bl':
                details['awl_bl'] = rec_shipment[i]
            elif i == 'shipment_po__shipment_num__notes':
                details['notes'] = rec_shipment[i]

        recship_summary_query = Shipment_Summary.objects.filter(shipment_po__po_num__po_number=po_num).values(
            'issue',)

        for recship_summary in recship_summary_query:
            details['issue'] = recship_summary.get('issue')

        details['closure_date'] = ""

        try:
            resolve_po_query = ResolvePO.objects.filter(po_num__po_number=po_num).values(
                'date_resolved',
                'notes',)

            for resolve_po in resolve_po_query:
                details['closure_date'] = resolve_po.get('date_resolved')
                details['closure_remarks'] = resolve_po.get('notes')

        except ObjectDoesNotExist as DoesNotExist:
            details['closure_date'] = 'None'
            details['closure_remarks'] = 'None'

        if details['closure_date'] == "" and details['issue'] == "Non-Issue":
            details['closure_date'] = 'None'
            details['closure_remarks'] = 'None'
        elif details['closure_date'] == "" and details['issue'] != "Non-Issue":
            details['closure_date'] = 'None'
            details['closure_remarks'] = 'Still not resolved'
        
        details['aging_val_date'] = (date_val-date_whse).days

        if int(details['aging_val_date']) < 0:
            details['timeliness'] = 'Not yet validated'
        elif int(details['aging_val_date']) < 2 and int(details['aging_val_date']) >= 0:
            details['timeliness'] = '0-1 days'
        elif int(details['aging_val_date']) == 2:
            details['timeliness'] = '2 days'
        elif int(details['aging_val_date']) > 2:
            details['timeliness'] = '>2 days'

        export_ship_list.append(details)

    return render(request, template_name, 
        {'export_ship_set':export_ship_list})

#--- EXPORT WHSE ADJUSTMENTS
@login_required
@warehouse_required
def ExportWarehouseAdjustments(request):
    template_name = 'invsys/warehouse/WhseUpdate/ExportWarehouseAdjustments.html'

    iaf_item_list = IAF_Item.objects.filter().values(
        'report_num__report_num',
        'report_num__iaf_whse__whse',
        'item_number__item_number',
        'bin_location__bin_location',
        'item_quantity',
        'iaf_operator__operator',
        'total_cost',
        'reason',
        'report_num__adjustment_type__iaf_code',
        'report_num__iaf_action',
        'report_num__date_requested',
        'report_num__prepared_by',)
    iaf_prod_list = IAF_Prod.objects.filter().values(
        'report_num__report_num',
        'report_num__iaf_whse__whse',
        'prod_number__prod_number',
        'bin_location__bin_location',
        'prod_quantity',
        'iaf_operator__operator',
        'total_cost',
        'reason',
        'report_num__adjustment_type__iaf_code',
        'report_num__iaf_action',
        'report_num__date_requested',
        'report_num__prepared_by',)

    iaf_list = []
    
    for iaf_item in iaf_item_list:
        details ={}

        for i in iaf_item:
            if i == "report_num__report_num":
                details['report_num'] = iaf_item[i]
            elif i == "report_num__iaf_whse__whse":
                details['iaf_whse'] = iaf_item[i]
            elif i == "item_number__item_number":
                details['item_num'] = iaf_item[i]
            elif i == "bin_location__bin_location":
                details['bin_loc'] = iaf_item[i]
            elif i == "item_quantity":
                details['item_quan'] = iaf_item[i]
            elif i == "iaf_operator__operator":
                details['iaf_operator'] = iaf_item[i]
            elif i == "total_cost":
                details['total_cost'] = iaf_item[i]
            elif i == "reason":
                details['reason'] = iaf_item[i]
            elif i == "report_num__adjustment_type__iaf_code":
                details['iaf_code'] = iaf_item[i]
            elif i == "report_num__iaf_action":
                details['iaf_action'] = iaf_item[i]
            elif i == "report_num__date_requested":
                details['date_requested'] = iaf_item[i]
            elif i == "report_num__prepared_by":
                details['prepared_by'] = iaf_item[i]

        iaf_list.append( details )

    for iaf_prod in iaf_prod_list:
        details ={}
        for i in iaf_prod:
            if i == "report_num__report_num":
                details['report_num'] = iaf_prod[i]
            elif i == "report_num__iaf_whse__whse":
                details['iaf_whse'] = iaf_prod[i]
            elif i == "prod_number__prod_number":
                details['item_num'] = iaf_prod[i]
            elif i == "bin_location__bin_location":
                details['bin_loc'] = iaf_prod[i]
            elif i == "prod_quantity":
                details['item_quan'] = iaf_prod[i]
            elif i == "iaf_operator__operator":
                details['iaf_operator'] = iaf_prod[i]
            elif i == "total_cost":
                details['total_cost'] = iaf_prod[i]
            elif i == "reason":
                details['reason'] = iaf_prod[i]
            elif i == "report_num__adjustment_type__iaf_code":
                details['iaf_code'] = iaf_prod[i]
            elif i == "report_num__iaf_action":
                details['iaf_action'] = iaf_prod[i]
            elif i == "report_num__date_requested":
                details['date_requested'] = iaf_prod[i]
            elif i == "report_num__prepared_by":
                details['prepared_by'] = iaf_prod[i]

        iaf_list.append( details )

    return render(request, template_name, 
        {'iaf_set':iaf_list})


#--View Ongoing Comp Issuance--
@login_required
@warehouse_required
def ViewOngoingCompIssuance(request):
    template_name = 'invsys/warehouse/CompIssuance/ViewOngoingCompIssuance.html'

    issuance_sched_query = WO_Issuance_Schedule.objects.filter(cleared=False).values(
        'schedule_num',
        'date_scheduled',
        'notes',
        'cleared',
        'issues',)

    issuance_sched_list = []
    for issuance_sched in issuance_sched_query:
        issuance_sched_list.append(issuance_sched.get('schedule_num'))

    issuance_item_query = WO_Issuance_Item.objects.filter(schedule_num__schedule_num__in=issuance_sched_list).values(
        'schedule_num__schedule_num',
        'schedule_num__date_scheduled',
        'prod_sched__id',
        'prod_sched__work_order_number__work_order_number',

        'prod_sched__work_order_number__prod_number__prod_number',
        'prod_sched__work_order_number__prod_number__prod_desc',
        'prod_sched__work_order_number__prod_number__prod_class__prod_class',
        'prod_sched__work_order_number__prod_number__uom__uom',
        'prod_sched__work_order_number__customer',
        'prod_sched__quantity',
        'prod_sched__date_required',

        'item_num__item_number',
        'item_num__item_desc',
        'item_quantity',
        'bin_location__bin_location',).order_by(
        'prod_sched__work_order_number__prod_number__prod_class__prod_class',
        'prod_sched__id',
        'bin_location__bin_location',)

    issuance_item_list = [] 
    for issuance_item in issuance_item_query:
        details = {}
        prod_class = ''
        for i in issuance_item:
            details[i] = issuance_item[i]

        prod_class = issuance_item.get('prod_sched__work_order_number__prod_number__prod_class__prod_class')
        assline_assignment_obj = Assembly_Line_Assignment.objects.get(prod_class__prod_class=prod_class)
        assline = assline_assignment_obj.assemblyline.name

        details['ass_line'] = assline

        issuance_item_list.append(details)

    return render(request, template_name, 
        {'issuancesched_set':issuance_sched_query, 
        'issuance_reqitem_set':issuance_item_list})


#--View Ongoing Put Away--
@login_required
@warehouse_required
def ViewOngoingPutAway(request):
    template_name = 'invsys/warehouse/PutAway/ViewOngoingPutAway.html'

    putaway_sched_query = Put_Away_Schedule.objects.filter(cleared=False).values(
        'schedule_num',
        'date_scheduled',
        'notes',
        'cleared',
        'issues',)

    putaway_sched_list = []
    for putaway_sched in putaway_sched_query:
        putaway_sched_list.append(putaway_sched.get('schedule_num'))

    putaway_item_query = Put_Away_Items.objects.filter(schedule_num__schedule_num__in=putaway_sched_list).values(
        'schedule_num__schedule_num',
        'schedule_num__date_scheduled',

        'reference_number',
        'item_num__item_number',
        'item_num__item_desc',
        'item_num__item_cat__item_cat',
        'item_num__prod_class__prod_class',
        'required_quantity',
        'bin_location__bin_location',).order_by(
        'required_quantity',
        'item_num__prod_class__prod_class',
        'item_num__item_cat__item_cat',
        'bin_location__bin_location',)

    return render(request, template_name, 
        {'putaway_sched_set':putaway_sched_query, 
        'putaway_item_set':putaway_item_query})


#--View Ongoing Part Req Issuance--
@login_required
@warehouse_required
def ViewOngoingPartReqIssuance(request):
    template_name = 'invsys/warehouse/PartRequest/ViewOngoingPartReqIssuance.html'

    partreq_sched_query = Request_Schedule.objects.filter(cleared=False).values(
        'schedule_num',
        'date_scheduled',
        'notes',
        'cleared',
        'issues',)

    partreq_sched_list = []
    for partreq_sched in partreq_sched_query:
        partreq_sched_list.append(partreq_sched.get('schedule_num'))

    partreq_item_query = Request_Item.objects.filter(schedule_num__schedule_num__in=partreq_sched_list).values(
        'schedule_num__schedule_num',
        'schedule_num__date_scheduled',

        'prod_sched__id',
        'prod_sched__work_order_number__work_order_number',
        'item_number__item_number',
        'item_number__item_desc',
        'item_number__item_cat__item_cat',
        'quantity',
        'location_from__bin_location',
        'location_to__name',).order_by(
        'location_to__name',
        'location_from__bin_location',)

    return render(request, template_name, 
        {'partreq_sched_set':partreq_sched_query, 
        'partreq_item_set':partreq_item_query})

#--View Ongoing Comp Return--
@login_required
@warehouse_required
def ViewOngoingCompReturn(request):
    template_name = 'invsys/warehouse/CompReturn/ViewOngoingCompReturn.html'

    compreturn_sched_query = ComponentReturn_Schedule.objects.filter(cleared=False).values(
        'schedule_num',
        'date_scheduled',
        'notes',
        'cleared',
        'issues',)

    compreturn_sched_list = []
    for compreturn_sched in compreturn_sched_query:
        compreturn_sched_list.append(compreturn_sched.get('schedule_num'))

    compreturn_item_query = ComponentReturn_Item.objects.filter(schedule_num__schedule_num__in=compreturn_sched_list).values(
        'schedule_num__schedule_num',
        'schedule_num__date_scheduled',

        'prod_sched__id',
        'prod_sched__work_order_number__work_order_number',
        'item_number__item_number',
        'item_number__item_desc',
        'item_number__item_cat__item_cat',
        'quantity',
        'location_from__name',).order_by('location_from__name',)

    return render(request, template_name, 
        {'compreturn_sched_set':compreturn_sched_query, 
        'compreturn_item_set':compreturn_item_query})


#PACKING-----------------------------------
#--Generate Packing Schedule--
@login_required
@warehouse_required
def GeneratePackingSchedule(request):
    template_name = 'invsys/warehouse/Packing/GeneratePackingSchedule.html'
    if request.method == 'GET':
        packingscheduleform = PackingScheduleForm(request.GET or None)
        #Populating Initial Forms
        packingschedules = Packing_Schedule.objects.all()
        if len(packingschedules) > 0:
            next_scheduleid = Packing_Schedule.objects.order_by('-schedule_num').first().schedule_num + 1
        else:
            next_scheduleid = 1
        prodformset = PackingProductFormset(queryset=Packing_Product.objects.none())
        return render(request, template_name, {'scheduleform': packingscheduleform,'prodformset': prodformset, 'scheduleid':next_scheduleid})
    
    elif request.method == 'POST' :
        packingscheduleform = PackingScheduleForm(request.POST)
        prodformset = PackingProductFormset(request.POST, request.FILES)

        if packingscheduleform.is_valid() and prodformset.is_valid():
            # Save the Schedule first before 
            packingschedule = packingscheduleform.save(commit=False)
            packingschedule.save()

            counter = 1
            for form in prodformset:
                if counter < len(prodformset):
                    #Loop through each form in the formset to get each of the items
                    packing_prod = form.save(commit=False)
                    packing_prod.schedule_num = packingschedule
                    packing_prod.save()
                    UpdateWhseBin_PackingSched(packing_prod.bin_location, packing_prod.reference_number)
                    RecordPackingSched_Transac(packing_prod.reference_number, packing_prod.prod_num, packing_prod.required_quantity, packing_prod.bin_location, request.user.username) #Record Schedule Transactions
                    
                    counter += 1 

        return redirect('home')

def UpdateWhseBin_PackingSched( bin_loc, ref_num):
    whseprod_obj = Warehouse_Products.objects.get(bin_location__bin_location=bin_loc, reference_number=ref_num)
    whseprod_obj.status = "Scheduled for Packing"
    whseprod_obj.save()

def RecordPackingSched_Transac(ref_num, prod_num, prod_quan, bin_loc, user):
    packingschedtransac = Packing_Schedule_Transaction.objects.create(
        reference_number=ref_num,
        transaction_type="Scheduled for Packing",
        transaction_location=bin_loc,
        prod_number=prod_num,
        prod_quantity=prod_quan,
        user_name=user,
        user_department="WHSE")
    packingschedtransac.full_clean()
    packingschedtransac.save()

@login_required
@warehouse_required
def GeneratePackingSchedule_SelectItem(request):
    template_name = 'invsys/warehouse/Packing/GeneratePackingSchedule_SelectWO.html'

    whse_prod_query = Warehouse_Products.objects.filter(status="In Stock").values(
        'bin_location__id',
        'bin_location__bin_location',
        'prod_number__prod_number',
        'prod_number__prod_class__prod_class',
        'quantity',
        'reference_number')

    whseprod_list = []
    for whse_prod in whse_prod_query:
        details = {}
        for i in whse_prod:
            if i == "bin_location__bin_location":
                details['bin_loc'] = whse_prod[i]
            elif i == "prod_number__prod_number":
                details['prod_num'] = whse_prod[i]
            elif i == "prod_number__prod_class__prod_class":
                details['prod_class'] = whse_prod[i]
            elif i == "quantity":
                details['prod_quan'] = whse_prod[i]
            elif i == "bin_location__id":
                details['bin_id'] = whse_prod[i]
        prodsched_obj = WO_Production_Schedule.objects.get(id=whse_prod.get('reference_number'))
        details['wo_num'] = prodsched_obj.work_order_number.work_order_number
        details['prod_sched'] = prodsched_obj.id
        whseprod_list.append(details)

    return render(request, template_name, {'whseprod_list':whseprod_list})

#--Finish Packing--
@login_required
@warehouse_required
def FinishPacking(request):
    template_name = 'invsys/warehouse/Packing/FinishPacking.html'
    if request.method == 'GET':
        
        packingsummaryformset = PackingSummaryFormset(queryset=Packing_Summary.objects.none(), prefix='formsetsum')
        
        return render(request, template_name, {'packingsummaryformset':packingsummaryformset})

    elif request.method == 'POST' :
        sched_num = request.POST.get("sched_num",'')
        packing_sched = Packing_Schedule.objects.get(schedule_num=sched_num)

        packingsummaryformset = PackingSummaryFormset(request.POST , request.FILES, prefix='formsetsum')

        if packingsummaryformset.is_valid():
            now = datetime.now().replace(tzinfo=pytz.utc)
            
            counter = 1
            for packingsum_form in packingsummaryformset:
                if counter < len(packingsummaryformset):
                    packing_sum = packingsum_form.save(commit=False)
                    packing_sum.schedule_num = packing_sched
                    packing_sum.date_scheduled = packing_sched.date_scheduled
                    packing_sum.date_picked = now
                    packing_sum.save()
                    counter += 1

            packingsum_query = Packing_Summary.objects.filter(schedule_num=packing_sched)
            for packing_sum in packingsum_query:

                try: #Check if the packing_sum exist in the packing_prod
                    packing_prod = Packing_Product.objects.get(schedule_num=packing_sched, wo_num=packing_sum.wo_num, prod_num=packing_sum.prod_num, bin_location=packing_sum.bin_location, reference_number=packing_sum.reference_number)
                    if (packing_sum.required_quantity >= packing_sum.picked_quantity):
                        packing_prod.picked = True
                        packing_prod.save()

                        prod_sched_obj = WO_Production_Schedule.objects.get(id=packing_sum.reference_number)

                        AddtoShippingLobby_PackingSched(prod_sched_obj, request.user.username)
                        AddWhsetoShippingLobbyTransac(prod_sched_obj, packing_sum.bin_location.bin_location)

                        RecordPackingFinish_Transac(packing_prod.reference_number, packing_sum.prod_num, packing_sum.picked_quantity, request.user.username)
                        
                        UpdateWhseProd_PackingFinish(packing_prod.reference_number, packing_sum.bin_location, packing_sum.prod_num, packing_sum.picked_quantity)
                        
                except packing_prod.DoesNotExist: #There are no prod in packing_prod
                    pass                
                        
            packing_products = Packing_Product.objects.filter(schedule_num=packing_sched)

            prodcounter = 0
            clearedcounter = 0

            for packing_prod in packing_products:
                prodcounter += 1
                if packing_prod.picked == True:
                    clearedcounter += 1

            if prodcounter == clearedcounter:
                packing_sched.cleared = True
                packing_sched.save()

        else:
            print("packingsummaryformset.errors")
            print(packingsummaryformset.errors)
        return redirect('home')

@login_required
@warehouse_required
def FinishPacking_SelectPASched(request):
    template_name = 'invsys/warehouse/Packing/FinishPacking_SelectPackingSched.html'

    packingscheduleset = Packing_Schedule.objects.filter(cleared=False).values( #Query for Packing schedules
        'schedule_num',
        'date_scheduled',
        'notes',)

    packingschedules = Packing_Schedule.objects.filter(cleared=False) #Queries for Packing Schedule products
    packingitems = Packing_Product.objects.filter(schedule_num__in=packingschedules).values(
        'schedule_num',
        'wo_num__work_order_number',
        'reference_number',
        'prod_num__prod_number',
        'required_quantity',
        'bin_location__id',
        'bin_location__bin_location',
        'picked',)

    return render(request, template_name, {'packingscheduleset':packingscheduleset, 
        'packingitems':packingitems})

def AddtoShippingLobby_PackingSched(prod_sched, user):
    now = datetime.now().replace(tzinfo=pytz.utc)
    new_shiplby = Shipping_Lobby.objects.create(
        prod_sched = prod_sched,
        prod_number=prod_sched.work_order_number.prod_number,
        quantity=prod_sched.quantity,
        date_received=now,
        received_by="Warehouse Personnel 1",
        checked_by=user,
        notes="Notes",
        )
    new_shiplby.full_clean()
    new_shiplby.save()
def AddWhsetoShippingLobbyTransac(prod_sched, bin_loc):
    whse_shiplby_transac = Shipping_WhseProduct_Transaction.objects.create(
        reference_number=prod_sched.id,
        transaction_type="Moved for Packing",
        transaction_location= bin_loc,
        prod_number=prod_sched.work_order_number.prod_number,
        prod_quantity=prod_sched.quantity,
        )
    whse_shiplby_transac.full_clean()
    whse_shiplby_transac.save()

def RecordPackingFinish_Transac(ref_num, prod_num, prod_quan, user):
    packingfinishtransac = Packing_Finish_Transaction.objects.create(
        reference_number=ref_num,
        transaction_type="Finished Packing",
        transaction_location="Shipping Lobby",
        prod_number=prod_num,
        prod_quantity=prod_quan,
        user_name=user,
        user_department="WHSE")
    packingfinishtransac.full_clean()
    packingfinishtransac.save()

def UpdateWhseProd_PackingFinish(ref_num, bin_loc, prod_num, pick_quan):
    whseprod_obj = Warehouse_Products.objects.get(bin_location=bin_loc, reference_number=ref_num, status="Scheduled for Packing", prod_number=prod_num)
    whseprod_obj.quantity -= pick_quan
    whseprod_obj.save()

    if whseprod_obj.quantity == 0:
        whseprod_obj.delete()

#--View Ongoing Comp Return--
@login_required
@warehouse_required
def ViewPackingSummary(request):
    template_name = 'invsys/warehouse/Packing/ViewPackingSummary.html'

    packing_sched_list = Packing_Schedule.objects.filter(cleared=True).values(
        'schedule_num',
        'date_scheduled',
        'cleared',
        'issues',
        'notes',)
    
    packing_sum_list = Packing_Summary.objects.filter(schedule_num__cleared=True).values(
        'schedule_num__schedule_num',
        'wo_num__work_order_number',
        'reference_number',
        'prod_num__prod_number',
        'prod_num__prod_class__prod_class',
        'required_quantity',
        'picked_quantity',
        'discrepancy_quantity',
        'status',
        'date_scheduled',
        'date_picked',
        'bin_location__bin_location',)

    return render(request, template_name, 
        {'packing_sched_set':packing_sched_list,
        'packing_sum_set':packing_sum_list,})


#--View Ongoing Comp Return--
@login_required
@warehouse_required
def ViewOngoingPacking(request):
    template_name = 'invsys/warehouse/Packing/ViewOngoingPacking.html'

    packing_sched_query = Packing_Schedule.objects.filter(cleared=False).values(
        'schedule_num',
        'date_scheduled',
        'notes',
        'cleared',
        'issues',)

    packing_sched_list = []
    for packing_sched in packing_sched_query:
        packing_sched_list.append(packing_sched.get('schedule_num'))

    packing_prod_query = Packing_Product.objects.filter(schedule_num__schedule_num__in=packing_sched_list).values(
        'schedule_num__schedule_num',
        'schedule_num__date_scheduled',

        'wo_num__work_order_number',
        'reference_number',
        'prod_num__prod_number',
        'prod_num__prod_desc',
        'prod_num__prod_type',
        'prod_num__prod_class__prod_class',
        'required_quantity',
        'bin_location__bin_location',).order_by(
        'required_quantity',
        'prod_num__prod_class__prod_class',
        'prod_num__prod_type',
        'bin_location__bin_location',)

    return render(request, template_name, 
        {'packing_sched_set':packing_sched_query, 
        'packing_prod_set':packing_prod_query})


@login_required
@warehouse_required
def ViewShippedProducts(request):
    template_name = 'invsys/warehouse/Shipping/ViewShippedProducts.html'

    ship_query = Shipping_Outbound.objects.all().values(
        'ship_out_num',
        'wo_num__work_order_number',
        'wo_num__prod_number__prod_number',
        'wo_num__prod_number__prod_desc',
        'wo_num__prod_number__prod_class__prod_class',
        'wo_num__prod_quantity',
        'date_out',        
        'notes',)

    prodsched_query = WO_Production_Schedule.objects.all().values(
        'work_order_number__work_order_number',
        'id',
        'quantity',
        'status',)

    return render(request, template_name, {
        'ship_set':ship_query,
        'prodsched_set':prodsched_query })

@login_required
@warehouse_required
def ExportShippedProducts(request):
    template_name = 'invsys/warehouse/Shipping/ExportShippedProducts.html'

    ship_query = Shipping_Outbound.objects.all().values(
        'ship_out_num',
        'wo_num__work_order_number',
        'wo_num__prod_number__prod_number',
        'wo_num__prod_number__prod_desc',
        'wo_num__prod_number__prod_class__prod_class',
        'wo_num__prod_quantity',
        'date_out',        
        'notes',)

    return render(request, template_name, {
        'ship_set':ship_query})


@login_required
@warehouse_required
def ViewReceivedProducts(request):
    template_name = 'invsys/warehouse/Shipping/ViewReceivedProducts.html'

    prodsched_query = WO_Finished.objects.filter(cleared=True).values(
        'prod_sched__work_order_number__work_order_number',
        'prod_sched__id',
        'prod_sched__quantity',
        'date_received',
        'name_plate',
        'label_sticker',
        'iom',
        'qr_code',
        'wrnty_card',
        'packaging',
        'date_out',
        'checked_by',
        'notes',)

    wo_list = []
    for prodsched in prodsched_query:
        wo_list.append( prodsched.get('prod_sched__work_order_number__work_order_number') )

    wo_query = Work_Order.objects.filter(work_order_number__in=wo_list).values(
        'work_order_number',
        'prod_number__prod_number',
        'prod_number__prod_desc',
        'prod_number__prod_class__prod_class',
        'prod_quantity',)

    return render(request, template_name, {
        'wo_set':wo_query,
        'prodsched_set':prodsched_query })

@login_required
@warehouse_required
def ExportReceivedProducts(request):
    template_name = 'invsys/warehouse/Shipping/ExportReceivedProducts.html'

    prodsched_query = WO_Finished.objects.filter(cleared=True).values(
        'prod_sched__work_order_number__work_order_number',
        'prod_sched__work_order_number__prod_number__prod_number',
        'prod_sched__work_order_number__prod_number__prod_desc',
        'prod_sched__work_order_number__prod_number__prod_class__prod_class',

        'prod_sched__id',
        'prod_sched__quantity',

        'date_received',
        'name_plate',
        'label_sticker',
        'iom',
        'qr_code',
        'wrnty_card',
        'packaging',
        'date_out',
        'checked_by',
        'notes',)

    return render(request, template_name, {
        'prodsched_set':prodsched_query})

@login_required
@warehouse_required
def ExportPartReqIssuance(request):
    template_name = 'invsys/warehouse/PartRequest/ExportPartReqIssuance.html'
    
    req_sum_list = Request_Summary.objects.filter(schedule_num__cleared=True).values(
        'schedule_num__schedule_num',
        'schedule_num__date_scheduled',
        'schedule_num__cleared',
        'schedule_num__issues',
        'schedule_num__notes',

        'prod_sched__work_order_number__work_order_number',
        'prod_sched__id',
        'item_number__item_number',
        'totalreq_quan',
        'totalrec_quan',
        'discrepancy',
        'discrepancy_quantity',
        'status',
        'date_received',
        'bin_location__bin_location',
        'ass_location__name',)

    return render(request, template_name, 
        {'req_sum_set':req_sum_list,})

@login_required
@warehouse_required
def ExportCompReturn(request):
    template_name = 'invsys/warehouse/CompReturn/ExportCompReturn.html'
    
    return_sum_list = ComponentReturn_Summary.objects.filter(schedule_num__cleared=True).values(
        'schedule_num__schedule_num',
        'schedule_num__date_scheduled',
        'schedule_num__cleared',
        'schedule_num__issues',
        'schedule_num__notes',

        'prod_sched__work_order_number__work_order_number',
        'prod_sched__id',
        'item_number__item_number',
        'totalreq_quan',
        'totalrec_quan',
        'discrepancy',
        'discrepancy_quantity',
        'status',
        'date_received',
        'ass_location__name',)

    return render(request, template_name, 
        {'return_sum_set':return_sum_list,})

@login_required
@warehouse_required
def ExportPutAway(request):
    template_name = 'invsys/warehouse/PutAway/ExportPutAway.html'
    
    pa_sum_list = Put_Away_Summary.objects.filter(schedule_num__cleared=True).values(
        'schedule_num__schedule_num',
        'schedule_num__date_scheduled',
        'schedule_num__notes',
        'schedule_num__cleared',
        'schedule_num__issues',

        'item_num__item_number',
        'required_quantity',
        'stored_quantity',
        'bin_location__bin_location',
        'discrepancy',
        'discrepancy_quantity',
        'status',
        'date_scheduled',
        'date_stored',
        'reference_number',)

    return render(request, template_name, 
        {'pasum_set':pa_sum_list})

@login_required
@warehouse_required
def ExportWhseItem(request):
    template_name = 'invsys/warehouse/WhseLoc/ExportWhseItem.html'

    whse_item_query = Warehouse_Items.objects.filter().values(
        'bin_location__bin_location',
        'bin_location__item_cat__item_cat',
        'bin_location__prod_class__prod_class',

        'item_number__item_number',
        'quantity',
        'status',
        'reference_number')

    item_cat_query = ItemCat.objects.all().exclude(item_cat="Product").values(
        'id',
        'item_cat')

    prod_class_query = ProdClass.objects.all().values(
        'id',
        'prod_class')

    return render(request, template_name, 
        {'whse_item_set':whse_item_query,
        'item_cat_set':item_cat_query,
        'prod_class_set':prod_class_query})

@login_required
@warehouse_required
def ExportWhseProduct(request):
    template_name = 'invsys/warehouse/WhseLoc/ExportWhseProduct.html'
    
    whse_product_query = Warehouse_Products.objects.filter().values(
        'bin_location__bin_location',
        'bin_location__item_cat__item_cat',
        'bin_location__prod_class__prod_class',

        'prod_number__prod_number',
        'quantity',
        'status',
        'reference_number')

    item_cat_query = ItemCat.objects.filter(item_cat="Product").values(
        'id',
        'item_cat')

    prod_class_query = ProdClass.objects.all().values(
        'id',
        'prod_class')

    return render(request, template_name, 
        {'whse_product_set':whse_product_query,
        'item_cat_set':item_cat_query,
        'prod_class_set':prod_class_query})

@login_required
@warehouse_required
def ExportPacking(request):
    template_name = 'invsys/warehouse/Packing/ExportPacking.html'
    
    packing_sum_list = Packing_Summary.objects.filter(schedule_num__cleared=True).values(
        'schedule_num__schedule_num',
        'schedule_num__date_scheduled',
        'schedule_num__cleared',
        'schedule_num__issues',
        'schedule_num__notes',

        'wo_num__work_order_number',
        'reference_number',
        'prod_num__prod_number',
        'required_quantity',
        'picked_quantity',

        'discrepancy',
        'discrepancy_quantity',
        'status',
        'date_scheduled',
        'date_picked',
        'bin_location__bin_location',)

    return render(request, template_name, 
        {'packing_sum_set':packing_sum_list,})


@login_required
@warehouse_required
def ImportItems(request):
    if request.method == 'GET':

        itemformset = ItemFormset(queryset=Item.objects.none(), prefix='form')

        return render(request, 'invsys/warehouse/CheckInv/ImportItems.html', {'itemformset':itemformset})
    
    elif request.method == 'POST':
        itemformset = ItemFormset(request.POST , request.FILES, prefix='form')

        if itemformset.is_valid():

            counter = 1;
            form_counter = 0;
            for itemform in itemformset:
                if counter < len(itemformset):
                    item = itemform.save(commit=False)

                    uom = Uom.objects.get(uom=request.POST.get('form-'+str(form_counter)+'-uom'))
                    item_cat = ItemCat.objects.get(item_cat=request.POST.get('form-'+str(form_counter)+'-item_cat'))
                    prod_class = ProdClass.objects.get(prod_class=request.POST.get('form-'+str(form_counter)+'-prod_class'))

                    item.uom = uom
                    item.item_cat = item_cat
                    item.prod_class = prod_class
                    item.save()
                    counter += 1
                    form_counter += 1

        return redirect('home')

#--UPDATE PURCHASE ORDERS---
@login_required
@warehouse_required
def ImportProducts(request):
    if request.method == 'GET':

        prodformset = ProductFormset(queryset=Product.objects.none(), prefix='form')

        return render(request, 'invsys/warehouse/CheckInv/ImportProducts.html', {'prodformset':prodformset})
    
    elif request.method == 'POST':

        return redirect('home')

def importprod_setprod(request):
    prod_set = json.loads(request.POST.get('prod_set[]'))
    item_set = json.loads(request.POST.get('item_set[]'))
    
    for prod in prod_set:
        count = 0
        prod_num = ''
        prod_desc = ''
        uom = ''
        prod_type = ''
        prod_class = ''
        price = ''
        notes = ''

        for details in prod:
            if count == 0: #prod_num
                prod_num = details
                count += 1
            elif count == 1: #prod_desc
                prod_desc = details
                count += 1
            elif count == 2: #uom
                uom = details
                count += 1
            elif count == 3: #prod_type
                prod_type = details
                count += 1
            elif count == 4: #prod_class
                prod_class = details
                count += 1
            elif count == 5: #price
                price = details
                count += 1
            elif count == 6: #notes
                notes = details
                count += 1

        uom_obj = Uom.objects.get(uom=uom)
        prod_class_obj = ProdClass.objects.get(prod_class=prod_class)

        prod_obj = Product.objects.create(
            prod_number= prod_num,
            prod_desc= prod_desc,
            uom= uom_obj,
            prod_type= prod_type,
            prod_class= prod_class_obj,
            price= price,
            notes= notes)
        prod_obj.full_clean()
        prod_obj.save()


    for item in item_set:
        count = 0
        prod_num= ''
        item_num = ''
        item_quan = 0

        for details in item:
            if count == 0: #prod_num
                prod_num = details
                count += 1
            elif count == 1: #item_num
                item_num = details
                count += 1
            elif count == 2: #item_quan
                item_quan = details
                count += 1

        prod_obj = Product.objects.get(prod_number=prod_num)
        item_obj = Item.objects.get(item_number=item_num)

        prod_item_obj = ProductItemList.objects.create(
            prod_number= prod_obj,
            item_number= item_obj,
            quantity= item_quan)

        prod_item_obj.full_clean()
        prod_item_obj.save()

    data = {}
    return JsonResponse(data)
