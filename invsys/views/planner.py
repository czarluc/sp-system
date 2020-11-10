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
from datetime import datetime as dt
import json
import datetime
from django.utils import timezone
import pytz


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

        prod_sched_query = WO_Production_Schedule.objects.filter(received=False).values(
            'id',
            'work_order_number__work_order_number',
            'work_order_number__prod_number__prod_class__prod_class',
            'quantity',
            'date_required',
            'scheduled',
            'issued',
            'assembled',
            'coupled',
            'tested',
            'received',
            'status',)

        prodsched_list = []
        for prod_sched in prod_sched_query:
            details={}
            prodsched_id = ''
            for i in prod_sched:
                if i == 'id':
                    details['id'] = prod_sched[i]
                    prodsched_id = prod_sched[i]
                elif i == 'work_order_number__work_order_number':
                    details['wo_num'] = prod_sched[i]
                elif i == 'work_order_number__prod_number__prod_class__prod_class':
                    details['prod_class'] = prod_sched[i]
                elif i == 'quantity':
                    details['prod_quan'] = prod_sched[i]
                elif i == 'status':
                    details['status'] = prod_sched[i]

            if prod_sched.get('scheduled') == False and prod_sched.get('issued') == False: #Not yet scheduled for issuance
                details['date_latest'] = prod_sched.get('date_required')
            elif prod_sched.get('scheduled') == True and prod_sched.get('issued') == False: #Not yet issued but scheduled
                details['date_latest'] = getDate_Scheduled(prodsched_id)
            elif prod_sched.get('issued') == True and prod_sched.get('assembled') == False: #Not yet assembled but issued
                details['date_latest'] = getDate_Issued(prodsched_id)
            elif prod_sched.get('assembled') == True and prod_sched.get('coupled') == False: #Not yet coupled but assembled
                details['date_latest'] = getDate_Assembled(prodsched_id)
            elif prod_sched.get('coupled') == True and prod_sched.get('tested') == False: #Not yet tested but coupled
                details['date_latest'] = getDate_Coupled(prodsched_id)
            elif prod_sched.get('tested') == True and prod_sched.get('received') == False: #Not yet received but tested
                details['date_latest'] = getDate_Tested(prodsched_id)
            
            prodsched_list.append(details)

        prod_class_query = ProdClass.objects.all().exclude(prod_class="None").values(
            'prod_class',)

        return render(request, template_name, 
            {'woquery':woquery,
            'prodsched_set':prodsched_list,
            'prod_class_set':prod_class_query})

    elif request.method == 'POST':
        return redirect('home')

def getDate_Scheduled(prodsched_id):
    issuance_query = WO_Issuance_List.objects.filter(prod_sched__id = prodsched_id).values(
        'schedule_num__date_scheduled')
    date_latest = ''

    for issuance in issuance_query:
        date_latest = issuance.get('schedule_num__date_scheduled')

    return date_latest

def getDate_Issued(prodsched_id):
    fin_issuance_query = WO_Assembly.objects.filter(prod_sched__id=prodsched_id).values(
        'date_received')

    date_latest = ''

    for fin_issuance in fin_issuance_query:
        date_latest = fin_issuance.get('date_received')

    return date_latest

def getDate_Assembled(prodsched_id):
    fin_assembly_query = WO_Coupling.objects.filter(prod_sched__id=prodsched_id).values(
        'date_received')

    date_latest = ''

    for fin_assembly in fin_assembly_query:
        date_latest = fin_assembly.get('date_received')

    return date_latest

def getDate_Coupled(prodsched_id):
    fin_coupled_query = WO_Testing.objects.filter(prod_sched__id=prodsched_id).values(
        'date_received')

    date_latest = ''

    for fin_coupled in fin_coupled_query:
        date_latest = fin_coupled.get('date_received')

    return date_latest

