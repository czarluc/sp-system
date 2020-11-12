from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.forms.utils import ValidationError
from django.forms import ModelForm, modelformset_factory
from invsys.models import *
from crispy_forms.helper import FormHelper
from crispy_forms.layout import *

class VisitServiceFormHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super(VisitServiceFormHelper, self).__init__(*args, **kwargs)
        self.layout = Layout(
            Div(Field('service'),css_class='col-sm-4'),
            Div(Field('unit'),css_class='col-sm-4'),
        )

#REGISTRATION
class WarehouseSignUpForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_warehouse = True
        if commit:
            user.save()
        return user
class PlannerSignUpForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_planner = True
        if commit:
            user.save()
        return user
class AssemblySignUpForm(UserCreationForm):
    
    assemblyline = forms.ModelChoiceField(
        queryset=AssemblyLine.objects.all(),
        widget=forms.Select(choices=AssemblyLine.objects.all())
    )

    class Meta(UserCreationForm.Meta):
        model = User

    @transaction.atomic
    def save(self):
        user = super().save(commit=False)
        user.is_assembly = True
        user.save()
        assembly = Assembly.objects.create(user=user)
        assembly.assemblyline = self.cleaned_data.get('assemblyline')
        assembly.save()
        return user
class BaseAnswerInlineFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()

        has_one_correct_answer = False
        for form in self.forms:
            if not form.cleaned_data.get('DELETE', False):
                if form.cleaned_data.get('is_correct', False):
                    has_one_correct_answer = True
                    break
        if not has_one_correct_answer:
            raise ValidationError('Mark at least one answer as correct.', code='no_correct_answer')


#MASTER TABLES
class ItemForm(forms.Form):
    item_number = forms.CharField(max_length=100)
    item_desc = forms.CharField(max_length=100)
    uom = forms.ModelChoiceField(
        queryset=Uom.objects.all(),
        widget=forms.Select(choices=Uom.objects.all(),)
    )
    item_cat = forms.ModelChoiceField(
        queryset=ItemCat.objects.all(),
        widget=forms.Select(choices=ItemCat.objects.all())
    )
    prod_class = forms.ModelChoiceField(
        queryset=ProdClass.objects.all(),
        widget=forms.Select(choices=ProdClass.objects.all())
    )
    barcode = forms.CharField(max_length=100)
    price = forms.IntegerField()
    notes = forms.CharField(
        max_length=2000,
        widget=forms.Textarea(),
        help_text='Write here your message!'
    )
    orderpoint = forms.IntegerField()

    def save(self):
        data = self.cleaned_data
        newitem = Item(item_number=data['item_number'], item_desc=data['item_desc'],uom=data['uom'], item_cat=data['item_cat'],
            prod_class=data['prod_class'], barcode=data['barcode'], price=data['price'], notes=data['notes'], orderpoint=data['orderpoint'])
        newitem.save()

    class Meta:
        model = Item

class ItemModelForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ('item_number','item_desc','uom','item_cat','prod_class','price','notes','orderpoint','image')

ItemFormset = modelformset_factory(
    Item,
    fields=('item_number','item_desc','price','notes', 'orderpoint'),
    extra=1,
    )

class ProductModelForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ('prod_number','prod_desc','uom','prod_type','prod_class','price','notes','image')

ProductItemListFormset = modelformset_factory(
    ProductItemList,
    fields=('item_number','quantity',),
    extra=1,
    )

ProductFormset = modelformset_factory(
    Product,
    fields=('prod_number','prod_desc','prod_type','price','notes'),
    extra=1,
    )

class WarehouseBinForm(forms.ModelForm):
    class Meta:
        model = Warehouse
        fields = ('rack',
            'column',
            'layer',
            'direction',
            'item_cat',
            'prod_class',
            'image',)

WarehouseBinFormset = modelformset_factory(
    Warehouse,
    fields=('rack','column','layer','direction'),
    extra=1,
    )

