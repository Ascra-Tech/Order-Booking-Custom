import frappe
from erpnext.stock.doctype.stock_entry.stock_entry_utils import make_stock_entry
from frappe.model.mapper import get_mapped_doc
from frappe.utils import get_link_to_form, nowdate, nowtime
from frappe import _, qb
from frappe.utils import cint, cstr, flt, get_link_to_form



@frappe.whitelist()
def update_serial_nos(self,method=None):
    if self.items:
         for item in self.items:
            if item.custom_work_order:
                item.custom_serial_no=frappe.db.get_value("Work Order",item.custom_work_order,"custom_serial_no")
                item.serial_no=""

import frappe

@frappe.whitelist(allow_guest=True)
def get_work_order_status(sales_order,item_code,serial_no=None):
    # Initialize an empty dictionary to store item statuses
    work_order_status = {}

    # Fetch the sales order items
    sales_order_doc = frappe.get_doc('Sales Order', sales_order)
    
    # for item in sales_order_doc.items:
        # Assuming there's a link between Sales Order item and Work Order, and Work Order has a status field
        # You may need to adjust this logic based on your data model
    work_order = frappe.db.get_value('Work Order', {'production_item': item_code, 'sales_order': sales_order,"custom_serial_no":serial_no}, 'status')
    work_order_name = frappe.db.get_value('Work Order', {'production_item': item_code, 'sales_order': sales_order,"custom_serial_no":serial_no}, 'name')
    custom_serial_no = frappe.db.get_value('Work Order', {'production_item': item_code, 'sales_order': sales_order,"custom_serial_no":serial_no}, 'custom_serial_no')
    if work_order:
        work_order_status["item_code"] = item_code
        work_order_status["serial_no"] = custom_serial_no
        work_order_status["status"] = "Rejected" if work_order == "Closed" else work_order
        sales_order_item_name=frappe.db.get_value("Sales Order Item",{"item_code":item_code,"serial_no":serial_no},"name")
        frappe.db.set_value("Sales Order Item",sales_order_item_name,"custom_status","Rejected" if work_order == "Closed" else work_order)
        frappe.db.set_value("Sales Order Item",sales_order_item_name,"custom_work_order",work_order_name)

    else:
        work_order_status["item_code"] = item_code
        work_order_status["serial_no"] = custom_serial_no
        work_order_status["status"] = "No Work Order"
        sales_order_item_name=frappe.db.get_value("Sales Order Item",{"item_code":item_code,"serial_no":serial_no},"name")
        frappe.db.set_value("Sales Order Item",sales_order_item_name,"custom_status","No Work Order")
        frappe.db.set_value("Sales Order Item",sales_order_item_name,"custom_work_order",work_order_name)

    frappe.msgprint('Work order statuses updated successfully.')
        

    # Return the status as a dictionary with item codes and statuses
    return work_order_status




@frappe.whitelist()
def update_order_bookng(self,method=None):
    if self.work_order:
        self.custom_order_booking=frappe.db.get_value("Work Order",self.work_order,"custom_order_booking")

@frappe.whitelist()
def get_serial_no(reference_type,reference_name,item_code):
    if item_code and reference_type == "Job Card":
        work_order=frappe.db.get_value("Job Card",{"name":reference_name,"production_item":item_code},"work_order")
        if work_order:
            return frappe.db.get_value("Work Order",work_order,"custom_serial_no")



@frappe.whitelist()
def update_serial_no(self,method=None):
    if self.work_order:
        get_item_code=frappe.db.get_value("Work Order",self.work_order,"production_item")
        serial_no=frappe.db.get_value("Work Order",self.work_order,"serial_no")
        if serial_no:
            for item in self.items:
                if item.item_code == get_item_code:
                    item.serial_no=serial_no


