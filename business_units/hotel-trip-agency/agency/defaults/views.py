"""View architectures for agency module.

All XML arch strings used by setup scripts to create/update Odoo views.
Centralized here so they can be reviewed and maintained independently of scripts.
"""

# ── Sale Order Form: Biblia Operativa tab (view 4487) ─────────────────────

SALE_ORDER_BIBLIA_ARCH = '''<data>
    <xpath expr="//div[@name='button_box']" position="inside">
        <button class="oe_stat_button" type="action" name="{view_budget_action_id}"
                icon="fa-bar-chart" invisible="not x_budget_id">
            <field name="x_budget_id" invisible="1"/>
            <span class="o_stat_text">Presupuesto</span>
        </button>
    </xpath>
    <xpath expr="//group[@name='sale_header']" position="after">
        <group string="Tour" name="tour_info">
            <group>
                <field name="x_is_tour"/>
                <field name="x_service_type" invisible="not x_is_tour" required="x_is_tour"/>
                <field name="x_travel_date" invisible="not x_is_tour"/>
                <field name="x_tour_start_date" invisible="not x_is_tour" required="x_is_tour"/>
                <field name="x_tour_end_date" invisible="not x_is_tour" required="x_is_tour"/>
            </group>
            <group>
                <field name="x_num_passengers" invisible="not x_is_tour" required="x_is_tour"/>
                <field name="x_departure_city" invisible="not x_is_tour"/>
                <field name="x_tour_group_ids" invisible="not x_is_tour"
                       widget="many2many_tags" string="Grupos"
                       options="{'color_field': 'x_color', 'no_create_edit': True}"/>
            </group>
        </group>
    </xpath>
    <xpath expr="//notebook" position="inside">
        <page string="Biblia Operativa" name="biblia_operativa" invisible="not x_is_tour">
            <div class="d-flex gap-2 mb-3" name="biblia_buttons">
                <button name="{biblia_report_action_id}" type="action" string="Descargar Biblia Operativa" class="btn btn-primary" icon="fa-file-pdf-o"/>
            </div>
            <group string="Informacion General" name="biblia_general">
                <group>
                    <field name="name" string="Codigo de Reserva" readonly="1"/>
                    <field name="partner_id" string="Contacto Principal" readonly="1"/>
                </group>
                <group>
                    <field name="x_tour_start_date" string="Fecha Inicio" readonly="1"/>
                    <field name="x_tour_end_date" string="Fecha Fin" readonly="1"/>
                    <field name="x_service_type" string="Tipo Servicio" readonly="1"/>
                    <field name="x_departure_city" string="Lugar de Partida" readonly="1"/>
                </group>
            </group>
            <separator string="Itinerario"/>
            <field name="x_itinerary_line_ids">
                <list default_order="x_sequence asc, x_day_number asc" editable="bottom">
                    <control><create string="Agregar dia"/></control>
                    <field name="x_sequence" widget="handle"/>
                    <field name="x_day_number" string="Dia"/>
                    <field name="x_title" string="Titulo"/>
                    <field name="x_description" string="Descripcion"/>
                    <field name="x_accommodation" string="Alojamiento"/>
                    <field name="x_meals" string="Comidas"/>
                </list>
            </field>
            <separator string="Pasajeros"/>
            <div class="mb-2" name="voucher_button">
                <button name="{voucher_report_action_id}" type="action" string="Descargar Vouchers de Pasajeros" class="btn btn-secondary btn-sm" icon="fa-id-card"/>
            </div>
            <field name="x_guest_line_ids">
                <list default_order="x_sequence asc, id desc">
                    <control><create string="Agregar pasajero"/></control>
                    <field name="x_sequence" widget="handle"/>
                    <field name="x_guest_partner_id" string="Pasajero" required="1"/>
                    <field name="x_tour_group_id" string="Grupo" options="{'no_create': True}"/>
                    <field name="x_nationality_id" string="Nacionalidad" readonly="1"/>
                    <field name="x_document_number_rel" string="Nro. Doc." readonly="1"/>
                    <field name="x_phone_rel" string="Telefono" readonly="1"/>
                    <field name="x_guest_identity_check" widget="badge" readonly="1"
                        decoration-success="x_guest_identity_check == 'ok'"
                        decoration-warning="x_guest_identity_check == 'na'"
                        decoration-danger="x_guest_identity_check == 'invalid'"/>
                </list>
                <form>
                    <group>
                        <group string="Datos Personales">
                            <field name="x_guest_partner_id" string="Nombre Completo" required="1"/>
                            <field name="x_nationality_id" string="Nacionalidad" readonly="1"/>
                            <field name="x_document_type_rel" string="Tipo de Documento" readonly="1"/>
                            <field name="x_document_number_rel" string="Nro. de Documento" readonly="1"/>
                            <field name="x_birthdate_rel" string="Fecha de Nacimiento" readonly="1"/>
                            <field name="x_lang_rel" string="Idioma" readonly="1"/>
                        </group>
                        <group string="Contacto">
                            <field name="x_phone_rel" string="Telefono" readonly="1"/>
                            <field name="x_email_rel" string="Email" readonly="1"/>
                        </group>
                    </group>
                    <group>
                        <group string="Salud y Restricciones">
                            <field name="x_medical_rel" string="Restricciones Medicas / Alimentarias" readonly="1"/>
                        </group>
                        <group string="Contacto de Emergencia">
                            <field name="x_emergency_name_rel" string="Nombre" readonly="1"/>
                            <field name="x_emergency_phone_rel" string="Telefono" readonly="1"/>
                        </group>
                    </group>
                    <group>
                        <group>
                            <field name="x_guest_identity_check" widget="badge" readonly="1"
                                decoration-success="x_guest_identity_check == 'ok'"
                                decoration-warning="x_guest_identity_check == 'na'"
                                decoration-danger="x_guest_identity_check == 'invalid'"
                                string="Verificacion Identidad"/>
                        </group>
                    </group>
                </form>
            </field>
            <separator string="Operadores Asignados"/>
            <field name="x_operator_line_ids" context="{'default_x_cost_currency_id': currency_id}">
                <list>
                    <field name="x_sequence" widget="handle"/>
                    <field name="x_product_id" string="Servicio" optional="show"
                        domain="[('type', '=', 'service')]"/>
                    <field name="x_partner_id" string="Operador" class="text-wrap"/>
                    <field name="x_service_type" string="Tipo de Servicio"/>
                    <field name="x_description" string="Descripcion" class="text-wrap"/>
                    <field name="x_date" string="Fecha"/>
                    <field name="x_cost_currency_id" string="Mon." optional="hide"/>
                    <field name="x_cost" string="Costo Est." widget="monetary"
                        options="{'currency_field': 'x_cost_currency_id'}"/>
                    <field name="x_cost_pen" string="Equiv. PEN" readonly="1" optional="hide"/>
                    <field name="x_purchase_order_id" string="Pedido Compra"/>
                    <field name="x_po_state" string="Estado PO" widget="badge"
                        decoration-info="x_po_state == 'draft'"
                        decoration-warning="x_po_state == 'sent'"
                        decoration-success="x_po_state == 'purchase'"
                        invisible="not x_purchase_order_id"/>
                    <field name="x_po_price" string="Precio PO" readonly="1"
                        widget="monetary" options="{'currency_field': 'x_cost_currency_id'}"
                        optional="show"/>
                </list>
                <form string="Operador">
                    <group>
                        <group string="Servicio">
                            <field name="x_product_id" string="Producto/Servicio"
                                domain="[('type', '=', 'service')]"/>
                            <field name="x_partner_id" string="Operador" required="1"/>
                            <field name="x_service_type" string="Tipo de Servicio" required="1"/>
                            <field name="x_description" string="Descripcion"
                                placeholder="Ej: Cusco a Ollantaytambo"/>
                            <field name="x_date" string="Fecha"/>
                        </group>
                        <group string="Contacto y Costo">
                            <field name="x_phone_rel" string="Telefono" readonly="1"/>
                            <field name="x_email_rel" string="Email" readonly="1"/>
                            <field name="x_cost_currency_id" string="Moneda"/>
                            <field name="x_cost" string="Costo Estimado" widget="monetary"
                                options="{'currency_field': 'x_cost_currency_id'}"/>
                            <field name="x_cost_pen" string="Equivalente PEN" readonly="1"/>
                        </group>
                    </group>
                    <group string="Pedido de Compra" invisible="not x_purchase_order_id">
                        <field name="x_purchase_order_id" readonly="1"/>
                        <field name="x_po_state" string="Estado" widget="badge" readonly="1"/>
                        <field name="x_po_line_id" readonly="1" invisible="1"/>
                        <field name="x_po_price" string="Precio Real PO" readonly="1"
                            widget="monetary" options="{'currency_field': 'x_cost_currency_id'}"/>
                    </group>
                </form>
            </field>
            <div class="d-flex gap-2 mt-2 mb-3">
                <button name="{create_po_action_id}" type="action"
                    string="Generar Pedidos de Compra"
                    class="btn btn-secondary" icon="fa-shopping-cart"
                    confirm="Se crearan pedidos de compra para todos los operadores que no tengan uno asignado. Continuar?"/>
                <button name="{create_budget_action_id}" type="action"
                    string="Crear Presupuesto" class="btn btn-secondary" icon="fa-bar-chart"
                    confirm="Se creara un presupuesto basado en los costos estimados. Continuar?"/>
            </div>
            <group string="Resumen Financiero" col="4" invisible="not x_is_tour" name="financial_summary">
                <field name="x_company_currency_id" invisible="1"/>
                <field name="x_total_estimated_cost" string="Costo Est. Total (PEN)"
                    widget="monetary" options="{'currency_field': 'x_company_currency_id'}" readonly="1"/>
                <field name="x_estimated_margin" string="Margen Estimado (PEN)"
                    widget="monetary" options="{'currency_field': 'x_company_currency_id'}" readonly="1"
                    decoration-success="x_estimated_margin &gt; 0"
                    decoration-danger="x_estimated_margin &lt; 0"/>
                <field name="x_estimated_margin_percent" string="Margen %"
                    widget="percentage" readonly="1"/>
                <field name="x_total_estimated_cost_cur" string="Costo Est. Total"
                    widget="monetary" readonly="1"
                    invisible="currency_id == x_company_currency_id"/>
                <field name="x_estimated_margin_cur" string="Margen Estimado"
                    widget="monetary" readonly="1"
                    decoration-success="x_estimated_margin_cur &gt; 0"
                    decoration-danger="x_estimated_margin_cur &lt; 0"
                    invisible="currency_id == x_company_currency_id"/>
            </group>
            <separator string="Servicios Incluidos"/>
            <field name="x_inclusions" placeholder="Detalle de servicios incluidos en el paquete..."/>
            <group string="Horarios y Observaciones">
                <field name="x_key_times"
                    placeholder="Ej: Recojo hotel 5:00am, Vuelo CUZ-LIM 18:30..."
                    nolabel="1" colspan="2"/>
                <field name="x_special_observations"
                    placeholder="Restricciones, pedidos especiales, notas operativas..."
                    nolabel="1" colspan="2"/>
            </group>
        </page>
    </xpath>
</data>'''