def getDate_Tested(prodsched_id):
    fin_tested_query = WO_Finished.objects.filter(prod_sched__id=prodsched_id).values(
        'date_received')

    date_latest = ''

    for fin_tested in fin_tested_query:
        date_latest = fin_tested.get('date_received')

    return date_latest


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
        'prod_number__prod_class__prod_class',
        'prod_quantity',
        'notes',)
    prod_sched_list = WO_Production_Schedule.objects.filter().values(
        'id',
        'work_order_number__work_order_number',
        'quantity',
        'date_required',
        'status',
        'issues',)
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

    prod_class_query = ProdClass.objects.all().exclude(prod_class="None").values(
            'prod_class',)

    return render(request, 'invsys/planner/WOCreation/ViewWO.html', 
        {'wo_set':wo_list,
        'prod_sched_set':prod_sched_list, 
        'prod_set':prod_list,
        'wo_item_set':wo_item_list,
        'prod_class_set':prod_class_query})

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
def ExportWO(request):
    template_name = 'invsys/planner/WOCreation/ExportWO.html'

    prod_sched_query = WO_Production_Schedule.objects.filter().values(
        'work_order_number__work_order_number',
        'work_order_number__customer',
        'work_order_number__order_type',
        'work_order_number__work_order_class',
        'work_order_number__fo_number',
        'work_order_number__tid_number',
        'work_order_number__prod_number',
        'work_order_number__customer_order_date',
        'work_order_number__otd_customer_req_date',
        'work_order_number__otp_commitment_date',
        'work_order_number__required_completion_date',
        'work_order_number__finished_completion_date',
        'work_order_number__creation_date',
        'work_order_number__notes',
        'id',
        'quantity',
        'date_required',)

    wo_export_list = []
    for prod_sched in prod_sched_query:
        details={}
        wo_num = ''
        for i in prod_sched:
            if i == "work_order_number__work_order_number":
                details['wo_num'] = prod_sched[i]
                wo_num = prod_sched[i]
            elif i == "work_order_number__customer":
                details['customer'] = prod_sched[i]
            elif i == 'work_order_number__order_type':
                details['order_type'] = prod_sched[i]
            elif i == 'work_order_number__work_order_class':
                details['work_order_class'] = prod_sched[i]
            elif i == 'work_order_number__fo_number':
                details['fo_number'] = prod_sched[i]
            elif i == 'work_order_number__tid_number':
                details['tid_number'] = prod_sched[i]
            elif i == 'work_order_number__prod_number':
                details['prod_number'] = prod_sched[i]
            elif i == 'work_order_number__customer_order_date':
                details['customer_order_date'] = prod_sched[i]
            elif i == 'work_order_number__otd_customer_req_date':
                details['otd_customer_req_date'] = prod_sched[i]
            elif i == 'work_order_number__otp_commitment_date':
                details['otp_commitment_date'] = prod_sched[i]
            elif i == 'work_order_number__required_completion_date':
                details['required_completion_date'] = prod_sched[i]
            elif i == 'work_order_number__finished_completion_date':
                details['finished_completion_date'] = prod_sched[i]
            elif i == 'work_order_number__creation_date':
                details['creation_date'] = prod_sched[i]
            elif i == 'work_order_number__notes':
                details['notes'] = prod_sched[i]
            elif i == 'id':
                details['ref_num'] = prod_sched[i]
            elif i == 'quantity':
                details['prod_quan'] = prod_sched[i]
            elif i == 'date_required':
                details['date_required'] = prod_sched[i]

        wo_item_query = Work_Order_Item_List.objects.filter(work_order_number=wo_num).values(
            'item_number__item_number',
            'item_quantity',)

        for wo_item in wo_item_query:
            for i in wo_item:
                if i == "item_number__item_number":
                    details['item_num'] = wo_item[i]
                elif i == "item_quantity":
                    details['item_quan'] = wo_item[i]
            details['tot_item_quan'] = int(details['prod_quan']) * int(details['item_quan'])
            wo_export_list.append(details)

    return render(request, template_name, {'wo_export_set':wo_export_list})

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
    whsebin_query = []
    for whsebin in whse_item_list:
        whsebin_query.append(whsebin.get("bin_location__bin_location"))
    whse_bin_list = Warehouse.objects.filter(bin_location__in=whsebin_query).values(
        'bin_location',
        'item_cat__item_cat',
        'prod_class__prod_class',
        'barcode',)

    prod_class_query = ProdClass.objects.all().exclude(prod_class="None").values(
            'prod_class',)

    item_cat_query = ItemCat.objects.all().exclude(item_cat="Product").values(
        'item_cat')
    return render(request, 'invsys/planner/CheckInv/CheckPart.html', 
        {'whse_bin_set':whse_bin_list,
        'whse_item_set':whse_item_list, 
        'item_set':item_list,
        'prod_class_set':prod_class_query,
        'item_cat_set':item_cat_query})

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

    prod_class_query = ProdClass.objects.all().exclude(prod_class="None").values(
        'prod_class',)

    return render(request, 'invsys/planner/CheckInv/CheckProduct.html', 
        {'whse_bin_set':whse_bin_list,
        'whse_prod_set':whse_prod_list, 
        'prod_set':prod_list,
        'prod_bom_set':prod_bom_list,
        'prod_class_set':prod_class_query})

def getItemStock(item_num):
    whse_item_query = Warehouse_Items.objects.filter(item_number__item_number=item_num, status="In Stock")
    avail_quan = 0
    try:
        for whse_item in whse_item_query:
            avail_quan += whse_item.quantity
    except whse_item_query.DoesNotExist:
        avail_quan = 0
    
    return avail_quan

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

#ISSUANCE TIMELINESS

#WORK ORDER STATUS
def Dashboard_get_wostatus(request):
    wo_sched = 0
    wo_assembled = 0
    wo_coupled = 0
    wo_tested = 0

    prod_sched_query = WO_Production_Schedule.objects.filter(received=False)

    for prod_sched in prod_sched_query:

        if prod_sched.scheduled == False and prod_sched.issued == False: #Not yet scheduled for issuance
            pass
        elif prod_sched.scheduled == True and prod_sched.issued == False: #Not yet issued but scheduled
            wo_sched += 1
        elif prod_sched.issued == True and prod_sched.assembled == False: #Not yet assembled but issued
            wo_assembled += 1
        elif prod_sched.assembled == True and prod_sched.coupled == False: #Not yet coupled but assembled
            wo_coupled += 1
        elif prod_sched.coupled == True and prod_sched.tested == False: #Not yet tested but coupled
            wo_tested += 1

    data = {
        "wo_sched" : wo_sched,
        "wo_assembled": wo_assembled,
        "wo_coupled":wo_coupled,
        "wo_tested":wo_tested
    }
    return JsonResponse(data) # http response


