import frappe
from erpnext.stock.doctype.stock_entry.stock_entry_utils import make_stock_entry
from frappe.model.mapper import get_mapped_doc
from frappe.utils import get_link_to_form, nowdate, nowtime
from frappe import _, qb
from frappe.utils import cint, cstr, flt, get_link_to_form





import frappe

@frappe.whitelist(allow_guest=True)
def get_work_order_status(sales_order,item_code,serial_no):
    # Initialize an empty dictionary to store item statuses
    work_order_status = {}

    # Fetch the sales order items
    sales_order_doc = frappe.get_doc('Sales Order', sales_order)
    
    # for item in sales_order_doc.items:
        # Assuming there's a link between Sales Order item and Work Order, and Work Order has a status field
        # You may need to adjust this logic based on your data model
    work_order = frappe.db.get_value('Work Order', {'production_item': item_code, 'sales_order': sales_order,"custom_serial_no":serial_no}, 'status')
    custom_serial_no = frappe.db.get_value('Work Order', {'production_item': item_code, 'sales_order': sales_order,"custom_serial_no":serial_no}, 'custom_serial_no')
    frappe.log_error(str(serial_no),str(work_order))
    frappe.log_error(str(item_code),str(serial_no))
    if work_order:
        work_order_status["item_code"] = item_code
        work_order_status["serial_no"] = custom_serial_no
        work_order_status["status"] = work_order
        sales_order_item_name=frappe.db.get_value("Sales Order Item",{"item_code":item_code,"serial_no":serial_no},"name")
        frappe.log_error(str(serial_no),str(sales_order_item_name))
        frappe.db.set_value("Sales Order Item",sales_order_item_name,"custom_status",work_order)
    else:
        work_order_status["item_code"] = item_code
        work_order_status["serial_no"] = custom_serial_no
        work_order_status["status"] = "No Work Order"
        sales_order_item_name=frappe.db.get_value("Sales Order Item",{"item_code":item_code,"serial_no":serial_no},"name")
        frappe.db.set_value("Sales Order Item",sales_order_item_name,"custom_status","No Work Order")

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
        make_purchase_order(source_name=name, target_doc=None)
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

        def set_missing_values(source, target):
            target.supplier = source.custom_supplier
            target.flags.ignore_permissions = ignore_permissions
            target.run_method("set_missing_values")
            target.transaction_date = source.delivery_date
            target.schedule_date = source.delivery_date
            target.run_method("calculate_taxes_and_totals")

        def update_item(obj, target, source_parent):
            target.rate = frappe.db.get_value("Item Price",{"item_code":obj.item_code,"supplier":source_parent.custom_supplier},"price_list_rate")
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
                    "field_map": {"item_code": "item_code", "qty": 1,"serial_no":"tyre_serial_number"},
                    "postprocess": update_item,
                },
                "Purchase Taxes and Charges": {"add_if_empty": True},
            },
            target_doc,
            set_missing_values,
            ignore_permissions=ignore_permissions,
        )
        frappe.log_error("doclist", doclist.as_dict())
        doclist.insert()
        doclist.submit()
        if doclist.name:
            frappe.db.set_value(
                "Order Booking Form", source_name, "custom_purchase_order", doclist.name
            )
            make_purchase_receipt(source_name=doclist.name,target_doc=None)
            frappe.msgprint(f"Purchase Order Order Created Successfully {doclist.name}")
            
        return doclist
    else:
        frappe.msgprint(
            f"Purchase Order Already Created {frappe.db.get_value('Order Booking Form',source_name,'custom_purchase_order')}"
        )


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
					"material_request": "material_request",
					"material_request_item": "material_request_item",
					"sales_order": "sales_order",
					"sales_order_item": "sales_order_item",
					"wip_composite_asset": "wip_composite_asset",
                    "serial_no":"serial_no"
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
            wo=frappe.db.get_value("Work Order",{"production_item":i.get("item_code"),"custom_order_booking":doc.name},"name")
            if not wo or frappe.db.get_value("Work Order",wo,"docstatus") == 2:
                if not i.get("bom"):
                    frappe.throw(
                        _("Please select BOM against item {0}").format(i.get("item_code"))
                    )
                # if not i.get("pending_qty"):
                # 	frappe.throw(_("Please select Qty against item {0}").format(i.get("item_code")))

                work_order = frappe.get_doc(
                    dict(
                        doctype="Work Order",
                        production_item=i.get("item_code"),
                        bom_no=i.get("bom"),
                        qty=1,
                        company=company,
                        custom_purchase_order=doc.custom_purchase_order,
                        # sales_order_item=i.get("name"),
                        serial_no=i.get("tyre_serial_number"),
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
                frappe.msgprint(f"Work Order Already Created Successfully {wo}")

        except Exception as e:
            frappe.log_error("Error Response",e)
    frappe.db.set_value(
        "Order Booking Form", name, "work_order", str([p.name for p in out])
    )
    # frappe.msgprint("Work Orders Created")
    if out:
        process_work_orders(out)
    # frappe.db.commit()
    return [p.name for p in out]


def process_work_orders(out):
    for p in out:
        try:
            doc = frappe.get_doc("Work Order", p.name)
            doc.submit()
        except Exception as e:
            # Log the error and optionally perform rollback if necessary
            frappe.log_error(f"Error Response from Work Order {p.name}  ", str(e))
            # # Raise the exception to indicate failure
            # raise e


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

    frappe.log_error("Missing Item",str(missing_items))
    frappe.log_error("obd Item",str(obd))
    frappe.log_error("existing_items Item",str(valid_item))
    frappe.log_error("replaced_items Item",str(replaced_items))

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
    material_receipt.submit()
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
            # "serial_no":frappe.db.get_value("Stock Entry Detail",{"item_code":item.item_code,"parent":self.stock_entry},"serial_no")
        })

    frappe.log_error("material_issue",material_issue.as_dict())
    material_issue.insert()
    material_issue.submit()
    if material_issue.name:
        for item in replaced_items:
            row_name=frappe.db.get_value("Order Booking Details",{"item_code":item.item_code,"parent":self.name},"name")
            if row_name:
                frappe.db.set_value("Order Booking Details",row_name,{"custom_stock_entry":material_issue.name})
        frappe.msgprint(f"Material Issue {material_issue.name} created.")

