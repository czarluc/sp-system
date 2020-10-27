from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.html import escape, mark_safe
from django.core.validators import FileExtensionValidator

#REGISTRATION
class User(AbstractUser):
    is_warehouse = models.BooleanField(default=False)
    is_planner = models.BooleanField(default=False)
    is_assembly = models.BooleanField(default=False)
class AssemblyLine(models.Model):
    name = models.CharField(max_length=255)
    
    class Meta: 
        verbose_name = "Assembly Line"
        verbose_name_plural = "Assembly Lines"

    def __str__(self):
        return self.name
class Assembly(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    assemblyline = models.ForeignKey(AssemblyLine, default='1', blank=True, on_delete=models.CASCADE)

    class Meta: 
        verbose_name = "Assembly"
        verbose_name_plural = "Assemblies"

    def __str__(self):
        return self.user.username

#MASTER TABLES
class ItemCat(models.Model):
    item_cat = models.CharField(max_length=100, default=False)

    class Meta: 
        verbose_name = "Item Category"
        verbose_name_plural = "Item Categories"

    def __str__(self):
        return self.item_cat
class ProdClass(models.Model):
    prod_class = models.CharField(max_length=100, default=False)

    class Meta: 
        verbose_name = "Product Class"
        verbose_name_plural = "Product Classes"

    def __str__(self):
        return self.prod_class
class Uom(models.Model):
    uom = models.CharField(max_length=100, default=False)

    def __str__(self):
        return self.uom

def upload_item_location(instance, filename):
    return "%s/%s" %("item", instance.item_number)

class Item(models.Model):
    item_number = models.CharField(max_length=100, default='', primary_key=True)
    item_desc = models.CharField(max_length=100, default='')
    uom = models.ForeignKey(Uom, default='1', blank=True, on_delete=models.CASCADE)
    item_cat = models.ForeignKey(ItemCat, default='1', blank=True, on_delete=models.CASCADE)
    prod_class = models.ForeignKey(ProdClass, default='1', blank=True, on_delete=models.CASCADE)
    barcode = models.CharField(max_length=100, default='', blank=True, null=True)
    price = models.IntegerField(blank=True, null=True)
    notes = models.CharField(max_length=200, default='')
    orderpoint = models.IntegerField(blank=True, null=True)
    image = models.ImageField(upload_to='item/',
        null=True,
        blank=True,
        width_field="width_field",
        height_field="height_field")
    width_field = models.IntegerField(default=0,null=True, blank=True)
    height_field = models.IntegerField(default=0,null=True, blank=True)

    def __str__(self):
        return self.item_number

def upload_prod_location(instance, filename):
    return "%s/%s" %("product", instance.prod_number)

class Product(models.Model):
    prod_number = models.CharField(max_length=100, default='', primary_key=True)
    prod_desc = models.CharField(max_length=100, default='')
    uom = models.ForeignKey(Uom, default='1', blank=True, on_delete=models.CASCADE)
    prod_type = models.CharField(max_length=100, default='')
    prod_class = models.ForeignKey(ProdClass, default='1', blank=True, on_delete=models.CASCADE)
    barcode = models.CharField(max_length=100, default='', blank=True, null=True)
    price = models.IntegerField(blank=True, null=True)
    notes = models.CharField(max_length=200, default='')
    image = models.ImageField(upload_to='product/',
        null=True,
        blank=True,
        width_field="width_field",
        height_field="height_field")
    width_field = models.IntegerField(default=0,null=True, blank=True)
    height_field = models.IntegerField(default=0,null=True, blank=True)

    def __str__(self):
        return self.prod_number

class ProductItemList(models.Model):
    prod_number = models.ForeignKey(Product, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    quantity = models.IntegerField(blank=True, null=True)

    class Meta: 
        verbose_name = "Product Item List"
        verbose_name_plural = "Product Item Lists"

    def __str__(self):
        return '%s %s' % (self.prod_number, self.item_number)

class Assembly_Items(models.Model):
    assemblyline = models.ForeignKey(AssemblyLine, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    quantity = models.IntegerField(blank=True, null=True)
    status = models.CharField(max_length=200, default='')
    reference_number = models.CharField(max_length=200, default='')

    class Meta: 
        verbose_name = "Assembly Item"
        verbose_name_plural = "Assembly Items"

    def __str__(self):
        return '%s %s' % (self.assemblyline, self.item_number)

class Assembly_Line_Assignment(models.Model):
    assemblyline = models.ForeignKey(AssemblyLine, default='1', blank=True, null=True, on_delete=models.CASCADE)
    prod_class = models.ForeignKey(ProdClass, default='1', blank=True, null=True, on_delete=models.CASCADE)

    class Meta: 
        verbose_name = "Assembly Line Assignment"
        verbose_name_plural = "Assembly Line Assignments"

    def __str__(self):
        return '%s %s' % (self.assemblyline, self.prod_class)

class Assembly_Discrepancy(models.Model):
    assemblyline = models.ForeignKey(AssemblyLine, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    quantity = models.IntegerField(blank=True, null=True)
    status = models.CharField(max_length=200, default='')
    reference_number = models.CharField(max_length=200, default='')

    class Meta: 
        verbose_name = "Assembly Discrepancy"
        verbose_name_plural = "Assembly Discrepancies"

    def __str__(self):
        return '%s %s' % (self.assemblyline, self.item_number)

def upload_whse_location(instance, filename):
    return "%s/%s" %("whse", instance.bin_location)

class Warehouse(models.Model):
    bin_location = models.CharField(max_length=200, default='')
    rack = models.CharField(max_length=200, default='')
    column = models.CharField(max_length=200, default='')
    layer = models.CharField(max_length=200, default='')
    direction = models.CharField(max_length=200, default='')
    item_cat = models.ForeignKey(ItemCat, default='1', blank=True, on_delete=models.CASCADE)
    prod_class = models.ForeignKey(ProdClass, default='1', blank=True, on_delete=models.CASCADE)
    barcode = models.CharField(max_length=100, default='', blank=True, null=True)
    image = models.ImageField(upload_to='whse/',
        null=True,
        blank=True,
        width_field="width_field",
        height_field="height_field")
    width_field = models.IntegerField(default=0,null=True, blank=True)
    height_field = models.IntegerField(default=0,null=True, blank=True)

    class Meta: 
        verbose_name = "Warehouse"
        verbose_name_plural = "Warehouses"
    def __str__(self):
        return self.bin_location

class Warehouse_Items(models.Model):
    bin_location = models.ForeignKey(Warehouse, default='1', blank=True, on_delete=models.CASCADE)
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    quantity = models.IntegerField(blank=True, null=True)
    status = models.CharField(max_length=200, default='')
    reference_number = models.CharField(max_length=200, default='')

    class Meta: 
        verbose_name = "Warehouse Item"
        verbose_name_plural = "Warehouse Items"

    def __str__(self):
        return '%s %s %s %s' % (self.bin_location, self.item_number, self.reference_number, self.status)
class Warehouse_Products(models.Model):
    bin_location = models.ForeignKey(Warehouse, default='1', blank=True, on_delete=models.CASCADE)
    prod_number = models.ForeignKey(Product, default='1', blank=True, null=True, on_delete=models.CASCADE)
    quantity = models.IntegerField(blank=True, null=True)
    status = models.CharField(max_length=200, default='')
    reference_number = models.CharField(max_length=200, default='')

    class Meta: 
        verbose_name = "Warehouse Product"
        verbose_name_plural = "Warehouse Products"

    def __str__(self):
        return '%s %s' % (self.bin_location, self.prod_number)
class Work_Order(models.Model):
    work_order_number = models.CharField(max_length=200, default='', primary_key=True)
    customer = models.CharField(max_length=200, default='')
    order_type = models.CharField(max_length=200, default='')
    work_order_class = models.CharField(max_length=200, default='')
    fo_number = models.CharField(max_length=200, default='')
    barcode = models.CharField(max_length=200, default='', blank=True, null=True)
    tid_number = models.CharField(max_length=200, default='')
    prod_number = models.ForeignKey(Product, default='1', blank=True, null=True, on_delete=models.CASCADE)
    prod_quantity = models.IntegerField(blank=True, null=True)
    customer_order_date = models.DateField(auto_now=False, auto_now_add=False)
    otd_customer_req_date = models.DateField(auto_now=False, auto_now_add=False)
    otp_commitment_date = models.DateField(auto_now=False, auto_now_add=False)
    required_completion_date = models.DateField(auto_now=False, auto_now_add=False)
    finished_completion_date = models.DateField(auto_now=False, auto_now_add=False)
    creation_date = models.DateField(auto_now=False, auto_now_add=False)
    allocated = models.BooleanField(default=False)
    notes = models.CharField(max_length=200, default='')

    class Meta: 
        verbose_name = "Work Order"
        verbose_name_plural = "Work Orders"

    def __str__(self):
        return self.work_order_number
class Work_Order_Item_List(models.Model):
    work_order_number = models.ForeignKey(Work_Order, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_quantity = models.IntegerField(blank=True, null=True)

    class Meta: 
        verbose_name = "Work Order Item"
        verbose_name_plural = "Work Order Items"

    def __str__(self):
        return '%s %s' % (self.work_order_number, self.item_number)

#RECEIVING PROCESS
class Purchase_Order(models.Model):
    po_number = models.CharField(max_length=200, default='', primary_key=True)
    purchase_date = models.DateField(auto_now=False, auto_now_add=False)
    notes = models.CharField(max_length=200, default='')
    supplier = models.CharField(max_length=200, default='')
    cleared = models.BooleanField(default=False)
    issues = models.BooleanField(default=False)

    class Meta: 
        verbose_name = "Purchase Order"
        verbose_name_plural = "Purchase Orders"

    def __str__(self):
        return self.po_number
class Purchase_Order_Item(models.Model):
    po_number = models.ForeignKey(Purchase_Order, default='8000', blank=True, null=True, on_delete=models.CASCADE)
    item_number = models.ForeignKey(Item, default='', blank=True, null=True, on_delete=models.CASCADE)
    item_quantity = models.IntegerField(blank=True, null=True)

    class Meta: 
        verbose_name = "Purchase Order Item"
        verbose_name_plural = "Purchase Order Items"

    def __str__(self):
        return '%s %s' % (self.po_number, self.item_number)
class Shipment(models.Model):
    shipment_num = models.AutoField(primary_key=True)
    dr_num = models.CharField(max_length=200, default=' ', blank=True, null=True)
    rr_num = models.CharField(max_length=200, default=' ', blank=True, null=True)
    invoice_num = models.CharField(max_length=200, default=' ', blank=True, null=True)
    ship_trucking = models.CharField(max_length=200, default='', blank=True, null=True)
    ship_category = models.CharField(max_length=200, default='', blank=True, null=True)
    container_num = models.CharField(max_length=200, default=' ', blank=True, null=True)
    container_type = models.CharField(max_length=200, default='', blank=True, null=True)
    awl_bl = models.CharField(max_length=200, default=' ', blank=True, null=True)
    notes = models.CharField(max_length=200, default='')
    date_dr = models.DateField(auto_now_add=False, blank=True, null=True)
    date_warehouse = models.DateField(auto_now_add=False, blank=True, null=True)
    cleared = models.BooleanField(default=False)

    class Meta: 
        verbose_name = "Shipment"
        verbose_name_plural = "Shipments"
    def __str__(self):
        return str(self.shipment_num)

class Shipment_PO(models.Model):
    shipment_num = models.ForeignKey(Shipment, default='1', blank=True, null=True, on_delete=models.CASCADE)
    po_num = models.ForeignKey(Purchase_Order, default='1', blank=True, null=True, on_delete=models.CASCADE)
    validated = models.BooleanField(default=False)

    class Meta: 
        verbose_name = "Shipment POs"
        verbose_name_plural = "Shipment POs"
    def __str__(self):
        return '%s %s' % (self.shipment_num, self.po_num)

class Receive_Shipment_Item(models.Model):
    shipment_po = models.ForeignKey(Shipment_PO, default='1', blank=True, null=True, on_delete=models.CASCADE)
    date_validated = models.DateField(auto_now_add=False, blank=True, null=True)
    start_time_validation = models.TimeField(auto_now=False, auto_now_add=False, null=True, blank=True)
    end_time_validation = models.TimeField(auto_now=False, auto_now_add=False, null=True, blank=True)
    validation_time = models.IntegerField(blank=True, null=True)
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_quantity = models.IntegerField(blank=True, null=True)
    notes = models.CharField(max_length=200, default=' ', blank=True, null=True)

    class Meta: 
        verbose_name = "Receive Shipment Item"
        verbose_name_plural = "Receive Shipment Items"

    def __str__(self):
        return '%s %s %s' % (self.shipment_po, self.date_validated, self.item_number)

class Shipment_Summary(models.Model):
    shipment_po = models.ForeignKey(Shipment_PO, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    purchased_quantity = models.IntegerField(blank=True, null=True)
    total_received_quantity = models.IntegerField(blank=True, null=True)
    discrepancy = models.BooleanField(default=False)
    discrepancy_quantity = models.IntegerField(blank=True, null=True)
    issue = models.CharField(max_length=200, default='', blank=True, null=True)
    received = models.BooleanField(default=False)

    class Meta: 
        verbose_name = "Shipment Summary"
        verbose_name_plural = "Shipment Summaries"

    def __str__(self):
        return '%s %s' % (self.shipment_po, self.item_number)

class InboundLobby(models.Model):
    shipment_num = models.ForeignKey(Shipment, default='1', blank=True, null=True, on_delete=models.CASCADE)
    date_in = models.DateTimeField(null=True,blank=True)

    def __str__(self):
        return '%s %s' % (self.id, self.shipment_num)

class Receiving_Lobby(models.Model):
    reference_number = models.CharField(max_length=200, default='')
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    received_quantity = models.IntegerField(blank=True, null=True)
    scheduled_quantity = models.IntegerField(blank=True, null=True)
    date_received = models.DateField(auto_now_add=True)
    time_received = models.TimeField(auto_now_add=True)
    status = models.CharField(max_length=200, default='', blank=True, null=True)

    class Meta: 
        verbose_name = "Receiving Lobby Item"
        verbose_name_plural = "Receiving Lobby Items"

    def __str__(self):
        return '%s %s' % (self.reference_number, self.item_number)
class VDR_Lobby(models.Model):
    po_number = models.CharField(max_length=200, default='')
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    purchased_quantity = models.IntegerField(blank=True, null=True)
    received_quantity = models.IntegerField(blank=True, null=True)
    date_received = models.DateField(auto_now_add=True)
    time_received = models.TimeField(auto_now_add=True)
    status = models.CharField(max_length=200, default='')

    class Meta: 
        verbose_name = "VDR Lobby Item"
        verbose_name_plural = "VDR Lobby Items"

    def __str__(self):
        return '%s %s' % (self.po_number, self.item_number)
class Shipment_Transaction(models.Model):
    reference_number = models.CharField(max_length=200, default='')
    transaction_type = models.CharField(max_length=200, default='')
    transaction_date = models.DateField(auto_now_add=True)
    transaction_location = models.CharField(max_length=200, default='')
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_quantity = models.IntegerField(blank=True, null=True)

    class Meta: 
        verbose_name = "Shipment Transaction"
        verbose_name_plural = "Shipment Transactions"

    def __str__(self):
        return '%s %s' % (self.reference_number, self.item_number)
class RecLobby_Transaction(models.Model):
    reference_number = models.CharField(max_length=200, default='')
    transaction_type = models.CharField(max_length=200, default='')
    transaction_date = models.DateField(auto_now_add=True)
    transaction_location = models.CharField(max_length=200, default='')
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_quantity = models.IntegerField(blank=True, null=True)

    class Meta: 
        verbose_name = "Receiving Lobby Transaction"
        verbose_name_plural = "Receiving Lobby Transactions"

    def __str__(self):
        return '%s %s' % (self.reference_number, self.item_number)
class VDRLobby_Transaction(models.Model):
    reference_number = models.CharField(max_length=200, default='')
    transaction_type = models.CharField(max_length=200, default='')
    transaction_date = models.DateField(auto_now_add=True)
    transaction_location = models.CharField(max_length=200, default='')
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_quantity = models.IntegerField(blank=True, null=True)

    class Meta: 
        verbose_name = "VDR Lobby Transaction"
        verbose_name_plural = "VDR Lobby Transactions"

    def __str__(self):
        return '%s %s' % (self.reference_number, self.item_number)
class VDR_To_Receiving_Transaction(models.Model):
    reference_number = models.CharField(max_length=200, default='')
    transaction_type = models.CharField(max_length=200, default='')
    transaction_date = models.DateField(auto_now_add=True)
    transaction_location = models.CharField(max_length=200, default='')
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_quantity = models.IntegerField(blank=True, null=True)

    class Meta: 
        verbose_name = "VDR to Receiving Transaction"
        verbose_name_plural = "VDR to Receiving Transactions"

    def __str__(self):
        return '%s %s' % (self.reference_number, self.item_number)

class ResolvePO(models.Model):
    po_num = models.ForeignKey(Purchase_Order, default='1', blank=True, null=True, on_delete=models.CASCADE)
    date_resolved = models.DateField(auto_now_add=False,blank=True, null=True)
    notes = models.CharField(max_length=200, default='', blank=True, null=True)

    class Meta: 
        verbose_name = "Resolve PO"
        verbose_name_plural = "Resolve POs"

    def __str__(self):
        return '%s %s' % (self.id, self.po_num)

class ResolvePO_Transaction(models.Model):
    reference_number = models.CharField(max_length=200, default='')
    transaction_type = models.CharField(max_length=200, default='')
    transaction_date = models.DateField(auto_now_add=True)
    transaction_location = models.CharField(max_length=200, default='')
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_quantity = models.IntegerField(blank=True, null=True)

    class Meta: 
        verbose_name = "Resolve PO Transaction"
        verbose_name_plural = "Resolve PO Transactions"

    def __str__(self):
        return '%s %s' % (self.reference_number, self.item_number)

#Put Away
class Put_Away_Schedule(models.Model):
    schedule_num = models.AutoField(primary_key=True)
    date_scheduled = models.DateField(auto_now=False)
    notes = models.CharField(max_length=200, default='')
    cleared = models.BooleanField(default=False)
    issues = models.BooleanField(default=False)
    class Meta: 
        verbose_name = "Put Away Schedule"
        verbose_name_plural = "Put Away Schedules"
    def __str__(self):
        return str(self.schedule_num)
class Put_Away_Items(models.Model):
    schedule_num = models.ForeignKey(Put_Away_Schedule, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_num = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    required_quantity = models.IntegerField(blank=True, null=True)
    bin_location = models.ForeignKey(Warehouse, default='1', blank=True, on_delete=models.CASCADE)
    reference_number = models.CharField(max_length=200, default='', blank=True, null=True)
    stored = models.BooleanField(default=False)
    class Meta: 
        verbose_name = "Put Away Item"
        verbose_name_plural = "Put Away Items"
    def __str__(self):
        return '%s %s' % (str(self.schedule_num), str(self.item_num))
class Put_Away_Summary(models.Model):
    schedule_num = models.ForeignKey(Put_Away_Schedule, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_num = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    required_quantity = models.IntegerField(blank=True, null=True)
    stored_quantity = models.IntegerField(blank=True, null=True)
    bin_location = models.ForeignKey(Warehouse, default='1', blank=True, on_delete=models.CASCADE)
    discrepancy = models.BooleanField(default=False)
    discrepancy_quantity = models.IntegerField(blank=True, null=True)
    status = models.CharField(max_length=200, default='', blank=True, null=True)
    date_scheduled = models.DateField(auto_now_add=False)
    date_stored = models.DateField(auto_now_add=False)
    reference_number = models.CharField(max_length=200, default='', blank=True, null=True)
    class Meta: 
        verbose_name = "Put Away Summary"
        verbose_name_plural = "Put Away Summaries"
    def __str__(self):
        return '%s %s' % (str(self.schedule_num), str(self.item_num))
class Put_Away_Finish_Transaction(models.Model):
    reference_number = models.CharField(max_length=200, default='')
    transaction_type = models.CharField(max_length=200, default='')
    transaction_date = models.DateField(auto_now_add=True)
    transaction_location = models.CharField(max_length=200, default='')
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_quantity = models.IntegerField(blank=True, null=True)
    class Meta: 
        verbose_name = "Finished Put Away Transaction"
        verbose_name_plural = "Finished Put Away Transactions"
    def __str__(self):
        return '%s %s' % (self.reference_number, self.item_number)
class Put_Away_Schedule_Transaction(models.Model):
    reference_number = models.CharField(max_length=200, default='')
    transaction_type = models.CharField(max_length=200, default='')
    transaction_date = models.DateField(auto_now_add=True)
    transaction_location = models.CharField(max_length=200, default='')
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_quantity = models.IntegerField(blank=True, null=True)
    class Meta: 
        verbose_name = "Put Away Schedule Transaction"
        verbose_name_plural = "Put Away Schedule Transactions"
    def __str__(self):
        return '%s %s' % (str(self.reference_number), str(self.item_number))

#Work Order Creation
class WO_Production_Schedule(models.Model):
    work_order_number = models.ForeignKey(Work_Order, default='1', blank=True, null=True, on_delete=models.CASCADE)
    quantity = models.IntegerField(blank=True, null=True)
    date_required = models.DateField(auto_now_add=False,blank=True, null=True)
    scheduled = models.BooleanField(default=False)
    issued = models.BooleanField(default=False)
    assembled = models.BooleanField(default=False)
    coupled = models.BooleanField(default=False)
    tested = models.BooleanField(default=False)
    received = models.BooleanField(default=False)
    status = models.CharField(max_length=200, default='', blank=True, null=True)
    issues = models.CharField(max_length=200, default='None', blank=True, null=True)
    class Meta: 
        verbose_name = "WO Production Schedule"
        verbose_name_plural = "WO Production Schedules"
    def __str__(self):
        return str(self.id)

#Component Issuance
class WO_Issuance_Schedule(models.Model):
    schedule_num = models.AutoField(primary_key=True)
    date_scheduled = models.DateField(auto_now=False)
    notes = models.CharField(max_length=200, default='')
    cleared = models.BooleanField(default=False)
    issues = models.BooleanField(default=False)
    class Meta: 
        verbose_name = "WO Issuance Schedule"
        verbose_name_plural = "WO Issuance Schedules"
    def __str__(self):
        return str(self.schedule_num)
class WO_Issuance_Item(models.Model):
    schedule_num = models.ForeignKey(WO_Issuance_Schedule, default='1', blank=True, null=True, on_delete=models.CASCADE)
    prod_sched = models.ForeignKey(WO_Production_Schedule, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_num = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_quantity = models.IntegerField(blank=True, null=True)
    bin_location = models.ForeignKey(Warehouse, default='1', blank=True, null=True, on_delete=models.CASCADE)
    class Meta: 
        verbose_name = "WO Issuance Item"
        verbose_name_plural = "WO Issuance Items"
    def __str__(self):
        return '%s %s' % (str(self.schedule_num), str(self.item_num))
class WO_Issuance_Summary(models.Model):
    schedule_num = models.ForeignKey(WO_Issuance_Schedule, default='1', blank=True, null=True, on_delete=models.CASCADE)
    prod_sched = models.ForeignKey(WO_Production_Schedule, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_num = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    totalreq_quan = models.IntegerField(blank=True, null=True)
    totalrec_quan = models.IntegerField(blank=True, null=True)
    discrepancy = models.BooleanField(default=False)
    discrepancy_quantity = models.IntegerField(blank=True, null=True)
    status = models.CharField(max_length=200, default='test', blank=True, null=True)
    date_received = models.DateField(auto_now_add=False, blank=True, null=True)
    class Meta: 
        verbose_name = "WO Issuance Summary"
        verbose_name_plural = "WO Issuance Summaries"
    def __str__(self):
        return '%s %s' % (str(self.schedule_num), str(self.item_num))
class WO_Issuance_RecItem(models.Model):
    schedule_num = models.ForeignKey(WO_Issuance_Schedule, default='1', blank=True, null=True, on_delete=models.CASCADE)
    prod_sched = models.ForeignKey(WO_Production_Schedule, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_num = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_quantity = models.IntegerField(blank=True, null=True)
    date_received = models.DateField(auto_now_add=False, blank=True, null=True)
    notes = models.CharField(max_length=200, default='test', blank=True, null=True)
    bin_location = models.ForeignKey(Warehouse, default='1', blank=True, null=True, on_delete=models.CASCADE)
    class Meta: 
        verbose_name = "WO Issuance RecItem"
        verbose_name_plural = "WO Issuance RecItems"
    def __str__(self):
        return '%s %s %s %s' % (str(self.schedule_num), str(self.item_num), str(self.bin_location), str(self.prod_sched))
class WO_Issuance_List(models.Model):
    schedule_num = models.ForeignKey(WO_Issuance_Schedule, default='1', blank=True, null=True, on_delete=models.CASCADE)
    prod_sched = models.ForeignKey(WO_Production_Schedule, default='1', blank=True, null=True, on_delete=models.CASCADE)
    cleared = models.BooleanField(default=False)
    issues = models.CharField(max_length=200, default='test')
    issued_by = models.CharField(max_length=200, default='test')
    date_issued = models.DateField(auto_now_add=False, blank=True, null=True)
    verified_by = models.CharField(max_length=200, default='test')
    notes = models.CharField(max_length=200, default='test')
    image = models.ImageField(upload_to='wo_issuance/',
        null=True,
        blank=True,
        width_field="width_field",
        height_field="height_field")
    width_field = models.IntegerField(default=0,null=True, blank=True)
    height_field = models.IntegerField(default=0,null=True, blank=True)

    class Meta: 
        verbose_name = "WO Issuance List"
        verbose_name_plural = "WO Issuance Lists"
    def __str__(self):
        return '%s %s' % (str(self.schedule_num), str(self.prod_sched))
class WO_Allocation_Transaction(models.Model):
    reference_number = models.CharField(max_length=200, default='')
    transaction_type = models.CharField(max_length=200, default='')
    transaction_date = models.DateField(auto_now_add=True)
    transaction_location = models.CharField(max_length=200, default='')
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_quantity = models.IntegerField(blank=True, null=True)
    class Meta: 
        verbose_name = "WO Allocation Transaction"
        verbose_name_plural = "WO Allocation Transactions"
    def __str__(self):
        return '%s %s' % (str(self.reference_number), str(self.item_number))
class WO_Issuance_Finish_Transaction(models.Model):
    reference_number = models.CharField(max_length=200, default='')
    transaction_type = models.CharField(max_length=200, default='')
    transaction_date = models.DateField(auto_now_add=True, blank=True, null=True)
    transaction_location = models.CharField(max_length=200, default='')
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_quantity = models.IntegerField(blank=True, null=True)
    class Meta: 
        verbose_name = "WO Issuance Finish Transaction"
        verbose_name_plural = "WO Issuance Finish Transactions"
    def __str__(self):
        return '%s %s' % (str(self.reference_number), str(self.item_number))
class WO_Issuance_Disc_Transaction(models.Model):
    reference_number = models.CharField(max_length=200, default='')
    transaction_type = models.CharField(max_length=200, default='')
    transaction_date = models.DateField(auto_now_add=True, blank=True, null=True)
    transaction_location = models.CharField(max_length=200, default='')
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_quantity = models.IntegerField(blank=True, null=True)
    class Meta: 
        verbose_name = "WO Issuance Disc Transaction"
        verbose_name_plural = "WO Issuance Disc Transactions"
    def __str__(self):
        return '%s %s' % (str(self.reference_number), str(self.item_number))


#Assembly
class WO_Assembly(models.Model):
    prod_sched = models.ForeignKey(WO_Production_Schedule, default='1', blank=True, null=True, on_delete=models.CASCADE)
    date_received = models.DateField(auto_now_add=False)
    assembled_by = models.CharField(max_length=200, default='', blank=True, null=True)
    date_assembled = models.DateField(auto_now_add=False, blank=True, null=True)
    verified_by =models.CharField(max_length=200, default='', blank=True, null=True)
    notes = models.CharField(max_length=200, default='', blank=True, null=True)
    cleared = models.BooleanField(default=False)
    image = models.ImageField(upload_to='wo_assembly/',
        null=True,
        blank=True,
        width_field="width_field",
        height_field="height_field")
    width_field = models.IntegerField(default=0,null=True, blank=True)
    height_field = models.IntegerField(default=0,null=True, blank=True)
    
    class Meta: 
        verbose_name = "WO Assembly"
        verbose_name_plural = "WO Assemblies"
    def __str__(self):
        return str(self.id)
class WO_Coupling(models.Model):
    prod_sched = models.ForeignKey(WO_Production_Schedule, default='1', blank=True, null=True, on_delete=models.CASCADE)
    date_received = models.DateField(auto_now_add=False)
    coupled_by = models.CharField(max_length=200, default='', blank=True, null=True)
    date_coupled = models.DateField(auto_now_add=False, blank=True, null=True)
    verified_by =models.CharField(max_length=200, default='', blank=True, null=True)
    notes = models.CharField(max_length=200, default='', blank=True, null=True)
    cleared = models.BooleanField(default=False)
    image = models.ImageField(upload_to='wo_coupling/',
        null=True,
        blank=True,
        width_field="width_field",
        height_field="height_field")
    width_field = models.IntegerField(default=0,null=True, blank=True)
    height_field = models.IntegerField(default=0,null=True, blank=True)

    class Meta: 
        verbose_name = "WO Coupling"
        verbose_name_plural = "WO Couplings"
    def __str__(self):
        return str(self.id)
class WO_Testing(models.Model):
    prod_sched = models.ForeignKey(WO_Production_Schedule, default='1', blank=True, null=True, on_delete=models.CASCADE)
    date_received = models.DateField(auto_now_add=False)
    tested_by = models.CharField(max_length=200, default='', blank=True, null=True)
    date_tested = models.DateField(auto_now_add=False, blank=True, null=True)
    verified_by =models.CharField(max_length=200, default='', blank=True, null=True)
    notes = models.CharField(max_length=200, default='', blank=True, null=True)
    cleared = models.BooleanField(default=False)
    image = models.ImageField(upload_to='wo_testing/',
        null=True,
        blank=True,
        width_field="width_field",
        height_field="height_field")
    width_field = models.IntegerField(default=0,null=True, blank=True)
    height_field = models.IntegerField(default=0,null=True, blank=True)

    class Meta: 
        verbose_name = "WO Testing"
        verbose_name_plural = "WO Testings"
    def __str__(self):
        return str(self.id)
class WO_Finished(models.Model):
    prod_sched = models.ForeignKey(WO_Production_Schedule, default='1', blank=True, null=True, on_delete=models.CASCADE)
    date_received = models.DateField(auto_now_add=False)
    name_plate = models.BooleanField(default=False)
    label_sticker = models.BooleanField(default=False)
    iom = models.BooleanField(default=False)
    qr_code = models.BooleanField(default=False)
    wrnty_card = models.BooleanField(default=False)
    packaging = models.BooleanField(default=False)
    date_out = models.DateField(auto_now_add=False, blank=True, null=True)
    checked_by = models.CharField(max_length=200, default='', blank=True, null=True)
    notes = models.CharField(max_length=200, default='', blank=True, null=True)
    cleared = models.BooleanField(default=False)
    image = models.ImageField(upload_to='wo_finished/',
        null=True,
        blank=True,
        width_field="width_field",
        height_field="height_field")
    width_field = models.IntegerField(default=0,null=True, blank=True)
    height_field = models.IntegerField(default=0,null=True, blank=True)

    class Meta: 
        verbose_name = "WO Finished"
        verbose_name_plural = "WO Finisheds"
    def __str__(self):
        return str(self.id)
class RecProduct_Item_Transaction(models.Model):
    reference_number = models.CharField(max_length=200, default='')
    transaction_type = models.CharField(max_length=200, default='')
    transaction_date = models.DateField(auto_now_add=True)
    transaction_location = models.CharField(max_length=200, default='')
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_quantity = models.IntegerField(blank=True, null=True)
    class Meta: 
        verbose_name = "Receive_Product Item Transaction"
        verbose_name_plural = "Receive_Product Item Transactions"
    def __str__(self):
        return '%s %s' % (str(self.reference_number), str(self.item_number))    
class RecProduct_Product_Transaction(models.Model):
    reference_number = models.CharField(max_length=200, default='')
    transaction_type = models.CharField(max_length=200, default='')
    transaction_date = models.DateField(auto_now_add=True)
    transaction_location = models.CharField(max_length=200, default='')
    prod_number = models.ForeignKey(Product, default='1', blank=True, null=True, on_delete=models.CASCADE)
    prod_quantity = models.IntegerField(blank=True, null=True)
    class Meta: 
        verbose_name = "Receive_Product Product Transaction"
        verbose_name_plural = "Receive_Product Product Transactions"
    def __str__(self):
        return '%s %s' % (str(self.reference_number), str(self.prod_number))
class RecProduct_ProductToShipLobby_Transaction(models.Model):
    reference_number = models.CharField(max_length=200, default='')
    transaction_type = models.CharField(max_length=200, default='')
    transaction_date = models.DateField(auto_now_add=True)
    transaction_location = models.CharField(max_length=200, default='')
    prod_number = models.ForeignKey(Product, default='1', blank=True, null=True, on_delete=models.CASCADE)
    prod_quantity = models.IntegerField(blank=True, null=True)
    class Meta: 
        verbose_name = "Receive_Product ProductToShipLobby Transaction"
        verbose_name_plural = "Receive_Product ProductToShipLobby Transactions"
    def __str__(self):
        return '%s %s' % (str(self.reference_number), str(self.prod_number))
class RecProduct_ProductToWhse_Transaction(models.Model):
    reference_number = models.CharField(max_length=200, default='')
    transaction_type = models.CharField(max_length=200, default='')
    transaction_date = models.DateField(auto_now_add=True)
    transaction_location = models.CharField(max_length=200, default='')
    prod_number = models.ForeignKey(Product, default='1', blank=True, null=True, on_delete=models.CASCADE)
    prod_quantity = models.IntegerField(blank=True, null=True)
    class Meta: 
        verbose_name = "Receive_Product ProductToWhse Transaction"
        verbose_name_plural = "Receive_Product ProductToWhse Transactions"
    def __str__(self):
        return '%s %s' % (str(self.reference_number), str(self.prod_number))


#SHIPPING
class Shipping_Lobby(models.Model):
    prod_sched = models.ForeignKey(WO_Production_Schedule, default='1', blank=True, null=True, on_delete=models.CASCADE)
    prod_number = models.ForeignKey(Product, default='1', blank=True, null=True, on_delete=models.CASCADE)
    quantity = models.IntegerField(blank=True, null=True)
    date_received = models.DateField(auto_now_add=False)
    received_by = models.CharField(max_length=200, default='')
    checked_by = models.CharField(max_length=200, default='')
    notes = models.CharField(max_length=200, default='',blank=True, null=True)
    class Meta: 
        verbose_name = "Shipping Lobby"
        verbose_name_plural = "Shipping Lobbies"
    def __str__(self):
        return str(self.id)
class Shipping_Outbound(models.Model):
    wo_num = models.ForeignKey(Work_Order, default='1', blank=True, null=True, on_delete=models.CASCADE)
    ship_out_num = models.CharField(max_length=200, default='',blank=True, null=True)
    date_out = models.DateField(auto_now_add=False,blank=True, null=True)
    notes = models.CharField(max_length=200, default='',blank=True, null=True)
    class Meta: 
        verbose_name = "Shipping Outbound"
        verbose_name_plural = "Shipping Outbounds"
    def __str__(self):
        return '%s %s' % (str(self.id), str(self.wo_num))
class Shipping_Outbound_Transaction(models.Model):
    reference_number = models.CharField(max_length=200, default='')
    transaction_type = models.CharField(max_length=200, default='')
    transaction_date = models.DateField(auto_now_add=True)
    transaction_location = models.CharField(max_length=200, default='')
    prod_number = models.ForeignKey(Product, default='1', blank=True, null=True, on_delete=models.CASCADE)
    prod_quantity = models.IntegerField(blank=True, null=True)
    class Meta: 
        verbose_name = "Shipping Outbound Transaction"
        verbose_name_plural = "Shipping Outbound Transactions"
    def __str__(self):
        return '%s %s' % (str(self.reference_number), str(self.prod_number))
class Shipping_WhseProduct_Transaction(models.Model):
    reference_number = models.CharField(max_length=200, default='')
    transaction_type = models.CharField(max_length=200, default='')
    transaction_date = models.DateField(auto_now_add=True)
    transaction_location = models.CharField(max_length=200, default='')
    prod_number = models.ForeignKey(Product, default='1', blank=True, null=True, on_delete=models.CASCADE)
    prod_quantity = models.IntegerField(blank=True, null=True)
    class Meta: 
        verbose_name = "Shipping WhseProduct Transaction"
        verbose_name_plural = "Shipping WhseProduct Transactions"
    def __str__(self):
        return '%s %s' % (str(self.reference_number), str(self.prod_number))


#SHRINKAGE
class Shrinkage_Type(models.Model):
    shrinkage_type = models.CharField(max_length=200, default='')
    class Meta: 
        verbose_name = "Shrinkage Type"
        verbose_name_plural = "Shrinkage Types"
    def __str__(self):
        return self.shrinkage_type
class Shrinkage_Ass_Report(models.Model):
    report_num = models.AutoField(primary_key=True)
    prod_sched = models.ForeignKey(WO_Production_Schedule, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    quantity = models.IntegerField(blank=True, null=True)
    shrinkage_type = models.ForeignKey(Shrinkage_Type, default='1', blank=True, null=True, on_delete=models.CASCADE)
    reason = models.CharField(max_length=200, default='')
    date_reported = models.DateField(auto_now_add=False)
    class Meta: 
        verbose_name = "Shrinkage Ass Report"
        verbose_name_plural = "Shrinkage Ass Reports"
    def __str__(self):
        return str(self.report_num)
class Shrinkage_Ass_Item(models.Model):
    report_num = models.ForeignKey(Shrinkage_Ass_Report, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    quantity = models.IntegerField(blank=True, null=True)
    scheduled = models.BooleanField(default=False)
    ass_location = models.ForeignKey(AssemblyLine, default='1', blank=True, null=True, on_delete=models.CASCADE)
    class Meta: 
        verbose_name = "Shrinkage Ass Item"
        verbose_name_plural = "Shrinkage Ass Items"
    def __str__(self):
        return '%s %s' % (str(self.report_num), str(self.item_number))
class Shrinkage_Ass_Report_Transaction(models.Model):
    reference_number = models.CharField(max_length=200, default='')
    transaction_type = models.CharField(max_length=200, default='')
    transaction_date = models.DateField(auto_now_add=True)
    transaction_location = models.CharField(max_length=200, default='')
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_quantity = models.IntegerField(blank=True, null=True)
    class Meta: 
        verbose_name = "Shrinkage Ass Report Transaction"
        verbose_name_plural = "Shrinkage Ass Report Transactions"
    def __str__(self):
        return '%s %s' % (str(self.reference_number), str(self.item_number))
class Shrinkage_Ass_Item_Transaction(models.Model):
    reference_number = models.CharField(max_length=200, default='')
    transaction_type = models.CharField(max_length=200, default='')
    transaction_date = models.DateField(auto_now_add=True)
    transaction_location = models.CharField(max_length=200, default='')
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_quantity = models.IntegerField(blank=True, null=True)
    class Meta: 
        verbose_name = "Shrinkage Ass Item Transaction"
        verbose_name_plural = "Shrinkage Ass Item Transactions"
    def __str__(self):
        return '%s %s' % (str(self.reference_number), str(self.item_number))

#ASSEMBLY REQUEST
class Request_Schedule(models.Model):
    schedule_num = models.AutoField(primary_key=True)
    date_scheduled = models.DateField(auto_now_add=False)
    cleared = models.BooleanField(default=False)
    issues = models.CharField(max_length=200, default='')
    notes = models.CharField(max_length=200, default='')
    class Meta: 
        verbose_name = "Request Schedule"
        verbose_name_plural = "Request Schedules"
    def __str__(self):
        return str(self.schedule_num)
class Request_Item(models.Model):
    schedule_num = models.ForeignKey(Request_Schedule, default='1', blank=True, null=True, on_delete=models.CASCADE)
    prod_sched = models.ForeignKey(WO_Production_Schedule, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    quantity = models.IntegerField(blank=True, null=True)
    location_from = models.ForeignKey(Warehouse, default='1', blank=True, null=True, on_delete=models.CASCADE)
    location_to = models.ForeignKey(AssemblyLine, default='1', blank=True, null=True, on_delete=models.CASCADE)
    refnum = models.CharField(max_length=200, default='', blank=True, null=True)
    cleared = models.BooleanField(default=False)
    class Meta: 
        verbose_name = "Request Item"
        verbose_name_plural = "Request Items"
    def __str__(self):
        return '%s %s %s' % (str(self.schedule_num), str(self.prod_sched), str(self.item_number))
class Request_RecItem(models.Model):
    schedule_num = models.ForeignKey(Request_Schedule, default='1', blank=True, null=True, on_delete=models.CASCADE)
    prod_sched = models.ForeignKey(WO_Production_Schedule, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    rec_quantity = models.IntegerField(blank=True, null=True)
    date_received = models.DateField(auto_now_add=False, blank=True, null=True)
    notes = models.CharField(max_length=200, default='', blank=True, null=True)
    bin_location = models.ForeignKey(Warehouse, default='1', blank=True, null=True, on_delete=models.CASCADE)
    ass_location = models.ForeignKey(AssemblyLine, default='1', blank=True, null=True, on_delete=models.CASCADE)
    class Meta: 
        verbose_name = "Request Rec_Item"
        verbose_name_plural = "Request Rec_Items"
    def __str__(self):
        return '%s %s %s' % (str(self.schedule_num), str(self.prod_sched), str(self.item_number))
class Request_Summary(models.Model):
    schedule_num = models.ForeignKey(Request_Schedule, default='1', blank=True, null=True, on_delete=models.CASCADE)
    prod_sched = models.ForeignKey(WO_Production_Schedule, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    totalreq_quan = models.IntegerField(blank=True, null=True)
    totalrec_quan = models.IntegerField(blank=True, null=True)
    discrepancy = models.BooleanField(default=False)
    discrepancy_quantity =models.IntegerField(blank=True, null=True)
    status = models.CharField(max_length=200, default='', blank=True, null=True)
    date_received = models.DateField(auto_now_add=False)
    bin_location = models.ForeignKey(Warehouse, default='1', blank=True, null=True, on_delete=models.CASCADE)
    ass_location = models.ForeignKey(AssemblyLine, default='1', blank=True, null=True, on_delete=models.CASCADE)
    class Meta: 
        verbose_name = "Request Summary"
        verbose_name_plural = "Request Summaries"
    def __str__(self):
        return '%s %s %s' % (str(self.schedule_num), str(self.prod_sched), str(self.item_number))
class Request_Schedule_Transaction(models.Model):
    reference_number = models.CharField(max_length=200, default='')
    transaction_type = models.CharField(max_length=200, default='')
    transaction_date = models.DateField(auto_now_add=True)
    transaction_location = models.CharField(max_length=200, default='')
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_quantity = models.IntegerField(blank=True, null=True)
    class Meta: 
        verbose_name = "Request Schedule Transaction"
        verbose_name_plural = "Request Schedule Transactions"
    def __str__(self):
        return '%s %s' % (str(self.reference_number), str(self.item_number))
class Request_Finish_Transaction(models.Model):
    reference_number = models.CharField(max_length=200, default='')
    transaction_type = models.CharField(max_length=200, default='')
    transaction_date = models.DateField(auto_now_add=True)
    transaction_location = models.CharField(max_length=200, default='')
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_quantity = models.IntegerField(blank=True, null=True)
    class Meta: 
        verbose_name = "Request Finish Transaction"
        verbose_name_plural = "Request Finish Transactions"
    def __str__(self):
        return '%s %s' % (str(self.reference_number), str(self.item_number))
class Request_DiscSummary_Transaction(models.Model):
    reference_number = models.CharField(max_length=200, default='')
    transaction_type = models.CharField(max_length=200, default='')
    transaction_date = models.DateField(auto_now_add=True)
    transaction_location = models.CharField(max_length=200, default='')
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_quantity = models.IntegerField(blank=True, null=True)
    class Meta: 
        verbose_name = "Request DiscSummary Transaction"
        verbose_name_plural = "Request DiscSummary Transactions"
    def __str__(self):
        return '%s %s' % (str(self.reference_number), str(self.item_number))


#COMPONENT RETURN
class ComponentReturn_Schedule(models.Model):
    schedule_num = models.AutoField(primary_key=True)
    date_scheduled = models.DateField(auto_now_add=False, blank=True, null=True)
    cleared = models.BooleanField(default=False)
    issues = models.CharField(max_length=200, default='', blank=True, null=True)
    notes = models.CharField(max_length=200, default='', blank=True, null=True)
    class Meta: 
        verbose_name = "Component Return Schedule"
        verbose_name_plural = "Component Return Schedules"
    def __str__(self):
        return str(self.schedule_num)
class ComponentReturn_Item(models.Model):
    schedule_num = models.ForeignKey(ComponentReturn_Schedule, default='1', blank=True, null=True, on_delete=models.CASCADE)
    prod_sched = models.ForeignKey(WO_Production_Schedule, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    quantity = models.IntegerField(blank=True, null=True)
    location_from = models.ForeignKey(AssemblyLine, default='1', blank=True, null=True, on_delete=models.CASCADE)
    cleared = models.BooleanField(default=False)
    class Meta: 
        verbose_name = "Component Return Item"
        verbose_name_plural = "Component Return Items"
    def __str__(self):
        return '%s %s %s' % (str(self.schedule_num), str(self.prod_sched), str(self.item_number))
class ComponentReturn_RecItem(models.Model):
    schedule_num = models.ForeignKey(ComponentReturn_Schedule, default='1', blank=True, null=True, on_delete=models.CASCADE)
    prod_sched = models.ForeignKey(WO_Production_Schedule, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    quantity = models.IntegerField(blank=True, null=True)
    date_received = models.DateField(auto_now_add=True)
    notes = models.CharField(max_length=200, default='', blank=True, null=True)
    ass_location = models.ForeignKey(AssemblyLine, default='1', blank=True, null=True, on_delete=models.CASCADE)
    class Meta: 
        verbose_name = "Component Return Rec_Item"
        verbose_name_plural = "Component Return Rec_Items"
    def __str__(self):
        return '%s %s %s' % (str(self.schedule_num), str(self.prod_sched), str(self.item_number))
class ComponentReturn_Summary(models.Model):
    schedule_num = models.ForeignKey(ComponentReturn_Schedule, default='1', blank=True, null=True, on_delete=models.CASCADE)
    prod_sched = models.ForeignKey(WO_Production_Schedule, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    totalreq_quan = models.IntegerField(blank=True, null=True)
    totalrec_quan = models.IntegerField(blank=True, null=True)
    discrepancy = models.BooleanField(default=False)
    discrepancy_quantity = models.IntegerField(blank=True, null=True)
    status = models.CharField(max_length=200, default='', blank=True, null=True)
    date_received = models.DateField(auto_now_add=True, blank=True, null=True)
    ass_location = models.ForeignKey(AssemblyLine, default='1', blank=True, null=True, on_delete=models.CASCADE)
    class Meta: 
        verbose_name = "Component Return Summary"
        verbose_name_plural = "Component Return Summaries"
    def __str__(self):
        return '%s %s %s' % (str(self.schedule_num), str(self.prod_sched), str(self.item_number))
class ComponentReturn_Schedule_Transaction(models.Model):
    reference_number = models.CharField(max_length=200, default='')
    transaction_type = models.CharField(max_length=200, default='')
    transaction_date = models.DateField(auto_now_add=True)
    transaction_location = models.CharField(max_length=200, default='')
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_quantity = models.IntegerField(blank=True, null=True)
    class Meta: 
        verbose_name = "Component Return Transaction"
        verbose_name_plural = "Component Return Transactions"
    def __str__(self):
        return '%s %s' % (str(self.reference_number), str(self.item_number))
class ComponentReturn_Summary_Transaction(models.Model):
    reference_number = models.CharField(max_length=200, default='')
    transaction_type = models.CharField(max_length=200, default='')
    transaction_date = models.DateField(auto_now_add=True)
    transaction_location = models.CharField(max_length=200, default='')
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_quantity = models.IntegerField(blank=True, null=True)
    class Meta: 
        verbose_name = "Component Return Summary Transaction"
        verbose_name_plural = "Component Return Summary Transactions"
    def __str__(self):
        return '%s %s' % (str(self.reference_number), str(self.item_number))


#INVENTORY ADJUSTMENT
class IAF_code(models.Model):
    iaf_code = models.CharField(max_length=200, default='', blank=True, null=True)
    iaf_adjustment = models.CharField(max_length=200, default='', blank=True, null=True)
    iaf_major = models.CharField(max_length=200, default='', blank=True, null=True)
    iaf_org = models.CharField(max_length=200, default='', blank=True, null=True)
    class Meta: 
        verbose_name = "IAF code"
        verbose_name_plural = "IAF codes"
    def __str__(self):
        return str(self.iaf_adjustment)
class IAF_whse(models.Model):
    whse = models.CharField(max_length=200, default='', blank=True, null=True)
    class Meta: 
        verbose_name = "IAF whse"
        verbose_name_plural = "IAF whses"
    def __str__(self):
        return str(self.whse)
class IAF_operator(models.Model):
    operator = models.CharField(max_length=200, default='', blank=True, null=True)
    class Meta: 
        verbose_name = "IAF operator"
        verbose_name_plural = "IAF operators"
    def __str__(self):
        return str(self.operator)
class IAF_Report(models.Model):
    report_num = models.AutoField(primary_key=True)
    iaf_whse = models.ForeignKey(IAF_whse, default='1', blank=True, null=True, on_delete=models.CASCADE)
    adjustment_type = models.ForeignKey(IAF_code, default='1', blank=True, null=True, on_delete=models.CASCADE)
    iaf_action = models.CharField(max_length=200, default='', blank=True, null=True)
    date_requested = models.DateField(auto_now_add=False, blank=True, null=True)
    date_approved = models.DateField(auto_now_add=False, blank=True, null=True)
    date_adjusted = models.DateField(auto_now_add=False, blank=True, null=True)
    prepared_by = models.CharField(max_length=200, default='', blank=True, null=True)
    noted_by = models.CharField(max_length=200, default='', blank=True, null=True)
    class Meta: 
        verbose_name = "IAF Report"
        verbose_name_plural = "IAF Reports"
    def __str__(self):
        return '%s %s' % (str(self.report_num), str(self.adjustment_type))
class IAF_Item(models.Model):
    report_num = models.ForeignKey(IAF_Report, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    bin_location = models.ForeignKey(Warehouse, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_quantity = models.IntegerField(blank=True, null=True)
    iaf_operator = models.ForeignKey(IAF_operator, default='1', blank=True, null=True, on_delete=models.CASCADE)
    total_cost = models.IntegerField(blank=True, null=True)
    reason = models.CharField(max_length=200, default='', blank=True, null=True)
    class Meta: 
        verbose_name = "IAF Item"
        verbose_name_plural = "IAF Items"
    def __str__(self):
        return '%s %s' % (str(self.report_num), str(self.item_number))
class IAF_Prod(models.Model):
    report_num = models.ForeignKey(IAF_Report, default='1', blank=True, null=True, on_delete=models.CASCADE)
    prod_number = models.ForeignKey(Product, default='1', blank=True, null=True, on_delete=models.CASCADE)
    bin_location = models.ForeignKey(Warehouse, default='1', blank=True, null=True, on_delete=models.CASCADE)
    prod_quantity = models.IntegerField(blank=True, null=True)
    iaf_operator = models.ForeignKey(IAF_operator, default='1', blank=True, null=True, on_delete=models.CASCADE)
    total_cost = models.IntegerField(blank=True, null=True)
    reason = models.CharField(max_length=200, default='', blank=True, null=True)
    class Meta: 
        verbose_name = "IAF Product"
        verbose_name_plural = "IAF Products"
    def __str__(self):
        return '%s %s' % (str(self.report_num), str(self.prod_number))
class IAF_Add_Transaction(models.Model):
    reference_number = models.CharField(max_length=200, default='')
    transaction_type = models.CharField(max_length=200, default='')
    transaction_date = models.DateField(auto_now_add=True)
    transaction_location = models.CharField(max_length=200, default='')
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_quantity = models.IntegerField(blank=True, null=True)
    class Meta: 
        verbose_name = "IAF Add Transaction"
        verbose_name_plural = "IAF Add Transactions"
    def __str__(self):
        return '%s %s' % (str(self.reference_number), str(self.item_number))
class IAF_Subt_Transaction(models.Model):
    reference_number = models.CharField(max_length=200, default='')
    transaction_type = models.CharField(max_length=200, default='')
    transaction_date = models.DateField(auto_now_add=True)
    transaction_location = models.CharField(max_length=200, default='')
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_quantity = models.IntegerField(blank=True, null=True)
    class Meta: 
        verbose_name = "IAF Subtract Transaction"
        verbose_name_plural = "IAF Subtract Transactions"
    def __str__(self):
        return '%s %s' % (str(self.reference_number), str(self.item_number))
class IAF_Prod_Subt_Transaction(models.Model):
    reference_number = models.CharField(max_length=200, default='')
    transaction_type = models.CharField(max_length=200, default='')
    transaction_date = models.DateField(auto_now_add=True)
    transaction_location = models.CharField(max_length=200, default='')
    prod_number = models.ForeignKey(Product, default='1', blank=True, null=True, on_delete=models.CASCADE)
    prod_quantity = models.IntegerField(blank=True, null=True)
    class Meta: 
        verbose_name = "IAF Product Subtract Transaction"
        verbose_name_plural = "IAF Product Subtract Transactions"
    def __str__(self):
        return '%s %s' % (str(self.reference_number), str(self.prod_number))


#DAMAGED MATERIALS
class DMMR_Report(models.Model):
    report_num = models.AutoField(primary_key=True)
    iaf_whse = models.ForeignKey(IAF_whse, default='1', blank=True, null=True, on_delete=models.CASCADE)
    date_reported = models.DateField(auto_now_add=False, blank=True, null=True)
    notes = models.CharField(max_length=200, default='', blank=True, null=True)
    class Meta: 
        verbose_name = "DMMR Report"
        verbose_name_plural = "DMMR Reports"
    def __str__(self):
        return '%s %s' % (str(self.report_num), str(self.iaf_whse))
class DMMR_Item(models.Model):
    report_num = models.ForeignKey(DMMR_Report, default='1', blank=True, null=True, on_delete=models.CASCADE)
    bin_location = models.ForeignKey(Warehouse, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_quantity = models.IntegerField(blank=True, null=True)
    iaf_operator = models.ForeignKey(IAF_operator, default='1', blank=True, null=True, on_delete=models.CASCADE)
    total_cost = models.IntegerField(blank=True, null=True)
    reason = models.CharField(max_length=200, default='', blank=True, null=True)
    class Meta: 
        verbose_name = "DMMR Item"
        verbose_name_plural = "DMMR Items"
    def __str__(self):
        return '%s %s' % (str(self.report_num), str(self.item_number))
class DMMR_Transaction(models.Model):
    reference_number = models.CharField(max_length=200, default='')
    transaction_type = models.CharField(max_length=200, default='')
    transaction_date = models.DateField(auto_now_add=True)
    transaction_location = models.CharField(max_length=200, default='')
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_quantity = models.IntegerField(blank=True, null=True)
    class Meta: 
        verbose_name = "DMMR Transaction"
        verbose_name_plural = "DMMR Transactions"
    def __str__(self):
        return '%s %s' % (str(self.reference_number), str(self.item_number))


#DEFECTIVE MATERIALS
class DFMR_Report(models.Model):
    report_num = models.AutoField(primary_key=True)
    iaf_whse = models.ForeignKey(IAF_whse, default='1', blank=True, null=True, on_delete=models.CASCADE)
    date_reported = models.DateField(auto_now_add=False, blank=True, null=True)
    notes = models.CharField(max_length=200, default='', blank=True, null=True)
    class Meta: 
        verbose_name = "DFMR Report"
        verbose_name_plural = "DFMR Reports"
    def __str__(self):
        return '%s %s' % (str(self.report_num), str(self.iaf_whse))
class DFMR_Item(models.Model):
    report_num = models.ForeignKey(DFMR_Report, default='1', blank=True, null=True, on_delete=models.CASCADE)
    bin_location = models.ForeignKey(Warehouse, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_quantity = models.IntegerField(blank=True, null=True)
    iaf_operator = models.ForeignKey(IAF_operator, default='1', blank=True, null=True, on_delete=models.CASCADE)
    total_cost = models.IntegerField(blank=True, null=True)
    reason = models.CharField(max_length=200, default='', blank=True, null=True)
    class Meta: 
        verbose_name = "DFMR Item"
        verbose_name_plural = "DFMR Items"
    def __str__(self):
        return '%s %s' % (str(self.report_num), str(self.item_number))
class DFMR_Transaction(models.Model):
    reference_number = models.CharField(max_length=200, default='')
    transaction_type = models.CharField(max_length=200, default='')
    transaction_date = models.DateField(auto_now_add=True)
    transaction_location = models.CharField(max_length=200, default='')
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_quantity = models.IntegerField(blank=True, null=True)
    class Meta: 
        verbose_name = "DFMR Transaction"
        verbose_name_plural = "DFMR Transactions"
    def __str__(self):
        return '%s %s' % (str(self.reference_number), str(self.item_number))


#SYSTEM ADJUSTMENT
class SA_Report(models.Model):
    report_num = models.AutoField(primary_key=True)
    iaf_whse = models.ForeignKey(IAF_whse, default='1', blank=True, null=True, on_delete=models.CASCADE)
    date_reported = models.DateField(auto_now_add=False, blank=True, null=True)
    notes = models.CharField(max_length=200, default='', blank=True, null=True)
    class Meta: 
        verbose_name = "SA Report"
        verbose_name_plural = "SA Reports"
    def __str__(self):
        return '%s %s' % (str(self.report_num), str(self.iaf_whse))
class SA_Item(models.Model):
    report_num = models.ForeignKey(SA_Report, default='1', blank=True, null=True, on_delete=models.CASCADE)
    bin_location = models.ForeignKey(Warehouse, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_quantity = models.IntegerField(blank=True, null=True)
    iaf_operator = models.ForeignKey(IAF_operator, default='1', blank=True, null=True, on_delete=models.CASCADE)
    total_cost = models.IntegerField(blank=True, null=True)
    reason = models.CharField(max_length=200, default='', blank=True, null=True)
    class Meta: 
        verbose_name = "SA Item"
        verbose_name_plural = "SA Items"
    def __str__(self):
        return '%s %s' % (str(self.report_num), str(self.item_number))
class SA_Subt_Transaction(models.Model):
    reference_number = models.CharField(max_length=200, default='')
    transaction_type = models.CharField(max_length=200, default='')
    transaction_date = models.DateField(auto_now_add=True)
    transaction_location = models.CharField(max_length=200, default='')
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_quantity = models.IntegerField(blank=True, null=True)
    class Meta: 
        verbose_name = "SA Subt Transaction"
        verbose_name_plural = "SA Subt Transactions"
    def __str__(self):
        return '%s %s' % (str(self.reference_number), str(self.item_number))
class SA_Add_Transaction(models.Model):
    reference_number = models.CharField(max_length=200, default='')
    transaction_type = models.CharField(max_length=200, default='')
    transaction_date = models.DateField(auto_now_add=True)
    transaction_location = models.CharField(max_length=200, default='')
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_quantity = models.IntegerField(blank=True, null=True)
    class Meta: 
        verbose_name = "SA Add Transaction"
        verbose_name_plural = "SA Add Transactions"
    def __str__(self):
        return '%s %s' % (str(self.reference_number), str(self.item_number))


#DISMANTLE
class Dismantle_Report(models.Model):
    report_num = models.AutoField(primary_key=True)
    iaf_whse = models.ForeignKey(IAF_whse, default='1', blank=True, null=True, on_delete=models.CASCADE)
    date_reported = models.DateField(auto_now_add=False, blank=True, null=True)
    notes = models.CharField(max_length=200, default='', blank=True, null=True)
    class Meta: 
        verbose_name = "Dismantle Report"
        verbose_name_plural = "Dismantle Reports"
    def __str__(self):
        return '%s %s' % (str(self.report_num), str(self.iaf_whse))
class Dismantle_Product(models.Model):
    report_num = models.ForeignKey(Dismantle_Report, default='1', blank=True, null=True, on_delete=models.CASCADE)
    prod_sched = models.ForeignKey(WO_Production_Schedule, default='1', blank=True, null=True, on_delete=models.CASCADE)
    bin_location = models.ForeignKey(Warehouse, default='1', blank=True, null=True, on_delete=models.CASCADE)
    prod_quantity = models.IntegerField(blank=True, null=True)
    iaf_operator = models.ForeignKey(IAF_operator, default='1', blank=True, null=True, on_delete=models.CASCADE)
    total_cost = models.IntegerField(blank=True, null=True)
    reason = models.CharField(max_length=200, default='', blank=True, null=True)
    class Meta: 
        verbose_name = "Dismantle Product"
        verbose_name_plural = "Dismantle Products"
    def __str__(self):
        return '%s %s' % (str(self.report_num), str(self.prod_sched))
class Dismantle_Item(models.Model):
    report_num = models.ForeignKey(Dismantle_Report, default='1', blank=True, null=True, on_delete=models.CASCADE)
    prod_sched = models.ForeignKey(WO_Production_Schedule, default='1', blank=True, null=True, on_delete=models.CASCADE)
    bin_location = models.ForeignKey(Warehouse, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_quantity = models.IntegerField(blank=True, null=True)
    iaf_operator = models.ForeignKey(IAF_operator, default='1', blank=True, null=True, on_delete=models.CASCADE)
    total_cost = models.IntegerField(blank=True, null=True)
    reason = models.CharField(max_length=200, default='', blank=True, null=True)
    class Meta: 
        verbose_name = "Dismantle Item"
        verbose_name_plural = "Dismantle Items"
    def __str__(self):
        return '%s %s' % (str(self.report_num), str(self.item_number))
class Dismantle_Product_Transaction(models.Model):
    reference_number = models.CharField(max_length=200, default='')
    transaction_type = models.CharField(max_length=200, default='')
    transaction_date = models.DateField(auto_now_add=True)
    transaction_location = models.CharField(max_length=200, default='')
    prod_number = models.ForeignKey(Product, default='1', blank=True, null=True, on_delete=models.CASCADE)
    prod_quantity = models.IntegerField(blank=True, null=True)
    class Meta: 
        verbose_name = "Dismantle Product Transaction"
        verbose_name_plural = "Dismantle Product Transactions"
    def __str__(self):
        return '%s %s' % (str(self.reference_number), str(self.prod_number))
class Dismantle_Item_Transaction(models.Model):
    reference_number = models.CharField(max_length=200, default='')
    transaction_type = models.CharField(max_length=200, default='')
    transaction_date = models.DateField(auto_now_add=True)
    transaction_location = models.CharField(max_length=200, default='')
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_quantity = models.IntegerField(blank=True, null=True)
    class Meta: 
        verbose_name = "Dismantle Item Transaction"
        verbose_name_plural = "Dismantle Item Transactions"
    def __str__(self):
        return '%s %s' % (str(self.reference_number), str(self.item_number))

#TRANSFER ITEM
class Transfer_Report(models.Model):
    report_num = models.AutoField(primary_key=True)
    iaf_whse = models.ForeignKey(IAF_whse, default='1', blank=True, null=True, on_delete=models.CASCADE)
    date_reported = models.DateField(auto_now_add=False, blank=True, null=True)
    notes = models.CharField(max_length=200, default='', blank=True, null=True)
    class Meta: 
        verbose_name = "Transfer Report"
        verbose_name_plural = "Transfer Reports"
    def __str__(self):
        return '%s %s' % (str(self.report_num), str(self.iaf_whse))
class Transfer_Item(models.Model):
    report_num = models.ForeignKey(Transfer_Report, default='1', blank=True, null=True, on_delete=models.CASCADE)
    bin_location = models.ForeignKey(Warehouse, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_quantity = models.IntegerField(blank=True, null=True)
    iaf_operator = models.ForeignKey(IAF_operator, default='1', blank=True, null=True, on_delete=models.CASCADE)
    total_cost = models.IntegerField(blank=True, null=True)
    reason = models.CharField(max_length=200, default='', blank=True, null=True)
    class Meta: 
        verbose_name = "Transfer Item"
        verbose_name_plural = "Transfer Items"
    def __str__(self):
        return '%s %s' % (str(self.report_num), str(self.item_number))
class Transfer_Subt_Transaction(models.Model):
    reference_number = models.CharField(max_length=200, default='')
    transaction_type = models.CharField(max_length=200, default='')
    transaction_date = models.DateField(auto_now_add=True)
    transaction_location = models.CharField(max_length=200, default='')
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_quantity = models.IntegerField(blank=True, null=True)
    class Meta: 
        verbose_name = "Transfer Subt Transaction"
        verbose_name_plural = "Transfer Subt Transactions"
    def __str__(self):
        return '%s %s' % (str(self.reference_number), str(self.item_number))
class Transfer_Add_Transaction(models.Model):
    reference_number = models.CharField(max_length=200, default='')
    transaction_type = models.CharField(max_length=200, default='')
    transaction_date = models.DateField(auto_now_add=True)
    transaction_location = models.CharField(max_length=200, default='')
    item_number = models.ForeignKey(Item, default='1', blank=True, null=True, on_delete=models.CASCADE)
    item_quantity = models.IntegerField(blank=True, null=True)
    class Meta: 
        verbose_name = "Transfer Add Transaction"
        verbose_name_plural = "Transfer Add Transactions"
    def __str__(self):
        return '%s %s' % (str(self.reference_number), str(self.item_number))

#SAMPLE MODEL
class Events(models.Model):
    event_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255,null=True,blank=True)
    start = models.DateTimeField(null=True,blank=True)
    end = models.DateTimeField(null=True,blank=True)
    event_type = models.CharField(max_length=10,null=True,blank=True)

    def __str__(self):
        return self.name