import frappe
from frappe.utils import flt


@frappe.whitelist()
def create_reverse_pr(self,method=None):
    process_reverse_pr(self,self.custom_purchase_receipt)



def process_reverse_pr(self):
    if not self.custom_supplier:
        return

    purchase_receipt=frappe.get_doc("Purchase Receipt",self.custom_purchase_receipt)
    """
    Process a Stock Entry to:
    1. Identify missing items and create a Material Receipt.
    2. Identify replaced items by matching stock_entry items with missing items and create a Material Issue.
    """
    # Fetch existing items from stock_entry
    existing_items = {d.item_code: d.qty for d in frappe.get_all(
        "Purchase Receipt Item",
        filters={"parent": self.custom_purchase_receipt},
        fields=["item_code","qty"]
    )}

    obd = {d.item_code: d.qty for d in frappe.get_all(
        "Order Booking Details",
        filters={"parent": self.name},
        fields=["item_code", "qty"]
    )}

    valid_item=frappe.get_all(
        "Purchase Receipt Item",
        filters={"parent": purchase_receipt.name},
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
    # if replaced_items:
    #     reverse_purchase_receipt(self,replaced_items)
    # if missing_items:
    #     create_material_receipt(self,missing_items)



def reverse_purchase_receipt(replaced_item):
    """
    Reverse the Purchase Receipt for the replaced item.

    :param replaced_item: The replaced item from the child table.
    """
    purchase_receipt = frappe.get_doc("Purchase Receipt", replaced_item.purchase_receipt)
    if purchase_receipt.docstatus == 1:
        # Create a Purchase Receipt Reversal
        reversed_pr = frappe.new_doc("Purchase Receipt")
        reversed_pr.update({
            "is_return": 1,
            "return_against": purchase_receipt.name,
            "items": [
                {
                    "item_code": replaced_item.item_code,
                    "qty": replaced_item.qty,
                    "rate": replaced_item.rate,
                    "warehouse": replaced_item.warehouse
                }
            ]
        })
        reversed_pr.submit()


def create_new_purchase_receipt(order_item):
    """
    Create a new Purchase Receipt for the replaced item.

    :param order_item: The new item from the child table.
    """
    new_pr = frappe.new_doc("Purchase Receipt")
    new_pr.update({
        "supplier": order_item.supplier,
        "items": [
            {
                "item_code": order_item.item_code,
                "qty": order_item.qty,
                "rate": order_item.rate,
                "warehouse": order_item.warehouse
            }
        ]
    })
    new_pr.submit()