# Create Serial No
@frappe.whitelist()
def create_serial_no(self, method=None):
    if self.get("order_booking_details"):
        for item in self.order_booking_details:
            try:
                if not frappe.db.get_value(
                    "Serial No",
                    {
                        "item_code": item.get("item_code"),
                        "serial_no": item.get("tyre_serial_number"),
                    },
                    "name",
                ):
                    frappe.get_doc(
                        {
                            "doctype": "Serial No",
                            "company": frappe.db.get_single_value(
                                "Global Defaults", "default_company"
                            ),
                            "serial_no": item.get("tyre_serial_number"),
                            "item_code": item.get("item_code"),
                        }
                    ).insert()
            except Exception as e:
                return e
                # frappe.log_error("Serial No Exist", e)


@frappe.whitelist()
def create_purchase_order(name=None):
    try:
        # create_stock_entry(name)
        # make_purchase_order(source_name=name, target_doc=None)
        create_work_order(name)
    except Exception as e:
        frappe.log_error("Exception",e)
    # pass


@frappe.whitelist()
def create_work_order(name=None):
    make_work_orders(name)


@frappe.whitelist()
def create_stock_entry(name):
    doc = frappe.get_doc("Order Booking Form", name)
    make_stock_entry(doc)


# make Sales Order


@frappe.whitelist()
def make_purchase_order(source_name: str, target_doc=None):
    return _make_purchase_order(source_name, target_doc)


def _make_purchase_order(source_name, target_doc=None, ignore_permissions=False):
    if not frappe.db.get_value("Order Booking Form", source_name, "custom_purchase_order"):
        frappe.msgprint(source_name)

        def set_missing_values(source, target):
            target.supplier = source.custom_supplier
            target.flags.ignore_permissions = ignore_permissions
            target.run_method("set_missing_values")
            target.transaction_date = source.delivery_date
            target.schedule_date = source.delivery_date
            target.run_method("calculate_taxes_and_totals")

        def update_item(obj, target, source_parent):
            target.rate =obj.item_rate #frappe.db.get_value("Item Price",{"item_code":obj.item_code,"supplier":source_parent.custom_supplier},"price_list_rate")
            frappe.log_error("tyre_serial_number",obj.tyre_serial_number)
            target.custom_serial_no=obj.tyre_serial_number

        doclist = get_mapped_doc(
            "Order Booking Form",
            source_name,
            {
                "Order Booking Form": {
                    "doctype": "Purchase Order",
                    # "validation": {"docstatus": ["=", 1]},
                },
                "Order Booking Details": {
                    "doctype": "Purchase Order Item",
                    "field_no_map": ["qty"],
                    "field_map": {
                        "branch":"branch",
                        "item_group":"item_group",
                        "sales_person":"sales_person",
                        "item_code": "item_code", 
                        "qty": 1
                        },
                    "postprocess": update_item,
                },
                "Purchase Taxes and Charges": {"add_if_empty": True},
            },
            target_doc,
            set_missing_values,
            ignore_permissions=ignore_permissions,
        )
        doclist.insert()
        doclist.submit()
        if doclist.name:
            frappe.db.set_value(
                "Order Booking Form", source_name, "custom_purchase_order", doclist.name
            )
            create_work_order(name=source_name)
            receipt_name=make_purchase_receipt(source_name=doclist.name,target_doc=None)
            
            # make_purchase_invoice(receipt_name)
            frappe.msgprint(f"Purchase Order Order Created Successfully {doclist.name}")
            
        return doclist
    else:
        frappe.msgprint(
            f"Purchase Order Already Created {frappe.db.get_value('Order Booking Form',source_name,'custom_purchase_order')}"
        )
