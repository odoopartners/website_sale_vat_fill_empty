import json

from odoo.http import request, route

from odoo.addons.website_sale.controllers.main import WebsiteSale as WebsiteSaleController
from odoo.addons.website_sale_vat_fill_empty.models.res_partner import CHECKOUT_VAT_CONTEXT


class WebsiteSale(WebsiteSaleController):
    """Allow a missing commercial NIF to be completed from checkout."""

    @staticmethod
    def _checkout_response_values(result):
        """Decode standard and wrapped checkout responses safely."""
        if isinstance(result, dict):
            return result
        if isinstance(result, str):
            payload = result
        elif hasattr(result, 'get_data'):
            payload = result.get_data(as_text=True)
        else:
            payload = getattr(result, 'data', b'')
            if isinstance(payload, bytes):
                payload = payload.decode()
        if not isinstance(payload, str):
            return {}
        try:
            values = json.loads(payload)
        except (TypeError, ValueError):
            return {}
        return values if isinstance(values, dict) else {}

    def _prepare_address_form_values(
        self, order_sudo, partner_sudo, address_type, use_delivery_as_billing,
        callback='', **kwargs
    ):
        values = super()._prepare_address_form_values(
            order_sudo,
            partner_sudo,
            address_type,
            use_delivery_as_billing,
            callback=callback,
            **kwargs,
        )
        base_partner = partner_sudo or order_sudo.partner_id
        company_partner = base_partner and base_partner.commercial_partner_id
        if (
            (address_type == 'billing' or use_delivery_as_billing)
            and company_partner
            and not company_partner.vat
        ):
            # This also covers a contact whose company has no NIF yet.
            values.update(show_vat=True, can_edit_vat=True)
        return values

    def _validate_address_values(
        self, address_values, partner_sudo, address_type, use_delivery_as_billing,
        required_fields, is_main_address, **kwargs
    ):
        if partner_sudo and not partner_sudo.commercial_partner_id.vat:
            partner_sudo = partner_sudo.with_context(
                **{CHECKOUT_VAT_CONTEXT: True}
            )
        return super()._validate_address_values(
            address_values,
            partner_sudo,
            address_type,
            use_delivery_as_billing,
            required_fields,
            is_main_address,
            **kwargs,
        )

    def _parse_form_data(self, form_data):
        """Keep checkout VAT in the values validated by standard Odoo.

        Some combinations of portal/website modules can omit ``vat`` from
        the generic form-writable field list even though the checkout renders
        the field. In that case the browser submits the value, but Odoo
        silently puts it in ``extra_form_data`` and it is never validated or
        saved. Only restore VAT here; all other fields keep Odoo's filtering.
        """
        address_values, extra_form_data = super()._parse_form_data(form_data)
        vat = form_data.get('vat')
        if vat and 'vat' not in address_values:
            address_values['vat'] = self._fix_eu_vat_number(
                vat.strip(), address_values.get('country_id')
            )
            extra_form_data.pop('vat', None)
        return address_values, extra_form_data

    @route()
    def shop_address_submit(
        self, partner_id=None, address_type='billing', use_delivery_as_billing=None,
        callback=None, required_fields=None, **form_data
    ):
        order_sudo = request.website.sale_get_order()
        partner_sudo = False
        if order_sudo:
            partner_sudo, address_type = super()._prepare_address_update(
                order_sudo,
                partner_id=partner_id and int(partner_id),
                address_type=address_type,
            )
        had_vat = bool(partner_sudo and partner_sudo.commercial_partner_id.vat)

        result = super().shop_address_submit(
            partner_id=partner_id,
            address_type=address_type,
            use_delivery_as_billing=use_delivery_as_billing,
            callback=callback,
            required_fields=required_fields,
            **form_data,
        )

        if not had_vat and form_data.get('vat'):
            feedback = self._checkout_response_values(result)
            if isinstance(result, dict):
                result = json.dumps(result)
            if 'redirectUrl' in feedback:
                order_sudo = request.website.sale_get_order()
                target_partner = order_sudo and (
                    order_sudo.partner_invoice_id
                    if address_type == 'billing'
                    else order_sudo.partner_shipping_id
                )
                company_partner = target_partner and target_partner.commercial_partner_id
                if company_partner and not company_partner.vat:
                    # The checkout has already run Odoo's VAT format/VIES
                    # validation. The helper writes the commercial partner,
                    # never only the child address.
                    target_partner._set_checkout_vat_on_commercial_partner(
                        form_data['vat']
                    )
        return result
