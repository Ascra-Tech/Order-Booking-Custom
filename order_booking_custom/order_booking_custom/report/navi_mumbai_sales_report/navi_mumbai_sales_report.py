import frappe

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    formatted_data = format_hierarchy(data)
    return columns, formatted_data

def get_columns():
    return [
        {"label": "Location", "fieldname": "location", "fieldtype": "Data", "width": 120},
        {"label": "Sales Person", "fieldname": "sales_person", "fieldtype": "Data", "width": 120},
        {"label": "Dealer Name", "fieldname": "dealer_name", "fieldtype": "Data", "width": 150},
        {"label": "Voucher Type", "fieldname": "voucher_type", "fieldtype": "Data", "width": 120},
        {"label": "Segment", "fieldname": "segment", "fieldtype": "Data", "width": 120},
        {"label": "Actual Quantity", "fieldname": "actual_qty", "fieldtype": "Float", "width": 100},
        {"label": "Unit Quantity", "fieldname": "unit_qty", "fieldtype": "Float", "width": 100},
        {"label": "Reject", "fieldname": "reject", "fieldtype": "Int", "width": 80},
        {"label": "INV Amount", "fieldname": "inv_amount", "fieldtype": "Currency", "width": 120},
        {"label": "Collection", "fieldname": "collection", "fieldtype": "Currency", "width": 120},
    ]

def get_data(filters):
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
            so.docstatus = 1 AND soi.branch != ""
        GROUP BY
            soi.branch, soi.sales_person, so.dealer_name, soi.item_group
        ORDER BY
            soi.branch, soi.sales_person, so.dealer_name, soi.item_group
    """
    return frappe.db.sql(query, as_dict=True)

def format_hierarchy(data):
    formatted = []
    location_totals = {}
    overall_totals = {
        "actual_qty": 0, "unit_qty": 0, "reject": 0, "inv_amount": 0, "collection": 0
    }

    for row in data:
        location = row["location"]
        sales_person = row["sales_person"]
        
        # Initialize location totals if not present
        if location not in location_totals:
            location_totals[location] = {
                "actual_qty": 0, "unit_qty": 0, "reject": 0, "inv_amount": 0, "collection": 0
            }

        # Update location and overall totals
        for key in ["actual_qty", "unit_qty", "reject", "inv_amount", "collection"]:
            location_totals[location][key] += row[key]
            overall_totals[key] += row[key]

        # Append data row
        formatted.append(row)

    # Add subtotal rows for each location
    for location, totals in location_totals.items():
        subtotal_row = {
            "location": f"{location} Total",
            "actual_qty": totals["actual_qty"],
            "unit_qty": totals["unit_qty"],
            "reject": totals["reject"],
            "inv_amount": totals["inv_amount"],
            "collection": totals["collection"],
        }
        formatted.append(subtotal_row)

    # Add grand total row
    grand_total_row = {
        "location": "Overall Total",
        "actual_qty": overall_totals["actual_qty"],
        "unit_qty": overall_totals["unit_qty"],
        "reject": overall_totals["reject"],
        "inv_amount": overall_totals["inv_amount"],
        "collection": overall_totals["collection"],
    }
    formatted.append(grand_total_row)

    return formatted
