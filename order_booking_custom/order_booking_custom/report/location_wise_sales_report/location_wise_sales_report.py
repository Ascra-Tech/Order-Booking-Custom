import frappe
from frappe import _
from frappe.utils import flt, getdate

def execute(filters=None):
    if not filters:
        filters = {}

    # Fetch data based on filters
    data = get_sales_data(filters)

    # Define columns
    columns = get_columns()

    return columns, data

def get_columns():
    return [
        {"label": _("Location"), "fieldname": "location", "fieldtype": "Data", "width": 150},
        {"label": _("Salesperson"), "fieldname": "sales_person", "fieldtype": "Data", "width": 150},
        {"label": _("Dealer Name"), "fieldname": "dealer_name", "fieldtype": "Data", "width": 150},
        {"label": _("Segment"), "fieldname": "segment", "fieldtype": "Data", "width": 100},
        {"label": _("Voucher Type"), "fieldname": "voucher_type", "fieldtype": "Data", "width": 100},
        {"label": _("Actual Quantity"), "fieldname": "actual_qty", "fieldtype": "Float", "width": 120},
        {"label": _("Rejected Quantity"), "fieldname": "rejected_qty", "fieldtype": "Float", "width": 120},
        {"label": _("Invoice Amount"), "fieldname": "invoice_amount", "fieldtype": "Currency", "width": 150},
        {"label": _("Collection"), "fieldname": "collection", "fieldtype": "Currency", "width": 150},
    ]

def get_sales_data(filters):
    conditions = get_conditions(filters)

    query = """
        SELECT
            soi.branch AS location,
            soi.sales_person AS sales_person,
            so.dealer_name AS dealer_name,
            so.order_type AS voucher_type,
            soi.item_group AS segment,
            SUM(soi.qty) AS actual_qty,
            SUM(CASE WHEN soi.custom_status != 'Cancelled' THEN soi.qty ELSE 0 END) AS unit_qty,
            SUM(CASE WHEN soi.custom_status = 'Cancelled' THEN soi.qty ELSE 0 END) AS reject,
            SUM(soi.amount) AS inv_amount,
            SUM(so.advance_paid) AS collection
        FROM
            `tabSales Order` AS so
        JOIN
            `tabSales Order Item` AS soi ON so.name = soi.parent
        WHERE
            {conditions} AND so.docstatus = 1 AND soi.branch != "" 
        GROUP BY
            soi.branch, soi.sales_person, so.dealer_name, so.order_type, soi.item_group
        ORDER BY
            soi.item_group
    """.format(conditions=conditions)

    # Fetch data
    data = frappe.db.sql(query, filters, as_dict=True)

    # Calculate totals
    if data:
        total_row = {
            "location": "Total",
            "sales_person": "",
            "dealer_name": "",
            "voucher_type": "",
            "segment": "",
            "actual_qty": sum(row["actual_qty"] for row in data),
            "unit_qty": sum(row["unit_qty"] for row in data),
            "reject": sum(row["reject"] for row in data),
            "inv_amount": sum(row["inv_amount"] for row in data),
            "collection": sum(row["collection"] for row in data),
        }
        data.append(total_row)

    return data

def get_conditions(filters):
    conditions = ["1=1"]

    if filters.get("from_date"):
        conditions.append("so.transaction_date >= %(from_date)s")
    if filters.get("to_date"):
        conditions.append("so.transaction_date <= %(to_date)s")
    if filters.get("salesperson"):
        conditions.append("soi.sales_person = %(salesperson)s")
    if filters.get("dealer_name"):
        conditions.append("so.dealer_name = %(dealer_name)s")
    if filters.get("segment"):
        conditions.append("soi.item_group = %(segment)s")

    return " AND ".join(conditions)
