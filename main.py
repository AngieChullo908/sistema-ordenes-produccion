from pathlib import Path
import sys
# El instalador incluye el conector PostgreSQL, sin instalar paquetes globales.
if sys.platform == 'win32':
    sys.path.insert(0,str(Path(__file__).resolve().parent / 'vendor'))
import os
if sys.platform == "win32":
    runtime=Path(sys.executable).resolve().parent
    if (runtime/"tcl").exists():
        os.environ["TCL_LIBRARY"]=str(runtime/"tcl/tcl8.6")
        os.environ["TK_LIBRARY"]=str(runtime/"tcl/tk8.6")
import logging
import tkinter as tk
from tkinter import messagebox

def main():
    from app.infrastructure.settings import DIRECTORY
    DIRECTORY.mkdir(parents=True,exist_ok=True)
    logging.basicConfig(filename=DIRECTORY/'diagnostico.log',level=logging.ERROR,
                        format='%(asctime)s %(levelname)s %(message)s')
    root=tk.Tk()
    def callback_error(kind,value,traceback):
        logging.error('Error de interfaz: %s',kind.__name__)
        messagebox.showerror('Gestión de Órdenes de Producción','No se pudo completar la acción. Consulte el diagnóstico.',parent=root)
    root.report_callback_exception=callback_error
    try:
        from app.controllers.production import ProductionController
        ProductionController(root)
    except ImportError as exc:
        logging.exception('No se pudieron cargar las dependencias del aplicativo')
        messagebox.showerror('Dependencias',f'No se pudo cargar una dependencia: {exc}\n\nEjecute VERIFICAR_WINDOWS.bat o consulte el diagnóstico en {DIRECTORY}. Reinstale con el paquete corregido si falta un módulo.',parent=root)
        root.destroy(); return
    root.mainloop()

if __name__=='__main__':
    main()