import random
from erpnext.stock.doctype.purchase_receipt.purchase_receipt import get_returned_qty_map
from erpnext.stock.doctype.purchase_receipt.purchase_receipt import get_invoiced_qty_map
from erpnext.controllers.accounts_controller import merge_taxes
@frappe.whitelist()
def make_purchase_invoice(source_name, target_doc=None, args=None):
	from erpnext.accounts.party import get_payment_terms_template

	doc = frappe.get_doc("Purchase Receipt", source_name)
	returned_qty_map = get_returned_qty_map(source_name)
	invoiced_qty_map = get_invoiced_qty_map(source_name)

	def set_missing_values(source, target):
		if len(target.get("items")) == 0:
			frappe.throw(_("All items have already been Invoiced/Returned"))

		doc = frappe.get_doc(target)
		doc.payment_terms_template = get_payment_terms_template(source.supplier, "Supplier", source.company)
		

		number = random.randint(1000, 9999)

		doc.bill_no=number
		doc.run_method("onload")
		doc.run_method("set_missing_values")

		if args and args.get("merge_taxes"):
			merge_taxes(source.get("taxes") or [], doc)

		doc.run_method("calculate_taxes_and_totals")
		doc.set_payment_schedule()

	def update_item(source_doc, target_doc, source_parent):
		target_doc.qty, returned_qty = get_pending_qty(source_doc)
		if frappe.db.get_single_value("Buying Settings", "bill_for_rejected_quantity_in_purchase_invoice"):
			target_doc.rejected_qty = 0
		target_doc.stock_qty = flt(target_doc.qty) * flt(
			target_doc.conversion_factor, target_doc.precision("conversion_factor")
		)
		returned_qty_map[source_doc.name] = returned_qty

	def get_pending_qty(item_row):
		qty = item_row.qty
		if frappe.db.get_single_value("Buying Settings", "bill_for_rejected_quantity_in_purchase_invoice"):
			qty = item_row.received_qty

		pending_qty = qty - invoiced_qty_map.get(item_row.name, 0)

		if frappe.db.get_single_value("Buying Settings", "bill_for_rejected_quantity_in_purchase_invoice"):
			return pending_qty, 0

		returned_qty = flt(returned_qty_map.get(item_row.name, 0))
		if returned_qty:
			if returned_qty >= pending_qty:
				pending_qty = 0
				returned_qty -= pending_qty
			else:
				pending_qty -= returned_qty
				returned_qty = 0

		return pending_qty, returned_qty

	doclist = get_mapped_doc(
		"Purchase Receipt",
		source_name,
		{
			"Purchase Receipt": {
				"doctype": "Purchase Invoice",
				"field_map": {
					"supplier_warehouse": "supplier_warehouse",
					"is_return": "is_return",
					"bill_date": "bill_date",
				},
				"validation": {
					"docstatus": ["=", 1],
				},
			},
			"Purchase Receipt Item": {
				"doctype": "Purchase Invoice Item",
				"field_map": {
					"name": "pr_detail",
					"parent": "purchase_receipt",
					"qty": "received_qty",
					"purchase_order_item": "po_detail",
					"purchase_order": "purchase_order",
					"is_fixed_asset": "is_fixed_asset",
					"asset_location": "asset_location",
					"asset_category": "asset_category",
					"wip_composite_asset": "wip_composite_asset",
				},
				"postprocess": update_item,
				"filter": lambda d: get_pending_qty(d)[0] <= 0
				if not doc.get("is_return")
				else get_pending_qty(d)[0] > 0,
			},
			"Purchase Taxes and Charges": {
				"doctype": "Purchase Taxes and Charges",
				"add_if_empty": True,
				"ignore": args.get("merge_taxes") if args else 0,
			},
		},
		target_doc,
		set_missing_values,
	)
	doclist.flags.ignore_mandatory=True
	doclist.insert()
	# doclist.submit()

	return doclist.name

#Make Purchase Receipt

def set_missing_values(source, target):
	target.run_method("set_missing_values")
	target.run_method("calculate_taxes_and_totals")

