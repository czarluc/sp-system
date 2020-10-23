from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Avg, Count
from django.forms import inlineformset_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)
from ..decorators import planner_required
from ..forms import *
from ..models import *
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from datetime import date, timedelta
import json
import datetime
from django.utils import timezone


class PlannerSignUpView(CreateView):
    model = User
    form_class = PlannerSignUpForm
    template_name = 'registration/signup_form.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'planner'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('planner:planner_home')


@login_required
@planner_required
def PlannerHome(request):
    return render(request, 'invsys/planner/planner_home.html')

#Work Order Creation
@login_required
@planner_required
def CreateWO(request):
    template_name = 'invsys/planner/WOCreation/CreateWO.html'
    if request.method == 'GET':
        newwoform = WorkOrderForm(request.GET or None)
        formset = WorkOrderItemFormset(queryset=Work_Order_Item_List.objects.none())
        return render(request, template_name, {'woform': newwoform,'formset': formset,})
    elif request.method == 'POST' :
        newwoform = WorkOrderForm(request.POST)
        formset = WorkOrderItemFormset(request.POST)
        if newwoform.is_valid() and formset.is_valid(): 
            wo = newwoform.save(commit=False) # Save the Product first before its items
            wo.save()
            counter = 1
            for form in formset: #Loop through each form in the formset to get each of the items
                if counter < len(formset):
                    
                    part = form.save(commit=False)
                    part.work_order_number = wo

                    totalpartreq = int(part.item_quantity) * int(wo.prod_quantity)
                    totalallocated = 0

                    AllocateWhseItemsCreateWO(part.item_number, totalpartreq, totalallocated, part.work_order_number)
                    part.save()
                    
                    counter += 1
            DeleteWhseItemBin()
            firsturl = "/planner/CreateWO/"
            wo_pk = str(wo.work_order_number)
            secondurl = "/ScheduleWorkOrder/"
            return redirect(firsturl+wo_pk+secondurl) #Redirect to Work Order Scheduler
        
        return redirect('home')
def AllocateWhseItemsCreateWO(itemnum, totalreq, totalalloc, wo_num):
    whseitemset = Warehouse_Items.objects.filter(status="In Stock", item_number=itemnum, bin_location__item_cat=itemnum.item_cat, bin_location__prod_class=itemnum.prod_class).order_by('quantity')
    for whsebin in whseitemset:
        if not totalreq == totalalloc:
            totalalloc, whsebin = SubtractBinStock(whsebin, totalreq, totalalloc, itemnum, wo_num)
            whsebin.save()
def SubtractBinStock(whsebin, totalreq, totalalloc, itemnum, wo_num):
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
    CreateWhseItemBin_CreateWO(whsebin.bin_location, itemnum, allocatedbinquan, wo_num)
    totalalloc += allocatedbinquan
    return totalalloc, whsebin
def CreateWhseItemBin_CreateWO(binloc, itemnum, allocquan, wonum):
    whseitemBin = Warehouse_Items.objects.create(
        bin_location=binloc, 
        item_number=itemnum,
        quantity=allocquan,
        status="Allocated for Work Order",
        reference_number=wonum)
    whseitemBin.full_clean()
    whseitemBin.save()
def DeleteWhseItemBin():
    whseitemset = Warehouse_Items.objects.order_by('quantity')
    for whsebin in whseitemset:
        if whsebin.quantity == 0:
            whsebin.delete()
@login_required
@planner_required
def CreateWO_SelectProduct(request):
    prodset = Product.objects.all().values(
        'prod_number',
        'prod_desc',
        'uom__uom',
        'prod_type',
        'prod_class__prod_class',
        'price',)
    proditemset = ProductItemList.objects.all().values(
        'prod_number__prod_number',
        'item_number__item_number',
        'item_number__item_desc',
        'quantity',)
    whseitemset = Warehouse_Items.objects.filter(status="In Stock").values(
        'bin_location__id',
        'bin_location__bin_location',
        'item_number__item_number',
        'quantity',)

    return render(request, 'invsys/planner/WOCreation/CreateWO_SelectProduct.html',
        {'prodset': prodset,
        'proditemset': proditemset,
        'whseitemset': whseitemset,})
@login_required
@planner_required
def CreateWO_ScheduleWO_pk(request, pk=None):
    template_name = 'invsys/planner/WOCreation/CreateWO_ScheduleWO.html'

    if request.method == 'GET':
        woquery = Work_Order.objects.filter(work_order_number=pk).values(
            'work_order_number',
            'prod_number__prod_number', 
            'prod_quantity',)

        pending_prod_sched = WO_Production_Schedule.objects.filter(scheduled=False).values(
            'id',
            'work_order_number__work_order_number',
            'quantity',
            'date_required',)

        scheduled_prod_sched = WO_Production_Schedule.objects.filter(scheduled=True).values(
            'id',
            'work_order_number__work_order_number',
            'quantity',
            'date_required',)

        return render(request, template_name, 
            {'woquery':woquery, 
            'pending_prod_sched':pending_prod_sched,
            'scheduled_prod_sched':scheduled_prod_sched})

    elif request.method == 'POST':
        return redirect('home')

