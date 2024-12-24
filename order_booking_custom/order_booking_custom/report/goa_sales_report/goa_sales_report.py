import frappe

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": "Location", "fieldname": "location", "fieldtype": "Data", "width": 150},
        {"label": "Sales Person", "fieldname": "sales_person", "fieldtype": "Data", "width": 150},
        {"label": "Dealer Name", "fieldname": "dealer_name", "fieldtype": "Data", "width": 150},
        {"label": "Voucher Type", "fieldname": "voucher_type", "fieldtype": "Data", "width": 150},
        {"label": "Segment", "fieldname": "segment", "fieldtype": "Data", "width": 100},
        {"label": "Actual Quantity", "fieldname": "actual_qty", "fieldtype": "Float", "width": 100},
        {"label": "Unit Quantity", "fieldname": "unit_qty", "fieldtype": "Float", "width": 100},
        {"label": "Reject", "fieldname": "reject", "fieldtype": "Int", "width": 80},
        {"label": "INV Amount", "fieldname": "inv_amount", "fieldtype": "Currency", "width": 120},
        {"label": "Collection", "fieldname": "collection", "fieldtype": "Currency", "width": 120},
    ]

def get_data(filters):
    conditions = ""
    if filters.get("location"):
        conditions += " AND soi.branch = %(location)s"
    if filters.get("sales_person"):
        conditions += " AND soi.sales_person = %(sales_person)s"

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
            so.docstatus = 1 AND soi.branch = "Goa" {conditions}
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
            "location": "GOA Total",
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

