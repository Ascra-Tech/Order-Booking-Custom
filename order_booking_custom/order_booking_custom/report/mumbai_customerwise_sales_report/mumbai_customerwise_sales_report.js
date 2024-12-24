// Copyright (c) 2024, satya and contributors
// For license information, please see license.txt
frappe.query_reports["MUMBAI CUSTOMERWISE SALES REPORT"] = {
    "filters": [
        {
            "fieldname": "location",
            "label": __("Location"),
            "fieldtype": "Link",
            "options": "Branch",
            "default": ""
        },
        {
            "fieldname": "sales_person",
            "label": __("Sales Person"),
            "fieldtype": "Link",
            "options": "Sales Person",
            "default": ""
        },
        {
            "fieldname": "party_name",
            "label": __("Party Name"),
            "fieldtype": "Link",
            "options": "Customer",
            "default": ""
        }
    ]
};
