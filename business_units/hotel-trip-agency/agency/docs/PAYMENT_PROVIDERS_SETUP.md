# Guía de Configuración: Pasarelas de Pago en Odoo 19

**Instancia**: `machupicchu-afdestiny-production.odoo.com`
**Empresa**: A & F DESTINY E.I.R.L
**Moneda base**: PEN (Sol peruano)
**Fecha**: Marzo 2026

---

## Estado Actual

| Proveedor | Módulo | Estado | Acción necesaria |
|-----------|--------|--------|-----------------|
| **Mercado Pago** | Instalado | Deshabilitado | Solo faltan credenciales |
| **Stripe** | Instalado | Deshabilitado | Solo faltan credenciales |
| **PayPal** | **NO instalado** | - | Instalar módulo + credenciales |

---

## 1. Mercado Pago (Recomendado para Perú)

### 1.1 En la plataforma de Mercado Pago

1. Ir a **https://www.mercadopago.com.pe/developers**
2. Iniciar sesión con la cuenta de A & F Destiny (o crear una cuenta Business)
3. Ir a **"Tus integraciones"** → **"Crear aplicación"**
4. Nombre de la aplicación: `AyF Destiny Odoo`
5. En **Credenciales de Producción**, copiar:
   - **Public Key** → empieza con `pk-prod-`
   - **Access Token** → empieza con `APP_USR-`

> **Nota**: Para probar primero sin cobrar de verdad, usar las **Credenciales de Prueba (Sandbox)** en lugar de las de Producción.

### 1.2 En Odoo

Ir a **Contabilidad → Configuración → Proveedores de Pago → Mercado Pago**

#### Opción A: Conexión automática (más fácil)

1. Seleccionar **País de la cuenta**: **Perú**
2. Clic en botón **"Conectar"**
3. Se abre ventana de Mercado Pago → autorizar acceso
4. Las credenciales se llenan automáticamente

#### Opción B: Configuración manual

1. Seleccionar **País de la cuenta**: **Perú**
2. Llenar **Access Token**: `APP_USR-xxxxx...`
3. Llenar **Public Key**: `pk-prod-xxxxx...`

#### Pasos finales (ambas opciones)

4. **Diario de pago**: seleccionar **"Banco"**
5. Cambiar estado a **"Habilitado"**
6. Marcar checkbox **"Publicado"** para que aparezca en el portal y ecommerce

### 1.3 Credenciales necesarias

| Campo en Odoo | De dónde sale | Formato |
|---------------|---------------|---------|
| País de la cuenta | Seleccionar Perú | `Peru` |
| Access Token | Mercado Pago → Tus integraciones → Credenciales | `APP_USR-1234567890abcdef...` |
| Public Key | Mercado Pago → Tus integraciones → Credenciales | `pk-prod-ABCDEF123456...` |

### 1.4 Webhook

No se necesita configurar webhook manualmente. Odoo envía la URL de notificación automáticamente en cada transacción.

### 1.5 Comisiones

| Tipo de transacción | Comisión |
|---------------------|----------|
| Nacional (tarjeta peruana) | ~3.49% + IVA |
| Internacional | ~4.49% + IVA |

---

## 2. Stripe

### 2.1 En la plataforma de Stripe

1. Ir a **https://dashboard.stripe.com** (crear cuenta si no existe)
2. Completar la **verificación del negocio** (datos de empresa, documentos de A & F Destiny)
3. Ir a **Developers → API Keys**, copiar:
   - **Publishable key** → empieza con `pk_live_`
   - **Secret key** → empieza con `sk_live_`

> **Para pruebas**: Usar las claves de test que empiezan con `pk_test_` y `sk_test_`

### 2.2 Webhook de Stripe

Hay dos formas de configurar el webhook:

#### Forma automática (recomendada)

Después de ingresar las API keys en Odoo, hacer clic en el botón **"Generar tu webhook"**. Odoo lo crea automáticamente en Stripe.

#### Forma manual

1. En Stripe ir a **Developers → Webhooks → Add endpoint**
2. URL del endpoint:
   ```
   https://machupicchu-afdestiny-production.odoo.com/payment/stripe/webhook
   ```
3. Seleccionar estos eventos:
   - `charge.refunded`
   - `charge.refund.updated`
   - `payment_intent.amount_capturable_updated`
   - `payment_intent.payment_failed`
   - `payment_intent.processing`
   - `payment_intent.succeeded`
   - `setup_intent.succeeded`
4. Copiar el **Signing secret** → empieza con `whsec_`

### 2.3 En Odoo

Ir a **Contabilidad → Configuración → Proveedores de Pago → Stripe**

#### Opción A: Odoo Connect (más fácil)

1. Clic en botón **"Conectar con Stripe"**
2. Completar el flujo de Stripe Connect
3. Todo se llena automáticamente

#### Opción B: Configuración manual

1. Llenar **Publishable Key**: `pk_live_xxxxx...`
2. Llenar **Secret Key**: `sk_live_xxxxx...`
3. Llenar **Webhook Secret**: `whsec_xxxxx...` (o usar botón "Generar tu webhook")

#### Pasos finales (ambas opciones)

4. **Diario de pago**: seleccionar **"Banco"**
5. Cambiar estado a **"Habilitado"**
6. Marcar checkbox **"Publicado"**

### 2.4 Credenciales necesarias