def add_schedule(request):
    prod_sched_set = json.loads(request.POST.get('prod_sched_set[]'))

    count = 0
    timezone_date = ''
    quantity = ''

    for prod_sched in prod_sched_set:
        for details in prod_sched:
            if count == 0: #Work Order Number
                wo_num = details
                count += 1
            elif count == 1: #Date
                date = datetime.datetime.strptime(details, '%Y-%m-%d')
                tz = timezone.get_current_timezone()
                timezone_date = timezone.make_aware(date, tz, True)
                count += 1
            else: #Quantity
                quantity = details
                count += 1
        count = 0
        
        #Create new Production Schedule
        woquery = Work_Order.objects.get(work_order_number=wo_num)
        new_prod_sched = WO_Production_Schedule.objects.create(
            work_order_number=woquery,
            quantity=quantity,
            date_required=timezone_date,
            status="Waiting for Schedule")
        new_prod_sched.full_clean()
        new_prod_sched.save()

    data = {}
    return JsonResponse(data)


@login_required
@planner_required
def ViewWO(request):
    wo_list = Work_Order.objects.filter().values(
        'work_order_number',
        'customer',
        'order_type',
        'work_order_class',
        'fo_number',
        'barcode',
        'tid_number',
        'prod_number__prod_number',
        'prod_quantity',
        'notes',)
    prod_sched_list = WO_Production_Schedule.objects.filter().values(
        'id',
        'work_order_number__work_order_number',
        'quantity',
        'date_required',
        'status',)
    prod_list = Work_Order.objects.filter().values(
        'work_order_number',
        'prod_number__prod_number',
        'prod_number__prod_desc',
        'prod_number__uom',
        'prod_number__prod_type',
        'prod_number__prod_class',
        'prod_number__barcode',
        'prod_number__price',)
    wo_item_list = Work_Order_Item_List.objects.filter().values(
        'work_order_number__work_order_number',
        'item_number__item_number',
        'item_quantity',)
    return render(request, 'invsys/planner/WOCreation/ViewWO.html', 
        {'wo_set':wo_list,
        'prod_sched_set':prod_sched_list, 
        'prod_set':prod_list,
        'wo_item_set':wo_item_list,})

@login_required
@planner_required
def ViewWO_getDetails(request):

    files = request.POST

    wo_num = files.get("wo_num")
    prod_sched = files.get("prod_sched")

    schedissuance_details = {}
    try:
        issuance_search = WO_Issuance_List.objects.get(prod_sched=prod_sched)
        schedissuance = WO_Issuance_Schedule.objects.get(schedule_num=issuance_search.schedule_num.schedule_num)
        
        schedissuance_details['schedule_num'] = schedissuance.schedule_num
        schedissuance_details['date_scheduled'] = schedissuance.date_scheduled
        schedissuance_details['notes'] = schedissuance.notes
        schedissuance_details['issues'] = schedissuance.issues
    except WO_Issuance_List.DoesNotExist:
        pass
        
    issuance_list = WO_Issuance_List.objects.filter(prod_sched=prod_sched).values(
        'prod_sched__id',
        'cleared',
        'issues',
        'issued_by',
        'date_issued',
        'verified_by',
        'notes',
        'image',)
    
    assembly_list = WO_Assembly.objects.filter(prod_sched=prod_sched).values(
        'prod_sched__id',
        'date_received',
        'assembled_by',
        'date_assembled',
        'verified_by',
        'notes',
        'cleared',
        'image',)
    
    coupling_list = WO_Coupling.objects.filter(prod_sched=prod_sched).values(
        'prod_sched__id',
        'date_received',
        'coupled_by',
        'date_coupled',
        'verified_by',
        'notes',
        'cleared',
        'image',)
    
    testing_list = WO_Testing.objects.filter(prod_sched=prod_sched).values(
        'prod_sched__id',
        'date_received',
        'tested_by',
        'date_tested',
        'verified_by',
        'notes',
        'cleared',
        'image',)

    finished_list = WO_Finished.objects.filter(prod_sched=prod_sched).values(
        'prod_sched__id',
        'date_received',
        'name_plate',
        'label_sticker',
        'iom',
        'qr_code',
        'wrnty_card',
        'packaging',
        'date_out',
        'checked_by',
        'notes',
        'cleared',
        'image',)

    schedule_query = []
    issuance_query = []
    assembly_query = []
    coupling_query = []
    testing_query = []
    finished_query = []

    schedule_query.append(schedissuance_details)

    for issuance in issuance_list:
        issuance_query.append(issuance)

    for assembly in assembly_list:
        assembly_query.append(assembly)

    for coupling in coupling_list:
        coupling_query.append(coupling)

    for testing in testing_list:
        testing_query.append(testing)

    for finished in finished_list:
        finished_query.append(finished)

    data = {
        "schedule_set" : schedule_query,
        "issuance_set" : issuance_query,
        "assembly_set" : assembly_query,
        "coupling_set" : coupling_query,
        "testing_set" : testing_query,
        "finished_set" : finished_query,
    }

    return JsonResponse(data) # http response

