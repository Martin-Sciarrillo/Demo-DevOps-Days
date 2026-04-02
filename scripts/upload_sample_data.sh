#!/bin/bash
#
# Subir Datos de Muestra a los Índices de Búsqueda
# Carga los índices con datos de muestra de DevOps Days CORP
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_common.sh" 2>/dev/null || true

log_step "Uploading Sample Data to Indexes"

API_VERSION="2024-07-01"

# Upload documents to index
upload_docs() {
    local index=$1
    local docs=$2
    
    log_info "Uploading documents to $index..."
    
    HTTP_CODE=$(curl -s -o /tmp/upload_response.json -w "%{http_code}" \
        -X POST "${SEARCH_ENDPOINT}/indexes/${index}/docs/index?api-version=${API_VERSION}" \
        -H "api-key: ${SEARCH_KEY}" \
        -H "Content-Type: application/json" \
        -d "$docs")
    
    if [ "$HTTP_CODE" -ge 200 ] && [ "$HTTP_CODE" -lt 300 ]; then
        log_success "Uploaded documents to $index"
    else
        log_warn "Upload to $index may have issues (HTTP $HTTP_CODE)"
        if [ "$VERBOSE" = true ]; then
            cat /tmp/upload_response.json
        fi
    fi
}

# HR Documents
HR_DOCS='{
    "value": [
        {
            "@search.action": "upload",
            "id": "hr-001",
            "title": "Política de Trabajo Remoto",
            "category": "Políticas",
            "content": "Política de Trabajo Remoto de DevOps Days CORP: Los empleados pueden trabajar de forma remota hasta 3 días por semana con aprobación del manager. Las horas de colaboración core son de 10 a 15 hs en tu zona horaria local. Se otorga un subsidio de $500 para equipamiento del home office. VPN obligatoria para todo acceso remoto. Las reuniones presenciales trimestrales son obligatorias."
        },
        {
            "@search.action": "upload",
            "id": "hr-002",
            "title": "Resumen de Beneficios de Salud",
            "category": "Beneficios",
            "content": "DevOps Days CORP ofrece beneficios de salud completos: cobertura médica (opciones PPO y HMO), odontológica, visual y salud mental. La empresa paga el 85% de las primas para empleados, el 60% para dependientes. Cuentas FSA y HSA disponibles. Subsidio anual de bienestar de $1.200. Membresía gratuita en gimnasios asociados."
        },
        {
            "@search.action": "upload",
            "id": "hr-003",
            "title": "Política de Vacaciones y Licencias",
            "category": "Licencias",
            "content": "Política de Vacaciones de DevOps Days CORP: 0-1 años: 15 días, 2-4 años: 20 días, 5+ años: 25 días, 10+ años: ilimitadas con aprobación. Licencia parental: 16 semanas con goce de sueldo. Duelo: 5 días para familia directa. Licencia por enfermedad: ilimitada con documentación para 3+ días consecutivos. Sabático: 4 semanas después de 7 años de antigüedad."
        },
        {
            "@search.action": "upload",
            "id": "hr-004",
            "title": "Guía de Incorporación",
            "category": "Incorporación",
            "content": "¡Bienvenido/a a DevOps Days CORP! Semana 1: configuración de IT, papeleo de RR.HH., visión general de la empresa. Semana 2: presentaciones al equipo, capacitación del rol. Semana 3: asignación de buddy, primer proyecto. Semana 4: check-in de 30 días con el manager. Todos los nuevos ingresos reciben laptop DDBook Pro, kit de bienvenida y merchandising de la empresa."
        },
        {
            "@search.action": "upload",
            "id": "hr-005",
            "title": "Proceso de Evaluación de Desempeño",
            "category": "Desempeño",
            "content": "DevOps Days CORP realiza evaluaciones de desempeño dos veces al año en Q1 y Q3. La autoevaluación se entrega 2 semanas antes. Se recopila feedback 360 de pares y socios interfuncionales. Escala: Supera expectativas (5), Cumple+ (4), Cumple (3), En desarrollo (2), Por debajo (1). Los ajustes salariales se vinculan a la revisión de Q1. Los planes de desarrollo se crean en Q3."
        },
        {
            "@search.action": "upload",
            "id": "hr-006",
            "title": "Opciones sobre Acciones y Equity",
            "category": "Compensación",
            "content": "Programa de equity de DevOps Days CORP: los grants de nuevos ingresos se consolidan en 4 años con cliff de 1 año. Los grants de actualización anual se basan en el desempeño (típicamente 25-50% del grant inicial). Ventana de ejercicio: 90 días post-salida para no consolidadas, 10 años para consolidadas. Las opciones se valúan a la última valuación 409A. Los refrescos de equity se otorgan en febrero."
        },
        {
            "@search.action": "upload",
            "id": "hr-007",
            "title": "Aprendizaje y Desarrollo",
            "category": "Desarrollo",
            "content": "Desarrollo profesional en DevOps Days CORP: presupuesto de aprendizaje de $5.000 anuales por empleado. Acceso a LinkedIn Learning, Coursera y la Academia interna de DevOps Days CORP. Asistencia a conferencias: hasta 2 por año. Programa de movilidad interna: explorá nuevos roles después de 18 meses. Programa de mentorías disponible."
        },
        {
            "@search.action": "upload",
            "id": "hr-008",
            "title": "Feriados de la Empresa 2026",
            "category": "Licencias",
            "content": "Feriados 2026 de DevOps Days CORP: Año Nuevo (1 ene), Día del Trabajo (1 may), 25 de Mayo (25 may), 9 de Julio (9 jul), Día de la Raza (12 oct), Inmaculada Concepción (8 dic), Navidad (25 dic), Fin de año (31 dic). Feriados flotantes: 2 días a usar cuando quieras. Oficina cerrada del 24 dic al 1 ene."
        }
    ]
}'

