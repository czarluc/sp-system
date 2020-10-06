from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView, UpdateView

from ..decorators import assembly_required
from ..forms import *
from ..models import *


class AssemblySignUpView(CreateView):
    model = User
    form_class = AssemblySignUpForm
    template_name = 'registration/signup_form.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'assembly'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('assembly:assembly_home')
@login_required
@assembly_required
def AssemblyHome(request):
    return render(request, 'invsys/assembly/assembly_home.html')

#--Assembly Updates
@login_required
@assembly_required
def FinishAssembly(request):
    template_name = 'invsys/assembly/AssemblyUpdates/FinishAssembly.html'
    if request.method == 'GET':
        wo_assemblyform = WO_AssemblyForm(request.GET or None)

        return render(request, template_name, {'wo_assembly':wo_assemblyform,'user':request.user})

    elif request.method == 'POST' :
        wo_assemblyform = WO_AssemblyForm(request.POST)
        if wo_assemblyform.is_valid():
            wo_assemblyform = wo_assemblyform.save(commit=False)

            wo_assembly = WO_Assembly.objects.get(prod_sched=wo_assemblyform.prod_sched)
            wo_assembly.assembled_by = wo_assemblyform.assembled_by
            wo_assembly.date_assembled = wo_assemblyform.date_assembled
            wo_assembly.verified_by = wo_assemblyform.verified_by
            wo_assembly.notes = wo_assemblyform.notes
            wo_assembly.cleared = True
            wo_assembly.save()

            prod_sched = WO_Production_Schedule.objects.get(id=wo_assemblyform.prod_sched.id)
            prod_sched.assembled = True
            prod_sched.status = "In Coupling"
            prod_sched.save()
            
            wo_coupling = WO_Coupling.objects.create(prod_sched=prod_sched, date_received=wo_assembly.date_assembled)
            wo_coupling.full_clean()
            wo_coupling.save()
            
        return redirect('home')

def FinishAssembly_SelectProdSched(request):
    template_name = 'invsys/assembly/AssemblyUpdates/FinishAssembly_SelectProdSched.html'

    wo_asslist = WO_Assembly.objects.filter(cleared=False).values(
        'prod_sched__id',
        'prod_sched__work_order_number__work_order_number',
        'prod_sched__work_order_number__prod_number__prod_number',
        'prod_sched__work_order_number__prod_number__prod_class__prod_class',
        'prod_sched__quantity',
        'date_received',)

    wo_asslist_query = WO_Assembly.objects.filter(cleared=False)
    prodsched = []
    for wo in wo_asslist_query:
        prodsched.append(wo.prod_sched.id)

    wo_itemasslist = Assembly_Items.objects.filter(reference_number__in=prodsched).values(
        'reference_number',
        'item_number__item_number',
        'quantity',
        'assemblyline__name',)

    return render(request, template_name, {'wo_asslist':wo_asslist,'wo_itemasslist':wo_itemasslist})

@login_required
@assembly_required
def FinishCoupling(request):
    template_name = 'invsys/assembly/AssemblyUpdates/FinishCoupling.html'
    if request.method == 'GET':
        wo_couplingform = WO_CouplingForm(request.GET or None)

        return render(request, template_name, {'wo_coupling':wo_couplingform,'user':request.user})

    elif request.method == 'POST' :
        wo_couplingform = WO_CouplingForm(request.POST)
        if wo_couplingform.is_valid():
            wo_couplingform = wo_couplingform.save(commit=False)

            wo_coupling = WO_Coupling.objects.get(prod_sched=wo_couplingform.prod_sched)
            wo_coupling.coupled_by = wo_couplingform.coupled_by
            wo_coupling.date_coupled = wo_couplingform.date_coupled
            wo_coupling.verified_by = wo_couplingform.verified_by
            wo_coupling.notes = wo_couplingform.notes
            wo_coupling.cleared = True
            wo_coupling.save()

            prod_sched = WO_Production_Schedule.objects.get(id=wo_couplingform.prod_sched.id)
            prod_sched.coupled = True
            prod_sched.status = "In Testing"
            prod_sched.save()

            wo_testing = WO_Testing.objects.create(prod_sched=prod_sched, date_received=wo_coupling.date_coupled)
            wo_testing.full_clean()
            wo_testing.save()
            
        return redirect('home')
