# Assets de marca (logo y redes)

Fuente de verdad del logo y los íconos de redes que usan los correos
(`templates/emails/base.html`) y la página de cambio de contraseña
(`templates/password/cambiar_contrasena.html`).

Viven acá y no solo en `<BASE_DIR>/static/vivefacil/` porque ese directorio es
`STATIC_ROOT`, o sea la **salida** de `collectstatic`: en producción funciona
(la ruta `serve_spa` de `TomeSoft_1/urls.py` sirve desde ahí), pero con
`DEBUG=True` el `runserver` intercepta `/static/` con `StaticFilesHandler`, que
resuelve por *finders* y nunca llega a esa ruta. Sin una copia dentro de una app
—que es lo que `AppDirectoriesFinder` sí ve— el logo daba 404 en local.

`collectstatic` copia estos archivos a `STATIC_ROOT`; la copia que ya está
commiteada ahí es esa salida, no una fuente aparte.