# ── Sale Order Template Form: Biblia Operativa tab (view 4489) ────────────

TEMPLATE_BIBLIA_ARCH = '''<data>
    <xpath expr="//group[@name='sale_info']" position="inside">
        <field name="x_is_tour"/>
    </xpath>
    <xpath expr="//notebook[@name='main_book']" position="inside">
        <page string="Biblia Operativa" name="biblia_operativa" invisible="not x_is_tour">
            <separator string="Itinerario"/>
            <field name="x_itinerary_line_ids">
                <list default_order="x_sequence asc, x_day_number asc" editable="bottom">
                    <control><create string="Agregar dia"/></control>
                    <field name="x_sequence" widget="handle"/>
                    <field name="x_day_number" string="Dia"/>
                    <field name="x_title" string="Titulo"/>
                    <field name="x_description" string="Descripcion"/>
                    <field name="x_accommodation" string="Alojamiento"/>
                    <field name="x_meals" string="Comidas"/>
                </list>
            </field>
            <separator string="Operadores por Defecto"/>
            <field name="x_operator_line_ids">
                <list>
                    <field name="x_sequence" widget="handle"/>
                    <field name="x_product_id" string="Servicio" optional="show"
                        domain="[('type', '=', 'service')]"/>
                    <field name="x_partner_id" string="Operador" class="text-wrap"/>
                    <field name="x_service_type" string="Tipo de Servicio"/>
                    <field name="x_description" string="Descripcion" class="text-wrap"/>
                    <field name="x_date" string="Fecha"/>
                    <field name="x_cost_currency_id" string="Mon." optional="hide"/>
                    <field name="x_cost" string="Costo Est." widget="monetary"
                        options="{'currency_field': 'x_cost_currency_id'}"/>
                </list>
                <form string="Operador">
                    <group>
                        <group string="Servicio">
                            <field name="x_product_id" string="Producto/Servicio"
                                domain="[('type', '=', 'service')]"/>
                            <field name="x_partner_id" string="Operador" required="1"/>
                            <field name="x_service_type" string="Tipo de Servicio" required="1"/>
                            <field name="x_description" string="Descripcion"
                                placeholder="Ej: Cusco a Ollantaytambo"/>
                            <field name="x_date" string="Fecha"/>
                        </group>
                        <group string="Contacto y Costo">
                            <field name="x_phone_rel" string="Telefono" readonly="1"/>
                            <field name="x_email_rel" string="Email" readonly="1"/>
                            <field name="x_cost_currency_id" string="Moneda"/>
                            <field name="x_cost" string="Costo Estimado" widget="monetary"
                                options="{'currency_field': 'x_cost_currency_id'}"/>
                        </group>
                    </group>
                </form>
            </field>
            <separator string="Servicios Incluidos"/>
            <field name="x_inclusions" placeholder="Detalle de servicios incluidos en el paquete..."/>
            <group string="Horarios y Observaciones">
                <field name="x_key_times"
                    placeholder="Ej: Recojo hotel 5:00am, Vuelo CUZ-LIM 18:30..."
                    nolabel="1" colspan="2"/>
                <field name="x_special_observations"
                    placeholder="Restricciones, pedidos especiales..."
                    nolabel="1" colspan="2"/>
            </group>
        </page>
    </xpath>
</data>'''

# ── Partner Form: Guest fields (inherits from booking engine view) ────────
# Inherits from view 3702 (res.partner.form.inherit.booking_engine)

PARTNER_GUEST_FIELDS_ARCH = '''<data>
    <xpath expr="//field[@name='x_document_type']" position="attributes">
        <attribute name="string">Tipo Doc. de Viaje</attribute>
    </xpath>
    <xpath expr="//field[@name='x_document_number']" position="attributes">
        <attribute name="string">Nro. Doc. de Viaje</attribute>
        <attribute name="placeholder">Requerido para validacion de identidad</attribute>
    </xpath>
    <xpath expr="//field[@name='x_document_number']" position="after">
        <field name="x_birthdate" string="Fecha de Nacimiento"/>
    </xpath>
    <xpath expr="//field[@name='x_nationality']/.." position="after">
        <group string="Info Pasajero">
            <field name="x_medical_restrictions" string="Restricciones Medicas / Alimentarias" placeholder="Ej: Vegetariano, alergia a mariscos, diabetes..."/>
            <field name="x_emergency_contact_name" string="Contacto Emergencia" placeholder="Nombre completo"/>
            <field name="x_emergency_contact_phone" string="Tel. Emergencia" placeholder="+51 999 999 999"/>
        </group>
    </xpath>
</data>'''