# Products Documents
PRODUCTS_DOCS='{
    "value": [
        {
            "@search.action": "upload",
            "id": "prod-001",
            "title": "DDBook Pro 16\"",
            "category": "Laptops",
            "content": "DDBook Pro 16 pulgadas: chip M4 Pro, CPU de 18 núcleos, 16GB de memoria unificada, SSD 512GB. Pantalla Liquid Retina XDR de 16,2 pulgadas, resolución 3456x2234. Batería de 22 horas. MagSafe 3, 3x Thunderbolt 4, HDMI, ranura SD. Precio: $1.899,99. Stock: 450 unidades. SKU: ZBP-2026-PRO. Ideal para creativos y desarrolladores."
        },
        {
            "@search.action": "upload",
            "id": "prod-002",
            "title": "Auriculares SoundMax Elite",
            "category": "Audio",
            "content": "Auriculares inalámbricos SoundMax Elite: cancelación activa de ruido con 3 modos. Drivers de 40mm, respuesta de frecuencia 20Hz-40kHz. Batería de 30 horas, carga rápida (10 min = 3 horas). Bluetooth 5.3, conexión multipunto. Diseño plegable, almohadillas de espuma viscoelástica premium. Precio: $349,99. Stock: 1.200 unidades. SKU: SMX-ELITE-BLK."
        },
        {
            "@search.action": "upload",
            "id": "prod-003",
            "title": "ProFit Watch Series 5",
            "category": "Wearables",
            "content": "ProFit Watch Series 5: monitoreo de salud avanzado con ECG, oxígeno en sangre y frecuencia cardíaca continua. GPS integrado, opción celular. Caja de 45mm, pantalla AMOLED siempre encendida. Resistencia al agua 5ATM, seguimiento de natación. Análisis de sueño con alarma inteligente. Batería de 18 horas. Precio: $299,99 (GPS), $399,99 (Celular). Stock: 800 unidades."
        },
        {
            "@search.action": "upload",
            "id": "prod-004",
            "title": "DDTab Pro 12.9\"",
            "category": "Tablets",
            "content": "Tablet DDTab Pro 12,9 pulgadas: chip M3, 8GB de RAM, 256GB de almacenamiento. Liquid Retina XDR de 12,9 pulgadas, ProMotion 120Hz. Face ID, USB-C con Thunderbolt. Compatible con DDPencil Pro y Magic Keyboard. Batería de 10 horas. Precio: $1.099,99. Stock: 600 unidades. SKU: ZTP-129-M3. Perfecta para artistas y profesionales móviles."
        },
        {
            "@search.action": "upload",
            "id": "prod-005",
            "title": "DDKeys Wireless Keyboard",
            "category": "Accesorios",
            "content": "Teclado mecánico inalámbrico DDKeys: switches de perfil bajo, feedback táctil. Retroiluminación RGB con zonas personalizables. Bluetooth + dongle 2.4GHz. Cambio entre dispositivos (hasta 3). Recargable, batería de 200 horas. Marco de aluminio, diseño compacto tenkeyless. Precio: $129,99. Stock: 2.500 unidades. SKU: ZK-WL-TKL."
        },
        {
            "@search.action": "upload",
            "id": "prod-006",
            "title": "Cargador PowerMax 100W",
            "category": "Accesorios",
            "content": "Cargador GaN PowerMax 100W: 4 puertos (2x USB-C PD, 2x USB-A). Carga laptop, teléfono, tablet y reloj al mismo tiempo. Clavijas plegables, ideal para viajes. Voltaje universal 100-240V. Distribución inteligente de energía. Precio: $79,99. Stock: 4.000 unidades. SKU: PM-100W-4P. Compacto y potente para todos tus dispositivos."
        },
        {
            "@search.action": "upload",
            "id": "prod-007",
            "title": "DDCam 4K Pro",
            "category": "Cámaras",
            "content": "Webcam DDCam 4K Pro: 4K/30fps o 1080p/60fps. Encuadre automático con IA, desenfoque de fondo. Doble micrófono con cancelación de ruido. Obturador de privacidad integrado. USB-C plug and play. Compatible con Zoom, Teams, Google Meet. Campo visual: ajustable a 90 grados. Precio: $199,99. Stock: 1.800 unidades. SKU: ZC-4K-PRO. Calidad de estudio para el trabajo remoto."
        },
        {
            "@search.action": "upload",
            "id": "prod-008",
            "title": "DDPods Ultra",
            "category": "Audio",
            "content": "Auriculares inalámbricos DDPods Ultra: ANC adaptativa, modo de transparencia. Batería de 6 horas, 30 horas con estuche. Audio espacial con seguimiento de cabeza. Resistencia al sudor IPX4. Controles táctiles, activación por voz Hey DevOps. EQ personalizable en la app. Precio: $249,99. Stock: 3.500 unidades. SKU: ZPU-2026-WHT. Sonido envolvente, comodidad todo el día."
        }
    ]
}'

