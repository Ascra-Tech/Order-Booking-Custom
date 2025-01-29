# Copyright (c) 2024, Satya and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    columns, data = [], []

    # Get report columns dynamically
    columns = get_columns()

    # Fetch report data
    report_data = get_report_data(filters)

    # Process and format the data
    formatted_data = format_report_data(report_data)

    # Return columns and data
    return columns, formatted_data


def get_columns():
    """Defines the columns dynamically for the report."""
    return [
        {"label": "Location", "fieldtype": "Data", "fieldname": "location", "width": 150},
        {"label": "Sales Person", "fieldtype": "Data", "fieldname": "sales_person", "width": 150},
        {"label": "Dealer Name", "fieldtype": "Data", "fieldname": "dealer_name", "width": 150},
        {"label": "Party Name", "fieldtype": "Data", "fieldname": "party_name", "width": 200},
        {"label": "Date", "fieldtype": "Date", "fieldname": "from_date", "width": 120},
        {"label": "Actual Quantity", "fieldtype": "Float", "fieldname": "actual_qty", "width": 120},
        {"label": "Unit Quantity", "fieldtype": "Float", "fieldname": "unit_qty", "width": 120},
        {"label": "Reject", "fieldtype": "Float", "fieldname": "reject", "width": 100}
    ]


def get_report_data(filters):
    """Fetches raw data from the database with date filters."""
    conditions = "WHERE so.docstatus = 1"

    # Apply filters dynamically
    if filters.get("location"):
        conditions += " AND soi.branch = %(location)s"
    if filters.get("sales_person"):
        conditions += " AND soi.sales_person = %(sales_person)s"
    if filters.get("party_name"):
        conditions += " AND so.customer = %(party_name)s"
    if filters.get("from_date"):
        conditions += " AND so.transaction_date >= %(from_date)s"
    if filters.get("to_date"):
        conditions += " AND so.transaction_date <= %(to_date)s"

    query = f"""
        SELECT
            soi.branch AS location,
            soi.sales_person AS sales_person,
            so.dealer_name AS dealer_name,
            so.customer AS party_name,
            so.transaction_date as from_date,
            SUM(soi.qty) AS actual_qty,
            SUM(CASE WHEN soi.custom_status != 'Cancelled' THEN soi.qty ELSE 0 END) AS unit_qty,
            SUM(CASE WHEN soi.custom_status = 'Cancelled' THEN soi.qty ELSE 0 END) AS reject
        FROM
            `tabSales Order` AS so
        JOIN
            `tabSales Order Item` AS soi ON so.name = soi.parent
        {conditions}
        GROUP BY
            soi.branch, soi.sales_person, so.dealer_name, so.customer
        ORDER BY
            soi.branch, soi.sales_person, so.dealer_name, so.customer
    """

    data = frappe.db.sql(query, filters, as_dict=True)
    return data


def format_report_data(report_data):
    """Processes and formats the data dynamically for nested totals."""
    formatted_data = []
    location_totals = {"actual_qty": 0, "unit_qty": 0, "reject": 0}
    current_location = None
    current_sales_person = None

    for row in report_data:
        # If location changes, add subtotal & total
        if current_location and row["location"] != current_location:
            formatted_data.append(get_subtotal_row(f"Total for {current_sales_person}", location_totals, is_final_total=False))
            location_totals = {"actual_qty": 0, "unit_qty": 0, "reject": 0}  # Reset location totals

        # If sales person changes, add subtotal
        if current_sales_person and row["sales_person"] != current_sales_person:
            formatted_data.append(get_subtotal_row(f"Subtotal for {current_sales_person}", location_totals, is_final_total=False))

        # Append row
        formatted_data.append(row)

        # Update totals
        location_totals["actual_qty"] += row["actual_qty"]
        location_totals["unit_qty"] += row["unit_qty"]
        location_totals["reject"] += row["reject"]

        # Update trackers
        current_location = row["location"]
        current_sales_person = row["sales_person"]

    # Append final total row
    formatted_data.append(get_subtotal_row("Final Total", location_totals, is_final_total=True))

    return formatted_data


def get_subtotal_row(label, totals, is_final_total=False):
    """Creates a subtotal/total row dynamically with different background colors."""
    bg_color = "#FFD700" if is_final_total else "#ADD8E6"  # Gold for Final Total, Light Blue for Subtotal

    return {
        "location": f"<b style='background-color:{bg_color}; padding:5px;'>{label}</b>",
        "sales_person": " ",
        "dealer_name": " ",
        "party_name": " ",
        "actual_qty": f"<b style='background-color:{bg_color}; padding:5px;'>{totals['actual_qty']}</b>",
        "unit_qty": f"<b style='background-color:{bg_color}; padding:5px;'>{totals['unit_qty']}</b>",
        "reject": f"<b style='background-color:{bg_color}; padding:5px;'>{totals['reject']}</b>",
    }