# ── Sale Order PDF Report: Exchange Rate (view 4486) ─────────────────────
# Adds exchange rate display below totals on quotation PDF

EXCHANGE_RATE_ARCH = '''<data>
    <xpath expr="//div[@name='so_total_summary']" position="inside">
        <div class="text-end mt-2" style="font-size: 0.85em; color: #555;">
            <t t-set="company_currency" t-value="doc.company_id.currency_id"/>
            <t t-if="doc.currency_id != company_currency and doc.currency_rate">
                <em>Tipo de cambio: 1 <t t-out="doc.currency_id.name"/> = <t t-out="'%.4f' % (1.0 / doc.currency_rate)"/> <t t-out="company_currency.name"/></em>
            </t>
        </div>
    </xpath>
</data>'''

# ── Automation code: copy Biblia from template to quotation ───────────────

BIBLIA_AUTOMATION_CODE = '''for record in records:
    tmpl = record.sale_order_template_id
    if not tmpl:
        continue
    if not tmpl.x_is_tour:
        continue
    if record.x_is_tour and record.x_itinerary_line_ids:
        continue
    vals = {
        "x_is_tour": True,
        "x_inclusions": tmpl.x_inclusions or False,
        "x_key_times": tmpl.x_key_times or False,
        "x_special_observations": tmpl.x_special_observations or False,
    }
    record.write(vals)
    existing_itin = env["x_itinerary_line"].search([("x_sale_order_id", "=", record.id)])
    if existing_itin:
        existing_itin.unlink()
    for line in tmpl.x_itinerary_line_ids:
        env["x_itinerary_line"].create({
            "x_sale_order_id": record.id,
            "x_sequence": line.x_sequence or 0,
            "x_day_number": line.x_day_number or 0,
            "x_title": line.x_title or False,
            "x_name": line.x_name or False,
            "x_description": line.x_description or False,
            "x_accommodation": line.x_accommodation or False,
            "x_meals": line.x_meals or False,
        })
    existing_ops = env["x_operator_line"].search([("x_sale_order_id", "=", record.id)])
    if existing_ops:
        existing_ops.unlink()
    for op in tmpl.x_operator_line_ids:
        env["x_operator_line"].create({
            "x_sale_order_id": record.id,
            "x_sequence": op.x_sequence or 0,
            "x_partner_id": op.x_partner_id.id if op.x_partner_id else False,
            "x_service_type": op.x_service_type or False,
            "x_name": op.x_name or False,
            "x_description": op.x_description or False,
            "x_date": op.x_date or False,
            "x_product_id": op.x_product_id.id if op.x_product_id else False,
            "x_cost_currency_id": op.x_cost_currency_id.id if op.x_cost_currency_id else False,
            "x_cost": op.x_cost or 0,
        })
'''

# ── PDF Report: Biblia Operativa ──────────────────────────────────────────
# Full operational document for the tour team

BIBLIA_REPORT_KEY = 'agency_report_biblia_operativa'

BIBLIA_REPORT_TEMPLATE = '''<?xml version="1.0"?>
<t t-name="agency_report_biblia_operativa">
    <t t-call="web.html_container">
        <t t-foreach="docs" t-as="doc">
            <t t-call="web.external_layout">
                <div class="page">
                    <div class="text-center mb-4">
                        <h2 style="color: #1a5276; font-weight: bold; letter-spacing: 2px;">BIBLIA OPERATIVA</h2>
                        <h3><span t-field="doc.name"/> — <span t-field="doc.partner_id"/></h3>
                    </div>

                    <div class="row mb-4" style="border: 1px solid #adb5bd; border-radius: 4px; padding: 15px; background-color: #f8f9fa;">
                        <div class="col-6">
                            <p class="mb-1"><strong>Contacto Principal:</strong> <span t-field="doc.partner_id"/></p>
                            <p class="mb-1"><strong>Tipo de Servicio:</strong> <span t-field="doc.x_service_type"/></p>
                            <p class="mb-1"><strong>Lugar de Partida:</strong> <span t-field="doc.x_departure_city"/></p>
                        </div>
                        <div class="col-6">
                            <p class="mb-1"><strong>Fecha Inicio:</strong> <span t-field="doc.x_tour_start_date"/></p>
                            <p class="mb-1"><strong>Fecha Fin:</strong> <span t-field="doc.x_tour_end_date"/></p>
                            <p class="mb-1"><strong>Nro. Pasajeros:</strong> <span t-field="doc.x_num_passengers"/></p>
                        </div>
                    </div>

                    <t t-if="doc.x_itinerary_line_ids">
                        <h4 style="color: #1a5276; border-bottom: 2px solid #1a5276; padding-bottom: 4px;">Itinerario</h4>
                        <table class="table table-sm table-bordered mt-2">
                            <thead>
                                <tr style="background-color: #1a5276 !important; color: white !important; -webkit-print-color-adjust: exact;">
                                    <th style="width: 6%; background-color: #1a5276; color: white;">Dia</th>
                                    <th style="width: 18%; background-color: #1a5276; color: white;">Titulo</th>
                                    <th style="width: 36%; background-color: #1a5276; color: white;">Descripcion</th>
                                    <th style="width: 20%; background-color: #1a5276; color: white;">Alojamiento</th>
                                    <th style="width: 20%; background-color: #1a5276; color: white;">Comidas</th>
                                </tr>
                            </thead>
                            <tbody>
                                <t t-foreach="doc.x_itinerary_line_ids" t-as="line">
                                    <tr>
                                        <td class="text-center"><span t-field="line.x_day_number"/></td>
                                        <td><strong><span t-field="line.x_title"/></strong></td>
                                        <td><span t-field="line.x_description"/></td>
                                        <td><span t-field="line.x_accommodation"/></td>
                                        <td><span t-field="line.x_meals"/></td>
                                    </tr>
                                </t>
                            </tbody>
                        </table>
                    </t>

                    <t t-if="doc.x_guest_line_ids">
                        <h4 style="color: #1a5276; border-bottom: 2px solid #1a5276; padding-bottom: 4px;">Pasajeros</h4>
                        <table class="table table-sm table-bordered mt-2">
                            <thead>
                                <tr style="background-color: #1a5276 !important; -webkit-print-color-adjust: exact;">
                                    <th style="background-color: #1a5276; color: white;">Nombre</th>
                                    <th style="background-color: #1a5276; color: white;">Nacionalidad</th>
                                    <th style="background-color: #1a5276; color: white;">Nro. Doc.</th>
                                    <th style="background-color: #1a5276; color: white;">Telefono</th>
                                    <th style="background-color: #1a5276; color: white;">Restricciones Medicas</th>
                                    <th style="background-color: #1a5276; color: white;">Emergencia</th>
                                </tr>
                            </thead>
                            <tbody>
                                <t t-foreach="doc.x_guest_line_ids" t-as="guest">
                                    <tr>
                                        <td><span t-field="guest.x_guest_partner_id"/></td>
                                        <td><span t-field="guest.x_nationality_id"/></td>
                                        <td><span t-field="guest.x_document_number_rel"/></td>
                                        <td><span t-field="guest.x_phone_rel"/></td>
                                        <td><t t-if="guest.x_medical_rel and guest.x_medical_rel != 'None'"><span t-field="guest.x_medical_rel"/></t><t t-else="">-</t></td>
                                        <td>
                                            <t t-if="guest.x_emergency_name_rel">
                                                <span t-field="guest.x_emergency_name_rel"/>
                                                <t t-if="guest.x_emergency_phone_rel">
                                                    <br/><small><span t-field="guest.x_emergency_phone_rel"/></small>
                                                </t>
                                            </t>
                                        </td>
                                    </tr>
                                </t>
                            </tbody>
                        </table>
                    </t>

                    <t t-if="doc.x_operator_line_ids">
                        <h4 style="color: #1a5276; border-bottom: 2px solid #1a5276; padding-bottom: 4px;">Operadores Asignados</h4>
                        <table class="table table-sm table-bordered mt-2">
                            <thead>
                                <tr style="background-color: #1a5276 !important; -webkit-print-color-adjust: exact;">
                                    <th style="background-color: #1a5276; color: white;">Operador</th>
                                    <th style="background-color: #1a5276; color: white;">Tipo de Servicio</th>
                                    <th style="background-color: #1a5276; color: white;">Descripcion</th>
                                    <th style="background-color: #1a5276; color: white;">Fecha</th>
                                    <th style="background-color: #1a5276; color: white;">Telefono</th>
                                    <th style="background-color: #1a5276; color: white;">Email</th>
                                </tr>
                            </thead>
                            <tbody>
                                <t t-foreach="doc.x_operator_line_ids" t-as="op">
                                    <tr>
                                        <td><span t-field="op.x_partner_id"/></td>
                                        <td><span t-field="op.x_service_type"/></td>
                                        <td><t t-if="op.x_description"><span t-field="op.x_description"/></t><t t-else="">-</t></td>
                                        <td><t t-if="op.x_date"><span t-field="op.x_date"/></t><t t-else="">-</t></td>
                                        <td><span t-field="op.x_phone_rel"/></td>
                                        <td><span t-field="op.x_email_rel"/></td>
                                    </tr>
                                </t>
                            </tbody>
                        </table>
                    </t>

                    <t t-if="doc.x_inclusions">
                        <h4 style="color: #1a5276; border-bottom: 2px solid #1a5276; padding-bottom: 4px;">Servicios Incluidos</h4>
                        <div t-field="doc.x_inclusions" class="mt-2"/>
                    </t>

                    <t t-if="doc.x_key_times">
                        <h4 style="color: #1a5276; border-bottom: 2px solid #1a5276; padding-bottom: 4px;">Horarios Clave</h4>
                        <p style="white-space: pre-wrap;" t-field="doc.x_key_times" class="mt-2"/>
                    </t>

                    <t t-if="doc.x_special_observations">
                        <h4 style="color: #1a5276; border-bottom: 2px solid #1a5276; padding-bottom: 4px;">Observaciones Especiales</h4>
                        <p style="white-space: pre-wrap;" t-field="doc.x_special_observations" class="mt-2"/>
                    </t>
                </div>
            </t>
        </t>
    </t>
</t>'''