# Marketing Documents
MARKETING_DOCS='{
    "value": [
        {
            "@search.action": "upload",
            "id": "mkt-001",
            "title": "Campaña de Verano 2026",
            "category": "Campañas",
            "content": "La Campaña de Verano 2026 va del 15 de junio al 15 de julio. Descuentos: Electrónica 20-30% off, Moda 25-40% off, Hogar 15-25% off. Códigos promocionales: VERANO20 (20% off en compras +$100), VERANO30 (30% off en compras +$200). Calendario de emails: 14 jun teaser, 15 jun lanzamiento, 22 jun mid-campaign, 10 jul última oportunidad. Objetivo: $5M de ingresos, 50.000 nuevos clientes."
        },
        {
            "@search.action": "upload",
            "id": "mkt-002",
            "title": "Estrategia de Campaña de Fin de Año",
            "category": "Campañas",
            "content": "Campaña de Fin de Año 2026: Tema \"Regalá Innovación\". Black Friday (27 nov): 40% off en todo el sitio. Cyber Monday (30 nov): foco en tecnología. 12 Días de Ofertas (13-24 dic). Guías de regalos: Amante de la Tecnología, Chef en Casa, Fan del Fitness, Económico. Alianzas con influencers: 25 creadores, contenido de unboxing. Presupuesto total: $2M."
        },
        {
            "@search.action": "upload",
            "id": "mkt-003",
            "title": "Lineamientos de Marca 2026",
            "category": "Marca",
            "content": "Lineamientos de Marca DevOps Days CORP: color primario DD Blue (#0066CC), secundario Electric Orange (#FF6600). Tipografía: DD Sans para títulos, Inter para cuerpo. Voz de marca: amigable, innovadora, confiable. Espacio libre del logo: 2x la altura del ícono. Nunca distorsionar, recolorear ni agregar efectos al logo. Estilo fotográfico: limpio, lifestyle, representación diversa."
        },
        {
            "@search.action": "upload",
            "id": "mkt-004",
            "title": "Manual de Redes Sociales",
            "category": "Social",
            "content": "Lineamientos de Redes Sociales de DevOps Days CORP: Instagram (2 publicaciones diarias, foco visual en productos). TikTok (3 diarias, tendencias y behind the scenes). Twitter/X (4 diarias, novedades y soporte). LinkedIn (1 diaria, cultura y B2B). YouTube (2 semanales, tutoriales y reseñas). Tiempo de respuesta: 2 horas para quejas, 24 horas en general. Hashtags: #DevOpsDaysLife #DevOpsDaysTech."
        },
        {
            "@search.action": "upload",
            "id": "mkt-005",
            "title": "Métricas de Email Marketing Q4 2025",
            "category": "Analítica",
            "content": "Desempeño de Email Q4 2025: 12,5M de emails enviados, tasa de apertura 22,3% (promedio industria 19,8%), CTR 3,8% (promedio 2,6%), tasa de conversión 0,4%. Los más exitosos: Black Friday (45% apertura), Lanzamiento de Producto (38% apertura). Ingresos atribuidos: $4,2M. Tasa de baja: 0,2%. Mejor horario de envío: martes a las 10 hs EST."
        },
        {
            "@search.action": "upload",
            "id": "mkt-006",
            "title": "Programa de Influencers",
            "category": "Alianzas",
            "content": "Programa de Influencers 2026 de DevOps Days CORP: Tier 1 (+1M seguidores): 15% de comisión, productos gratuitos, acceso exclusivo. Tier 2 (100K-1M): 10% de comisión, productos trimestrales. Micro (10K-100K): 8% de comisión, bonos por desempeño. Plantel actual: 47 Tier 1, 312 Tier 2, 1.847 micro. Ingresos por influencers Q4 2025: $4,2M. Categoría líder: Electrónica (TechTubers)."
        },
        {
            "@search.action": "upload",
            "id": "mkt-007",
            "title": "Análisis de Competencia 2026",
            "category": "Investigación",
            "content": "Competitive Landscape 2026: Amazon - Leader in delivery speed, Prime ecosystem. Best Buy - Strong in-store experience, Geek Squad services. Walmart - Price leader, grocery crossover. Diferenciación de DevOps Days CORP: Superior customer service (89% satisfaction), curated product selection, exclusive brands, loyalty rewards. Market share: 8.2% (up from 6.7% in 2025)."
        },
        {
            "@search.action": "upload",
            "id": "mkt-008",
            "title": "Calendario de Contenidos Q1 2026",
            "category": "Contenido",
            "content": "Plan de Contenidos Q1 2026: Enero - "Año Nuevo, Tech Nueva" (2-15 ene), cobertura CES, Liquidación de Verano (16-31 ene). Febrero - Guía de Regalos para San Valentín (1-14 feb), Venta de Presidentes (15-19 feb). Marzo - Renovación de Otoño (1-15 mar), Flash Sale del 17 de Marzo. Blogs: 3 semanales (lunes reseñas, miércoles how-tos, viernes tendencias). Video: 4 YouTube/mes, 20 TikTok/semana."
        }
    ]
}'