@frappe.whitelist()
def make_purchase_receipt(source_name, target_doc=None):
	def update_item(obj, target, source_parent):
		target.qty = flt(obj.qty) - flt(obj.received_qty)
		target.stock_qty = (flt(obj.qty) - flt(obj.received_qty)) * flt(obj.conversion_factor)
		target.amount = (flt(obj.qty) - flt(obj.received_qty)) * flt(obj.rate)
		target.base_amount = (
			(flt(obj.qty) - flt(obj.received_qty)) * flt(obj.rate) * flt(source_parent.conversion_rate)
		)

	doc = get_mapped_doc(
		"Purchase Order",
		source_name,
		{
			"Purchase Order": {
				"doctype": "Purchase Receipt",
				"field_map": {"supplier_warehouse": "supplier_warehouse"},
				"validation": {
					"docstatus": ["=", 1],
				},
			},
			"Purchase Order Item": {
				"doctype": "Purchase Receipt Item",
				"field_map": {
					"name": "purchase_order_item",
					"parent": "purchase_order",
					"bom": "bom",
                    "branch":"branch",
                    "item_group":"item_group",
                    "sales_person":"sales_person",
					"material_request": "material_request",
					"material_request_item": "material_request_item",
					"sales_order": "sales_order",
					"sales_order_item": "sales_order_item",
					"wip_composite_asset": "wip_composite_asset",
                    "custom_serial_no":"custom_serial_no"
				},
				"postprocess": update_item,
				"condition": lambda doc: abs(doc.received_qty) < abs(doc.qty)
				and doc.delivered_by_supplier != 1,
			},
			"Purchase Taxes and Charges": {"doctype": "Purchase Taxes and Charges", "add_if_empty": True},
		},
		target_doc,
		set_missing_values,
	)
	doc.insert()
	doc.submit()
	frappe.msgprint(f"Purchase Receipt Created Successfully {doc.name}")
	frappe.db.set_value(
        "Order Booking Form", doc.custom_order_booking_form, "custom_purchase_receipt", doc.name
    )

	return doc.name




# Create Stock Entry





@frappe.whitelist()
def make_stock_entry(doc):
    kwargs = doc
    if isinstance(kwargs, str):
        kwargs = frappe.parse_json(kwargs)

    if isinstance(kwargs, dict):
        kwargs = frappe._dict(kwargs)

    if not kwargs.get("stock_entry"):

        stock_entry = frappe.new_doc("Stock Entry")
        stock_entry.update(
            {
                "company": frappe.db.get_single_value(
                    "Global Defaults", "default_company"
                ),
                "purpose": "Material Receipt",
                "stock_entry_type": "Material Receipt",
                "custom_order_booking": kwargs.get("name"),
                "posting_date": nowdate(),
                "posting_time": nowtime(),
                "dealer_name" : kwargs.get("dealer_name"),
                "items": get_item_details(kwargs),
            }
        )

        stock_entry.insert()
        stock_entry.submit()
        if stock_entry.name:
            frappe.msgprint(f"Stock Entry Created Successfully {stock_entry.name}")
            frappe.db.set_value(
                "Order Booking Form",
                kwargs.get("name"),
                "stock_entry",
                stock_entry.name,
            )

        return stock_entry
    else:
        frappe.msgprint(f"Stock Entry Already Created {kwargs.get('stock_entry')}")


def get_item_details(kwargs):
    if kwargs:
        item_details = []
        company = frappe.db.get_single_value("Global Defaults", "default_company")
        for item in kwargs.get("order_booking_details"):
            item_dict = {}
            item_dict["qty"] = 1
            item_dict["uom"] = frappe.db.get_value(
                "Item", item.get("item_code"), "stock_uom"
            )
            item_dict["item_code"] = item.get("item_code")
            item_dict["conversion_factor"] = 1
            item_dict["t_warehouse"] =item.get("target_warehouse_se")
            item_dict["serial_no"] = item.get("tyre_serial_number")
            item_dict["branch"] = item.get("branch")
            item_dict["item_group"] = item.get("item_group")
            item_dict["sales_person"] = item.get("sales_person")
            item_dict["allow_zero_valuation_rate"]=1
            # frappe.db.get_value(
            #     "Item Default",
            #     {"company": company, "parent": item.get("item_code")},
            #     "default_warehouse",
            # )
            item_details.append(item_dict)
        return item_details


# Creating Work Order
import json


