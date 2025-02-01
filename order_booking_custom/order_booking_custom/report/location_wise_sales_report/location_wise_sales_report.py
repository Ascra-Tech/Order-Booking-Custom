# import frappe
# from frappe import _
# from frappe.utils import flt, getdate

# def execute(filters=None):
#     if not filters:
#         filters = {}

#     # Fetch data based on filters
#     data = get_sales_data(filters)

#     # Define columns
#     columns = get_columns()

#     return columns, data

# def get_columns():
#     return [
#         {"label": _("Location"), "fieldname": "location", "fieldtype": "Data", "width": 150},
#         {"label": _("Salesperson"), "fieldname": "sales_person", "fieldtype": "Data", "width": 150},
#         {"label": _("Dealer Name"), "fieldname": "dealer_name", "fieldtype": "Data", "width": 150},
#         {"label": _("Segment"), "fieldname": "segment", "fieldtype": "Data", "width": 100},
#         {"label": _("Voucher Type"), "fieldname": "voucher_type", "fieldtype": "Data", "width": 100},
#         {"label": _("Actual Quantity"), "fieldname": "actual_qty", "fieldtype": "Float", "width": 120},
#         {"label": _("Rejected Quantity"), "fieldname": "rejected_qty", "fieldtype": "Float", "width": 120},
#         {"label": _("Invoice Amount"), "fieldname": "invoice_amount", "fieldtype": "Currency", "width": 150},
#         {"label": _("Collection"), "fieldname": "collection", "fieldtype": "Currency", "width": 150},
#     ]

# def get_sales_data(filters):
#     conditions = get_conditions(filters)

#     query = """
#         SELECT
#             soi.branch AS location,
#             soi.sales_person AS sales_person,
#             so.dealer_name AS dealer_name,
#             so.order_type AS voucher_type,
#             soi.item_group AS segment,
#             SUM(soi.qty) AS actual_qty,
#             SUM(CASE WHEN soi.custom_status != 'Cancelled' THEN soi.qty ELSE 0 END) AS unit_qty,
#             SUM(CASE WHEN soi.custom_status = 'Cancelled' THEN soi.qty ELSE 0 END) AS reject,
#             SUM(soi.amount) AS inv_amount,
#             SUM(so.advance_paid) AS collection
#         FROM
#             `tabSales Order` AS so
#         JOIN
#             `tabSales Order Item` AS soi ON so.name = soi.parent
#         WHERE
#             {conditions} AND so.docstatus = 1 AND soi.branch != "" 
#         GROUP BY
#             soi.branch, soi.sales_person, so.dealer_name, so.order_type, soi.item_group
#         ORDER BY
#             soi.item_group
#     """.format(conditions=conditions)

#     # Fetch data
#     data = frappe.db.sql(query, filters, as_dict=True)

#     # Calculate totals
#     if data:
#         total_row = {
#             "location": "Total",
#             "sales_person": "",
#             "dealer_name": "",
#             "voucher_type": "",
#             "segment": "",
#             "actual_qty": sum(row["actual_qty"] for row in data),
#             "unit_qty": sum(row["unit_qty"] for row in data),
#             "reject": sum(row["reject"] for row in data),
#             "inv_amount": sum(row["inv_amount"] for row in data),
#             "collection": sum(row["collection"] for row in data),
#         }
#         data.append(total_row)

#     return data

# def get_conditions(filters):
#     conditions = ["1=1"]

#     if filters.get("from_date"):
#         conditions.append("so.transaction_date >= %(from_date)s")
#     if filters.get("to_date"):
#         conditions.append("so.transaction_date <= %(to_date)s")
#     if filters.get("salesperson"):
#         conditions.append("soi.sales_person = %(salesperson)s")
#     if filters.get("dealer_name"):
#         conditions.append("so.dealer_name = %(dealer_name)s")
#     if filters.get("segment"):
#         conditions.append("soi.item_group = %(segment)s")

#     return " AND ".join(conditions)


import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
    if not filters:
        filters = {}

    data = get_sales_data(filters)
    columns = get_columns()

    return columns, data

def get_columns():
    return [
        {"label": _("✨ Location"), "fieldname": "location", "fieldtype": "Data", "width": 150},
        {"label": _("👨‍💼 Salesperson"), "fieldname": "sales_person", "fieldtype": "Data", "width": 150},
        {"label": _("👤 Dealer Name"), "fieldname": "dealer_name", "fieldtype": "Data", "width": 150},
        {"label": _("💼 Voucher Type"), "fieldname": "voucher_type", "fieldtype": "Data", "width": 120},
        {"label": _("👀 Segment"), "fieldname": "segment", "fieldtype": "Data", "width": 120},
        {"label": _("✔️ Actual Quantity"), "fieldname": "actual_qty", "fieldtype": "Float", "width": 120},
        {"label": _("❌ Rejected Quantity"), "fieldname": "rejected_qty", "fieldtype": "Float", "width": 120},
        {"label": _("💰 Invoice Amount"), "fieldname": "invoice_amount", "fieldtype": "Currency", "width": 150},
        {"label": _("🏆 Collection"), "fieldname": "collection", "fieldtype": "Currency", "width": 150}
    ]