def ViewWO_getPDF(request):

    files = request.POST

    wo_num = files.get("wo_num")
    prod_sched = files.get("prod_sched")

    prodsched_list = WO_Production_Schedule.objects.filter(id=prod_sched).values(
        'work_order_number__work_order_number',
        'work_order_number__customer',
        'work_order_number__tid_number',
        'work_order_number__prod_number__prod_number',
        'work_order_number__prod_number__prod_desc',
        'work_order_number__work_order_class',
        'work_order_number__order_type',
        'work_order_number__creation_date',
        'work_order_number__required_completion_date',
        'quantity',
        'date_required')
        
    issuance_list = WO_Issuance_List.objects.filter(prod_sched=prod_sched).values(
        'date_issued',
        'verified_by',)
    
    assembly_list = WO_Assembly.objects.filter(prod_sched=prod_sched).values(
        'assembled_by',
        'date_assembled',)
    
    coupling_list = WO_Coupling.objects.filter(prod_sched=prod_sched).values(
        'coupled_by',
        'date_coupled',)
    
    testing_list = WO_Testing.objects.filter(prod_sched=prod_sched).values(
        'tested_by',
        'date_tested',)

    finished_list = WO_Finished.objects.filter(prod_sched=prod_sched).values(
        'name_plate',
        'label_sticker',
        'iom',
        'qr_code',
        'wrnty_card',
        'packaging',
        'date_out',
        'checked_by',)

    prodsched_query = []
    issuance_query = []
    assembly_query = []
    coupling_query = []
    testing_query = []
    finished_query = []

    for prodsched in prodsched_list:
        prodsched_query.append(prodsched)

    for issuance in issuance_list:
        issuance_query.append(issuance)

    for assembly in assembly_list:
        assembly_query.append(assembly)

    for coupling in coupling_list:
        coupling_query.append(coupling)

    for testing in testing_list:
        testing_query.append(testing)

    for finished in finished_list:
        finished_query.append(finished)

    data = {
        "planner" : request.user.username,
        "prodsched_set" : prodsched_query,
        "issuance_set" : issuance_query,
        "assembly_set" : assembly_query,
        "coupling_set" : coupling_query,
        "testing_set" : testing_query,
        "finished_set" : finished_query,
    }

    return JsonResponse(data) # http response

@login_required
@planner_required
def ConvertWO(request):
    return render(request, 'invsys/warehouse/Shipping/Sample_ShipProd.html')

#Check Inv
@login_required
@planner_required
def CheckPart(request):
    item_list = Item.objects.filter().values(
        'item_number',
        'item_desc',
        'uom__uom',
        'item_cat__item_cat',
        'prod_class__prod_class',
        'barcode',
        'price',
        'notes',)
    whse_item_list = Warehouse_Items.objects.filter(status="In Stock").values(
        'bin_location__bin_location',
        'item_number__item_number',
        'quantity',
        'status',
        'reference_number',)
    print(whse_item_list)
    whsebin_query = []
    for whsebin in whse_item_list:
        whsebin_query.append(whsebin.get("bin_location__bin_location"))
    print(whsebin_query)
    whse_bin_list = Warehouse.objects.filter(bin_location__in=whsebin_query).values(
        'bin_location',
        'item_cat__item_cat',
        'prod_class__prod_class',
        'barcode',)
    print(whse_bin_list)
    return render(request, 'invsys/planner/CheckInv/CheckPart.html', 
        {'whse_bin_set':whse_bin_list,
        'whse_item_set':whse_item_list, 
        'item_set':item_list,})