@frappe.whitelist()
def make_work_orders(name=None, project=None):
    """Make Work Orders against the given Sales Order for the given `items`"""
    doc = frappe.get_doc("Order Booking Form", name)
    company = frappe.db.get_single_value("Global Defaults", "default_company")
    items = doc.get("order_booking_details")
    out = []

    for i in items:
        try:
            wo=frappe.db.get_value("Work Order",{"production_item":i.get("item_code"),"custom_order_booking":doc.name,"custom_serial_no":i.get("tyre_serial_number")},"name")
            if not wo or frappe.db.get_value("Work Order",wo,"docstatus") == 2:
                if not i.get("bom"):
                    frappe.throw(
                        _("Please select BOM against item {0}").format(i.get("item_code"))
                    )

                work_order = frappe.get_doc(
                    dict(
                        doctype="Work Order",
                        production_item=i.get("item_code"),
                        bom_no=i.get("bom"),
                        qty=1,
                        company=company,
                        custom_purchase_order=doc.custom_purchase_order,
                        # sales_order_item=i.get("name"),

                        custom_serial_no=i.get("tyre_serial_number"),
                        branch=i.get("branch"),
                        item_group=i.get("item_group"),
                        dealer_name= doc.get("dealer_name"),
                        sales_person=i.get("sales_person"),
                        custom_order_booking=doc.name,
                        wip_warehouse=i.get("wip_warehouse"),
                        source_warehouse=i.get("source_warehouse"),
                        project=project,
                        fg_warehouse=frappe.db.get_value(
                            "Item Default",
                            {"company": company, "parent": i.get("item_code")},
                            "default_warehouse",
                        ),
                        description=frappe.db.get_value(
                            "Item", i.get("item_code"), "description"
                        ),
                    )
                ).insert()
                work_order.set_work_order_operations()
                work_order.flags.ignore_mandatory = True
                work_order.save()
                out.append(work_order)

            else:
                name_wo=frappe.db.get_value("Work Order",{"production_item":i.get("item_code"),"custom_serial_no":i.get("tyre_serial_number"),"custom_order_booking":doc.name},"name")
                if name_wo:
                    frappe.db.set_value("Work Order",name_wo,"custom_purchase_order",doc.custom_purchase_order)
                    frappe.msgprint(f"Work Order Already Created Successfully {wo}")


        except Exception as e:
            frappe.log_error("Error Response",e)
    frappe.db.set_value(
        "Order Booking Form", name, "work_order", str([p.name for p in out])
    )

    if out:
        process_work_orders(out)
    return [p.name for p in out]


def process_work_orders(out):
    for p in out:
        try:
            doc = frappe.get_doc("Work Order", p.name)
            create_stock_receipt(doc)
            # doc.submit()
        except Exception as e:
            frappe.log_error(f"Error Response from Work Order {p.name}  ", str(e))





def create_stock_receipt(work_order):
    frappe.log_error("work_order",work_order.as_dict())
    """Create a Stock Receipt entry on Work Order draft creation."""
    stock_entry = frappe.get_doc({
        "doctype": "Stock Entry",
        "stock_entry_type": "Material Receipt",
        "company": work_order.company,
        "items": [
            {
                "item_code": work_order.production_item,
                "qty": 1,
                "t_warehouse": work_order.fg_warehouse,
                "serial_no": work_order.custom_serial_no
            }
        ]
    })
    stock_entry.insert()
    stock_entry.submit()
    frappe.db.set_value("Work Order", work_order.name, "custom_stock_receipt", stock_entry.name)



@frappe.whitelist()
def on_work_order_cancel(doc, method=None):
    """Cancel Stock Receipt when Work Order is canceled."""
    stock_receipt = frappe.db.get_value("Work Order", doc.name, "custom_stock_receipt")
    if stock_receipt:
        stock_entry = frappe.get_doc("Stock Entry", stock_receipt)
        stock_entry.cancel()
        frappe.db.set_value("Work Order", doc.name, "custom_stock_receipt", None)


# @frappe.whitelist()
def on_work_order_delete(doc, method=None):
    """Delete Stock Receipt when Work Order is deleted."""
    stock_receipt = frappe.db.get_value("Work Order", doc.name, "custom_stock_receipt")
    if stock_receipt:
        stock_entry = frappe.get_doc("Stock Entry", stock_receipt)
        stock_entry.cancel()
        frappe.delete_doc("Stock Entry", stock_receipt)
        frappe.db.set_value("Work Order", doc.name, "custom_stock_receipt", None)