# ── PDF Report: Voucher Pasajero ──────────────────────────────────────────
# One page per passenger with their tour details

VOUCHER_REPORT_KEY = 'agency_report_voucher_pasajero'

# ── Ecommerce: Tour detection conditions ─────────────────────────────────
# Single source of truth: x_is_tour boolean on product.template.
_IS_TOUR = "product.x_is_tour"
_NOT_TOUR = "not product.x_is_tour"

# ── Ecommerce: Hide add-to-cart + show "Request Quote" for tours ─────────
# Inherits from website_sale.cta_wrapper (product detail CTA buttons)
# Base language: English. Spanish translations applied separately via update_field_translations.

ECOM_CTA_TOUR_ARCH = '''<data>
    <xpath expr="//div[@id='add_to_cart_wrap']" position="attributes">
        <attribute name="t-if">__NOT_TOUR__</attribute>
    </xpath>
    <xpath expr="//div[@id='add_to_cart_wrap']" position="after">
        <div t-if="__IS_TOUR__"
             id="request_quote_wrap" class="flex-grow-1">
            <button type="button" class="btn btn-primary w-100"
                    data-bs-toggle="modal" data-bs-target="#tourQuoteModal">
                <i class="fa fa-envelope me-2"/>Request Quote
            </button>
        </div>
    </xpath>
</data>'''.replace('__IS_TOUR__', _IS_TOUR).replace('__NOT_TOUR__', _NOT_TOUR)

# ── Ecommerce: Modal form on product page → creates crm.lead ─────────────
# Inherits from website_sale.product (product detail page)

ECOM_PRODUCT_MODAL_ARCH = '''<data>
    <!-- 1. Remove js_product class for tours — prevents JS configurator hooks -->
    <xpath expr="//div[@id='o_wsale_product_details_content']" position="attributes">
        <attribute name="t-attf-class">
            {{ 'js_product' if __NOT_TOUR__ else '' }} o_wsale_content_contained container
        </attribute>
    </xpath>
    <!-- 2. Hide variant selector section for tours — prevents ProductPage JS from
         finding UL elements and calling get_combination_info_website RPC.
         Attributes still appear in specifications/accordion tab below. -->
    <xpath expr="//t[@name='variant_info']" position="attributes">
        <attribute name="t-if">__NOT_TOUR__</attribute>
    </xpath>
    <!-- Modal with CRM lead form -->
    <xpath expr="//section[@id='product_detail']" position="after">
        <t t-if="__IS_TOUR__">
            <div class="modal fade" id="tourQuoteModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header" style="background-color: #1a5276; color: white;">
                            <h5 class="modal-title">Request Quote</h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"/>
                        </div>
                        <form action="/website/form/" method="post"
                              class="s_website_form"
                              data-model_name="crm.lead"
                              data-success-mode="redirect"
                              t-att-data-success-page="product.website_url + '?quote_sent=1'">
                            <input type="hidden" name="csrf_token" t-att-value="request.csrf_token()"/>
                            <input type="hidden" name="name" t-attf-value="Web Quote: #{product.name}"/>
                            <div class="modal-body">
                                <p class="text-muted mb-3">
                                    Tour: <strong t-field="product.name"/>
                                </p>
                                <div class="s_website_form_rows">
                                    <div class="mb-3 s_website_form_field">
                                        <label class="form-label">Full name *</label>
                                        <input type="text" class="form-control s_website_form_input"
                                               name="contact_name" required="1"/>
                                    </div>
                                    <div class="mb-3 s_website_form_field">
                                        <label class="form-label">Email *</label>
                                        <input type="email" class="form-control s_website_form_input"
                                               name="email_from" required="1"/>
                                    </div>
                                    <div class="mb-3 s_website_form_field">
                                        <label class="form-label">Phone</label>
                                        <input type="tel" class="form-control s_website_form_input"
                                               name="phone"/>
                                    </div>
                                    <div class="mb-3 s_website_form_field">
                                        <label class="form-label">Tell us about your trip (dates, passengers, preferences)</label>
                                        <textarea class="form-control s_website_form_input"
                                                  name="description" rows="4"
                                                  placeholder="E.g.: 2 adults traveling April 15-20, we prefer private service..."/>
                                    </div>
                                </div>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                                <button type="submit" class="btn btn-primary s_website_form_send">
                                    <i class="fa fa-paper-plane me-1"/>Send Request
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
            <!-- Success overlay: shown when redirected back after form submission -->
            <t t-if="request.httprequest.args.get('quote_sent')">
                <div class="modal show" tabindex="-1"
                     style="display:block; position:fixed; z-index:1055;">
                    <div class="modal-dialog modal-dialog-centered">
                        <div class="modal-content">
                            <div class="modal-header" style="background-color: #1a5276; color: white;">
                                <h5 class="modal-title">Request Sent</h5>
                            </div>
                            <div class="modal-body text-center py-4">
                                <i class="fa fa-check-circle text-success" style="font-size:3em;"></i>
                                <h5 class="mt-3">Your request has been sent!</h5>
                                <p class="text-muted">We will contact you shortly by email or WhatsApp.</p>
                            </div>
                            <div class="modal-footer justify-content-center">
                                <a t-att-href="product.website_url" class="btn btn-primary">Close</a>
                            </div>
                        </div>
                    </div>
                </div>
                <div style="position:fixed; top:0; left:0; width:100vw; height:100vh; background:rgba(0,0,0,0.5); z-index:1050;"></div>
            </t>
        </t>
    </xpath>
</data>'''.replace('__IS_TOUR__', _IS_TOUR).replace('__NOT_TOUR__', _NOT_TOUR)

