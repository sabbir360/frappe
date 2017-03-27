# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import validate_email_add
from frappe.model.document import Document
from email.utils import parseaddr

class EmailGroup(Document):
	def onload(self):
			singles = [d.name for d in frappe.db.get_all("DocType", "name", {"issingle": 1})]
			self.get("__onload").import_types = [{"value": d.parent, "label": "{0} ({1})".format(d.parent, d.label)} \
				for d in frappe.db.get_all("DocField", ("parent", "label"), {"options": "Email"}) 
				if d.parent not in singles]

	def import_from(self, doctype):
		"""Extract email ids from given doctype and add them to the current list"""
		meta = frappe.get_meta(doctype)
		email_field = [d.fieldname for d in meta.fields 
			if d.fieldtype in ("Data", "Small Text", "Text", "Code") and d.options=="Email"][0]
		unsubscribed_field = "unsubscribed" if meta.get_field("unsubscribed") else None
		added = 0

		for user in frappe.db.get_all(doctype, [email_field, unsubscribed_field or "name"]):
			try:
				email = parseaddr(user.get(email_field))[1]
				if email:
					frappe.get_doc({
						"doctype": "Email Group Member",
						"email_group": self.name,
						"email": email,
						"unsubscribed": user.get(unsubscribed_field) if unsubscribed_field else 0
					}).insert(ignore_permissions=True)

					added += 1
			except frappe.UniqueValidationError:
				pass

		frappe.msgprint(_("{0} subscribers added").format(added))

		return self.update_total_subscribers()

	def update_total_subscribers(self):
		self.total_subscribers = self.get_total_subscribers()
		self.db_update()
		return self.total_subscribers

	def get_total_subscribers(self):
		return frappe.db.sql("""select count(*) from `tabEmail Group Member`
			where email_group=%s""", self.name)[0][0]

	def on_trash(self):
		for d in frappe.get_all("Email Group Member", "name", {"email_group": self.name}):
			frappe.delete_doc("Email Group Member", d.name)

@frappe.whitelist()
def import_from(name, doctype):
	nlist = frappe.get_doc("Email Group", name)
	if nlist.has_permission("write"):
		return nlist.import_from(doctype)

@frappe.whitelist()
def add_subscribers(name, email_list):
	if not isinstance(email_list, (list, tuple)):
		email_list = email_list.replace(",", "\n").split("\n")
	count = 0
	for email in email_list:
		email = email.strip()
		valid = validate_email_add(email, False)

		if valid:
			if not frappe.db.get_value("Email Group Member",
				{"email_group": name, "email": email}):
				frappe.get_doc({
					"doctype": "Email Group Member",
					"email_group": name,
					"email": email
				}).insert(ignore_permissions = frappe.flags.ignore_permissions)

				count += 1
			else:
				pass
		else:
			frappe.msgprint(_("{0} is not a valid email id").format(email))

	frappe.msgprint(_("{0} subscribers added").format(count))

	return frappe.get_doc("Email Group", name).update_total_subscribers()

def restrict_email_group(doc, method):
	from frappe.limits import get_limits

	email_group_limit = get_limits().get('email_group')
	if not email_group_limit:
		return

	email_group = frappe.get_doc("Email Group", doc.email_group)
	if email_group.get_total_subscribers() >= email_group_limit:
		frappe.throw(_("Please Upgrade to add more than {0} subscribers").format(email_group_limit))
