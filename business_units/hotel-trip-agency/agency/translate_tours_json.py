#!/usr/bin/env python3
"""Add English translations (_en fields) to wordpress_tours.json.

Reads the existing JSON, adds *_en fields for all translatable content,
and writes back the updated JSON.

Usage:
    uv run python business_units/hotel-trip-agency/agency/translate_tours_json.py
    uv run python business_units/hotel-trip-agency/agency/translate_tours_json.py --dry-run
"""
import argparse
import json
from pathlib import Path

TOURS_JSON = Path(__file__).parent / "generated" / "wordpress_tours.json"

# ── Common item translations ─────────────────────────────────────────────
# Key: Spanish item (exact match), Value: English translation

INCLUDES_EN = {
    # Guides
    "Guía español / inglés": "Spanish / English guide",
    "Guía profesional de turismo": "Professional tourism guide",
    "Guía profesional de turismo.": "Professional tourism guide.",
    "Guía profesional.": "Professional guide.",
    "Guía profesional": "Professional guide",
    "Guía profesional de montaña.": "Professional mountain guide.",
    "Guía bilingüe (inglés y español).": "Bilingual guide (English and Spanish).",
    "Guía, en inglés y español.": "Guide, in English and Spanish.",
    "Guía certificado en español / inglés": "Certified guide in Spanish / English",
    "Guía profesional de turismo inglés – Español.": "Professional tourism guide English – Spanish.",
    "Guía oficial de turismo": "Official tourism guide",
    "Guía de sitio, en Machu Picchu.": "On-site guide at Machu Picchu.",
    "Guía instructor": "Instructor guide",
    # Transport
    "Transporte turístico": "Tourist transportation",
    "Transporte turístico compartido": "Shared tourist transportation",
    "Transporte turístico, en grupo.": "Group tourist transportation.",
    "Transporte turístico ida y vuelta.": "Round-trip tourist transportation.",
    "Transporte turístico en Sprinter Mercedes Benz, de 19 pasajeros.": "Tourist transportation in a 19-passenger Mercedes Benz Sprinter.",
    "Transporte en Sprinter Mercedes Benz, de 19 pasajeros.": "Transportation in a 19-passenger Mercedes Benz Sprinter.",
    "Transporte turístico: Mercedes Benz, de 19 pasajeros.": "Tourist transportation: 19-passenger Mercedes Benz.",
    "Transporte a Soraypampa.": "Transportation to Soraypampa.",
    "Transporte a Lares.": "Transportation to Lares.",
    "Transporte a Cruz Pata (lugar donde se inicia la caminata).": "Transportation to Cruz Pata (trailhead).",
    "Transporte al Km. 82": "Transportation to Km. 82",
    "Transporte Cusco a Estación de Ollantaytambo  (ida y vuelta).": "Transportation Cusco to Ollantaytambo Station (round trip).",
    "Transporte cusco a estación de Ollantaytambo ida y vuelta": "Transportation Cusco to Ollantaytambo Station round trip",
    "Transporte Ollantaytambo a Cusco": "Transportation Ollantaytambo to Cusco",
    "Transporte Ollantaytambo- Cusco.": "Transportation Ollantaytambo – Cusco.",
    "Transporte Ollanta – Cusco.": "Transportation Ollanta – Cusco.",
    "Transporte turistico: Cusco – Hidroeléctrica – Cusco.": "Tourist transportation: Cusco – Hidroelectrica – Cusco.",
    "Transporte-Hotel – Estación de tren.": "Transportation: Hotel – Train station.",
    "Movilidad": "Transportation",
    "Movilidad Turística con baño": "Tourist vehicle with restroom",
    "Bus de turismo.": "Tour bus.",
    "Bus-Ollanta – Cuzco.": "Bus Ollanta – Cusco.",
    # Hotel / Accommodation
    "Hotel en Aguas Calientes.": "Hotel in Aguas Calientes.",
    'Hotel en "Aguas Calientes".': 'Hotel in "Aguas Calientes".',
    'Hotel en \u201cAguas Calientes\u201d.': 'Hotel in "Aguas Calientes".',
    "Hotel en Machupicchu pueblo": "Hotel in Machu Picchu town",
    'Hotel en «Machu-Picchu».': 'Hotel in Machu Picchu.',
    "1 noche de hotel, en Machupicchu Pueblo.": "1 night hotel in Machu Picchu town.",
    "02 Noches de alojamiento en Cusco.": "02 Nights accommodation in Cusco.",
    "03 Noches de alojamiento en Cusco.": "03 Nights accommodation in Cusco.",
    "04 Noches de alojamiento en Cusco.": "04 Nights accommodation in Cusco.",
    # Meals
    "Almuerzo": "Lunch",
    "Almuerzo.": "Lunch.",
    "Almuerzo Buffet": "Buffet lunch",
    "Almuerzo bufette en el Restaurante Turístico en Urubamba": "Buffet lunch at the tourist restaurant in Urubamba",
    "Almuerzo bufette en restaurante Don Ángel en Urubamba (Valle sagrado)": "Buffet lunch at Don Angel restaurant in Urubamba (Sacred Valley)",
    "Almuerzo buffet en restaurante Don Ángel en Urubamba (Valle sagrado)": "Buffet lunch at Don Angel restaurant in Urubamba (Sacred Valley)",
    "Almuerzo-buffet en el Restaurante Turístico en Urubamba": "Buffet lunch at the tourist restaurant in Urubamba",
    "Desayuno y almuerzo.": "Breakfast and lunch.",
    "Alimentación 1B, 1L, 1D.": "Meals: 1 Breakfast, 1 Lunch, 1 Dinner.",
    "Alimentación (3 desayunos, 3 almuerzos, 3 cenas).": "Meals (3 breakfasts, 3 lunches, 3 dinners).",
    "Bus para subir y bajar Machu Picchu. Alimentación (4 desayunos, 4 almuerzos y 4 cenas)": "Bus up and down Machu Picchu. Meals (4 breakfasts, 4 lunches and 4 dinners)",
    "Snack o Box Lunch": "Snack or box lunch",
    "Snacks para la caminata.": "Snacks for the hike.",
    # Pickup
    "Recojo en el hotel": "Hotel pickup",
    "Asistencia permanente": "Permanent assistance",
    # Tickets / Entries
    "Entrada": "Entrance ticket",
    "Ingresos": "Entrance tickets",
    "Ticket de Ingreso": "Entrance ticket",
    "Ticket de ingreso.": "Entrance ticket.",
    "Ingreso a Machu Picchu.": "Entrance to Machu Picchu.",
    "Ingreso a Machupicchu": "Entrance to Machu Picchu",
    "Ingreso a Machu Picchu, Camino Inca.": "Entrance to Machu Picchu, Inca Trail.",
    "Ingreso al Camino Inca y Machu Picchu.": "Entrance to the Inca Trail and Machu Picchu.",
    "Boleto de ingreso a Machu Picchu.": "Machu Picchu entrance ticket.",
    "Boletos de ingreso a Machu Picchu.": "Machu Picchu entrance tickets.",
    "Ticket de ingreso a Machupicchu": "Machu Picchu entrance ticket",
    "Ingreso a Maras( salineras).": "Entrance to Maras (salt mines).",
    "Ingresos a Qoricancha.": "Entrance to Qoricancha.",
    "Entradas a Wacra Pucara y tierras privadas.": "Entrance to Waqra Pucara and private lands.",
    "Entradas a los farallones": "Entrance to the Farallones",
    "Ticket de entrada al área de la Laguna Humantay.": "Entrance ticket to the Humantay Lagoon area.",
    "Boleto turístico general para visita  a Sacsayhuaman, Qenqo, Puka – Pukara,  Tambomachay, Pisaq Ruinas, Ollantaytambo, Moray, Chincheros.": "General tourist ticket for visiting Sacsayhuaman, Qenqo, Puka Pukara, Tambomachay, Pisaq Ruins, Ollantaytambo, Moray, Chinchero.",
    "Boleto turístico general para visita  a Sacsayhuaman, Qenqo, Puka – Pukara, yTambomachay, Pisaq Ruinas, Ollantaytambo, Moray, Chincheros": "General tourist ticket for visiting Sacsayhuaman, Qenqo, Puka Pukara, Tambomachay, Pisaq Ruins, Ollantaytambo, Moray, Chinchero",
    "Boleto turístico parcial para visita  a Sacsayhuaman, Qenqo, Puka - Pukara y Tambomachay.": "Partial tourist ticket for visiting Sacsayhuaman, Qenqo, Puka Pukara and Tambomachay.",
    # Train
    "Boleto de tren Aguas Calientes – Ollantaytambo.": "Train ticket Aguas Calientes – Ollantaytambo.",
    "Boleto de tren de retorno de Machu Picchu a Ollantaytambo.": "Return train ticket from Machu Picchu to Ollantaytambo.",
    'Boleto de tren de "Aguas Calientes" a Ollanta y bus a Cusco.': 'Train ticket from "Aguas Calientes" to Ollanta and bus to Cusco.',
    'Boleto de tren de \u201cAguas Calientes\u201d a Ollanta y bus a Cusco.': 'Train ticket from "Aguas Calientes" to Ollanta and bus to Cusco.',
    'Boleto de tren de "Aguas Calientes" a Ollanta.': 'Train ticket from "Aguas Calientes" to Ollanta.',
    'Boleto de tren de \u201cAguas Calientes\u201d a Ollanta.': 'Train ticket from "Aguas Calientes" to Ollanta.',
    "Boleto de tren, Ollantaytambo-KM-104.": "Train ticket, Ollantaytambo – KM 104.",
    "Tren de Turismo Expedición Ollantaytambo – Machupicchu Pueblo – Ollantaytambo.": "Expedition tourist train Ollantaytambo – Machu Picchu town – Ollantaytambo.",
    "Tren turístico expedición de Ollantaytambo hacia Aguas Calientes, ida y vuelta.": "Expedition tourist train from Ollantaytambo to Aguas Calientes, round trip.",
    "Tren turístico expedition de Ollantaytambo hacia Aguas Calientes, ida y vuelta.": "Expedition tourist train from Ollantaytambo to Aguas Calientes, round trip.",
    "Tren turístico expedition ida y vuelta": "Expedition tourist train round trip",
    "Tren turístico expeditión de Ollantaytambo hacia Aguas Calientes, ida y vuelta.": "Expedition tourist train from Ollantaytambo to Aguas Calientes, round trip.",
    "Tren-Ollantaytambo – Machu Picchu – Ollantaytambo.": "Train Ollantaytambo – Machu Picchu – Ollantaytambo.",
    # Bus
    "Boleto de bus a Machu Picchu Aguas Calientes.": "Bus ticket to Machu Picchu Aguas Calientes.",
    "Bus de bajada de Machu Picchu – Aguas Calientes.": "Bus down from Machu Picchu – Aguas Calientes.",
    "Bus de subida a Machu Picchu, y bajada a Machupicchu Pueblo.": "Bus up to Machu Picchu, and down to Machu Picchu town.",
    "Bus de subida y bajada a Machupicchu": "Bus up and down to Machu Picchu",
    "Bus de subida y bajada a Mapi": "Bus up and down to Machu Picchu",
    "Bus para subir y bajar de Machu Picchu.": "Bus up and down Machu Picchu.",
    "Ticket de bus desde Aguas Calientes hacia Machu Picchu ida y vuelta.": "Bus ticket from Aguas Calientes to Machu Picchu round trip.",
    # Camping / Equipment
    "Equipo de campamento (carpas, matras).": "Camping equipment (tents, sleeping mats).",
    "Equipo de campamento y equipo de cocina, comedor, sillas, mesas.": "Camping equipment and kitchen equipment, dining area, chairs, tables.",
    "Equipo de campamento, carpas, matras, carpa comedor, cocina, mesas y sillas.": "Camping equipment, tents, sleeping mats, dining tent, kitchen, tables and chairs.",
    "Equipo de campamento, cocina, carpas, carpas, sillas, mesas, cocina.": "Camping equipment, kitchen, tents, chairs, tables.",
    "Equipo de cocina. (mesas, sillas, carpa comedor).": "Kitchen equipment (tables, chairs, dining tent).",
    "Caballos o mulas para el transporte del equipo.": "Horses or mules for equipment transport.",
    "Caballos, para el equipo.": "Horses for the equipment.",
    "Paquete de caballos de fuerza.": "Pack horses.",
    "Portero.": "Porter.",
    "Cocinero.": "Cook.",
    # Medical
    "Botiquín de primeros auxilios y oxígeno.": "First aid kit and oxygen.",
    "Botiquín de primeros auxilios, incluido oxígeno.": "First aid kit, including oxygen.",
    "Botiquín de primeros auxilios, oxígeno.": "First aid kit, oxygen.",
    "Oxígeno y botiquín de primeros auxilios.": "Oxygen and first aid kit.",
    # Tours
    "Tour guiado, de 2 horas, en Machu Picchu.": "2-hour guided tour at Machu Picchu.",
    "Tour guiado, en grupo.": "Guided group tour.",
    "Demostración de tejidos.": "Textile weaving demonstration.",
    "Visita 4 Lagunas": "Visit to 4 Lagoons",
    "Visita puente Queswachaca": "Visit to Queswachaca Bridge",
    # Transfers
    "Traslado de la estación a su hotel.": "Transfer from the station to your hotel.",
    "Traslado hotel a estación de bus - hotel": "Transfer hotel to bus station – hotel",
    "Traslado hotel a estación de bus ida y vuelta": "Transfer hotel to bus station round trip",
    "Traslado in/out": "Transfer in/out",
    "Traslados aeropuerto- hotel - aeropuerto": "Airport – hotel – airport transfers",
    # Ceremonies
    "Ceremonia dirigida por un chamán": "Ceremony led by a shaman",
    # Pre-hike
    "Informe previo a la caminata noche anterior a la caminata para repasar el itinerario, reunirse con su (s) guía (s) y pueda hacer cualquier pregunta.": "Pre-hike briefing the night before the trek to review the itinerary, meet your guide(s) and ask any questions.",
    # Other
    "Servicio a Bordo": "Onboard service",
    "Lancha rápida": "Speedboat",
    "Saco de dormir (bolígrafo).": "Sleeping bag (synthetic).",
    "Saco de dormir (pluma).": "Sleeping bag (down).",
    # Note: these are recommendations (in RECOMMENDATIONS_EN) but also appear in INCLUDES_EN
}