# ── Ecommerce: Replace listing button for tours ──────────────────────────
# Inherits from website_sale.shop_product_buttons (product grid/list buttons)

ECOM_LISTING_TOUR_ARCH = '''<data>
    <!-- Hide original add-to-cart button for tours -->
    <xpath expr="//button[@name='add_to_cart']" position="attributes">
        <attribute name="t-if">__NOT_TOUR__</attribute>
    </xpath>
    <!-- Add quote button for tours -->
    <xpath expr="//div[hasclass('o_wsale_product_action_row')]" position="inside">
        <a t-if="__IS_TOUR__"
           t-attf-href="/shop/#{slug(product)}"
           class="o_wsale_product_btn_primary btn btn-primary"
           title="Request Quote">
            <i class="fa fa-fw fa-envelope o_not-animable"/>
            <span class="o_label small ms-1">Quote</span>
        </a>
    </xpath>
</data>'''.replace('__IS_TOUR__', _IS_TOUR).replace('__NOT_TOUR__', _NOT_TOUR)

# ── Ecommerce: Hide add-to-cart in wishlist for tours ────────────────────
# Inherits from website_sale_wishlist.product_wishlist (wishlist product cards)
# The original has a t-if/t-else chain (Contact Us + Add to Cart) so we hide
# the entire action row via CSS and add our own quote link.

ECOM_WISHLIST_TOUR_ARCH = '''<data>
    <!-- Hide original action row for tours (includes Contact Us + Add to Cart) -->
    <xpath expr="//div[hasclass('o_wsale_product_action_row')]" position="attributes">
        <attribute name="t-att-style">'display:none' if (__IS_TOUR__) else ''</attribute>
    </xpath>
    <!-- Add tour quote link after hidden row -->
    <xpath expr="//div[hasclass('o_wsale_product_action_row')]" position="after">
        <div t-if="__IS_TOUR__" class="o_wsale_product_action_row">
            <a t-att-href="product.website_url"
               class="o_wsale_product_btn_primary btn btn-primary"
               title="Request Quote">
                <i class="fa fa-fw fa-envelope o_not-animable"/>
                <span class="o_label small ms-1">Quote</span>
            </a>
        </div>
    </xpath>
</data>'''.replace('__IS_TOUR__', _IS_TOUR).replace('__NOT_TOUR__', _NOT_TOUR)

# ── Ecommerce: Hide add-to-cart in dynamic catalog snippets for tours ────
# Inherits from website_sale.dynamic_filter_template_product_product_products_item
# Used by the "Dynamic Products" website building block / snippet.

ECOM_DYNAMIC_SNIPPET_TOUR_ARCH = '''<data>
    <!-- Hide original action row for tours -->
    <xpath expr="//div[hasclass('o_wsale_product_action_row')]" position="attributes">
        <attribute name="t-att-style">'display:none' if (__IS_TOUR__) else ''</attribute>
    </xpath>
    <!-- Add tour quote link after hidden row -->
    <xpath expr="//div[hasclass('o_wsale_product_action_row')]" position="after">
        <div t-if="__IS_TOUR__" class="o_wsale_product_action_row">
            <a t-att-href="product.website_url"
               class="o_wsale_product_btn_primary btn btn-primary"
               title="Request Quote">
                <i class="fa fa-fw fa-envelope o_not-animable"/>
                <span class="o_label small ms-1">Quote</span>
            </a>
        </div>
    </xpath>
</data>'''.replace('__IS_TOUR__', _IS_TOUR).replace('__NOT_TOUR__', _NOT_TOUR)

# ── Ecommerce: "from" price prefix for tours ─────────────────────────────
# Each price context has its own template, so we need separate inherited views.

# Product detail page: website_sale.product_price (oe_price span)
ECOM_PRICE_PREFIX_TOUR_ARCH = '''<data>
    <xpath expr="//span[hasclass('oe_price')]" position="before">
        <small t-if="__IS_TOUR__" class="text-muted me-1">from</small>
    </xpath>
</data>'''.replace('__IS_TOUR__', _IS_TOUR).replace('__NOT_TOUR__', _NOT_TOUR)

# Shop listing cards: website_sale.products_item (product_price div > span.fw-bold)
ECOM_PRICE_PREFIX_LISTING_ARCH = '''<data>
    <xpath expr="//div[hasclass('product_price')]/span[hasclass('fw-bold')]" position="before">
        <small t-if="__IS_TOUR__" class="text-muted me-1">from</small>
    </xpath>
</data>'''.replace('__IS_TOUR__', _IS_TOUR).replace('__NOT_TOUR__', _NOT_TOUR)

# Wishlist cards: website_sale_wishlist.product_wishlist (o_wish_price div > span)
ECOM_PRICE_PREFIX_WISHLIST_ARCH = '''<data>
    <xpath expr="//div[hasclass('o_wish_price')]/span" position="before">
        <small t-if="__IS_TOUR__" class="text-muted me-1">from</small>
    </xpath>
</data>'''.replace('__IS_TOUR__', _IS_TOUR).replace('__NOT_TOUR__', _NOT_TOUR)

# Dynamic snippet cards: website_sale.price_dynamic_filter_template_product_product
ECOM_PRICE_PREFIX_DYNAMIC_ARCH = '''<data>
    <xpath expr="//span[@name='product_price']" position="before">
        <small t-if="__IS_TOUR__" class="text-muted me-1">from</small>
    </xpath>
</data>'''.replace('__IS_TOUR__', _IS_TOUR).replace('__NOT_TOUR__', _NOT_TOUR)

# ── Ecommerce: Extended description section for tours ────────────────────
# Renders x_extended_description (html field) below the main product section
# and ABOVE the specifications/accordion section. Only shown for tour products.
# Inherits from website_sale.product (product detail page).

ECOM_EXTENDED_DESC_ARCH = '''<data>
    <xpath expr="//section[@id='product_detail']" position="after">
        <section t-if="(__IS_TOUR__) and product.x_extended_description"
                 class="container py-4" id="tour_extended_description">
            <div t-field="product.x_extended_description"
                 class="o_wsale_extended_description"/>
        </section>
    </xpath>
</data>'''.replace('__IS_TOUR__', _IS_TOUR).replace('__NOT_TOUR__', _NOT_TOUR)

# ── Backend Form: Add x_extended_description to product.template ecommerce tab ──
# Inherits from the website_sale product form view that contains description_ecommerce.
# Places the new field below the existing "Descripcion Larga" field.