#RECEIVING
class ShipmentForm(forms.ModelForm):
    class Meta:
        model = Shipment
        fields = ('dr_num',
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

ShipmentPOFormset = modelformset_factory(
    Shipment_PO,
    fields=('po_num',),
    extra=1,
    )

ReceiveShipmentItemFormset = modelformset_factory(
    Receive_Shipment_Item,
    fields=('date_validated','start_time_validation','end_time_validation','validation_time','item_number','item_quantity','notes',),
    extra=1,
    )
ShipmentSummaryFormset = modelformset_factory(
    Shipment_Summary,
    fields=('item_number','purchased_quantity','total_received_quantity','discrepancy','discrepancy_quantity', 'issue',),
    extra=1,)

class ShipmentForm_VDR(forms.ModelForm):
    class Meta:
        model = Shipment
        fields = ('shipment_num','notes',)

ReceiveShipmentItem_VDR_Formset = modelformset_factory(
    Receive_Shipment_Item,
    fields=('shipment_po','date_validated','start_time_validation','end_time_validation','validation_time','item_number','item_quantity','notes',),
    extra=1,
    )

ShipmentSummary_VDR_Formset = modelformset_factory(
    Shipment_Summary,
    fields=('shipment_po','item_number','purchased_quantity','total_received_quantity','discrepancy','discrepancy_quantity', 'issue',),
    extra=1,)

class ResolvePOForm(forms.ModelForm):
    class Meta:
        model = ResolvePO
        fields = ('po_num','notes',)

#PUT AWAY
#--PUT AWAY CREATE SCHEDULE--
class PutAwayScheduleForm(forms.ModelForm):
    class Meta:
        model = Put_Away_Schedule
        fields = ('schedule_num','date_scheduled','notes',)
        labels = {
            'schedule_num':'Put Away Schedule Number',
            'date_scheduled':'Scheduled Date',
            'notes':'Notes',
        }
PutAwayItemFormset = modelformset_factory(
    Put_Away_Items,
        fields=('item_num','required_quantity','bin_location','reference_number',),
        extra=1,
        )
PutAwaySummaryFormset = modelformset_factory(
    Put_Away_Summary,
        fields=('item_num','required_quantity','stored_quantity','bin_location','discrepancy','discrepancy_quantity','status','reference_number'),
        extra=1,
        )
#--PUT AWAY FINISH--
class PutAwayItemForm(forms.ModelForm):
    class Meta:
        model = Put_Away_Items
        fields = ('item_num',)
        labels = {
            'item_num':'Item Number',
        }
class PutaAwaySummaryForm(forms.ModelForm):
    class Meta:
        model = Put_Away_Summary
        fields = ('required_quantity','stored_quantity','bin_location','discrepancy','discrepancy_quantity','status','date_stored','reference_number',)
        labels = {
            'required_quantity':'Required Quantity',
            'stored_quantity':'Stored Quantity',
            'bin_location':'Bin Location',
            'discrepancy':'Discrepancy',
            'discrepancy_quantity':'Discrepancy Quantity',
            'status':'Status',
            'date_stored':'Date Stored',
            'reference_number':'Reference Number',
        }


#WORK ORDER CREATION
class WorkOrderForm(forms.ModelForm):
    class Meta:
        model = Work_Order
        fields = ('work_order_number','customer','order_type','work_order_class','fo_number','tid_number','prod_number','prod_quantity','customer_order_date','otd_customer_req_date','otp_commitment_date','required_completion_date','creation_date','notes',)
WorkOrderItemFormset = modelformset_factory(
    Work_Order_Item_List,
        fields=('item_number','item_quantity',),
        extra=1,
        )
WOProductionSchedFormset = modelformset_factory(
    WO_Production_Schedule,
        fields=('work_order_number','quantity','date_required',),
        extra=1,
        )


#COMPONENT ISSUANCE SCHEDULE
class CompIssuanceScheduleform(forms.ModelForm):
    class Meta:
        model = WO_Issuance_Schedule
        fields = ('schedule_num','date_scheduled','notes',)
        labels = {
            'schedule_num':'Put Away Schedule Number',
            'date_scheduled':'Scheduled Date',
            'notes':'Notes',
        }
WO_Issuance_ListFormset = modelformset_factory(
    WO_Issuance_List,
        fields=('prod_sched',),
        extra=1,
    )

WO_Issuance_RecItemFormset = modelformset_factory(
    WO_Issuance_RecItem,
        fields=('prod_sched','item_num','item_quantity','date_received','notes','bin_location'),
        extra=1,
    )

WO_Issuance_SummaryFormset = modelformset_factory(
    WO_Issuance_Summary,
        fields=('prod_sched','item_num','totalreq_quan','totalrec_quan','discrepancy','discrepancy_quantity','status',),
        extra=1,
    )

#ASSEMBLY UPDATES - ASSEMBLY
class WO_AssemblyForm(forms.ModelForm):
    class Meta:
        model = WO_Assembly
        fields = ('prod_sched','date_received','assembled_by','date_assembled','verified_by','notes',)
        labels = {
            'prod_sched':'Production Schedule ID',
            'date_received':'Date Received',
            'assembled_by':'Assembled By',
            'date_assembled':'Date Assembled',
            'verified_by':'Verified By',
            'notes':'Notes',
        }
#ASSEMBLY UPDATES - COUPLING
class WO_CouplingForm(forms.ModelForm):
    class Meta:
        model = WO_Coupling
        fields = ('prod_sched','date_received','coupled_by','date_coupled','verified_by','notes',)
        labels = {
            'prod_sched':'Production Schedule ID',
            'date_received':'Date Received',
            'coupled_by':'Coupled By',
            'date_coupled':'Date Coupled',
            'verified_by':'Verified By',
            'notes':'Notes',
        }
#ASSEMBLY UPDATES - COUPLING
class WO_TestingForm(forms.ModelForm):
    class Meta:
        model = WO_Testing
        fields = ('prod_sched','date_received','tested_by','date_tested','verified_by','notes',)
        labels = {
            'prod_sched':'Production Schedule ID',
            'date_received':'Date Received',
            'tested_by':'Tested By',
            'date_tested':'Date Tested',
            'verified_by':'Verified By',
            'notes':'Notes',
        }
#RECEIVE PRODUCt
class WO_FinishedForm(forms.ModelForm):
    class Meta:
        model = WO_Finished
        fields = ('prod_sched','date_received','name_plate','label_sticker','iom','qr_code','wrnty_card','packaging','date_out','checked_by','notes',)
Warehouse_ProductsFormset = modelformset_factory(
    Warehouse_Products,
        fields=('bin_location','quantity',),
        extra=1,
    )

#SHIPPING_OUTBOUND
class Shipping_OutboundForm(forms.ModelForm):
    class Meta:
        model = Shipping_Outbound
        fields = ('wo_num','ship_out_num','notes',)

#PACKING
#--PACKING CREATE SCHEDULE--
class PackingScheduleForm(forms.ModelForm):
    class Meta:
        model = Packing_Schedule
        fields = ('schedule_num','date_scheduled','notes',)
PackingProductFormset = modelformset_factory(
    Packing_Product,
        fields=('wo_num','prod_num','required_quantity','bin_location','reference_number',),
        extra=1,
        )
PackingSummaryFormset = modelformset_factory(
    Packing_Summary,
        fields=('wo_num',
            'prod_num',
            'required_quantity',
            'picked_quantity',
            'bin_location',
            'discrepancy',
            'discrepancy_quantity',
            'status',
            'reference_number',),
        extra=1,
        )


#SHRINKAGE REPORT
class Shrinkage_Ass_ReportForm(forms.ModelForm):
    class Meta:
        model = Shrinkage_Ass_Report
        fields = ('prod_sched','item_number','quantity','shrinkage_type','reason','date_reported',)
        labels = {
            'prod_sched':'Production Schedule ID',
            'item_number':'Item Number',
            'quantity':'Quantity',
            'shrinkage_type':'Shrinkage Type',
            'reason':'Reason',
            'date_reported':'Date Reported',
        }
class Shrinkage_Ass_ItemForm(forms.ModelForm):
    class Meta:
        model = Shrinkage_Ass_Item
        fields = ('item_number','quantity',)
        labels = {
            'item_number':'Item Number',
            'quantity':'Quantity',
            'ass_location':'Assembly Location',
        }
#REQUEST SCHED
class Request_ScheduleForm(forms.ModelForm):
    class Meta:
        model = Request_Schedule
        fields = ('schedule_num','date_scheduled','notes',)
        labels = {
            'schedule_num':'Schedule Number',
            'date_scheduled':'Date Scheduled',
            'notes':'Notes',
        }
Request_ItemFormset = modelformset_factory(
    Request_Item, 
        fields=('prod_sched','item_number','quantity','location_from','location_to','refnum',),
        extra=1,
    )

PartReq_Issuance_RecItemFormset = modelformset_factory(
    Request_RecItem,
        fields=('prod_sched','item_number','date_received','rec_quantity','notes','bin_location','ass_location'),
        extra=1,
    )

PartReq_Issuance_SummaryFormset = modelformset_factory(
    Request_Summary,
        fields=('prod_sched','item_number','totalreq_quan','totalrec_quan','discrepancy','discrepancy_quantity','status','bin_location','ass_location'),
        extra=1,
    )

class ComponentReturn_ScheduleForm(forms.ModelForm):
    class Meta:
        model = ComponentReturn_Schedule
        fields = ('schedule_num','date_scheduled','notes',)
        labels = {
            'schedule_num':'Schedule Number',
            'date_scheduled':'Date Scheduled',
            'notes':'Notes',
        }

ComponentReturn_ItemFormset = modelformset_factory(
    ComponentReturn_Item, 
        fields=('prod_sched','item_number','quantity','location_from',),
        extra=1,
    )

CompReturn_RecItemFormset = modelformset_factory(
    ComponentReturn_RecItem,
        fields=('prod_sched','item_number','quantity','notes','ass_location',),
        extra=1,
    )

CompReturn_SummaryFormset = modelformset_factory(
    ComponentReturn_Summary,
        fields=('prod_sched','item_number','totalreq_quan','totalrec_quan','discrepancy','discrepancy_quantity','status','ass_location',),
        extra=1,
    )


#UPDATE WHSE
class DMMR_ReportForm(forms.ModelForm):
    class Meta:
        model = DMMR_Report
        fields = ('report_num','iaf_whse','date_reported',"notes")
        labels = {
            'report_num':'Report Number',
            'iaf_whse':'Warehouse',
            'date_reported':'Date Reported',
            'notes':'Notes',
        }

DMMR_Item_Formset = modelformset_factory(
    DMMR_Item, 
        fields=('bin_location','item_number','item_quantity','total_cost',"reason"),
        extra=1,
    )

class DFMR_ReportForm(forms.ModelForm):
    class Meta:
        model = DFMR_Report
        fields = ('report_num','iaf_whse','date_reported',"notes")
        labels = {
            'report_num':'Report Number',
            'iaf_whse':'Warehouse',
            'date_reported':'Date Reported',
            'notes':'Notes',
        }

DFMR_Item_Formset = modelformset_factory(
    DFMR_Item, 
        fields=('bin_location','item_number','item_quantity','total_cost',"reason"),
        extra=1,
    )

class SA_ReportForm(forms.ModelForm):
    class Meta:
        model = SA_Report
        fields = ('report_num','iaf_whse','date_reported',"notes")
        labels = {
            'report_num':'Report Number',
            'iaf_whse':'Warehouse',
            'date_reported':'Date Reported',
            'notes':'Notes',
        }

SA_Item_Formset = modelformset_factory(
    SA_Item, 
        fields=('bin_location','item_number','item_quantity',"iaf_operator",'total_cost',"reason", ),
        extra=1,
    )


class Dismantle_ReportForm(forms.ModelForm):
    class Meta:
        model = Dismantle_Report
        fields = ('report_num','iaf_whse','date_reported',"notes")
        labels = {
            'report_num':'Report Number',
            'iaf_whse':'Warehouse',
            'date_reported':'Date Reported',
            'notes':'Notes',
        }

class Dismantle_ProductForm(forms.ModelForm):
    class Meta:
        model = Dismantle_Product
        fields = ('prod_sched','bin_location',"prod_quantity", "total_cost", "reason")

Dismantle_Item_Formset = modelformset_factory(
    Dismantle_Item, 
        fields=('item_number', 'item_quantity', "total_cost"),
        extra=1,
    )

class Transfer_ReportForm(forms.ModelForm):
    class Meta:
        model = Transfer_Report
        fields = ('report_num','iaf_whse','date_reported',"notes")

Transfer_Item_Formset = modelformset_factory(
    Transfer_Item, 
        fields=('bin_location','item_number','item_quantity',"iaf_operator",'total_cost',"reason", ),
        extra=1,
    )

#UPDATE PURCHASE ORDERS
Purchase_Order_Formset = modelformset_factory(
    Purchase_Order, 
        fields=('po_number', 'purchase_date'),
        extra=1,
    )

Purchase_Order_Item_Formset = modelformset_factory(
    Purchase_Order_Item, 
        fields=('po_number','item_number', 'item_quantity'),
        extra=1,
    )