def get_sales_data(filters):
    conditions = get_conditions(filters)
    query = f'''
        SELECT
            soi.branch AS location,
            soi.sales_person AS sales_person,
            so.dealer_name AS dealer_name,
            so.order_type AS voucher_type,
            soi.item_group AS segment,
            SUM(soi.qty) AS actual_qty,
            SUM(CASE WHEN soi.custom_status != 'Cancelled' THEN soi.qty ELSE 0 END) AS unit_qty,
            SUM(CASE WHEN soi.custom_status = 'Cancelled' THEN soi.qty ELSE 0 END) AS rejected_qty,
            SUM(soi.amount) AS invoice_amount,
            SUM(so.advance_paid) AS collection
        FROM `tabSales Order` AS so
        JOIN `tabSales Order Item` AS soi ON so.name = soi.parent
        WHERE {conditions} AND so.docstatus = 1 AND soi.branch != ""
        GROUP BY soi.branch, soi.sales_person, so.dealer_name, so.order_type, soi.item_group
        ORDER BY soi.sales_person, so.order_type
    '''

    data = frappe.db.sql(query, filters, as_dict=True)
    
    # Subtotals and Final Total Calculation
    subtotal_rows = []
    final_totals = {"actual_qty": 0, "rejected_qty": 0, "invoice_amount": 0, "collection": 0}
    current_voucher = None
    current_salesperson = None
    voucher_totals = {}
    salesperson_totals = {}
    
    processed_data = []
    for row in data:
        if row["voucher_type"] != current_voucher or row["sales_person"] != current_salesperson:
            if current_voucher:
                processed_data.append(voucher_totals)
            if current_salesperson and row["sales_person"] != current_salesperson:
                processed_data.append(salesperson_totals)
            
            current_voucher = row["voucher_type"]
            current_salesperson = row["sales_person"]

            
            
            voucher_totals = {
                "location": "",
                "sales_person": row["sales_person"],
                "dealer_name": "",
                "voucher_type":f"<b style='background-color:#89f853; padding:5px;'>{row['voucher_type'] } Subtotal</b>" ,
                "segment": "",
                "actual_qty": 0,
                "rejected_qty": 0,
                "invoice_amount": 0,
                "collection": 0,
            }
            salesperson_totals = {
                "location": "",
                "sales_person":f"<b style='background-color:#FFD700; padding:5px;'>{row['sales_person']} Total</b>" ,
                "dealer_name": "",
                "voucher_type": "",
                "segment": "",
                "actual_qty": 0,
                "rejected_qty": 0,
                "invoice_amount": 0,
                "collection": 0,
            }
        
        # Aggregate Subtotals
        voucher_totals["actual_qty"] += row["actual_qty"]
        voucher_totals["rejected_qty"] += row["rejected_qty"]
        voucher_totals["invoice_amount"] += row["invoice_amount"]
        voucher_totals["collection"] += row["collection"]
        
        salesperson_totals["actual_qty"] += row["actual_qty"]
        salesperson_totals["rejected_qty"] += row["rejected_qty"]
        salesperson_totals["invoice_amount"] += row["invoice_amount"]
        salesperson_totals["collection"] += row["collection"]
        
        # Aggregate Final Totals
        for key in final_totals:
            final_totals[key] += row[key]
            
        processed_data.append(row)
    
    if voucher_totals:
        processed_data.append(voucher_totals)
    if salesperson_totals:
        processed_data.append(salesperson_totals)
    
    # Append Final Total Row
    final_totals_row = {
        "location": "<b style='background-color:#6cfb27; padding:5px;'>Grand Total</b>",
        "sales_person": "",
        "dealer_name": "",
        "voucher_type": "",
        "segment": "",
        "actual_qty": final_totals["actual_qty"],
        "rejected_qty": final_totals["rejected_qty"],
        "invoice_amount": final_totals["invoice_amount"],
        "collection": final_totals["collection"],
    }
    processed_data.append(final_totals_row)
    
    return processed_data

def get_conditions(filters):
    conditions = ["1=1"]
    if filters.get("from_date"):
        conditions.append("so.transaction_date >= %(from_date)s")
    if filters.get("to_date"):
        conditions.append("so.transaction_date <= %(to_date)s")
    if filters.get("location"):
        conditions.append("soi.branch = %(location)s")
    if filters.get("salesperson"):
        conditions.append("soi.sales_person = %(salesperson)s")
    if filters.get("dealer_name"):
        conditions.append("so.dealer_name = %(dealer_name)s")
    if filters.get("segment"):
        conditions.append("soi.item_group = %(segment)s")
    if filters.get("voucher_type"):
        conditions.append("so.order_type = %(voucher_type)s")
    return " AND ".join(conditions)