def FinishCoupling_SelectProdSched(request):
    template_name = 'invsys/assembly/AssemblyUpdates/FinishCoupling_SelectProdSched.html'

    wo_couplist = WO_Coupling.objects.filter(cleared=False).values(
        'prod_sched__id',
        'prod_sched__work_order_number__work_order_number',
        'prod_sched__work_order_number__prod_number__prod_number',
        'prod_sched__work_order_number__prod_number__prod_class__prod_class',
        'prod_sched__quantity',
        'date_received',)

    wo_couplist_query = WO_Coupling.objects.filter(cleared=False)
    prodsched = []
    for wo in wo_couplist_query:
        prodsched.append(wo.prod_sched.id)

    wo_itemcouplist = Assembly_Items.objects.filter(reference_number__in=prodsched).values(
        'reference_number',
        'item_number__item_number',
        'quantity',
        'assemblyline__name',)

    return render(request, template_name, {'wo_couplist':wo_couplist,'wo_itemcouplist':wo_itemcouplist})


@login_required
@assembly_required
def FinishTesting(request):
    template_name = 'invsys/assembly/AssemblyUpdates/FinishTesting.html'
    if request.method == 'GET':
        wo_testingform = WO_TestingForm(request.GET or None)

        return render(request, template_name, {'wo_testing':wo_testingform,'user':request.user})

    elif request.method == 'POST' :
        wo_testingform = WO_TestingForm(request.POST)
        if wo_testingform.is_valid():
            wo_testingform = wo_testingform.save(commit=False)

            wo_testing = WO_Testing.objects.get(prod_sched=wo_testingform.prod_sched)
            wo_testing.tested_by = wo_testingform.tested_by
            wo_testing.date_tested = wo_testingform.date_tested
            wo_testing.verified_by = wo_testingform.verified_by
            wo_testing.notes = wo_testingform.notes
            wo_testing.cleared = True
            wo_testing.save()

            prod_sched = WO_Production_Schedule.objects.get(id=wo_testingform.prod_sched.id)
            prod_sched.tested = True
            prod_sched.status = "Finished"
            prod_sched.save()

            wo_finished = WO_Finished.objects.create(prod_sched=prod_sched, date_received=wo_testing.date_tested)
            wo_finished.full_clean()
            wo_finished.save()
                       
        return redirect('home')
def FinishTesting_SelectProdSched(request):
    template_name = 'invsys/assembly/AssemblyUpdates/FinishTesting_SelectProdSched.html'
    wo_testlist = WO_Testing.objects.filter(cleared=False).values(
        'prod_sched__id',
        'prod_sched__work_order_number__work_order_number',
        'prod_sched__work_order_number__prod_number__prod_number',
        'prod_sched__work_order_number__prod_number__prod_class__prod_class',
        'prod_sched__quantity',
        'date_received',)

    wo_testlist_query = WO_Testing.objects.filter(cleared=False)
    prodsched = []
    for wo in wo_testlist_query:
        prodsched.append(wo.prod_sched.id)

    wo_itemtestlist = Assembly_Items.objects.filter(reference_number__in=prodsched).values(
        'reference_number',
        'item_number__item_number',
        'quantity',
        'assemblyline__name',)

    return render(request, template_name, {'wo_testlist':wo_testlist,'wo_itemtestlist':wo_itemtestlist})
def AddtoFinish(prodsched, date_received):
    wo_testing = WO_Testing.objects.create(
        prod_sched=prodsched, 
        date_received=date_received)
    wo_testing.full_clean()
    return wo_testing
def UpdateProdSched_FTest(prod_sched):
    prod_sched.coupled = True
    prod_sched.status = "In Testing"