PRODUCT_EXTENDED_DESC_FORM_ARCH = '''<data>
    <xpath expr="//group[@name='ecom_description']" position="after">
        <group string="Extended Description" name="ecom_extended_description">
            <field colspan="2" name="x_extended_description" nolabel="1"
                   placeholder="Detailed tour content (itinerary, includes, conditions, etc.)"/>
        </group>
    </xpath>
</data>'''

# ── Backend Form: product.template General Info — x_is_tour checkbox ─────
# Inherits from the product.template form to add Is a Tour in General Info.

PRODUCT_IS_TOUR_FORM_ARCH = '''<data>
    <xpath expr="//field[@name='type']" position="after">
        <field name="x_is_tour"/>
    </xpath>
</data>'''

# ── Backend Form: product.template ecommerce tab — Tour sections ─────────
# All tour-specific fields in the ecommerce tab, visible only when x_is_tour.
# Placed AFTER ecom_extended_description group.

PRODUCT_TOUR_FIELDS_FORM_ARCH = '''<data>
    <xpath expr="//group[@name='ecom_extended_description']" position="after">
        <group string="Tour Details" invisible="not x_is_tour" name="tour_details">
            <field colspan="2" name="x_tour_details" nolabel="1"
                   placeholder="General tour description and highlights..."/>
        </group>
        <group string="Departure &amp; Return" invisible="not x_is_tour" name="tour_departure">
            <group>
                <field name="x_tour_departure_location"/>
                <field name="x_tour_departure_time"/>
            </group>
            <group>
                <field name="x_tour_return_location"/>
                <field name="x_tour_return_time"/>
            </group>
        </group>
        <group string="Includes" invisible="not x_is_tour" name="tour_includes">
            <field colspan="2" name="x_tour_includes_ids" nolabel="1">
                <list editable="bottom">
                    <field name="x_sequence" widget="handle"/>
                    <field name="x_name"/>
                </list>
            </field>
        </group>
        <group string="Does NOT Include" invisible="not x_is_tour" name="tour_excludes">
            <field colspan="2" name="x_tour_excludes_ids" nolabel="1">
                <list editable="bottom">
                    <field name="x_sequence" widget="handle"/>
                    <field name="x_name"/>
                </list>
            </field>
        </group>
        <group string="Recommendations" invisible="not x_is_tour" name="tour_recommendations">
            <field colspan="2" name="x_tour_recommendations_ids" nolabel="1">
                <list editable="bottom">
                    <field name="x_sequence" widget="handle"/>
                    <field name="x_name"/>
                </list>
            </field>
        </group>
        <group string="Itinerary" invisible="not x_is_tour" name="tour_itinerary">
            <field colspan="2" name="x_tour_itinerary" nolabel="1"
                   placeholder="Day-by-day itinerary..."/>
        </group>
        <group string="Departures" invisible="not x_is_tour" name="tour_schedule">
            <field colspan="2" name="x_tour_schedule" nolabel="1"
                   placeholder="Departure schedule and frequency..."/>
        </group>
        <group string="Conditions" invisible="not x_is_tour" name="tour_conditions">
            <field colspan="2" name="x_tour_conditions" nolabel="1"
                   placeholder="Terms and conditions..."/>
        </group>
        <group string="Booking Considerations" invisible="not x_is_tour" name="tour_booking">
            <field colspan="2" name="x_tour_booking_notes" nolabel="1"
                   placeholder="Payment, cancellation policy..."/>
        </group>
        <group string="Pricing" invisible="not x_is_tour" name="tour_pricing">
            <field colspan="2" name="x_tour_pricing_notes" nolabel="1"
                   placeholder="Price details, exceptions, group rates..."/>
        </group>
    </xpath>
</data>'''

# ── Ecommerce: Tour structured sections (website product page) ───────────
# Renders structured tour data below #product_detail.
# Replaces the old single x_extended_description blob with individual sections.
# Each section only renders if the corresponding field has content.
# Inherits from website_sale.product (product detail page).

ECOM_TOUR_SECTIONS_ARCH = '''<data>
    <xpath expr="//section[@id='product_detail']" position="after">
        <t t-if="__IS_TOUR__">
            <!-- Compute tab visibility -->
            <t t-set="_has_details" t-value="product.x_tour_details or product.x_tour_departure_location or product.x_tour_return_location or product.x_tour_departure_time or product.x_tour_return_time or product.x_tour_includes_ids or product.x_tour_excludes_ids"/>
            <t t-set="_has_itinerary" t-value="product.x_tour_itinerary or product.x_tour_schedule"/>
            <t t-set="_has_conditions" t-value="product.x_tour_conditions or product.x_tour_booking_notes or product.x_tour_recommendations_ids"/>
            <t t-set="_has_pricing" t-value="product.x_tour_pricing_notes"/>
            <t t-set="_any_tab" t-value="_has_details or _has_itinerary or _has_conditions or _has_pricing"/>
            <t t-set="_first" t-value="'details' if _has_details else ('itinerary' if _has_itinerary else ('conditions' if _has_conditions else 'pricing'))"/>

            <section t-if="_any_tab" class="container py-4" id="tour_tabs_section">
                <ul class="nav nav-tabs" id="tourTabs" role="tablist">
                    <li t-if="_has_details" class="nav-item" role="presentation">
                        <a t-att-class="'nav-link' + (' active' if _first == 'details' else '')"
                           data-bs-toggle="tab" href="#tourDetails" role="tab">Details</a>
                    </li>
                    <li t-if="_has_itinerary" class="nav-item" role="presentation">
                        <a t-att-class="'nav-link' + (' active' if _first == 'itinerary' else '')"
                           data-bs-toggle="tab" href="#tourItinerary" role="tab">Itinerary</a>
                    </li>
                    <li t-if="_has_conditions" class="nav-item" role="presentation">
                        <a t-att-class="'nav-link' + (' active' if _first == 'conditions' else '')"
                           data-bs-toggle="tab" href="#tourConditions" role="tab">Conditions</a>
                    </li>
                    <li t-if="_has_pricing" class="nav-item" role="presentation">
                        <a t-att-class="'nav-link' + (' active' if _first == 'pricing' else '')"
                           data-bs-toggle="tab" href="#tourPricing" role="tab">Pricing</a>
                    </li>
                </ul>
                <div class="tab-content pt-3" id="tourTabsContent">
                    <!-- Tab 1: Details -->
                    <div t-if="_has_details"
                         t-att-class="'tab-pane fade' + (' show active' if _first == 'details' else '')"
                         id="tourDetails" role="tabpanel">
                        <div t-if="product.x_tour_details" t-field="product.x_tour_details" class="mb-3"/>
                        <!-- Departure &amp; Return grid -->
                        <t t-set="_has_departure" t-value="product.x_tour_departure_location or product.x_tour_return_location or product.x_tour_departure_time or product.x_tour_return_time"/>
                        <div t-if="_has_departure" class="row mb-3">
                            <div class="col-md-6">
                                <t t-if="product.x_tour_departure_location">
                                    <p><strong>Departure Location:</strong> <span t-field="product.x_tour_departure_location"/></p>
                                </t>
                                <t t-if="product.x_tour_departure_time">
                                    <p><strong>Departure Time:</strong> <span t-field="product.x_tour_departure_time"/></p>
                                </t>
                            </div>
                            <div class="col-md-6">
                                <t t-if="product.x_tour_return_location">
                                    <p><strong>Return Location:</strong> <span t-field="product.x_tour_return_location"/></p>
                                </t>
                                <t t-if="product.x_tour_return_time">
                                    <p><strong>Return Time:</strong> <span t-field="product.x_tour_return_time"/></p>
                                </t>
                            </div>
                        </div>
                        <!-- Includes -->
                        <div t-if="product.x_tour_includes_ids" class="mb-3">
                            <h5 style="color: #1a5276;">What's Included</h5>
                            <ul class="list-unstyled">
                                <t t-foreach="product.x_tour_includes_ids" t-as="item">
                                    <li class="mb-1"><i class="fa fa-check text-success me-2"/><span t-field="item.x_name"/></li>
                                </t>
                            </ul>
                        </div>
                        <!-- Excludes -->
                        <div t-if="product.x_tour_excludes_ids" class="mb-3">
                            <h5 style="color: #1a5276;">What's NOT Included</h5>
                            <ul class="list-unstyled">
                                <t t-foreach="product.x_tour_excludes_ids" t-as="item">
                                    <li class="mb-1"><i class="fa fa-times text-danger me-2"/><span t-field="item.x_name"/></li>
                                </t>
                            </ul>
                        </div>
                    </div>
                    <!-- Tab 2: Itinerary -->
                    <div t-if="_has_itinerary"
                         t-att-class="'tab-pane fade' + (' show active' if _first == 'itinerary' else '')"
                         id="tourItinerary" role="tabpanel">
                        <div t-if="product.x_tour_itinerary" t-field="product.x_tour_itinerary" class="mb-3"/>
                        <div t-if="product.x_tour_schedule" class="mb-3">
                            <h5 style="color: #1a5276;">Departures</h5>
                            <div t-field="product.x_tour_schedule"/>
                        </div>
                    </div>
                    <!-- Tab 3: Conditions -->
                    <div t-if="_has_conditions"
                         t-att-class="'tab-pane fade' + (' show active' if _first == 'conditions' else '')"
                         id="tourConditions" role="tabpanel">
                        <div t-if="product.x_tour_conditions" class="mb-3">
                            <h5 style="color: #1a5276;">Conditions</h5>
                            <div t-field="product.x_tour_conditions"/>
                        </div>
                        <div t-if="product.x_tour_booking_notes" class="mb-3">
                            <h5 style="color: #1a5276;">Booking Considerations</h5>
                            <div t-field="product.x_tour_booking_notes"/>
                        </div>
                        <div t-if="product.x_tour_recommendations_ids" class="mb-3">
                            <h5 style="color: #1a5276;">Recommendations</h5>
                            <ul class="list-unstyled">
                                <t t-foreach="product.x_tour_recommendations_ids" t-as="item">
                                    <li class="mb-1"><i class="fa fa-info-circle text-primary me-2"/><span t-field="item.x_name"/></li>
                                </t>
                            </ul>
                        </div>
                    </div>
                    <!-- Tab 4: Pricing -->
                    <div t-if="_has_pricing"
                         t-att-class="'tab-pane fade' + (' show active' if _first == 'pricing' else '')"
                         id="tourPricing" role="tabpanel">
                        <div t-field="product.x_tour_pricing_notes"/>
                    </div>
                </div>
            </section>
        </t>
    </xpath>
</data>'''.replace('__IS_TOUR__', _IS_TOUR).replace('__NOT_TOUR__', _NOT_TOUR)