| Campo en Odoo | De dónde sale | Formato |
|---------------|---------------|---------|
| Publishable Key | Stripe → Developers → API Keys | `pk_live_51Abc...` |
| Secret Key | Stripe → Developers → API Keys | `sk_live_51Abc...` |
| Webhook Secret | Stripe → Developers → Webhooks (o auto-generado) | `whsec_abc123...` |

### 2.5 Comisiones

| Tipo de transacción | Comisión |
|---------------------|----------|
| Nacional | ~2.9% + $0.30 |
| Internacional | ~3.9% + $0.30 |

---

## 3. PayPal

### 3.1 Instalar el módulo primero

PayPal **no está instalado** en la instancia. Antes de configurar:

1. Ir a **Contabilidad → Configuración → Proveedores de Pago**
2. Buscar la tarjeta de **PayPal**
3. Clic en **"Instalar"**
4. Esperar a que se complete la instalación

### 3.2 En la plataforma de PayPal

1. Ir a **https://developer.paypal.com/dashboard/**
2. Iniciar sesión con cuenta **PayPal Business** de A & F Destiny
3. Ir a **Apps & Credentials → Create App**
4. Nombre: `AyF Destiny Odoo`
5. Copiar:
   - **Client ID**
   - **Secret**

> **Para pruebas**: Cambiar a modo **Sandbox** en el dashboard de PayPal y usar esas credenciales.

### 3.3 En Odoo

Ir a **Contabilidad → Configuración → Proveedores de Pago → PayPal**

1. Llenar **Email**: el email de la cuenta PayPal Business
2. Llenar **Client ID**
3. Llenar **Client Secret**
4. Clic en **"Generar tu webhook"** (crea el webhook automáticamente)
5. **Diario de pago**: seleccionar **"Banco"**
6. Cambiar estado a **"Habilitado"**
7. Marcar checkbox **"Publicado"**

### 3.4 Credenciales necesarias

| Campo en Odoo | De dónde sale | Formato |
|---------------|---------------|---------|
| Email | Email de la cuenta PayPal Business | `pagos@afdestiny.com` |
| Client ID | PayPal → Apps & Credentials | `AaBb123CcDd456...` |
| Client Secret | PayPal → Apps & Credentials | `EeFf456GgHh789...` |

### 3.5 Webhook

El webhook se genera automáticamente con el botón "Generar tu webhook" en Odoo. La URL es:
```
https://machupicchu-afdestiny-production.odoo.com/payment/paypal/webhook
```

### 3.6 Comisiones

| Tipo de transacción | Comisión |
|---------------------|----------|
| Nacional | ~3.49% + tarifa fija |
| Internacional | ~5.4% + tarifa fija |

---

## Configuración ya realizada

Los siguientes cambios ya fueron aplicados a la instancia de producción:

### Término de pago creado

- **"50% Anticipo, 50% antes del viaje"** (ID=12)
- 50% al confirmar la reserva, 50% restante a 30 días
- Disponible en **Contabilidad → Configuración → Plazos de Pago**

### Prepago online actualizado

- Los **29 templates de cotización** ahora tienen:
  - `require_payment = True` (pago online activado)
  - `prepayment_percent = 50%`
- El cliente en el portal solo necesita pagar el **50%** para confirmar la cotización

### En cada cotización nueva

1. En la pestaña principal, seleccionar **Término de pago**: "50% Anticipo, 50% antes del viaje"
2. En la pestaña **"Otra Información"** → sección "Ventas", verificar que aparezca:
   - ☑ Pago en línea — **50%**

---

## Flujo del Cliente (después de configurar la pasarela)

```
1. Agente crea cotización con template del tour
2. Cotización se envía al cliente por email/WhatsApp
3. Cliente abre el link del portal de Odoo
4. Ve el detalle del tour y botón "Firmar y Pagar"
5. Paga el 50% con tarjeta (Mercado Pago / Stripe / PayPal)
6. La orden de venta se confirma automáticamente
7. Agente factura el 50% inicial (anticipo)
8. Antes del viaje → agente factura el 50% restante
9. Cliente paga el restante por el mismo portal o transferencia
```

---

## Checklist Rápido

- [ ] **Mercado Pago**: ¿Tiene cuenta en mercadopago.com.pe? → Credenciales → Pegar en Odoo → Habilitar
- [ ] **Stripe**: ¿Tiene cuenta en stripe.com? → API Keys → Pegar en Odoo → Generar webhook → Habilitar
- [ ] **PayPal**: Instalar módulo en Odoo → ¿Tiene cuenta PayPal Business? → App credentials → Pegar en Odoo → Generar webhook → Habilitar
- [ ] Para **cada proveedor**: Asignar diario **"Banco"**, estado **"Habilitado"**, checkbox **"Publicado"**
- [ ] Probar con credenciales de **prueba/sandbox** antes de pasar a producción
- [ ] Verificar que el portal muestre las opciones de pago correctamente

---

## Notas Importantes

1. **Comisiones**: Las absorbe el comercio (A & F Destiny), no el cliente. El cliente paga el precio publicado. La diferencia aparece como gasto financiero al conciliar con el banco.

2. **Probar primero**: Configurar cada proveedor en modo **"Test"** antes de cambiar a **"Habilitado"** (producción). Usar credenciales de sandbox/prueba.

3. **Diario bancario**: Los tres proveedores deben usar el diario **"Banco"** para que los pagos se registren correctamente en contabilidad.

4. **Monedas**: Mercado Pago trabaja nativamente con PEN. Stripe y PayPal funcionan mejor con USD para clientes internacionales. Las listas de precios ya están configuradas para manejar PEN y USD.
