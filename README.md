# Buscador Mercado Público

Herramienta local para detectar oportunidades activas en el sistema de
compras públicas de Chile (Licitaciones + Compra Ágil), filtradas por
habilidades profesionales y por oportunismo comercial simple.

Ver alcance completo y decisiones de diseño en [`SCOPE.md`](./SCOPE.md).

## Requisitos

- Python 3.8+
- Un ticket de acceso a la API de Mercado Público
  (se solicita en https://www.chilecompra.cl/api/ con Clave Única).

## Configuración inicial

1. Copia `config/config.example.json` a `config/config.local.json`.
2. Pon tu ticket real en `config/config.local.json`.
   **Este archivo nunca se sube a Git** (ver `.gitignore`).
3. Edita `keywords.txt` con tus palabras clave, una por línea.

## Uso

Doble clic en `ejecutar.bat`. Se genera un reporte HTML en `output/` y se
abre automáticamente en tu navegador.

## Estado del proyecto

MVP en construcción. Ver `SCOPE.md` para lo que SÍ y NO incluye esta
versión.