# SharePoint HR Documents (indexed separately)
SHAREPOINT_HR_DOCS='{
    "value": [
        {
            "@search.action": "upload",
            "id": "sp-hr-001",
            "title": "Criterios de Promoción",
            "category": "Política de RR.HH.",
            "content": "CRITERIOS DE PROMOCIÓN DE DEVOPS DAYS CORP. Requisitos: mínimo 12 meses en el rol actual, calificación Cumple o Supera en los últimos 2 ciclos, recomendación del manager. Ciclos de promoción: Q1 Ingeniería/Producto/Diseño, Q2 Ventas/Marketing, Q3 Operaciones/Customer Success, Q4 todos los departamentos (excepcional). Compensación: nivel IC 10-15% de aumento, transición a gestión 15-20%. Carrera: Track IC (Asociado→IC→Senior→Staff→Principal→Distinguished), Track Gestión (Manager→Director→VP→C-Level)."
        },
        {
            "@search.action": "upload",
            "id": "sp-hr-002",
            "title": "Detalle de Política de Vacaciones",
            "category": "Política de RR.HH.",
            "content": "POLÍTICA DETALLADA DE VACACIONES DE DEVOPS DAYS CORP. Por antigüedad: 0-1 años 15 días, 2-4 años 20 días, 5-9 años 25 días, 10+ años ilimitadas con aprobación. Licencias adicionales: Parental 16 semanas pagas, Duelo 5 días familia directa, Deber cívico pago, Voluntariado 2 días/año, Sabático 4 semanas después de 7 años. Proceso de solicitud: enviar por Workday con 2 semanas de antelación, aprobación del manager en 48 horas. Períodos bloqueados: últimas 2 semanas del trimestre para equipos de cara al cliente. Transferencia: máx. 5 días al año siguiente, usarlos antes del 31 de marzo."
        },
        {
            "@search.action": "upload",
            "id": "sp-hr-003",
            "title": "Bandas Salariales 2026",
            "category": "Compensación",
            "content": "BANDAS SALARIALES 2026 DE DEVOPS DAYS CORP. Ingeniería: L1 $80-100K, L2 $100-130K, L3 $130-170K, L4 $170-220K, L5 $220-280K. Producto: PM Asociado $85-105K, PM $110-140K, PM Senior $140-180K, Director $180-240K. Ventas: SDR $50K base + $30K OTE, AE $80K + $80K OTE, AE Senior $100K + $150K OTE, AE Enterprise $120K + $200K OTE. Equity: consolidación en 4 años, cliff de 1 año, actualización anual según desempeño. Niveles geográficos: SF/NYC/Seattle tarifa base, Austin/Denver/Boston 90%, Remoto otros 80%."
        },
        {
            "@search.action": "upload",
            "id": "sp-hr-004",
            "title": "Resumen del Manual del Empleado",
            "category": "General",
            "content": "MANUAL DEL EMPLEADO DE DEVOPS DAYS CORP. Código de Conducta: integridad, respeto, proteger información confidencial, reportar conflictos de interés. Gastos: viáticos por ciudad, comidas hasta $75/día, vuelos en turista hasta 6 hs o business en vuelos de 6+ hs, hoteles hasta $250/noche en grandes ciudades. Equipamiento: elección entre MacBook Pro o Dell XPS, hasta 2 monitores, auriculares y webcam provistos. Trabajo remoto: híbrido mínimo 2 días en oficina, encuentros trimestrales presenciales obligatorios. Horario core para reuniones: 10 a 15 hs. Redes sociales: evitar comentar información confidencial, solo portavoces autorizados representan a la empresa."
        }
    ]
}'

