# Movido a core/pagination.py (docs/refactor/03-fase-1-esqueletos.md).
# Re-exportado acá para no romper los imports existentes en api/views.py.
# Se borra junto con el resto de `api` en la Fase 6.
from core.pagination import MyPaginationMixin as MyPaginationMixin
from core.pagination import MyCustomPagination as MyCustomPagination
