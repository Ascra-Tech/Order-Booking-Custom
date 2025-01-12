import frappe

def execute(filters=None):
    columns, data = [], []

    # Get report columns
    columns = get_columns()

    # Fetch report data
    report_data = get_report_data(filters)

    # Process and format the data
    formatted_data = format_report_data(report_data)

    # Return columns and data
    return columns, formatted_data


def get_columns():
    """Defines the columns for the report."""
    return [
        {"label": "Location", "fieldtype": "Data","fieldname":"location", "width": 100},
        {"label": "Sales Person", "fieldtype": "Data","fieldname":"sales_person",  "width": 150},
        {"label": "Dealer Name", "fieldtype": "Data", "fieldname":"dealer_name", "width": 150},
        {"label": "Party Name", "fieldtype": "Data","fieldname":"party_name", "width": 200},
        {"label": "Actual Quantity", "fieldtype": "Float","fieldname":"actual_qty", "width": 120},
        {"label": "Unit Quantity", "fieldtype": "Float","fieldname":"unit_qty", "width": 120},
        {"label": "Reject", "fieldtype": "Float","fieldname":"reject", "width": 80},
    ]


def get_report_data(filters):
    """Fetches raw data from the database."""
    conditions = "WHERE so.docstatus = 1"

    # Apply filters if available
    if filters.get("location"):
        conditions += " AND soi.branch = %(location)s"
    if filters.get("sales_person"):
        conditions += " AND soi.sales_person = %(sales_person)s"
    if filters.get("party_name"):
        conditions += " AND so.customer = %(party_name)s"

    query = """
        SELECT
            soi.branch AS location,
            soi.sales_person AS sales_person,
            so.dealer_name AS dealer_name,
            so.customer AS party_name,
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
    """.format(conditions=conditions)

    data=frappe.db.sql(query, filters, as_dict=True)
    frappe.log_error("data",data)
    return data


def format_report_data(report_data):
    """Processes and formats the data for nested totals."""
    formatted_data = []
    location_total = {"actual_qty": 0, "unit_qty": 0, "reject": 0}
    current_location = ""
    current_sales_person = ""

    for row in report_data:
        # Check if location or sales person changes
        if row["location"] != current_location:
            if current_location:
                # Append location subtotal
                formatted_data.append(get_subtotal_row("Total for " + current_sales_person, location_total))
                location_total = {"actual_qty": 0, "unit_qty": 0, "reject": 0}

            # Append location row
            formatted_data.append({
                "location": row["location"],
                "sales_person": "",
                "dealer_name": "",
                "party_name": "",
                "actual_qty": "",
                "unit_qty": "",
                "reject": ""
            })
            current_location = row["location"]

        if row["sales_person"] != current_sales_person:
            if current_sales_person:
                # Append sales person subtotal
                formatted_data.append(get_subtotal_row("Subtotal for " + current_sales_person, location_total))
            current_sales_person = row["sales_person"]

        # Append individual row
        formatted_data.append(row)

        # Update totals
        location_total["actual_qty"] += row["actual_qty"]
        location_total["unit_qty"] += row["unit_qty"]
        location_total["reject"] += row["reject"]

    # Append the final total
    formatted_data.append(get_subtotal_row("Final Total", location_total))

    return formatted_data


def get_subtotal_row(label, totals):
    """Creates a subtotal row."""
    return {
        "location": label,
        "sales_person": "",
        "dealer_name": "",
        "party_name": "",
        "actual_qty": totals["actual_qty"],
        "reject": totals["reject"]
    }