EXCLUDES_EN = {
    # Tickets
    "Boleto Turístico Parcial: Extranjeros S/ 70.00 soles por persona, Peruanos S/ 40.00 soles por persona": "Partial Tourist Ticket: Foreigners S/ 70.00 per person, Peruvians S/ 40.00 per person",
    "Boleto Turístico: extranjeros a S/.70.00 soles, Peruanos S/. 40.00 soles": "Tourist Ticket: foreigners S/ 70.00, Peruvians S/ 40.00",
    "Boleto turístico Extranjero S/. 70.00 soles y Nacionales S/.40.00 soles": "Tourist Ticket: foreigners S/ 70.00 and nationals S/ 40.00",
    "Ingreso a Maras (salineras).": "Entrance to Maras (salt mines).",
    "Ingreso a Maras (Salineras). Extranjeros S/. 15.00 por persona, Peruanos S/.10.00 soles por persona": "Entrance to Maras (salt mines). Foreigners S/ 15.00 per person, Peruvians S/ 10.00 per person",
    "Ingreso a Qoricancha S/. 15.00 soles.": "Entrance to Qoricancha S/ 15.00.",
    "Tickets de Ingreso a los lugares a visitar S/ 50.00 soles": "Entrance tickets to visited sites S/ 50.00",
    "Entrada a las montañas.": "Mountain entrance fees.",
    "Entrada a las termas de Lares.": "Entrance to Lares hot springs.",
    'Entrada a las termas de "Aguas Calientes"': 'Entrance to "Aguas Calientes" hot springs',
    'Entrada a las termas de \u201cAguas Calientes\u201d': 'Entrance to "Aguas Calientes" hot springs',
    'Entrada a las termas de "Aguas': 'Entrance to "Aguas Calientes" hot springs',
    'Entrada a las termas de \u201cAguas': 'Entrance to "Aguas Calientes" hot springs',
    "Entrada a los baños termales": "Entrance to hot springs",
    "Entradas": "Entrance tickets",
    # Meals
    "Almuerzo": "Lunch",
    "Almuerzo del segundo día.": "Lunch on the second day.",
    "Almuerzo del último día.": "Lunch on the last day.",
    "Almuerzo el segundo día.": "Lunch on the second day.",
    "Almuerzo en Machupicchu Pueblo, el segundo día.": "Lunch in Machu Picchu town, on the second day.",
    "Almuerzo en Machupicchu Pueblo.": "Lunch in Machu Picchu town.",
    "Almuerzo, en Machupicchu Pueblo, el segundo día.": "Lunch in Machu Picchu town, on the second day.",
    "Alimentos": "Food",
    "Comidas": "Meals",
    "Desayuno": "Breakfast",
    "Primer desayuno": "First breakfast",
    "Primer desayuno y último almuerzo.": "First breakfast and last lunch.",
    "Primer desayuno, último almuerzo.": "First breakfast, last lunch.",
    "Alimentación no especificada": "Meals not specified",
    "El almuerzo.": "Lunch.",
    # Personal expenses
    "Propinas": "Tips",
    "Propinas.": "Tips.",
    "Propinas y cualquier otro gasto personal.": "Tips and any other personal expenses.",
    "Propinas y gastos personales no incluidos en el programa.": "Tips and personal expenses not included in the program.",
    "Propinas y gastos personales.": "Tips and personal expenses.",
    "Propinas y otros gastos personales.": "Tips and other personal expenses.",
    "Otros gastos personales.": "Other personal expenses.",
    # Equipment
    "Bolsa de dormir.": "Sleeping bag.",
    "Bolsa de dormir. Ingreso a las termas en \"Aguas Calientes\".": "Sleeping bag. Entrance to hot springs in \"Aguas Calientes\".",
    "Bolsa de dormir. Ingreso a las termas en \u201cAguas Calientes\u201d.": "Sleeping bag. Entrance to hot springs in \"Aguas Calientes\".",
    "Chubasquero y poncho de lluvia.": "Raincoat and rain poncho.",
    "Caballo de emergencia": "Emergency horse",
    "Caballos, para transportar caminantes.": "Horses for transporting hikers.",
    "Portero adicional.": "Additional porter.",
    # Other
    "Agua, snacks, medicación personal, etc.": "Water, snacks, personal medication, etc.",
    "Documento original (pasaporte).": "Original document (passport).",
    "IGV 18%, en caso desee factura": "IGV 18% tax, in case an invoice is needed",
    "Seguro de viaje.": "Travel insurance.",
    "Paseo en embarcaciones de Totora": "Totora reed boat ride",
    "Recojo hotel Cusco": "Hotel pickup in Cusco",
    "Traductor del Chamán (opcional): $125.00 USD por reserva": "Shaman translator (optional): $125.00 USD per booking",
}

RECOMMENDATIONS_EN = {
    # Clothing
    "Ropa abrigada (ropa interior térmica, vellón, gorro, guantes y calcetines).": "Warm clothing (thermal underwear, fleece, hat, gloves and socks).",
    "Ropa calida.": "Warm clothing.",
    "Ropa sintética o de algodón (calcetines, pantalones, pantalones cortos, camisetas).": "Synthetic or cotton clothing (socks, pants, shorts, t-shirts).",
    "Vestimenta impermeable (poncho).": "Waterproof clothing (poncho).",
    "Chubasquero y poncho de lluvia.": "Raincoat and rain poncho.",
    "Poncho de lluvia Chubasquero.": "Raincoat and rain poncho.",
    # Footwear
    "Calzado de trekking resistente al agua.": "Waterproof trekking boots.",
    "Buenos zapatos para caminar (sandalias).": "Good walking shoes (sandals).",
    "Buenos zapatos para caminar, Sandalias.": "Good walking shoes, sandals.",
    # Sun protection
    "Gafas de sol": "Sunglasses",
    "Gafas de sol.": "Sunglasses.",
    "Lentes.": "Glasses.",
    "Sombrero para el sol y gafas de sol.": "Sun hat and sunglasses.",
    "Crema solar": "Sunscreen",
    "Protector solar.": "Sunscreen.",
    # Bags
    "Mochila pequeña": "Small backpack",
    "Mochila pequeña.": "Small backpack.",
    "Mochila pequeña con funda de lluvia.": "Small backpack with rain cover.",
    "Mochila pequeña. Medicamentos personales si es necesario": "Small backpack. Personal medication if necessary",
    # Medical
    "Medicamentos básicos.": "Basic medication.",
    "Medicamentos personales (si es necesario).": "Personal medication (if necessary).",
    "Medicamentos personales si es necesario.": "Personal medication if necessary.",
    "Medicamentos personales.": "Personal medication.",
    # Documents
    "Documento original (pasaporte, DNI).": "Original document (passport, ID).",
    "Pasaporte original.": "Original passport.",
    # Water / Food
    "Botellas de agua": "Water bottles",
    "1 litro y la mitad del agua (por persona, ¡al menos!).": "At least 1.5 liters of water per person.",
    "Snack personales (opcional).": "Personal snacks (optional).",
    # Equipment
    "Bastón (opcional).": "Walking stick (optional).",
    "Bastón y protector (opcional).": "Walking stick and protector (optional).",
    "Binoculares (opcional).": "Binoculars (optional).",
    "Prismáticos (opcional).": "Binoculars (optional).",
    "Prismáticos (opcional)..": "Binoculars (optional).",
    "Linterna – Baterías.": "Flashlight – Batteries.",
    "Linterna – pilas.": "Flashlight – batteries.",
    # Money
    "Dinero extra": "Extra money",
    "Dinero extra.": "Extra money.",
    # Other
    "Cosas personales.": "Personal belongings.",
    "Repelente.": "Insect repellent.",
    "Saco de dormir (bolígrafo).": "Sleeping bag (synthetic).",
    "Saco de dormir (pluma).": "Sleeping bag (down).",
}