@frappe.whitelist()
def update_stock_entry_ob(self, method=None):
    update_child_table_and_reverse_stock_entry(self)
def update_child_table_and_reverse_stock_entry(self):
    process_stock_entry(self,self.stock_entry)
    


def process_stock_entry(self,stock_entry):
    if not self.customer_name:
        return

    stock_entry=frappe.get_doc("Stock Entry",stock_entry)
    """
    Process a Stock Entry to:
    1. Identify missing items and create a Material Receipt.
    2. Identify replaced items by matching stock_entry items with missing items and create a Material Issue.
    """
    # Fetch existing items from stock_entry
    existing_items = {d.item_code: d.qty for d in frappe.get_all(
        "Stock Entry Detail",
        filters={"parent": stock_entry.name},
        fields=["item_code","qty"]
    )}

    obd = {d.item_code: d.qty for d in frappe.get_all(
        "Order Booking Details",
        filters={"parent": self.name},
        fields=["item_code", "qty"]
    )}

    valid_item=frappe.get_all(
        "Stock Entry Detail",
        filters={"parent": stock_entry.name},
        fields=["item_code","qty"])

    
    

    
    
    missing_items = []
    replaced_items=[]

    # Step 1: Identify missing items
    for item in self.order_booking_details:
        if item.item_code not in existing_items:
            missing_items.append(item)


    for item in valid_item:
        if item.item_code not in obd:
            replaced_items.append(item)


    # Create Material Receipt for missing items
    if replaced_items:
        create_material_issue(self,replaced_items)
    if missing_items:
        create_material_receipt(self,missing_items)

    # # Create Material Issue for replaced items
    

def create_material_receipt(self,missing_items):
    """
    Create a Material Receipt for the missing items.
    """
    
    material_receipt = frappe.new_doc("Stock Entry")
    material_receipt.stock_entry_type = "Material Receipt"
    
    for item in missing_items:
        # if not frappe.db.get_value("Stock Entry Detail",{"item_code":item.item_code,})
        material_receipt.append("items", {
            "item_code": item.item_code,
            "qty": 1,
            "uom": frappe.db.get_value(
                "Item", item.get("item_code"), "stock_uom"
            ),
            "t_warehouse": item.target_warehouse_se,
            "allow_zero_valuation_rate":1,
            "conversion_factor":1,
            # "serial_no":item.tyre_serial_number
        })
    material_receipt.insert()
    # material_receipt.submit()
    if material_receipt.name:
        for item in missing_items:
            row_name=frappe.db.get_value("Order Booking Details",{"item_code":item.item_code,"parent":self.name},"name")
            if row_name:
                frappe.db.set_value("Order Booking Details",row_name,{"custom_stock_entry":material_receipt.name})
        frappe.msgprint(f"Material Receipt {material_receipt.name} created.")


def create_material_issue(self,replaced_items):
    """
    Create a Material Issue for the replaced items.
    """
    material_issue = frappe.new_doc("Stock Entry")
    material_issue.stock_entry_type = "Material Issue"
    for item in replaced_items:
        material_issue.append("items", {
            "item_code": item.item_code,
            "qty": 1,
            "uom": frappe.db.get_value(
                "Item", item.get("item_code"), "stock_uom"
            ),
            "s_warehouse": frappe.db.get_value("Stock Entry Detail",{"item_code":item.item_code,"parent":self.stock_entry},"t_warehouse"),
            "allow_zero_valuation_rate":1,
            "conversion_factor":1,
            "serial_no":frappe.db.get_value("Stock Entry Detail",{"item_code":item.item_code,"parent":self.stock_entry},"serial_no")
        })

    frappe.log_error("material_issue",material_issue.as_dict())
    material_issue.insert()
    # material_issue.submit()
    if material_issue.name:
        for item in replaced_items:
            row_name=frappe.db.get_value("Order Booking Details",{"item_code":item.item_code,"parent":self.name},"name")
            if row_name:
                frappe.db.set_value("Order Booking Details",row_name,{"custom_stock_entry":material_issue.name})
        frappe.msgprint(f"Material Issue {material_issue.name} created.")

