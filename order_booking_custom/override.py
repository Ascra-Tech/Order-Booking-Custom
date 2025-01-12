from collections import defaultdict


import frappe
from frappe import _, bold
from frappe.model.naming import make_autoname
from frappe.query_builder.functions import CombineDatetime, Sum, Timestamp
from frappe.utils import add_days, cint, cstr, flt, get_link_to_form, now, nowtime, today
from pypika import Order

from erpnext.stock.deprecated_serial_batch import (
	DeprecatedBatchNoValuation,
	DeprecatedSerialNoValuation,
)
from erpnext.stock.valuation import round_off_if_near_zero

@frappe.whitelist()
def validate_item(self):
    msg = ""
    if self.sle.actual_qty > 0:
        if not self.item_details.has_batch_no and not self.item_details.has_serial_no:
            msg = f"Item {self.item_code} is not a batch or serial no item"

        if self.item_details.has_serial_no and not self.item_details.serial_no_series:
            msg += f". If you want auto pick serial bundle, then kindly set Serial No Series in Item {self.item_code}"

        if (
            self.item_details.has_batch_no
            and not self.item_details.batch_number_series
            and not frappe.db.get_single_value("Stock Settings", "naming_series_prefix")
        ):
            msg += f". If you want auto pick batch bundle, then kindly set Batch Number Series in Item {self.item_code}"

    elif self.sle.actual_qty < 0:
        if not frappe.db.get_single_value(
            "Stock Settings", "auto_create_serial_and_batch_bundle_for_outward"
        ):
            msg += ". If you want auto pick serial/batch bundle, then kindly enable 'Auto Create Serial and Batch Bundle' in Stock Settings."

    if msg:
        error_msg = (
            f"Serial and Batch Bundle not set for item {self.item_code} in warehouse {self.warehouse}"
            + msg
        )
        #frappe.throw(_(error_msg))