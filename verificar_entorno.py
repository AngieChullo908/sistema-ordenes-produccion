"""Diagnóstico local del entorno portable en Windows, sin tocar la base."""
import os
import sys
from pathlib import Path
base=Path(__file__).resolve().parent
sys.path.insert(0,str(base/'vendor'))
os.environ['TCL_LIBRARY']=str(base/'runtime/tcl/tcl8.6')
os.environ['TK_LIBRARY']=str(base/'runtime/tcl/tk8.6')
try:
    import tkinter
    import psycopg
    from psycopg import pq
    root=tkinter.Tk(); root.withdraw()
    from app import __version__
    print('Gestión de Órdenes de Producción:',__version__)
    print('Python:',sys.version)
    print('Tk:',root.tk.call('info','patchlevel'))
    print('Psycopg:',psycopg.__version__)
    print('libpq:',pq.version())
    from app.views.desktop import MainView
    MainView(root); root.update_idletasks(); root.destroy()
    print('CORRECTO: entorno portable e interfaz disponibles. PostgreSQL se configura al abrir Gestión de Órdenes de Producción.')
except Exception:
    import traceback
    traceback.print_exc()
    sys.exit(1)
