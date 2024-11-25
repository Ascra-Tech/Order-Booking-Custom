import frappe


@frappe.whitelist()
def update_serial_no_on_item_change(doc, method):
    for child in doc.get("order_booking_details"):  # Replace with your actual child table fieldname
        if child.idx:  # Assuming 'idx' determines the row index
            # Fetch the current serial no record from the database
            serial_no_doc = frappe.get_doc("Serial No", child.tyre_serial_number)  # Replace with your Serial No doctype name
            
            # Check if the item_code in the serial number matches the updated one
            if serial_no_doc.item_code != child.item_code:
                get_sbbb=frappe.db.get_value("Serial and Batch Entry",{"serial_no":child.tyre_serial_number},"parent")
                if get_sbbb:
                    if frappe.db.exists("Serial and Batch Bundle", {"name": get_sbbb,"item_code":serial_no_doc.item_code}):
                        frappe.db.set_value("Serial and Batch Bundle",get_sbbb,"item_code",child.item_code)
                # Update the item_code in the Serial No document
                # serial_no_doc.item_code = child.item_code
                frappe.db.set_value("Serial No",child.tyre_serial_number,"item_code",child.item_code)
                # serial_no_doc.save(ignore_permissions=True)
                frappe.db.commit()  # Commit changes to the database
