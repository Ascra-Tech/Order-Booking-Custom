import frappe
from frappe.utils import flt



@frappe.whitelist()
def cancel_trash_pr(self,method=None):
    
    if self.custom_purchase_order and self.custom_order_booking:
        get_ob=frappe.get_doc("Order Booking Form",self.custom_order_booking)
        if get_ob.custom_purchase_order:
            get_pr=frappe.db.get_value("Purchase Receipt Item",{"purchase_order":get_ob.custom_purchase_order},"parent")
            if get_pr:
                frappe.db.set_value("Order Booking Form",self.custom_order_booking,"custom_purchase_receipt","")
                
                get_pr_data=frappe.get_doc("Purchase Receipt",get_pr)
                if get_pr_data.docstatus != 2:
                    get_pr_data.cancel()

                get_po_date=frappe.get_doc("Purchase Order",get_ob.custom_purchase_order)
                if get_po_date.docstatus != 2:
                    get_po_date.cancel()

                frappe.db.commit()
                frappe.db.delete("Stock Ledger Entry",{"voucher_no":get_pr})
                frappe.db.delete("Purchase Receipt",{"name":get_pr})
                frappe.db.delete("Purchase Order",{"name":get_ob.custom_purchase_order})
                frappe.db.set_value("Order Booking Form",self.custom_order_booking,"custom_purchase_order","")
        


    