# ── Ecommerce i18n: English → Spanish translation mapping ────────────────
# Used by setup_ecommerce.py to write es_419 translations after the base arch.
# Order: longest strings first to avoid partial matches during replacement.

ECOM_TRANSLATIONS_ES = [
    # ── Button/modal translations (CTA, modal, listing, wishlist, dynamic views) ──
    ('<i class="fa fa-envelope me-2"/>Request Quote',
     '<i class="fa fa-envelope me-2"/>Solicitar Cotización'),
    ('<i class="fa fa-paper-plane me-1"/>Send Request',
     '<i class="fa fa-paper-plane me-1"/>Enviar Solicitud'),
    # Listing view (12-space indent)
    ('<i class="fa fa-fw fa-envelope o_not-animable"/>\n            <span class="o_label small ms-1">Quote</span>',
     '<i class="fa fa-fw fa-envelope o_not-animable"/>\n            <span class="o_label small ms-1">Cotizar</span>'),
    # Wishlist + dynamic snippet views (16-space indent)
    ('<i class="fa fa-fw fa-envelope o_not-animable"/>\n                <span class="o_label small ms-1">Quote</span>',
     '<i class="fa fa-fw fa-envelope o_not-animable"/>\n                <span class="o_label small ms-1">Cotizar</span>'),
    # Plain text terms
    ('Tell us about your trip (dates, passengers, preferences)',
     'Cuéntanos sobre tu viaje (fechas, pasajeros, preferencias)'),
    ('E.g.: 2 adults traveling April 15-20, we prefer private service...',
     'Ej: Viajamos 2 adultos del 15 al 20 de abril, preferimos servicio privado...'),
    ('Your request has been sent!', '¡Se envió tu solicitud!'),
    ('We will contact you shortly by email or WhatsApp.',
     'Nos comunicaremos con usted en breve por correo o por WhatsApp.'),
    ('Request Sent', 'Solicitud Enviada'),
    ('Request Quote', 'Solicitar Cotización'),
    ('Full name *', 'Nombre completo *'),
    ('Cancel', 'Cancelar'),
    ('Phone', 'Teléfono'),
    ('Close', 'Cerrar'),
    ('from', 'desde'),
    # ── Tour tab labels ──
    ('Details', 'Detalles'),
    ('Itinerary', 'Itinerario'),
    ('Conditions', 'Condiciones'),
    ('Pricing', 'Precios'),
    # ── Departure/return labels within Details tab ──
    # Source terms include <strong> tags (QWeb inline extraction)
    ('<strong>Departure Location:</strong>', '<strong>Lugar de Salida:</strong>'),
    ('<strong>Departure Time:</strong>', '<strong>Hora de Salida:</strong>'),
    ('<strong>Return Location:</strong>', '<strong>Lugar de Retorno:</strong>'),
    ('<strong>Return Time:</strong>', '<strong>Hora de Retorno:</strong>'),
    # ── Sub-headings and icons within tabs ──
    ("<i class=\"fa fa-check text-success me-2\"/>", "<i class=\"fa fa-check text-success me-2\"/>"),
    ("<i class=\"fa fa-times text-danger me-2\"/>", "<i class=\"fa fa-times text-danger me-2\"/>"),
    ("<i class=\"fa fa-info-circle text-primary me-2\"/>", "<i class=\"fa fa-info-circle text-primary me-2\"/>"),
    ("What's Included", '¿Qué incluye?'),
    ("What's NOT Included", '¿Qué NO incluye?'),
    ('Recommendations', 'Recomendaciones'),
    ('Departures', 'Salidas'),
    ('Booking Considerations', 'Consideraciones de Reserva'),
]


# ── Tour Group: Form + List views ────────────────────────────────────────

TOUR_GROUP_FORM_ARCH = '''<form>
    <sheet>
        <div class="oe_title">
            <h1><field name="x_name" placeholder="Nombre del grupo..."/></h1>
        </div>
        <group>
            <group>
                <field name="x_start_date"/>
                <field name="x_end_date"/>
                <field name="x_max_capacity"/>
            </group>
            <group>
                <field name="x_color" widget="color_picker"/>
            </group>
        </group>
        <separator string="Pasajeros"/>
        <field name="x_passenger_ids" widget="many2many_tags"
               options="{'no_create': True, 'color_field': 'color'}"/>
        <separator string="Notas Operativas"/>
        <field name="x_notes" placeholder="Notas operativas del grupo..."/>
        <notebook>
            <page string="Ventas Vinculadas" name="linked_sales">
                <field name="x_sale_order_ids" readonly="1">
                    <list>
                        <field name="name" string="Pedido"/>
                        <field name="partner_id" string="Cliente"/>
                        <field name="x_tour_start_date" string="Fecha Inicio"/>
                        <field name="x_tour_end_date" string="Fecha Fin"/>
                        <field name="state" string="Estado" widget="badge"
                            decoration-info="state == 'draft'"
                            decoration-warning="state == 'sent'"
                            decoration-success="state == 'sale'"/>
                    </list>
                </field>
            </page>
            <page string="Tareas de Flota" name="linked_tasks">
                <field name="x_task_ids" readonly="1">
                    <list>
                        <field name="name" string="Tarea"/>
                        <field name="sale_order_id" string="Pedido"/>
                        <field name="x_vehicle_id" string="Vehiculo"/>
                        <field name="x_driver_id" string="Chofer"/>
                        <field name="x_seats_needed" string="Asientos"/>
                        <field name="stage_id" string="Etapa"/>
                    </list>
                </field>
            </page>
        </notebook>
    </sheet>
</form>'''

