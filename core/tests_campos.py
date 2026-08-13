"""Al reemplazar un archivo se borra el anterior del storage; si no cambia, no.
Al borrar la fila se borran todos sus archivos.

    python manage.py test core.tests_campos
"""
from unittest import mock

from django.test import SimpleTestCase

from core.campos import URLCompletaFileField, borrar_archivos_al_eliminar


class _Archivo:
    """Lo mínimo que FileField.pre_save espera de un FieldFile ya guardado."""

    _committed = True

    def __init__(self, name):
        self.name = name

    def __bool__(self):
        return bool(self.name)


class _Instancia:
    def __init__(self, pk, nombre_archivo):
        self.pk = pk
        self.documento = _Archivo(nombre_archivo)


def _campo(ruta_en_bd):
    campo = URLCompletaFileField(upload_to='documents')
    campo.attname = 'documento'
    campo.storage = mock.Mock()
    manager = mock.Mock()
    manager.filter.return_value.values_list.return_value.first.return_value = ruta_en_bd
    return campo, manager


class BorraAnteriorTests(SimpleTestCase):
    def _pre_save(self, campo, manager, instancia, add=False):
        with mock.patch.object(type(instancia), '_base_manager', manager, create=True), \
                mock.patch('core.campos.transaction.on_commit', side_effect=lambda f: f()):
            return campo.pre_save(instancia, add)

    def test_borra_el_anterior_al_reemplazar(self):
        campo, manager = _campo('documents/viejo.pdf')
        self._pre_save(campo, manager, _Instancia(1, 'documents/nuevo.pdf'))
        campo.storage.delete.assert_called_once_with('documents/viejo.pdf')

    def test_no_borra_si_el_archivo_no_cambio(self):
        campo, manager = _campo('documents/igual.pdf')
        self._pre_save(campo, manager, _Instancia(1, 'documents/igual.pdf'))
        campo.storage.delete.assert_not_called()

    def test_no_borra_al_crear(self):
        campo, manager = _campo('documents/viejo.pdf')
        self._pre_save(campo, manager, _Instancia(None, 'documents/nuevo.pdf'), add=True)
        campo.storage.delete.assert_not_called()


class BorrarAlEliminarTests(SimpleTestCase):
    def _instancia(self, *nombres):
        instancia = mock.Mock()
        campos = []
        for i, nombre in enumerate(nombres):
            campo = URLCompletaFileField(upload_to='x')
            campo.attname = f'archivo{i}'
            campo.storage = mock.Mock()
            campos.append(campo)
            setattr(instancia, campo.attname, _Archivo(nombre))
        instancia._meta.concrete_fields = campos + [mock.Mock()]  # uno que no es FileField
        return instancia, campos

    def test_borra_todos_los_archivos_de_la_fila(self):
        instancia, campos = self._instancia('documents/a.pdf', 'foto_perfil/b.png')
        with mock.patch('core.campos.transaction.on_commit', side_effect=lambda f: f()):
            borrar_archivos_al_eliminar(None, instancia)
        campos[0].storage.delete.assert_called_once_with('documents/a.pdf')
        campos[1].storage.delete.assert_called_once_with('foto_perfil/b.png')

    def test_ignora_los_campos_vacios(self):
        instancia, campos = self._instancia('')
        with mock.patch('core.campos.transaction.on_commit', side_effect=lambda f: f()):
            borrar_archivos_al_eliminar(None, instancia)
        campos[0].storage.delete.assert_not_called()