# ── Per-tour translations ────────────────────────────────────────────────
# Key: slug, Value: dict of _en fields

TOUR_TRANSLATIONS = {
    "chinchero-maras-moray": {
        "description_en": "Discover the magical city of the Inca Empire through a complete all-inclusive experience. In this tour package you can enjoy the following tours: Chinchero + Maras – Moray.",
        "itinerary_en": "Around 08:30 we will pick you up at your hotel and travel north of the city of Cusco. Our first destination will be Chinchero, where you can learn about its history. Then we will head to the terraces of Moray, where you will discover this beautiful agricultural site. Next, we will visit the Maras Salt Mines viewpoint, where you can observe more than 3,000 salt pools, each about 5 meters in area. The Maras salt mines are a spectacular destination. We finish our tour around 2 pm back in the city of Cusco.",
        "schedule_en": "Monday to Sunday, 08:30 am",
        "difficulty_en": "Moderate",
        "conditions_en": "Tours are shared service. The tour starts at 08:30 hrs, but hotel pickups begin from 08:00 hrs or earlier if your hotel is far away. The service ends at Plaza Regocijo in Cusco (2 blocks from the Main Square). Children: From 5 years old pay the same rate, children under 5 sit on their parents' laps. In case of no-show, cancellations or postponements, 100% will be charged.",
        "booking_en": "100% payment required to guarantee your reservation. You can pay with any credit/debit card.",
        "prices_en": "PRICE PER PERSON:\n$14.00 USD\n\"Prices are not valid for holidays, Easter, national holidays, New Year, some festive days and long weekends\"",
    },
    "city-tour-cusco": {
        "description_en": "Discover the magical city of the Inca Empire through a complete all-inclusive experience. In this tour package you can enjoy the following tours: City Tour Cusco + 4 Ruins, Sacred Valley, Machu Picchu.\nEnjoy an unforgettable trip in Cusco and its surroundings on a tour with many experiences and archaeological destinations near the city.",
        "itinerary_en": "9:00 to 9:30 am pickup at your hotel to start visiting the famous Plaza San Blas, where we will talk about the history of the place and its importance. Then we walk to Hatun Rumiyoc street, famous for the Twelve-Angle Stone. From there we walk to the Plaza de Armas where we will have the most complete information about the place. We continue walking to Plaza Regocijo, notable for the Municipal Palace of Cusco. Then we head to Plaza San Francisco, famous for the Botanical Garden with native species of the Andes. Next, we visit the Arch of Santa Clara, an important place for our independence. Finally, to wrap up the tour, we head to the Traditional San Pedro Market.",
        "schedule_en": "Monday to Sunday, 09:00 hrs",
        "difficulty_en": "Moderate",
        "conditions_en": "Tours are private service. The tour is on foot, no vehicles are used. The service ends at the plaza. Children: From 5 years old pay the same rate. In case of no-show, cancellations or postponements, 100% will be charged.",
        "booking_en": "100% payment required to guarantee your reservation. You can pay with any credit/debit card or bank transfer. Please check availability before making payment.",
        "prices_en": "PRICE PER PERSON: $40.00 USD\n\"Prices are not valid for holidays, Easter, national holidays, New Year, some festive days and long weekends\"",
    },
    "circuito-sur": {
        "description_en": "Today, we start the tour with pickup from your hotel around 08:30 hrs. After one hour we will arrive at the Inca Architectural Complex of Tipon, with its aqueducts, fountains and terraces, dedicated to agriculture and the Water Cult. There, the Water Temple stands out, where the Incas performed ceremonies during times of drought.",
        "itinerary_en": "Today, we start the tour with pickup from your hotel around 08:30 hrs. After one hour we arrive at the Inca Architectural Complex of Tipon, with its aqueducts, fountains and terraces, dedicated to agriculture and the Water Cult. There, the Water Temple stands out, where the Incas performed ceremonies during times of drought.\nAfter this guided visit, our transport will take us about 40 minutes to the Pre-Inca Architectural Complex of Pikillaqta, from the Wari Civilization and Culture. There, well-organized temples, houses, streets and plazas stand out, built with small stones and clay. In several rooms, you can still see remains of the stucco applied to the walls, with plaster and clay combined.\nFinally, we will head to the famous Colonial Church of Andahuaylillas, better known as the 'Sistine Chapel of the Americas', whose interior is almost entirely decorated with frescoes, murals and canvases, as well as sculptures and paintings by famous Peruvian and foreign artists from the Colonial Era. The tour ends a few blocks from the Main Square of Cusco, around 2:00 p.m.",
        "schedule_en": "Monday to Sunday, 08:30 am",
        "difficulty_en": "Moderate",
        "conditions_en": "Tours are shared service. The tour starts at 09:00 hrs, but hotel pickups begin from 08:30 hrs or earlier if your hotel is far away. The service ends at Plaza Regocijo in Cusco (2 blocks from the Main Square). Children: From 5 years old pay the same rate, children under 5 sit on their parents' laps. In case of no-show, cancellations or postponements, 100% will be charged.",
        "booking_en": "100% payment required to guarantee your reservation. You can pay with any credit/debit card.",
        "prices_en": "PRICE PER PERSON: $14.00 USD\n\"Prices are not valid for holidays, Easter, national holidays, New Year, some festive days and long weekends\"",
    },
    "laguna-de-humantay": {
        "description_en": "Between 4:10 and 4:50 a.m., we will pick you up at your hotel, aboard our 19-passenger vehicle, and travel as a group along a paved road between Cusco and Abancay until reaching Mollepata, where you will have breakfast. Then we will detour to Soraypampa, where we will start the hike at an altitude of 3,900 meters above sea level.",
        "itinerary_en": "Between 4:10 and 4:50 a.m., we will pick you up at your hotel, aboard our 19-passenger vehicle, and travel as a group along a paved road between Cusco and Abancay until reaching Mollepata, where you will have breakfast. Then we will detour to Soraypampa, where we will start the hike at an altitude of 3,900 meters above sea level. After a brief rest, we will begin walking uphill towards Humantay Lagoon, located at about 4,180 m.a.s.l.\nAfter the ascent of approximately 1 hour and 20 minutes, we can admire the wonderful landscape, with the beautiful lagoon and spectacular glaciers on the horizon. Then, our guide will give a brief explanation, we will take souvenir photos, and have some free time to enjoy the place. We will return to Mollepata where you will have lunch before returning to the city of Cusco, arriving around 5:00 p.m.",
        "schedule_en": "Monday to Sunday, 05:00 am",
        "difficulty_en": "Moderate",
        "conditions_en": "Tours are shared service. The tour starts at 05:00 hrs, but hotel pickups begin from 04:20 hrs or earlier if your hotel is far away. In case of no-show, cancellations or postponements, 100% will be charged.",
        "booking_en": "100% payment required to guarantee your reservation. You can pay with any credit/debit card.",
        "prices_en": "Peruvians $28.00 USD\nForeigners $35.00 USD\n\"Prices are not valid for holidays, Easter, national holidays, New Year, some festive days and long weekends\"",
    },
    "combinada": {
        "description_en": "In Cusco, every corner is steeped in history. The former capital of Peru (during the Inca Empire) still preserves vestiges of what was the most important power of this ancient civilization. Ancient history can be felt in every step through the streets of its towns, which seem frozen in time.",
        "itinerary_en": "Our tour begins at 1:00 pm with pickup from your hotel or Airbnb. We will visit Qoricancha or the ancient Inca Temple of the Sun, built with finely finished stone blocks, which, before the arrival of the Spanish, were covered with gold sheets. Then Sacsayhuaman, whose monoliths of up to 130 tons were shaped and placed block upon block without any mortar. Besides its fortress-like appearance, this monumental complex served astronomical, sacred and ceremonial functions.\nThe next architectural complex we will visit is Qenqo. At first glance, you can see the sculpture, destroyed by the Spanish, of a totem or Apu, shaped like a phallus. Additionally, on the back rock, whose surface is carved with monkeys, you will find the Sector of Fertility and Water Rites.\nOur next visit is the Architectural Complex of Puka Pukara, which consists of a walled construction giving it a military appearance and, from its highest point, you can enjoy a great view of the entire valley.\nThen, we will visit Tambomachay, also known as the Temple to the Water Deity. Our tour ends around 5:30 pm and the drop-off will be in the center of Cusco.",
        "schedule_en": "Monday to Sunday, 10:00 hrs and 1:00 pm",
        "difficulty_en": "Moderate",
        "conditions_en": "Tours are shared service. The tour starts at 13:00 hrs, but hotel pickups begin from 12:30 hrs or earlier if your hotel is far away. The service ends at Plaza Regocijo in Cusco (2 blocks from the Main Square). Children: From 5 years old pay the same rate, children under 5 sit on their parents' laps. In case of no-show, cancellations or postponements, 100% will be charged.",
        "booking_en": "100% payment required to guarantee your reservation. You can pay with any credit/debit card.",
        "prices_en": "$8.00 USD\n\"Prices are not valid for holidays, Easter, national holidays, New Year, some festive days and long weekends\"",
    },
    "palcoyo": {
        "description_en": "Discover the itinerary we have for you. We offer a complete experience and personalized attention. In this tour package you can enjoy the Palcoyo Tour departing from Cusco, as well as a combined experience with other destinations.\nEnjoy an unforgettable trip to Palcoyo and its surroundings.",
        "itinerary_en": "Early in the morning we will pick you up at your hotel, then we will begin our magical adventure and travel south from Cusco until reaching Combapata. On the way we can see local animals and beautiful landscapes. Once we arrive at our destination, we will have a slow walk where we will enjoy privileged views of this part of the mountain range, with three colorful mountains visible from the highest point. Then you will have an explanation from the guide and can take unforgettable photos and visit Palcoyo Mountain. After visiting Palcoyo, we will return to our vehicle and drive for 1 hour to the Checacupe Bridge, a hanging bridge built by the Quechua people to connect the Inca Empire. Then we can have lunch and rest a bit before continuing our journey back to the city of Cusco.",
        "schedule_en": "Monday to Sunday, 06:30 am",
        "difficulty_en": "Moderate",
        "conditions_en": "Tours are shared service. The tour starts at 06:30 hrs, but hotel pickups begin from 06:00 hrs or earlier if your hotel is far away. In case of no-show, cancellations or postponements, 100% will be charged.",
        "booking_en": "100% payment required to guarantee your reservation. You can pay with any credit/debit card.",
        "prices_en": "PRICE PER PERSON:\nPeruvians $30.00 USD\nForeigners $40.00 USD\n\"Prices are not valid for holidays, Easter, national holidays, New Year, some festive days and long weekends\"",
    },
    "valle-sagrado-vip": {
        "description_en": "Upon arriving at the Sacred Valley, it is impossible not to be impressed by the beauty of the Urubamba mountain range, the green fields bathed by the sun god or Inti, and the winding Vilcanota River.\nThis impressive Andean valley shelters important archaeological sites and picturesque towns that maintain their cultural identity intact.",
        "itinerary_en": "Around 6:45 we will pick you up at your hotel and travel north of Cusco to visit the Sacred Valley of the Incas. The first destination will be Chinchero, where you can learn about its history. Then we will go to the Terraces of Moray, where you will discover this beautiful agricultural site. Next, we visit the Maras Salt Mines viewpoint, where you can observe more than 3,000 salt pools, each about 5 meters in area. The Maras salt mines are a spectacular destination. We will continue to Urubamba where we will have our buffet lunch.\nAfter lunch we will visit the archaeological center of Ollantaytambo where we will have a guided tour and some time to explore the site. Finally we will go to the ruins of Pisac for a guided tour and then return to the city of Cusco.\nDrop-off in the center of Cusco.",
        "schedule_en": "Monday to Sunday, 06:30 am",
        "difficulty_en": "Moderate",
        "conditions_en": "Tours are shared service. The tour starts at 07:00 hrs, but hotel pickups begin from 06:30 hrs or earlier if your hotel is far away. The service ends at Plaza Regocijo in Cusco (2 blocks from the Main Square). Children: From 5 years old pay the same rate, children under 5 sit on their parents' laps. In case of no-show, cancellations or postponements, 100% will be charged.",
        "booking_en": "100% payment required to guarantee your reservation. You can pay with any credit/debit card.",
        "prices_en": "PRICE PER PERSON:\n$22.00 USD\n\"Prices are not valid for holidays, Easter, national holidays, New Year, some festive days and long weekends\"",
    },
    "valle-sagrado-tradicional": {
        "description_en": "The Sacred Valley of the Incas is one of the most beautiful experiences on your trip to Cusco and Machu Picchu. Throughout the day you can appreciate its magnificence along the Urubamba River.\nThe Sacred Valley is a traditional and highly sought-after tour for its variety of experiences.",
        "itinerary_en": "Between 7:30 and 8:00 a.m., we will pick you up at your hotel, aboard our tourist transport vehicle, and travel as a group to the Inca Architectural Complex of Pisac, located one and a half hours from the city of Cusco, at 2,850 meters above sea level. Its impressive stepped terraces were multifunctional, serving for agriculture, as gardens and agricultural laboratories, and as retaining structures on mountain slopes. Then we will head to Urubamba to enjoy a buffet lunch at Don Angel Restaurant.\nContinuing the tour to the Archaeological Complex of Ollantaytambo, with its megalithic constructions where administrative, military and religious functions were carried out. Then, 30 minutes from Ollantaytambo, we will visit the Colonial Church and Inca Architectural Complex of Chinchero.\nFinally, we can witness a demonstration of the alpaca wool dyeing process for hand-weaving traditional textiles, with designs and symbols representing various aspects of daily life and Andean cosmology, with fine finishes, before returning to the city of Cusco.",
        "schedule_en": "Monday to Sunday, 08:00 am",
        "difficulty_en": "Moderate",
        "conditions_en": "Tours are shared service. The tour starts at 08:00 hrs, but hotel pickups begin from 07:30 hrs or earlier if your hotel is far away. The service ends at Plaza Regocijo in Cusco (2 blocks from the Main Square). Children: From 5 years old pay the same rate, children under 5 sit on their parents' laps. In case of no-show, cancellations or postponements, 100% will be charged.",
        "booking_en": "100% payment required to guarantee your reservation. You can pay with any credit/debit card.",
        "prices_en": "PRICE PER PERSON: $22.00 USD\n\"Prices are not valid for holidays, Easter, national holidays, New Year, some festive days and long weekends\"",
    },
    "walking-tour-cusco": {
        "description_en": "Discover the magical city of the Inca Empire through a complete all-inclusive experience. In this tour package you can enjoy the following tours: City Tour Cusco + 4 Ruins, Sacred Valley, Machu Picchu.\nEnjoy an unforgettable trip in Cusco and its surroundings on a tour with many experiences and archaeological destinations near the city.",
        "itinerary_en": "9:00 to 9:30 am pickup at your hotel to start visiting the famous Plaza San Blas, where we will talk about the history of the place and its importance. Then we walk to Hatun Rumiyoc street, famous for the Twelve-Angle Stone. From there we walk to the Plaza de Armas where we will have the most complete information about the place. We continue walking to Plaza Regocijo, notable for the Municipal Palace of Cusco. Then we head to Plaza San Francisco, famous for the Botanical Garden with native species of the Andes. Next, we visit the Arch of Santa Clara, an important place for our independence. Finally, to wrap up the tour, we head to the Traditional San Pedro Market.",
        "schedule_en": "Monday to Sunday, 09:00 hrs",
        "difficulty_en": "Moderate",
        "conditions_en": "Tours are private service. The tour is on foot, no vehicles are used. The service ends at the plaza. Children: From 5 years old pay the same rate. In case of no-show, cancellations or postponements, 100% will be charged.",
        "booking_en": "100% payment required to guarantee your reservation. You can pay with any credit/debit card or bank transfer. Please check availability before making payment.",
        "prices_en": "PRICE PER PERSON: $40.00 USD\n\"Prices are not valid for holidays, Easter, national holidays, New Year, some festive days and long weekends\"",
    },
    "montana-de-7-colores": {
        "description_en": "The Rainbow Mountain (also called Vinicunca or simply 'Rainbow Mountain') is one of Peru's best new attractions. Located more than 100 kilometers from the city of Cusco, at a summit altitude of 5,200 meters above sea level. It is a mountain formation dyed with various shades resulting from the complex combination of minerals.",
        "itinerary_en": "Between 4:20 and 4:50 in the morning, we will pick you up at your hotel, to travel aboard a group tourist transport along the South Valley. After two and a half hours, we will arrive at the District of Cusipata (3,310 m.a.s.l.), in the Province of Quispicanchis, where we will have breakfast.\nThen we will continue aboard our vehicle along a dirt road, passing through several rural communities such as Japura and Hanchipacha, until reaching the Community of Pampachiri (4,600 m.a.s.l.), where the road ends. There, we will begin the 5 km hike up to the Vinicunca Pass (5,020 m.a.s.l.).\nThis trail climbs gradually to the pass in a one-and-a-half-hour hike, during which we will have the opportunity to observe alpacas and llamas. At the summit, we will contemplate the famous mountain range and its impressive colors.\nAt the pass, we will have free time to enjoy the most beautiful panoramic views that Mother Nature offers, with the Rainbow Mountain in shades of pink, white, red, green, brown and mustard yellow.\nAfterwards, we will descend through the Red Valley for about two hours, reaching the starting point of the second part of our hike through magical places, with beautiful red mountains, and, with luck, we will spot vicuñas, condors, wallatas (Andean geese), etc., before returning to our vehicle which will take us to Cusipata for lunch.\nIn the afternoon, we will return to Cusco, where the vehicle will drop us off a few blocks from the Main Square, between 6:00 and 7:00 p.m.",
        "schedule_en": "Monday to Sunday, 05:00 am",
        "difficulty_en": "Moderate",
        "conditions_en": "Tours are shared service. The tour starts at 05:00 hrs, but hotel pickups begin from 04:10 hrs or earlier if your hotel is far away. In case of no-show, cancellations or postponements, 100% will be charged.",
        "booking_en": "100% payment required to guarantee your reservation. You can pay with any credit/debit card.",
        "prices_en": "PRICE PER PERSON:\nPeruvians $26.00 USD\nForeigners $34.00 USD\n\"Prices are not valid for holidays, Easter, national holidays, New Year, some festive days and long weekends\"",
    },
    "machupicchu": {
        "description_en": "Around 5:00 am we will pick you up at your hotel to transfer you to the bus station for Ollantaytambo, where you will board the Expedition tourist train to Machu Picchu town, where our guide will meet you.\nThen, you will board a bus up to Machu Picchu to enjoy a guided tour.",
        "schedule_en": "Monday to Sunday, 05:00 am",
        "difficulty_en": "Moderate",
        "conditions_en": "Tours are shared service. The tour starts at 06:30 hrs, but hotel pickups begin from 06:00 hrs or earlier if your hotel is far away. In case of no-show, cancellations or postponements, 100% will be charged.",
        "booking_en": "100% payment required to guarantee your reservation. You can pay with any credit/debit card.",
        "prices_en": "PRICE PER PERSON:\nPeruvians $220.00 USD\nForeigners $260.00 USD\n\"Prices are not valid for holidays, Easter, national holidays, New Year, some festive days and long weekends\"",
    },
    "machu-picchu-by-car-2d-1n": {
        "description_en": "Day 1: CUSCO – HIDROELECTRICA – MACHU PICCHU TOWN\nWe will pick you up from your hotel around 06:30 hrs, aboard our tourist transport, to head to the Hidroelectrica Railway Station, a 5-hour journey, to start the 2-hour hike from Hidroelectrica to Machu Picchu town.",
        "itinerary_en": "Day 1: CUSCO – HIDROELECTRICA – MACHU PICCHU TOWN\nWe will pick you up from your hotel around 06:30 hrs, aboard our tourist transport, to head to the Hidroelectrica Railway Station, a 5-hour journey, to start a 2-hour hike without a guide from Hidroelectrica to Machu Picchu town, as it is a single path that follows the train tracks. Once in town, you will go to your hotel.\nDay 2: MACHU PICCHU – HIDROELECTRICA – CUSCO\nVery early, the guide will pick you up from your hotel to head to the bus station, on the way to Machu Picchu. Upon entering, you will have a guided visit of approximately 2 and a half hours through the main architectural complexes.\nAfterwards, you will have free time to explore the site on your own and take photos. After the visit, you can take the buses down to the town where, after having lunch, you will need to head back to Hidroelectrica, arriving by 2:30 pm. Our transport will pick you up to return to Cusco, where the tour ends around 9:30 pm.",
        "schedule_en": "Monday to Sunday, 06:30 am",
        "difficulty_en": "Moderate",
        "conditions_en": "Tours are shared service. The tour starts at 06:30 hrs, but hotel pickups begin from 06:00 hrs or earlier if your hotel is far away. In case of no-show, cancellations or postponements, 100% will be charged.",
        "booking_en": "100% payment required to guarantee your reservation. You can pay with any credit/debit card.",
        "prices_en": "PRICE PER PERSON:\nPeruvians $120.00 USD\nForeigners $160.00 USD\n\"Prices are not valid for holidays, Easter, national holidays, New Year, some festive days and long weekends\"",
    },
    "valle-sagrado-conexion-a-machu-picchu": {
        "description_en": "Day 1: CUSCO – PISAC – URUBAMBA – OLLANTAYTAMBO – MACHU PICCHU TOWN\nWe will start the day picking up our travelers at their hotels around 08:30 hrs. Then aboard our tour bus, we will head to the Sacred Valley to visit the Inca Architectural Complex of Pisac.",
        "itinerary_en": "Day 1: CUSCO – PISAC – URUBAMBA – OLLANTAYTAMBO – MACHU PICCHU TOWN\nWe will start the day picking up our travelers at their hotels around 08:30 hrs. Then aboard our tour bus, we will head to the Sacred Valley to visit the Inca Architectural Complex of Pisac, located about 30 kilometers from Cusco. Among its most notable sectors are Qallaqasa, the Military Sector, Inca Cemetery, Inti Huatana, the Urban Sector, the Qolcas and the Agricultural Terraces.\nAfter this guided visit, we will descend to the valley floor to visit the Pisac Handicraft Market. Then, we will continue aboard our transport to the small city of Urubamba, where we will have lunch.\nIn the afternoon, about 30 minutes by bus, we will visit the Inca Architectural Complex of Ollantaytambo. Then, we will take the train to Machu Picchu town for dinner and an overnight stay at the hotel.\nDay 2: MACHU PICCHU – OLLANTAYTAMBO – CUSCO\nAccording to the scheduled entry time for Machu Picchu, we will take a bus for about 30 minutes uphill to the Inca City. Then, we will begin the guided tour and reach the highest part of the archaeological complex, from which we will have the opportunity to take photos at will, facing the world-famous Huayna Picchu mountain, from an open viewpoint where the guide will give us all the information about the history of Machu Picchu.\nAfter the visit, you will take a bus back down to Machu Picchu town, where you will have time for lunch and then head to the train station for the return to Cusco. Our staff will take you back to your hotel.",
        "schedule_en": "Monday to Sunday, 08:30 am",
        "difficulty_en": "Moderate",
        "conditions_en": "Tours are shared service. The tour starts at 08:30 hrs, but hotel pickups begin from 08:00 hrs or earlier if your hotel is far away. In case of no-show, cancellations or postponements, 100% will be charged.",
        "booking_en": "100% payment required to guarantee your reservation. You can pay with any credit/debit card.",
        "prices_en": "PRICE PER PERSON:\nPeruvians $260.00 USD\nForeigners $320.00 USD\n\"Prices are not valid for holidays, Easter, national holidays, New Year, some festive days and long weekends\"",
    },
    "camino-inka-a-machupicchu-2-dias-1-noche": {
        "description_en": "Day 01:\nKM 104 – Aguas Calientes\nEarly pickup from your hotel to the Ollantaytambo train station, where we will board the train at approximately 06:10 am. We will continue the journey by train for approximately 1 hour and 30 minutes to KM 104.",
        "itinerary_en": "Day 01:\nKM 104 – Aguas Calientes\nEarly pickup from your hotel to the Ollantaytambo train station, where we will board the train at approximately 06:10 am. We will continue the journey by train for approximately 1 hour and 30 minutes to KM 104. There is an access control where we must present our ORIGINAL DOCUMENTS to be registered. Then, we will start the Inca Trail through the archaeological site of Chachabamba, then begin the mountain ascent for approximately three hours to reach the archaeological complex of Wiñayhuayna at (2,650 masl / 8,694 ft). We will have a rest stop for lunch. Continuing, we will arrive at \"Intipunku\" (Sun Gate). From here, we can enjoy one of the classic views of Machu Picchu. After taking some photos, we will head to the entrance control point and then take our bus to the town of \"Aguas Calientes\" where we will spend the night at a hotel.\nDay 02:\n\"Aguas Calientes\" – Machu Picchu – Cusco\nAfter breakfast at the hotel, we will take the first bus to the Inca city of Machu Picchu. After collecting our tickets at the control point, we will visit the archaeological complex of Machu Picchu, which takes about 2 hours. After a wonderful experience at Machu Picchu, we will return to \"Aguas Calientes\" to take our return train to Ollantaytambo. Upon arriving at Ollantaytambo, we will have transport to continue to Cusco, where you will be dropped off at your hotel.",
        "schedule_en": "",
        "difficulty_en": "Moderate",
        "conditions_en": "Tours are shared service. In case of no-show, cancellations or postponements, 100% will be charged.",
        "booking_en": "100% payment required to guarantee your reservation. You can pay with any credit/debit card.",
        "prices_en": "PRICE PER PERSON: $490.00 USD\n\"Prices are not valid for holidays, Easter, national holidays, New Year, some festive days and long weekends\"",
    },
    "camino-inka-a-machupicchu-4-dias-3-noches": {
        "description_en": "Day 01: Cusco – Huayllabamba\nWe will pick you up from your hotel in transport to head to KM 82 (2,650 masl / 8,694 ft), the starting point of our hike. It is important to present your original passport for the Inca Trail control. This day we will visit the archaeological complex of Patallacta.",
        "itinerary_en": "Day 01: Cusco – Huayllabamba\nWe will pick you up from your hotel in transport to head to KM 82 (2,650 masl / 8,694 ft), the starting point of our hike. It is important to present your original passport for the Inca Trail control. This day we will visit the archaeological complex of Patallacta, dry forests, and the archaeological site of Willkaracay. Our hike ends at the community of Huayllabamba, our first campsite (3,100 masl / 10,170 ft).\nDay 02: Huayllabamba – Pacaymayu\nAfter breakfast, we will start hiking; this is one of the most difficult days on the Inca Trail. Hiking uphill to reach the Warmiwañuska pass (4,250 masl / 13,828 ft) we will see the imposing peaks of the Vilcanota mountain range, then descend to the second campsite at Pacaymayo (3,600 masl / 11,811 ft).\nDay 03: Pacaymayu – Wiñaywayna\nThis is the longest day on the Inca Trail, but the most beautiful. We will observe the different ecological levels from highlands to cloud forests and rainforests, as well as all the tourist sites like Runkurakay (3,760 masl / 12,335 ft). We continue to the highest pass (3,900 masl / 12,795 ft), where we will have a brief rest and then descend to the archaeological remains of Sayacmarca (3,625 masl / 11,893 ft). Then, we head to Phuyupatamarka (3,600 masl / 11,811 ft), a rest stop to take some photos of the mountains. Continuing down the stairs, we take a path leading to our last campsite, Wiñaywayna.\nDay 04: Wiñaywayna – Machu Picchu\nEarly in the morning, we will have breakfast. Then, we pass through the Wiñaywayna control point, where we present our entry ticket, and hike to the \"Sun Gate\", known as \"Inti Punku\" (2,720 masl / 8,923 ft), for the first views of Machu Picchu. Leaving our backpacks at the Machu Picchu archaeological park control, we will enter Machu Picchu for a guided tour. After the visit, we descend to Aguas Calientes to take the return train to Ollantaytambo and then transport back to Cusco.",
        "schedule_en": "",
        "difficulty_en": "Moderate",
        "conditions_en": "Tours are shared service. In case of no-show, cancellations or postponements, 100% will be charged.",
        "booking_en": "100% payment required to guarantee your reservation. You can pay with any credit/debit card.",
        "prices_en": "PRICE PER PERSON: $660.00 USD\n\"Prices are not valid for holidays, Easter, national holidays, New Year, some festive days and long weekends\"",
    },
    "lares-trek-machu-picchu-4-dias-y-3-noches": {
        "description_en": "Day 01: Cusco – Lares – Huacahuasi\nPickup from your hotel at 06:00 a.m. Our transport will take us to Calca, where we will stop for breakfast and a short walk through the typical market of Calca.",
        "itinerary_en": "Day 01: Cusco – Lares – Huacahuasi\nPickup from your hotel at 06:00 a.m. Our transport will take us to Calca, where we will stop for breakfast and a short walk through the typical market of Calca. Continuing, we will arrive at the \"Hualcapunku Pass\" (4,300 masl / 14,107 ft) where we can enjoy views of the Ausangate snow-capped mountain, the highest in the Cusco region (6,370 masl / 20,898 ft). Continuing, we arrive at the Lares hot springs where we will have time to enjoy the waters. After lunch, we will prepare to set off on our walk to Huacahuasi, about 2 to 3 hours (3,800 masl / 12,467 ft), where we will spend the night in tents.\nDay 02: Huacahuasi – Patacancha\nIn the morning we will enjoy breakfast and start our hike towards the Ipsaycocha Pass with beautiful views of the Vilcanota mountain range. Then we descend to the Ipsaycocha lagoon with views of the Patacancha valley, which will be our second campsite.\nDay 03: Patacancha – Ollantaytambo – Machu Picchu\nAfter breakfast, we continue our hike. From this point we will find agricultural terraces and pass through the community of Willoq, a very picturesque village. The main attraction is their very characteristic clothing made by themselves, where red, green and yellow colors predominate in their textiles. We will have lunch in the town of Ollantaytambo. In the afternoon, we take the train to Machu Picchu and spend the night at a hotel.\nDay 04: Machu Picchu – Cusco\nAfter breakfast at the hotel, we will take one of the first buses to the Inca citadel of Machu Picchu, where we will have a guided tour of approximately 2 hours. Then, we return to Machu Picchu town to take our return train to Ollantaytambo and then transport back to Cusco, where you will be dropped off at your hotel.",
        "schedule_en": "",
        "difficulty_en": "Moderate",
        "conditions_en": "Tours are shared service. In case of no-show, cancellations or postponements, 100% will be charged.",
        "booking_en": "100% payment required to guarantee your reservation. You can pay with any credit/debit card.",
        "prices_en": "PRICE PER PERSON: $600.00 USD\n\"Prices are not valid for holidays, Easter, national holidays, New Year, some festive days and long weekends\"",
    },
    "salkantay-trek-machupicchu-4-dias-3-noches": {
        "description_en": "Day 01: Soraypampa – Chaullay\nPickup at 04:00 am from your hotels. Our transport will take us to Soraypampa (3,900 masl / 12,795 ft), with a stop at Mollepata for breakfast.",
        "itinerary_en": "Day 01: Soraypampa – Chaullay\nPickup at 04:00 am from your hotels. Our transport will take us to Soraypampa (3,900 masl / 12,795 ft), with a stop in Mollepata for breakfast and to pay a 20 soles entrance fee to the local municipality. We will begin our hike of approximately 4 hours ascending to the highest pass (4,650 masl / 15,255 ft). We can enjoy the most impressive views of Salkantay (6,272 masl / 20,577 ft). We continue through spectacular mountains and observe Humantay and Huayanay. We will also see small water pools. After a 4-hour descent, we arrive at our first campsite in Chaullay (2,950 masl / 9,678 ft).\nDay 02: Chaullay – La Playa\nAfter breakfast, we will hike towards La Playa river. On the way we will enjoy pleasant tropical jungle weather and appreciate plantations of coffee, cocoa, coca, bananas and other fruits, including some beautiful orchids. We will make a small stop for lunch at Lluscamayu and continue our hike to the second campsite.\nDay 03: La Playa – Hidroelectrica – Aguas Calientes\nEarly in the morning after breakfast, we will take local transport to Santa Teresa, then continue walking to \"Hidroelectrica\". Here, we will have two options: take the train or walk 3 more hours to reach Machu Picchu town. We spend the night at a hotel.\nDay 04: Aguas Calientes (Machu Picchu) – Cusco\nAfter breakfast at our hotel, we will take one of the first buses to Machu Picchu. At the entry point we present our original document and Machu Picchu tickets. The guided tour usually takes about 2 hours, during which you can take photos. To descend, we use the bus to Aguas Calientes and then take our return train to Ollantaytambo, continuing by bus to Cusco, where you will be dropped off at your hotel.",
        "schedule_en": "",
        "difficulty_en": "Moderate",
        "conditions_en": "Tours are shared service. In case of no-show, cancellations or postponements, 100% will be charged.",
        "booking_en": "100% payment required to guarantee your reservation. You can pay with any credit/debit card.",
        "prices_en": "PRICE PER PERSON: $380.00 USD\n\"Prices are not valid for holidays, Easter, national holidays, New Year, some festive days and long weekends\"",
    },
    "salkantay-trek-machupicchu-5-dias-4-noches": {
        "description_en": "Day 01: Cusco – Cruz Pata – Soraypampa\nPickup from your hotel at 05:00 a.m. Our transport will take us to Cruz Pata (2,800 masl / 9,186 ft). After a 3-hour journey, we arrive at Cruz Pata where we meet our muleteers and horses.",
        "itinerary_en": "Day 01: Cusco – Cruz Pata – Soraypampa\nPickup from your hotel at 05:00 a.m. Our transport will take us to Cruz Pata (2,800 masl / 9,186 ft). After a 3-hour journey, we arrive at Cruz Pata where we meet our muleteers and horses. From here we start our hike, approximately 6 hours, passing through traditional Andean communities like Challacancha that preserve their natural beauty, heading to Soraypampa. In the afternoon we visit Humantay Lagoon at 4,250 m.a.s.l., a wonderful place. Overnight at Soraypampa.\nDay 02: Soraypampa – Chaullay\nAfter breakfast, we begin our hike for about 4 hours climbing to the highest pass (4,650 masl / 15,255 ft). We can enjoy the most impressive views of Salkantay (6,272 masl / 20,577 ft). We continue through spectacular mountains observing Humantay and Huayanay. We will also see small ponds. After a long descent, we arrive at our campsite in Chaullay (2,950 masl / 9,678 ft), our 2nd camp.\nDay 03: Chaullay – La Playa\nAfter breakfast, we hike to La Playa. On the way we enjoy pleasant tropical jungle weather and can see plantations of coffee, bananas and other fruits, including beautiful orchids. We make a brief stop for lunch at Lluscamayu, continue our hike, arriving at our third campsite \"La Playa / The Beach\".\nDay 04: La Playa – Santa Teresa – Aguas Calientes\nEarly in the morning after breakfast, we take local transport to Santa Teresa, then continue walking to Machu Picchu \"Hidroelectrica\". Here we have two options: take the train or walk 2 hours to reach Aguas Calientes in Machu Picchu, where we stay at a hotel.\nDay 05: Machu Picchu – Cusco\nEarly in the morning after breakfast, we take the bus to Machu Picchu for a guided tour. After the visit, we return to Aguas Calientes and take the train to Ollantaytambo, then transport back to Cusco where you will be dropped off at your hotel.",
        "schedule_en": "",
        "difficulty_en": "Moderate",
        "conditions_en": "Tours are shared service. In case of no-show, cancellations or postponements, 100% will be charged.",
        "booking_en": "100% payment required to guarantee your reservation. You can pay with any credit/debit card.",
        "prices_en": "PRICE PER PERSON: $400.00 USD\n\"Prices are not valid for holidays, Easter, national holidays, New Year, some festive days and long weekends\"",
    },
    "choquequirao-4-dias-3-noches": {
        "description_en": "Day 01: Cusco – Cachora – Capuliyoc – Chiquisca\nOur transport will pick you up from your hotel at 5:00 a.m. Then, we begin our journey to the town of Cachora. Our trip takes approximately 4 hours from Cusco to Cachora (2,800 m / 9,186 ft).",
        "itinerary_en": "Day 01: Cusco – Cachora – Capuliyoc – Chiquisca\nOur transport will pick you up from your hotel at 5:00 a.m. Then, we begin our journey to the town of Cachora. Our trip takes approximately 4 hours from Cusco to Cachora (2,800 m / 9,186 ft). On the way we will make a stop to use the restrooms or have a coffee. Arriving in Cachora, we organize the horses and muleteers who will accompany us throughout the trip. We start our hike on this trail, seeing the most beautiful landscapes of the area, and arrive at the Capuliyoc pass (2,915 m / 9,563 ft). There we have lunch with a panoramic view of the Apurimac valley, and the Padreyoc and Wayna Cachora mountains. Then we descend to Coca Masana (2,330 masl / 7,644 ft), where the weather is warm. Finally, we arrive at CHIQUISCA (1,900 masl / 6,233 ft) near the Apurimac River, our first campsite.\nDay 02: Chiquisca – Rosalina Beach – Choquequirao\nEarly in the morning we have breakfast around 06:00 am and continue our hike for about 1 hour and 30 minutes to reach Rosalina Beach where we cross a hanging bridge over the Apurimac River. Then, we begin ascending Santa Rosa mountain (2,115 masl / 6,938 ft). During our journey we are accompanied by mountains and local vegetation. We arrive at Maranpata above the Chunchumayo River for a short rest. This section is the most difficult because after our rest we have 3 hours to climb Maranpata (2,850 m / 9,350 ft). We continue to Choquequirao, our second campsite.\nDay 03: Choquequirao – Maranpata – Chiquisca\nAfter breakfast at 07:00 am, we visit Choquequirao for 3 hours, then return to Maranpata to descend to Rosalina Beach. From Maranpata to Choquequirao (3,035 masl / 9,957 ft), we enjoy incredible views of the Apurimac Canyon. We continue our descent to our third campsite at Chiquisca.\nDay 04: Chiquisca – Cachora – Cusco\nAfter an early breakfast, we begin the final ascent to Capuliyoc and then descend to Cachora where our transport awaits to return us to Cusco.",
        "schedule_en": "",
        "difficulty_en": "Moderate",
        "conditions_en": "Tours are shared service. In case of no-show, cancellations or postponements, 100% will be charged.",
        "booking_en": "100% payment required to guarantee your reservation. You can pay with any credit/debit card.",
        "prices_en": "PRICE PER PERSON: $420.00 USD\n\"Prices are not valid for holidays, Easter, national holidays, New Year, some festive days and long weekends\"",
    },
    "queswachca-4-lagunas": {
        "description_en": "06:40 – 7:10 hrs. Pickup at hotels to head southeast of Cusco along the paved road from Cusco to Sicuani. After almost 2 and a half hours of travel, we arrive at the largest of the four lagoons, Pomacanchi Lagoon, where the guide will explain its formation and legends.",
        "itinerary_en": "06:40 – 7:10 hrs. Pickup at hotels to head southeast of Cusco along the paved Cusco–Sicuani road. After almost 2 and a half hours of travel, we arrive at the largest of the four lagoons, Pomacanchi Lagoon, where the guide will explain its formation and legends. Then we continue by vehicle to Acopia Lagoon, Asnaqocha and Pampamarca, where we can observe Andean and migratory birds.\nLunch in the district of Acopia. Then we continue to the Inca bridge of Queswachaca, passing by Yanaoca, the capital of Canas province, arriving in 30 minutes at the mysterious Inca bridge of Queswachaca, where the guide will explain and you will have the challenge of crossing the Inca bridge (built from an Andean plant called \"Ccoya\", similar to ichu grass, braided to make a rope). Then return to the city of Cusco at 4:00 p.m.",
        "schedule_en": "Monday to Sunday, 07:00 hrs",
        "difficulty_en": "Moderate",
        "conditions_en": "Tours are shared service. The tour starts at 07:00 hrs, but hotel pickups begin from 06:30 hrs or earlier if your hotel is far away. The service ends at Plaza Regocijo in Cusco (2 blocks from the Main Square), only if the hotel is on the return route the vehicle may drop passengers at their hotel. Children: From 5 years old pay the same rate, children under 5 sit on their parents' laps. In case of no-show, cancellations or postponements, 100% will be charged.",
        "booking_en": "100% payment required to guarantee your reservation. You can pay with any credit/debit card.",
        "prices_en": "PRICE PER PERSON: $420.00 USD\n\"Prices are not valid for holidays, Easter, national holidays, New Year, some festive days and long weekends\"",
    },
    "los-farallones-de-tecsecocha": {
        "description_en": "Tours are shared service. In case of no-show, cancellations or postponements, 100% will be charged.\n\n100% payment required to guarantee your reservation. You can pay with any credit/debit card or bank transfer. Please check availability before making payment.",
        "schedule_en": "",
        "difficulty_en": "Moderate",
        "conditions_en": "Tours are shared service. In case of no-show, cancellations or postponements, 100% will be charged.",
        "booking_en": "100% payment required to guarantee your reservation. You can pay with any credit/debit card or bank transfer. Please check availability before making payment.",
        "prices_en": "PRICE PER PERSON: $420.00 USD\n\"Prices are not valid for holidays, Easter, national holidays, New Year, some festive days and long weekends\"",
    },
    "waqrapucara": {
        "description_en": "Cusco – Acomayo – Waqrapukara – Cusco\nVery early, around 3:30 am, we will pick you up from your hotel to head to the starting point of our hike, 2.5 hours to the province of Acomayo, where we will enjoy the four-lagoon circuit.",
        "itinerary_en": "Cusco – Acomayo – Waqrapukara – Cusco\nVery early, around 3:30 am, we will pick you up from your hotel to head to the starting point of our hike, 2.5 hours to the province of Acomayo, where we will enjoy the four-lagoon circuit of Acomayo. We continue for 30 more minutes to Qenterococha Lagoon (4,330 m / 14,138 ft) where we will have a delicious breakfast. After breakfast, we will begin our hike to the Waqrapukara complex. During the hike, we can identify the flora and wildlife of the area.\nOnce we reach the first viewpoint of Waqrapukara, we will take a rest and then continue until we reach our objective. Finally we arrive at this incredible place, rest, and explore the archaeological center with our guide who will provide all the detailed information. Then you will have free time to explore and take photos. We then begin walking back, but taking a different path that is easier and also has different viewpoints of the Apurimac Canyon. We return to the trailhead around 1:40 pm, where our private vehicle awaits and we will also have lunch. We return to Cusco around 7:00 pm. Travelers doing the Waqrapukara trip must be in good physical condition and well acclimatized to altitude.",
        "schedule_en": "",
        "difficulty_en": "Moderate",
        "conditions_en": "Tours are shared service. In case of no-show, cancellations or postponements, 100% will be charged.",
        "booking_en": "100% payment required to guarantee your reservation. You can pay with any credit/debit card.",
        "prices_en": "PRICE PER PERSON: $420.00 USD\n\"Prices are not valid for holidays, Easter, national holidays, New Year, some festive days and long weekends\"",
    },
    "tradicional-cusco-3-d-2-n": {
        "description_en": "Discover the magical city of the Inca Empire through a complete all-inclusive experience. In this tour package you can enjoy the following tours: City Tour Cusco + 4 Ruins, Sacred Valley, Machu Picchu.\nEnjoy an unforgettable trip in Cusco and its surroundings on a tour with many experiences and archaeological destinations near the city.",
        "itinerary_en": "Day 1:\nCUSCO CITY\nThis program allows us to visit the best of the city of Cusco and reach one of the most enigmatic places in the world: Machu Picchu. We will pick you up from the airport and transfer you to your hotel in Cusco.\nAround 1 pm we will pick you up from the hotel to begin the tour. First, we will visit the Qoricancha Temple or Temple of the Sun. We continue our journey visiting the great fortress of Sacsayhuaman, Qenqo (also known as the labyrinth), Puka Pukara the red fortress, and lastly the Inca Baths of Tambomachay. Our tour ends near the Main Square of Cusco, around 6 pm.\nOvernight in Cusco.\nDay 2:\nMACHU PICCHU\nEarly in the morning we will pick you up from your hotel to transfer you to the bus station that will take you to Ollantaytambo station, where you will board the train to Aguas Calientes (Machu Picchu town), approximately a 2-hour journey during which you can appreciate the beautiful Sacred Valley landscapes. Upon arriving at Aguas Calientes, we board the bus that takes us to the Archaeological Park of Machu Picchu, situated high on the mountain. We will meet our guide who will begin the guided tour explaining the history and characteristics of the Inca city. The guided tour lasts approximately 2 hours, after which you will have time to explore Machu Picchu freely. After the visit, we return by bus to Aguas Calientes, where we will have time for lunch and explore the picturesque town. In the afternoon, we head to the train station to board the return train to Ollantaytambo, and then take transport to Cusco where our staff will be waiting to transfer you to your hotel.\nImportant:\nTrain schedules may vary according to seat availability. Entry to the citadel of Machu Picchu will be in the first time slots.\nDay 3:\nFREE DAY / AIRPORT TRANSFER\nThis day you can explore on your own or rest before your airport transfer.",
        "schedule_en": "Daily",
        "difficulty_en": "Moderate",
        "conditions_en": "Tours are shared service. The city tour starts at 13:00 hrs, but hotel pickups begin from 12:45 hrs or earlier if your hotel is far away. The service ends at Plaza Regocijo in Cusco (2 blocks from the Main Square), only if the hotel is on the return route the vehicle may drop passengers at their hotel. Children: From 5 years old pay the same rate, children under 5 sit on their parents' laps. In case of no-show, cancellations or postponements, 100% will be charged.",
        "booking_en": "100% payment required to guarantee your reservation. You can pay with any credit/debit card.",
        "prices_en": "PRICE PER PERSON:\nA&F APART HOTEL / HOTEL 2* OR 3* ECONOMY\nForeigners: $455.00 USD\nPeruvians: $425.00 USD\nHOTEL 3*\nForeigners: $485.00 USD\nPeruvians: $455.00 USD\nHOTEL 3* SUPERIOR\nForeigners: $515.00 USD\nPeruvians: $485.00 USD",
    },
    "cusco-magico-4-dias-3-noches": {
        "description_en": "Discover the magical city of the Inca Empire through a complete all-inclusive experience. In this tour package you can enjoy the following tours: City Tour Cusco + 4 Ruins, Sacred Valley, Machu Picchu.\nEnjoy an unforgettable trip in Cusco and its surroundings on a tour with many experiences and archaeological destinations near the city.",
        "itinerary_en": "Day 1:\nCITY TOUR + 4 RUINS\nAirport reception and transfer to hotel. Check-in and welcome coca tea. 12:45 – 1:20 pm Hotel pickup to start the excursion. City Tour Cusco: Sightseeing tour of the city, visiting: Qoricancha or Temple of the Sun, the Cathedral, continuing to the four ruins surrounding the city: Sacsayhuaman, Qenqo, Pukapukara and Tambomachay. 6:00 pm approx. return to Cusco. Overnight at selected hotel.\nDay 2:\nSACRED VALLEY\nAt 07:40 we pick you up from your hotel to begin the Sacred Valley of the Incas Tour: We visit the archaeological complex of Pisac, also the handicraft market, passing through the towns of Qoya, Lamay, Calca, Yucay. We continue to Urubamba, the commercial center of the valley, notable for its farmlands and pleasant weather at the foot of Chicon snow-capped mountain, where we enjoy lunch at a tourist restaurant. Then we continue to Ollantaytambo; an architectural complex that during the Tahuantinsuyo was a gigantic agricultural, administrative, social, religious and military complex. Then we head to Chinchero, the last stop. This town is a beautiful example of mestizo and colonial style. Tour ends in Cusco around 6:30 pm. Overnight at selected hotel.\nDay 3:\nMACHU PICCHU\nEarly in the morning we pick you up from your hotel to transfer you to the bus station that takes you to Ollantaytambo station, where you board the train to Aguas Calientes (Machu Picchu town), approximately a 2-hour journey with beautiful Sacred Valley landscapes. Upon arrival at Aguas Calientes, we board the bus to Machu Picchu Archaeological Park, high on the mountain. Our guide starts the tour explaining the history of the Inca city. The guided tour lasts approximately 2 hours, then free time to explore. After the visit, bus down to Aguas Calientes for lunch and exploration. In the afternoon, train back to Ollantaytambo and transport to Cusco.\nDay 4:\nFREE DAY / AIRPORT TRANSFER\nFree day to explore on your own or rest before your airport transfer.",
        "schedule_en": "Daily",
        "difficulty_en": "Moderate",
        "conditions_en": "Tours are shared service. Published price is valid for a minimum reservation of 2 people in a double or matrimonial room. Prices for 1 person or more than 2 people vary. Buffet lunch included in the Sacred Valley tour at Don Angel Restaurant. Due to fluctuating train availability and schedules, there may be some waiting time at the citadel to start the shared tour as passengers from other trains must be waited for. Services end at Plaza Regocijo in Cusco (2 blocks from the Main Square), only if the hotel is on the return route the vehicle may drop passengers at their hotel. In case of no-show, cancellations or postponements, 100% will be charged.",
        "booking_en": "100% payment required to guarantee your reservation.",
        "prices_en": "Prices per person:\nA&F APART HOTEL / HOTEL 2* OR 3* ECONOMY\nForeigners: $515.00 USD\nPeruvians: $490.00 USD\nHOTEL 3*\nForeigners: $555.00 USD\nPeruvians: $535.00 USD\nHOTEL 3* SUPERIOR\nForeigners: $595.00 USD\nPeruvians: $575.00 USD",
    },
    "cusco-tradicional-5-dias-4-noches": {
        "description_en": "Discover the magical city of the Inca Empire through a complete all-inclusive experience. In this tour package you can enjoy the following tours: City Tour Cusco + 4 Ruins, Sacred Valley, Machu Picchu.\nEnjoy an unforgettable trip in Cusco and its surroundings on a tour with many experiences and archaeological destinations near the city.",
        "itinerary_en": "Day 1:\nCITY TOUR + 4 RUINS\nAirport reception and transfer to hotel. Check-in and welcome coca tea. 12:45 pm Hotel pickup to start the excursion. City Tour Cusco: Sightseeing tour of the city, visiting: Qoricancha or Temple of the Sun, the Cathedral, continuing to the four ruins surrounding the city: Sacsayhuaman, Qenqo, Pukapukara and Tambomachay. 6:00 pm approx. return to Cusco. Overnight at selected hotel.\nDay 2:\nSACRED VALLEY\nAt 07:40 we pick you up from your hotel to begin the Sacred Valley of the Incas Tour: We visit the archaeological complex of Pisac, the handicraft market, passing through the towns of Qoya, Lamay, Calca, Yucay. We continue to Urubamba, notable for its farmlands and pleasant weather at the foot of Chicon snow-capped mountain, where we enjoy lunch at a tourist restaurant. Then to Ollantaytambo; a gigantic agricultural, administrative, social, religious and military complex from the Tahuantinsuyo era. Then Chinchero, a beautiful example of mestizo and colonial style. Tour ends in Cusco around 6:30 pm. Overnight at selected hotel.\nDay 3:\nRAINBOW MOUNTAIN\nLocated more than 100 kilometers from Cusco. Around 04:20 we pick you up from your accommodation to enjoy this mountain formation dyed with various shades from a complex combination of minerals. The slopes and summit are dyed in tones including red, purple, green, yellow, pink and other variations, at 5,200 m.a.s.l. It belongs to the town of Pitumarca who call it 'Cerro Colorado'. After the visit, we return to Cusco.\nDay 4:\nMACHU PICCHU\nEarly morning pickup to transfer to Ollantaytambo station. Train to Aguas Calientes (Machu Picchu town), approximately 2 hours with beautiful Sacred Valley landscapes. Bus up to Machu Picchu Archaeological Park. Guided tour of approximately 2 hours, then free time. Bus down to Aguas Calientes for lunch. Afternoon train to Ollantaytambo and transport to Cusco.\nDay 5:\nFREE DAY / AIRPORT TRANSFER\nFree day to explore on your own or rest before your airport transfer.",
        "schedule_en": "Daily",
        "difficulty_en": "Moderate",
        "conditions_en": "Tours are shared service. Published price is valid for a minimum reservation of 2 people in a double or matrimonial room. Prices for 1 person or more than 2 people vary. Buffet lunch included in the Sacred Valley tour at Don Angel Restaurant. Due to fluctuating train availability and schedules, there may be some waiting time at the citadel to start the shared tour as passengers from other trains must be waited for. Services end at Plaza Regocijo in Cusco (2 blocks from the Main Square), only if the hotel is on the return route the vehicle may drop passengers at their hotel. In case of no-show, cancellations or postponements, 100% will be charged.",
        "booking_en": "100% payment required to guarantee your reservation.",
        "prices_en": "PRICE PER PERSON:\nA&F APART HOTEL / HOTEL 2* OR 3* ECONOMY\nForeigners: $515.00 USD\nPeruvians: $490.00 USD\nHOTEL 3*\nForeigners: $555.00 USD\nPeruvians: $535.00 USD\nHOTEL 3* SUPERIOR\nForeigners: $595.00 USD\nPeruvians: $575.00 USD",
    },
    "ruta-del-sol-cusco-a-puno": {
        "description_en": "06:40 HRS Departure from OUR TERMINAL IN CUSCO. Andahuaylillas \"Sistine Chapel of the Americas\". We visit the church of San Pedro Apostol de Andahuaylillas, built by the Jesuits in the 16th century.",
        "itinerary_en": "06:40 HRS Departure from OUR TERMINAL IN CUSCO.\nAndahuaylillas \"Sistine Chapel of the Americas\"\nWe visit the church of San Pedro Apostol de Andahuaylillas, built by the Jesuits in the 16th century. Like other Spanish and religious constructions of the era, it was built on top of a huaca or sacred place for the Incas. Made of adobe and brick, the church is a small structure consisting of a single nave, apse and bell tower. But there is a reason it is known as the Sistine Chapel of the Americas.\nRaqchi – \"Temple of Wiracocha\"\nThe most important building within the complex is the \"Temple of Wiracocha\" which, according to ancient chroniclers, was built by Inca Wiracocha in honor of the invisible Supreme God of the Andean people \"Apu Kon Titi Wiracocha\". The \"Temple of Wiracocha\" is a large construction for that age. Architecturally it is classified as \"Kallanka\", that is, a tall building completely covered with thatch.\nMarangani Buffet Lunch\nLa Raya (tourist stop with beautiful Andean landscapes)\nAbra La Raya is the watershed between the valley that flows into Lake Titicaca and the valley leading to Cusco and the Sacred Valley. The altitude is 4,338 meters.\nPucara Museum – \"The Fertility Temple\"\nPucara was the first regional population center in the northern Lake Titicaca basin during the Late Formative Period (500 BC – 200 AD), providing valuable information about the origins of Andean civilization on the altiplano. The Pucara style is identified by impressive monolithic sculptures with a variety of geometric, zoomorphic and the most intricate anthropomorphic images, multi-colored ceramics in a variety of ritual and domestic forms.\n17:00 HRS Arrival in PUNO (BUS TERMINAL)",
        "schedule_en": "Monday to Sunday, 06:40 HRS",
        "difficulty_en": "Moderate",
        "conditions_en": "Shared service tour. Children: From 4 years old pay the same rate, children under 5 sit on their parents' laps. Hotel pickup in Puno $22.00 USD for up to 3 people, and return to hotel in Cusco $22.00 USD for up to 3 people. You must arrive 20 minutes before the indicated time for boarding. In case of no-show, cancellations or postponements, 100% will be charged.",
        "booking_en": "100% payment required to guarantee your reservation. You can pay with any credit/debit card or bank transfer. Please check availability before making payment.",
        "prices_en": "PRICE PER PERSON: $420.00 USD\n\"Prices are not valid for holidays, Easter, national holidays, New Year, some festive days and long weekends\"",
    },
    "pago-a-la-tierra-lectura-hojas-de-coca-ceremonia-andina": {
        "description_en": "AM/PM. Very traditional Andean ceremonies such as the Payment to the Earth (Pachamama offering), in which tribute is paid to Pachamama (Mother Earth), who gives us so many things. We express gratitude using a great variety of Andean elements while learning about the customs of the Andean people. A series of activities such as coca leaf reading, meditation or yoga in the village of Husao.",
        "itinerary_en": "AM/PM. Very traditional Andean ceremonies such as the Payment to the Earth, in which tribute is paid to Pachamama (Mother Earth), who gives us so many things. We express gratitude using a great variety of Andean elements while learning about the customs of the Andean people. A series of activities such as coca leaf reading, meditation or yoga in the village of Husao.",
        "schedule_en": "Monday to Sunday, approximate duration 2 – 3 hours",
        "difficulty_en": "Moderate",
        "conditions_en": "Tours are shared service, minimum 2 people to access the offered price. Children: From 5 years old pay the same rate, children under 5 ride with one of their parents. In case of no-show, cancellations or postponements, 100% will be charged.",
        "booking_en": "100% payment required to guarantee your reservation. You can pay with any credit/debit card or bank transfer. Please check availability before making payment.",
        "prices_en": "PRICE PER PERSON: $420.00 USD\n\"Prices are not valid for holidays, Easter, national holidays, New Year, some festive days and long weekends\"",
    },
    "puno-01-dia-isla-uros-taquile": {
        "description_en": "Take an excursion to the floating islands of the Uros on Lake Titicaca and discover the customs, dances, way of life and textiles of the Uros people. Take the best photos and videos of these impressive figures. Travel by boat and enjoy the scenery.",
        "itinerary_en": "Take an excursion to the floating islands of the Uros on Lake Titicaca and discover the customs, dances, way of life and textiles of the Uros people. Take the best photos and videos of these impressive figures. Travel by boat and enjoy the scenery.\n9:00 AM approx. Transfer from hotel to the lake port of Puno, to board a motorboat where we travel to the floating island of the Uros, visiting for about 45 minutes. We will have a friendly bilingual guide (English and Spanish) from the departure point who will tell us about the life of the inhabitants.\nThe Uros are a very ancient native community, made up of more than 40 islands built with totora reeds by their own inhabitants. The reeds are also used for building their homes, boats (rafts), fuel and as food. On this excursion we visit 2 or 3 islands for about 30 minutes each (with the option of taking a ride on the typical Totora reed boats). We arrive in Puno at approximately 12:30 pm and return to the hotel.",
        "schedule_en": "Monday to Sunday, 09:00 AM – 10:00 PM (DURATION: APPROX 3 HOURS)",
        "difficulty_en": "Moderate",
        "conditions_en": "Shared service tour. Children: From 5 years old pay the same rate, children under 5 sit on their parents' laps. For pickup at hotels far from the Main Square, an additional fee of S/ 60.00 (per trip) for up to 3 people applies. You must reconfirm your pickup time one day before with the reservations department. In case of no-show, cancellations or postponements, 100% will be charged.",
        "booking_en": "100% payment required to guarantee your reservation. You can pay with any credit/debit card or bank transfer. Please check availability before making payment.",
        "prices_en": "PRICE PER PERSON: $420.00 USD\n\"Prices are not valid for holidays, Easter, national holidays, New Year, some festive days and long weekends\"",
    },
}