TOUR_GROUP_LIST_ARCH = '''<list>
    <field name="x_name"/>
    <field name="x_start_date"/>
    <field name="x_end_date"/>
    <field name="x_max_capacity"/>
</list>'''


VOUCHER_REPORT_TEMPLATE = '''<?xml version="1.0"?>
<t t-name="agency_report_voucher_pasajero">
    <t t-call="web.html_container">
        <t t-foreach="docs" t-as="doc">
            <t t-foreach="doc.x_guest_line_ids" t-as="guest">
                <t t-call="web.external_layout">
                    <div class="page">
                        <div class="text-center mb-4">
                            <h2 style="color: #1a5276; font-weight: bold; letter-spacing: 2px;">VOUCHER DE VIAJE</h2>
                            <h3><span t-field="doc.name"/> — <span t-field="guest.x_guest_partner_id"/></h3>
                        </div>

                        <div style="border: 2px solid #1a5276; border-radius: 8px; padding: 16px; margin-bottom: 20px; background-color: #f8f9fa;">
                            <h4 style="color: #1a5276; margin-top: 0;">Datos del Pasajero</h4>
                            <div class="row">
                                <div class="col-6">
                                    <p class="mb-1"><strong>Nombre:</strong> <span t-field="guest.x_guest_partner_id"/></p>
                                    <p class="mb-1"><strong>Nacionalidad:</strong> <span t-field="guest.x_nationality_id"/></p>
                                    <p class="mb-1"><strong>Documento:</strong> <span t-field="guest.x_document_number_rel"/></p>
                                </div>
                                <div class="col-6">
                                    <p class="mb-1"><strong>Telefono:</strong> <span t-field="guest.x_phone_rel"/></p>
                                    <p class="mb-1"><strong>Email:</strong> <span t-field="guest.x_email_rel"/></p>
                                    <t t-if="guest.x_emergency_name_rel">
                                        <p class="mb-1"><strong>Emergencia:</strong>
                                            <span t-field="guest.x_emergency_name_rel"/>
                                            <t t-if="guest.x_emergency_phone_rel"> - <span t-field="guest.x_emergency_phone_rel"/></t>
                                        </p>
                                    </t>
                                </div>
                            </div>
                        </div>

                        <div class="row mb-3">
                            <div class="col-6">
                                <p class="mb-1"><strong>Fecha Inicio:</strong> <span t-field="doc.x_tour_start_date"/></p>
                                <p class="mb-1"><strong>Fecha Fin:</strong> <span t-field="doc.x_tour_end_date"/></p>
                            </div>
                            <div class="col-6">
                                <p class="mb-1"><strong>Tipo Servicio:</strong> <span t-field="doc.x_service_type"/></p>
                                <p class="mb-1"><strong>Lugar de Partida:</strong> <span t-field="doc.x_departure_city"/></p>
                            </div>
                        </div>

                        <t t-if="doc.x_itinerary_line_ids">
                            <h4 style="color: #1a5276; border-bottom: 2px solid #1a5276; padding-bottom: 4px;">Itinerario</h4>
                            <table class="table table-sm table-bordered mt-2">
                                <thead>
                                    <tr style="background-color: #1a5276 !important; -webkit-print-color-adjust: exact;">
                                        <th style="width: 6%; background-color: #1a5276; color: white;">Dia</th>
                                        <th style="width: 20%; background-color: #1a5276; color: white;">Titulo</th>
                                        <th style="width: 34%; background-color: #1a5276; color: white;">Descripcion</th>
                                        <th style="width: 20%; background-color: #1a5276; color: white;">Alojamiento</th>
                                        <th style="width: 20%; background-color: #1a5276; color: white;">Comidas</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <t t-foreach="doc.x_itinerary_line_ids" t-as="line">
                                        <tr>
                                            <td class="text-center"><span t-field="line.x_day_number"/></td>
                                            <td><strong><span t-field="line.x_title"/></strong></td>
                                            <td><span t-field="line.x_description"/></td>
                                            <td><span t-field="line.x_accommodation"/></td>
                                            <td><span t-field="line.x_meals"/></td>
                                        </tr>
                                    </t>
                                </tbody>
                            </table>
                        </t>

                        <t t-if="doc.x_inclusions">
                            <h4 style="color: #1a5276; border-bottom: 2px solid #1a5276; padding-bottom: 4px;">Servicios Incluidos</h4>
                            <div t-field="doc.x_inclusions" class="mt-2"/>
                        </t>

                        <t t-if="doc.x_key_times">
                            <h4 style="color: #1a5276; border-bottom: 2px solid #1a5276; padding-bottom: 4px;">Horarios Clave</h4>
                            <p style="white-space: pre-wrap;" t-field="doc.x_key_times" class="mt-2"/>
                        </t>

                        <t t-if="doc.x_operator_line_ids">
                            <h4 style="color: #1a5276; border-bottom: 2px solid #1a5276; padding-bottom: 4px;">Contactos Operativos</h4>
                            <table class="table table-sm table-bordered mt-2">
                                <thead>
                                    <tr style="background-color: #1a5276 !important; -webkit-print-color-adjust: exact;">
                                        <th style="background-color: #1a5276; color: white;">Servicio</th>
                                        <th style="background-color: #1a5276; color: white;">Descripcion</th>
                                        <th style="background-color: #1a5276; color: white;">Operador</th>
                                        <th style="background-color: #1a5276; color: white;">Telefono</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <t t-foreach="doc.x_operator_line_ids" t-as="op">
                                        <tr>
                                            <td><span t-field="op.x_service_type"/></td>
                                            <td><t t-if="op.x_description"><span t-field="op.x_description"/></t><t t-else="">-</t></td>
                                            <td><span t-field="op.x_partner_id"/></td>
                                            <td><span t-field="op.x_phone_rel"/></td>
                                        </tr>
                                    </t>
                                </tbody>
                            </table>
                        </t>

                        <t t-set="has_medical" t-value="guest.x_medical_rel and str(guest.x_medical_rel).strip() not in ('', 'None', 'False')"/>
                        <div t-if="has_medical" style="border: 2px solid #e74c3c; border-radius: 8px; padding: 12px; margin-top: 16px; background-color: #fdf2f2;">
                            <h5 style="color: #e74c3c; margin-top: 0;">Restricciones Medicas / Alimentarias</h5>
                            <p t-field="guest.x_medical_rel"/>
                        </div>
                        <div t-else="" style="border: 1px solid #adb5bd; border-radius: 8px; padding: 12px; margin-top: 16px; background-color: #f8f9fa;">
                            <h5 style="color: #6c757d; margin-top: 0;">Restricciones Medicas / Alimentarias</h5>
                            <p style="color: #6c757d; font-style: italic;">Sin restricciones registradas</p>
                        </div>
                    </div>
                </t>
            </t>
        </t>
    </t>
</t>'''