@frappe.whitelist()
def delete_so_item(doc,method=None):
    if doc.production_item and doc.custom_serial_no and doc.sales_order:
        get_obf=frappe.get_doc("Order Booking Form",doc.custom_order_booking)
        if len(get_obf.order_booking_details) > 0:
            frappe.db.delete("Sales Order", {"name": get_obf.sales_order})
            frappe.db.set_value("Order Booking Form",doc.custom_order_booking,"sales_order","")



@frappe.whitelist()
def update_item_so(doc,method=None):
    if doc.production_item and doc.custom_serial_no and doc.sales_order and not doc.is_new():
        get_item=frappe.db.get_value("Sales Order Item",{"item_code":doc.production_item,"serial_no":doc.custom_serial_no,"parent":doc.sales_order},"name")
        if not get_item:
        # Generate a unique name for the child row
            child_row_name = frappe.generate_hash(length=10)
            frappe.log_error("child_row_name",child_row_name)
        
            # # Prepare the row data
            child_row = {
                "name": child_row_name,
                "parent": doc.sales_order,
                "parentfield": "items",  # This should match the child table fieldname in the parent doctype
                "parenttype": "Sales Order",
                "doctype": "Sales Order Item",
                "item_code": doc.production_item,
                "item_name": frappe.db.get_value("Item",doc.production_item,"item_name"),
                "qty": 1,
                "serial_no": doc.custom_serial_no,
                "conversion_factor":1,
                "stock_uom":"Nos",
                "uom": "Nos",
                "rate": frappe.db.get_value(
                            "Item Price",
                            {"item_code": doc.production_item},
                            "price_list_rate",
                        ),
                "idx": frappe.db.count("Sales Order Item", filters={"parent": doc.sales_order}) + 1,  # Row index
            }
        
            # # Insert the row into the child doctype table
            child_doc=frappe.get_doc(child_row)
            child_doc.insert()
            frappe.db.commit()



#make Purchase Invoice from order bOOking
import frappe
from frappe.model.mapper import get_mapped_doc

@frappe.whitelist()
def make_purchase_invoice_from_order_booking(source_name, target_doc=None):
    # Check if a purchase invoice is already created
    existing_invoice = frappe.db.get_value("Order Booking Form", source_name, "custom_purchase_invoice")
    if existing_invoice:
        frappe.msgprint(f"Purchase Invoice already exists: {existing_invoice}")
        return existing_invoice

    def set_missing_values(source, target):
        target.supplier = source.custom_supplier
        target.bill_date = source.delivery_date
        target.bill_no = random.randint(1000, 9999)
        target.posting_date = frappe.utils.nowdate()
        target.run_method("set_missing_values")
        target.run_method("calculate_taxes_and_totals")

    def update_item(source_doc, target_doc, source_parent):
        target_doc.qty = 1
        target_doc.rate = float(source_doc.item_rate) if source_doc.item_rate else 0
        target_doc.amount = 1 * target_doc.rate
        target_doc.custom_serial_no = source_doc.tyre_serial_number


    # Mapping Order Booking Form to Purchase Invoice
    doclist = get_mapped_doc(
        "Order Booking Form",
        source_name,
        {
            "Order Booking Form": {
                "doctype": "Purchase Invoice",
            },
            "Order Booking Details": {
                "doctype": "Purchase Invoice Item",
                "field_map": {
                    "item_code": "item_code",
                    "qty": "qty",
                    "item_rate": "rate",
                    "branch": "branch",
                    "item_group": "item_group",
                    "sales_person": "sales_person",
                },
                "postprocess": update_item,
            },
            "Purchase Taxes and Charges": {"add_if_empty": True},
        },
        target_doc,
        set_missing_values,
    )

    # Insert and Submit Purchase Invoice
    doclist.flags.ignore_mandatory= True
    doclist.insert()
    # doclist.submit()

    # Link the Purchase Invoice to the Order Booking Form
    frappe.db.set_value("Order Booking Form", source_name, "custom_purchase_invoice", doclist.name)

    frappe.msgprint(f"Purchase Invoice Created Successfully: {doclist.name}")

    return doclist.name
