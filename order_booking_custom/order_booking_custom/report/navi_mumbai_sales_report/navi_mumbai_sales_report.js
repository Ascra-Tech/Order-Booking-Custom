// Copyright (c) 2024, satya and contributors
// For license information, please see license.txt

frappe.query_reports["NAVI MUMBAI SALES REPORT"] = {
    "filters": [
        {
            "fieldname": "location",
            "label": __("Location"),
            "fieldtype": "Link",
            "options": "Branch",
        },
        {
            "fieldname": "sales_person",
            "label": __("Sales Person"),
            "fieldtype": "Link",
            "options": "Sales Person",
        },
        {
            "fieldname": "dealer_name",
            "label": __("Dealer Name"),
            "fieldtype": "Data"
        }
    ]
};