#ASSEMBLY PRODUCTIVITY
def Dashboard_get_assprod(request):
    date_7 = dt.today()
    date_6 = dt.today() - timedelta(days=1)
    date_5 = dt.today() - timedelta(days=2)
    date_4 = dt.today() - timedelta(days=3)
    date_3 = dt.today() - timedelta(days=4)
    date_2 = dt.today() - timedelta(days=5)
    date_1 = dt.today() - timedelta(days=6)

    week_7 = date_7.strftime('%A')
    week_6 = date_6.strftime('%A')
    week_5 = date_5.strftime('%A')
    week_4 = date_4.strftime('%A')
    week_3 = date_3.strftime('%A')
    week_2 = date_2.strftime('%A')
    week_1 = date_1.strftime('%A')

    eSV_label = []
    eSV_prod = []

    Jets_label = []
    Jets_prod = []

    ACFire_label = []
    ACFire_prod = []

    GISO_label = []
    GISO_prod = []

    GS_label = []
    GS_prod = []


    date_label = [week_1, week_2, week_3, week_4, week_5, week_6, week_7];
    Jets_label = [week_1, week_2, week_3, week_4, week_5, week_6, week_7];
    ACFire_label = [week_1, week_2, week_3, week_4, week_5, week_6, week_7];
    GISO_label = [week_1, week_2, week_3, week_4, week_5, week_6, week_7];
    GS_label = [week_1, week_2, week_3, week_4, week_5, week_6, week_7];

    eSV_prod = getprodquan("eSV", date_7, date_6, date_5, date_4, date_3, date_2, date_1)
    Jets_prod = getprodquan("Jets", date_7, date_6, date_5, date_4, date_3, date_2, date_1)
    ACFire_prod = getprodquan("AC Fire", date_7, date_6, date_5, date_4, date_3, date_2, date_1)
    GISO_prod = getprodquan("GISO", date_7, date_6, date_5, date_4, date_3, date_2, date_1)
    GS_prod = getprodquan("GS", date_7, date_6, date_5, date_4, date_3, date_2, date_1)

    prod_sched_query = WO_Finished.objects.filter()    

    data = {
        "date_label":date_label,
        "eSV_prod": eSV_prod,
        "Jets_prod": Jets_prod,
        "ACFire_prod": ACFire_prod,
        "GISO_prod": GISO_prod,
        "GS_prod": GS_prod
    }
    return JsonResponse(data) # http response

def getprodquan(prod_class, date_7, date_6, date_5, date_4, date_3, date_2, date_1):
    prod_quan = []
    prod_7 = 0
    prod_6 = 0
    prod_5 = 0
    prod_4 = 0
    prod_3 = 0
    prod_2 = 0
    prod_1 = 0

    prodfinish_7 = WO_Finished.objects.filter( date_out=date_7, prod_sched__work_order_number__prod_number__prod_class__prod_class=prod_class )
    for prodfinish in prodfinish_7:
        prod_7 += prodfinish.prod_sched.quantity

    prodfinish_6 = WO_Finished.objects.filter( date_out=date_6, prod_sched__work_order_number__prod_number__prod_class__prod_class=prod_class )
    for prodfinish in prodfinish_6:
        prod_6 += prodfinish.prod_sched.quantity

    prodfinish_5 = WO_Finished.objects.filter( date_out=date_5, prod_sched__work_order_number__prod_number__prod_class__prod_class=prod_class )
    for prodfinish in prodfinish_5:
        prod_5 += prodfinish.prod_sched.quantity

    prodfinish_4 = WO_Finished.objects.filter( date_out=date_4, prod_sched__work_order_number__prod_number__prod_class__prod_class=prod_class )
    for prodfinish in prodfinish_4:
        prod_4 += prodfinish.prod_sched.quantity

    prodfinish_3 = WO_Finished.objects.filter( date_out=date_3, prod_sched__work_order_number__prod_number__prod_class__prod_class=prod_class )
    for prodfinish in prodfinish_3:
        prod_3 += prodfinish.prod_sched.quantity

    prodfinish_2 = WO_Finished.objects.filter( date_out=date_2, prod_sched__work_order_number__prod_number__prod_class__prod_class=prod_class )
    for prodfinish in prodfinish_2:
        prod_2 += prodfinish.prod_sched.quantity

    prodfinish_1 = WO_Finished.objects.filter( date_out=date_1, prod_sched__work_order_number__prod_number__prod_class__prod_class=prod_class )
    for prodfinish in prodfinish_1:
        prod_1 += prodfinish.prod_sched.quantity

    prod_quan = [prod_1, prod_2, prod_3, prod_4, prod_5, prod_6, prod_7]

    return prod_quan