#Check Product
@login_required
@planner_required
def CheckProduct(request):
    prod_list = Product.objects.filter().values(
        'prod_number',
        'prod_desc',
        'uom__uom',
        'prod_type',
        'prod_class__prod_class',
        'barcode',
        'price',
        'notes',)

    whse_prod_list = Warehouse_Products.objects.filter(status="In Stock").values(
        'bin_location__bin_location',
        'prod_number__prod_number',
        'quantity',
        'status',
        'reference_number',)

    whsebin_query = []
    for whsebin in whse_prod_list:
        whsebin_query.append(whsebin.get("bin_location__bin_location"))

    whse_bin_list = Warehouse.objects.filter(bin_location__in=whsebin_query).values(
        'bin_location',
        'item_cat__item_cat',
        'prod_class__prod_class',
        'barcode',)

    prod_bom_query = ProductItemList.objects.filter().values(
        'prod_number__prod_number',
        'item_number__item_number',
        'item_number__item_desc',
        'quantity',)

    prod_bom_list = []
    for prod_bom in prod_bom_query:
        details = {}
        avail_quan = 0
        for i in prod_bom:
            if i == "prod_number__prod_number":
                details['prod_num'] = prod_bom[i]
            elif i == "item_number__item_number":
                details['item_num'] = prod_bom[i]
                avail_quan = getItemStock(prod_bom[i])
            elif i == "item_number__item_desc":
                details['item_desc'] = prod_bom[i]
            elif i == "quantity":
                details['quantity'] = prod_bom[i]
            details['avail_quan'] = avail_quan
        prod_bom_list.append(details)

    return render(request, 'invsys/planner/CheckInv/CheckProduct.html', 
        {'whse_bin_set':whse_bin_list,
        'whse_prod_set':whse_prod_list, 
        'prod_set':prod_list,
        'prod_bom_set':prod_bom_list})

def getItemStock(item_num):
    whse_item_query = Warehouse_Items.objects.filter(item_number__item_number=item_num, status="In Stock")
    avail_quan = 0
    try:
        for whse_item in whse_item_query:
            avail_quan += whse_item.quantity
    except whse_item_query.DoesNotExist:
        avail_quan = 0
    
    return avail_quan

#ISSUANCE TIMELINESS
def Dashboard_get_issuance_acc(request):

    now = datetime.datetime.now()

    label = ["Non-Issue", "Over-Shipped", "Short-Shipped"]

    count = []

    for date in label:
        count.append(Purchase_Order.objects.filter(purchase_date=date).count())

    print(len(count))
    print(label)
    print(count)

    data = {
        "labels" : label,
        "default" : count,
    }
    return JsonResponse(data) # http response

def Dashboard_update_issuance_acc(request):
    files = request.POST

    start_date = datetime.datetime.strptime(files.get("from"), '%Y-%m-%d').date()
    end_date = datetime.datetime.strptime(files.get("to"), '%Y-%m-%d').date()

    label = [ start_date + datetime.timedelta(n) for n in range(int ((end_date - start_date).days))]

    count = []
    for date in label:
        count.append(Purchase_Order.objects.filter(purchase_date=date).count())

    data = {
        "labels" : label,
        "default" : count,
    }
    return JsonResponse(data) # http response

#WORK ORDER STATUS
def Dashboard_get_issuance_acc(request):

    now = datetime.datetime.now()

    label = ["Non-Issue", "Over-Shipped", "Short-Shipped"]

    count = []

    for date in label:
        count.append(Purchase_Order.objects.filter(purchase_date=date).count())

    print(len(count))
    print(label)
    print(count)

    data = {
        "labels" : label,
        "default" : count,
    }
    return JsonResponse(data) # http response
def Dashboard_update_issuance_acc(request):
    files = request.POST

    start_date = datetime.datetime.strptime(files.get("from"), '%Y-%m-%d').date()
    end_date = datetime.datetime.strptime(files.get("to"), '%Y-%m-%d').date()

    label = [ start_date + datetime.timedelta(n) for n in range(int ((end_date - start_date).days))]

    count = []
    for date in label:
        count.append(Purchase_Order.objects.filter(purchase_date=date).count())

    data = {
        "labels" : label,
        "default" : count,
    }
    return JsonResponse(data) # http response
#ASSEMBLY PRODUCTIVITY
def Dashboard_get_issuance_acc(request):

    now = datetime.datetime.now()

    label = ["Non-Issue", "Over-Shipped", "Short-Shipped"]

    count = []

    for date in label:
        count.append(Purchase_Order.objects.filter(purchase_date=date).count())

    print(len(count))
    print(label)
    print(count)

    data = {
        "labels" : label,
        "default" : count,
    }
    return JsonResponse(data) # http response
def Dashboard_update_issuance_acc(request):
    files = request.POST

    start_date = datetime.datetime.strptime(files.get("from"), '%Y-%m-%d').date()
    end_date = datetime.datetime.strptime(files.get("to"), '%Y-%m-%d').date()

    label = [ start_date + datetime.timedelta(n) for n in range(int ((end_date - start_date).days))]

    count = []
    for date in label:
        count.append(Purchase_Order.objects.filter(purchase_date=date).count())

    data = {
        "labels" : label,
        "default" : count,
    }
    return JsonResponse(data) # http response