# Upload all documents
upload_docs "index-politicas" "$HR_DOCS"
upload_docs "index-herramientas" "$PRODUCTS_DOCS"
upload_docs "index-runbooks" "$MARKETING_DOCS"

# Create marketing blob container and upload data
log_info "Creating marketing blob container..."
az storage container create --name marketing --account-name "$STORAGE_ACCOUNT" --auth-mode login 2>/dev/null || true

# Create marketing blob files
mkdir -p /tmp/marketing-blob

cat > /tmp/marketing-blob/influencer_partnerships.json << 'EOF'
{
  "title": "Programa de Influencers DevOps Days CORP 2026",
  "category": "influencer-marketing",
  "content": "de DevOps Days CORP influencer partnership program connects with content creators across YouTube, TikTok, and Instagram. Tier 1 partners (1M+ followers) receive 15% commission on sales, free products, and exclusive early access. Tier 2 partners (100K-1M followers) receive 10% commission and quarterly product bundles. Micro-influencers (10K-100K) receive 8% commission with performance bonuses. Current active partnerships: 47 Tier 1, 312 Tier 2, 1,847 micro-influencers. Q4 2025 influencer-driven revenue: $4.2M. Top performing category: Electronics (DDBook Pro campaign with TechTuber generated 23,000 direct sales)."
}
EOF