@login_required
@assembly_required
def ViewPendingWO(request):
    prod_sched_list = WO_Production_Schedule.objects.filter(issued=True, received=False).values(
        'id',
        'work_order_number__work_order_number',
        'quantity',
        'date_required',
        'status',)
    
    wo_filter = []
    for prodsched in prod_sched_list:
        wo_filter.append(prodsched.get("work_order_number__work_order_number"))
    
    prodsched_filter = []
    for prodsched in prod_sched_list:
        prodsched_filter.append(prodsched.get("id"))
    
    wo_list = Work_Order.objects.filter(work_order_number__in=wo_filter).values(
        'work_order_number',
        'prod_number__prod_number',
        'prod_number__prod_desc',
        'prod_number__uom',
        'prod_number__prod_type',
        'prod_number__prod_class',
        'prod_number__barcode',
        'prod_number__price',)
    
    issuance_list = WO_Issuance_List.objects.filter(prod_sched__in=prodsched_filter).values(
        'prod_sched__id',
        'cleared',
        'issues',
        'issued_by',
        'date_issued',
        'verified_by',
        'notes',)
    
    assembly_list = WO_Assembly.objects.filter(prod_sched__in=prodsched_filter).values(
        'prod_sched__id',
        'date_received',
        'assembled_by',
        'date_assembled',
        'verified_by',
        'notes',
        'cleared',)
    
    coupling_list = WO_Coupling.objects.filter(prod_sched__in=prodsched_filter).values(
        'prod_sched__id',
        'date_received',
        'coupled_by',
        'date_coupled',
        'verified_by',
        'notes',
        'cleared',)
    
    testing_list = WO_Testing.objects.filter(prod_sched__in=prodsched_filter).values(
        'prod_sched__id',
        'date_received',
        'tested_by',
        'date_tested',
        'verified_by',
        'notes',
        'cleared',)
    
    return render(request, 'invsys/assembly/AssemblyUpdates/ViewPendingWO.html', 
        {'prod_sched_set':prod_sched_list, 
        'wo_set':wo_list,
        'issuance_set':issuance_list,
        'assembly_set':assembly_list,
        'coupling_set':coupling_list,
        'testing_set':testing_list,})

@login_required
@assembly_required
def ReportShrinkage(request):
    template_name = 'invsys/assembly/AssemblyShrinkage/ReportShrinkage.html'
    if request.method == 'GET':

        shrnk_reportform = Shrinkage_Ass_ReportForm(request.GET or None, prefix='report')
        shrnk_itemform = Shrinkage_Ass_ItemForm(request.GET or None, prefix='item')

        shrnk_reports = Shrinkage_Ass_Report.objects.all()
        print(shrnk_reports)
        if len(shrnk_reports) > 0:
            next_reportid = Shrinkage_Ass_Report.objects.order_by('-report_num').first().report_num + 1
        else:
            next_reportid = 1

        return render(request, template_name,{'shrnk_reportform':shrnk_reportform,'shrnk_itemform':shrnk_itemform,'next_reportid':next_reportid})

    elif request.method == 'POST' :

        shrnk_reportform = Shrinkage_Ass_ReportForm(request.POST, request.FILES, prefix='report')
        shrnk_itemform = Shrinkage_Ass_ItemForm(request.POST, request.FILES, prefix='item')

        if shrnk_reportform.is_valid() and shrnk_itemform.is_valid():
            shrnk_report = shrnk_reportform.save(commit=False)
            shrnk_report.save()
            shrnk_item = shrnk_itemform.save(commit=False)
            shrnk_item.report_num = shrnk_report 
            shrnk_item.save()
            totalallocated = 0

            AllocateWhseItems_Shrnk(shrnk_item.item_number, shrnk_item.quantity, totalallocated, shrnk_report.prod_sched.id)
            UpdateAssemblyItems(shrnk_report.prod_sched.id, shrnk_item.item_number, shrnk_item.quantity)
            DeleteWhseItemBin()
            AddShrnkReportTransac(shrnk_report.prod_sched.id, shrnk_report.date_reported, shrnk_report.item_number, shrnk_report.quantity, shrnk_item.ass_location.name)
            AddShrnkRplItemTransac(shrnk_report.prod_sched.id, shrnk_report.date_reported, shrnk_item.item_number, shrnk_item.quantity, shrnk_item.ass_location.name)
            return redirect('home')
    
        return redirect('home')
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
def UpdateAssemblyItems(prod_sched, item_num, item_quan):
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
            totalalloc, whsebin = SubtractBinStock(whsebin, totalreq, totalalloc, itemnum, prod_sched)
            whsebin.save()
def SubtractBinStock(whsebin, totalreq, totalalloc, itemnum, prod_sched):
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
        
        
#ISSUANCE ACCURACY
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
#ASSEMBLY TIMELINESS
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
#PRODUCTION VOLUME
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