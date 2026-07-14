# SCOPE.md — Buscador Mercado Público

> Documento de alcance. Cualquier función nueva que no esté aquí requiere
> evaluar explícitamente si es indispensable para el MVP antes de agregarla.

## Objetivo

Complementar renta personal detectando oportunidades activas en el sistema
de compras públicas de Chile (Mercado Público), cruzando dos lógicas de
búsqueda distintas: expertise profesional y oportunismo comercial simple.

## Fuentes de datos (dos APIs distintas, con auth distinta)

| Fuente | Base URL | Auth | Búsqueda por keyword |
|---|---|---|---|
| Licitaciones | `api.mercadopublico.cl` | ticket en query string | No — se descarga y filtra localmente |
| Compra Ágil | `api2.mercadopublico.cl` (v2) | ticket en header HTTP | Sí (`q=`) |

**Fuera de alcance del MVP:** Órdenes de Compra. Es historial de compras ya
adjudicadas — no es una oportunidad a la que se pueda postular. Se reserva
para una Fase 2 ("Módulo de Análisis de Mercado").

## Motores de búsqueda

### Motor 1 — Filtro por habilidad (sobre Licitaciones)
- La API no tiene endpoint de búsqueda por texto para Licitaciones.
- Estrategia: se descarga el listado de licitaciones activas del día/rango
  de fechas y se filtra localmente contra `Nombre` + `Descripcion` usando
  una lista de palabras clave editable por el usuario (`keywords.txt`).
- Set inicial de keywords: `geología, innovación, subsidios, profesor
  universitario, I+D`.

### Motor 2 — Oportunismo comercial (sobre Compra Ágil)
- La API sí soporta `q=` (keyword) y `region=`.
- Se usan las mismas keywords como filtro sugerido, PERO el reporte
  también trae todo lo disponible sin filtrar, con filtros interactivos
  en el HTML (monto, organismo, región) para que el usuario revise
  manualmente sin perder oportunidades que no coincidan con texto.

## Arquitectura

- Script Python local, ejecutado por el usuario con doble clic
  (`ejecutar.bat` en Windows).
- Genera un reporte HTML estático (auto-abre en el navegador) con diseño
  de alta densidad de datos, filtros interactivos vía JS plano (sin
  frameworks, sin build step).
- El ticket vive en `config/config.local.json`, **excluido de Git desde
  el primer commit** (ver `.gitignore`). El repositorio solo versiona
  `config/config.example.json` como plantilla.
- Manejo de rate limits: Licitaciones (10.000 req/día), Compra Ágil
  (cuota propia + error 429 con `Retry-After`). El script debe respetar
  ambos límites y fallar de forma clara si se alcanzan.

## Explícitamente fuera de alcance (MVP)

- Órdenes de Compra / Módulo de Análisis de Mercado.
- Notificaciones automáticas (email, push).
- Dashboard con backend propio u hosting.
- Análisis territorial o de tendencias.
- Cualquier función no listada arriba. Si aparece la tentación de
  agregar algo a mitad de camino: **detente y pregunta si es
  estrictamente necesario para este alcance.**

## Historial de decisiones

- 2026-07-14: Se descarta Órdenes de Compra del MVP → Fase 2.
- 2026-07-14: Se descarta artifact HTML en navegador (riesgo de CORS
  contra API de gobierno) → se opta por script Python local.
- 2026-07-14: Se corrige supuesto inicial: Compra Ágil sí soporta
  búsqueda por keyword (`q=`), a diferencia de Licitaciones.
- 2026-07-14: **v1.0 declarado MVP completo y estable.** Funcionando:
  Motor 1 (Licitaciones + Compra Ágil por habilidad) y Motor 2
  (Compra Ágil sin filtrar, acotado a región). Links verificados
  manualmente por el usuario. Se congela el alcance aquí.

## Candidatos a Fase 2 (explícitamente NO en v1.0)

Evaluados y pospuestos a propósito — no se construyen hasta abrir un
Scope nuevo para cada uno:

- **Favoritos**: guardar códigos marcados para revisar después.
- **Ordenar por categoría**: pendiente verificar si el campo categoría
  viene en el listado básico de cada API o si requiere una llamada de
  detalle adicional por resultado (afecta cuota diaria).
- **"Perfil Validado" con IA**: leer la ficha completa de una
  licitación/Compra Ágil seleccionada, generar resumen, plan de acción
  y estimación de tiempo vía una API de IA. Esto es un **proyecto
  separado**, no una función del buscador — requiere su propio Scope,
  su propia arquitectura (llamada a API de IA, manejo de costos por
  uso, diseño de la pantalla de resultado) y se evalúa recién después
  de que v1.0 lleve semanas de uso real.
- **Órdenes de Compra / Módulo de Análisis de Mercado**: ver sección
  anterior, sigue pendiente desde el diseño original.