cat > /tmp/marketing-blob/content_calendar_q1_2026.json << 'EOF'
{
  "title": "Calendario de Contenidos Q1 2026",
  "category": "content-planning",
  "content": "January: New Year New Gear campaign (Jan 2-15), Winter Clearance (Jan 16-31). February: Valentine's Gift Guide (Feb 1-14), Presidents Day Sale (Feb 15-19), Spring Preview (Feb 20-28). March: Spring Forward Home Refresh (Mar 1-15), St. Patrick's Day Flash Sale (Mar 17), End of Quarter Push (Mar 20-31). Blog posts: 3x weekly (Monday product reviews, Wednesday how-tos, Friday trend roundups). Social media: 2x daily Instagram, 3x daily TikTok, 1x daily LinkedIn. Email cadence: 2x weekly promotional, 1x weekly newsletter. Video content: 4 YouTube reviews per month, 20 TikTok shorts per week."
}
EOF

cat > /tmp/marketing-blob/customer_testimonials.json << 'EOF'
{
  "title": "Testimonios Destacados de Clientes",
  "category": "social-proof",
  "content": "Sarah M., Austin TX: 'The DDBook Pro changed how I work remotely. Battery lasts all day and the display is gorgeous. 5 stars!' Rating: 5/5. James K., Seattle WA: 'Ordered the SoundMax headphones on Monday, arrived Wednesday. Noise cancellation is incredible for my commute.' Rating: 5/5. Maria L., Miami FL: 'Third time comprando en DevOps Days CORP. Customer service helped me with a return, no questions asked. Will keep coming back.' Rating: 5/5. David R., Chicago IL: 'The ProFit smartwatch tracks my workouts better than my old Fitbit. Heart rate accuracy is spot-on.' Rating: 4/5. Current NPS score: 72. Review response rate: 94% within 24 hours."
}
EOF

cat > /tmp/marketing-blob/market_research_electronics.json << 'EOF'
{
  "title": "Investigación de Mercado de Electrónica - Enero 2026",
  "category": "market-research",
  "content": "Key findings from de DevOps Days CORP Q4 2025 consumer electronics survey (n=5,000). Purchase drivers: 1) Price (78%), 2) Reviews (71%), 3) Brand reputation (54%), 4) Free shipping (52%), 5) Return policy (48%). Emerging trends: Sustainable packaging influences 34% of Gen Z buyers. Wireless charging now expected as standard feature (up from 23% in 2024 to 67% in 2025). Average customer research time before purchase: 4.2 days for items over $200. Competitor analysis: Amazon leads in delivery speed, Best Buy in in-store experience, DevOps Days CORP lidera in customer service satisfaction (89% vs industry average 71%). Recommended focus areas: Same-day delivery expansion, enhanced AR product previews."
}
EOF

cat > /tmp/marketing-blob/press_release_expansion.json << 'EOF'
{
  "title": "Comunicado de Prensa: DevOps Days CORP Anuncia Expansión Europea",
  "category": "press-release",
  "content": "FOR IMMEDIATE RELEASE - January 15, 2026. DevOps Days CORP, el marketplace líder for consumer electronics and lifestyle products, today announced its expansion into the European market with dedicated fulfillment centers in Dublin, Ireland and Rotterdam, Netherlands. The expansion will enable 2-day delivery to 90% of EU customers. 'This represents a major milestone in de DevOps Days CORP mission to deliver quality products globally,' said CEO Amanda Chen. Initial European catalog includes 50,000 SKUs with plans to reach 200,000 by end of 2026. The company will hire 500 employees across both locations. European operations expected to contribute 15% of total revenue by Q4 2026. Media contact: prensa@devopsdays.corp."
}
EOF

# Upload blob files
log_info "Uploading marketing blob files..."
for file in /tmp/marketing-blob/*.json; do
    az storage blob upload --account-name "$STORAGE_ACCOUNT" --container-name marketing \
        --file "$file" --name "$(basename $file)" --auth-mode login --overwrite 2>/dev/null || true
done

log_success "Sample data uploaded to all indexes and blob storage"