def translate_item(item: str, dictionary: dict) -> str:
    """Look up exact match in dictionary, return as-is if not found."""
    return dictionary.get(item, item)


def main():
    parser = argparse.ArgumentParser(description="Add English translations to wordpress_tours.json")
    parser.add_argument('--dry-run', action='store_true',
                        help="Preview changes without writing")
    args = parser.parse_args()

    with open(TOURS_JSON, 'r', encoding='utf-8') as f:
        tours = json.load(f)

    translated = 0
    skipped = 0

    for tour in tours:
        if 'error' in tour:
            skipped += 1
            continue

        slug = tour['slug']
        t = TOUR_TRANSLATIONS.get(slug)
        if not t:
            print(f"  [SKIP] {slug}: no translation entry")
            skipped += 1
            continue

        # Add _en fields from per-tour translations
        for key in ('description_en', 'itinerary_en', 'schedule_en', 'difficulty_en',
                     'conditions_en', 'booking_en', 'prices_en'):
            if key in t:
                tour[key] = t[key]

        # Translate includes/excludes/recommendations lists
        if tour.get('includes'):
            tour['includes_en'] = [translate_item(i, INCLUDES_EN) for i in tour['includes']]
        if tour.get('excludes'):
            tour['excludes_en'] = [translate_item(e, EXCLUDES_EN) for e in tour['excludes']]
        if tour.get('recommendations'):
            tour['recommendations_en'] = [translate_item(r, RECOMMENDATIONS_EN) for r in tour['recommendations']]

        translated += 1
        if args.dry_run:
            # Show count of translated fields
            en_keys = [k for k in tour if k.endswith('_en')]
            print(f"  [TRANSLATE] {slug}: {len(en_keys)} _en fields")

    print(f"\nTranslated: {translated}, Skipped: {skipped}")

    if not args.dry_run:
        with open(TOURS_JSON, 'w', encoding='utf-8') as f:
            json.dump(tours, f, ensure_ascii=False, indent=2)
        print(f"Written to {TOURS_JSON}")
    else:
        print("(dry run — no changes written)")


if __name__ == "__main__":
    main()
